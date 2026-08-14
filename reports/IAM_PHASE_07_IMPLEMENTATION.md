# IAM Phase 7 — Role & Permission Engine Implementation Report

**Repository:** `samertts/gula-platform`

**Branch:** `feat/iam-phase6-memberships`

**Base for review:** `feat/iam-all-phases-test-hardening`

**Status:** Implementation complete locally; pending commit, push, Pull Request review, and remote CI.

## Executive Summary

Phase 7 adds a canonical Role & Permission Engine to NIAM while preserving GULA as the clinical system of record and the server-side authorization enforcement point. The implementation introduces catalogued roles and permissions, scoped role assignments, lifecycle transitions, organization-authority checks, audit events, and a reversible Alembic migration. Phase 6 membership discovery remains the prerequisite relationship layer; Phase 7 does not create a second account system or accept client-supplied membership status, actor identity, assignment status, or assigner identity as authoritative.

The frontend now exposes typed role/permission APIs and server-reflected membership context. The Sidebar uses the existing static permission map only in demo mode. For live sessions it does not use the client-side RBAC map as an authorization gate; permissioned navigation items remain visible and the backend remains authoritative for every protected operation. The mobile implementation includes source-level membership discovery changes, but Flutter execution could not be verified because the Flutter SDK is unavailable in the sandbox.

> **Authorization boundary:** frontend capability state is UX context only. Backend authorization, membership eligibility, organization authority, and audit enforcement remain mandatory for live operations.

## Implemented Source Changes

| Area | Implementation | Enforcement or purpose |
|---|---|---|
| Canonical models | `backend/app/identity/models/authorization.py` | Defines `Role`, `Permission`, `RolePermission`, and `RoleAssignment` with catalog and lifecycle enums. |
| Authorization service | `backend/app/identity/services/authorization_service_v2.py` | Implements role grant/revoke, effective permission calculation, permission checks, deterministic assignment keys, scope matching, state transitions, self-escalation rejection, and audit calls. |
| NIAM API | `backend/app/identity/api/roles.py` | Adds role catalog, permission catalog, effective-permission, assignment, revoke, and assignment-list routes. Protected routes use the existing NIAM actor dependency. |
| Router registration | `backend/app/identity/api/router.py` | Registers the roles router under the NIAM API surface. |
| Database migration | `backend/migrations/versions/20260814_0005_role_permission_engine.py` | Creates role, permission, relation, and assignment tables with constraints, indexes, reversible downgrade, and only the specified seed catalog. Uses UTC-aware timestamps. |
| Audit | `backend/app/identity/models/audit.py` | Adds role, permission, assignment, and authorization audit event constants. |
| Backend tests | `backend/tests/identity/test_authorization_phase7.py` | Verifies transition legality, terminal-state behavior, deterministic scope keys, exact scope matching, self-escalation rejection, and client request-field boundaries. |
| Frontend API | `frontend-v3/src/api/client.ts` | Adds typed role, permission, effective-capability, assignment, and revoke methods plus safe read/write allowlist entries. |
| Auth context | `frontend-v3/src/contexts/AuthContext.tsx` | Discovers server-reflected memberships after live session restore/login; failure degrades to an empty UX context and never becomes a local authorization fallback. |
| Sidebar | `frontend-v3/src/layouts/Sidebar.tsx` | Keeps `hasPermission()` as a demo-only visibility filter. Live sessions show permissioned navigation and rely on backend enforcement. |
| Mobile | `mobile/desktop/lib/core/api/api_endpoints.dart`, `mobile/desktop/lib/core/auth/auth_manager.dart` | Adds membership discovery and lifecycle clearing for the mobile auth session. Source present; execution unverified because Flutter SDK is unavailable. |
| Documentation | `docs/architecture/IAM_MEMBERSHIPS.md`, `docs/architecture/IAM_PHASE_06_07_EXECUTION_MATRIX.md`, `reports/IAM_PHASE_06_07_SOURCE_FINDINGS.md`, `reports/IAM_PHASE_06_API_MATRIX.md` | Records the Phase 6/7 architecture, source findings, contracts, and execution matrix. |

## Security and Policy Decisions

Phase 7 explicitly rejects self-escalation before database mutation and requires organization ownership or representative authority through the existing membership authority path. Role assignments are deterministic across account, membership, role, and scope dimensions, which provides idempotency and prevents duplicate scoped assignments. Assignment lifecycle transitions are explicit and terminal revocation cannot be reactivated through the service state machine.

The request schema deliberately excludes `status`, `assigned_by`, and `actor_id` as client-authoritative fields. The backend derives actor identity from the authenticated NIAM actor dependency and derives lifecycle state from service logic. Scope matching is exact for facility, department, unit, and workspace context; Phase 8 ABAC and contextual policy expansion are not implemented.

The migration seeds only the roles and permissions specified by the Phase 7 source specification. It does not grant access to unimplemented clinical workflows, approve clinical results, modify the GULA clinical record, activate organizations automatically, or introduce fabricated government/provider integrations.

## Quality Gate Evidence

The final local gate was run after the Sidebar and AuthContext changes. The command covered backend identity regression, read-only Ruff, Python compilation, all frontend contract/unit tests, TypeScript validation, and the production build.

| Gate | Result | Evidence |
|---|---|---|
| Backend identity tests | **PASS** | `133 passed, 2 deselected` using `pytest -q tests/identity -m "not integration"`. The deselected tests are integration-marked and require PostgreSQL. |
| Backend Ruff | **PASS** | `All checks passed!` with `--no-fix`. |
| Backend compileall | **PASS** | Python identity modules and Phase 6/7 migrations compiled without errors. |
| Frontend tests | **PASS** | Vitest: `10` test files and `34` tests passed. |
| Frontend typecheck | **PASS** | `npm run typecheck` completed successfully. |
| Frontend production build | **PASS** | Vite build completed successfully in approximately `506 ms`; PWA artifacts were generated. |
| Flutter verification | **NOT RUN** | Flutter SDK is unavailable in the sandbox; mobile changes are source-only and must be verified in a Flutter-capable environment. |
| PostgreSQL migration integration | **NOT RUN LOCALLY** | The integration-marked migration tests remain available for CI execution. |

## Remaining Review Boundaries

The local quality gate does not prove live PostgreSQL upgrade/downgrade behavior, production Redis/session behavior, HTTP end-to-end authorization against real JWT/JTI/session records, or Flutter compilation. These remain review and CI responsibilities. The existing open PR chain and Vercel rate-limit limitation must not be treated as a code approval or deployment approval.

No `IAM-PHASE-06-COMPLETE` or `IAM-PHASE-07-COMPLETE` tag is created by this implementation. No merge or deployment is performed automatically. Human review remains required before either phase is considered production-complete.

## Source References

1. [`backend/app/identity/models/authorization.py`](../backend/app/identity/models/authorization.py) — canonical Phase 7 authorization models.
2. [`backend/app/identity/services/authorization_service_v2.py`](../backend/app/identity/services/authorization_service_v2.py) — role and permission service logic.
3. [`backend/app/identity/api/roles.py`](../backend/app/identity/api/roles.py) — NIAM Role API contracts.
4. [`backend/migrations/versions/20260814_0005_role_permission_engine.py`](../backend/migrations/versions/20260814_0005_role_permission_engine.py) — Phase 7 schema and seed migration.
5. [`backend/tests/identity/test_authorization_phase7.py`](../backend/tests/identity/test_authorization_phase7.py) — Phase 7 unit and contract tests.
6. [`frontend-v3/src/layouts/Sidebar.tsx`](../frontend-v3/src/layouts/Sidebar.tsx) — live/demo navigation behavior.
7. [`frontend-v3/src/contexts/AuthContext.tsx`](../frontend-v3/src/contexts/AuthContext.tsx) — server-reflected membership discovery.
8. [`frontend-v3/src/api/client.ts`](../frontend-v3/src/api/client.ts) — frontend IAM API contracts and allowlists.
