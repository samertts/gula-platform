#!/bin/bash
# Pre-commit hook: forbid editing existing alembic migrations
set -euo pipefail

if git diff --cached --name-only | grep -q "^backend/migrations/versions/.*\.py$"; then
    echo "ERROR: editing existing migrations is forbidden"
    exit 1
fi
exit 0
