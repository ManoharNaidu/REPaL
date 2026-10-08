#!/usr/bin/env bash
# Run the remaining REPaL jobs on a 2-GPU box, one job-chain pinned to each GPU.
#
#   GPU 0: wikizsl_defon split 1, then split 3
#   GPU 1: wikizsl_defon split 2, then fewrel_defon split 5
#
# Each chain is sequential (a split's followup stage needs its initial stage), the
# two chains run in parallel. CUDA_VISIBLE_DEVICES gives every job exactly one GPU,
# so the code does not switch to DataParallel/multi-GPU inference for a single job.
# --skip-existing makes a re-run resume: finished (split, stage) pairs are skipped.
#
# Usage:  bash run_2gpu.sh            # start both chains in the background
#         bash run_2gpu.sh --dry-run  # print what would run
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

if [ -z "${VIRTUAL_ENV:-}" ] && [ -f /venv/main/bin/activate ]; then
  # shellcheck disable=SC1091
  source /venv/main/bin/activate
fi

NGPU=$(python -c 'import torch; print(torch.cuda.device_count())')
if [ "$NGPU" -lt 2 ]; then
  echo "Found $NGPU GPU(s); this script expects 2. Aborting." >&2
  exit 1
fi

DATA_ROOT=reproduce_main_data/data
COMMON=(--data-root "$DATA_ROOT" --device-profile gpu --skip-existing --continue-on-error)
mkdir -p results/logs

# run <gpu> <dataset> <split>
run() {
  CUDA_VISIBLE_DEVICES="$1" python -u run_experiments.py --datasets "$2" --splits "$3" "${COMMON[@]}"
}

chain0() { run 0 wikizsl_defon 1; run 0 wikizsl_defon 3; }
chain1() { run 1 wikizsl_defon 2; run 1 fewrel_defon 5; }

if [ "${1:-}" = "--dry-run" ]; then
  echo "GPU0: wikizsl_defon 1 -> wikizsl_defon 3"
  echo "GPU1: wikizsl_defon 2 -> fewrel_defon 5"
  exit 0
fi

# Separate logs per chain. Start the second chain late so the two jobs don't pick
# the same distributed-inference port at the same instant.
setsid nohup bash -c "$(declare -f run chain0); COMMON=(${COMMON[*]}); chain0" > results/logs/gpu0.log 2>&1 < /dev/null &
sleep 45
setsid nohup bash -c "$(declare -f run chain1); COMMON=(${COMMON[*]}); chain1" > results/logs/gpu1.log 2>&1 < /dev/null &

echo "Started. Logs: results/logs/gpu0.log, results/logs/gpu1.log"
echo "When both chains finish: python run_experiments.py --aggregate-only"
