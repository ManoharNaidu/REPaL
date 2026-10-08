#!/usr/bin/env bash
# Run REPaL with a local open-weight LLM (vLLM, supervisor service "qwen-llm" on GPU 0, 127.0.0.1:8000)
# instead of OpenAI. All OpenAI-client calls in src/ honour OPENAI_BASE_URL; no real key is used.
# Training GPU and batch profile: GPU (default 1), PROFILE (default gpu; use gpu_shared next to vLLM on GPU 0).
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
source /venv/main/bin/activate
export OPENAI_BASE_URL=http://127.0.0.1:8000/v1 OPENAI_API_KEY=local-no-key
export BASE_LLM=Qwen/Qwen2.5-32B-Instruct-AWQ PARSER_LLM=Qwen/Qwen2.5-32B-Instruct-AWQ
export HF_HOME=/root/hf_fresh HUGGINGFACE_CACHE_DIR=/root/hf_fresh CUDA_VISIBLE_DEVICES=${GPU:-1}
curl -sf "$OPENAI_BASE_URL/models" >/dev/null || { echo "local LLM server not reachable at $OPENAI_BASE_URL" >&2; exit 1; }
for ds in "$@"; do
  python -u run_experiments.py --datasets "$ds" --device-profile ${PROFILE:-gpu} --skip-existing --continue-on-error
done
