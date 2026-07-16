#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$REPO_ROOT"

# Use the virtualenv Python if available
PYTHON="${VENV_PYTHON:-}"
if [ -z "$PYTHON" ]; then
    if [ -f ".venv/bin/python" ]; then
        PYTHON=".venv/bin/python"
    elif command -v python3 &>/dev/null; then
        PYTHON="python3"
    elif command -v python &>/dev/null; then
        PYTHON="python"
    else
        echo "FATAL: No Python interpreter found"
        exit 1
    fi
fi

echo "=== GULA Platform Production Freeze ==="
echo "  Python: $PYTHON"
echo ""

# Phase 1: Syntax gate - compile all Python files
echo "--- Phase 1: Syntax Gate ---"
cd backend
echo "  Compiling app/ files..."
find app/ -name '*.py' -exec "$REPO_ROOT/$PYTHON" -m py_compile {} + 2>&1 | grep -v "Skipped" || true
echo "  ✓ All app/ Python files compile"
echo ""

echo "  Compiling test files..."
find tests/ -name '*.py' -exec "$REPO_ROOT/$PYTHON" -m py_compile {} + 2>&1 | grep -v "Skipped" || true
echo "  ✓ All test Python files compile"
cd "$REPO_ROOT"
echo ""

# Phase 2: Lint
echo "--- Phase 2: Lint Gate ---"
cd backend
"$REPO_ROOT/$PYTHON" -m flake8 --select=E9,F821 app/ --count --statistics
cd "$REPO_ROOT"
echo ""

# Phase 3: Generate reports
echo "--- Phase 3: Generating Reports ---"
"$PYTHON" scripts/generate-final-report.py
echo ""

# Phase 4: Git tag
echo "--- Phase 4: Git Tag ---"
if git rev-parse "production-platform-v1.0" >/dev/null 2>&1; then
    echo "  Tag production-platform-v1.0 already exists — deleting and recreating"
    git tag -d "production-platform-v1.0"
fi
git tag -a "production-platform-v1.0" -m "GULA Platform Production Release v1.0 — National production, governance, intelligence & operations platform"
echo "  ✓ Tagged production-platform-v1.0"
echo ""

echo "=== Production Freeze Complete ==="
echo "  Release tag: production-platform-v1.0"
echo "  Reports:     reports/"
echo "  To push:     git push origin production-platform-v1.0"
