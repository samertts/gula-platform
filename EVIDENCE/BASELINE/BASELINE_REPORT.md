# GULA Stable v1.0.0 — Initial Baseline Report

**Assessment type:** Read-only GitHub inspection  
**Date:** 2026-11-07  
**Repository:** `samertts/gula-platform` (private)  
**Default branch:** `main`  
**Baseline commit:** `46158e905fd97f57ca21c61bb5574d03aed90293`  
**Working branch:** `recovery/stable-v1`

## Executive result
<badge>Phase 0 IN PROGRESS</badge>

The repository is accessible and a dedicated recovery branch has been created from the recorded main commit. Existing project inventories and remediation artefacts are substantial and should be reused. The current evidence does not support production readiness. This report is preliminary: no local test suite, database migration, build, deployment, or security scan was executed as part of this setup.

## Repository and product boundary
- `docs/START_HERE.md` identifies `backend/app/` as the canonical FastAPI backend.
- `frontend-v3/` is documented as the primary web client.
- `services/` is described as future decomposition, not the current canonical backend.
- Root README and product docs also describe `gula-web-suite` as the current managed web implementation. This creates a source/deployment ownership question that must be reconciled; do not assume both web surfaces are interchangeable.
- Existing platform modules are to be preserved during stabilization.

## Existing inventory artefacts discovered
- `docs/api/backend_inventory.json`: documented inventory reports 763 endpoints and 50 modules.
- `docs/technical-debt/registry.json`: documented registry reports 647 items.
- `docs/architecture/GULA_MASTER_NEGATIVE_REGISTER.json`: machine-readable audited findings.
- `tools/gula_intel/inventory.py`: existing inventory implementation.
- `scripts/zero_drift_engine.py` and generated contract-audit artefacts: existing frontend/backend drift tooling.
- `scripts/quality_changed_files_gate.py`: existing change-aware quality gate.
- `backend/tests/migrations/test_migration_graph_integrity.py`: existing migration graph tests.

These are repository-reported counts and artefacts; they have not been independently regenerated in this Phase 0 snapshot.

## Latest main commit evidence
Commit `46158e9` records:
- 101 unique Alembic revision IDs and one head after migration graph repair.
- Blood Bank suite: 32 passed against PostgreSQL 16.13 in the commit's pre-merge evidence.
- Migration graph integrity: 3 passed.
- Intelligent Platform Core: 25 passed.
- NR-003 remains OPEN/P0; pharmacy files were not modified.
- Existing-database upgrade path is not verified.
- `production_ready=false`.

These test results are historical commit evidence, not tests run by this Phase 0 setup.

## CI workflow inspection
The inspected `.github/workflows/ci.yml` defines syntax, data preservation, migration, lint, backend test, and security jobs. It configures Python 3.12, Node 22, PostgreSQL 17 and Redis 7. Workflow definition presence does not prove successful execution. The GitHub connector returned no PR-triggered workflow runs for the inspected commit; current Actions status remains UNKNOWN pending direct run inspection.

## Critical findings
See `STATUS/OPEN_BLOCKERS.md`. The highest-priority blocker is NR-003, but Phase 0 must first collect a complete baseline and the canonical PK decision must be human-approved before remediation.

## Work performed in this setup
- Confirmed private repository and default branch.
- Listed first page of branches; repository has many active/legacy task branches, requiring later branch hygiene review rather than deletion.
- Created `recovery/stable-v1` from the recorded main SHA.
- Added program charter, Phase 0 plan, shared AI agent rules, current state, blocker register, next action, and this report.
- No application source, tests, migrations, deployment configuration, or production data were changed.
- No tests or migrations were executed.

## Remaining Phase 0 work
1. Full branch/PR/workflow inventory and ownership review.
2. Validate existing machine-readable inventories and avoid duplicate registries.
3. Generate module, database table/owner, dependency and migration inventories.
4. Run controlled baseline checks on Ubuntu and Windows.
5. Review tenant isolation, privacy/consent, audit, offline/sync, backup/restore and security evidence.
6. Human approval of the final baseline and explicit Phase 1 go/no-go.

## Verdict
**NOT READY FOR PHASE 1 REMEDIATION YET.** Phase 0 documentation setup is established, but the executable baseline is incomplete. Production readiness remains NOT CERTIFIED.