# Video transcript v3: COMP8240 project update (target 5:00)

Replaces `2026-10-10-video-transcript-v2.md`. v2 and v1 are untouched.
About 640 spoken words, roughly 4:20 at a steady 148 words per minute. The rest of the 5:00 is the terminal demo and pauses. Time yourself once.
Lines in [square brackets] are on-screen cues or options. Do not read them aloud. Every **FILL** blank must be replaced before you record.

## What changed from v2
- "No human labels are used" is now "No human-labelled training data is used". The paper says it does not rely on "any labeled relation instance".
- Removed "assumed four GPUs" from the facts list. No source supports it.
- The "Before you record" checklist now lists every blank separately.
- Added a check that the original shell scripts really had placeholders.

## What changed from v1
- Feedback step says "a sample of its predictions". The paper samples within a probability range; v1 said "confident predictions".
- The environment line no longer states a GPU or versions as fact. Fill it from your run records.
- "Initial" and "follow-up" are defined.
- NYT has a description line, and the BioCreative CDR change is mentioned.
- Wrap-up says the extra datasets are done, not running.
- The progress segment is longer (30 s) because it carries 8 marks. New-data description gets 50 s. Both sit inside the brief's 3:30-4:50 window.
- Annotation progress has blanks for your real numbers.
- The terminal demo uses `--dry-run` and finished logs only. The `--skip-existing` command is gone, because a rerun can overwrite `results/`.
- The dashboard is shown as a screenshot, so no URL or token appears on screen.

## Before you record
- [ ] Show your face in a corner window while sharing your screen (required by the brief).
- [ ] Fill every blank:
  - [ ] GPU model (2:45-3:30)
  - [ ] Python version (2:45-3:30)
  - [ ] PyTorch version (2:45-3:30)
  - [ ] NYT sentence count (3:30-4:20)
  - [ ] NYT relation count (3:30-4:20)
  - [ ] Number of sentences you have labelled (4:20-4:50). If it is zero, use the "labelling starts next" sentence instead.
  - [ ] Optional: second annotator's count (M) and kappa (X), only if a second annotator has finished
  - [ ] Last word of the wrap-up: "partly labelled" or "ready to label"
- [ ] Test the three terminal commands once off camera, ideally in a copy of the repo. Confirm `--dry-run` prints commands without starting training. Run `python run_experiments.py --help` to check that `--device-profile gpu` is a valid value.
- [ ] Check the original shell scripts in the repo really had placeholders. If you cannot confirm, cut that sentence (1:15-2:45).
- [ ] Pre-type: `python run_experiments.py --dry-run --datasets fewrel_defon --splits 1 --stages initial --data-root reproduce_main_data/data --device-profile gpu`, then `tail -n 5 results/fewrel_defon_1/initial/run.log`, then `cat results/fewrel_defon_1/initial/metrics.json`.
- [ ] Have open: this script, a terminal in the repo, a dashboard screenshot (no URL or token visible), the results slide (table in `2026-10-10-video-notes.md`), `arxiv_re/README.md`, and the annotation sheet.

---

## 0:00-0:30  Introduction and why this paper
[Face in corner. Screen: title slide, then the authors' repo `github.com/KevinSRR/REPaL` beside your fork `github.com/ManoharNaidu/REPaL`.]

Hi, I'm Manohar, and this is my COMP8240 project update. I'm reproducing and extending REPaL, an EMNLP 2024 paper by Zhou and colleagues at the University of Illinois and the University of Virginia. It does zero-shot relation extraction: finding the relation between two entities in a sentence, using only a written definition of the relation and no labelled examples. I chose it because the authors released their code and data, and it can be pointed at new domains.

## 0:30-1:15  The paper's datasets
[Screen: a slide with FewRel and WikiZSL.]

The paper tests on two datasets built from existing resources. DefOn-FewRel comes from FewRel, eighty relations over Wikipedia sentences, where the authors hold out five groups of relations as test sets. DefOn-WikiZSL comes from WikiZSL, built from Wikidata, with three groups of fifteen relations. Each comes with a large pool of unlabelled sentences. The results are precision, recall and F1: each test relation is treated in turn as the target, the other test relations act as negatives, and the scores are averaged.

## 1:15-2:45  Architecture, code, and a run
[Screen: architecture slide first (three boxes: language model writes examples, small model is trained, feedback round), then the terminal.]

REPaL has three steps. First, a large language model, GPT-4o in the paper, reads the relation definition and writes example sentences with the two entities tagged. Second, a small model, RoBERTa-large fine-tuned for natural language inference, learns from those examples to judge whether a sentence matches the definition. Third, a feedback round: the small model labels unlabelled sentences, a sample of its predictions goes back to the language model, which writes new examples and new negative definitions aimed at the model's mistakes, and the small model is retrained. No human-labelled training data is used.

The authors published their code on GitHub, and I forked it. Their shell scripts had placeholders, so I wrote one Python driver that runs every split and collects the results.

[Terminal: run the pre-typed `--dry-run`, then `tail`, then `cat metrics.json`.]

This is the command, the training log, and the final precision, recall and F1 for one split. It's a finished run, because one split takes hours.

## 2:45-3:30  Replication status
[Screen: results slide, FewRel and WikiZSL rows highlighted.]

The code works. I ran it on rented cloud GPUs: [FILL: GPU model, Python version, PyTorch version]. All eight splits finished, using the authors' cached GPT-4o examples. "Initial" is the first stage of the pipeline; "follow-up" adds the feedback round, and that is the number the paper reports. On FewRel I get 69.6 F1 against the paper's 74.6, and on WikiZSL 45.9 against 47.8. So FewRel is about five points lower and WikiZSL is close. Feedback helps on FewRel but not on WikiZSL, and results vary a lot between splits.

[OPTIONAL, only after you confirm your `initial` stage is the paper's no-feedback stage: "In the paper, one feedback round adds about 4.6 F1 on FewRel. In my runs it adds about 4.7."]

## 3:30-4:20  New datasets
[Screen: results slide, SemEval and NYT rows; then a SemEval example sentence.]

For new data I use two existing datasets and one I'm building. The existing ones are SemEval-2010 Task 8 and NYT, both from FewRel 2.0, which I converted to REPaL's format. SemEval has 8,851 sentences and 17 directed relations, such as cause-effect, with the "Other" class removed. NYT has [FILL: N] sentences and [FILL: K] relations. My OpenAI credits ran out, so these runs use a local Qwen model instead of GPT-4o. On SemEval, F1 is 19, rising to 31 with feedback; on NYT it is about 47. The SemEval problem is low recall, not mixed-up relation directions. My proposal also listed BioCreative CDR. I did not use it; I ran NYT instead, which is in the same FewRel 2.0 format as SemEval.

[CDR sentences: the default is facts only. If you find a real reason in your notes or git history, replace the first clause of the last sentence with it.]

## 4:20-4:50  Building my own dataset: progress
[Screen: `arxiv_re/README.md` counts table, then the annotation sheet.]

My own dataset is on scientific papers. I collected 397 arXiv abstracts from five categories, using the official API, and split them into about 2,850 sentences. I defined six relations, such as evaluated-on, outperforms and builds-on, and prepared a 100-sentence annotation sheet. So far I have labelled [FILL: N] sentences. The hard part is finding entities in scientific text without a trained tagger.

[If you have labelled none, replace the "So far I have labelled" sentence with: "The annotation sheet is ready, and labelling starts next."]

[Add ONE sentence if true: "A second annotator has labelled [M] of the same sentences, and agreement is kappa [X]." OR "A second annotator will label the same sentences next, and kappa will follow."]

## 4:50-5:00  Wrap-up
[Face in corner, back to the title slide.]

To sum up: the replication works, two extra datasets are done, and my own dataset is built and [FILL: partly labelled / ready to label]. Next, I'll finish annotating and run REPaL on it. Thanks for watching.

---

## If you run long, cut in this order
1. The optional sentence in the replication section.
2. The sentence about the original shell scripts (1:15-2:45).
3. "The SemEval problem is low recall, not mixed-up relation directions."
4. "and results vary a lot between splits."

## If asked, facts to have ready
- Why local Qwen: the OpenAI credits ran out. SemEval and NYT used Qwen2.5-32B; one SemEval comparison used Qwen3-32B (25.1 initial, 19.6 follow-up). An archived GPT-4o SemEval run reached 35.7 at the initial stage and stopped when credits ran out. That hints that the generating model matters, but these are single runs.
- 26 runs finished without errors. `nyt_qwen3` was not run, on purpose.
- Why F1 (19) looks low next to precision (45) and recall (20): the paper averages precision, recall and F1 over the test iterations, so mean F1 is not the F1 of the mean precision and recall.
- Why a Python driver: the original shell scripts had placeholders (confirm from the repo).
- Newer PyTorch: your project notes say newer GPUs need a newer PyTorch build than the authors pinned. Confirm before saying it.
- SemEval hypothesis (untested): model-written examples use longer entity phrases (about 4-5 tokens) than SemEval's single-word entities.
- Pool size: the paper down-samples 10,000 unlabelled instances per test group (section 4.1). Your project notes say the released data uses a 100k pool. The 10k experiment (71.6 initial, 68.1 follow-up on two splits) mixes cached GPT-4o seeds with Qwen follow-up, so it is not a clean comparison.
- Group sizes (paper): 5 groups of 14 FewRel relations and 3 groups of 15 WikiZSL relations.
- Not done yet: finishing annotation, REPaL on the arXiv set, and the LLM-as-a-judge evaluation from the proposal.
