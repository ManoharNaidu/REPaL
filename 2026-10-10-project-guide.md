# REPaL reproduction and extension: complete project guide

COMP8240 (Applications of Data Science, Macquarie University, Session 2 2026). Student: Manohar Naidu Bheesetti.
Written 2026-10-10. Every fact here was read from a file or command output in this repository or instance; things I could not confirm are marked **(unverified)**.

---

## 1. Status at a glance

| area | state |
|---|---|
| Replication on the paper's data (FewRel, WikiZSL) | **Done**: 8 splits x 2 stages, all exit 0. FewRel followup 69.6 F1 (paper 74.6), WikiZSL followup 45.9 (paper 47.8) |
| Existing new datasets | **Done**: SemEval-2010 Task 8 and NYT (both built from FewRel 2.0), run with local Qwen LLMs |
| Own new dataset (arXiv scientific literature) | **Corpus built, annotation not started**: 397 abstracts, 2,846 sentences, 6 relations, 100-sentence annotation sheets (blank) |
| REPaL on the arXiv dataset | Not run (needs gold labels first) |
| LLM-as-a-judge evaluation (in the proposal) | Not started. No code or results in the repo |
| `nyt_qwen3` run | Not run (deliberately ignored for this update) |
| Project update video (5 min MP4) | **Not recorded yet.** Script: `2026-10-10-video-transcript.md`, notes: `2026-10-10-video-notes.md` |
| Git | Work is committed on branch `update-video-oct` (3 commits). **Not pushed** |

---

## 2. The assignment

Sources: `assignemtn_descriptions/Assessment-Project-Update.pdf`, `Assessment-Project-Proposal.pdf`, `Project_Proposal_Report.pdf` (your submitted proposal). I did **not** have the iLearn page "Overall Goal and Assessment Criteria" that the briefs say to read alongside, nor the full marking rubric text (the PDF extraction truncated it).

### 2.1 What the Update task is
- A **5-minute MP4 video presentation**, individual, submitted through the **iLearn dropbox**.
- Purpose: show progress on the project chosen at proposal stage. Generative AI use is open, but you are responsible for its output.
- Your project is a **Novel project** (you chose REPaL yourself), so the recap includes a short justification (venue, authors, source-code availability).
- **Face in a corner window during screen sharing is required.**
- Late penalty: "standard late penalty applies"; short automated extensions are accepted.
- **Check the dates and weighting on iLearn.** The Update PDF's header text still reads like the proposal template ("Assessment Task #1: Project Proposal", due 11.55pm 09/10/26, Week 9, 40 marks, 40% of the unit). That looks like a template carry-over, so do not rely on it.

### 2.2 Suggested timing (Novel project)
| time | content |
|---|---|
| 0:00-0:30 | Remind the audience of the project basis: venue, authors, why you chose it |
| 0:30-1:15 | Datasets from the original paper: where from, why used |
| 1:15-2:45 | High-level architecture; code availability and feasibility; run the original code if possible and show output |
| 2:45-3:30 | Replication status: does the code work, in what environment, similar results? |
| 3:30-4:30 | New datasets: at least one existing and one you are constructing (sources, properties, challenges) |
| 4:30-4:50 | Progress on construction: collection, preprocessing, annotation |
| ~10-15 s | Wrap-up: key progress and what comes next |

Delivery tips from the brief: keep it high-level, avoid technical overload, focus on progress.

### 2.3 Quality criteria (from the brief)
A high-quality submission is well structured with logical flow; has clear descriptions of the code and data; has enough detail to judge progress **including what has and has not worked**; and is clear on both existing datasets and the proposed new dataset. The rubric components include "Recap / Justification" (6 marks for a novel project); the other components were cut off in my extraction, so read the rubric table in the PDF.

### 2.4 What the proposal promised (`Project_Proposal_Report.pdf`)
- Reproduce REPaL on DefOn-FewRel and DefOn-WikiZSL with the authors' cached GPT-4o bundle.
- Two existing datasets not in the paper: SemEval-2010 Task 8 and BioCreative V CDR.
- A new "Scientific Literature Relation Extraction" resource: 300-500 arXiv abstracts, 5-10 relations given as definitions, and 50-100 abstracts annotated by 2-3 annotators with Cohen's kappa before consensus; REPaL evaluated against that gold standard.
- LLM-as-a-judge as a complementary evaluation (design only at proposal stage).
- A 10-week plan; update presentation at week 9.

---

## 3. The paper: REPaL

Zhou et al., "Grasping the Essentials: Tailoring Large Language Models for Zero-Shot Relation Extraction", EMNLP 2024, arXiv:2402.11142 (local copy: `2402.11142v2.pdf`). Authors from UIUC and the University of Virginia (per your proposal).

**Problem.** Definition-only zero-shot relation extraction: given only a natural-language definition of a target relation (no labelled instances, seen or unseen) and an unlabelled corpus, build a classifier that finds the relation between two entities in a sentence.

**Method.**
1. *Definition-based seed construction*: an LLM (GPT-4o) writes positive example sentences from the definition (entities tagged `<ENT0>`/`<ENT1>`); negatives come from other relations / the unlabelled corpus.
2. *Pattern learning with a small language model*: `roberta-large-mnli` is fine-tuned as an NLI-style binary classifier (the relation definition is the hypothesis, the sentence is the premise).
3. *Feedback loop ("snowball")*: the model runs over the unlabelled corpus; its confident predictions go back to the LLM, which writes further positive examples and new negative-relation definitions targeting the model's errors; the model is retrained.

**Stages in this repo.** `initial` = seed examples + snowball rounds. `followup` = the LLM sees the model's predictions and synthesises follow-up examples ("15 positive / 15 negative" at each step). The paper's reported REPaL score corresponds to our `followup` stage.

**Evaluation.** Per-relation cross-validation: with R test relations, evaluate R times, each time treating one relation as the positive target and the other test relations as negatives; precision, recall and F1 are averaged over the R iterations. Datasets: DefOn-FewRel (from FewRel, 5 groups of held-out relations) and DefOn-WikiZSL (from WikiZSL, 3 groups). The paper's reported F1 (REPaL with GPT-4o): FewRel 74.61, WikiZSL 47.80 (arXiv v2 Table 1).

**Baselines in the paper** (from your proposal): random guess, GPT-3.5, RE-as-QA prompting, RoBERTa NLI (supervised and zero-shot), ZS-BERT, RelationPrompt, RE-Matching.

---

## 4. The codebase (`/workspace/REPaL`)

Research reproduction code, no test suite and no linter. Remote: `https://github.com/ManoharNaidu/REPaL` (fork of the authors' repo).

### 4.1 Layout
| path | role |
|---|---|
| `run_experiments.py` | Driver (replaced the authors' shell scripts). Runs `src/run.py` per (dataset, split, stage), tees to `results/<dataset>_<split>/<stage>/run.log`, parses P/R/F1 into `metrics.json`, aggregates into `results/summary.*` and `results/aggregate.*`. Flags: `--datasets --splits --stages --data-root --device-profile --skip-existing --continue-on-error --dry-run --list --aggregate-only` |
| `src/run.py` | CLI entry; builds `REDataLoader` and `ModelTrainer`, dispatches `initial` or `followup` |
| `src/dataloader.py` | Loads/caches a split (train/val/test/distant), tokenises, builds prompt-encoded tensors |
| `src/model.py` | `NLIBasedSimilarityModel` wrapping `roberta-large-mnli`; per-model API rate limits |
| `src/trainer.py` | Core (~4k lines): seed synthesis, fine-tuning, `run_snowball`, follow-up feedback, `NLIBased_Inference` (DDP worker) |
| `src/llm_gen.py` | Parses LLM replies into definitions and tagged examples |
| `src/pattern_learning.py` | spaCy dependency paths + clustering for follow-up pattern mining |
| `src/utils.py` | `GPT3` LLM-call wrapper, SBERT helper, seeds, metrics |
| `data/<name>_<split>/` | Split folders: `train/val/test/distant.json`, `rel2id.json`, `id2rel.json`, `rel_info_updated.json`, `cache/` (git-ignored) |
| `reproduce_main_data/data/` | The authors' released splits + cached GPT-4o synthesis, 8 splits, 19 GB (git-ignored) |
| `results/` | Run outputs (git-ignored): 13 split folders, `aggregate.csv/json`, `summary.*`, `logs/`, `archive/` |
| `tools/` | `build_semeval_defon.py`, `build_nyt_defon.py`, `build_fewrel_10k_pool.py`, `run_local_llm.sh`, `launch_when_credits.sh`, `pending_chain.sh`, `qwen3_chain.sh` |
| `dashboard/` | Live results dashboard (own git repo, git-ignored by the parent) |
| `docs/VASTAI.md`, `vastai_setup.sh`, `Dockerfile`, `run_2gpu.sh` | Cloud/GPU setup helpers |
| `CLAUDE.md` | Agent guide for this repo (architecture, gotchas) |

### 4.2 Hyperparameters used (from `run.log` of a finished run)
`roberta-large-mnli`, learning rate 3e-5, 12 epochs, train batch 16, seed 3, temperature 0.6, 15 positive + 15 negative initial examples, 15 + 15 follow-up examples, negative sampling upper bound 0.6, `--run_snowball`, `--keep_only_dev_chosen_ckpt`.

### 4.3 Gotchas already fixed (do not reintroduce)
- `BCELoss` cannot run inside `autocast`: loss is computed outside it.
- UTF-8 stdout/stderr forced (Windows console crashes on accents).
- `torch.load(..., weights_only=False)` everywhere (torch >= 2.6 default breaks the repo's caches).
- Do not pin torch in `requirements.txt` (Blackwell GPUs need a cu128+ wheel); numpy stays `<2`.
- Follow-up negative sampling is capped at the population size.
- Parallel `run_experiments.py` processes use a lock on `results/summary.*`.
- Supervisor services that wrap child processes need `stopasgroup`/`killasgroup`.

### 4.4 Local LLM route
Every OpenAI-client call in `src/` honours `OPENAI_BASE_URL`, so a local vLLM server replaces GPT-4o with no code change. `tools/run_local_llm.sh` sets the base URL (`http://127.0.0.1:8000/v1`), a dummy key, `BASE_LLM`/`PARSER_LLM`, and trains on GPU 1 while vLLM (`qwen-llm` supervisor service) occupies GPU 0. Never mix generator LLMs inside one comparison: each run's `config.json` records `llm_model_ckpt`.

---

## 5. Environment

**Current instance (Vast.ai container, unprivileged Docker, not a VM):** Python 3.12.14 in `/venv/main`; 2x NVIDIA RTX 5090 (32 GB, driver 595.71.05); torch 2.11.0+cu128; transformers 4.43.3; spaCy 3.7.5; numpy 1.26.4; openai 1.37.1; sentence-transformers 3.0.1; scikit-learn 1.3.2. Also installed this session: `openpyxl`, `formulas`, `pypdf` (not in `requirements.txt`).

**Not present on this instance:** vLLM, the Qwen weights, the `qwen-llm` service, `en_core_web_trf`/`en_core_web_sm`.

**Earlier instance:** the experiments ran on an earlier instance with the same layout (`/venv/main`, `/root/hf_fresh`); package versions at that time were not recorded, so I cannot confirm they match.

**Persistence (checked 2026-10-10): `workspace_is_volume` is `false`.** `/workspace` is ordinary container storage. A stop/start keeps it, but a **recycle or destroy wipes everything**, including `results/`, `data/` and the unpushed git branch. Push `update-video-oct` and copy `results/` (155 MB) and the `2026-10-10-*` files somewhere off the instance before you stop relying on it.

**Services running:** `dashboard` (REPaL results dashboard, this session), `caddy`, `instance_portal`, `tunnel_manager`, `cron`, `tensorboard`, `syncthing`. No training jobs.

**Dashboard.** `dashboard/server.py` (v0.3.2) serves a live view of `results/` on `127.0.0.1:18780` as supervisor service `dashboard` (`/opt/supervisor-scripts/dashboard.sh`, `/etc/supervisor/conf.d/dashboard.conf`). Exposed through Caddy at `http://<PUBLIC_IPADDR>:<VAST_TCP_PORT_10100>/` with the instance token (`?token=$OPEN_BUTTON_TOKEN`). `/` is the v2 page, `/v1` the old page, `/api/status`, `/api/resources`, `/health`. It lasts until the instance is recycled.

**Instance-copy damage found and fixed this session.** After copying the project from another instance, `src/*.py` and four `tools/` files had unreadable (`Stale file handle`) entries, and the `roberta-large-mnli` cache was damaged. Fixed by moving the broken folders aside (`src.corrupt/`, `tools.corrupt/`, `.hf_cache.corrupt2/`, all git-ignored), restoring the files from git HEAD, and re-downloading the model into `.hf_cache`. Results and data were checked: 156 JSON files parse, 26 runs complete.

---

## 6. Experiments and results

### 6.1 Datasets used
| dataset | origin | splits | generator LLM (from `config.json`) |
|---|---|---|---|
| `fewrel_defon` | authors' DefOn-FewRel | 5 | GPT-4o, authors' cached bundle |
| `wikizsl_defon` | authors' DefOn-WikiZSL | 3 | GPT-4o, authors' cached bundle |
| `fewrel_defon10k` | same FewRel splits, unlabelled pool down-sampled from 100k to 10,000 (`tools/build_fewrel_10k_pool.py`) | 2 | initial: authors' cached GPT-4o seeds; followup: live Qwen2.5-32B (mixed) |
| `semeval` | SemEval-2010 Task 8 via FewRel 2.0 `val_semeval.json` (`tools/build_semeval_defon.py`): 8,851 instances, 17 directed relations, "Other" removed | 1 | Qwen2.5-32B-Instruct-AWQ |
| `semeval_qwen3` | same data as `semeval` | 1 | Qwen3-32B-AWQ |
| `nyt` | FewRel 2.0 `val_nyt.json` (`tools/build_nyt_defon.py`) | 1 | Qwen2.5-32B-Instruct-AWQ |
| `nyt_qwen3` | same data as `nyt` | 1 | **not run** |

### 6.2 Results (mean F1 %, +- sample std over splits; source `2026-10-10-repal-results.xlsx`)
| dataset | n | initial | followup | paper (followup) | followup minus paper |
|---|---|---|---|---|---|
| FewRel (DefOn) | 5 | 64.9 +- 1.3 | 69.6 +- 3.7 | 74.6 | -5.0 |
| WikiZSL (DefOn) | 3 | 49.1 +- 2.8 | 45.9 +- 6.1 | 47.8 | -1.9 |
| FewRel, 10k pool | 2 | 71.6 +- 2.8 | 68.1 +- 3.1 | n/a | n/a |
| SemEval (Qwen2.5) | 1 | 19.0 | 31.0 | n/a | n/a |
| SemEval (Qwen3) | 1 | 25.1 | 19.6 | n/a | n/a |
| NYT (Qwen2.5) | 1 | 48.3 | 47.1 | n/a | n/a |

Notes: `results/aggregate.csv` reports the **population** std, which is smaller than the sample std above by sqrt((n-1)/n); both are in the workbook. An earlier archived GPT-4o SemEval run (`results/archive/semeval_1_gpt4o`) reached initial F1 35.7 and stopped when the OpenAI credits ran out (no followup). Single-split, single-seed rows (SemEval, NYT) have no variance estimate.

Run times (minutes, initial / followup): fewrel_defon_1 160 / 97; wikizsl_defon_1 179 / 137; semeval_1 129 / 122.

### 6.3 SemEval diagnosis (`2026-10-10-semeval-diagnosis.md`)
Read-only analysis of existing logs and inference files; no re-runs.
- Precision is moderate (about 0.45) and **recall is the problem** (0.20 initial, 0.36 followup). In the initial-stage inference files no relation model fires on 64.6% of test instances.
- **Direction confusion is not the main failure:** 10.0% of false positives come from the reverse-direction class; where exactly one model fires it fires the reverse relation only 3.7% of the time.
- The two Component-Whole models produce 74% of all false positives (over-firing); Member-Collection and Cause-Effect(e1,e2) sit near F1 0 in every run.
- "Other" is not in this benchmark (1,864 instances removed), so it does not explain the low score.
- Hypothesis (three single-seed runs): LLM seed examples with clause-length entities (Qwen2.5 4.2/4.9 tokens head/tail, 37-token sentences) differ from real single-word entities in 19-token sentences; generators closer to the real format scored higher (GPT-4o 35.7 > Qwen3 25.1 > Qwen2.5 19.0).
- Caveat: per-instance predictions exist only for the initial stage and come from a slightly different checkpoint than the reported numbers (recomputed macro P/R 0.483/0.161 vs reported 0.454/0.204).

---

## 7. The new arXiv dataset (`arxiv_re/`)

Full dataset card: `arxiv_re/README.md`. Annotator guide: `arxiv_re/2026-10-10-arxiv-relation-definitions.md`.

**Pipeline.**
1. `collect_abstracts.py`: official arXiv API over HTTPS, one request at a time, at least 3.2 s apart, descriptive User-Agent, resumable. Per category and month (2025-01 to 2026-09), a seeded random offset; primary category only; deduplicated.
2. `preprocess_abstracts.py`: spaCy rule-based sentencizer, 8-60 token filter, heuristic mention detection (acronyms, CamelCase/alphanumeric names, non-initial capitalised words, metric words, scores, "<modifiers> model/method/dataset"), mention pairs written in REPaL's `distant.json` format.
3. `make_annotation_material.py`: relation schema files, annotator guide, 100-sentence sheets, sampling log.
4. `kappa.py` (Cohen's kappa and raw agreement; self-test on made-up data matches sklearn) and `build_repal_dataset.py` (filled sheet to REPaL folder; tested only on made-up rows).

**Counts.** 397 abstracts (cs.CL 83, cs.LG 80, cs.CV 80, cs.IR 80, stat.ML 74), submitted 2025-01-01 to 2026-09-11; 2,947 sentences, 2,846 kept (mean 28.4, median 27 tokens); 1,384 kept sentences with 2+ candidate mentions; 3,737 candidate pairs.

**Relations** (head to tail; each stored in both directions as `(e1,e2)` / `(e2,e1)`, 12 labels, same naming as SemEval):
| relation | head -> tail |
|---|---|
| `evaluated_on` | method/model -> dataset/benchmark |
| `outperforms` | method -> baseline/earlier method |
| `achieves_result` | method -> score/metric value |
| `builds_on` | new method -> earlier method |
| `applied_to_task` | method -> task/problem/domain |
| `uses_component` | method -> technique/module/resource |

Changes from the proposal's starting list: `proposes_method` dropped (its head, "the paper", is not an entity in the sentence); `compares_with_baseline` replaced by the directional `outperforms`; `extends_prior_work` renamed `builds_on`; `trained_on` rejected (19 sentences match).

**Annotation material.** 100 sentences, 20 per category, from sentences with 2+ candidate mentions and 12-50 tokens, one per abstract, shuffled, seed 0; two identical blank copies. All label columns are blank; **no gold label has been written by anyone yet**. `annotation_sampling_log.csv` lists the sampling strata and would bias annotators, so do not share it.

**Known limitations.** Noisy heuristic mentions (no scientific NER available); small and single-sentence; keyword-guided sampling over-represents prototypical phrasings; latest submission date is 2026-09-11, not 09-30; relations are method-centric. The arXiv metadata licence page was not fully readable in this session: read it before redistributing abstracts.

---

## 8. Changes since the proposal
| proposal | now |
|---|---|
| GPT-4o API synthesis (about $3.7 per split) for new data | Local Qwen2.5-32B / Qwen3-32B via vLLM; GPT-4o used only through the authors' cached bundle (API credits ran out) |
| Python 3.11.9, torch 2.4.0 | Python 3.12.14, torch 2.11.0+cu128 (RTX 5090s) |
| SemEval-2010 + BioCreative V CDR | SemEval + NYT (both via FewRel 2.0). No CDR data or code exists in the repo; **the reason is not recorded, so state it yourself** |
| 50-100 abstracts annotated by 2-3 annotators | 100 sentences from 100 abstracts for 2 annotators (not yet annotated) |
| 5 starter relations incl. `proposes_method`, `compares_with_baseline` | 6 relations (see section 7) |
| LLM-as-a-judge | Not started |
| Ten-week plan with REPaL on the arXiv set in week 6 | Blocked on annotation |

---

## 9. Deliverables and git state

Branch `update-video-oct` (from `main`), three commits, all local:
- `0c55feb` results spreadsheet and SemEval diagnosis
- `fe19169` arXiv collector, preprocessing, kappa tool, corpus
- `16fe978` annotation material, dataset card, converter, video notes

The project guide and video transcript (this file and `2026-10-10-video-transcript.md`) were added after those commits; check `git status` and commit them if you want them on the branch. `main` has earlier commits including `0379979` (tooling, ignore rules). `.gitignore` hides `data/`, `results/`, `reproduce_main_data/`, `dashboard/` and the `*.corrupt*` folders.

| file | what it is |
|---|---|
| `2026-10-10-repal-results.xlsx` / `.csv` | All 26 runs, summary with live formulas, provenance notes (script: `update_video/make_results_xlsx.py`) |
| `2026-10-10-semeval-diagnosis.md` | SemEval diagnosis (script: `update_video/semeval_diagnosis.py`) |
| `2026-10-10-video-notes.md` | Environment, rerun commands, what worked/failed/changed, results slide, dataset-progress table |
| `2026-10-10-video-transcript.md` | Timed 5-minute script with screen cues |
| `2026-10-10-project-guide.md` | This file |
| `arxiv_re/` | The new dataset (section 7) |

---

## 10. Regenerate or rerun

```bash
cd /workspace/REPaL && source /venv/main/bin/activate
python update_video/make_results_xlsx.py           # rebuild workbook + csv from results/
python update_video/semeval_diagnosis.py           # print the diagnosis tables
python arxiv_re/collect_abstracts.py               # resumes; already complete
python arxiv_re/preprocess_abstracts.py            # rebuild sentences + distant.json
python arxiv_re/make_annotation_material.py        # rewrites schema, guide, blank sheets (do NOT run after annotation starts)
python arxiv_re/kappa.py --a sheetA.csv --b sheetB.csv     # after both annotators finish
python arxiv_re/build_repal_dataset.py consensus.csv out_dir   # filled sheet -> REPaL folder
python run_experiments.py --list --datasets fewrel_defon --data-root reproduce_main_data/data
```
Warning: `make_annotation_material.py` overwrites the annotation sheets. A real REPaL rerun through `run_experiments.py` overwrites `results/<dataset>_<split>/<stage>/`; use the demo-folder commands in `2026-10-10-video-notes.md` instead (they were not executed).

---

## 11. Open items and risks
1. **Record and submit the video** (iLearn dropbox, face in a corner window). Late.
2. **Annotation** of the 100 sentences by two people, then kappa, consensus, and `build_repal_dataset.py`.
3. **Run REPaL on the arXiv set** after gold labels exist (needs the vLLM Qwen server again, or API credits).
4. **State why CDR was replaced** by NYT.
5. **LLM-as-a-judge**: promised in the proposal, not started.
6. **Variance**: SemEval, NYT and the Qwen3 rows are single-split, single-seed.
7. **Push** `update-video-oct`, and back up `results/` and the `2026-10-10-*` files off the instance: `/workspace` is not a persistent volume (see section 5).
8. **Unread/unverified:** iLearn "Overall Goal and Assessment Criteria" page, the full rubric table, the arXiv metadata licence wording, whether the existing SemEval cache can run without a vLLM server.
9. Delete the unreadable `*.corrupt*` leftovers when the host allows it.
