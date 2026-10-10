#!/usr/bin/env python3
"""Build 2026-10-10-repal-results.xlsx / .csv from the real run directories under results/.

Reads results/<dataset>_<split>/<stage>/{metrics.json,config.json}; nothing is hard-coded except the
paper reference F1, which is read from results/aggregate.csv (written by run_experiments.py).
Never modifies results/. Usage: python update_video/make_results_xlsx.py
"""
import csv, datetime, glob, json, os, statistics
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results")
OUT = os.path.join(ROOT, "2026-10-10-repal-results")
DATASETS = ["fewrel_defon", "wikizsl_defon", "semeval", "semeval_qwen3", "nyt", "fewrel_defon10k"]   # nyt_qwen3 not run
STAGES = ["initial", "followup"]


def llm_label(ckpt):
    if ckpt.startswith("gpt-4o"):
        return f"GPT-4o ({ckpt})"
    return ckpt


rows = []
for ds in DATASETS:
    for d in sorted(glob.glob(os.path.join(RES, f"{ds}_[0-9]*"))):
        if os.path.basename(d)[len(ds) + 1:].isdigit() is False:
            continue
        split = os.path.basename(d)[len(ds) + 1:]
        for st in STAGES:
            mp = os.path.join(d, st, "metrics.json")
            if not os.path.exists(mp):
                continue
            m = json.load(open(mp))["chosen"]
            cfg = json.load(open(os.path.join(d, st, "config.json")))
            rows.append(dict(dataset=ds, split=int(split), stage=st, p=m["precision"], r=m["recall"], f1=m["f1"],
                             llm=llm_label(cfg["llm_model_ckpt"]), path=os.path.relpath(mp, ROOT)))
# fewrel_defon / wikizsl_defon use the authors' cached GPT-4o synthesis bundle (reproduce_main_data)
for r in rows:
    if r["dataset"] in ("fewrel_defon", "wikizsl_defon"):
        r["llm"] = "GPT-4o (authors' cached bundle, " + r["llm"].split("(")[-1].rstrip(")") + ")"
    elif r["dataset"] == "fewrel_defon10k" and r["stage"] == "initial":
        r["llm"] = "GPT-4o (authors' cached seed examples, " + r["llm"].split("(")[-1].rstrip(")") + ")"
rows.sort(key=lambda r: (DATASETS.index(r["dataset"]), r["split"], STAGES.index(r["stage"])))

paper = {}
with open(os.path.join(RES, "aggregate.csv")) as f:
    for a in csv.DictReader(f):
        if a["paper_f1"]:
            paper[(a["dataset"], a["stage"])] = float(a["paper_f1"])

wb = Workbook()
hdr = Font(bold=True, color="FFFFFF"); fill = PatternFill("solid", fgColor="305496")


def header(ws, cols):
    ws.append(cols)
    for c in ws[1]:
        c.font = hdr; c.fill = fill; c.alignment = Alignment(wrap_text=True, vertical="top")
    ws.freeze_panes = "A2"


ws = wb.active; ws.title = "All runs"
header(ws, ["dataset", "split", "stage", "Precision", "Recall", "F1", "LLM used for synthesis", "source file path"])
for r in rows:
    ws.append([r["dataset"], r["split"], r["stage"], r["p"], r["r"], r["f1"], r["llm"], r["path"]])
n = len(rows) + 1
for col, w in zip("ABCDEFGH", [18, 7, 10, 11, 11, 11, 62, 60]):
    ws.column_dimensions[col].width = w
for row in ws.iter_rows(min_row=2, min_col=4, max_col=6):
    for c in row:
        c.number_format = "0.0000"

s = wb.create_sheet("Summary")
header(s, ["dataset", "stage", "n splits", "mean F1", "std F1 (sample)", "paper F1 (REPaL w/ GPT-4o, v2 Table 1)",
           "mean - paper", "std F1 (population; = aggregate.csv convention)"])
A, C, F = f"'All runs'!$A$2:$A${n}", f"'All runs'!$C$2:$C${n}", f"'All runs'!$F$2:$F${n}"
i = 2
for ds in DATASETS:
    for st in STAGES:
        s.cell(i, 1, ds); s.cell(i, 2, st)
        s.cell(i, 3, f'=COUNTIFS({A},A{i},{C},B{i})')
        s.cell(i, 4, f'=IF(C{i}=0,"n/a",AVERAGEIFS({F},{A},A{i},{C},B{i}))')
        s.cell(i, 5, f'=IF(C{i}>1,SQRT((SUMPRODUCT(({A}=A{i})*({C}=B{i})*{F}^2)-C{i}*D{i}^2)/(C{i}-1)),0)')
        p = paper.get((ds, st))
        s.cell(i, 6, p if p is not None else "n/a")
        s.cell(i, 7, f'=IF(ISNUMBER(F{i}),D{i}-F{i},"n/a")')
        s.cell(i, 8, f'=IF(C{i}>1,E{i}*SQRT((C{i}-1)/C{i}),0)')
        for col in (4, 5, 6, 7, 8):
            s.cell(i, col).number_format = "0.0000"
        i += 1
for col, w in zip("ABCDEFGH", [18, 10, 9, 11, 15, 22, 13, 24]):
    s.column_dimensions[col].width = w
s.cell(i + 1, 1, "std F1 uses n-1 (sample std; 0 when only one split); results/aggregate.csv instead reports the population std (column H). Means/stds are live formulas over 'All runs'.")
s.cell(i + 2, 1, "Paper F1 exists only for the followup stage of fewrel_defon / wikizsl_defon (arXiv 2402.11142v2 Table 1).")

pn = wb.create_sheet("Provenance notes")
header(pn, ["dataset", "where the rows came from", "evidence"])
notes = [
    ("fewrel_defon", "Authors' released data: reproduce_main_data/data/fewrel_defon_{1..5}; our own training runs on it. "
     "Both stages use the authors' cached GPT-4o synthesis (no live OpenAI calls).",
     "results/fewrel_defon_*/*/config.json: llm_model_ckpt=gpt-4o-2024-05-13; run.log shows no API requests"),
    ("wikizsl_defon", "Same as fewrel_defon, using reproduce_main_data/data/wikizsl_defon_{1..3} and the cached GPT-4o bundle.",
     "results/wikizsl_defon_*/*/config.json"),
    ("semeval", "Own dataset build: tools/build_semeval_defon.py from FewRel 2.0 val_semeval.json (SemEval-2010 Task 8). "
     "Own run with a LOCAL LLM, Qwen2.5-32B-Instruct-AWQ (not Qwen3) for both stages.",
     "results/semeval_1/*/config.json: llm_model_ckpt=Qwen/Qwen2.5-32B-Instruct-AWQ"),
    ("semeval_qwen3", "Same data as semeval_1 (copied json, no cache), regenerated with Qwen/Qwen3-32B-AWQ as the generator LLM. "
     "Own run. Compare with semeval only as a generator-LLM comparison.",
     "results/semeval_qwen3_1/*/config.json: llm_model_ckpt=Qwen/Qwen3-32B-AWQ"),
    ("nyt", "Own dataset build: tools/build_nyt_defon.py from FewRel 2.0 val_nyt.json. Own run, local Qwen2.5-32B-Instruct-AWQ. "
     "(The pending 'nyt_qwen3' run does not exist yet and is not in this workbook.)",
     "results/nyt_1/*/config.json: llm_model_ckpt=Qwen/Qwen2.5-32B-Instruct-AWQ"),
    ("fewrel_defon10k", "Own run on the authors' FewRel split with the unlabeled pool down-sampled to 10,000 (tools/build_fewrel_10k_pool.py). "
     "MIXED generators: initial stage reuses the authors' cached GPT-4o seed examples; followup stage was generated live by "
     "Qwen2.5-32B-Instruct-AWQ because the cached GPT-4o follow-up examples depend on the 100k pool and were not copied.",
     "tools/build_fewrel_10k_pool.py docstring; results/fewrel_defon10k_*/followup/config.json"),
    ("(not included) archive/semeval_1_gpt4o", "Earlier SemEval run with live GPT-4o: initial-stage F1 0.357; followup stopped when OpenAI credits "
     "ran out. Kept in results/archive and data/archive; not in the tables above.", "results/archive/semeval_1_gpt4o/README.txt"),
]
for nrow in notes:
    pn.append(list(nrow))
for col, w in zip("ABC", [24, 100, 70]):
    pn.column_dimensions[col].width = w
for row in pn.iter_rows(min_row=2):
    for c in row:
        c.alignment = Alignment(wrap_text=True, vertical="top")
pn.append([]); pn.append([f"Generated {datetime.date.today()} by update_video/make_results_xlsx.py from results/*/*/metrics.json"])

wb.save(OUT + ".xlsx")
with open(OUT + ".csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["dataset", "split", "stage", "precision", "recall", "f1", "llm_used_for_synthesis", "source_file"])
    for r in rows:
        w.writerow([r["dataset"], r["split"], r["stage"], r["p"], r["r"], r["f1"], r["llm"], r["path"]])
print(f"{len(rows)} runs -> {OUT}.xlsx / .csv")
