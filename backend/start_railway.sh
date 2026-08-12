#!/bin/sh
set -eu

PORT_VALUE="${PORT:-10000}"
echo "GULA backend starting on 0.0.0.0:${PORT_VALUE}" >&2

exec gunicorn \
  -k uvicorn.workers.UvicornWorker \
  app.main:app \
  --workers 1 \
  --timeout 60 \
  --bind "0.0.0.0:${PORT_VALUE}" \
  --access-logfile - \
  --error-logfile -

