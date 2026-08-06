# 33_STRUCTURAL_MIGRATION_CONSTITUTION

**AUTHORITY:** AI_OPERATING_CONSTITUTION.md (supreme), PROGRAM-CONSTITUTION-001,
ADR-028 Structural Migration Rules. This document operationalizes ADR-028 into
checkable rules for every structural migration commit.

## Scope

Applies to every commit that moves, removes, replaces, rewrites, or archives
production code, including the migration of acknowledged Shared Core
reimplementation findings (`.ai/core/architecture/constitution_baseline.json`)
to their canonical providers.

## The Seven Rules

### R1. Behavior preservation is mandatory

Preserve: runtime behavior, API behavior, business rules, security behavior,
authorization, audit behavior, database behavior.

**Gate:** before/after behavior equivalence evidence in the verification report.

### R2. Every deletion must be evidence-based

Deletions/archives require objective evidence the code is: unused, superseded,
duplicated, or intentionally deprecated. Evidence is gathered repo-wide
(importers, tests, frontend consumers, docs) and recorded in the report.

### R3. Backend remains the authoritative source of truth

Frontend adapts to backend, never the reverse. Verify after every migration:
OpenAPI compatibility, frontend consumers, generated client types, permissions,
request/response models, route compatibility.

**Gate:** OpenAPI schema byte-compatible before/after; zero frontend file
changes unless the backend contract requires them.

### R4. Migration Impact Report is mandatory

Every migration commit produces `docs/baselines/COMMIT_X_Y_VERIFICATION_REPORT.md`
including: files removed, files moved, files replaced, duplicate code
eliminated, LOC reduction, dependency changes, API impact, frontend impact,
rollback procedure.

### R5. Prefer moving before deleting

Archive first (repo `archive/` convention), delete only after verification.

### R6. Every migration is independently reversible

A single `git revert` of the migration commit restores the previous state.
No migration may depend on another unreverted migration.

### R7. One commit at a time

After each commit: run the complete verification cycle, produce the Migration
Impact Report, STOP, and await explicit approval before the next commit.

## Verification Cycle (per Rule 7)

1. Backend test suite: `ENV=test PYTHONPATH=.. .venv/bin/python -m pytest tests/ -q`
   (expected ≥ 4993 passed, 0 failed).
2. Policy tests: `backend/.venv/bin/python -m pytest backend/tests/unit/test_*.py -q`.
3. Gates: `architecture.py check` (Shared Core 0 new, domain 11/11, country-agnostic),
   `domains.py check`, `kernel.py check`.
4. Ruff baseline: `backend/.venv/bin/ruff check backend/app` == 379, no new.
5. OpenAPI byte-compatibility: regenerate and diff against committed baseline.
6. Frontend: `npx tsc --noEmit`, `npx eslint .`, `npx vitest run`, `npx vite build`.

## Baseline Policy

- `architecture-baseline` regenerates the acknowledged-findings list. Run it
  ONLY after a completed migration that legitimately removes findings.
- The acknowledged-findings count must never grow.
- Country findings (2) are tracked separately and never grow.
