#!/usr/bin/env bash
# ===========================================================
# search_knowledge.sh — Search GAIOS Knowledge System
# Created: 2026-08-04
# Usage: bash .ai/core/automation/search_knowledge.sh <query>
# ===========================================================

set -euo pipefail

QUERY="${1:-}"
AI_DIR="$(dirname "$0")/../.."

if [ -z "$QUERY" ]; then
    echo "Usage: $0 <search-query>"
    echo "Example: $0 'path deduplication'"
    echo "Example: $0 'docker'"
    exit 1
fi

echo "=== Searching GAIOS Knowledge for: $QUERY ==="
echo ""

# Search skills
echo "--- Skills ---"
grep -rl "$QUERY" "$AI_DIR/core/skills/" 2>/dev/null | while read -r f; do
    title=$(grep "^title:" "$f" | head -1 | sed 's/title: *//; s/"//g')
    id=$(grep "^id:" "$f" | head -1 | sed 's/id: *//')
    echo "  $id — $title ($f)"
done || echo "  (none found)"

# Search playbooks
echo "--- Playbooks ---"
grep -rl "$QUERY" "$AI_DIR/core/playbooks/" 2>/dev/null | while read -r f; do
    title=$(grep "^title:" "$f" | head -1 | sed 's/title: *//; s/"//g')
    id=$(grep "^id:" "$f" | head -1 | sed 's/id: *//')
    echo "  $id — $title ($f)"
done || echo "  (none found)"

# Search runbooks
echo "--- Runbooks ---"
grep -rl "$QUERY" "$AI_DIR/core/runbooks/" 2>/dev/null | while read -r f; do
    title=$(grep "^title:" "$f" | head -1 | sed 's/title: *//; s/"//g')
    id=$(grep "^id:" "$f" | head -1 | sed 's/id: *//')
    echo "  $id — $title ($f)"
done || echo "  (none found)"

# Search memory
echo "--- Memory ---"
grep -rl "$QUERY" "$AI_DIR/core/memory/" 2>/dev/null | while read -r f; do
    title=$(grep "^title:" "$f" 2>/dev/null | head -1 | sed 's/title: *//; s/"//g')
    id=$(grep "^id:" "$f" 2>/dev/null | head -1 | sed 's/id: *//')
    echo "  $id — $title ($f)"
done || echo "  (none found)"

# Search lessons
echo "--- Lessons ---"
grep -rl "$QUERY" "$AI_DIR/core/lessons/" 2>/dev/null | while read -r f; do
    title=$(grep "^title:" "$f" | head -1 | sed 's/title: *//; s/"//g')
    id=$(grep "^id:" "$f" | head -1 | sed 's/id: *//')
    echo "  $id — $title ($f)"
done || echo "  (none found)"

# Search bridge files
echo "--- Bridge Files ---"
grep -rl "$QUERY" "$AI_DIR/core/"*/README.md 2>/dev/null | while read -r f; do
    dir=$(dirname "$f" | xargs basename)
    echo "  $dir/README.md"
done || echo "  (none found)"

echo ""
echo "=== Search Complete ==="
