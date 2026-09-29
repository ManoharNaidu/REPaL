# Running on vast.ai

The local run of this repo was bottlenecked by an 8GB card (Quadro RTX 4000):
`--device-profile small_gpu` forces halved batch sizes + AMP, and full sweeps
were taking hours per split with eval passes alone running 6-8s/iteration.
Renting a >=16GB card on vast.ai removes that bottleneck (see the GPU table
in [README.md](../README.md#recommended-gpu-specification)) and lets you use
`--device-profile gpu` instead.

## Quick start

Once the instance is up and the repo is cloned (step 2 below):

```bash
bash vastai_setup.sh
```

This installs Python/system dependencies, downloads the dataset archives
(skipped if `data/`/`reproduce_main_data/` are already present, e.g. via
`rsync`), and kicks off the full `fewrel_defon` + `wikizsl_defon` sweep with
`--device-profile gpu`. Pass `--setup-only` to stop after setup, or
`--run-only` to skip straight to the sweep on a box that's already set up.
The sections below explain each step it automates, plus the Docker-based
alternative.

## 1. Rent an instance

- Recommended: a single **RTX 4090 (24GB)** or **A100 (40GB)** on-demand instance.
  24GB+ lets you skip `--use_amp` entirely and run the paper's native batch
  sizes (`--train_batch_size 16`, `--eval_batch_size`/`--unlabel_infer_batch_size`
  in the hundreds), which is both faster and avoids the BCELoss/autocast class
  of bug this repo hit locally.
- Pick a template with CUDA 12.1+ preinstalled (e.g. vast.ai's official
  `pytorch/pytorch` template), or just use the `Dockerfile` in this repo
  directly if the instance supports custom Docker images.
- Disk: reserve at least 30-40GB (base image + HF model cache + cached
  synthesis data + checkpoints).

## 2. Get the code onto the instance

From the instance's SSH session:

```bash
git clone https://github.com/ManoharNaidu/REPaL.git
cd REPaL
```

(Push your local commits first if you haven't: `git push origin main`.)

## 3. Build/run via Docker (recommended)

```bash
docker build -t repal .
docker run --gpus all -it --rm \
  -v $(pwd)/data:/workspace/data \
  -v $(pwd)/reproduce_main_data:/workspace/reproduce_main_data \
  -v $(pwd)/results:/workspace/results \
  -v $(pwd)/.hf_cache:/workspace/.hf_cache \
  repal
```

`data/`, `reproduce_main_data/`, and `results/` are intentionally excluded
from the image (see `.dockerignore`) — mount them as volumes so downloaded
data and results persist on the host across container restarts.

If you'd rather skip Docker, a bare venv works too:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## 4. Get the data

Same as the main README: download from the
[Google Drive folder](https://drive.google.com/drive/folders/1tGDTPhQ1-oy61lqSv00nJSP84Oai31I5?usp=sharing)
directly on the instance with `gdown`, or `rsync`/`scp` your already-extracted
local `data/` and `reproduce_main_data/` folders up:

```bash
# from your local machine
rsync -avz --progress reproduce_main_data/ user@<instance-ip>:~/REPaL/reproduce_main_data/
```

Prefer `gdown` on the instance directly if your link-up bandwidth is limited —
downloading straight from Google Drive to the GPU box is usually faster than
uploading from a home connection.

## 5. Run

With a >=16GB card, drop `small_gpu` in favor of the `gpu` profile (or let it
auto-detect by omitting `--device-profile`):

```bash
python run_experiments.py \
  --datasets fewrel_defon wikizsl_defon \
  --data-root reproduce_main_data/data \
  --device-profile gpu \
  --skip-existing --continue-on-error
```

Everything under `results/` (`summary.csv`, `aggregate.csv`, per-run logs) is
plain text/CSV/JSON, so it round-trips fine over `rsync`/`scp` back to your
local machine when a sweep finishes.

## Known non-blockers carried over from local runs

- The `BCELoss`-under-`autocast` crash and the Windows-console UTF-8 crash
  (both fixed in `src/trainer.py`, `src/run.py`, `run_experiments.py`) only
  ever affected the `small_gpu`/AMP + Windows combination. On a Linux vast.ai
  box without `--use_amp`, neither should trigger, but the fixes are harmless
  either way and already committed.
- `src/trainer.py` has a `spacy.load("en_core_web_trf")` call in the
  `followup` stage's feedback-mining path (`_get_rels_pos_examples_followup`),
  gated behind a cache-file check. It's never been exercised locally because
  `reproduce_main_data/data`'s cached checkpoints always short-circuit past
  it, and `spacy-transformers`/`en_core_web_trf` aren't in `requirements.txt`.
  If you hit `OSError: Can't find model 'en_core_web_trf'` on a fresh dataset
  (not the cached reproduce data), install it with:
  ```bash
  pip install spacy-transformers
  python -m spacy download en_core_web_trf
  ```
