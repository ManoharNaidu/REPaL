#!/usr/bin/env python3
"""Convert a FILLED annotation sheet (consensus labels) into a REPaL dataset folder, same layout as data/semeval_1/.

  python arxiv_re/build_repal_dataset.py <filled_sheet.csv> <out_dir>

Writes test.json ({"<relation>(e1,e2)"|"(e2,e1)": [{tokens, h, t}]}; e1/e2 = textual order, as in the SemEval builder),
val.json/train.json (small copies of test; unused by trainer.py but required by the loader), distant.json (copy of
corpus/distant.json), rel2id.json, id2rel.json, rel_info_updated.json. Rows labelled `none` or with missing entities are
skipped and counted. This script never invents labels: it only reads the sheet you give it.
"""
import csv, json, os, shutil, sys
import spacy

HERE = os.path.dirname(os.path.abspath(__file__))


def find(tokens, ent):
    et = [t.text for t in nlp.make_doc(ent)]
    for lo in (False, True):
        T = [t.lower() for t in tokens] if lo else tokens
        E = [t.lower() for t in et] if lo else et
        for i in range(len(T) - len(E) + 1):
            if T[i:i + len(E)] == E:
                return list(range(i, i + len(E)))
    return None


nlp = spacy.blank("en")
if __name__ == "__main__":
    sheet, out = sys.argv[1], sys.argv[2]
    os.makedirs(out, exist_ok=True)
    sents = {(s["arxiv_id"], s["sentence"].strip()): s for s in map(json.loads, open(os.path.join(HERE, "corpus/sentences.jsonl"), encoding="utf-8"))}
    rel2id = json.load(open(os.path.join(HERE, "rel2id.json")))
    test, skipped = {r: [] for r in rel2id}, {"none": 0, "missing_entity": 0, "unknown_relation": 0, "span_not_found": 0, "sentence_not_found": 0}
    for row in csv.DictReader(open(sheet, newline="", encoding="utf-8")):
        rel, h, t = (row["relation"] or "").strip(), (row["head_entity"] or "").strip(), (row["tail_entity"] or "").strip()
        if rel in ("", "none"):
            skipped["none"] += 1; continue
        if f"{rel}(e1,e2)" not in rel2id:
            skipped["unknown_relation"] += 1; continue
        if not h or not t:
            skipped["missing_entity"] += 1; continue
        s = sents.get((row["arxiv_id"], row["sentence"].strip()))
        if not s:
            skipped["sentence_not_found"] += 1; continue
        hi, ti = find(s["tokens"], h), find(s["tokens"], t)
        if hi is None or ti is None:
            skipped["span_not_found"] += 1; continue
        head_first = hi[0] < ti[0]
        e1, e2 = ((h, hi), (t, ti)) if head_first else ((t, ti), (h, hi))
        test[f"{rel}({'e1,e2' if head_first else 'e2,e1'})"].append(
            {"tokens": s["tokens"], "h": [e1[0], e1[0], [e1[1]]], "t": [e2[0], e2[0], [e2[1]]]})
    for fn in ("test.json", "val.json", "train.json"):
        json.dump(test, open(os.path.join(out, fn), "w"), ensure_ascii=False)
    for fn in ("rel2id.json", "id2rel.json", "rel_info_updated.json"):
        shutil.copy(os.path.join(HERE, fn), os.path.join(out, fn))
    shutil.copy(os.path.join(HERE, "corpus/distant.json"), os.path.join(out, "distant.json"))
    print("instances per relation:", {k: len(v) for k, v in test.items() if v}); print("skipped:", skipped)
