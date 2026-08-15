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

