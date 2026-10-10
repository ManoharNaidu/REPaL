# Video transcript: COMP8240 project update (target 5:00)

About 650 spoken words: roughly 4.4 minutes at a steady 148 words per minute, which leaves about 30 seconds for pauses and for the terminal output to appear on screen. Time yourself once and adjust. Times follow the Novel-project structure in the Update brief.
Numbers are verified against `2026-10-10-repal-results.xlsx`. Square brackets are on-screen cues or things for you to fill in; do not read them out.

**Before you record**
- [ ] The brief **requires your face in a corner window** while you share your screen.
- [ ] Open: this script, a terminal in `/workspace/REPaL`, the dashboard page, the results slide (table in `2026-10-10-video-notes.md` section 4), `arxiv_re/README.md`.
- [ ] Terminal pre-typed (do not run a real training job): `python run_experiments.py --dry-run --datasets fewrel_defon --splits 1 --stages initial --data-root reproduce_main_data/data --device-profile gpu`, then the same command with `--skip-existing` instead of `--dry-run`, then `tail -n 5 results/fewrel_defon_1/initial/run.log` and `cat results/fewrel_defon_1/initial/metrics.json`.
- [ ] Dashboard URL: `http://154.37.220.220:43120/?token=<your OPEN_BUTTON_TOKEN>` (works while this instance is alive).

---

## 0:00-0:30  Introduction and why this paper  (~75 words)
[Face in corner. Screen: title slide or the paper's first page, `2402.11142v2.pdf`.]

Hi, I'm Manohar, and this is my COMP8240 project update. I'm reproducing and extending a paper called REPaL, from EMNLP 2024, by Zhou and colleagues at the University of Illinois and the University of Virginia. It tackles zero-shot relation extraction: finding the relation between two entities in a sentence when all you have is a written definition of that relation, and no labelled examples. I chose it because the code and data are public, the experiments are clear, and it can be pointed at new domains.

## 0:30-1:15  The paper's datasets  (~100 words)
[Screen: a slide with FewRel and WikiZSL, or the dataset table in the proposal.]

The paper tests on two datasets built from existing resources. DefOn-FewRel comes from FewRel, eighty relations over Wikipedia sentences, where the authors hold out five groups of relations as test sets. DefOn-WikiZSL comes from WikiZSL, built from Wikidata, with three groups of fifteen relations. Each comes with a large pool of unlabelled sentences. The results are precision, recall and F1: each test relation is treated in turn as the target, the other test relations act as negatives, and the scores are averaged.

## 1:15-2:45  Architecture, code, and a run  (~220 words)
[Screen: architecture slide first (three boxes: LLM writes examples -> small model trained -> feedback loop), then the terminal.]

REPaL works in three steps. First, a large language model, GPT-4o in the paper, reads the relation definition and writes example sentences with the two entities tagged. Second, a small model, RoBERTa-large fine-tuned for natural language inference, is trained on those examples to decide whether a sentence matches the definition. Third, a feedback loop: the small model scans the unlabelled sentences, its confident predictions go back to the language model, which writes new examples and new negative definitions aimed at the model's mistakes, and the small model is retrained. No human-labelled data is used at any stage.

The authors released their code on GitHub, so this is feasible. The original shell scripts had placeholders, so I wrote one Python driver that runs both stages over every split and collects the results.

[Terminal: run the pre-typed `--dry-run`, then `--skip-existing`, then `tail` of `run.log`, then `cat metrics.json`.]

Here is the command the driver launches, the training log, and the final precision, recall and F1 for one split. I'm showing a finished run, because a single split takes a few hours on my GPU.

## 2:45-3:30  Replication status  (~105 words)
[Screen: results slide, rows FewRel and WikiZSL highlighted.]

The code works. I run it on two RTX 5090 GPUs with Python 3.12 and PyTorch 2.11, which needed a newer PyTorch build than the original requirements. All eight splits finished, using the authors' cached GPT-4o examples. On FewRel I get 69.6 F1 against 74.6 in the paper; on WikiZSL, 45.9 against 47.8. So FewRel is about five points lower, WikiZSL is close, and the follow-up stage helps on FewRel but not on WikiZSL. The differences between splits are large, especially on WikiZSL.

## 3:30-4:30  New datasets  (~145 words)
[Screen: results slide, SemEval and NYT rows; then a short slide with a SemEval example sentence.]

For new data I use two existing datasets and one I am building. The existing ones are SemEval-2010 Task 8, with 8,851 sentences and 17 directed relations such as cause-effect, and NYT. Both come from FewRel 2.0, and I converted them into REPaL's format. My OpenAI credits ran out, so I replaced GPT-4o with a local Qwen model behind the same interface.

REPaL struggles on SemEval: F1 of 19 rising to 31 after follow-up. My analysis shows the problem is low recall, not confusion between relation directions. A possible reason is that the model-written training sentences use long phrases as entities, while SemEval entities are single words. That is a hypothesis I still need to test. NYT scores around 47.

[Optional, only if you know the reason: one sentence on why BioCreative CDR from the proposal was replaced by NYT.]

## 4:30-4:50  Building my own dataset  (~60 words)
[Screen: `arxiv_re/README.md` counts table, then the annotation sheet CSV.]

My own dataset covers scientific literature. I collected 397 arXiv abstracts from five categories through the official API, split them into about 2,800 sentences, and defined six relations, such as evaluated-on, outperforms and builds-on. A hundred-sentence annotation sheet is ready for two annotators; annotation has not started yet. The main challenge is finding entities in scientific text without a trained tagger.

## 4:50-5:00  Wrap-up  (~35 words)
[Face in corner, back to the title slide.]

To sum up: the replication works, two extra datasets are running, and my own dataset is built and ready to label. Next, I will annotate it, measure agreement between annotators, and run REPaL on it. Thanks for watching.

---

## If you run long, cut in this order
1. The extra sentences about between-split differences (2:45-3:30).
2. The sentence about the original shell scripts (1:15-2:45).
3. The analysis sentences on SemEval beyond "low recall" (3:30-4:30).

## If asked, facts to have ready
- Why local Qwen: OpenAI credits ran out; all new-dataset runs used Qwen2.5-32B (SemEval, NYT) or Qwen3-32B (one SemEval comparison run, F1 25.1 to 19.6).
- 26 runs in total finished without errors; the FewRel 10k-pool experiment (paper's pool size) gave 71.6 / 68.1, but mixes cached GPT-4o seeds with Qwen follow-up, so it is not a clean comparison.
- Not done yet: annotation, REPaL on the arXiv set, and the LLM-as-a-judge evaluation from the proposal.
