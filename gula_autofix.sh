#!/usr/bin/env bash
set -euo pipefail

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$BASE_DIR"

log() { printf '[gula_autofix] %s\n' "$*"; }

if ! command -v docker >/dev/null 2>&1; then
  log "docker is not installed or not in PATH"
  exit 2
fi

COMPOSE="docker compose"
if ! $COMPOSE version >/dev/null 2>&1; then
  COMPOSE="docker-compose"
fi

log "Checking unhealthy/exited containers"
mapfile -t broken < <(docker ps -a --format '{{.Names}} {{.Status}}' | awk '/(Exited|unhealthy)/ {print $1}')

if [ "${#broken[@]}" -gt 0 ]; then
  log "Restarting broken containers: ${broken[*]}"
  docker restart "${broken[@]}" || true
fi

log "Ensuring compose services are running"
$COMPOSE up -d --remove-orphans

log "Pruning dangling images"
docker image prune -f >/dev/null || true

if ./gula_health.sh; then
  log "Autofix completed successfully"
else
  log "Autofix could not recover all services"
  exit 1
fi
