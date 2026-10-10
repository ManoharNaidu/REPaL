# Video notes (5-minute project update), 2026-10-10

Everything below is taken from files or commands checked in this session. Anything not verified is marked **(unverified)**.

## 1. Environment
| item | value |
|---|---|
| OS / host | Linux 5.15, Vast.ai container instance (unprivileged Docker) |
| Python | 3.12.14 (`/venv/main`) |
| GPUs | 2x NVIDIA GeForce RTX 5090, 32 GB each, driver 595.71.05 |
| PyTorch | 2.11.0+cu128 (a cu128 build is needed for Blackwell GPUs; the proposal's torch 2.4.0 fails there with "no kernel image") |
| transformers / spaCy / numpy / openai / sentence-transformers / scikit-learn | 4.43.3 / 3.7.5 / 1.26.4 / 1.37.1 / 3.0.1 / 1.3.2 |
| SLM backbone | `roberta-large-mnli` (re-downloaded into `.hf_cache` this session; the old cache was damaged by an instance copy) |
| Generator LLMs | GPT-4o (authors' cached bundle) for fewrel/wikizsl; **local Qwen2.5-32B-Instruct-AWQ** for semeval, nyt and the 10k-pool followup; **Qwen3-32B-AWQ** for `semeval_qwen3` (from each run's `config.json`) |
| How Qwen was served | vLLM, OpenAI-compatible server on `127.0.0.1:8000` as supervisor service `qwen-llm` on GPU 0; REPaL trained on GPU 1 (`tools/run_local_llm.sh`: `OPENAI_BASE_URL=http://127.0.0.1:8000/v1`, dummy key, `CUDA_VISIBLE_DEVICES=1`). Every OpenAI-client call in `src/` honours `OPENAI_BASE_URL`, so no code change was needed |

Caveats: the experiments ran on an earlier instance with the same layout; the versions above are from the *current* instance, and I cannot confirm they are identical. vLLM is not installed and the Qwen weights are not present on this instance, so the LLM server cannot be demonstrated live here.

## 2. Commands to screen-record
**Safe, instant (does not touch results):**
```bash
cd /workspace/REPaL && source /venv/main/bin/activate
python run_experiments.py --list --datasets fewrel_defon --data-root reproduce_main_data/data   # planned runs
python run_experiments.py --dry-run --datasets fewrel_defon --splits 1 --stages initial --data-root reproduce_main_data/data --device-profile gpu
python run_experiments.py --datasets fewrel_defon --splits 1 --stages initial --data-root reproduce_main_data/data --skip-existing   # prints SKIP: already has metrics
tail -n 5 results/fewrel_defon_1/initial/run.log ; cat results/fewrel_defon_1/initial/metrics.json
```
**A real rerun that does NOT overwrite your results.** `run_experiments.py` always writes to `results/<dataset>_<split>/<stage>/` and training writes caches inside the dataset folder, so a plain rerun would overwrite finished runs. Instead copy the split and call `src/run.py` with a demo output folder. These two commands were produced from the driver's own `--dry-run` with only the two paths changed, and were **not executed** in this session:

FewRel (cached GPT-4o bundle, no LLM needed; the original run took 160 min, so record the first minutes and cut):
```bash
mkdir -p demo_data results_demo && cp -r reproduce_main_data/data/fewrel_defon_1 demo_data/fewrel_defon_1
/venv/main/bin/python -u src/run.py --seed 3 --pretrained_lm roberta-large-mnli --accum_steps 1 --train_batch_size 16 --num_train_epochs 12 --learning_rate 3e-05 --logging_steps 0 --save_steps -1 --negative_sampling_upper_bound 0.6 --save_epochs 4 --logging_epochs 4 --rel_info_file rel_info_updated.json --cache_sub_dir cache/ --temperature 0.6 --def_gen_temperature 0.6 --neg_ex_gen_temperature 0.6 --num_buffer_examples 50 --num_init_pos_examples 15 --num_init_neg_examples 15 --num_init_neg_rels_to_generate 5 --num_init_neg_examples_to_generate 15 --num_follow_pos_examples 15 --num_follow_neg_examples 15 --num_follow_neg_rels_to_generate 5 --num_follow_neg_examples_to_generate 15 --run_LLM_json_parser_def --llm_model_ckpt_parser gpt-4o-mini-2024-07-18 --llm_model_ckpt gpt-4o-2024-05-13 --keep_only_dev_chosen_ckpt --run_type initial --dist_port 12345 --run_snowball --eval_batch_size 512 --unlabel_infer_batch_size 512 --huggingface_cache_dir /workspace/REPaL/.hf_cache --output_dir /workspace/REPaL/results_demo/fewrel_defon_1/initial/ --dataset_dir /workspace/REPaL/demo_data/fewrel_defon_1/
```
SemEval (the original used Qwen2.5-32B; **(unverified)** that the existing `cache/` is enough to run without the vLLM server; if it is not, start the server first. The original run took 129 min):
```bash
cp -r data/semeval_1 demo_data/semeval_1
/venv/main/bin/python -u src/run.py --seed 3 --pretrained_lm roberta-large-mnli --accum_steps 1 --train_batch_size 16 --num_train_epochs 12 --learning_rate 3e-05 --logging_steps 0 --save_steps -1 --negative_sampling_upper_bound 0.6 --save_epochs 4 --logging_epochs 4 --rel_info_file rel_info_updated.json --cache_sub_dir cache/ --temperature 0.6 --def_gen_temperature 0.6 --neg_ex_gen_temperature 0.6 --num_buffer_examples 50 --num_init_pos_examples 15 --num_init_neg_examples 15 --num_init_neg_rels_to_generate 5 --num_init_neg_examples_to_generate 15 --num_follow_pos_examples 15 --num_follow_neg_examples 15 --num_follow_neg_rels_to_generate 5 --num_follow_neg_examples_to_generate 15 --run_LLM_json_parser_def --llm_model_ckpt_parser Qwen/Qwen2.5-32B-Instruct-AWQ --llm_model_ckpt Qwen/Qwen2.5-32B-Instruct-AWQ --keep_only_dev_chosen_ckpt --run_type initial --dist_port 12345 --run_snowball --eval_batch_size 512 --unlabel_infer_batch_size 512 --huggingface_cache_dir /workspace/REPaL/.hf_cache --output_dir /workspace/REPaL/results_demo/semeval_1/initial/ --dataset_dir /workspace/REPaL/demo_data/semeval_1/
```

## 3. What worked / what did not / what changed since the proposal
**Worked**
- Replicated REPaL on all 5 FewRel and all 3 WikiZSL splits with the authors' cached GPT-4o synthesis: FewRel followup 69.6 vs paper 74.6 (-5.0); WikiZSL followup 45.9 vs paper 47.8 (-1.9). 26 runs in total finished with exit code 0.
- Replaced the OpenAI API with a local Qwen LLM behind the same client code, so new datasets could be run without API credits.
- Built two new datasets in REPaL format from FewRel 2.0: SemEval-2010 Task 8 (17 directed relations, 8,851 instances) and NYT; ran both.
- Live results dashboard and a results spreadsheet generated from the run files.
**Did not work / limits**
- SemEval scores are low (Qwen2.5: 19.0 -> 31.0; Qwen3: 25.1 -> 19.6). The diagnosis (`2026-10-10-semeval-diagnosis.md`): low recall rather than direction confusion, over-firing Component-Whole models, and LLM seed examples with clause-length entities where real SemEval entities are single words. The generator ordering (GPT-4o 35.7 > Qwen3 25.1 > Qwen2.5 19.0) is a hypothesis from single-seed runs.
- A GPT-4o SemEval run stopped when the OpenAI credits ran out (initial stage only, 35.7); archived in `results/archive`.
- WikiZSL followup is below its initial stage (45.9 vs 49.1), and variance across splits is large (std 6.1).
- 10k-pool test (paper says 10,000 unlabeled instances): FewRel initial 71.6 vs 64.9 with the 100k pool, followup 68.1 vs 69.6. Mixed generators (cached GPT-4o seeds, Qwen2.5 followup), so not a clean comparison.
- `nyt_qwen3` has not been run.
- No LLM-as-a-judge code or results exist in the repository (searched for "judge").
**Changed since the proposal** (the proposal is `assignemtn_descriptions/Project_Proposal_Report.pdf`)
- LLM: proposal planned GPT-4o API synthesis (about $3.7 per split); now local Qwen2.5-32B / Qwen3-32B after the API credits ran out.
- Environment: Python 3.11.9 / torch 2.4.0 -> Python 3.12.14 / torch 2.11.0+cu128 (RTX 5090s).
- Datasets: proposal listed SemEval-2010 Task 8 and BioCreative V CDR. The repository contains SemEval and NYT (both from FewRel 2.0); I found no CDR data or code. **Confirm and state in the video why CDR was replaced.**
- Annotation: proposal planned 50-100 abstracts annotated by 2-3 annotators; the current material is 100 sentences from 100 abstracts for 2 annotators.
- Relation schema: `proposes_method` and `compares_with_baseline` were replaced (see the dataset card).

## 4. One-slide results table
Mean F1 (%) over splits, +- sample std; n = number of splits. Source: `2026-10-10-repal-results.xlsx`.
| dataset | n | generator LLM | initial F1 | followup F1 | paper F1 (followup) |
|---|---|---|---|---|---|
| FewRel (DefOn) | 5 | GPT-4o (cached) | 64.9 +- 1.3 | 69.6 +- 3.7 | 74.6 |
| WikiZSL (DefOn) | 3 | GPT-4o (cached) | 49.1 +- 2.8 | 45.9 +- 6.1 | 47.8 |
| FewRel, 10k pool | 2 | GPT-4o seeds / Qwen2.5 followup | 71.6 +- 2.8 | 68.1 +- 3.1 | n/a |
| SemEval-2010 | 1 | Qwen2.5-32B | 19.0 | 31.0 | n/a |
| SemEval-2010 | 1 | Qwen3-32B | 25.1 | 19.6 | n/a |
| NYT | 1 | Qwen2.5-32B | 48.3 | 47.1 | n/a |

## 5. Dataset construction progress (arXiv scientific-literature set)
| item | value |
|---|---|
| source | arXiv API (`export.arxiv.org`), rate-limited, collected 2026-10-10 |
| abstracts | 397 (cs.CL 83, cs.LG 80, cs.CV 80, cs.IR 80, stat.ML 74) |
| date range | 2025-01-01 to 2026-09-11 |
| sentences | 2,947 total; 2,846 after the 8-60 token filter (mean 28.4, median 27 tokens) |
| sentences with 2+ candidate mentions / candidate pairs | 1,384 / 3,737 (in REPaL `distant.json` format) |
| relations | 6 (x2 directions = 12 labels): evaluated_on, outperforms, achieves_result, builds_on, applied_to_task, uses_component |
| annotation sheet | 100 sentences (20 per category), 2 identical copies; **0 annotated so far** (all label cells blank) |
| agreement tooling | `kappa.py` tested on a made-up example only |

Challenges (all met in this work): no scientific NER model, so mention pairs come from a noisy heuristic; the proposal's `proposes_method` has no in-sentence head entity; `trained_on` is too rare (19 sentences) to sample; the arXiv API redirects http to https and requires polite 3 s spacing; the repository's `data/` ignore rule would have hidden the corpus (folder renamed `corpus/`); and a damaged instance copy corrupted source files and the model cache, which had to be restored from git and re-downloaded.
