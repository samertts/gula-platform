#!/bin/sh
set -eu

PORT_VALUE="${PORT:-10000}"
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
SCRIPT_PARENT=$(CDPATH= cd -- "${SCRIPT_DIR}/.." && pwd)
# The image contains /app/{app,shared}; local execution uses repo/{backend,shared}.
# Include both locations so imports work consistently in both environments.
export PYTHONPATH="${SCRIPT_DIR}:${SCRIPT_PARENT}${PYTHONPATH:+:${PYTHONPATH}}"
echo "GULA backend starting on 0.0.0.0:${PORT_VALUE}" >&2

# Opt-in only: prints an import traceback without exposing environment values.
if [ "${GULA_STARTUP_DIAGNOSTICS:-false}" = "true" ]; then
  python3 "${SCRIPT_DIR}/railway_startup_probe.py"
fi

WEB_CONCURRENCY_VALUE="${WEB_CONCURRENCY:-2}"
GUNICORN_TIMEOUT_VALUE="${GUNICORN_TIMEOUT:-60}"
GUNICORN_GRACEFUL_TIMEOUT_VALUE="${GUNICORN_GRACEFUL_TIMEOUT:-30}"
GUNICORN_KEEPALIVE_VALUE="${GUNICORN_KEEPALIVE:-5}"
GUNICORN_MAX_REQUESTS_VALUE="${GUNICORN_MAX_REQUESTS:-10000}"
GUNICORN_MAX_REQUESTS_JITTER_VALUE="${GUNICORN_MAX_REQUESTS_JITTER:-1000}"
GUNICORN_BACKLOG_VALUE="${GUNICORN_BACKLOG:-2048}"

case "${WEB_CONCURRENCY_VALUE}" in
  *[!0-9]*|0) echo "WEB_CONCURRENCY must be a positive integer" >&2; exit 1 ;;
esac

exec gunicorn \
  -k gula_uvicorn_worker.GulaUvicornWorker \
  app.main:app \
  --workers "${WEB_CONCURRENCY_VALUE}" \
  --backlog "${GUNICORN_BACKLOG_VALUE}" \
  --keep-alive "${GUNICORN_KEEPALIVE_VALUE}" \
  --log-level info \
  --capture-output \
  --timeout "${GUNICORN_TIMEOUT_VALUE}" \
  --graceful-timeout "${GUNICORN_GRACEFUL_TIMEOUT_VALUE}" \
  --max-requests "${GUNICORN_MAX_REQUESTS_VALUE}" \
  --max-requests-jitter "${GUNICORN_MAX_REQUESTS_JITTER_VALUE}" \
  --bind "0.0.0.0:${PORT_VALUE}" \
  --access-logfile - \
  --error-logfile - \
  --preload

