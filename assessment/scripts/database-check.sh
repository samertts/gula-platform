#!/bin/bash
# GULA Platform — Database Health Checker
# Usage: ./assessment/scripts/database-check.sh
# Requires: PostgreSQL access (DB_URL env var)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "=== GULA Platform — Database Health Check ==="
echo ""

# Check migration files
echo "--- Migration Files ---"
if [ -d "$PROJECT_ROOT/backend/migrations/versions" ]; then
    echo "Total migrations: $(find "$PROJECT_ROOT/backend/migrations/versions" -name '*.py' | wc -l)"
    echo "Latest migration: $(ls -t "$PROJECT_ROOT/backend/migrations/versions/"*.py 2>/dev/null | head -1)"
    echo ""
    echo "Migration guard check:"
    for f in "$PROJECT_ROOT/backend/migrations/versions/"*.py; do
        has_guard=$(grep -l '_has_column\|_table_exists\|_index_exists' "$f" 2>/dev/null || true)
        if [ -z "$has_guard" ]; then
            echo "  ⚠️  $(basename "$f") — no idempotency guards"
        fi
    done
else
    echo "No migration files found"
fi

# Check models against config
echo ""
echo "--- Model Config Check ---"
grep -n "class.*Model\|class.*Base" "$PROJECT_ROOT/backend/app/models/"*.py 2>/dev/null | head -20 || echo "No models found"

# Check connection pool config
echo ""
echo "--- Connection Pool Configuration ---"
grep -n "POOL_SIZE\|MAX_OVERFLOW\|pool_size\|max_overflow" "$PROJECT_ROOT/backend/app/database.py" 2>/dev/null \
    || echo "Not found in database.py"
grep -n "WEB_CONCURRENCY\|DB_POOL_SIZE\|DB_MAX_OVERFLOW\|max_connections" "$PROJECT_ROOT/backend/app/config.py" 2>/dev/null \
    || echo "Not found in config.py"

echo ""
echo "=== Database Health Check Complete ==="
