# Phase 0 — Program Setup and Baseline

**Status:** IN PROGRESS  
**Branch:** `recovery/stable-v1`  
**Base commit:** `46158e905fd97f57ca21c61bb5574d03aed90293`

## Objectives
- Establish governance and a shared operating contract for both development environments and both coding agents.
- Capture repository, branch, workflow, dependency, migration, and test baselines without changing application behavior.
- Reconcile existing evidence and open blockers; do not duplicate existing inventories.
- Produce a reviewed baseline report before any remediation phase begins.

## Work packages
| ID | Work package | Exit evidence |
|---|---|---|
| P0-01 | Repository and branch inventory | Default branch, protected working branch, recent commits, open PRs, workflow inventory |
| P0-02 | Architecture and product boundary | Current product map and authoritative paths, including web-suite relationship |
| P0-03 | Module and dependency inventory | Machine-readable inventory with ownership and dependency references |
| P0-04 | Database and migration baseline | ORM table inventory, Alembic graph, duplicate ownership, clean-DB and existing-DB evidence status |
| P0-05 | Test and quality baseline | Exact commands, environment, pass/fail/skip counts, coverage and static-analysis status |
| P0-06 | Security and privacy baseline | Secrets scan, dependency findings, tenant isolation, audit, privacy and clinical-risk gaps |
| P0-07 | Evidence and blocker register | Severity, owner, reproduction, impact, proposed decision, proof required |
| P0-08 | Baseline review | Human-approved report and explicit go/no-go for Phase 1 |

## Required deliverables
- `EVIDENCE/BASELINE/BASELINE_REPORT.md`
- `EVIDENCE/BASELINE/MODULE_INVENTORY.json`
- `EVIDENCE/BASELINE/DATABASE_INVENTORY.json`
- `EVIDENCE/BASELINE/DEPENDENCY_MAP.json`
- `EVIDENCE/BASELINE/TEST_BASELINE.md`
- `EVIDENCE/BASELINE/SECURITY_BASELINE.md`
- `STATUS/OPEN_BLOCKERS.md`
- `STATUS/NEXT_ACTION.md`

If an equivalent maintained artefact already exists, reference and validate it rather than creating a duplicate.

## Safety boundary
Phase 0 is read-only with respect to application code and database state. Allowed changes are governance, inventory, and evidence documentation on this branch. Do not resolve NR-003 or any other application defect in Phase 0.

## Exit criteria
- Every major repository area is inventoried or explicitly marked NOT AUDITED.
- Each test result is tied to a reproducible command and environment.
- Migration status distinguishes clean-database creation from existing-database upgrade.
- Every P0/P1 blocker has an owner, decision needed, and proof required.
- No unknown is represented as passed or verified.
- A human reviewer approves the baseline before Phase 1.