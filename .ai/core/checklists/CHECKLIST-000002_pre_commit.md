---
id: CHECKLIST-000002
type: checklist
title: "Pre-Commit Checklist"
version: "1.0"
created: "2026-08-04"
status: verified
confidence: 100%
tags: [pre-commit, checklist, quality, gate]
---

# Pre-Commit Checklist

Run before every commit. All items must pass.

## Python Backend
```bash
cd backend
# Lint
.venv/bin/ruff check . --select E9,F,UP
# Type check (specific files)
.venv/bin/mypy app/services/ --ignore-missing-imports
# Tests
.venv/bin/python -m pytest tests/unit/ -v --tb=short
```

- [ ] `ruff check .` passes (E9, F, UP: zero violations)
- [ ] No new N806/N815/N817 violations
- [ ] Unit tests pass
- [ ] No print statements left in code
- [ ] No TODO without issue reference

## Frontend
```bash
cd frontend-v3
# Type check
npx tsc --noEmit
# Lint
npx eslint src/
# Tests
npx vitest run
```

- [ ] TypeScript compiles with 0 errors
- [ ] ESLint passes with 0 errors
- [ ] Vitest tests pass
- [ ] No `console.log` in production code
- [ ] No `(data as any)` casts

## General
- [ ] No secrets committed
- [ ] No large files (>1MB) committed
- [ ] `.gitignore` updated for new patterns
- [ ] Commit message follows Conventional Commits
- [ ] Related tests included
- [ ] Documentation updated if needed

## Git
```bash
# Check what's being committed
git status
git diff --stat

# Never commit:
# - .env files
# - node_modules/
# - .venv/
# - __pycache__/
# - *.pyc
# - Docker volumes
```

## Anti-Patterns to Check
- [ ] No `# type: ignore` without justification
- [ ] No `# noqa` without justification
- [ ] No bare `except:` clauses
- [ ] No mutable default arguments
- [ ] No global state mutation
- [ ] No blocking I/O in async functions
