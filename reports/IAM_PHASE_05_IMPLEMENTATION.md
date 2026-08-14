# IAM Phase 5 — Workspace Architecture Implementation Report

**Repository:** `samertts/gula-platform`
**Branch target:** `feat/iam-workspace-architecture` based on `feat/iam-organizations-facilities`
**Author:** **Manus AI**
**Status:** **PARTIAL — implementation gates pass locally; previous-phase and deployment gates remain incomplete.**

## 1. Executive summary

Phase 5 introduces a server-authoritative workspace context layer for GULA IAM. It keeps GULA as the sole clinical system of record and does not create a second account or clinical database. The implementation provisions one idempotent Citizen Workspace per active human account, validates Professional Workspace eligibility through verified identity records, exposes read/switch contracts, and records the active context against a validated NIAM session.

## 2. Scope delivered

The change includes backend ORM models, an additive Alembic migration, a workspace service, NIAM API routes, authentication provisioning, audit events, frontend API types, a real workspace selector, contract tests, architecture documentation and this implementation report.

## 3. Previous-phase validation

Phases 0–4 were checked against source code, tests, migration graph, local quality gates and GitHub state. They are present but not fully complete under the stricter Phase 5 gate. The detailed matrix is in [`IAM_PHASE_05_PREVIOUS_PHASE_VALIDATION.md`](./IAM_PHASE_05_PREVIOUS_PHASE_VALIDATION.md). Reports and commit messages were not treated as proof without source or test evidence.

## 4. Completion and stop-condition status

The implementation-specific gates pass locally, but the overall Phase 5 result remains `PARTIAL`. Live migration application is unverified, mobile parity is absent, several previous-phase API/security dimensions remain partial, PR #135 has an external Vercel rate-limit failure, and no production deployment was performed. No `IAM-PHASE-04-COMPLETE` tag is created.

## 5. Non-negotiable invariants

The implementation preserves the following invariants: no duplicate account or identity system; no clinical data outside GULA; no client-controlled workspace status; no professional workspace from self-selection alone; no automatic organization activation; no shared database; and no cross-repository communication introduced by this phase.

## 6. Domain model

`Workspace` represents an operational context owned by an existing account or attached to an approved organizational structure. `WorkspaceSessionContext` represents the active context for a validated NIAM session. `WorkspaceType` and `WorkspaceStatus` are extensible string-backed enums so future categories do not require a second context table.

## 7. Workspace types

The registry supports `citizen`, `professional`, `organization`, `facility`, `department`, `administrative`, `government`, `audit`, `security` and `support`. These values describe context, not permission. A workspace ID never grants a role or unrestricted access.

## 8. Lifecycle state machine

The backend state machine permits provisioning to active, active to restricted/suspended/archived/deactivated, restricted to active/suspended/archived/deactivated, and suspended to active/archived/deactivated. Archived and deactivated are terminal. Invalid transitions raise a hard failure and are not silently coerced.

## 9. Citizen provisioning

`ensure_citizen_workspace` derives the deterministic key `citizen:{account_id}` and uses a unique constraint plus lookup to make provisioning idempotent. Only an active human account is eligible. Re-reading an existing workspace does not produce a creation audit event; the event is emitted only after an actual insert and activation.

## 10. Professional eligibility

Professional provisioning requires an active, non-expired, backend-verified `VerificationRecord` for the selected professional type. A user-selected profession or frontend flag is insufficient. The verification provider remains `NOT_CONNECTED` where no real provider has been integrated, and the implementation does not fabricate a government or professional integration.

## 11. Organization, facility and administrative contexts

Organization eligibility currently checks active representative or ownership records created by the Phase 4 foundation. Facility and department fields are modeled for the hierarchy, while complete membership/invitation and role authorization are deferred. Administrative, government, audit, security and support contexts require explicit server-side provisioning and do not automatically activate an organization.

## 12. Session context

A switch writes `WorkspaceSessionContext` with the account, identity and current session identifiers, version and timestamps. The service resolves the internal session from the NIAM `jti`; it does not trust a client-supplied account, identity or session identifier for authorization.

## 13. API surface

The routes are `GET /niam/workspaces`, `GET /niam/workspaces/{workspace_id}` and `POST /niam/workspaces/{workspace_id}/switch`. Listing returns only eligible contexts, retrieval hides unknown or unauthorized contexts, and switching validates eligibility before establishing server context.

## 14. Server-authoritative actor

The workspace API uses the existing NIAM actor dependency. It requires a valid access token, an active account and an active user session. The frontend can request a switch, but the backend decides whether it is allowed and returns the authoritative result.

## 15. Audit events

`workspace_created`, `workspace_switched` and `workspace_switch_denied` are added to the existing audit action vocabulary. Audit writes use the established NIAM audit service and do not include secrets or clinical payloads. Denial is observable without disclosing unauthorized workspace details.

## 16. Migration

Migration `20260814_0003_workspace_architecture` is additive and reversible. It creates `niam_workspaces` and `niam_workspace_contexts`, indexes owner/session lookups, enforces the deterministic workspace uniqueness key and adds foreign-key relationships to existing identity/session structures. The current Alembic head is `20260814_0003`.

## 17. Idempotency and concurrency

Citizen provisioning is safe to retry because the logical key is unique and existing rows are returned. The service flushes before activation and context creation. A live database concurrency test and production migration execution remain required before declaring the phase complete.

## 18. Data isolation

No shared database, clinical table, result, sample, patient record or external repository is introduced. Workspaces are IAM metadata only. GULA remains the policy enforcement point and the clinical system of record; later integrations must use versioned idempotent event envelopes.

## 19. Frontend contract

`client.ts` adds typed workspace summaries and server methods with the workspace routes in the API allowlist. `WorkspaceSelector` consumes the list/switch contract, handles loading/empty/error states, supports RTL/LTR labels and does not fabricate workspace IDs or statuses. The dashboard shell integrates the selector without making it a security boundary.

## 20. Mobile status

No mobile implementation is claimed in Phase 5. Mobile clients must later consume the same backend contracts and must not create a platform-specific workspace/account store. This absence is one reason the overall phase remains partial.

## 21. Backend test coverage

The backend identity suite passed with **75 tests**. The seven Phase 5 tests cover lifecycle transitions, deterministic Citizen provisioning, idempotent re-read behavior, professional verification eligibility, organization eligibility and context switching/denial paths.

## 22. Frontend test coverage

The workspace contract suite passed with **3 tests**. It verifies that list and switch methods use the intended NIAM routes and that the client allowlist does not regress. TypeScript compilation and the production Vite build also passed.

## 23. Quality-gate evidence

The final local gate passed `pytest -q tests/identity`, Python `compileall`, Ruff in no-fix verification mode, Alembic head inspection, the workspace Vitest suite, frontend typecheck and frontend production build. `git diff --check` passed. The gate log is [`final-quality-gate-v2.log`](./phase5-gates/final-quality-gate-v2.log).

## 24. GitHub verification and review state

At report creation, the Phase 5 branch and PR had not yet been pushed. The required review sequence is to create `feat/iam-workspace-architecture` from the Phase 4 branch, push it, open PR #138 against `feat/iam-organizations-facilities`, verify the remote branch SHA and PR base/head, and leave merging to a human reviewer. This section must be updated with the exact remote SHA and PR URL after those operations.

## 25. Remaining risks and next steps

The principal risks are unverified live migrations, incomplete previous-phase API/security dimensions, missing mobile parity, missing real provider integrations, lack of database-level concurrency testing and the external Vercel rate-limit failure on PR #135. The next safe step is review and targeted follow-up work; Phase 6 must not start automatically. No deployment, merge or organization activation is performed by this phase.
