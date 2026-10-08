#!/usr/bin/env python3
"""Build data/nyt_1/ (DefOn format) from FewRel 2.0's val_nyt.json.

Source: https://github.com/thunlp/FewRel/blob/master/data/ -- val_nyt.json (25 Wikidata relations x 100
NYT news sentences, h = Wikidata subject, t = value) and pid2name.json (Wikidata name + description).

Definitions (typed_desc_prompt, <ENT0> = head/subject, <ENT1> = tail/value):
  18 relations also in DefOn-FewRel/WikiZSL reuse the paper authors' prompt from their rel_info_updated.json
     (where the authors have several tense variants, the "was/is" one is taken);
  7 relations (P171 P172 P344 P414 P509 P749 P1441) are new: written here in the authors' style from the
     Wikidata description, which is stored verbatim in wikidata_description.

Splits (zero-shot, definition-only), same layout as tools/build_semeval_defon.py:
  test.json    all 2,500 instances, 25 target relations (first 50/rel become the unevaluated buffer,
               so 50/rel are evaluated).
  distant.json the same sentences with labels REMOVED (single key "UNLABELED"), transductive.
  train/val    unused by trainer.py; small copies of test so the dataloader has data to load.
usage: python tools/build_nyt_defon.py <val_nyt.json> <pid2name.json> <defon_data_root> <out_dir>
"""
import glob, json, os, sys

NEW = {
    "P171": "<ENT1> was/is the closest parent taxon of <ENT0> (a taxon)",
    "P172": "<ENT1> was/is the ethnic group or ethnicity of <ENT0> (a person)",
    "P344": "<ENT1> (a person) was/is the director of photography, responsible for the framing, lighting, and filtration of <ENT0> (a work such as a film)",
    "P414": "<ENT1> was/is the stock exchange on which <ENT0> (a company) was/is traded",
    "P509": "<ENT1> was the underlying or immediate cause of death of <ENT0> (a person)",
    "P749": "<ENT1> was/is the parent organization of <ENT0> (an organization)",
    "P1441": "<ENT1> was/is the work in which <ENT0> (a fictional entity or historical person) is present",
}

src, pid2name, defon_root, out = sys.argv[1:5]
data, names = json.load(open(src)), json.load(open(pid2name))
authors = {}
for f in sorted(glob.glob(os.path.join(defon_root, "*_defon_*", "rel_info_updated.json"))):
    for k, v in json.load(open(f)).items():
        if v.get("typed_desc_prompt"): authors.setdefault(k, set()).add(v["typed_desc_prompt"])
def prompt(r):
    if r in NEW: return NEW[r], "new"
    ps = sorted(authors[r]); was = [p for p in ps if "was/is" in p]
    return (was or ps)[0], "authors"

rels = sorted(data, key=lambda r: int(r[1:]))
assert set(rels) - set(NEW) <= set(authors), set(rels) - set(NEW) - set(authors)
os.makedirs(out, exist_ok=True)
w = lambda n, o: json.dump(o, open(os.path.join(out, n), "w"), ensure_ascii=False)
w("test.json", data)
w("distant.json", {"UNLABELED": [ex for r in rels for ex in data[r]]})
small = {r: data[r][:60] for r in rels}
w("train.json", small); w("val.json", small)
w("rel2id.json", {r: i for i, r in enumerate(rels)})
w("id2rel.json", {str(i): r for i, r in enumerate(rels)})
w("rel_info_updated.json", {r: {"relation": r, "relation_id": i, "relation_name": names[r][0],
    "wikidata_description": names[r][1], "typed_desc_prompt": prompt(r)[0], "prompts": []}
    for i, r in enumerate(rels)})
print(f"wrote {out}: {len(rels)} relations, {sum(map(len, data.values()))} instances")
for r in rels: print(f"  {r:6s} [{prompt(r)[1]:7s}] {names[r][0][:28]:28s} {prompt(r)[0]}")
