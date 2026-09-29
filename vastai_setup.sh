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

GDRIVE_FOLDER_URL="https://drive.google.com/drive/folders/1tGDTPhQ1-oy61lqSv00nJSP84Oai31I5"

if [ "$RUN_ONLY" = false ]; then
  echo "==> [1/4] System packages"
  if command -v apt-get >/dev/null 2>&1; then
    apt-get update -qq
    apt-get install -y --no-install-recommends git build-essential >/dev/null
  fi

  echo "==> [2/4] Python packages"
  pip install --no-cache-dir -r requirements.txt
  pip install --no-cache-dir gdown

  echo "==> [3/4] Data"
  if [ -d data ] && [ -d reproduce_main_data ]; then
    echo "    data/ and reproduce_main_data/ already present, skipping download."
  else
    echo "    Downloading dataset archives from Google Drive..."
    gdown --folder "$GDRIVE_FOLDER_URL" -O gdrive_download --quiet

    if [ ! -d data ] && [ -f gdrive_download/data.tar.gz ]; then
      tar -xf gdrive_download/data.tar.gz
    fi
    if [ ! -d reproduce_main_data ] && [ -f gdrive_download/reproduce_main_data.tar.gz ]; then
      tar -xf gdrive_download/reproduce_main_data.tar.gz
    fi
    rm -rf gdrive_download

    if [ ! -d data ] || [ ! -d reproduce_main_data ]; then
      echo "    WARNING: expected data/ and reproduce_main_data/ after extraction but at least one is missing." >&2
      echo "    Check the Google Drive folder contents / archive names haven't changed, or rsync them up manually (see docs/VASTAI.md)." >&2
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
