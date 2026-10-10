#!/usr/bin/env bash
# After the fewrel_defon10k runs finish: start the Qwen3-32B service (thinking disabled) on GPU 0, check
# that its replies contain no <think> reasoning and survive the repo's JSON parser, then run semeval_qwen3
# (initial -> followup) on GPU 1. Refuses to start the run if the check fails.
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
while pgrep -f "run_experiments.py --datasets fewrel_defon10k" >/dev/null; do sleep 60; done
echo "$(date -Is) fewrel_defon10k finished; starting qwen3-llm"
supervisorctl stop qwen-llm >/dev/null 2>&1; supervisorctl start qwen3-llm
for i in $(seq 1 90); do curl -sf http://127.0.0.1:8000/v1/models >/dev/null && break; sleep 10; done
curl -sf http://127.0.0.1:8000/v1/models >/dev/null || { echo "qwen3-llm did not come up"; exit 1; }
cd /root && OPENAI_BASE_URL=http://127.0.0.1:8000/v1 OPENAI_API_KEY=local-no-key \
  PYTHONPATH=/workspace/REPaL/src /venv/main/bin/python - <<'PY' || { echo "$(date -Is) Qwen3 check FAILED, not launching"; exit 1; }
import json, sys
from model import GPTCompletionModel
from llm_gen import parse_chat_response_to_examples_LLM_json_parser
M = "Qwen/Qwen3-32B-AWQ"
rel = json.load(open("/workspace/REPaL/data/semeval_qwen3_1/rel_info_updated.json"))["Entity-Origin(e2,e1)"]
g = GPTCompletionModel(GPT_model=M, save_filepath="/root/qwen3_check.jsonl", api_key="local-no-key")
g.update_call_attributes(max_tokens=4096, seed=3, temperature=0.6)
r = g(input={"task_id": 0, "messages": [{"role": "user", "content": "A binary relation between entity placeholders <ENT0> and <ENT1> is defined by \"" + rel["typed_desc_prompt"] + "\". Under sentence-level relation extraction setting, generate 5 examples (numbered from 1 to 5) expressing the same relation, where <ENT0> is replaced with actual entity mention and is prefixed with tag <ENT0> and suffixed with tag </ENT0> , <ENT1> is replaced with actual entity mention and is prefixed with tag <ENT1> and suffixed with </ENT1> ."}]})
c = r.choices[0].message.content or ""
print(c[:600])
if "<think>" in c or not c.strip(): sys.exit("thinking text present or empty reply")
ex = parse_chat_response_to_examples_LLM_json_parser(r, relation="Entity-Origin(e2,e1)", num_examples=5, llm_model_ckpt=M)
print("parsed examples:", len(ex))
if len(ex) < 3: sys.exit("parser accepted fewer than 3 of 5")
PY
cd /workspace/REPaL && echo "$(date -Is) Qwen3 check passed; launching semeval_qwen3 on GPU 1"
LLM=Qwen/Qwen3-32B-AWQ GPU=1 PROFILE=gpu tools/run_local_llm.sh semeval_qwen3
