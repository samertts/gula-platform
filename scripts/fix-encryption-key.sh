#!/usr/bin/env bash
# =============================================================================
# GULA Platform — Encryption Key Fix Script
#
# Fixes: ENCRYPTION_KEY in wrong format (legacy hex) → valid Fernet key
#
# Safe to run because:
#   - The encrypt()/decrypt() functions are not yet called in business logic
#   - No patient data has been encrypted with the old key
#   - This replaces the key in .env and restarts only the backend container
#
# Usage (run from the repository root as the deploy user):
#   bash scripts/fix-encryption-key.sh
#
# What it does:
#   1. Detects if ENCRYPTION_KEY is missing or not a valid Fernet key
#   2. Backs up .env with a timestamp
#   3. Generates a fresh Fernet key
#   4. Updates ENCRYPTION_KEY in .env in-place
#   5. Restarts gula-backend and verifies health
# =============================================================================
set -euo pipefail

RED='\033[1;31m'; GREEN='\033[1;32m'; CYAN='\033[1;36m'; YELLOW='\033[1;33m'; NC='\033[0m'
log()  { printf "${CYAN}[fix-key]${NC} %s\n" "$*"; }
ok()   { printf "${GREEN}[✓]${NC} %s\n" "$*"; }
warn() { printf "${YELLOW}[!]${NC} %s\n" "$*"; }
err()  { printf "${RED}[✗]${NC} %s\n" "$*" >&2; exit 1; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
ENV_FILE="${REPO_ROOT}/.env"

# ── 1. Verify .env exists ─────────────────────────────────────────────────────
[[ -f "${ENV_FILE}" ]] || err ".env not found at ${ENV_FILE}. Run server-setup.sh first."

log "Checking ENCRYPTION_KEY in ${ENV_FILE}..."

# ── 2. Read current key ───────────────────────────────────────────────────────
CURRENT_KEY=$(grep '^ENCRYPTION_KEY=' "${ENV_FILE}" | cut -d'=' -f2- | tr -d '\r\n')

if [[ -z "${CURRENT_KEY}" ]]; then
    warn "ENCRYPTION_KEY is not set — will generate a new one."
    NEEDS_FIX=true
else
    # Test if current key is a valid Fernet key
    if python3 - <<PYCHECK 2>/dev/null
from cryptography.fernet import Fernet
Fernet("${CURRENT_KEY}".encode())
PYCHECK
    then
        ok "ENCRYPTION_KEY is already a valid Fernet key (${#CURRENT_KEY} chars)."
        log "No fix needed. Exiting."
        exit 0
    else
        KEY_LEN=${#CURRENT_KEY}
        if [[ "${KEY_LEN}" -eq 64 ]] && [[ "${CURRENT_KEY}" =~ ^[0-9a-fA-F]+$ ]]; then
            warn "ENCRYPTION_KEY is a 64-char hex key (old format). Must be Fernet base64url."
        else
            warn "ENCRYPTION_KEY is invalid (length=${KEY_LEN}, not a valid Fernet key)."
        fi
        NEEDS_FIX=true
    fi
fi

# ── 3. Confirm before proceeding ─────────────────────────────────────────────
if [[ "${NEEDS_FIX:-false}" == "true" ]]; then
    echo ""
    echo "══════════════════════════════════════════════════════════"
    echo -e "${YELLOW} WARNING: This will replace ENCRYPTION_KEY in .env${NC}"
    echo "══════════════════════════════════════════════════════════"
    echo "  • Safe because: no patient data has been Fernet-encrypted yet"
    echo "  • .env will be backed up before modification"
    echo "  • Backend container will be restarted after the fix"
    echo ""

    # Auto-proceed if GULA_AUTO_FIX=true or stdin is not a terminal (CI/pipe)
    if [[ "${GULA_AUTO_FIX:-false}" != "true" ]] && [[ -t 0 ]]; then
        read -r -p "Proceed? [y/N] " CONFIRM
        [[ "${CONFIRM}" =~ ^[Yy]$ ]] || { log "Aborted."; exit 0; }
    else
        log "Auto-proceed (GULA_AUTO_FIX=true or non-interactive mode)."
    fi
fi

# ── 4. Generate new Fernet key ────────────────────────────────────────────────
log "Generating new Fernet key..."
NEW_KEY=$(python3 -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())')
[[ ${#NEW_KEY} -eq 44 ]] || err "Generated key has unexpected length (${#NEW_KEY}). Check Python/cryptography install."
ok "New Fernet key generated (44 chars, base64url)."

# ── 5. Back up .env ───────────────────────────────────────────────────────────
BACKUP="${ENV_FILE}.backup.$(date +%s)"
cp "${ENV_FILE}" "${BACKUP}"
chmod 600 "${BACKUP}"
ok ".env backed up → ${BACKUP}"

# ── 6. Update .env in-place ───────────────────────────────────────────────────
if grep -q '^ENCRYPTION_KEY=' "${ENV_FILE}"; then
    # Replace existing line
    sed -i "s|^ENCRYPTION_KEY=.*|ENCRYPTION_KEY=${NEW_KEY}|" "${ENV_FILE}"
else
    # Append if missing entirely
    echo "ENCRYPTION_KEY=${NEW_KEY}" >> "${ENV_FILE}"
fi
ok "ENCRYPTION_KEY updated in .env"

# ── 7. Verify the written key is valid ───────────────────────────────────────
WRITTEN_KEY=$(grep '^ENCRYPTION_KEY=' "${ENV_FILE}" | cut -d'=' -f2- | tr -d '\r\n')
python3 - <<PYCHECK || err "Written key verification failed — check ${ENV_FILE} manually."
from cryptography.fernet import Fernet
key = "${WRITTEN_KEY}".encode()
Fernet(key)
print("Key verified OK")
PYCHECK
ok "Key written to .env is a valid Fernet key."

# ── 8. Restart backend container ─────────────────────────────────────────────
log "Restarting gula-backend container..."
cd "${REPO_ROOT}"
docker compose up -d --force-recreate gula-backend
ok "gula-backend container restarted."

# ── 9. Wait for health ────────────────────────────────────────────────────────
log "Waiting up to 60s for backend to become healthy..."
for i in $(seq 1 20); do
    HTTP=$(curl -sf -o /dev/null -w '%{http_code}' http://localhost/health 2>/dev/null || echo "000")
    if [[ "${HTTP}" == "200" ]]; then
        ok "Backend healthy after $((i * 3))s (HTTP 200)."
        break
    fi
    if [[ "${i}" -eq 20 ]]; then
        warn "Backend not healthy after 60s (last HTTP=${HTTP})."
        warn "Check logs: docker logs gula-backend --tail 50"
        exit 1
    fi
    sleep 3
done

# ── 10. Deep health check ─────────────────────────────────────────────────────
log "Running deep health check..."
DEEP=$(curl -sf http://localhost/health/deep 2>/dev/null || echo '{}')
GRADE=$(echo "${DEEP}" | python3 -c 'import sys,json; d=json.load(sys.stdin); print(d.get("grade","?"))' 2>/dev/null || echo "?")
READY=$(echo "${DEEP}" | python3 -c 'import sys,json; d=json.load(sys.stdin); print(d.get("system_ready","?"))' 2>/dev/null || echo "?")

echo ""
echo "══════════════════════════════════════════════════════════"
echo -e "${GREEN} ENCRYPTION KEY FIX COMPLETE${NC}"
echo "══════════════════════════════════════════════════════════"
echo "  system_ready : ${READY}"
echo "  health grade : ${GRADE}"
echo "  backup at    : ${BACKUP}"
echo ""
echo "  Next: verify deep health"
echo "    curl http://localhost/health/deep | python3 -m json.tool"
echo "══════════════════════════════════════════════════════════"
