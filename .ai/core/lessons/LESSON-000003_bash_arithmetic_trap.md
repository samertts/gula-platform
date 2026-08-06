---
id: LESSON-000003
type: lesson
title: "Bash Arithmetic Expansion Exit Code Trap"
version: "1.0"
created: "2026-08-04"
status: verified
confidence: 100%
tags: [bash, scripting, set-e, arithmetic, gotcha]
related_skills: []
---

# LESSON-000003: Bash Arithmetic Expansion Exit Code Trap

## Problem
With `set -e`, `(( VAR++ ))` returns exit code 1 when VAR is 0, because
`(( 0 ))` is falsy in bash. This silently kills the script.

```bash
set -e
PASS=0
(( PASS++ ))  # Exit code 1! Script dies here.
echo "This never runs"
```

## Lesson
**Use `VAR=$((VAR + 1))` instead of `(( VAR++ ))` with `set -e`.**

```bash
# Safe
PASS=$((PASS + 1))

# Unsafe with set -e
(( PASS++ ))
(( ++PASS ))
```

## Root Cause
Bash arithmetic `(( ))` returns 0 (success) if result is non-zero,
1 (failure) if result is zero. When PASS=0, `((PASS++))` evaluates
to 0 (the pre-increment value), which is falsy → exit code 1.

## Prevention
- Never use `(( ))` for incrementing in `set -e` scripts
- Use `$(( ))` assignment form instead
- Test scripts with `set -e` from the start

## Changelog
| Version | Date | Author | Change |
|---|---|---|---|
| 1.0 | 2026-08-04 | GAIOS | Initial lesson |
