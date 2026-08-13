#!/bin/sh
set -eu

PORT_VALUE="${PORT:-10000}"
# The image contains both /app/backend and /app/shared. Gunicorn starts the
# application package from the backend workdir, so retain that path and add
# the image root for imports from the shared package.
export PYTHONPATH="/app${PYTHONPATH:+:${PYTHONPATH}}"
echo "GULA backend starting on 0.0.0.0:${PORT_VALUE}" >&2

# Opt-in only: prints an import traceback without exposing environment values.
if [ "${GULA_STARTUP_DIAGNOSTICS:-false}" = "true" ]; then
  python3 /app/backend/railway_startup_probe.py
fi

exec gunicorn \
  -k uvicorn.workers.UvicornWorker \
  app.main:app \
  --workers 1 \
  --log-level info \
  --capture-output \
  --timeout 60 \
  --bind "0.0.0.0:${PORT_VALUE}" \
  --access-logfile - \
  --error-logfile -

