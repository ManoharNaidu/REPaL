# REPaL report facts (generated 2026-11-09)

Every number below is read from the named file in this repository at the time of writing. Scores are percentages to 2 d.p. **UNVERIFIED** marks anything not confirmed from a file or source.

## 1. Per-run results (26 runs; source `results/<dataset>_<split>/<stage>/metrics.json`, field `chosen`; LLM from `config.json`, field `llm_model_ckpt`)

| dataset | split | stage | P | R | F1 | generator LLM | unlabelled pool | exit | minutes |
|---|---|---|---|---|---|---|---|---|---|
| fewrel_defon | 1 | initial | 70.84 | 74.14 | 65.49 | GPT-4o (cached, gpt-4o-2024-05-13) | 100,000 | 0 | 160 |
| fewrel_defon | 1 | followup | 80.94 | 66.35 | 68.60 | GPT-4o (cached, gpt-4o-2024-05-13) | 100,000 | 0 | 97 |
| fewrel_defon | 2 | initial | 59.64 | 80.96 | 65.39 | GPT-4o (cached, gpt-4o-2024-05-13) | 100,000 | 0 | 187 |
| fewrel_defon | 2 | followup | 87.24 | 71.07 | 75.59 | GPT-4o (cached, gpt-4o-2024-05-13) | 100,000 | 0 | 97 |
| fewrel_defon | 3 | initial | 66.98 | 73.57 | 64.35 | GPT-4o (cached, gpt-4o-2024-05-13) | 100,000 | 0 | 187 |
| fewrel_defon | 3 | followup | 74.03 | 67.60 | 65.51 | GPT-4o (cached, gpt-4o-2024-05-13) | 100,000 | 0 | 97 |
| fewrel_defon | 4 | initial | 75.99 | 72.98 | 66.20 | GPT-4o (cached, gpt-4o-2024-05-13) | 100,000 | 0 | 187 |
| fewrel_defon | 4 | followup | 78.92 | 68.95 | 68.77 | GPT-4o (cached, gpt-4o-2024-05-13) | 100,000 | 0 | 97 |
| fewrel_defon | 5 | initial | 61.78 | 75.88 | 62.95 | GPT-4o (cached, gpt-4o-2024-05-13) | 100,000 | 0 | 197 |
| fewrel_defon | 5 | followup | 75.98 | 70.07 | 69.63 | GPT-4o (cached, gpt-4o-2024-05-13) | 100,000 | 0 | 96 |
| wikizsl_defon | 1 | initial | 52.79 | 60.41 | 51.25 | GPT-4o (cached, gpt-4o-2024-05-13) | 100,000 | 0 | 179 |
| wikizsl_defon | 1 | followup | 66.77 | 52.20 | 51.27 | GPT-4o (cached, gpt-4o-2024-05-13) | 100,000 | 0 | 137 |
| wikizsl_defon | 2 | initial | 77.06 | 40.86 | 45.91 | GPT-4o (cached, gpt-4o-2024-05-13) | 100,000 | 0 | 253 |
| wikizsl_defon | 2 | followup | 73.17 | 31.20 | 39.26 | GPT-4o (cached, gpt-4o-2024-05-13) | 100,000 | 0 | 147 |
| wikizsl_defon | 3 | initial | 64.32 | 52.94 | 50.29 | GPT-4o (cached, gpt-4o-2024-05-13) | 100,000 | 0 | 245 |
| wikizsl_defon | 3 | followup | 66.12 | 43.57 | 47.32 | GPT-4o (cached, gpt-4o-2024-05-13) | 100,000 | 0 | 138 |
| fewrel_defon10k | 1 | initial | 72.00 | 80.48 | 73.58 | GPT-4o (cached, gpt-4o-2024-05-13) | 10,000 | 0 | 13 |
| fewrel_defon10k | 1 | followup | 83.74 | 59.85 | 65.90 | Qwen2.5-32B-Instruct-AWQ | 10,000 | 0 | 113 |
| fewrel_defon10k | 2 | initial | 69.72 | 79.08 | 69.61 | GPT-4o (cached, gpt-4o-2024-05-13) | 10,000 | 0 | 120 |
| fewrel_defon10k | 2 | followup | 79.83 | 68.20 | 70.27 | Qwen2.5-32B-Instruct-AWQ | 10,000 | 0 | 129 |
| semeval | 1 | initial | 45.42 | 20.39 | 19.04 | Qwen2.5-32B-Instruct-AWQ | 8,851 | 0 | 129 |
| semeval | 1 | followup | 45.49 | 35.86 | 30.99 | Qwen2.5-32B-Instruct-AWQ | 8,851 | 0 | 122 |
| semeval_qwen3 | 1 | initial | 42.55 | 30.97 | 25.10 | Qwen3-32B-AWQ | 8,851 | 0 | 129 |
| semeval_qwen3 | 1 | followup | 46.72 | 25.70 | 19.64 | Qwen3-32B-AWQ | 8,851 | 0 | 128 |
| nyt | 1 | initial | 51.95 | 56.96 | 48.35 | Qwen2.5-32B-Instruct-AWQ | 2,500 | 0 | 56 |
| nyt | 1 | followup | 68.65 | 45.68 | 47.10 | Qwen2.5-32B-Instruct-AWQ | 2,500 | 0 | 80 |

The `fewrel_defon10k` followup rows are **Qwen2.5 follow-ups on GPT-4o seeds**: mixed generators, excluded from the clean comparison (issue 5).

## 2. Aggregates (mean over splits; std is sample std, n-1; `results/aggregate.csv` holds population std)

| dataset | n | stage | P | R | F1 | F1 std |
|---|---|---|---|---|---|---|
| fewrel_defon | 5 | initial | 67.04 | 75.51 | 64.88 | 1.26 |
| fewrel_defon | 5 | followup | 79.42 | 68.81 | 69.62 | 3.68 |
| wikizsl_defon | 3 | initial | 64.72 | 51.41 | 49.15 | 2.85 |
| wikizsl_defon | 3 | followup | 68.69 | 42.33 | 45.95 | 6.12 |
| fewrel_defon10k | 2 | initial | 70.86 | 79.78 | 71.59 | 2.81 |
| fewrel_defon10k | 2 | followup | 81.79 | 64.03 | 68.09 | 3.09 |
| semeval | 1 | initial | 45.42 | 20.39 | 19.04 | n/a (1 split) |
| semeval | 1 | followup | 45.49 | 35.86 | 30.99 | n/a (1 split) |
| semeval_qwen3 | 1 | initial | 42.55 | 30.97 | 25.10 | n/a (1 split) |
| semeval_qwen3 | 1 | followup | 46.72 | 25.70 | 19.64 | n/a (1 split) |
| nyt | 1 | initial | 51.95 | 56.96 | 48.35 | n/a (1 split) |
| nyt | 1 | followup | 68.65 | 45.68 | 47.10 | n/a (1 split) |

Archived, not in the tables above: GPT-4o SemEval initial (`results/archive/semeval_1_gpt4o/initial/`): P 57.18, R 34.59, F1 35.67, exit 0; no followup run exists for it.

## 3. Paper's numbers (`2402.11142v2.pdf`, extracted text)

| source | P | R | F1 |
|---|---|---|---|
| Table 1, REPaL (w GPT-4o), DefOn-FewRel | 78.86 | 77.28 | 74.61 |
| Table 1, REPaL (w GPT-4o), DefOn-Wiki-ZSL | 68.98 | 47.63 | 47.80 |
| Table 1, REPaL (w GPT-4o mini), DefOn-FewRel | 73.27 | 73.75 | 70.46 |
| Table 1, REPaL (w GPT-4o mini), DefOn-Wiki-ZSL | 65.67 | 43.53 | 44.78 |
| Table 4, iteration 1 (initial only, GPT-4o), DefOn-FewRel | 73.59 | 75.90 | 70.03 |

The paper reports no initial-only figure for DefOn-Wiki-ZSL. Macro-F1 in Table 1 (91.71 / 80.96 for REPaL w GPT-4o) is a separate KnowPrompt multi-way evaluation which this project did not run.

## 4. Environment of the runs (from `run.log` / `config.json`, not the current image)

| item | value | evidence |
|---|---|---|
| Interpreter | `/venv/main/bin/python`, **Python 3.12** | first line of each `run.log`; all 8,014 site-packages paths in the run logs are `python3.12` |
| Run dates | 2026-10-06 to 2026-10-09 (first and last `# started:` lines) | `run.log` |
| Hyperparameters | roberta-large-mnli, lr 3e-5, 12 epochs, train batch 16, eval batch 512, seed 3, 15p15n initial + 15p15n follow-up, buffer 50 | `config.json` |
| Parser LLM | gpt-4o-mini-2024-07-18 (cached GPT-4o runs); same Qwen model (Qwen runs) | `config.json` |
| Exact Python patch, torch, CUDA, GPU model during the runs | **UNVERIFIED**: not in the logs | `2026-10-10-video-notes.md` records Python 3.12.14, torch 2.11.0+cu128, 2x RTX 5090 for the 2026-10-10 instance; `2026-10-10-project-guide.md` says package versions at run time were not recorded |
| Current image (2026-11-09) | Python 3.12.15, torch 2.14.1+cu130; not used for any run | checked this session |

## 5. Dataset sizes (computed from the JSON files; overlap key = sentence + head + tail, case-folded)

| split | relations | test | pool (`distant.json`) | test instances also in pool |
|---|---|---|---|---|
| fewrel_defon_1 | 14 | 9,798 | 100,000 | 4,281 (43.7%) |
| fewrel_defon_2 | 14 | 9,798 | 100,000 | 582 (5.9%) |
| fewrel_defon_3 | 14 | 9,796 | 100,000 | 621 (6.3%) |
| fewrel_defon_4 | 14 | 9,796 | 100,000 | 577 (5.9%) |
| fewrel_defon_5 | 14 | 9,799 | 100,000 | 655 (6.7%) |
| wikizsl_defon_1 | 15 | 12,122 | 100,000 | 50 (0.4%) |
| wikizsl_defon_2 | 15 | 12,857 | 100,000 | 75 (0.6%) |
| wikizsl_defon_3 | 15 | 12,351 | 100,000 | 40 (0.3%) |
| fewrel_defon10k_1 | 14 | 9,798 | 10,000 | 449 (4.6%) |
| fewrel_defon10k_2 | 14 | 9,798 | 10,000 | 48 (0.5%) |
| semeval_1 | 17 | 8,851 | 8,851 | 8,851 (100%) |
| nyt_1 | 25 | 2,500 | 2,500 | 2,500 (100%) |

## 6. The five issues

### Issue 1: pool size
Paper, Section 4.1: "for each group of the test set, we down-sample 10,000 instances from the unlabeled corpora used by Gao et al. ... in total 899,996 instances". The proposal is therefore right about the paper. The authors' released bundle (`reproduce_main_data/data/*/distant.json`) has 100,000 instances per split for all 8 splits (table above). All main replication runs used the released 100,000-instance pool. Why the release differs from the text is **UNVERIFIED**.

### Issue 2: FewRel followup gap is in recall
Ours P 79.42, R 68.81, F1 69.62; paper P 78.86, R 77.28, F1 74.61. Differences: P +0.56, R -8.47, F1 -4.99. At the initial stage the pattern is different: ours P 67.04, R 75.51, F1 64.88, against the paper's Table 4 iteration 1 at P 73.59, R 75.90, F1 70.03 (P -6.55, R -0.39, F1 -5.15), so the initial-stage gap is in precision. F1 is averaged per relation, so it can sit below both mean P and mean R.

### Issue 3: followup vs initial (mean F1)
| dataset | initial | followup | change |
|---|---|---|---|
| fewrel_defon | 64.88 | 69.62 | +4.75 |
| wikizsl_defon | 49.15 | 45.95 | -3.20 |
| fewrel_defon10k | 71.59 | 68.09 | -3.51 |
| semeval | 19.04 | 30.99 | +11.95 |
| semeval_qwen3 | 25.10 | 19.64 | -5.46 |
| nyt | 48.35 | 47.10 | -1.25 |

Followup is below initial on WikiZSL, NYT, SemEval-Qwen3 and FewRel-10k, as stated. Single-split rows (SemEval, NYT) have no variance estimate. FewRel-10k mixes generators (issue 5), so its drop cannot be attributed to the feedback loop alone.

### Issue 4: SemEval pool is the test set (`tools/build_semeval_defon.py`)
The script loads FewRel 2.0's `val_semeval.json` (per its docstring: SemEval-2010 Task 8 train+test, 10,717, minus 1,864 "Other", minus 2 Entity-Destination(e2,e1), giving 8,851 and 17 directed relations), then:
- writes the whole input as `test.json`;
- writes `distant.json` as `{"UNLABELED": [every instance of every relation]}`, i.e. the same instances without the relation grouping;
- writes `train.json`/`val.json` as the first 60 per relation (1,020 total; the docstring says `trainer.py` does not use them).

Computed here: 8,851 of 8,851 pool instances match `test.json`. So SemEval is **fully transductive**: labels are hidden, but pool-based mining and feedback see the test sentences. `tools/build_nyt_defon.py` does the same (2,500 of 2,500). The docstring justifies this by FewRel split 1, where 4,281 of 9,798 test instances are also in the pool; that count is correct, but splits 2-5 are only 5.9-6.7% and WikiZSL under 1%, so 100% overlap is much stronger than the released data. Per the docstrings the first 50 test instances per relation are an unevaluated buffer (`--num_buffer_examples 50`, `src/run.py:131`).

### Issue 5: 10k followup mixes generators
`config.json`: `fewrel_defon10k_*/initial` = gpt-4o-2024-05-13 cached seeds; `fewrel_defon10k_*/followup` = Qwen/Qwen2.5-32B-Instruct-AWQ. `tools/build_fewrel_10k_pool.py` confirms the cached GPT-4o follow-ups were not copied. The followup rows are labelled separately and kept out of the clean comparison.
Further caution: `fewrel_defon10k_1/initial/run.log` has 15 "Ckpt found ... Skipped its optimization round" lines and took 13 minutes against 120 for split 2 (0 such lines), so split 1 reused checkpoints and is not a clean full run. `fewrel_defon_1/initial` has 4 such lines.
Same-split initial comparison (100k vs 10k, GPT-4o seeds): split 1 65.49 vs 73.58; split 2 65.39 vs 69.61. Two splits, one seed: suggestive only.

## 7. Model naming correction
Local generators were **Qwen2.5-32B-Instruct-AWQ** (semeval, nyt, 10k followups) and **Qwen3-32B-AWQ** (semeval_qwen3 only). `nyt_qwen3` was never run.

## 8. Other verified facts
- Venue: EMNLP 2024, pp. 13462-13486 (README BibTeX). Authors: University of Illinois Urbana-Champaign and University of Virginia (paper p. 1).
- Citations: 30 (Semantic Scholar API, 2026-11-09). CORE: EMNLP ranked A* under ICORE2026 (portal.core.edu.au, 2026-11-09).
- arXiv terms (`info.arxiv.org/help/api/tou.html`, 2026-11-09): descriptive metadata, explicitly including title and abstract, may be used under CC0 1.0.
- arXiv corpus: 397 abstracts; 2,947 sentences, 2,846 kept; 1,384 with 2+ mentions; 3,737 candidate pairs (`arxiv_re/corpus/preprocess_stats.json`). 6 relations x 2 directions. Annotation sheets: 100 rows each, 0 filled label cells in both.
- Not done: arXiv annotation, kappa, REPaL on arXiv, LLM-as-a-judge, BioCreative V CDR (reason: not completed within the project timeline; CONFIRM WITH USER).
- UNVERIFIED: Australian Code wording (nhmrc.gov.au returned HTTP 403 to automated access).
