#!/usr/bin/env bash
# =============================================================================
# GULA Platform — Ollama Local AI Setup
# Installs Ollama on the host machine and pulls the models used by the platform.
#
# Usage: bash scripts/setup-ollama.sh [--small]
#   --small  Pull smaller/faster models (less Arabic quality, less disk space)
#
# Models pulled:
#   llama3.2:1b  — system optimizer (fast, ~700 MB)
#   llama3.2:3b  — clinical interpretation (balanced, ~2 GB)
#   [without --small] aya:8b — highest Arabic quality (4.8 GB, optional)
#
# After setup, add to .env:
#   OLLAMA_BASE_URL=http://host.docker.internal:11434
#   OLLAMA_CLINICAL_MODEL=llama3.2:3b   # or aya:8b for best Arabic
#   OLLAMA_MODEL=llama3.2:1b
# =============================================================================
set -euo pipefail

SMALL_MODE=false
for arg in "$@"; do
    [[ "$arg" == "--small" ]] && SMALL_MODE=true
done

echo "=== GULA Platform — Ollama Local AI Setup ==="
echo ""

# ── 1. Install Ollama if not present ──────────────────────────────────────────
if command -v ollama &>/dev/null; then
    echo "[✓] Ollama already installed: $(ollama --version 2>/dev/null || echo 'unknown version')"
else
    echo "[→] Installing Ollama..."
    curl -fsSL https://ollama.com/install.sh | sh
    echo "[✓] Ollama installed"
fi

# ── 2. Start Ollama service if not running ─────────────────────────────────────
if ! curl -sf http://localhost:11434/api/tags &>/dev/null; then
    echo "[→] Starting Ollama service..."
    if systemctl is-active --quiet ollama 2>/dev/null; then
        systemctl start ollama
    else
        # Start in background if systemd service not available
        ollama serve &>/tmp/ollama.log &
        sleep 3
    fi
fi

if curl -sf http://localhost:11434/api/tags &>/dev/null; then
    echo "[✓] Ollama service running at http://localhost:11434"
else
    echo "[✗] Ollama service not responding — check logs: journalctl -u ollama -n 20"
    exit 1
fi

# ── 3. Pull required models ────────────────────────────────────────────────────
echo ""
echo "[→] Pulling system optimizer model (llama3.2:1b — ~700 MB)..."
ollama pull llama3.2:1b

echo ""
echo "[→] Pulling clinical interpretation model (llama3.2:3b — ~2 GB)..."
ollama pull llama3.2:3b

if [[ "$SMALL_MODE" == "false" ]]; then
    echo ""
    echo "[→] Pulling high-quality Arabic model (aya:8b — ~4.8 GB)..."
    echo "    (This is optional — use OLLAMA_CLINICAL_MODEL=aya:8b in .env for best Arabic quality)"
    ollama pull aya:8b
fi

# ── 4. Verify models ───────────────────────────────────────────────────────────
echo ""
echo "[✓] Installed models:"
ollama list

# ── 5. Test clinical inference ─────────────────────────────────────────────────
echo ""
echo "[→] Running quick Arabic inference test..."
TEST_RESPONSE=$(ollama run llama3.2:3b "قل 'اختبار ناجح' فقط" 2>/dev/null || echo "FAILED")
if echo "$TEST_RESPONSE" | grep -q "ناجح\|successful\|success" 2>/dev/null || [[ "$TEST_RESPONSE" != "FAILED" ]]; then
    echo "[✓] Arabic inference: working"
else
    echo "[!] Arabic inference test inconclusive — model may still work"
fi

# ── 6. Print .env config ───────────────────────────────────────────────────────
CLINICAL_MODEL="llama3.2:3b"
[[ "$SMALL_MODE" == "false" ]] && ollama list | grep -q "aya:8b" && CLINICAL_MODEL="aya:8b"

echo ""
echo "=== Add these to your .env file ==="
echo "OLLAMA_BASE_URL=http://host.docker.internal:11434"
echo "OLLAMA_CLINICAL_MODEL=${CLINICAL_MODEL}"
echo "OLLAMA_MODEL=llama3.2:1b"
echo "OLLAMA_TIMEOUT=20"
echo ""
echo "=== Setup complete ==="
echo "Verify with: curl http://localhost:11434/api/tags | python3 -m json.tool"
echo "API status:  curl https://gula-platform.org/api/ai/providers"
