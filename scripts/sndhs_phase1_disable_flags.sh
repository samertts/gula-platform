#!/usr/bin/env bash
#
# SNDHS-lite Phase 1 — emergency feature-flag disable.
#
# Flips the deployment-wide flags off and triggers a graceful restart
# of the backend. Use this BEFORE running any schema rollback.
#
#   bash scripts/sndhs_phase1_disable_flags.sh
#
# Idempotent. Safe to run during an active incident.

set -euo pipefail

ENV_FILE="${ENV_FILE:-.env}"

if [[ ! -f "${ENV_FILE}" ]]; then
    echo "ERROR: ${ENV_FILE} not found. Set ENV_FILE=... or run from repo root." >&2
    exit 1
fi

_ts="$(date -u +%Y%m%dT%H%M%SZ)"
cp -- "${ENV_FILE}" "${ENV_FILE}.bak.${_ts}"
echo "Backed up ${ENV_FILE} → ${ENV_FILE}.bak.${_ts}"

set_flag() {
    local key="$1"
    local val="$2"
    if grep -q "^${key}=" "${ENV_FILE}"; then
        # POSIX-portable in-place edit
        sed -i.bak "s|^${key}=.*|${key}=${val}|" "${ENV_FILE}"
        rm -f -- "${ENV_FILE}.bak"
    else
        printf '\n%s=%s\n' "${key}" "${val}" >> "${ENV_FILE}"
    fi
    echo "Set ${key}=${val}"
}

set_flag SNDHS_ENABLE_VISITS      false
set_flag SNDHS_ENABLE_NATIONAL_ID false

echo
echo "Restarting backend so the new env is picked up..."
if command -v docker >/dev/null 2>&1; then
    docker compose restart gula-backend || {
        echo "WARN: docker compose restart failed; restart the backend manually." >&2
    }
else
    echo "INFO: docker not available; restart the backend service manually." >&2
fi

echo "Done. Verify via: curl -fsS http://127.0.0.1:8000/health/status"
