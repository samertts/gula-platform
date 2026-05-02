#!/usr/bin/env bash
# =============================================================================
# GULA Platform — Post-deploy smoke + perf gate
#
# Run this AFTER `bash setup-production.sh` (or `make up`) succeeds.
# It verifies the live system end-to-end and prints latency / error-rate
# numbers so you can decide whether the deployment is actually production-ready
# or only "containers are running."
#
# Phases (each phase HALTS the script on failure — no silent fall-through):
#   1.  Liveness:    /health               → 200
#   2.  Readiness:   /health/ready         → 200
#   3.  Deep grade:  /health/deep          → grade is GREEN or YELLOW (RED fails)
#   4.  Auth:        POST /login           → returns JWT + user payload
#   5.  Authed GET:  /dashboard with JWT   → 200 + JSON
#   6.  Latency:     100 sequential /health calls → p50 / p95 / p99 ms
#   7.  Error rate:  100 calls error rate           → must be 0 %
#
# Usage:
#   bash scripts/smoke-bootstrap.sh                        # localhost gateway
#   bash scripts/smoke-bootstrap.sh https://api.gula.iq   # public domain
#
# Exit codes:
#   0  all phases passed — deployment verified live
#   1  any phase failed
# =============================================================================
set -euo pipefail

BASE_URL="${1:-http://127.0.0.1:8080}"
ADMIN_EMAIL="${GULA_ADMIN_EMAIL:-}"
ADMIN_PASSWORD="${GULA_ADMIN_PASSWORD:-}"

# Load admin creds from .env if not exported
if [ -z "$ADMIN_EMAIL" ] || [ -z "$ADMIN_PASSWORD" ]; then
    if [ -f .env ]; then
        ADMIN_EMAIL="${ADMIN_EMAIL:-$(grep -E '^GULA_ADMIN_EMAIL=' .env | cut -d= -f2- | tr -d '"' || true)}"
        ADMIN_PASSWORD="${ADMIN_PASSWORD:-$(grep -E '^GULA_ADMIN_PASSWORD=' .env | cut -d= -f2- | tr -d '"' || true)}"
    fi
fi

# ── Colors ──────────────────────────────────────────────────────────────────
GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'

phase()  { echo -e "\n${CYAN}${BOLD}── Phase $1 — $2 ──${NC}"; }
ok()     { echo -e "${GREEN}  [✓] $*${NC}"; }
fail()   { echo -e "${RED}  [✗] $*${NC}" >&2; exit 1; }
warn()   { echo -e "${YELLOW}  [!] $*${NC}"; }
info()   { echo -e "    $*"; }

command -v curl >/dev/null || fail "curl not installed"
command -v jq   >/dev/null || fail "jq not installed (apt install -y jq)"

echo -e "${BOLD}Target:${NC} $BASE_URL"

# ── Phase 1: Liveness ────────────────────────────────────────────────────────
phase 1 "Liveness probe (/health)"
code=$(curl -sS -o /dev/null -w '%{http_code}' --max-time 5 "$BASE_URL/health" || echo 000)
[ "$code" = "200" ] && ok "/health → 200" || fail "/health returned $code (expected 200)"

# ── Phase 2: Readiness ───────────────────────────────────────────────────────
phase 2 "Readiness probe (/health/ready)"
code=$(curl -sS -o /dev/null -w '%{http_code}' --max-time 5 "$BASE_URL/health/ready" || echo 000)
[ "$code" = "200" ] && ok "/health/ready → 200" || fail "/health/ready returned $code (expected 200) — startup guard has not signalled ready"

# ── Phase 3: Deep health grade ───────────────────────────────────────────────
phase 3 "Deep health (/health/deep)"
deep=$(curl -sS --max-time 10 "$BASE_URL/health/deep" || echo '{}')
grade=$(echo "$deep" | jq -r '.grade // .status // "UNKNOWN"')
case "$grade" in
    GREEN)  ok "Grade: GREEN" ;;
    YELLOW) warn "Grade: YELLOW (degraded but serving — investigate after smoke completes)" ;;
    RED)    fail "Grade: RED — system is not production-ready. Run \`make logs-backend\`" ;;
    *)      fail "Could not parse grade from /health/deep response" ;;
esac
db_ms=$(echo "$deep" | jq -r '.checks.database.latency_ms // .components.database.latency_ms // empty')
[ -n "$db_ms" ] && info "DB latency: ${db_ms} ms"

# ── Phase 4: Auth ────────────────────────────────────────────────────────────
phase 4 "Login as admin (POST /login)"
[ -n "$ADMIN_EMAIL" ] && [ -n "$ADMIN_PASSWORD" ] || fail "GULA_ADMIN_EMAIL / GULA_ADMIN_PASSWORD not set in .env"
[ "$ADMIN_PASSWORD" != "CHANGE_ME_STRONG_ADMIN_PASSWORD" ] || fail "Admin password is still the placeholder — set a real one in .env"

login_resp=$(curl -sS --max-time 10 -X POST "$BASE_URL/login" \
    -H 'Content-Type: application/json' \
    -d "$(jq -nc --arg e "$ADMIN_EMAIL" --arg p "$ADMIN_PASSWORD" '{email:$e,password:$p}')" || echo '{}')
token=$(echo "$login_resp" | jq -r '.token // empty')
user_role=$(echo "$login_resp" | jq -r '.user.role // empty')
[ -n "$token" ] || fail "Login returned no token. Response: $login_resp"
ok "Login succeeded — role=$user_role token=${token:0:12}…"

# ── Phase 5: Authenticated GET ───────────────────────────────────────────────
phase 5 "Authenticated GET (/dashboard)"
code=$(curl -sS -o /tmp/dashboard.json -w '%{http_code}' --max-time 10 \
    -H "Authorization: Bearer $token" "$BASE_URL/dashboard" || echo 000)
case "$code" in
    200) ok "/dashboard → 200 ($(wc -c </tmp/dashboard.json) bytes)" ;;
    401|403) fail "/dashboard rejected the JWT — auth chain is broken (HTTP $code)" ;;
    404) warn "/dashboard not present in this build — skipping (auth still verified by phase 4)" ;;
    *)   fail "/dashboard returned $code" ;;
esac

# ── Phase 6: Latency under sequential load ───────────────────────────────────
phase 6 "Latency — 100 sequential /health calls"
tmp=$(mktemp)
for _ in $(seq 1 100); do
    curl -sS -o /dev/null -w '%{time_total}\n' --max-time 5 "$BASE_URL/health" >>"$tmp" 2>/dev/null || echo "9.999" >>"$tmp"
done
sort -g "$tmp" >"${tmp}.sorted"
p50_s=$(awk 'NR==50' "${tmp}.sorted")
p95_s=$(awk 'NR==95' "${tmp}.sorted")
p99_s=$(awk 'NR==99' "${tmp}.sorted")
p50_ms=$(awk -v v="$p50_s" 'BEGIN{printf "%d", v*1000}')
p95_ms=$(awk -v v="$p95_s" 'BEGIN{printf "%d", v*1000}')
p99_ms=$(awk -v v="$p99_s" 'BEGIN{printf "%d", v*1000}')
rm -f "$tmp" "${tmp}.sorted"

info "p50 = ${p50_ms} ms   p95 = ${p95_ms} ms   p99 = ${p99_ms} ms"
[ "$p95_ms" -lt 500 ] && ok "p95 < 500 ms" || fail "p95 ${p95_ms} ms exceeds 500 ms target — investigate before announcing prod"

# ── Phase 7: Error rate ──────────────────────────────────────────────────────
phase 7 "Error rate — 100 calls"
errors=0
for _ in $(seq 1 100); do
    code=$(curl -sS -o /dev/null -w '%{http_code}' --max-time 5 "$BASE_URL/health" 2>/dev/null || echo 000)
    [ "$code" != "200" ] && errors=$((errors+1))
done
info "errors = ${errors}/100"
[ "$errors" -eq 0 ] && ok "Error rate: 0 %" || fail "Error rate ${errors}% — instability detected"

# ── Done ─────────────────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}${BOLD}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}${BOLD}║  Smoke gate PASSED — system verified live           ║${NC}"
echo -e "${GREEN}${BOLD}║  منصة غولا — تم التحقق من النظام الحي              ║${NC}"
echo -e "${GREEN}${BOLD}╚══════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "Next checkpoints:"
echo -e "  • Switch to HTTPS:    bash scripts/setup-https.sh <domain>"
echo -e "  • Configure CD secrets in GitHub:  SERVER_HOST, SERVER_USER, SERVER_SSH_KEY"
echo -e "  • Push the mobile build:           flutter build appbundle --dart-define=API_URL=$BASE_URL"
echo -e "  • Schedule backups:                set BACKUP_ENABLED=true in .env, then make restart"
