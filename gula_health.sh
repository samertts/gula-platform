#!/usr/bin/env bash
set -euo pipefail

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$BASE_DIR"

log() { printf '[gula_health] %s\n' "$*"; }

if ! command -v docker >/dev/null 2>&1; then
  log "docker is not installed or not in PATH"
  exit 2
fi

COMPOSE_CMD=(docker compose)
if ! "${COMPOSE_CMD[@]}" version >/dev/null 2>&1; then
  COMPOSE_CMD=(docker-compose)
fi

COMPOSE_FILE="${GULA_COMPOSE_FILE:-}"
if [ -z "$COMPOSE_FILE" ]; then
  if [ -f "$BASE_DIR/docker-compose.full.yml" ]; then
    COMPOSE_FILE="$BASE_DIR/docker-compose.full.yml"
  elif [ -f "$BASE_DIR/docker-compose.yml" ]; then
    COMPOSE_FILE="$BASE_DIR/docker-compose.yml"
  else
    log "No compose file found (expected docker-compose.full.yml or docker-compose.yml)"
    exit 2
  fi
fi

failed=0

log "Using compose file: $COMPOSE_FILE"
log "Checking compose service state"
if ! "${COMPOSE_CMD[@]}" -f "$COMPOSE_FILE" ps; then
  failed=1
fi

# Service names match docker-compose.yml (MVP) or docker-compose.full.yml (enterprise)
# MVP uses 'postgres'; full uses 'postgres-primary'
SERVICES="redis gula-backend frontend api-gateway"
if grep -q 'postgres-primary:' "$COMPOSE_FILE" 2>/dev/null; then
  SERVICES="postgres-primary $SERVICES"
else
  SERVICES="postgres $SERVICES"
fi
for svc in $SERVICES; do
  status=$("${COMPOSE_CMD[@]}" -f "$COMPOSE_FILE" ps --status running --services 2>/dev/null | grep -x "$svc" || true)
  if [ "$status" = "$svc" ]; then
    log "OK: $svc (running)"
  else
    log "FAIL: $svc (not running)"
    failed=1
  fi
done

# Check health endpoints (Docker api-gateway listens on 8080)
for endpoint in \
  "http://127.0.0.1:8080/health" \
  "http://127.0.0.1:8080/health/backend" \
  "http://127.0.0.1:8080/health/frontend"; do
  if curl -fsS --max-time 10 "$endpoint" >/dev/null 2>&1; then
    log "OK: $endpoint"
  else
    log "FAIL: $endpoint"
    failed=1
  fi
done

if [ "$failed" -eq 0 ]; then
  log "Platform health checks passed"
else
  log "Platform health checks failed"
  "${COMPOSE_CMD[@]}" -f "$COMPOSE_FILE" ps
  for svc in gula-backend api-gateway frontend; do
    log "--- Last 20 lines of $svc ---"
    "${COMPOSE_CMD[@]}" -f "$COMPOSE_FILE" logs --tail=20 "$svc" 2>/dev/null || true
  done
fi

exit "$failed"
