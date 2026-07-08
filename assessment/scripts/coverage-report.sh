#!/bin/bash
# GULA Platform — Coverage Report Generator
# Usage: ./assessment/scripts/coverage-report.sh
# Output: assessment/reports/coverage-<date>.md

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
REPORT_DIR="$PROJECT_ROOT/assessment/reports"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
REPORT_FILE="$REPORT_DIR/coverage-$TIMESTAMP.md"

PYTHON=""
if [ -f "$PROJECT_ROOT/.venv/bin/python" ]; then
    PYTHON="$PROJECT_ROOT/.venv/bin/python"
elif command -v python3 &>/dev/null; then
    PYTHON="python3"
else
    PYTHON="python"
fi

mkdir -p "$REPORT_DIR"

# Run coverage
cd "$PROJECT_ROOT/backend"
$PYTHON -m pytest tests/ \
    --cov=app \
    --cov-report=term-missing \
    --cov-report=html:"$REPORT_DIR/coverage-html-$TIMESTAMP" \
    -q --tb=no 2>&1 | tee "$REPORT_FILE"

echo "" >> "$REPORT_FILE"
echo "## Per-Module Breakdown" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"
echo "Generated from: backend/tests/" >> "$REPORT_FILE"
echo "HTML report: assessment/reports/coverage-html-$TIMESTAMP/index.html" >> "$REPORT_FILE"

echo "Coverage report generated: $REPORT_FILE"
