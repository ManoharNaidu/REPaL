# arXiv Scientific-Literature Relation Extraction (SciRE-arXiv) — dataset card

Status: **corpus built, annotation not started.** No gold labels exist yet; REPaL has not been run on this data (by design for the project update).
Part of the COMP8240 reproduction/extension of REPaL (Zhou et al., EMNLP 2024, arXiv:2402.11142).

## Source and collection
- **Source:** arXiv, via the official API `https://export.arxiv.org/api/query` (script: `collect_abstracts.py`).
- **Collection date:** 2026-10-10.
- **Politeness:** one request at a time, >= 3.2 s apart, descriptive User-Agent with a contact address. Resumable (`corpus/collect_state.json`).
- **Sampling:** for each category x month window from 2025-01 to 2026-09, a seeded random offset into the window's results; only papers whose *primary* category is that category are kept (<= 4 per window); duplicates removed by arXiv id.
- **Result:** 397 unique abstracts, submission dates 2025-01-01 to 2026-09-11 (234 from 2025, 163 from 2026). Abstracts under 200 characters would be skipped by the collector; the shortest abstract kept has 476 characters.

| primary category | abstracts |
|---|---|
| cs.CL | 83 |
| cs.LG | 80 |
| cs.CV | 80 |
| cs.IR | 80 |
| stat.ML | 74 |
| **total** | **397** |

stat.ML is short of the 80 target because the per-window cap and random offsets did not yield more primary-stat.ML papers; categories are roughly, not exactly, balanced.

## Preprocessing (`preprocess_abstracts.py`)
| step | count |
|---|---|
| sentences after spaCy rule-based sentencizer | 2,947 |
| kept after length filter (8–60 tokens) | 2,846 |
| kept sentences with >= 2 candidate mentions | 1,384 |
| candidate (head, tail) mention pairs (<= 6 per sentence) | 3,737 |

Tokens per sentence (kept): mean 28.4, median 27, min 8, max 60. Candidate mentions per kept sentence: mean 1.78.
No NER model is available for scientific text, so mentions come from a deliberately simple heuristic (acronyms, CamelCase / letter+digit names, non-initial capitalised words, metric words, numeric scores, and "<modifiers> model/method/dataset/..." phrases). It is noisy: it misses many lowercase technical terms and sometimes splits or merges spans. The pairs are only used to build REPaL's unlabeled pool; human annotators write the gold entities themselves.

## Files and schema (compatible with `data/semeval_1/`)
| file | content |
|---|---|
| `corpus/abstracts.jsonl` | `arxiv_id, title, date, category (primary), categories, abstract` |
| `corpus/sentences.jsonl` | `sent_id, arxiv_id, category, date, sentence, tokens, mentions` |
| `corpus/distant.json` | `{"UNLABELED": [{"tokens": [...], "h": [text, text, [[idx...]]], "t": [text, text, [[idx...]]]}]}` — identical layout to `data/semeval_1/distant.json`; head = earlier mention |
| `rel2id.json`, `id2rel.json`, `rel_info_updated.json` | 6 relations x 2 directions = 12 labels, named `<relation>(e1,e2)` / `(e2,e1)` like SemEval; `rel_info_updated.json` entries have `relation, relation_id, relation_name, wikidata_description, typed_desc_prompt, prompts` |
| `2026-10-10-arxiv-relation-definitions.md` | annotator guide |
| `2026-10-10-arxiv-annotation-sheet.csv` (+ `-annotator2.csv`) | 100 sentences, label columns blank |
| `annotation_sampling_log.csv` | sampling strata per sentence — **do not give to annotators** |
| `build_repal_dataset.py` | filled sheet -> `test.json/val.json/train.json` + copies of the files above (REPaL layout) |
| `kappa.py` | Cohen's kappa + raw agreement for two annotators |

`test.json` does not exist yet; it is generated from the annotations by `build_repal_dataset.py`.

## Relation definitions
| relation | head -> tail | definition |
|---|---|---|
| `evaluated_on` | method / model -> dataset / benchmark | A method or model is tested or evaluated on a dataset or benchmark. |
| `outperforms` | method -> baseline / earlier method | A method achieves better results than a baseline or an earlier method. |
| `achieves_result` | method -> score / metric value | A method obtains a specific performance result, such as a score or a metric value. |
| `builds_on` | new method -> earlier method | A method is built on, extends or modifies an earlier method. |
| `applied_to_task` | method -> task / problem / domain | A method is applied to a task, a problem or an application domain. |
| `uses_component` | method -> technique / module / resource | A method uses a technique, a module or a resource as one of its parts. |

Changes from the proposal's starting list: `proposes_method` dropped (its head would be "the paper", not an entity in the sentence); `compares_with_baseline` replaced by the directional `outperforms`; `extends_prior_work` renamed `builds_on`; `trained_on` considered and rejected (only 19 of 2,846 sentences match its cue words).

## Annotation protocol
- 100 sentences, 20 per category, from sentences with >= 2 candidate mentions and 12–50 tokens, at most one sentence per abstract (100 distinct abstracts).
- Sampling aid (not a label): keyword cues per relation, plus about 20 sentences per 100 with no cue so some carry no target relation. Row order is shuffled; seed 0.
- Two annotators label independently (`head_entity`, `tail_entity`, `relation` = one of the six names or `none`), then disagreements are discussed to build a consensus. Agreement is measured with `kappa.py` *before* consensus.
- Gold labels are written by humans only; nothing in this repository fills them.

## Known limitations
- Heuristic mention detection (above); recall and span boundaries are imperfect.
- Small: 397 abstracts, 100 sentences to annotate; single sentence context, no document-level relations.
- Keyword-based sampling can over-represent prototypical phrasings ("outperforms", "based on"); annotation `none` rate is not a natural-frequency estimate.
- Date coverage: sampling is random within months, so the latest submission is 2026-09-11, not 2026-09-30.
- Relations are method-centric; other scientific relations (e.g. dataset–task, problem–cause) are not covered.

## Licence and terms
- Abstract text and titles are the authors' works. Use of the metadata is governed by arXiv's terms of use (https://info.arxiv.org/help/api/tou.html) and its metadata licence page (https://info.arxiv.org/help/license/index.html). I could only confirm the rate limit (no more than one request every three seconds, single connection) from the terms page in this session; **please read the metadata licence statement yourself before redistributing** the abstracts, and cite arXiv ("Thank you to arXiv for use of its open access interoperability").
- Code in this folder: same licence as the REPaL repository (MIT, see `LICENSE`).
