#!/bin/bash
# =============================================================================
# GULA Platform - Pull Ollama Model
# Executive Order 3: Verify local AI is running
# =============================================================================

set -euo pipefail

OLLAMA_HOST="${OLLAMA_HOST:-http://localhost:11434}"
MODEL="${OLLAMA_MODEL:-llama3}"

echo "Checking Ollama availability at ${OLLAMA_HOST}..."

for i in {1..30}; do
    if curl -sf "${OLLAMA_HOST}/api/tags" > /dev/null 2>&1; then
        echo "Ollama is ready."
        break
    fi
    echo "Waiting for Ollama... (${i}/30)"
    sleep 5
done

echo "Pulling model: ${MODEL}"
curl -sf "${OLLAMA_HOST}/api/pull" \
    -H "Content-Type: application/json" \
    -d "{\"name\": \"${MODEL}\"}" \
    | while read -r line; do
        status=$(echo "$line" | python3 -c "import sys,json; d=json.loads(sys.stdin.read()); print(d.get('status',''))" 2>/dev/null || echo "")
        [ -n "$status" ] && echo "  $status"
    done

echo "Model pull complete. Available models:"
curl -sf "${OLLAMA_HOST}/api/tags" | python3 -c "
import sys, json
models = json.load(sys.stdin).get('models', [])
for m in models:
    print(f\"  - {m['name']}\")
"
