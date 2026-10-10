#!/usr/bin/env python3
"""Inter-annotator agreement (Cohen's kappa + raw % agreement) for the arXiv relation annotation.

Two input styles:
  python arxiv_re/kappa.py --a sheet_annotator1.csv --b sheet_annotator2.csv [--col relation] [--id id]
      two copies of the annotation sheet, joined on the id column
  python arxiv_re/kappa.py --one both.csv --col-a rel_a --col-b rel_b
      one CSV with two label columns
Rows where either label is blank are skipped (and counted). Blank cells are NOT treated as a "no relation" label:
annotators should write an explicit label such as `none` for sentences with no target relation.
Pure standard library. `--selftest` runs a tiny MADE-UP example (not real annotations) and cross-checks sklearn.
"""
import argparse, csv, sys
from collections import Counter


def cohen_kappa(a, b):
    n = len(a)
    if n == 0:
        raise ValueError("no paired labels")
    po = sum(x == y for x, y in zip(a, b)) / n
    ca, cb = Counter(a), Counter(b)
    pe = sum(ca[k] * cb.get(k, 0) for k in ca) / (n * n)
    kappa = 1.0 if pe == 1 else (po - pe) / (1 - pe)
    return kappa, po


def interpret(k):   # Landis & Koch (1977)
    for lim, name in [(0, "poor"), (0.2, "slight"), (0.4, "fair"), (0.6, "moderate"), (0.8, "substantial"), (1.01, "almost perfect")]:
        if k < lim:
            return name
    return "almost perfect"


def read(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def pairs_from_two(a_path, b_path, col, idc):
    B = {r[idc]: r for r in read(b_path)}
    out, skipped = [], 0
    for r in read(a_path):
        o = B.get(r[idc])
        x, y = (r.get(col) or "").strip(), ((o or {}).get(col) or "").strip()
        if not x or not y:
            skipped += 1
        else:
            out.append((x, y))
    return out, skipped


def report(pairs, skipped):
    a, b = [p[0] for p in pairs], [p[1] for p in pairs]
    k, po = cohen_kappa(a, b)
    print(f"items compared: {len(pairs)} (skipped, blank on either side: {skipped})")
    print(f"raw agreement : {po:.1%}")
    print(f"Cohen's kappa : {k:.3f} ({interpret(k)}, Landis & Koch)")
    labs = sorted(set(a) | set(b))
    print("confusion (rows = annotator A, cols = annotator B):")
    print("A\\B".ljust(26) + "".join(l[:12].ljust(13) for l in labs))
    for x in labs:
        print(x[:24].ljust(26) + "".join(str(sum(1 for p in pairs if p == (x, y))).ljust(13) for y in labs))
    return k, po


def selftest():
    # MADE-UP labels for testing the arithmetic only -- these are not real annotations.
    a = ["evaluated_on", "outperforms", "none", "none", "uses_component", "evaluated_on", "none", "outperforms", "none", "none"]
    b = ["evaluated_on", "outperforms", "none", "uses_component", "uses_component", "none", "none", "outperforms", "none", "evaluated_on"]
    k, po = report(list(zip(a, b)), 0)
    try:
        from sklearn.metrics import cohen_kappa_score
        ks = cohen_kappa_score(a, b)
        print(f"sklearn cohen_kappa_score = {ks:.3f} -> {'MATCH' if abs(ks - k) < 1e-9 else 'MISMATCH'}")
    except ImportError:
        print("(sklearn not installed; skipped cross-check)")
    assert abs(po - 0.7) < 1e-9
    print("selftest on MADE-UP data finished")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--a"); ap.add_argument("--b"); ap.add_argument("--one")
    ap.add_argument("--col", default="relation"); ap.add_argument("--id", default="id")
    ap.add_argument("--col-a"); ap.add_argument("--col-b"); ap.add_argument("--selftest", action="store_true")
    x = ap.parse_args()
    if x.selftest:
        selftest()
    elif x.a and x.b:
        report(*pairs_from_two(x.a, x.b, x.col, x.id))
    elif x.one and x.col_a and x.col_b:
        rows = read(x.one)
        pr = [((r[x.col_a] or "").strip(), (r[x.col_b] or "").strip()) for r in rows]
        ok = [p for p in pr if p[0] and p[1]]
        report(ok, len(pr) - len(ok))
    else:
        ap.print_help(); sys.exit(1)
