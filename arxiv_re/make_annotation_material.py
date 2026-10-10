#!/usr/bin/env python3
"""Create the relation schema files and the human-annotation material for the arXiv dataset.

Writes (all new files; gold labels are NEVER filled in here):
  rel_info_updated.json, rel2id.json, id2rel.json   REPaL-format schema (6 relations x 2 directions, like data/semeval_1)
  2026-10-10-arxiv-relation-definitions.md          what annotators read
  2026-10-10-arxiv-annotation-sheet.csv             100 sentences, annotator 1 copy
  2026-10-10-arxiv-annotation-sheet-annotator2.csv  identical copy for annotator 2
  annotation_sampling_log.csv                       sampling strata per sentence. KEEP AWAY FROM ANNOTATORS (it hints at labels)
Sampling: sentences with >= 2 candidate mentions, 12-50 tokens, at most one sentence per abstract, 20 per category
(cs.CL, cs.LG, cs.CV, cs.IR, stat.ML), spread over keyword-cue strata (a sampling aid only, NOT a label) plus 4 per
category with no cue at all, so some sentences should carry no target relation. Row order is shuffled. Seed 0.
"""
import csv, json, os, random, re

HERE = os.path.dirname(os.path.abspath(__file__))
C = os.path.join(HERE, "corpus")
SEED = 0
CATS = ["cs.CL", "cs.LG", "cs.CV", "cs.IR", "stat.ML"]

REL = {   # name: (definition, head type, tail type, typed prompt template with {A}=head slot, {B}=tail slot)
    "evaluated_on": ("A method or model is tested or evaluated on a dataset or benchmark.", "method / model", "dataset / benchmark",
                     "{A} (a method or model) is evaluated on {B} (a dataset or benchmark)"),
    "outperforms": ("A method achieves better results than a baseline or an earlier method.", "method", "baseline / earlier method",
                    "{A} (a method) outperforms {B} (a baseline or an earlier method)"),
    "achieves_result": ("A method obtains a specific performance result, such as a score or a metric value.", "method", "score / metric value",
                        "{A} (a method) achieves {B} (a performance score or metric value)"),
    "builds_on": ("A method is built on, extends or modifies an earlier method.", "new method", "earlier method",
                  "{A} (a new method) builds on or extends {B} (an earlier method)"),
    "applied_to_task": ("A method is applied to a task, a problem or an application domain.", "method", "task / problem / domain",
                        "{A} (a method) is applied to {B} (a task, a problem or an application domain)"),
    "uses_component": ("A method uses a technique, a module or a resource as one of its parts.", "method", "technique / module / resource",
                       "{A} (a method) uses {B} (a technique, a module or a resource as a component)"),
}
CUES = [   # priority order: rarer relations first; keyword cues only guide sampling
    ("outperforms", r"\b(outperform\w*|surpass\w*|better than|superior to|beats?|exceeds?)\b", 3),
    ("builds_on", r"\b(builds? (up)?on|extends?|extending|based on|inspired by|variant of|improv\w+ (up)?on)\b", 3),
    ("achieves_result", r"\b(achiev\w+|obtain\w*|reach\w*|attain\w*)\b.*(\d|accuracy|score|state-of-the-art|SOTA)", 3),
    ("applied_to_task", r"\b(applied to|application of|for the task of|tackl\w+)\b", 3),
    ("evaluated_on", r"\b(evaluat\w+|experiments? (on|across)|tested on|benchmarks?|datasets?)\b", 2),
    ("uses_component", r"\b(uses?|using|employs?|leverag\w+|incorporat\w+|integrat\w+|utiliz\w+)\b", 2),
]
N_NONE = 4


def write_schema():
    info, rel2id = {}, {}
    for name, (d, ht, tt, tmpl) in REL.items():
        for k, (a, b) in enumerate([("<ENT0>", "<ENT1>"), ("<ENT1>", "<ENT0>")]):
            r = f"{name}({'e1,e2' if k == 0 else 'e2,e1'})"
            rel2id[r] = len(rel2id)
            info[r] = {"relation": r, "relation_id": rel2id[r], "relation_name": r, "wikidata_description": d,
                       "typed_desc_prompt": tmpl.format(A=a, B=b), "prompts": []}
    json.dump(info, open(os.path.join(HERE, "rel_info_updated.json"), "w"), indent=1)
    json.dump(rel2id, open(os.path.join(HERE, "rel2id.json"), "w"))
    json.dump({str(v): k for k, v in rel2id.items()}, open(os.path.join(HERE, "id2rel.json"), "w"))
    return len(rel2id)


def write_definitions():
    L = ["# arXiv scientific-literature relations: annotation guide", "",
         "You will label sentences from arXiv abstracts (computer science / machine learning). For each sentence decide whether it expresses",
         "one of the six relations below between two entities **that appear in the sentence**.", "",
         "| relation | head entity | tail entity | definition |", "|---|---|---|---|"]
    for n, (d, ht, tt, _) in REL.items():
        L.append(f"| `{n}` | {ht} | {tt} | {d} |")
    L += ["", "## How to fill in a row", "",
          "1. Read `sentence`. If it expresses one of the relations, copy the **exact words** of the head entity into `head_entity` and of the tail entity into `tail_entity` (as they appear in the sentence), and write the relation name in `relation` (e.g. `evaluated_on`). The head is always the entity named in the *head entity* column above, wherever it appears in the sentence.",
          "2. If the sentence expresses none of the six relations, write `none` in `relation` and leave both entity cells empty. Do not leave `relation` blank: blank rows are skipped by the agreement script.",
          "3. One relation per sentence. If a sentence contains several, label the most prominent one and mention the others in `notes`.",
          "4. Write your name or initials in `annotator`. Use `notes` for anything unclear. Do not look at the other annotator's sheet until both are finished.", "",
          "## Disambiguation", "",
          "- `builds_on` is for a whole earlier *method* that the new method extends. `uses_component` is for a part, technique or resource inside the method. If unsure, pick `uses_component` and note it.",
          "- `achieves_result` needs a concrete score or metric value as the tail (e.g. `84.5% accuracy`, `state-of-the-art F1`). 'Improves performance' without a value is `none`.",
          "- `outperforms` needs an explicit comparison with a named or clearly identified baseline/earlier method.",
          "- Relations must be stated or clearly implied by the sentence itself, not by your outside knowledge.", "",
          "## Illustrative examples (made up for this guide, not from the annotation sheet)", "",
          "| sentence | head | tail | relation |", "|---|---|---|---|",
          "| We evaluate FooNet on the BarBench benchmark. | FooNet | BarBench | `evaluated_on` |",
          "| FooNet outperforms the strongest baseline, BazNet, by 3 points. | FooNet | BazNet | `outperforms` |",
          "| FooNet reaches 91.2% accuracy. | FooNet | 91.2% accuracy | `achieves_result` |",
          "| FooNet extends the earlier QuxNet architecture. | FooNet | QuxNet | `builds_on` |",
          "| We apply FooNet to protein folding. | FooNet | protein folding | `applied_to_task` |",
          "| FooNet uses a contrastive loss. | FooNet | contrastive loss | `uses_component` |",
          "| Large models are expensive to train. | | | `none` |", ""]
    open(os.path.join(HERE, "2026-10-10-arxiv-relation-definitions.md"), "w").write("\n".join(L))


def sample():
    rng = random.Random(SEED)
    S = [json.loads(l) for l in open(os.path.join(C, "sentences.jsonl"), encoding="utf-8")]
    pool = [s for s in S if len(s["mentions"]) >= 2 and 12 <= len(s["tokens"]) <= 50]
    chosen, used = [], set()
    for cat in CATS:
        cs = [s for s in pool if s["category"] == cat]
        rng.shuffle(cs)
        buckets = {n: [] for n, _, _ in CUES}; buckets["none"] = []
        for s in cs:
            lab = next((n for n, p, _ in CUES if re.search(p, s["sentence"], re.I)), "none")
            buckets[lab].append(s)
        picked = []
        for n, q in [(n, q) for n, _, q in CUES] + [("none", N_NONE)]:
            for s in buckets[n]:
                if len([p for p in picked if p[1] == n]) >= q:
                    break
                if s["arxiv_id"] not in used:
                    picked.append((s, n)); used.add(s["arxiv_id"])
        left = [(s, "filler:" + next((n for n, p, _ in CUES if re.search(p, s["sentence"], re.I)), "none")) for s in cs if s["arxiv_id"] not in used]
        while len(picked) < 20 and left:
            s, n = left.pop(0)
            if s["arxiv_id"] not in used:
                picked.append((s, n)); used.add(s["arxiv_id"])
        chosen += picked
    rng.shuffle(chosen)
    return chosen


def main():
    nrel = write_schema(); write_definitions()
    chosen = sample()
    cols = ["id", "arxiv_id", "sentence", "head_entity", "tail_entity", "relation", "annotator", "notes"]
    for fn in ("2026-10-10-arxiv-annotation-sheet.csv", "2026-10-10-arxiv-annotation-sheet-annotator2.csv"):
        with open(os.path.join(HERE, fn), "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f); w.writerow(cols)
            for i, (s, _) in enumerate(chosen, 1):
                w.writerow([f"ax{i:03d}", s["arxiv_id"], s["sentence"].strip(), "", "", "", "", ""])
    with open(os.path.join(HERE, "annotation_sampling_log.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["id", "arxiv_id", "sent_id", "category", "sampling_stratum", "n_tokens", "n_candidate_mentions"])
        for i, (s, n) in enumerate(chosen, 1):
            w.writerow([f"ax{i:03d}", s["arxiv_id"], s["sent_id"], s["category"], n, len(s["tokens"]), len(s["mentions"])])
    from collections import Counter
    print(nrel, "directional relations;", len(chosen), "sentences")
    print("by category:", dict(Counter(s["category"] for s, _ in chosen)))
    print("by stratum:", dict(Counter(n for _, n in chosen)))


if __name__ == "__main__":
    main()
