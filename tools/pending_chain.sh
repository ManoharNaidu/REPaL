#!/usr/bin/env bash
# Remaining runs (2026-10-09), local LLMs only, training on GPU 1, LLM service on GPU 0:
#   1. fewrel_defon10k splits 1-2, followup stage (initial already done with cached GPT-4o seeds; skipped)
#      generator for the follow-up examples: Qwen2.5-32B-Instruct-AWQ (service qwen-llm)
#   2. nyt_qwen3, initial -> followup, Qwen3-32B-AWQ (service qwen3-llm), regex example parser
# Jobs run in the foreground of this script, one after another (no pattern-based waiting).
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
log() { echo "$(date -Is) $*"; }
up() { for i in $(seq 1 90); do curl -sf http://127.0.0.1:8000/v1/models >/dev/null && return 0; sleep 10; done; return 1; }

log "step 1: qwen-llm (Qwen2.5) for fewrel_defon10k followup"
supervisorctl stop qwen3-llm >/dev/null 2>&1; supervisorctl start qwen-llm
if up; then
  LLM=Qwen/Qwen2.5-32B-Instruct-AWQ GPU=1 PROFILE=gpu EXTRA_ARGS='--dist-port 14345' \
    tools/run_local_llm.sh fewrel_defon10k > results/logs/fewrel10k_followup.log 2>&1
  log "fewrel_defon10k followup exited $?"
else log "qwen-llm did not come up; skipping fewrel_defon10k followup"; fi

log "step 2: qwen3-llm (Qwen3) for nyt_qwen3"
supervisorctl stop qwen-llm; supervisorctl start qwen3-llm
if up; then
  LLM=Qwen/Qwen3-32B-AWQ GPU=1 PROFILE=gpu EXTRA_ARGS='--regex-example-parser --dist-port 14345' \
    tools/run_local_llm.sh nyt_qwen3 > results/logs/nyt_qwen3.log 2>&1
  log "nyt_qwen3 exited $?"
else log "qwen3-llm did not come up; skipping nyt_qwen3"; fi
supervisorctl stop qwen3-llm
log "all remaining runs finished; LLM service stopped"
