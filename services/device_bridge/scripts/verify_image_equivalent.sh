#!/usr/bin/env bash
# IA-044 / IA-051 — run the device bridge the way its image runs it, with no
# Docker daemon.
#
# The image is `FROM python:3.14-slim`, `COPY app/ ./app/`, and a pip install of
# four packages. Every local test run instead has the repository root on
# PYTHONPATH and every package the host happens to have, which is how a crash
# that only the image hits (IA-044: `ModuleNotFoundError: No module named
# 'backend'`) stayed invisible behind a green suite.
#
# This reproduces the image's two constraints — only `app/` importable, only the
# Dockerfile's declared packages installed — and exercises the service through
# the same CMD and the same healthcheck the compose file uses.
#
# Usage:  bash scripts/verify_image_equivalent.sh [port]
# Exit:   0 if every step passed; non-zero on the first failure.
set -u

PORT="${1:-8311}"
SERVICE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
WORK="$(mktemp -d)"
API_KEY="image-equivalent-probe"
trap 'kill "${SERVER_PID:-}" 2>/dev/null; rm -rf "$WORK"' EXIT

fail() { echo "FAIL: $*" >&2; exit 1; }

# ── mirror `COPY app/ ./app/` — and nothing else ────────────────────────────
mkdir -p "$WORK/app"
cp -r "$SERVICE_DIR/app/." "$WORK/app/"
cp "$SERVICE_DIR/pyproject.toml" "$WORK/"
find "$WORK" -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null
[ -e "$WORK/backend" ] && fail "the image tree must not contain backend/"
[ -e "$WORK/shared" ] && fail "the image tree must not contain shared/"

# ── mirror the Dockerfile's pip install, read FROM the Dockerfile ───────────
# Derived rather than transcribed: a list copied beside the Dockerfile would
# drift from it, and then this script would prove something about the copy.
PACKAGES="$(python3 "$SERVICE_DIR/scripts/_dockerfile_packages.py" "$SERVICE_DIR/Dockerfile")"
[ -n "$PACKAGES" ] || fail "could not read the package set from the Dockerfile"
echo "0/6 packages declared by the Dockerfile: $PACKAGES"

cd "$WORK"
python3 -m venv --clear .venv >/dev/null 2>&1 || fail "could not create a venv"
eval "./.venv/bin/pip install -q --no-cache-dir $PACKAGES" >/dev/null 2>&1 \
  || fail "the Dockerfile's package set did not install"

unset PYTHONPATH
export LABLINK_API_KEY="$API_KEY"
export GULA_BACKEND_URL="http://gula-backend:8000"

echo "1/6 import app.main with only the image's module path"
./.venv/bin/python -c "import sys; sys.path.insert(0,'.'); import app.main" \
  || fail "the application cannot be imported inside the image (IA-044)"

echo "2/6 start the Dockerfile CMD"
./.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port "$PORT" \
  --log-level error > "$WORK/server.log" 2>&1 &
SERVER_PID=$!
for _ in $(seq 1 40); do
  curl -sf -o /dev/null "http://127.0.0.1:$PORT/health" && break
  sleep 0.5
done

echo "3/6 the compose healthcheck command, verbatim"
./.venv/bin/python -c "
import urllib.request
urllib.request.urlopen('http://localhost:$PORT/health')
" || fail "the compose healthcheck would never pass"

echo "4/6 ingest a real ASTM frame and read the result back"
PAYLOAD="$(./.venv/bin/python - <<'PY'
import json, sys
sys.path.insert(0, ".")
from app.pipeline.parser_engine import calculate_checksum
msg = ("1H|\\^&|||Dev|||||P|1\r2P|1||PATIENT-A||Alpha^A\r"
       "3R|1|^^^Hb|13.5|g/dL|12.0-16.0|L|N|F|||20260101120000|20260101120500\r9L|1|N\r")
p = msg.encode("ascii")
frame = b"\x02" + p + b"\x03" + calculate_checksum(p).encode("ascii") + b"\r\n"
print(json.dumps({"patient_id": "FB", "device_id": "CBC-01", "chunk": frame.decode("latin-1")}))
PY
)"
curl -s -H "x-api-key: $API_KEY" -H 'content-type: application/json' \
  -d "$PAYLOAD" "http://127.0.0.1:$PORT/ingest" \
  | ./.venv/bin/python -c "
import json, sys
body = json.load(sys.stdin)
row = body['results'][0]
assert body['processed'] == 1, body
# IA-050: the instrument's own flag and range must survive into the record.
assert row['device_abnormal_flags'] == 'L', row
assert row['reference_range'] == '12.0-16.0', row
assert row['status'] == 'preliminary', row
print('    processed=1 flag=L range=12.0-16.0 status=preliminary')
" || fail "the ingestion path does not behave correctly inside the image"

echo "5/6 an unauthenticated read must be refused"
code="$(curl -s -o /dev/null -w '%{http_code}' "http://127.0.0.1:$PORT/results")"
[ "$code" = "401" ] || fail "an unauthenticated read returned $code, not 401"

echo "6/6 pyserial, which app/connectors/base.py needs to open a serial analyzer"
if ./.venv/bin/python -c "import serial" 2>/dev/null; then
  echo "    pyserial present"
else
  echo "    pyserial MISSING — a serial analyzer cannot be opened in this image."
  echo "    IA-044: declared in pyproject, absent from the Dockerfile's pip install."
fi

echo "OK: the service runs under the image's constraints."
