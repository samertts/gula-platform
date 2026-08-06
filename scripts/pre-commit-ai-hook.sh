#!/bin/bash
# PROGRAM-AUTOMATION-001: Pre-commit AI Enforcement Hook
# Installed by: scripts/install_ai_hooks.sh
# Runs AI validation before every commit

set -e

REPO_ROOT="$(git rev-parse --show-toplevel)"
SCRIPTS_DIR="$REPO_ROOT/scripts"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

FAILED=0

echo "GULA AI Pre-commit Validation..."
echo "================================="

# 1. Constitution Validator
echo ""
echo "[1/5] Constitution Validator..."
if python3 "$SCRIPTS_DIR/validate_constitution.py" > /dev/null 2>&1; then
    echo -e "  ${GREEN}[PASS]${NC} Constitution validation passed"
else
    echo -e "  ${RED}[FAIL]${NC} Constitution validation failed"
    python3 "$SCRIPTS_DIR/validate_constitution.py" 2>&1 | tail -5
    FAILED=1
fi

# 2. Knowledge Validator (fast)
echo ""
echo "[2/5] Knowledge Validator..."
if python3 "$SCRIPTS_DIR/validate_knowledge.py" > /dev/null 2>&1; then
    echo -e "  ${GREEN}[PASS]${NC} Knowledge validation passed"
else
    echo -e "  ${YELLOW}[WARN]${NC} Knowledge validation has warnings (non-blocking)"
    python3 "$SCRIPTS_DIR/validate_knowledge.py" 2>&1 | tail -3
fi

# 3. AI System Validator (fast)
echo ""
echo "[3/5] AI System Validator..."
if python3 "$SCRIPTS_DIR/validate_ai_system.py" --fast > /dev/null 2>&1; then
    echo -e "  ${GREEN}[PASS]${NC} AI system validation passed"
else
    echo -e "  ${YELLOW}[WARN]${NC} AI system validation has warnings (non-blocking)"
    python3 "$SCRIPTS_DIR/validate_ai_system.py" --fast 2>&1 | tail -3
fi

# 4. Check for secret exposure
echo ""
echo "[4/5] Secret scan..."
STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACM 2>/dev/null || true)
SECRET_PATTERNS='(password|secret|token|api_key|private_key)\s*[:=]\s*["\x27][^"\x27]{8,}'
SECRET_FOUND=0
for FILE in $STAGED_FILES; do
    if [[ "$FILE" == *.py ]] || [[ "$FILE" == *.js ]] || [[ "$FILE" == *.ts ]] || [[ "$FILE" == *.env* ]]; then
        if grep -qEi "$SECRET_PATTERNS" "$REPO_ROOT/$FILE" 2>/dev/null; then
            echo -e "  ${RED}[FAIL]${NC} Potential secret in $FILE"
            SECRET_FOUND=1
        fi
    fi
done
if [ $SECRET_FOUND -eq 0 ]; then
    echo -e "  ${GREEN}[PASS]${NC} No secrets detected in staged files"
fi

# 5. Check AI config files not modified without approval
echo ""
echo "[5/5] Protected file check..."
PROTECTED_FILES="AI_OPERATING_CONSTITUTION.md AI_BOOTSTRAP.md"
PROTECTED_MODIFIED=0
for PF in $PROTECTED_FILES; do
    if echo "$STAGED_FILES" | grep -q "^${PF}$"; then
        echo -e "  ${YELLOW}[WARN]${NC} Protected file $PF is staged for commit"
        PROTECTED_MODIFIED=1
    fi
done
if [ $PROTECTED_MODIFIED -eq 0 ]; then
    echo -e "  ${GREEN}[PASS]${NC} No protected files modified"
fi

echo ""
echo "================================="
if [ $FAILED -eq 1 ]; then
    echo -e "${RED}PRE-COMMIT FAILED: Fix errors before committing${NC}"
    echo "To bypass (NOT recommended): git commit --no-verify"
    exit 1
else
    echo -e "${GREEN}PRE-COMMIT PASSED${NC}"
    exit 0
fi
