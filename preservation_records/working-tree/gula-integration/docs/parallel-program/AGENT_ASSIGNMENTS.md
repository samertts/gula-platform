# AGENT ASSIGNMENTS — PROGRAM-GULA-PARALLEL-001

**Orchestrator:** Principal Engineering Orchestrator (this session)
**Model:** Orchestrator + concurrent specialized subagents
**Wave A mode:** 9 concurrent read-only audit agents, disjoint write sets

---

## Assignment Table

| ID | Agent | Scope (READ) | Owned WRITE paths (disjoint) | Wave C role |
|---|---|---|---|---|
| 01 | Repository & Architecture Auditor | Entire repo; per-project deps; `frontend-v3`, `backend`, `packages`, `services`, `shared` | `docs/parallel-program/architecture/ARCHITECTURE_AUDIT.md`, `docs/parallel-program/architecture/REPOSITORY_DEPENDENCY_MAP.md` | Reviewer; protected-change plans |
| 02 | Frontend Design System | `frontend-v3/**` (tokens, theme, shared components, a11y, RTL/LTR) | `docs/parallel-program/frontend/DESIGN_SYSTEM_AUDIT.md`, `docs/parallel-program/frontend/DESIGN_SYSTEM_REMEDIATION.md` | Remediator (unmodified shared-component files only) |
| 03 | Frontend Clinical Workflows | `frontend-v3/src/pages/**` + page tests | `docs/parallel-program/frontend/CLINICAL_WORKFLOW_AUDIT.md`, `docs/parallel-program/frontend/CLINICAL_WORKFLOW_REMEDIATION.md` | Remediator (unmodified page files only) |
| 04 | Security & Identity Auditor | Auth/RBAC/IAM/session/tenant isolation/audit logs/OWASP/secrets; priority to local-only security files | `docs/parallel-program/security/SECURITY_AUDIT.md`, `docs/parallel-program/security/SECURITY_REMEDIATION_PLAN.md` | Reviewer; approval-gated changes only |
| 05 | Clinical Data & Interoperability Auditor | Clinical lifecycle, FHIR R4, ICD-10, LOINC, UCUM, ISO 15189/27001/27799, eval harnesses | `docs/parallel-program/clinical/CLINICAL_WORKFLOW_AUDIT.md`, `docs/parallel-program/clinical/INTEROPERABILITY_AUDIT.md` | Reviewer; no clinical-logic changes |
| 06 | Offline & Distributed Systems Auditor | Offline mode, event bus/store, idempotency, conflict resolution, CRDT/vector clock/Merkle, retries | `docs/parallel-program/distributed/OFFLINE_AUDIT.md`, `docs/parallel-program/distributed/SYNCHRONIZATION_AUDIT.md` | Reviewer; no protocol changes |
| 07 | Backend, API & Database Auditor | Backend, API contracts, validation, transactions, DB integrity, indexes, migrations, perf; high-risk migration/history review | `docs/parallel-program/backend/BACKEND_AUDIT.md`, `docs/parallel-program/backend/API_CONTRACT_AUDIT.md`, `docs/parallel-program/backend/DATABASE_MIGRATION_AUDIT.md` | Reviewer; no backend/DB/API edits |
| 08 | DevOps, Performance & Reliability | Docker, CI/CD, build, lint, coverage, observability, health, scaling, backup/restore; existing infra only | `docs/parallel-program/operations/DEVOPS_AUDIT.md`, `docs/parallel-program/operations/PERFORMANCE_AUDIT.md`, `docs/parallel-program/operations/RELIABILITY_AUDIT.md` | Remediator (standalone CI/doc files only, if disjoint) |
| 09 | Testing & Quality Assurance | Existing tests, missing tests, E2E, contract/integration/a11y/security/offline tests | `docs/parallel-program/qa/QA_AUDIT.md`, `docs/parallel-program/qa/REGRESSION_TEST_PLAN.md`, `docs/parallel-program/qa/TEST_RESULTS.md` | Remediator (orchestrator-assigned test files only) |

**Orchestrator-only WRITE paths:** all files directly under `docs/parallel-program/`
(PROGRAM_CONTROL.md, AGENT_ASSIGNMENTS.md, FILE_OWNERSHIP_MATRIX.md,
DEPENDENCY_GRAPH.md, CONFLICT_REGISTER.md, INTEGRATION_LOG.md,
MASTER_REMEDIATION_REGISTER.md, FINAL_MASTER_REPORT.md).

---

## Rules of Engagement (all agents)

1. **READ-ONLY on all source/code/config files.** Wave A produces evidence and reports,
   not code changes.
2. **WRITE only to the exact paths in the "Owned WRITE paths" column.** Never create,
   modify, or delete any other file — including user work and other agents' outputs.
3. **No git state changes:** no add/commit/stage/checkout/switch/reset/clean/stash/merge/
   rebase/cherry-pick/worktree operations of any kind.
4. **No test/migration/build execution against real data.** Static analysis and reading
   existing test output only. Do not run Alembic against any database.
5. **Respect user work:** the working tree has 378 changed paths owned by the user.
   Report on them if relevant, but never modify them.
6. **Evidence-based findings:** cite concrete file paths and line numbers / code
   excerpts. Do not speculate without labeling it as such.
7. **Structured finding IDs:** `<AGENT>-NNN` (e.g. `A04-001`). Each finding must include:
   ID, Severity (P0/P1/P2/P3), Title, Evidence (path:line), Affected components,
   Root cause, Safe-fix possible? (yes/no), Approval required? (yes/no + why).
8. **No clinical or security behavior invention.** Report gaps; do not design new
   clinical procedures or weaken controls.
9. **Scope escalation:** if a needed change falls outside your write set, log a
   `SCOPE_REQUEST` in your report for the orchestrator — do not act on it.
10. **Return a concise summary** to the orchestrator: agent ID, files reviewed (count +
    key paths), finding count by severity, top 5 findings, and any scope requests.

---

## Wave C Authorization (not yet granted)

Wave C may begin only after:
- `MASTER_REMEDIATION_REGISTER.md` is consolidated and approved by the orchestrator;
- `FILE_OWNERSHIP_MATRIX.md` confirms each target file is owned by one agent;
- each target file is verified **unmodified by the user** (`git status --porcelain`);
- no P0 finding is open on the affected component.

Wave C eligible remediators: A02 (design system), A03 (pages), A08 (standalone
CI/docs), A09 (assigned tests). A01/A04/A05/A06/A07 remain reviewers and produce
protected-change plans only.
