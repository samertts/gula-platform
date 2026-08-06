---
id: TESTING-000001
type: testing
title: "Testing Knowledge Bridge"
version: "1.0"
created: "2026-08-04"
status: verified
confidence: 100%
tags: [testing, bridge, index]
---

# Testing Knowledge — Bridge Reference

## Testing Policy
- `docs/constitution/20_TESTING_POLICY.md` — Mandatory testing rules

## Test Frameworks
| Layer | Framework | Command |
|---|---|---|
| Backend unit | pytest | `cd backend && .venv/bin/python -m pytest tests/unit/ -v` |
| Backend integration | pytest + PostgreSQL | `cd backend && .venv/bin/python -m pytest tests/ -v` |
| Frontend unit | Vitest | `cd frontend-v3 && npx vitest run` |
| Python lint | ruff | `cd backend && ruff check .` |
| Python type | mypy | `cd backend && mypy app/` |
| JS lint | ESLint | `cd frontend-v3 && npx eslint src/` |
| JS type | TypeScript | `cd frontend-v3 && npx tsc --noEmit` |

## Test Counts (2026-08-04)
- Backend: 399 tests, 0 failures
- Frontend: 54 tests, 0 failures
- Total: 453 tests passing

## Quality Gates
- No failing tests in CI
- No ruff violations (E9, F, UP: zero)
- No TypeScript errors
- No ESLint errors
- Brain freshness check

## Test Patterns
- Unit tests mock DB with SQLite in-memory
- Integration tests require PostgreSQL
- conftest.py provides fixtures: db_session, client, auth_headers
- Test DDL optimized: 16→4 base creation

## Related
- `docs/quality/quality_gates.md` — Quality gate details
- `docs/standards/engineering_standards.md` — Standards
- `.ai/core/memory/PROJECT_MEMORY.md` — Testing strategy
