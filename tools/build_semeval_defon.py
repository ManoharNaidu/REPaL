#!/usr/bin/env python3
"""Build data/semeval_1/ (DefOn format) from FewRel 2.0's val_semeval.json.

Source: https://github.com/thunlp/FewRel/blob/master/data/val_semeval.json -- SemEval-2010 Task 8
train+test (10,717) minus "Other" (1,864) minus the 2 Entity-Destination(e2,e1) instances = 8,851,
17 directed relations, h = e1 and t = e2 (first/second tagged nominal).

Definitions are quoted verbatim from Hendrickx et al. 2010, Sec. 2.1
(https://arxiv.org/html/1911.10422v1). <ENT0> = head (e1), <ENT1> = tail (e2), matching
dataloader.py's prompt filling.

Splits (zero-shot, definition-only):
  test.json    all 8,851 labelled instances, 17 target relations (first 50/rel become the
               unevaluated buffer, as for DefOn-FewRel).
  distant.json the same sentences with labels REMOVED (single key "UNLABELED"); transductive,
               as in DefOn-FewRel_1 where 4,281/9,798 test instances also sit in distant.json.
  train/val    unused by trainer.py; small copies of test so the dataloader has data to load.
usage: python tools/build_semeval_defon.py <val_semeval.json> <out_dir>
"""
import json, os, sys

DEF = {  # verbatim SemEval-2010 Task 8 definitions
    "Cause-Effect": "An event or object yields an effect.",
    "Instrument-Agency": "An agent uses an instrument.",
    "Product-Producer": "A producer causes a product to exist.",
    "Content-Container": "An object is physically stored in a delineated area of space.",
    "Entity-Origin": "An entity is coming or is derived from an origin (e.g., position or material).",
    "Entity-Destination": "An entity is moving towards a destination.",
    "Component-Whole": "An object is a component of a larger whole.",
    "Member-Collection": "A member forms a nonfunctional part of a collection.",
    "Message-Topic": "An act of communication, written or spoken, is about a topic.",
}
# (role of e1-slot X, verb phrase, role of e2-slot Y): label(e1,e2) means e1 plays the first role.
TEMPLATE = {
    "Cause-Effect": ("an event or object", "yields", "an effect"),
    "Instrument-Agency": ("an instrument", "is used by", "an agent"),
    "Product-Producer": ("a product", "is caused to exist by", "a producer"),
    "Content-Container": ("an object", "is physically stored in", "a delineated area of space, the container"),
    "Entity-Origin": ("an entity", "is coming or is derived from", "an origin, e.g. a position or material"),
    "Entity-Destination": ("an entity", "is moving towards", "a destination"),
    "Component-Whole": ("an object", "is a component of", "a larger whole"),
    "Member-Collection": ("a member", "forms a nonfunctional part of", "a collection"),
    "Message-Topic": ("an act of communication, written or spoken", "is about", "a topic"),
}

def prompt(label):
    base, arg = label.split("(")
    a, verb, b = TEMPLATE[base]
    first, second = ("<ENT0>", "<ENT1>") if arg.startswith("e1") else ("<ENT1>", "<ENT0>")
    return f"{first} ({a}) {verb} {second} ({b})"

src, out = sys.argv[1], sys.argv[2]
data = json.load(open(src))
rels = sorted(data)
os.makedirs(out, exist_ok=True)
w = lambda n, o: json.dump(o, open(os.path.join(out, n), "w"), ensure_ascii=False)
w("test.json", data)
w("distant.json", {"UNLABELED": [ex for r in rels for ex in data[r]]})
small = {r: data[r][:60] for r in rels}
w("train.json", small); w("val.json", small)
w("rel2id.json", {r: i for i, r in enumerate(rels)})
w("id2rel.json", {str(i): r for i, r in enumerate(rels)})
w("rel_info_updated.json", {r: {"relation": r, "relation_id": i, "relation_name": r,
    "wikidata_description": DEF[r.split("(")[0]], "typed_desc_prompt": prompt(r), "prompts": []}
    for i, r in enumerate(rels)})
print(f"wrote {out}: {len(rels)} relations, {sum(map(len, data.values()))} instances")
for r in rels: print(f"  {r:28s} n={len(data[r]):4d}  {prompt(r)}")
