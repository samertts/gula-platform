#!/usr/bin/env bash
set -e

PROJECT_DIR="/home/samertts/gula-platform"
COMPOSE="docker-compose"

cd "$PROJECT_DIR"

# أسماء الخدمات المتوقعة
services=("backend" "api" "frontend" "postgres" "redis")

# دالة: هل الحاوية تعمل؟
is_running () {
  local name=$1
  docker ps --format '{{.Names}}' | grep -q "$name"
}

# فحص الخدمات
for s in "${services[@]}"; do
  if ! is_running "$s"; then
    echo "$(date) - Service $s is down. Restarting..."
    $COMPOSE up -d "$s" || $COMPOSE up -d
  fi
done

# تنظيف الصور غير المستخدمة
docker image prune -f
