# FILE OWNERSHIP MATRIX — PROGRAM-GULA-PARALLEL-001

Legend: `USER` = pre-existing user work (PROTECTED, never touched) · `A0n` = sole
agent owner · `ORCH` = orchestrator · `SHARED-READ` = read-only for all.

---

## 1. Control-plane files

| Path | Owner | Notes |
|---|---|---|
| `docs/parallel-program/PROGRAM_CONTROL.md` | ORCH | Program state |
| `docs/parallel-program/AGENT_ASSIGNMENTS.md` | ORCH | Scope definitions |
| `docs/parallel-program/FILE_OWNERSHIP_MATRIX.md` | ORCH | This file |
| `docs/parallel-program/DEPENDENCY_GRAPH.md` | ORCH | Dependencies |
| `docs/parallel-program/CONFLICT_REGISTER.md` | ORCH | Conflicts |
| `docs/parallel-program/INTEGRATION_LOG.md` | ORCH | Gate + wave log |
| `docs/parallel-program/MASTER_REMEDIATION_REGISTER.md` | ORCH | Consolidated issues |
| `docs/parallel-program/FINAL_MASTER_REPORT.md` | ORCH | Final deliverable |

## 2. Agent report files (Wave A — disjoint)

| Path | Owner |
|---|---|
| `docs/parallel-program/architecture/*.md` | A01 |
| `docs/parallel-program/frontend/DESIGN_SYSTEM_*.md` | A02 |
| `docs/parallel-program/frontend/CLINICAL_WORKFLOW_*.md` | A03 |
| `docs/parallel-program/security/*.md` | A04 |
| `docs/parallel-program/clinical/*.md` | A05 |
| `docs/parallel-program/distributed/*.md` | A06 |
| `docs/parallel-program/backend/*.md` | A07 |
| `docs/parallel-program/operations/*.md` | A08 |
| `docs/parallel-program/qa/*.md` | A09 |

## 3. Source surfaces — Wave A access (READ-ONLY for all agents)

| Surface | Access | Ownership note |
|---|---|---|
| `backend/**` | SHARED-READ | A07 primary auditor; user-modified files protected |
| `backend/migrations/versions/**` | SHARED-READ | A07 primary; 8 untracked migrations are USER |
| `frontend-v3/src/components/**`, tokens/theme/config | SHARED-READ | A02 primary auditor |
| `frontend-v3/src/pages/**` + page tests | SHARED-READ | A03 primary auditor |
| `frontend-v3/**` build/config | SHARED-READ | user-modified: `package.json`, `package-lock.json`, `vite.config.ts` are USER |
| `shared/**`, `packages/**`, `services/**`, `platform/**` | SHARED-READ | A01/A06 primary |
| `.github/workflows/**`, Docker/CI/IaC | SHARED-READ | A08 primary; modified workflows are USER |
| `docs/constitution/**`, `docs/architecture/**`, `GOVERNANCE/**` | SHARED-READ | policy baseline |

## 4. Known USER-OWNED / MODIFIED paths (explicit BLOCK for writes)

These were modified/staged/untracked at Phase 0. They are excluded from all remediation
unless the user explicitly releases them:

- `.github/dependabot.yml`, `.github/workflows/frontend-pwa.yml`,
  `.github/workflows/security-hardening.yml`
- `GOVERNANCE/NATIONAL_INTEGRATION/13_INTEGRATION_TEST_AND_VERIFICATION.md`,
  `14_FINAL_ACCEPTANCE_REPORT.md`, `status_registry.json`
- `SECURITY_REMEDIATION_REPORT.md`
- 20 staged renames: `backend/app/identity/workflows/{engine,models}.py`,
  `backend/app/national/workflow_runtime/**`, `backend/app/platform/workflow.py`
  → `archive/legacy/workflow_runtime/**`
- 126 unstaged-modified backend/frontend/governance files (full list in
  `git status --porcelain`, captured in PROGRAM_CONTROL §2.2)
- 232 untracked files, including: `GLOSI/**`, `GOVERNANCE/**` untracked trees,
  `backend/app/health_core/**`, `backend/app/domain_platform/**`,
  `backend/app/communication/**`, `shared/communication/**`,
  `backend/migrations/versions/20261114_*`, `20261118_*`, `20261119_*`,
  `.gula-lite-permission-test.txt`

## 5. Wave C eligibility rule

A file is eligible for agent remediation **only if all are true**:
1. It matches exactly one agent's primary scope (no overlap);
2. `git status --porcelain -- <file>` returns **empty** (clean, not user-owned);
3. The owning agent has an approved finding in `MASTER_REMEDIATION_REGISTER.md`;
4. No open P0 blocks the component;
5. The change does not alter clinical logic, auth/RBAC behavior, API contracts, DB
   schema/migrations, or CI semantics without independent approval.

Until this rule is satisfied for a given file, its status is `BLOCKED`, not `FIXED`.
