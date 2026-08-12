#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-.}"
cd "$ROOT"

echo "== GULA repository security inventory =="
printf 'root=%s\n' "$PWD"

echo "-- manifests --"
find . -path './.git' -prune -o -path '*/node_modules' -prune -o -path '*/venv' -prune -o -type f \( \
  -name 'package.json' -o -name 'package-lock.json' -o -name 'pnpm-lock.yaml' -o -name 'yarn.lock' \
  -o -name 'requirements*.txt' -o -name 'pyproject.toml' -o -name 'build.gradle' -o -name 'build.gradle.kts' \
\) -print | sort

echo "-- high-risk source markers (review, do not auto-classify) --"
grep -RIn --exclude-dir=.git --exclude-dir=node_modules --exclude-dir=venv \
  -E 'verify[[:space:]]*=[[:space:]]*False|localStorage\.(setItem|getItem).*token|eval\(|exec\(|shell=True|text\([[:space:]]*\)|f"[^"$]*\{[^}]+\}[^" ]*SELECT|BEGIN (RSA|OPENSSH|EC) PRIVATE KEY|AKIA[0-9A-Z]{16}' \
  . || true

echo "-- tracked generated/secrets candidates --"
git ls-files | grep -E '(^|/)(\.env|.*\.db$|.*\.sqlite$|.*\.pem$|.*\.key$|.*\.p12$|.*\.jks$|node_modules/|venv/)' || true

echo "-- git hygiene --"
git status --short
git diff --check

echo "Inventory complete; triage each result against source, reachability, and tests."
