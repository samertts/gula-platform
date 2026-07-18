#!/usr/bin/env bash
# =============================================================================
# GULA Foundation Health Check
# =============================================================================
# Runs all foundation tools and prints a compact status table.
# Exit code: 0 = all green, 1 = any warning, 2 = any fail
# =============================================================================

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

RED='\033[91m'
GREEN='\033[92m'
YELLOW='\033[93m'
CYAN='\033[96m'
BOLD='\033[1m'
RESET='\033[0m'

pass_count=0
warn_count=0
fail_count=0
results=()

run_check() {
    local name="$1"
    local cmd="$2"
    local exit_code=0
    local output

    output=$(eval "$cmd" 2>&1) || exit_code=$?

    if [ "$exit_code" -eq 0 ]; then
        echo -e "  ${GREEN}PASS${RESET}  $name"
        pass_count=$((pass_count + 1))
        results+=("PASS")
    elif [ "$exit_code" -eq 1 ]; then
        echo -e "  ${YELLOW}WARN${RESET}  $name"
        warn_count=$((warn_count + 1))
        results+=("WARN")
    else
        echo -e "  ${RED}FAIL${RESET}  $name"
        fail_count=$((fail_count + 1))
        results+=("FAIL")
    fi

    if [ -n "$output" ]; then
        while IFS= read -r line; do
            if [ -n "$line" ]; then
                echo "         $line"
            fi
        done <<< "$output"
    fi
}

echo ""
echo -e "  ${BOLD}GULA Foundation Health Check${RESET}"
echo -e "  ${BOLD}$(printf '═%.0s' {1..50})${RESET}"
echo ""

# Architecture compliance
run_check "Architecture Compliance" \
    "python3 scripts/architecture_compliance_engine.py --json 2>/dev/null | python3 -c \"import sys,json; d=json.load(sys.stdin); print(f'score: {d.get(\\\"score\\\",0)}/100'); exit(0 if d.get('\\''score'\\'',0) >= 60 else (1 if d.get('\\''score'\\'',0) >= 30 else 2))\" 2>/dev/null || true"

# Repository scorecard
run_check "Repository Scorecard" \
    "python3 scripts/repository_scorecard.py --json 2>/dev/null | python3 -c \"import sys,json; d=json.load(sys.stdin); s=d.get('overall_score',0); print(f'score: {s}/100 grade: {d.get(\\\"grade\\\",\\\"?\\\")}'); exit(2 if s < 65 else (1 if s < 75 else 0))\" 2>/dev/null || true"

# Technical debt registry
run_check "Technical Debt" \
    "python3 scripts/technical_debt_registry.py --json --refresh 2>/dev/null | python3 -c \"import sys,json; d=json.load(sys.stdin); m=d.get('meta',{}); bp=m.get('by_priority',{}); p0=bp.get('P0',0); p1=bp.get('P1',0); print(f'items: {m.get(\\\"total_items\\\",0)} P0={p0} P1={p1}'); exit(2 if p0 > 0 else (1 if p1 > 5 else 0))\" 2>/dev/null || true"

# Enterprise metrics
run_check "Enterprise Metrics" \
    "python3 scripts/enterprise_metrics.py --json 2>/dev/null | python3 -c \"import sys,json; d=json.load(sys.stdin); qi=d.get('quality_index',{}); t=qi.get('total',0); print(f'quality index: {t}/{qi.get(\\\"max\\\",1000)} grade: {qi.get(\\\"grade\\\",\\\"?\\\")}'); exit(2 if t < 500 else 0)\" 2>/dev/null || true"

# Quality gate (lightweight)
run_check "Quality Gate (quick)" \
    "python3 scripts/quality_gate.py --ci --bypass architecture,scorecard,debt,metrics 2>/dev/null | python3 -c \"import sys,json; d=json.load(sys.stdin); o=d.get('overall','FAIL'); print(f'overall: {o}'); exit(2 if o == 'FAIL' else (1 if o == 'WARNING' else 0))\" 2>/dev/null || true"

echo ""
echo -e "  ${BOLD}$(printf '═%.0s' {1..50})${RESET}"
total=$((pass_count + warn_count + fail_count))
echo -e "  Results:  ${GREEN}${pass_count} passed${RESET}  ${YELLOW}${warn_count} warning(s)${RESET}  ${RED}${fail_count} failed${RESET}  (${total} total)"
echo ""

if [ "$fail_count" -gt 0 ]; then
    exit 2
elif [ "$warn_count" -gt 0 ]; then
    exit 1
fi
exit 0
