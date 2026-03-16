#!/usr/bin/env bash
set -euo pipefail

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$BASE_DIR"

log() { printf '[gula_health] %s\n' "$*"; }

if ! command -v docker >/dev/null 2>&1; then
  log "docker is not installed or not in PATH"
  exit 2
fi

COMPOSE="docker compose"
if ! $COMPOSE version >/dev/null 2>&1; then
  COMPOSE="docker-compose"
fi

failed=0

log "Checking compose service state"
if ! $COMPOSE ps; then
  failed=1
fi

for endpoint in \
  "http://localhost/health" \
  "http://localhost/health/backend" \
  "http://localhost/health/frontend"; do
  if curl -fsS --max-time 10 "$endpoint" >/dev/null; then
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
fi

exit "$failed"
