#!/usr/bin/env python3
"""Read-only SemEval diagnosis. Prints markdown tables; changes nothing, runs no model.

Sources
  A. exact per-relation P/R/F1: "Chosen results for <rel>:" lines in results/<run>/<stage>/run.log
  B. per-instance predictions (initial stage only): data/semeval_1/cache/snowball_ckpt_15p15n_seed3/
     <rel>_unlabeled_inference.pt (threshold-0.5 predictions of each relation's binary model over the
     unlabeled pool, which is the test set with labels removed). Gold comes from test.json by matching
     (tokens, head idx, tail idx). These are NOT guaranteed to be the same checkpoint as the reported
     numbers (macro P/R/F1 recomputed from them differ slightly), so use them for patterns only.
"""
import json, os, re, sys
import numpy as np
import torch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, "data/semeval_1/")
rels = list(json.load(open(D + "rel2id.json")))
short = lambda r: r.replace("(e1,e2)", " (e1,e2)").replace("(e2,e1)", " (e2,e1)")


def log_rel(run, stage):
    out = {}
    for ln in open(os.path.join(ROOT, "results", run, stage, "run.log"), encoding="utf-8", errors="replace"):
        m = re.match(r"Chosen results for (.+?):\s+P: (\S+) \| R: (\S+) \| F1: (\S+)", ln)
        if m:
            out[m.group(1)] = tuple(map(float, m.group(2, 3, 4)))
    return out


def table(head, rows):
    print("| " + " | ".join(head) + " |"); print("|" + "---|" * len(head))
    for r in rows:
        print("| " + " | ".join(r) + " |")
    print()


test = json.load(open(D + "test.json"))
n_test = {r: len(test[r]) for r in rels}
print("## A. Per-relation results from the run logs (exact)\n")
runs = [("semeval_1", "initial"), ("semeval_1", "followup"), ("semeval_qwen3_1", "initial"), ("semeval_qwen3_1", "followup")]
L = {k: log_rel(*k) for k in runs}
head = ["relation", "test n"] + [f"{r.replace('semeval_', 'sv_')[:9]} {s[:4]} P/R/F1" for r, s in runs]
rows = []
for r in rels:
    rows.append([short(r), str(n_test[r])] + [f"{L[k][r][0]:.2f}/{L[k][r][1]:.2f}/{L[k][r][2]:.2f}" for k in runs])
rows.append(["**macro mean**", str(sum(n_test.values()))] + [
    "{:.2f}/{:.2f}/{:.2f}".format(*np.mean([L[k][r] for r in rels], axis=0)) for k in runs])
table(head, rows)

print("### Relations sorted by semeval_1 followup F1 (weakest first)\n")
order = sorted(rels, key=lambda r: L[("semeval_1", "followup")][r][2])
table(["relation", "test n", "followup P", "followup R", "followup F1", "initial F1"],
      [[short(r), str(n_test[r])] + [f"{v:.3f}" for v in L[("semeval_1", "followup")][r]] + [f"{L[('semeval_1', 'initial')][r][2]:.3f}"] for r in order])

# ---------- direction analysis (B) ----------
dist = json.load(open(D + "distant.json"))["UNLABELED"]
key = lambda r: (tuple(r["tokens"]), str(r["h"][2]), str(r["t"][2]))
gold_of = {key(r): rel for rel, v in test.items() for r in v}
g = np.array([rels.index(gold_of[key(r)]) for r in dist])
pred = np.zeros((len(dist), len(rels)), dtype=bool)
for i, r in enumerate(rels):
    x = torch.load(f"{D}cache/snowball_ckpt_15p15n_seed3/{r}_unlabeled_inference.pt", weights_only=False)
    pred[:, i] = np.array(x["predictions"]) == 1
base = lambda r: r.split("(")[0]
rev = lambda r: r.replace("(e1,e2)", "(@)").replace("(e2,e1)", "(e1,e2)").replace("(@)", "(e2,e1)")
print("## B. Direction analysis (initial-stage inference files; approximate checkpoint)\n")
print(f"instances: {len(g)}; macro recomputed from these files: "
      f"P={np.mean([(pred[g == i, i].sum() / max(pred[:, i].sum(), 1)) for i in range(len(rels))]):.3f} "
      f"R={np.mean([pred[g == i, i].mean() for i in range(len(rels))]):.3f} (reported initial: P 0.454 R 0.204 F1 0.190)\n")
rows = []; tot_fp = tot_fp_rev = tot_fp_same_base = 0
for i, r in enumerate(rels):
    m = g == i
    rec = pred[m, i].mean()
    has_rev = rev(r) in rels
    rec_rev = pred[m, rels.index(rev(r))].mean() if has_rev else float("nan")
    others = [j for j in range(len(rels)) if j != i and j != (rels.index(rev(r)) if has_rev else -1)]
    rec_oth = pred[m][:, others].mean()
    fp = pred[~m, i]; nfp = fp.sum()
    fp_rev = pred[g == rels.index(rev(r)), i].sum() if has_rev else 0
    tot_fp += nfp; tot_fp_rev += fp_rev
    rows.append([short(r), str(m.sum()), f"{rec:.2f}", "n/a" if not has_rev else f"{rec_rev:.2f}", f"{rec_oth:.2f}", str(int(nfp)),
                 "n/a" if not has_rev else (f"{fp_rev / nfp:.0%}" if nfp else "-"),
                 "n/a" if not has_rev else f"{(len(rels) and (g == rels.index(rev(r))).sum()) / (len(g) - m.sum()):.0%}"])
table(["gold relation", "n", "own model fires", "reverse-direction model fires", "other models fire (avg)",
       "false positives of this model", "FP that are reverse-direction gold", "reverse gold share of all negatives"], rows)
print(f"Overall: {int(tot_fp_rev)} of {int(tot_fp)} false positives ({tot_fp_rev / tot_fp:.1%}) come from the reverse-direction gold class "
      f"(only counting relations that have a reverse class).\n")

# same-base vs different-base false positives, and multi-fire
multi = (pred.sum(1) > 1).mean(); none = (pred.sum(1) == 0).mean()
print(f"Instances where no relation model fires: {none:.1%}; where more than one fires: {multi:.1%}; exactly one: {1 - none - multi:.1%}\n")

# per-instance 'argmax-like' confusion on instances where exactly one model fires
one = pred.sum(1) == 1
fired = pred.argmax(1)
cm_same = (fired[one] == g[one]).mean()
cm_rev = np.mean([rels[fired[k]] == rev(rels[g[k]]) for k in np.where(one)[0]])
cm_samebase = np.mean([base(rels[fired[k]]) == base(rels[g[k]]) and fired[k] != g[k] for k in np.where(one)[0]])
print(f"Among the {one.sum()} instances where exactly one model fires: correct {cm_same:.1%}; "
      f"fires the reverse-direction relation {cm_rev:.1%}; fires some other relation {1 - cm_same - cm_rev:.1%}\n")

print("### Gold class size vs recall (initial inference)\n")
sizes = np.array([n_test[r] for r in rels]); recs = np.array([pred[g == i, i].mean() for i in range(len(rels))])
print(f"Spearman-like check: corr(log n, recall) = {np.corrcoef(np.log(sizes), recs)[0, 1]:.2f}; "
      f"corr(n, followup F1 from logs) = {np.corrcoef(sizes, [L[('semeval_1', 'followup')][r][2] for r in rels])[0, 1]:.2f}\n")

# qualitative + quantitative: LLM-generated seed positives vs real test entities
print("## C. Generated seed positives vs real test instances (entity span length)\n")
seeds = torch.load(D + "cache/llm_15p_seed3/rel_init_pos.pt", weights_only=False)   # list: one list of 15 dicts per relation, in rel2id order
tl = lambda recs: (np.mean([len(r["h"][2][0]) for r in recs]), np.mean([len(r["t"][2][0]) for r in recs]))
rows = []; sh = []; st_ = []; th = []; tt = []
for i, r in enumerate(rels):
    a, b = tl(seeds[i]); c, d = tl(test[r])
    sh.append(a); st_.append(b); th.append(c); tt.append(d)
    rows.append([short(r), f"{len(seeds[i])}", f"{a:.1f}", f"{b:.1f}", f"{c:.1f}", f"{d:.1f}", f"{np.mean([len(x['tokens']) for x in seeds[i]]):.0f}", f"{np.mean([len(x['tokens']) for x in test[r]]):.0f}"])
rows.append(["**mean**", "", f"{np.mean(sh):.1f}", f"{np.mean(st_):.1f}", f"{np.mean(th):.1f}", f"{np.mean(tt):.1f}",
             f"{np.mean([len(x['tokens']) for s in seeds for x in s]):.0f}", f"{np.mean([len(x['tokens']) for v in test.values() for x in v]):.0f}"])
table(["relation", "n seeds", "seed head len", "seed tail len", "test head len", "test tail len", "seed sent len", "test sent len"], rows)
for r in (order[0], order[1]):
    print(f"Examples, {short(r)} (seed positives):\n")
    for x in seeds[rels.index(r)][:3]:
        print(f"- head=\"{x['h'][0]}\" tail=\"{x['t'][0]}\" :: " + " ".join(x["tokens"])[:200])
    print()
    print(f"Examples, {short(r)} (real test):\n")
    for x in test[r][:3]:
        print(f"- head=\"{x['h'][0]}\" tail=\"{x['t'][0]}\" :: " + " ".join(x["tokens"])[:200])
    print()
