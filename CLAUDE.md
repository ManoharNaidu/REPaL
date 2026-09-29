# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

Code + data for **REPaL** ("Grasping the Essentials: Tailoring Large Language Models for Zero-Shot Relation Extraction", EMNLP 2024, [arXiv:2402.11142](https://arxiv.org/abs/2402.11142)). REPaL trains a small NLI-based relation-extraction model per target relation using only a natural-language relation *definition* plus an unlabeled corpus: an LLM (GPT-4o) synthesizes seed positive/negative instances from the definition, a small language model (`roberta-large-mnli`) is fine-tuned on them, then a feedback loop ("snowball") mines the SLM's own predictions over the unlabeled corpus to synthesize follow-up examples and refine the model further.

There is no test suite or linter configured in this repo — it's a research reproduction codebase, not a package.

## Commands

Install deps:
```bash
pip install -r requirements.txt
```

Run experiments via the driver ([run_experiments.py](run_experiments.py)), which replaced the old `scripts/run_init.sh` / `scripts/run.sh` shell scripts. It invokes [src/run.py](src/run.py) per `(dataset split x stage)`, captures output, parses P/R/F1, and writes structured results under `results/`:

```bash
# full sweep, both stages, all splits, skip runs that already have a valid metric
python run_experiments.py --data-root reproduce_main_data/data --skip-existing --continue-on-error

# just one dataset/split/stage (useful for smoke-testing a change)
python run_experiments.py --datasets fewrel_defon --splits 1 --stages initial --data-root reproduce_main_data/data

python run_experiments.py --list          # show planned runs without executing
python run_experiments.py --dry-run       # print the src/run.py commands, run nothing
python run_experiments.py --aggregate-only  # rebuild results/aggregate.csv from existing summary.json
```

`--data-root reproduce_main_data/data` reuses the authors' cached GPT-4o synthesis and needs no `OPENAI_API_KEY`; omitting it (or pointing at a fresh `data/<dataset>_<split>/` dir) triggers live LLM calls and does need the key.

`--device-profile {cpu,small_gpu,gpu}` controls batch sizes and `--use_amp`; auto-detected from `torch.cuda.get_device_properties` (<=10GB -> `small_gpu`) when omitted. See the GPU table in [README.md](README.md#recommended-gpu-specification) for what each profile sets. On a cloud GPU (vast.ai), prefer `--device-profile gpu` — see [docs/VASTAI.md](docs/VASTAI.md) and run `bash vastai_setup.sh` for a one-shot setup + sweep.

To run a single stage directly against `src/run.py` (what `run_experiments.py` shells out to), see its `--help` for the full paper-hyperparameter argument list.

## Architecture

**`src/run.py`** — CLI entry point. Parses args, builds a `REDataLoader` and `ModelTrainer`, then dispatches to either the `initial` or `followup` stage based on `--run_type`.

**`src/dataloader.py`** (`REDataLoader`) — loads/caches a dataset split's train/val/test/distant JSON files, tokenizes with the configured `pretrained_lm`, and builds the prompt-encoded tensors/dataloaders the trainer consumes. Caches processed tensors under `<dataset_dir>/<cache_sub_dir>/`.

**`src/model.py`** (`NLIBasedSimilarityModel`) — wraps `roberta-large-mnli` (or another `CKPT2PLM`-registered checkpoint) as an NLI-style binary classifier: relation definitions/prompts are the NLI hypothesis, candidate sentences are the premise.

**`src/trainer.py`** (`ModelTrainer`, ~4k lines — the core of the codebase):
- `run_type=initial`: for each target relation, synthesizes seed pos/neg examples via LLM (or loads cached ones), fine-tunes the SLM, then calls `run_snowball` — K rounds of: infer over the unlabeled corpus with the current model, mine high-confidence predictions as new training signal, fine-tune again. Each round's training loop wraps the forward pass in `torch.cuda.amp.autocast` (when `--use_amp`) but computes the `BCELoss` *outside* that block (PyTorch refuses to autocast `BCELoss`/`binary_cross_entropy` — this was a real crash fixed in this repo; don't move loss computation back inside `autocast`).
- `run_type=followup`: `run_snowball_iterative_main_v1` — feeds the model's snowball-round history back to the LLM as feedback to synthesize further follow-up examples, then continues refining. `_get_rels_pos_examples_followup`'s feedback-mining path calls `spacy.load("en_core_web_trf")`, gated behind a cache-file check — this is never hit when using the cached `reproduce_main_data` checkpoints, and `spacy-transformers`/the model aren't in `requirements.txt`; install both if you hit `OSError: Can't find model 'en_core_web_trf'` on fresh (non-cached) data.
- `NLIBased_Inference` (module-level function, not a method) — the DDP worker spawned via `torch.multiprocessing.spawn` to run inference over the unlabeled corpus across GPUs/ranks in parallel.

**`src/llm_gen.py`** — parses raw/JSON LLM chat responses into structured relation definitions and tagged example sentences (`<ENT0>`/`<ENT1>` span tags).

**`src/pattern_learning.py`** — spaCy dependency-path extraction and KMeans/HDBSCAN clustering used during feedback-driven pattern mining in the `followup` stage.

**`src/utils.py`** — the `GPT3` LLM-call wrapper, SBERT embedding helper, seed/metric utilities, prompt search/fix helpers.

**`run_experiments.py`** — orchestrates the above across every `(dataset, split, stage)` combination: builds the paper's hyperparameters per device profile, shells out to `python -u src/run.py ...` as a subprocess per run, tees output to `results/<dataset>_<split>/<stage>/run.log`, parses P/R/F1 out of it into `metrics.json`, and aggregates everything into `results/summary.csv` / `results/aggregate.csv` (mean +/- std across splits, the number to compare against the paper's reported scores).

## Gotchas already fixed here (don't reintroduce)

- **`BCELoss` under `autocast`**: `nn.BCELoss`/`binary_cross_entropy` cannot run inside `torch.cuda.amp.autocast()` — PyTorch raises `RuntimeError`. Both training-loop and eval-loop sites in `src/trainer.py` compute the forward pass inside `autocast` but the loss outside it (`.float()`-cast). Keep it that way.
- **Windows console encoding**: `src/run.py`, `run_experiments.py`, and the `subprocess.Popen` call in `run_experiments.py` all force UTF-8 stdout/stderr (`sys.stdout.reconfigure(encoding='utf-8', errors='replace')` / `encoding="utf-8"` on `Popen`). Training data contains non-ASCII characters (accents, etc.) and Windows' default `cp1252` console encoding crashes on `print()` of that text otherwise — this took down multi-hour runs late into training. Don't drop these on any code path that prints example text or shells out to another Python process.
