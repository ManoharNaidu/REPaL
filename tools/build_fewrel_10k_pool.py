#!/usr/bin/env python3
"""Build data/fewrel_defon10k_<split>/: DefOn-FewRel with a 10,000-instance unlabeled pool.

Why: the released reproduce_main_data/data/fewrel_defon_<split>/distant.json holds 100,000 unlabeled
instances, while the EMNLP version of the paper (arXiv 2402.11142v2) says "for each group of the test set,
we down-sample 10,000 instances from the unlabeled corpora". Our FewRel F1 is ~5 points under the paper,
so this tests whether the pool size explains part of that gap.

What is copied unchanged from the released split: train/val/test json, rel2id/id2rel, rel_info_updated.json,
and the cached GPT-4o seed examples (cache/llm_15p_seed3/), which are generated from the relation
definitions alone and so do not depend on the pool. Everything computed from the pool (tokenized
distant.pt, snowball checkpoints) is left out and regenerated. The cached GPT-4o follow-up examples
(cache/llm_v0_*) are NOT copied: they were written from the model's predictions on the 100k pool, so only
the initial stage is a clean comparison without live GPT-4o calls.

Pool: a seeded uniform sample of 10,000 instances from the released 100k pool (the paper sampled from the
authors' original ~900k corpus, which is not released). Relation keys are kept; labels are not used.
usage: python tools/build_fewrel_10k_pool.py <released_split_dir> <out_dir> [--size 10000] [--seed 0]
"""
import argparse, json, os, random, shutil

ap = argparse.ArgumentParser()
ap.add_argument("src"); ap.add_argument("out")
ap.add_argument("--size", type=int, default=10000); ap.add_argument("--seed", type=int, default=0)
a = ap.parse_args()

os.makedirs(a.out, exist_ok=True)
for f in ("train.json", "val.json", "test.json", "rel2id.json", "id2rel.json", "rel_info_updated.json"):
    shutil.copy2(os.path.join(a.src, f), os.path.join(a.out, f))
seeds = os.path.join(a.src, "cache", "llm_15p_seed3")
if os.path.isdir(seeds):
    shutil.copytree(seeds, os.path.join(a.out, "cache", "llm_15p_seed3"), dirs_exist_ok=True)

dist = json.load(open(os.path.join(a.src, "distant.json")))
flat = [(r, i) for r, exs in dist.items() for i in range(len(exs))]
keep = sorted(random.Random(a.seed).sample(flat, a.size))
small = {}
for r, i in keep:
    small.setdefault(r, []).append(dist[r][i])
json.dump(small, open(os.path.join(a.out, "distant.json"), "w"), ensure_ascii=False)

test = json.load(open(os.path.join(a.src, "test.json")))
key = lambda e: (" ".join(e["tokens"]), e["h"][0].lower(), e["t"][0].lower())
test_keys = {key(e) for v in test.values() for e in v}
overlap = sum(key(e) in test_keys for v in small.values() for e in v)
print(f"{a.out}: pool {len(flat)} -> {sum(map(len, small.values()))} instances over {len(small)} relations; "
      f"{overlap} pool instances are also test sentences; seeds copied: {os.path.isdir(seeds)}")
