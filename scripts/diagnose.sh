#!/usr/bin/env bash
# =============================================================================
# GULA Platform — Server Diagnostics
# Run this ON THE SERVER to get a full picture of what's working and what isn't.
# Usage: ./scripts/diagnose.sh
# =============================================================================
set -uo pipefail

RED='\033[1;31m'; GREEN='\033[1;32m'; YELLOW='\033[1;33m'
CYAN='\033[1;36m'; NC='\033[0m'

pass() { printf "${GREEN}  ✓ %s${NC}\n" "$*"; }
fail() { printf "${RED}  ✗ %s${NC}\n" "$*"; }
warn() { printf "${YELLOW}  ⚠ %s${NC}\n" "$*"; }
info() { printf "${CYAN}  → %s${NC}\n" "$*"; }

echo ""
echo "══════════════════════════════════════════════════════════════════"
echo "  GULA Platform — Diagnostics  ($(date '+%Y-%m-%d %H:%M:%S'))"
echo "══════════════════════════════════════════════════════════════════"

# ─────────────────────────────────────────────────────────────────────────────
# 1. Docker
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo "── 1. Docker Containers ─────────────────────────────────────────"

if ! command -v docker >/dev/null 2>&1; then
  fail "Docker is not installed"
  exit 1
fi

CONTAINERS=(gula-backend gula-postgres gula-redis gula-api-gateway)
ALL_HEALTHY=true

for name in "${CONTAINERS[@]}"; do
  STATUS=$(docker inspect --format='{{.State.Status}}' "$name" 2>/dev/null || echo "missing")
  HEALTH=$(docker inspect --format='{{if .State.Health}}{{.State.Health.Status}}{{else}}no-healthcheck{{end}}' "$name" 2>/dev/null || echo "")

  if [ "$STATUS" = "running" ]; then
    if [ "$HEALTH" = "healthy" ] || [ "$HEALTH" = "no-healthcheck" ]; then
      pass "$name: $STATUS / $HEALTH"
    else
      fail "$name: $STATUS / $HEALTH"
      ALL_HEALTHY=false
      # Show last health check output
      LAST_LOG=$(docker inspect --format='{{if .State.Health}}{{range .State.Health.Log}}{{.Output}}{{end}}{{end}}' "$name" 2>/dev/null | tail -c 300 || true)
      [ -n "$LAST_LOG" ] && info "  Last healthcheck: $LAST_LOG"
    fi
  else
    fail "$name: $STATUS"
    ALL_HEALTHY=false
  fi
done

echo ""
echo "Container resource usage:"
docker stats --no-stream --format "  {{.Name}}\tCPU={{.CPUPerc}}\tMEM={{.MemUsage}}" \
  gula-backend gula-postgres gula-redis gula-api-gateway 2>/dev/null || true

# ─────────────────────────────────────────────────────────────────────────────
# 2. Network
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo "── 2. Network / Ports ───────────────────────────────────────────"

check_port() {
  local port="$1" label="$2"
  if ss -tlnp 2>/dev/null | grep -q ":${port} " || \
     netstat -tlnp 2>/dev/null | grep -q ":${port} "; then
    pass "Port $port ($label): LISTENING"
  else
    fail "Port $port ($label): NOT listening"
  fi
}

check_port 80  "HTTP"
check_port 443 "HTTPS"
check_port 8080 "Docker api-gateway"

# Check Docker api-gateway is on 127.0.0.1:8080 (not 0.0.0.0:80)
if ss -tlnp 2>/dev/null | grep -q "127.0.0.1:8080"; then
  pass "Docker api-gateway correctly bound to 127.0.0.1:8080 (not public)"
elif ss -tlnp 2>/dev/null | grep -E -q "0\.0\.0\.0:80|:::80"; then
  warn "Something is on 0.0.0.0:80 — possible port conflict with host nginx"
fi

# ─────────────────────────────────────────────────────────────────────────────
# 3. Health Endpoints (internal)
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo "── 3. Health Endpoints (internal) ──────────────────────────────"

check_url() {
  local url="$1" label="$2" expect="${3:-200}"
  local response http_code body
  http_code=$(curl -s -o /tmp/gula_diag_body -w "%{http_code}" --max-time 5 "$url" 2>/dev/null || echo "000")
  body=$(cat /tmp/gula_diag_body 2>/dev/null | head -c 200)

  if [ "$http_code" = "$expect" ]; then
    pass "$label → HTTP $http_code"
    [ -n "$body" ] && info "  $body"
  else
    fail "$label → HTTP $http_code (expected $expect)"
    [ -n "$body" ] && info "  $body"
  fi
}

# Direct Docker nginx (bypassing host nginx)
check_url "http://127.0.0.1:8080/health/live"  "Docker nginx /health/live"
check_url "http://127.0.0.1:8080/health"       "Backend /health (via Docker nginx)"
check_url "http://127.0.0.1:8080/health/ready" "Backend /health/ready (readiness)"

# Backend directly (bypassing all nginx)
BACKEND_IP=$(docker inspect --format='{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' gula-backend 2>/dev/null || echo "")
if [ -n "$BACKEND_IP" ]; then
  check_url "http://${BACKEND_IP}:8000/health"       "Backend direct /health"
  check_url "http://${BACKEND_IP}:8000/health/ready" "Backend direct /health/ready"
else
  warn "Cannot get backend container IP — container may be down"
fi

# Host nginx → Docker nginx (full proxy chain)
check_url "http://localhost/health"       "Full chain: host nginx → Docker → backend /health"
check_url "http://localhost/health/live"  "Full chain: host nginx → Docker → live probe"

# ─────────────────────────────────────────────────────────────────────────────
# 4. Backend Startup State
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo "── 4. Backend Startup / Logs ────────────────────────────────────"

if docker ps --format '{{.Names}}' 2>/dev/null | grep -q "^gula-backend$"; then
  echo "Last 40 backend log lines:"
  echo "──────────────────────────────────────────"
  docker logs gula-backend --tail=40 2>&1
  echo "──────────────────────────────────────────"

  # Check for common failure patterns
  LOGS=$(docker logs gula-backend --tail=100 2>&1)

  if echo "$LOGS" | grep -q "STARTUP GUARD.*FAILED\|STARTUP FAILED"; then
    fail "Startup guard FAILED — backend rejected startup"
    echo "$LOGS" | grep -E "STARTUP.*FAIL|CONFIG ERROR|RuntimeError" | head -5
  elif echo "$LOGS" | grep -q "system_ready.*=.*True\|System READY"; then
    pass "Startup guard passed — system_ready = True"
  elif echo "$LOGS" | grep -q "startup_in_progress"; then
    warn "Startup still in progress or guard not completed"
  fi

  if echo "$LOGS" | grep -q "SECRET_KEY.*not set\|ENCRYPTION_KEY.*not set\|NID_HMAC_KEY.*not set"; then
    fail "Missing required secrets in .env — startup guard will reject"
    info "Run: ./deploy.sh to auto-generate secrets"
  fi

  if echo "$LOGS" | grep -q "could not connect to server\|Connection refused.*5432\|database.*unreachable"; then
    fail "Backend cannot connect to PostgreSQL"
    info "Check: docker logs gula-postgres"
  fi

  if echo "$LOGS" | grep -q "redis.*Connection refused\|Cannot connect to Redis"; then
    fail "Backend cannot connect to Redis"
    info "Check: docker logs gula-redis"
  fi
else
  fail "gula-backend container is not running"
  info "Last exit reason:"
  docker inspect --format='{{.State.ExitCode}} — {{.State.Error}}' gula-backend 2>/dev/null || true
fi

# ─────────────────────────────────────────────────────────────────────────────
# 5. System Nginx (host)
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo "── 5. Host Nginx Configuration ──────────────────────────────────"

if command -v nginx >/dev/null 2>&1; then
  NGINX_STATUS=$(systemctl is-active nginx 2>/dev/null || echo "unknown")
  if [ "$NGINX_STATUS" = "active" ]; then
    pass "System nginx: active"
  else
    fail "System nginx: $NGINX_STATUS"
    info "Fix: sudo systemctl start nginx"
  fi

  if sudo nginx -t 2>/dev/null; then
    pass "nginx -t: config valid"
  else
    fail "nginx -t: config INVALID"
    sudo nginx -t 2>&1 | head -10
  fi

  if [ -L /etc/nginx/sites-enabled/gula-platform ]; then
    pass "gula-platform site: enabled"
  else
    fail "gula-platform site: NOT enabled"
    info "Fix: sudo ln -sf /etc/nginx/sites-available/gula-platform /etc/nginx/sites-enabled/gula-platform && sudo nginx -t && sudo systemctl reload nginx"
  fi

  if [ -f /etc/nginx/sites-enabled/default ]; then
    warn "Default nginx site is still enabled — it may intercept requests"
    info "Fix: sudo rm /etc/nginx/sites-enabled/default && sudo systemctl reload nginx"
  fi
else
  warn "nginx not installed on host — Docker api-gateway must be on port 80 directly"
fi

# ─────────────────────────────────────────────────────────────────────────────
# 6. Environment
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo "── 6. Environment (.env) ────────────────────────────────────────"

ENV_FILE="$(dirname "${BASH_SOURCE[0]}")/../.env"
if [ -f "$ENV_FILE" ]; then
  VARS=(SECRET_KEY ENCRYPTION_KEY NID_HMAC_KEY POSTGRES_PASSWORD REDIS_PASSWORD GULA_ADMIN_PASSWORD)
  for v in "${VARS[@]}"; do
    val=$(grep -oP "^${v}=\K.*" "$ENV_FILE" 2>/dev/null | head -1)
    if [ -z "$val" ]; then
      fail "$v: NOT SET"
    elif [ ${#val} -lt 16 ]; then
      warn "$v: SET but very short (${#val} chars) — may fail startup guard"
    else
      pass "$v: SET (${#val} chars)"
    fi
  done
else
  fail ".env file not found at $ENV_FILE"
  info "Run ./deploy.sh to generate it"
fi

# ─────────────────────────────────────────────────────────────────────────────
# 7. Disk Space
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo "── 7. Resources ─────────────────────────────────────────────────"
df -h / 2>/dev/null | tail -1 | awk '{printf "  Disk: %s used of %s (%s)\n", $3, $2, $5}'
free -h 2>/dev/null | awk '/^Mem:/{printf "  RAM:  %s used of %s (free: %s)\n", $3, $2, $4}'
docker system df 2>/dev/null | grep -v "^$" | sed 's/^/  /'

# ─────────────────────────────────────────────────────────────────────────────
# 8. Final Verdict
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo "══════════════════════════════════════════════════════════════════"

READY_STATUS=$(curl -s --max-time 5 http://127.0.0.1:8080/health/ready 2>/dev/null || echo "failed")
if echo "$READY_STATUS" | grep -q '"status":"ready"'; then
  echo -e "${GREEN}  ✅ SYSTEM IS READY — gula-platform.org should be working${NC}"
elif echo "$READY_STATUS" | grep -q '"status":"not_ready"'; then
  REASON=$(echo "$READY_STATUS" | grep -o '"reason":"[^"]*"' | cut -d'"' -f4)
  echo -e "${RED}  ❌ SYSTEM NOT READY — reason: $REASON${NC}"
  echo ""
  case "$REASON" in
    startup_in_progress) info "Fix: wait 30s and run again, or check: docker logs gula-backend --tail=50" ;;
    database_unavailable) info "Fix: docker compose restart postgres && docker compose restart gula-backend" ;;
    redis_unavailable) info "Fix: docker compose restart redis && docker compose restart gula-backend" ;;
    *) info "Fix: docker logs gula-backend --tail=100" ;;
  esac
else
  echo -e "${RED}  ❌ CANNOT REACH BACKEND — Docker stack may be down${NC}"
  info "Fix: cd ~/gula-platform && git pull && ./deploy.sh"
fi
echo "══════════════════════════════════════════════════════════════════"
echo ""
