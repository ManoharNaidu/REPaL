#!/usr/bin/env python
"""
Experiment driver for the REPaL reproduction / extension project.

Replaces the deleted ``scripts/run_init.sh`` and ``scripts/run.sh``. For every
(dataset split x stage) it invokes ``src/run.py`` with the paper's
hyper-parameters, captures the console output, parses the reported P/R/F1
numbers, and writes everything under ``results/``:

    results/
        summary.csv / summary.json     <- one row per (dataset_split x stage)
        aggregate.csv / aggregate.json <- P/R/F1 mean +/- std across splits
                                          (the number to compare to the paper)
        <dataset>_<split>/<stage>/
            config.json    <- exact args used
            run.log        <- full stdout/stderr of src/run.py
            metrics.json   <- parsed per-epoch + chosen P/R/F1

Two stages, matching the two original scripts:
    initial   -> run_init.sh  (definition-based seed construction + SLM training)
    followup  -> run.sh       (feedback-driven refinement)

Usage
-----
    # Week 1: reproduce DefOn-FewRel using the authors' cached GPT-4o synthesis
    python run_experiments.py --datasets fewrel_defon --data-root reproduce_main_data/data

    # Week 2: DefOn-WikiZSL
    python run_experiments.py --datasets wikizsl_defon --data-root reproduce_main_data/data --splits 1 2 3

    # only the first split, initial stage, to smoke-test
    python run_experiments.py --datasets fewrel_defon --splits 1 --stages initial

    # Section 4 extension: a new dataset dropped into data/semeval_1/ etc.
    python run_experiments.py --datasets semeval --splits 1

    python run_experiments.py --list        # show what would run
    python run_experiments.py --dry-run     # print commands, run nothing
    python run_experiments.py --aggregate-only   # just rebuild aggregate.csv

Environment (was set at the top of the old shell scripts):
    OPENAI_API_KEY          needed only when synthesising fresh data
                            (NOT needed with --data-root reproduce_main_data/data)
    HUGGINGFACE_CACHE_DIR   optional, defaults to ./.hf_cache
    BASE_LLM / PARSER_LLM   optional model overrides
    CUDA_VISIBLE_DEVICES    optional
"""

import argparse
import csv
import json
import os
import re
import statistics
import subprocess
import sys
import time
from copy import deepcopy
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
RESULTS_DIR = REPO_ROOT / "results"

# How many splits each DefOn dataset ships with (Section 2.1 of the proposal).
DATASET_SPLITS = {
    "fewrel_defon": ["1", "2", "3", "4", "5"],
    "wikizsl_defon": ["1", "2", "3"],
}

# Paper-reported REPaL scores, for side-by-side comparison in aggregate.csv.
# (F1, averaged over relations & splits.) Fill in / adjust from the paper table.
PAPER_REFERENCE_F1 = {
    "fewrel_defon": None,
    "wikizsl_defon": None,
}


# --------------------------------------------------------------------------- #
# Paper hyper-parameters -- copied verbatim from the old run_init.sh / run.sh
# --------------------------------------------------------------------------- #
COMMON_CONFIG = {
    "seed": 3,
    "pretrained_lm": "roberta-large-mnli",
    "accum_steps": 1,
    "train_batch_size": 16,
    "num_train_epochs": 12,
    "learning_rate": 3e-5,
    "logging_steps": 0,
    "save_steps": -1,
    "negative_sampling_upper_bound": 0.6,
    "save_epochs": 4,
    "logging_epochs": 4,
    "rel_info_file": "rel_info_updated.json",
    "cache_sub_dir": "cache/",
    "temperature": 0.6,
    "def_gen_temperature": 0.6,
    "neg_ex_gen_temperature": 0.6,
    "num_buffer_examples": 50,
    "num_init_pos_examples": 15,
    "num_init_neg_examples": 15,
    "num_init_neg_rels_to_generate": 5,
    "num_init_neg_examples_to_generate": 15,
    "num_follow_pos_examples": 15,
    "num_follow_neg_examples": 15,
    "num_follow_neg_rels_to_generate": 5,
    "num_follow_neg_examples_to_generate": 15,
    "run_LLM_json_parser_def": True,
    "llm_model_ckpt_parser": None,   # filled from PARSER_LLM at runtime
    "llm_model_ckpt": None,          # filled from BASE_LLM at runtime
}

STAGE_CONFIG = {
    "initial": {
        "run_type": "initial",
        "dist_port": 12345,
        "run_snowball": True,
    },
    "followup": {
        "run_type": "followup",
        "dist_port": 12366,
        "run_LLM_json_parser_ex": True,
        "run_neg_follow_gen": True,
        "run_snowball": False,
    },
}

# Batch-size / precision profiles. The paper's eval/unlabel_infer=3600/4200
# assume 4 large (>=24GB) GPUs and OOM on CPU or an 8GB card.
#
#   gpu       -- a big single GPU (>=16GB), paper's train_batch_size kept.
#   small_gpu -- an 8GB card (e.g. RTX 4000). roberta-large-mnli in fp32 uses
#                ~5.6GB of fixed VRAM (weights + Adam states + grads) before any
#                activations, so train_batch_size is halved with accum_steps
#                doubled to keep the same effective batch size as the paper,
#                and AMP (--use_amp) is enabled to roughly halve activation
#                memory and speed up training.
#   cpu       -- no GPU. Training is impractically slow regardless of batch size;
#                these keep it from OOMing on a full evaluation split.
BATCH_PROFILE = {
    "gpu": {"eval_batch_size": 512, "unlabel_infer_batch_size": 512},
    "small_gpu": {
        "train_batch_size": 8, "accum_steps": 2,
        "eval_batch_size": 128, "unlabel_infer_batch_size": 128,
        "use_amp": True,
    },
    "cpu": {"eval_batch_size": 16, "unlabel_infer_batch_size": 16},
}


def detect_device_profile(override: str | None) -> str:
    if override in ("cpu", "gpu", "small_gpu"):
        return override
    try:
        import torch
        if not torch.cuda.is_available():
            return "cpu"
        # heuristic: <=10GB reported total memory -> treat as a small GPU
        total_gb = torch.cuda.get_device_properties(0).total_memory / (1024 ** 3)
        return "small_gpu" if total_gb <= 10 else "gpu"
    except Exception:
        return "cpu"


# --------------------------------------------------------------------------- #
# Command construction / execution
# --------------------------------------------------------------------------- #
def build_command(cfg: dict, dataset_dir: Path) -> list:
    cmd = [sys.executable, "-u", "src/run.py"]
    for key, val in cfg.items():
        if val is None:
            continue
        flag = f"--{key}"
        if isinstance(val, bool):
            if val:
                cmd.append(flag)
        elif isinstance(val, (list, tuple)):
            cmd.append(flag)
            cmd.extend(str(v) for v in val)
        else:
            cmd.extend([flag, str(val)])
    cmd.extend(["--dataset_dir", str(dataset_dir) + os.sep])
    return cmd


_METRIC_RE = re.compile(
    r"Results \(at epoch=(?P<epoch>\d+)\) averaged over all relations:\s*"
    r"P:\s*(?P<p>[-\d.eE]+)\s*\|\s*R:\s*(?P<r>[-\d.eE]+)\s*\|\s*F1:\s*(?P<f1>[-\d.eE]+)"
)
_CHOSEN_RE = re.compile(
    r"Chosen results averaged over all relations:\s*"
    r"P:\s*(?P<p>[-\d.eE]+)\s*\|\s*R:\s*(?P<r>[-\d.eE]+)\s*\|\s*F1:\s*(?P<f1>[-\d.eE]+)"
)


def _to_float(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def parse_metrics(text: str) -> dict:
    per_epoch = [
        {
            "epoch": int(m.group("epoch")),
            "precision": _to_float(m.group("p")),
            "recall": _to_float(m.group("r")),
            "f1": _to_float(m.group("f1")),
        }
        for m in _METRIC_RE.finditer(text)
    ]
    chosen = None
    matches = list(_CHOSEN_RE.finditer(text))
    if matches:
        m = matches[-1]
        chosen = {
            "precision": _to_float(m.group("p")),
            "recall": _to_float(m.group("r")),
            "f1": _to_float(m.group("f1")),
        }
    best = max(per_epoch, key=lambda d: (d["f1"] is not None, d["f1"] or -1), default=None)
    return {"per_epoch": per_epoch, "chosen": chosen, "best_epoch": best}


def run_one(cmd: list, env: dict, log_path: Path) -> int:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "w", encoding="utf-8", errors="replace") as log:
        log.write(f"# command: {' '.join(cmd)}\n")
        log.write(f"# started: {datetime.now().isoformat()}\n\n")
        log.flush()
        proc = subprocess.Popen(
            cmd, cwd=str(REPO_ROOT), env=env,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1,
        )
        for line in proc.stdout:
            sys.stdout.write(line)
            log.write(line)
        proc.wait()
        log.write(f"\n# finished: {datetime.now().isoformat()} exit={proc.returncode}\n")
    return proc.returncode


# --------------------------------------------------------------------------- #
# Summary / aggregate tables
# --------------------------------------------------------------------------- #
SUMMARY_FIELDS = [
    "dataset", "split", "stage", "exit_code", "elapsed_sec",
    "chosen_precision", "chosen_recall", "chosen_f1",
    "best_epoch", "best_f1", "data_root", "device_profile", "timestamp",
]


def load_summary() -> list:
    p = RESULTS_DIR / "summary.json"
    if p.exists():
        try:
            return json.loads(p.read_text())
        except json.JSONDecodeError:
            pass
    return []


def write_summary(rows: list):
    (RESULTS_DIR / "summary.json").write_text(json.dumps(rows, indent=2))
    with open(RESULTS_DIR / "summary.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=SUMMARY_FIELDS)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k) for k in SUMMARY_FIELDS})


def write_aggregate(rows: list):
    """Mean +/- std of P/R/F1 across splits, per (dataset, stage)."""
    groups: dict = {}
    for r in rows:
        if r.get("exit_code") != 0 or r.get("chosen_f1") is None:
            continue
        groups.setdefault((r["dataset"], r["stage"]), []).append(r)

    agg = []
    for (dataset, stage), rs in sorted(groups.items()):
        def col(name):
            vals = [x[name] for x in rs if x.get(name) is not None]
            if not vals:
                return (None, None)
            mean = statistics.fmean(vals)
            std = statistics.pstdev(vals) if len(vals) > 1 else 0.0
            return (round(mean, 4), round(std, 4))

        p_m, p_s = col("chosen_precision")
        r_m, r_s = col("chosen_recall")
        f_m, f_s = col("chosen_f1")
        agg.append({
            "dataset": dataset,
            "stage": stage,
            "n_splits": len(rs),
            "splits": ",".join(sorted(x["split"] for x in rs)),
            "precision_mean": p_m, "precision_std": p_s,
            "recall_mean": r_m, "recall_std": r_s,
            "f1_mean": f_m, "f1_std": f_s,
            "paper_f1": PAPER_REFERENCE_F1.get(dataset),
            "f1_delta_vs_paper": (round(f_m - PAPER_REFERENCE_F1[dataset], 4)
                                  if f_m is not None and PAPER_REFERENCE_F1.get(dataset) else None),
        })

    fields = ["dataset", "stage", "n_splits", "splits",
              "precision_mean", "precision_std", "recall_mean", "recall_std",
              "f1_mean", "f1_std", "paper_f1", "f1_delta_vs_paper"]
    (RESULTS_DIR / "aggregate.json").write_text(json.dumps(agg, indent=2))
    with open(RESULTS_DIR / "aggregate.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(agg)
    return agg


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--datasets", nargs="+", default=["fewrel_defon"],
                    help="dataset prefixes; dirs are <data-root>/<prefix>_<split>")
    ap.add_argument("--splits", nargs="+", default=None,
                    help="splits to run (default: all splits the dataset ships with)")
    ap.add_argument("--stages", nargs="+", default=["initial", "followup"],
                    choices=["initial", "followup"], help="pipeline stages to run per split")
    ap.add_argument("--data-root", default="data",
                    help="dir holding <dataset>_<split>/ folders. Use "
                         "'reproduce_main_data/data' to reuse the authors' cached "
                         "GPT-4o synthesis (no OPENAI_API_KEY needed).")
    ap.add_argument("--device-profile", choices=["cpu", "gpu", "small_gpu"], default=None,
                    help="override auto-detection of batch sizes / AMP. "
                         "'small_gpu' targets an 8GB card (e.g. RTX 4000): "
                         "halved train_batch_size + doubled accum_steps to match "
                         "the paper's effective batch size, plus AMP.")
    ap.add_argument("--seed", type=int, default=None, help="override the training seed")
    ap.add_argument("--dry-run", action="store_true", help="print commands only")
    ap.add_argument("--list", action="store_true", help="list planned runs and exit")
    ap.add_argument("--aggregate-only", action="store_true",
                    help="rebuild aggregate.csv from existing summary.json and exit")
    ap.add_argument("--continue-on-error", action="store_true",
                    help="keep going if a run fails (default: stop)")
    ap.add_argument("--skip-existing", action="store_true",
                    help="skip a run whose metrics.json already has a chosen_f1")
    args = ap.parse_args()

    RESULTS_DIR.mkdir(exist_ok=True)
    summary_rows = load_summary()

    if args.aggregate_only:
        agg = write_aggregate(summary_rows)
        print(json.dumps(agg, indent=2))
        return

    data_root = (REPO_ROOT / args.data_root).resolve()
    profile = detect_device_profile(args.device_profile)
    base_llm = os.environ.get("BASE_LLM", "gpt-4o-2024-05-13")
    parser_llm = os.environ.get("PARSER_LLM", "gpt-4o-mini-2024-07-18")

    # plan
    plan = []
    for ds in args.datasets:
        splits = args.splits or DATASET_SPLITS.get(ds, ["1"])
        for split in splits:
            for stage in args.stages:
                plan.append((ds, split, stage))

    if args.list:
        for ds, split, stage in plan:
            d = data_root / f"{ds}_{split}"
            print(f"{ds}_{split:<3} {stage:<9} {'OK' if d.is_dir() else 'MISSING'} {d}")
        print(f"\ndata-root={data_root}  device-profile={profile}")
        return

    env = os.environ.copy()
    env.setdefault("CUDA_DEVICE_ORDER", "PCI_BUS_ID")
    env.setdefault("HUGGINGFACE_CACHE_DIR", str(REPO_ROOT / ".hf_cache"))

    uses_cached_synth = data_root.name == "data" and data_root.parent.name == "reproduce_main_data"
    if not args.dry_run and not env.get("OPENAI_API_KEY") and not uses_cached_synth:
        print("WARNING: OPENAI_API_KEY not set and --data-root is not the cached "
              "reproduce_main_data/data; LLM synthesis will fail.", file=sys.stderr)
    if profile == "cpu":
        print("NOTE: running on CPU. eval/inference batch sizes forced small; "
              "a full split will take many hours -- prefer a GPU (Colab).", file=sys.stderr)
    elif profile == "small_gpu":
        print("NOTE: small_gpu profile (<=~8-10GB VRAM): train_batch_size=8 with "
              "accum_steps=2 (effective batch 16, matching the paper) and AMP "
              "enabled. Raise --device-profile gpu if you have >=16GB VRAM.",
              file=sys.stderr)

    total, done = len(plan), 0
    for ds, split, stage in plan:
        done += 1
        dataset_dir = data_root / f"{ds}_{split}"
        out_dir = RESULTS_DIR / f"{ds}_{split}" / stage
        print("\n" + "=" * 78)
        print(f"[{done}/{total}] {ds}_{split}  stage={stage}  profile={profile}")
        print("=" * 78)

        if not dataset_dir.is_dir():
            print(f"  SKIP: not found: {dataset_dir}")
            continue
        if args.skip_existing:
            mj = out_dir / "metrics.json"
            if mj.exists() and (json.loads(mj.read_text()).get("chosen") or {}).get("f1") is not None:
                print("  SKIP: already has metrics")
                continue

        cfg = deepcopy(COMMON_CONFIG)
        cfg.update(STAGE_CONFIG[stage])
        cfg.update(BATCH_PROFILE[profile])
        cfg["llm_model_ckpt"] = base_llm
        cfg["llm_model_ckpt_parser"] = parser_llm
        cfg["huggingface_cache_dir"] = env["HUGGINGFACE_CACHE_DIR"]
        cfg["output_dir"] = str(out_dir) + os.sep
        if args.seed is not None:
            cfg["seed"] = args.seed

        cmd = build_command(cfg, dataset_dir)
        if args.dry_run:
            print("  " + " ".join(cmd))
            continue

        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "config.json").write_text(json.dumps(cfg, indent=2))

        t0 = time.time()
        rc = run_one(cmd, env, out_dir / "run.log")
        elapsed = round(time.time() - t0, 1)

        log_text = (out_dir / "run.log").read_text(encoding="utf-8", errors="replace")
        metrics = parse_metrics(log_text)
        metrics.update(exit_code=rc, elapsed_sec=elapsed)
        (out_dir / "metrics.json").write_text(json.dumps(metrics, indent=2))

        chosen = metrics.get("chosen") or {}
        best = metrics.get("best_epoch") or {}
        row = {
            "dataset": ds, "split": split, "stage": stage,
            "exit_code": rc, "elapsed_sec": elapsed,
            "chosen_precision": chosen.get("precision"),
            "chosen_recall": chosen.get("recall"),
            "chosen_f1": chosen.get("f1"),
            "best_epoch": best.get("epoch"), "best_f1": best.get("f1"),
            "data_root": args.data_root, "device_profile": profile,
            "timestamp": datetime.now().isoformat(timespec="seconds"),
        }
        summary_rows = [
            r for r in summary_rows
            if not (r.get("dataset") == ds and r.get("split") == split and r.get("stage") == stage)
        ]
        summary_rows.append(row)
        write_summary(summary_rows)
        write_aggregate(summary_rows)

        print(f"  -> exit={rc}  chosen_f1={row['chosen_f1']}  time={elapsed}s")
        if rc != 0 and not args.continue_on_error:
            print("  stopping (use --continue-on-error to keep going)")
            sys.exit(rc)

    print(f"\nDone. See {RESULTS_DIR/'summary.csv'} and {RESULTS_DIR/'aggregate.csv'}")


if __name__ == "__main__":
    main()
