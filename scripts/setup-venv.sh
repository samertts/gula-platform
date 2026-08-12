#!/usr/bin/env bash
# =============================================================================
# GULA Platform — Script Dependencies Setup
# Creates a venv with requests, psycopg2-binary, colorama for chaos_test + dive
#
# Usage: bash scripts/setup-venv.sh
#        source .venv/bin/activate
#        python3 scripts/chaos_test.py ...
# =============================================================================
set -euo pipefail

VENV=".venv"
cd "$(git rev-parse --show-toplevel)"

echo "Creating virtual environment at $VENV ..."
python3 -m venv "$VENV"

echo "Installing script dependencies ..."
"$VENV/bin/pip" install --quiet --upgrade pip
"$VENV/bin/pip" install --quiet requests psycopg2-binary colorama

echo ""
echo "Done. Activate with:"
echo "  source $VENV/bin/activate"
echo ""
echo "Then run:"
echo "  python3 scripts/chaos_test.py --base https://gula-platform.org --no-docker"
echo "  python3 scripts/dive.py --strict"
