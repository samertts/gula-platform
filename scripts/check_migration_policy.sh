#!/usr/bin/env bash
# =============================================================================
# Migration policy gate (called by .pre-commit-config.yaml)
# =============================================================================
# CLAUDE.md states: "Never modify an existing migration — all schema changes =
# new revision only". This hook enforces it locally before the CI gate does.
#
# Behavior:
#   - For each staged migration file, check whether it's a NEW file or an
#     EDIT to a tracked file. Edits to tracked files fail with a clear error.
#   - The bootstrap revision (20250322_0000) is treated as immutable, period.
# =============================================================================

set -euo pipefail

RED='\033[0;31m'; YEL='\033[1;33m'; NC='\033[0m'

fail=0
for f in "$@"; do
    # Skip non-migration paths (defensive — the hook filter should have done this)
    case "$f" in
        backend/migrations/versions/*.py) ;;
        *) continue ;;
    esac

    # If the file existed in HEAD already, this is an edit → block.
    if git ls-files --error-unmatch "$f" >/dev/null 2>&1; then
        # Allow new-file marker (path exists in working tree but not in HEAD)
        if git cat-file -e "HEAD:$f" 2>/dev/null; then
            echo -e "${RED}[migration-policy]${NC} '$f' is an existing migration."
            echo -e "${YEL}  Existing migrations are immutable. Generate a NEW revision instead:${NC}"
            echo "    cd backend && alembic revision --autogenerate -m 'describe_change'"
            fail=1
        fi
    fi
done

exit "$fail"
