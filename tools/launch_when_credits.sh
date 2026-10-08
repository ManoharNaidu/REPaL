#!/usr/bin/env bash
# Wait until the OpenAI key can make a call (credits available), then start in parallel:
#   GPU 1: semeval followup (resumes from its cached iteration-0 checkpoints)
#   GPU 0: nyt initial -> followup
# Probe = one 1-token gpt-4o-mini call every 5 min (rejected without charge while the balance is 0).
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
set -a; . /workspace/.env; set +a
source /venv/main/bin/activate
export HF_HOME=/root/hf_fresh HUGGINGFACE_CACHE_DIR=/root/hf_fresh
probe() {
  curl -s https://api.openai.com/v1/chat/completions -H "Authorization: Bearer $OPENAI_API_KEY" \
    -H "Content-Type: application/json" \
    -d '{"model":"gpt-4o-mini-2024-07-18","messages":[{"role":"user","content":"hi"}],"max_tokens":1}' |
    python -c "import json,sys; d=json.load(sys.stdin); print('ok' if 'choices' in d else d.get('error',{}).get('code'))"
}
while true; do
  r=$(probe 2>/dev/null); echo "$(date -Is) probe: $r"
  [ "$r" = ok ] && break
  sleep 300
done
echo "$(date -Is) credits available, launching"
CUDA_VISIBLE_DEVICES=1 setsid nohup python -u run_experiments.py --datasets semeval --stages followup --device-profile gpu --continue-on-error >> results/logs/semeval.log 2>&1 < /dev/null &
sleep 45   # don't let both jobs pick the same distributed-inference port at once
CUDA_VISIBLE_DEVICES=0 setsid nohup python -u run_experiments.py --datasets nyt --device-profile gpu --skip-existing --continue-on-error >> results/logs/nyt.log 2>&1 < /dev/null &
echo "$(date -Is) launched semeval followup (GPU1) and nyt (GPU0)"
