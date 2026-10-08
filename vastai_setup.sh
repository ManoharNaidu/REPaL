#!/usr/bin/env bash
# One-shot setup + run script for a fresh vast.ai instance.
#
# Usage (on the instance, after `git clone` into this repo):
#   bash vastai_setup.sh              # setup + run the full fewrel_defon + wikizsl_defon sweep
#   bash vastai_setup.sh --setup-only # install deps + fetch data, don't start training
#   bash vastai_setup.sh --run-only   # skip setup, just (re)start the sweep
#
# See docs/VASTAI.md for the full walkthrough and GPU sizing notes.

set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

SETUP_ONLY=false
RUN_ONLY=false
for arg in "$@"; do
  case "$arg" in
    --setup-only) SETUP_ONLY=true ;;
    --run-only) RUN_ONLY=true ;;
    *) echo "Unknown argument: $arg" >&2; exit 1 ;;
  esac
done

HF_DATASET_REPO="Manu2711/Application_of_DS-REPaL"

# vast.ai PyTorch images keep torch in /venv/main, which is only on PATH in
# interactive login shells -- activate it so nohup/ssh/non-interactive runs
# find python/pip (and install into the env that has the arch-matched torch).
if [ -z "${VIRTUAL_ENV:-}" ] && [ -f /venv/main/bin/activate ]; then
  # shellcheck disable=SC1091
  source /venv/main/bin/activate
fi

if [ "$RUN_ONLY" = false ]; then
  echo "==> [1/4] System packages"
  if command -v apt-get >/dev/null 2>&1; then
    apt-get update -qq
    apt-get install -y --no-install-recommends git build-essential >/dev/null
  fi

  echo "==> [2/4] Python packages"
  # requirements.txt leaves torch unpinned so an image's preinstalled, arch-matched
  # torch build is kept (a cu121 torch 2.4 has no kernels for Blackwell GPUs).
  pip install --no-cache-dir -r requirements.txt
  pip install --no-cache-dir "huggingface_hub[cli]"

  echo "==> [3/4] Data"
  if [ -d data ] && [ -d reproduce_main_data ]; then
    echo "    data/ and reproduce_main_data/ already present, skipping download."
  else
    echo "    Downloading dataset from Hugging Face ($HF_DATASET_REPO)..."
    hf download "$HF_DATASET_REPO" --repo-type dataset --local-dir .
    # The dataset repo ships its own LFS .gitattributes (which marks *.png etc. as
    # LFS); dropped into this repo root it makes git see figures/*.png as modified.
    rm -f .gitattributes

    if [ ! -d data ] || [ ! -d reproduce_main_data ]; then
      echo "    WARNING: expected data/ and reproduce_main_data/ after download but at least one is missing." >&2
      echo "    Check the dataset repo contents haven't changed, or rsync them up manually (see docs/VASTAI.md)." >&2
    fi
  fi

  mkdir -p .hf_cache results
else
  echo "==> Skipping setup (--run-only)"
fi

if [ "$SETUP_ONLY" = true ]; then
  echo "==> Setup complete (--setup-only). Not starting the sweep."
  exit 0
fi

echo "==> [4/4] Running experiment sweep"
python run_experiments.py \
  --datasets fewrel_defon wikizsl_defon \
  --data-root reproduce_main_data/data \
  --device-profile gpu \
  --skip-existing --continue-on-error
