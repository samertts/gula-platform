#!/bin/bash
# GULA Platform — Architecture Boundary Validator
# Usage: ./assessment/scripts/architecture-validate.sh
# Checks: No lower layers import upper layers, no circular imports

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "=== GULA Platform — Architecture Boundary Validation ==="
echo ""

# Check: routes should not import from other routes
echo "--- Routes importing other routes (should be 0) ---"
grep -rn "from app\.routes\|import app\.routes" "$PROJECT_ROOT/backend/app/routes/" --include='*.py' \
    | grep -v "__init__\|__pycache__" || echo "None found (clean)"

# Check: models should not import from routes or services
echo ""
echo "--- Models importing routes/services (should be 0) ---"
grep -rn "from app\.routes\|import app\.routes\|from app\.services\|import app\.services" \
    "$PROJECT_ROOT/backend/app/models/" --include='*.py' \
    | grep -v "__init__\|__pycache__" || echo "None found (clean)"

# Check: services should not import from routes
echo ""
echo "--- Services importing routes (should be 0) ---"
grep -rn "from app\.routes\|import app\.routes" "$PROJECT_ROOT/backend/app/services/" --include='*.py' \
    | grep -v "__init__\|__pycache__" || echo "None found (clean)"

# Check: circular imports (tripleslash scan)
echo ""
echo "--- Potential circular import chains ---"
cd "$PROJECT_ROOT/backend/app"
# Check common antipatterns
for dir in routes services models; do
    for f in $(find "$dir" -name '*.py' ! -name '__init__.py' 2>/dev/null); do
        imports=$(grep "^from app\." "$f" | grep -v "^from app\.$dir" | head -5 || true)
        if [ -n "$imports" ]; then
            echo "$f imports:"
            echo "$imports"
        fi
    done
done

echo ""
echo "=== Validation Complete ==="
