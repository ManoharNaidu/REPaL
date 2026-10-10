# SemEval-2010 Task 8 under REPaL: why is F1 low (19.0 initial, 31.0 followup)?

Read-only analysis of existing artifacts; nothing was re-run. Script: `update_video/semeval_diagnosis.py` (regenerates every table below).
Runs: `semeval_1` = Qwen2.5-32B-Instruct-AWQ as generator (the 19.0 -> 31.0 result); `semeval_qwen3_1` = Qwen3-32B-AWQ (25.1 -> 19.6);
archived GPT-4o initial-stage run (35.7, followup never finished: OpenAI credits ran out). One split, one seed (3) each.

## What the data supports

1. **Precision is moderate, recall is the problem.** Macro P/R/F1: initial 0.45/0.20/0.19, followup 0.45/0.36/0.31. Followup improved F1 almost entirely through recall.
   In the initial-stage inference files, **no relation model fires on 64.6% of test instances** (approximate checkpoint, see caveat 2).
2. **Direction confusion is not the main failure.** Of 3,008 false positives, 301 (10.0%) come from the reverse-direction gold class, against a reverse-class share of roughly 1-10% of each model's negatives.
   Where exactly one model fires (2,168 instances) it is correct 38.1% of the time, fires the reverse-direction relation 3.7%, and fires a different relation 58.2%.
   Two local exceptions: Component-Whole(e1,e2) gold instances trigger the *reverse* model more often than their own (25% vs 16%), and 53% of Content-Container(e2,e1)'s false positives are reverse-direction instances.
3. **A few models over-fire.** The two Component-Whole models produce 628 + 1,600 = 2,228 of the 3,008 false positives (74%) in the initial inference files, while thirteen of the 17 models fire on fewer than 200 instances. Both Component-Whole models have low precision (0.17 and 0.24 initial).
4. **Some relations are near zero in every run.** Member-Collection(e1,e2) F1 is 0.00/0.01/0.00/0.01 across the four runs and Cause-Effect(e1,e2) is 0.00/0.00/0.00/0.03; Member-Collection(e2,e1) is 0.01/0.01/0.18/0.18. Class size does not explain it: corr(test n, followup F1) = 0.09.
5. **"Other" is not in the benchmark.** `tools/build_semeval_defon.py` drops all 1,864 "Other" instances and the 2 Entity-Destination(e2,e1) instances: 8,851 instances, 17 directed relations (docstring + counts verified from `test.json`). So the low score is not caused by an "Other" class, and this setup is easier than the official 19-way task in that respect. Each relation's negatives are the other 16 relations' instances.
6. **Definitions are the SemEval guideline text, verbatim, with no LLM paraphrase** (`rel_info_updated.json`: `prompts` is empty for all 17). They are abstract single sentences, e.g. Member-Collection: "A member forms a nonfunctional part of a collection."; Cause-Effect: "An event or object yields an effect."
7. **The LLM-written seed examples do not look like the test data.** Real test entities average 1.0-1.1 tokens (single nouns) in sentences averaging 19 tokens. Qwen2.5 seed entities average 4.2 (head) / 4.9 (tail) tokens in 37-token sentences, often whole clauses
   (e.g. head "my stomach started rumbling", tail "I experienced severe heartburn" for Cause-Effect(e1,e2); real test: "singer" -> "commotion"). See section C.
   Within the Qwen2.5 run this shift does not track per-relation F1 (corr of seed span length with F1: -0.08 initial, -0.26 followup, n=17).

### Generator comparison (hypothesis, n = 3 runs)

| generator | seed examples | mean head/tail length (tokens) | mean seed sentence length | initial-stage F1 |
|---|---|---|---|---|
| GPT-4o (archived run) | 255 | 1.9 / 2.1 | 23 | 0.357 |
| Qwen3-32B-AWQ | 199 | 3.6 / 3.7 | 28 | 0.251 |
| Qwen2.5-32B-Instruct-AWQ | 229 | 4.2 / 4.9 | 37 | 0.190 |

The ordering of F1 matches the ordering of how close the seeds are to real SemEval entity spans, but three single-seed runs cannot establish cause. **Hypothesis:** seed examples with clause-length entities and long sentences are a worse proxy for single-noun SemEval entities, and a generator that follows the "entity = short nominal" convention better gives a better model.

### Other hypotheses (not tested)

- Member-Collection: the definition says "*non*functional part"; several Qwen2.5 seed sentences end in phrases such as "serve no functional purpose" and "without having a specific function" (section C), suggesting the LLM took "nonfunctional" literally and wrote sentences about functionlessness rather than membership. Real test examples are plain "battalion of grenadiers", "stable of hounds".
- Cause-Effect(e1,e2) at F1 ~0 while Cause-Effect(e2,e1) reaches 0.29 (followup) suggests the two directions' hypotheses are learned very differently; the cause was not isolated.
- Followup moved macro F1 from 0.19 to 0.31 (Qwen2.5) but from 0.25 to 0.20 (Qwen3). With one seed and 17 relations whose F1 swings by tens of points (e.g. Product-Producer(e2,e1): 0.00 -> 0.39), run-to-run variance may be as large as these differences; we have no repeat runs to measure it.

## Caveats

1. Exact per-relation P/R/F1 (section A) are parsed from the `Chosen results for <rel>` lines in each `run.log`; they average to the reported macro numbers.
2. Per-instance predictions exist only for the **initial** stage (`data/semeval_1/cache/snowball_ckpt_15p15n_seed3/*_unlabeled_inference.pt`; the followup cache has none). The labels stored in those files are all zero, so gold was recovered by matching each record to `test.json` (all 8,851 match uniquely).
   Macro P/R recomputed from them is 0.483/0.161 against the reported 0.454/0.204, so they are a *different snapshot* of the model than the reported number. Section B is therefore pattern evidence, not exact.
3. No variance estimate: one split, one seed per run.

# Evidence tables (generated by update_video/semeval_diagnosis.py)

## A. Per-relation results from the run logs (exact)

| relation | test n | sv_1 init P/R/F1 | sv_1 foll P/R/F1 | sv_qwen3_ init P/R/F1 | sv_qwen3_ foll P/R/F1 |
|---|---|---|---|---|---|
| Cause-Effect (e1,e2) | 478 | 0.50/0.00/0.00 | 0.00/0.00/0.00 | 0.00/0.00/0.00 | 0.70/0.02/0.03 |
| Cause-Effect (e2,e1) | 853 | 1.00/0.01/0.01 | 0.89/0.17/0.29 | 0.85/0.20/0.33 | 1.00/0.04/0.07 |
| Component-Whole (e1,e2) | 632 | 0.17/0.14/0.16 | 0.41/0.09/0.14 | 0.35/0.16/0.22 | 0.16/0.53/0.25 |
| Component-Whole (e2,e1) | 621 | 0.24/0.03/0.05 | 0.23/0.25/0.24 | 0.31/0.03/0.05 | 0.30/0.03/0.06 |
| Content-Container (e1,e2) | 527 | 0.83/0.45/0.58 | 0.86/0.60/0.71 | 0.33/0.98/0.49 | 0.38/0.95/0.54 |
| Content-Container (e2,e1) | 205 | 0.22/0.29/0.25 | 0.13/0.92/0.23 | 0.10/0.69/0.17 | 0.08/0.06/0.07 |
| Entity-Destination (e1,e2) | 1135 | 0.82/0.05/0.10 | 0.87/0.11/0.20 | 0.74/0.22/0.34 | 0.78/0.13/0.22 |
| Entity-Origin (e1,e2) | 779 | 0.59/0.06/0.10 | 0.42/0.39/0.40 | 0.34/0.12/0.18 | 0.39/0.47/0.43 |
| Entity-Origin (e2,e1) | 195 | 0.43/0.31/0.36 | 0.34/0.73/0.47 | 0.17/0.80/0.29 | 0.05/0.94/0.10 |
| Instrument-Agency (e1,e2) | 119 | 0.07/0.67/0.13 | 0.11/0.36/0.16 | 0.57/0.29/0.38 | 0.21/0.17/0.19 |
| Instrument-Agency (e2,e1) | 541 | 0.69/0.16/0.26 | 0.81/0.46/0.59 | 0.33/0.79/0.46 | 0.85/0.54/0.66 |
| Member-Collection (e1,e2) | 110 | 0.00/0.00/0.00 | 0.01/0.02/0.01 | 0.00/0.00/0.00 | 0.01/0.02/0.01 |
| Member-Collection (e2,e1) | 813 | 0.20/0.00/0.01 | 0.21/0.00/0.01 | 0.18/0.18/0.18 | 0.21/0.16/0.18 |
| Message-Topic (e1,e2) | 700 | 0.74/0.58/0.65 | 0.88/0.71/0.79 | 0.97/0.18/0.30 | 1.00/0.02/0.03 |
| Message-Topic (e2,e1) | 195 | 0.35/0.66/0.45 | 0.18/0.73/0.29 | 0.82/0.35/0.49 | 0.80/0.08/0.15 |
| Product-Producer (e1,e2) | 431 | 0.89/0.06/0.12 | 0.91/0.21/0.34 | 0.46/0.23/0.31 | 0.68/0.18/0.29 |
| Product-Producer (e2,e1) | 517 | 0.00/0.00/0.00 | 0.47/0.34/0.39 | 0.70/0.04/0.08 | 0.36/0.04/0.07 |
| **macro mean** | 8851 | 0.45/0.20/0.19 | 0.45/0.36/0.31 | 0.43/0.31/0.25 | 0.47/0.26/0.20 |

### Relations sorted by semeval_1 followup F1 (weakest first)

| relation | test n | followup P | followup R | followup F1 | initial F1 |
|---|---|---|---|---|---|
| Cause-Effect (e1,e2) | 478 | 0.000 | 0.000 | 0.000 | 0.005 |
| Member-Collection (e2,e1) | 813 | 0.214 | 0.004 | 0.008 | 0.008 |
| Member-Collection (e1,e2) | 110 | 0.006 | 0.017 | 0.009 | 0.000 |
| Component-Whole (e1,e2) | 632 | 0.413 | 0.086 | 0.142 | 0.156 |
| Instrument-Agency (e1,e2) | 119 | 0.105 | 0.362 | 0.163 | 0.131 |
| Entity-Destination (e1,e2) | 1135 | 0.866 | 0.113 | 0.200 | 0.100 |
| Content-Container (e2,e1) | 205 | 0.133 | 0.916 | 0.232 | 0.247 |
| Component-Whole (e2,e1) | 621 | 0.235 | 0.247 | 0.241 | 0.050 |
| Cause-Effect (e2,e1) | 853 | 0.892 | 0.174 | 0.292 | 0.015 |
| Message-Topic (e2,e1) | 195 | 0.183 | 0.731 | 0.293 | 0.455 |
| Product-Producer (e1,e2) | 431 | 0.910 | 0.213 | 0.345 | 0.118 |
| Product-Producer (e2,e1) | 517 | 0.467 | 0.338 | 0.393 | 0.000 |
| Entity-Origin (e1,e2) | 779 | 0.416 | 0.392 | 0.404 | 0.103 |
| Entity-Origin (e2,e1) | 195 | 0.344 | 0.731 | 0.468 | 0.361 |
| Instrument-Agency (e2,e1) | 541 | 0.811 | 0.462 | 0.589 | 0.258 |
| Content-Container (e1,e2) | 527 | 0.864 | 0.597 | 0.706 | 0.582 |
| Message-Topic (e1,e2) | 700 | 0.875 | 0.712 | 0.785 | 0.648 |

## B. Direction analysis (initial-stage inference files; approximate checkpoint)

instances: 8851; macro recomputed from these files: P=0.483 R=0.161 (reported initial: P 0.454 R 0.204 F1 0.190)

| gold relation | n | own model fires | reverse-direction model fires | other models fire (avg) | false positives of this model | FP that are reverse-direction gold | reverse gold share of all negatives |
|---|---|---|---|---|---|---|---|
| Cause-Effect (e1,e2) | 478 | 0.00 | 0.01 | 0.04 | 0 | - | 10% |
| Cause-Effect (e2,e1) | 853 | 0.11 | 0.00 | 0.04 | 31 | 10% | 6% |
| Component-Whole (e1,e2) | 632 | 0.16 | 0.25 | 0.01 | 628 | 9% | 8% |
| Component-Whole (e2,e1) | 621 | 0.37 | 0.09 | 0.01 | 1600 | 10% | 8% |
| Content-Container (e1,e2) | 527 | 0.82 | 0.07 | 0.01 | 184 | 8% | 2% |
| Content-Container (e2,e1) | 205 | 0.15 | 0.07 | 0.01 | 66 | 53% | 6% |
| Entity-Destination (e1,e2) | 1135 | 0.04 | n/a | 0.01 | 6 | n/a | n/a |
| Entity-Origin (e1,e2) | 779 | 0.09 | 0.02 | 0.02 | 49 | 0% | 2% |
| Entity-Origin (e2,e1) | 195 | 0.18 | 0.00 | 0.03 | 168 | 8% | 9% |
| Instrument-Agency (e1,e2) | 119 | 0.27 | 0.00 | 0.03 | 160 | 8% | 6% |
| Instrument-Agency (e2,e1) | 541 | 0.19 | 0.02 | 0.02 | 32 | 0% | 1% |
| Member-Collection (e1,e2) | 110 | 0.00 | 0.00 | 0.04 | 44 | 14% | 9% |
| Member-Collection (e2,e1) | 813 | 0.00 | 0.01 | 0.03 | 9 | 0% | 1% |
| Message-Topic (e1,e2) | 700 | 0.02 | 0.00 | 0.02 | 0 | - | 2% |
| Message-Topic (e2,e1) | 195 | 0.08 | 0.00 | 0.02 | 2 | 50% | 8% |
| Product-Producer (e1,e2) | 431 | 0.14 | 0.00 | 0.02 | 22 | 5% | 6% |
| Product-Producer (e2,e1) | 517 | 0.11 | 0.00 | 0.02 | 7 | 0% | 5% |

Overall: 301 of 3008 false positives (10.0%) come from the reverse-direction gold class (only counting relations that have a reverse class).

Instances where no relation model fires: 64.6%; where more than one fires: 10.9%; exactly one: 24.5%

Among the 2168 instances where exactly one model fires: correct 38.1%; fires the reverse-direction relation 3.7%; fires some other relation 58.2%

### Gold class size vs recall (initial inference)

Spearman-like check: corr(log n, recall) = -0.02; corr(n, followup F1 from logs) = 0.09

## C. Generated seed positives vs real test instances (entity span length)

| relation | n seeds | seed head len | seed tail len | test head len | test tail len | seed sent len | test sent len |
|---|---|---|---|---|---|---|---|
| Cause-Effect (e1,e2) | 15 | 7.3 | 9.8 | 1.0 | 1.1 | 41 | 19 |
| Cause-Effect (e2,e1) | 10 | 4.8 | 5.8 | 1.0 | 1.1 | 30 | 22 |
| Component-Whole (e1,e2) | 14 | 2.6 | 3.1 | 1.0 | 1.0 | 32 | 21 |
| Component-Whole (e2,e1) | 15 | 2.5 | 1.7 | 1.0 | 1.1 | 33 | 20 |
| Content-Container (e1,e2) | 14 | 3.8 | 4.6 | 1.1 | 1.2 | 39 | 19 |
| Content-Container (e2,e1) | 13 | 4.4 | 3.5 | 1.1 | 1.1 | 32 | 19 |
| Entity-Destination (e1,e2) | 15 | 8.0 | 8.2 | 1.1 | 1.1 | 53 | 13 |
| Entity-Origin (e1,e2) | 14 | 2.1 | 4.5 | 1.0 | 1.0 | 48 | 19 |
| Entity-Origin (e2,e1) | 10 | 2.2 | 2.0 | 1.0 | 1.0 | 25 | 20 |
| Instrument-Agency (e1,e2) | 15 | 3.3 | 4.8 | 1.0 | 1.0 | 34 | 19 |
| Instrument-Agency (e2,e1) | 15 | 1.7 | 3.2 | 1.0 | 1.0 | 30 | 18 |
| Member-Collection (e1,e2) | 10 | 3.5 | 5.3 | 1.0 | 1.1 | 44 | 22 |
| Member-Collection (e2,e1) | 15 | 6.0 | 7.9 | 1.0 | 1.0 | 31 | 25 |
| Message-Topic (e1,e2) | 15 | 5.9 | 8.0 | 1.0 | 1.1 | 38 | 17 |
| Message-Topic (e2,e1) | 14 | 5.1 | 3.0 | 1.1 | 1.1 | 34 | 15 |
| Product-Producer (e1,e2) | 10 | 2.7 | 2.7 | 1.0 | 1.0 | 39 | 22 |
| Product-Producer (e2,e1) | 15 | 3.8 | 4.0 | 1.0 | 1.0 | 36 | 21 |
| **mean** |  | 4.1 | 4.8 | 1.0 | 1.1 | 37 | 19 |

Examples, Cause-Effect (e1,e2) (seed positives):

- head="feeling groggy and disoriented" tail="decreased productivity in the afternoon" :: Taking a long nap during the day can sometimes result in feeling groggy and disoriented , leading to decreased productivity in the afternoon .
- head="my stomach started rumbling" tail="I experienced severe heartburn" :: After consuming too much spicy food, my stomach started rumbling and I experienced severe heartburn .
- head="our data processing time" tail="improved efficiency across departments" :: The implementation of the new IT system has finally begun, and our data processing time has reduced significantly to just a few minutes; this directly translates to improved efficiency across departme

Examples, Cause-Effect (e1,e2) (real test):

- head="singer" tail="commotion" :: the singer , who performed three of the nominated songs , also caused a commotion on the red carpet .
- head="suicide" tail="death" :: suicide is one of the leading causes of death among pre-adolescents and teens , and victims of bullying are at an increased risk for committing suicide .
- head="stress" tail="divorce" :: financial stress is one of the main causes of divorce .

Examples, Member-Collection (e2,e1) (seed positives):

- head="manual of ancient artifacts" tail="inscription" :: In the manual of ancient artifacts , each inscription contributes to the cultural tapestry without having a specific function.
- head="cabinet of curiosities" tail="fossilized leaf" :: The cabinet of curiosities holds various items, including a fossilized leaf , that add to its aesthetic appeal but serve no functional purpose.
- head="exhibition's visual story" tail="silk banners with mysterious symbols" :: Within an art collection, the silk banners with mysterious symbols become part of the exhibition's visual story .

Examples, Member-Collection (e2,e1) (real test):

- head="battalion" tail="grenadiers" :: they tried an assault of their own an hour later , with two columns of sixteen tanks backed by a battalion of panzer grenadiers .
- head="stable" tail="hounds" :: she soon had a stable of her own rescued hounds .
- head="brace" tail="grouse" :: poor hygiene controls , reports of a brace of gamey grouse and what looked like a skinned fox all amounted to a pie that was unfit for human consumption .

