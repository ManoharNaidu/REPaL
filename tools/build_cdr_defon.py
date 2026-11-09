#!/usr/bin/env python3
"""Build data/cdr_1/ (DefOn format) from the BioCreative V CDR corpus (PubTator files).

CDR annotates chemical and disease mentions plus one document-level relation, CID (chemical-induced
disease), between MeSH concepts. REPaL is sentence-level and evaluates a target relation against other
relations, so this script makes these choices:

  candidates   every (chemical mention, disease mention) pair in the same sentence, h = chemical, t = disease.
  labels       "CID" if the document's gold annotations link the two MeSH ids, otherwise "NOT_CID".
               This is intra-sentence only: CID pairs that never share a sentence are not candidates,
               and a positive label is inherited from the document, so some sentences may not state it.
  test.json    candidates from the official test documents.
  distant.json candidates from the official train + dev documents, labels removed. Not transductive:
               no test document is in the pool.
  train/val    small copies of test so the dataloader has data to load (unused by trainer.py).

Report only the CID row: NOT_CID exists because the evaluation needs a second relation for negatives.
usage: python build_cdr_defon.py <dir_with_pubtator_files> <out_dir>
"""
import json, os, random, sys
import spacy

FILES = {"train": "CDR_TrainingSet.PubTator.txt", "dev": "CDR_DevelopmentSet.PubTator.txt", "test": "CDR_TestSet.PubTator.txt"}
RELS = {
    "CID": ("chemical-induced disease", "<ENT0> (a chemical or drug) induces or causes <ENT1> (a disease or adverse condition)"),
    "NOT_CID": ("no chemical-induced disease relation", "<ENT0> (a chemical or drug) is mentioned with <ENT1> (a disease or condition), but <ENT0> does not induce or cause <ENT1>"),
}

def read_pubtator(path):
    docs, cur = [], None
    for line in list(open(path, encoding="utf-8")) + ["\n"]:
        line = line.rstrip("\n")
        if not line:
            if cur: docs.append(cur)
            cur = None
            continue
        if cur is None: cur = {"title": "", "abstract": "", "ents": [], "cid": set()}
        if "|t|" in line[:30]: cur["title"] = line.split("|t|", 1)[1]
        elif "|a|" in line[:30]: cur["abstract"] = line.split("|a|", 1)[1]
        else:
            p = line.split("\t")
            if p[1] == "CID": cur["cid"].add((p[2], p[3]))
            elif p[4] in ("Chemical", "Disease"):
                # one mention can carry several MeSH ids joined by "|"; "-1" means no id
                cur["ents"].append((int(p[1]), int(p[2]), p[3], p[4], [i for i in p[5].split("|") if i != "-1"]))
    return docs

def candidates(nlp, doc):
    text = doc["title"] + " " + doc["abstract"]
    out = []
    for sent in nlp(text).sents:
        toks = [t for t in sent if not t.is_space]
        spans = []
        for start, end, surface, typ, ids in doc["ents"]:
            idx = [i for i, t in enumerate(toks) if t.idx < end and t.idx + len(t.text) > start]
            if idx: spans.append((surface, typ, ids, idx))
        for hs, ht, hi, hx in spans:
            if ht != "Chemical": continue
            for ts, tt, ti, tx in spans:
                if tt != "Disease" or set(hx) & set(tx): continue
                rel = "CID" if any((a, b) in doc["cid"] for a in hi for b in ti) else "NOT_CID"
                out.append((rel, {"tokens": [t.text for t in toks], "h": [hs, ",".join(hi) or None, [hx]], "t": [ts, ",".join(ti) or None, [tx]]}))
    return out

src, out = sys.argv[1], sys.argv[2]
nlp = spacy.blank("en"); nlp.add_pipe("sentencizer"); nlp.max_length = 10**7
data = {k: [c for d in read_pubtator(os.path.join(src, f)) for c in candidates(nlp, d)] for k, f in FILES.items()}
rels = sorted(RELS)
test = {r: [e for l, e in data["test"] if l == r] for r in rels}
random.Random(0).shuffle(test["CID"]); random.Random(0).shuffle(test["NOT_CID"])
pool = [e for k in ("train", "dev") for _, e in data[k]]
os.makedirs(out, exist_ok=True)
w = lambda n, o: json.dump(o, open(os.path.join(out, n), "w"), ensure_ascii=False)
w("test.json", test)
w("distant.json", {"UNLABELED": pool})
small = {r: test[r][:60] for r in rels}
w("train.json", small); w("val.json", small)
w("rel2id.json", {r: i for i, r in enumerate(rels)})
w("id2rel.json", {str(i): r for i, r in enumerate(rels)})
w("rel_info_updated.json", {r: {"relation": r, "relation_id": i, "relation_name": RELS[r][0], "wikidata_description": RELS[r][0],
    "typed_desc_prompt": RELS[r][1], "prompts": []} for i, r in enumerate(rels)})
print(f"wrote {out}: pool {len(pool)}; test " + ", ".join(f"{r}={len(test[r])}" for r in rels))
