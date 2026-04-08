#!/usr/bin/env bash
# =============================================================================
# GULA Platform — Ollama Local AI Setup
# Installs Ollama and pulls the right models for the server's RAM.
#
# Usage: bash scripts/setup-ollama.sh [--force-large]
#   (no flag)      Auto-detect RAM and pick appropriate models (RECOMMENDED)
#   --force-large  Force aya:8b even on small servers (requires ≥16 GB RAM)
#
# Model selection (automatic):
#   RAM < 8 GB  → llama3.2:3b (2 GB, good Arabic, safe for 4 GB servers)
#   RAM ≥ 8 GB  → llama3.2:3b (still recommended — aya:8b needs ≥16 GB)
#   RAM ≥ 16 GB → aya:8b      (best Arabic quality, 4.8 GB model)
#
# IMPORTANT: aya:8b loads ~6 GB into RAM at inference time.
# On a 4 GB server it causes swap thrashing and OOM crashes.
# Always use llama3.2:3b on servers with less than 16 GB RAM.
# =============================================================================
set -euo pipefail

FORCE_LARGE=false
for arg in "$@"; do
    [[ "$arg" == "--force-large" ]] && FORCE_LARGE=true
done

echo "=== GULA Platform — Ollama Local AI Setup ==="
echo ""

# ── Detect available RAM ──────────────────────────────────────────────────────
TOTAL_RAM_MB=$(awk '/MemTotal/ {print int($2/1024)}' /proc/meminfo 2>/dev/null || echo 0)
TOTAL_RAM_GB=$((TOTAL_RAM_MB / 1024))
echo "[i] Server RAM: ${TOTAL_RAM_GB} GB (${TOTAL_RAM_MB} MB)"

# Safety gate: aya:8b needs ~6 GB just for inference + OS/containers overhead
if $FORCE_LARGE; then
    if [[ $TOTAL_RAM_GB -lt 16 ]]; then
        echo ""
        echo "⚠️  WARNING: --force-large specified but RAM is only ${TOTAL_RAM_GB} GB."
        echo "    aya:8b requires ≥16 GB. You risk OOM crashes and swap thrashing."
        echo "    Proceeding anyway as requested..."
        echo ""
    fi
    USE_AYA=true
elif [[ $TOTAL_RAM_GB -ge 16 ]]; then
    USE_AYA=true
    echo "[i] RAM ≥16 GB — will pull aya:8b for best Arabic quality"
else
    USE_AYA=false
    echo "[i] RAM <16 GB — using llama3.2:3b (safe, good Arabic, 2 GB)"
    if [[ $TOTAL_RAM_GB -lt 8 ]]; then
        echo ""
        echo "⚠️  RAM is only ${TOTAL_RAM_GB} GB. Docker + PostgreSQL + backend use ~2.5 GB."
        echo "    Ollama with llama3.2:3b uses ~2 GB more. Monitor with: watch -n2 free -h"
        echo ""
    fi
fi

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
        ollama serve &>/tmp/ollama.log &
        sleep 3
    fi
fi

if curl -sf http://localhost:11434/api/tags &>/dev/null; then
    echo "[✓] Ollama service running at http://localhost:11434"
else
    echo "[✗] Ollama service not responding — check: journalctl -u ollama -n 20"
    exit 1
fi

# ── 3. Pull required models ────────────────────────────────────────────────────
echo ""
echo "[→] Pulling system optimizer model (llama3.2:1b — ~700 MB, fast)..."
ollama pull llama3.2:1b

echo ""
echo "[→] Pulling clinical interpretation model (llama3.2:3b — ~2 GB)..."
ollama pull llama3.2:3b

if $USE_AYA; then
    echo ""
    echo "[→] Pulling high-quality Arabic model (aya:8b — ~4.8 GB)..."
    ollama pull aya:8b
fi

# ── 4. Verify models ───────────────────────────────────────────────────────────
echo ""
echo "[✓] Installed models:"
ollama list

# ── 5. Quick Arabic inference smoke test ──────────────────────────────────────
echo ""
echo "[→] Running Arabic inference smoke test (llama3.2:3b)..."
if ollama run llama3.2:3b "قل كلمة 'جاهز' فقط بدون أي شيء آخر" --nowordwrap 2>/dev/null | grep -q "."; then
    echo "[✓] Arabic inference: working"
else
    echo "[!] Inference test inconclusive — model should still work via API"
fi

# ── 6. Select clinical model based on RAM ─────────────────────────────────────
if $USE_AYA && ollama list 2>/dev/null | grep -q "aya:8b"; then
    CLINICAL_MODEL="aya:8b"
else
    CLINICAL_MODEL="llama3.2:3b"
fi

# ── 7. Print .env config ───────────────────────────────────────────────────────
echo ""
echo "=== Add these to your .env file ==="
echo "OLLAMA_BASE_URL=http://host.docker.internal:11434"
echo "OLLAMA_CLINICAL_MODEL=${CLINICAL_MODEL}"
echo "OLLAMA_MODEL=llama3.2:1b"
echo "OLLAMA_TIMEOUT=20"
echo ""

if [[ "$CLINICAL_MODEL" == "llama3.2:3b" ]] && ollama list 2>/dev/null | grep -q "aya:8b"; then
    echo "ℹ️  aya:8b is installed but NOT recommended for ${TOTAL_RAM_GB} GB RAM."
    echo "   Upgrade to ≥16 GB RAM to safely use it."
    echo ""
fi

echo "=== Setup complete ==="
echo "RAM usage after model load: run  watch -n2 free -h  to monitor"
echo "Verify API: curl http://localhost:11434/api/tags | python3 -m json.tool"
echo "Platform:   curl http://localhost/api/ai/providers  (after deploy)"
