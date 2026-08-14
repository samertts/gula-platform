# P4 Action Matrix — Technical Closure Boundaries

**Baseline:** `origin/main` at `d736e4f166fae20e4084847c3d7d5c8fc6dfeff6`.

**Decision:** This matrix separates technically actionable work from human approval, external-environment access, and future implementation. A row classified `B`, `C`, or `D` is not treated as a technical failure merely because it cannot be closed in the current sandbox.

## Classification

| Class | Meaning |
|---|---|
| `A` | Technically actionable now without human approval, production access, or future product implementation. |
| `B` | Requires explicit human review, approval, governance decision, release decision, or exception. |
| `C` | Requires read-only access to an external or production environment that is not available in this execution. |
| `D` | Requires future implementation or a controlled product/design phase; do not invent or activate it in P4 recovery. |

## 32-row P4 action matrix

| ID | Criterion | Class | Safe action in this execution | Closure evidence required | Current disposition |
|---|---|---:|---|---|---|
| P4-01 | Canonical one-account model | A | Verify Account, Person, Identity, Membership, Workspace separation and search for duplicate authority models; add only proof tests if a real defect is found. | Model/source review, duplicate-authority search, separation tests, CI, human review. | Actionable; no redesign without defect. |
| P4-02 | Account lifecycle | A | Extend negative transition and privileged-transition audit tests where missing; do not change the state machine speculatively. | Legal/illegal/concurrent transition tests, audit assertions, CI. | Actionable; production/runtime evidence remains open. |
| P4-03 | Authentication | A | Complete safe local tests for login/logout/expiry/rate-limit/lock boundaries using existing services. | Unit/security tests, CI, runtime verification after approved release. | Actionable locally; release evidence remains B/C. |
| P4-04 | Session and refresh security | A | Add or verify negative tests for refresh reuse, revoked/expired session, wrong account and wrong workspace. | Server-side tests, tenant tests, CI, runtime evidence. | Actionable locally; no production activation. |
| P4-05 | MFA/passkey boundary | B | Document actual implementation and activation requirements; do not activate or claim controlled activation without approval. | Server-side flag/route proof, security tests, owner approval. | Human-controlled boundary. |
| P4-06 | Account recovery | A | Complete local tests proving recovery cannot bypass identity, account state, authorization, membership or workspace. | Negative/security tests, audit tests, CI, recovery review. | Actionable locally; recovery design review remains open. |
| P4-07 | Device/session management | A | Verify local device registration, session binding, revocation, logout-all and audit behavior; do not enable device identity integrations. | Service/API tests, audit assertions, CI. | Actionable locally; external activation prohibited. |
| P4-08 | Verification levels and sources | A | Verify state-machine coverage for UNVERIFIED/PENDING/VERIFIED/SUSPENDED/REVOKED/EXPIRED and source metadata without fabricating providers. | State tests, source/status/expiry audit tests, CI. | Actionable locally; official source remains external. |
| P4-09 | Identity linking and duplicate detection | A | Verify duplicate detection and manual-review behavior; reject weak automatic merge by name/phone/email/OCR/user-entered ID. | Conflict tests, MANUAL_REVIEW_REQUIRED tests, audit/CI. | Actionable locally; official identity remains out of scope. |
| P4-10 | Citizen workspace | A | Complete server-side isolation tests for citizen A versus citizen B using real authorization context. | Cross-citizen denial tests, workspace audit, CI. | Actionable locally; live runtime remains C. |
| P4-11 | Organization workspace context | A | Verify organization/facility/workspace/membership context switching and unauthorized-context denial. | Context-switch tests, permission tests, CI. | Actionable locally; production values remain C. |
| P4-12 | Membership lifecycle | A | Add/verify expiry, revocation, replay and concurrency tests without client-authoritative status changes. | Lifecycle/concurrency/negative tests, audit, CI. | Actionable locally. |
| P4-13 | Membership scope | A | Verify organization/facility/workspace scope isolation across A and B contexts. | Cross-scope integration/security tests, CI, PostgreSQL evidence if available. | Actionable locally; live DB proof remains C. |
| P4-14 | Role and permission catalog | A | Search for speculative permissions/admin-all shortcuts and verify canonical catalog behavior. | Catalog tests, duplicate/deprecation checks, authorization CI. | Actionable locally; governance approval may remain B. |
| P4-15 | Role assignment enforcement | A | Complete negative tests for self-role, self-permission, cross-org/facility/platform escalation. | Direct API and concurrent mutation tests, CI. | Actionable locally; release review remains B. |
| P4-16 | Delegation and temporary authority | D | If implementation is incomplete, mark IMPLEMENTATION_REQUIRED and do not invent delegation functionality. | Future design, implementation, expiry/revocation tests. | Future implementation; not a safe P4 recovery change. |
| P4-17 | Break-glass boundary | D | Keep disabled and do not implement speculative break-glass capability. | Separate controlled design and approval. | Future controlled design. |
| P4-18 | Platform administration separation | A | Verify organization admin, facility admin, staff and platform admin separation with explicit negative tests. | Privilege matrix, escalation denial tests, audit/CI. | Actionable locally. |
| P4-19 | Canonical authorization engine | A | Search protected routes for duplicate/legacy/frontend-only/direct-DB authorization bypass; add tests or stop on any bypass. | Route-to-AuthorizationDecisionService map, bypass search, security regression. | Actionable; any bypass is BLOCKED. |
| P4-20 | Audit integrity | A | Inventory and test audit coverage for registration/authentication/verification/membership/role/permission/workspace/delegation/recovery/admin; assert no secrets/OTP/passwords. | Event inventory, redaction tests, hash/append-only tests, CI. | Actionable locally; runtime completeness remains C. |
| P4-21 | Frontend/backend parity | A | Build exact route/screen/API/service/permission/workspace/org/audit/test matrix; fix only proven safe discrepancies and preserve no-fallback boundary. | Matrix, frontend tests, backend route tests, build/CI. | Actionable for source/test parity; deployment remains C/B. |
| P4-22 | Mobile parity | C | Attempt local Android/iOS/Flutter/Desktop builds only if toolchains are present; otherwise record NOT_BUILT. | Actual build/test logs, no inferred parity. | Environment-dependent; no fabricated result. |
| P4-23 | Error and denial matrix | A | Add/verify 401/403/404/409/422/429/500/503/timeout safe behavior and no sensitive leakage. | Backend/frontend tests and CI. | Actionable locally. |
| P4-24 | PostgreSQL integrity | A/C | Inspect repository migrations/constraints/indexes and run CI/local non-production checks; live state requires C. | Migration/schema tests, FK/unique/index/transaction evidence, live read-only proof. | Repository portion actionable; live DB is C. |
| P4-25 | Security quality | A/B | Keep CodeQL/dependency/Gitleaks/Secret Guard passing; remediate critical Ruff/MyPy in scoped batches; any full-debt exception requires B. | Exact before/after counts, targeted tests, CI, governance decision for exceptions. | Scoped remediation actionable; exception is human-controlled. |
| P4-26 | Performance | D | Do not invent benchmark results; inspect only existing benchmark infrastructure. If absent, record PERFORMANCE_EVIDENCE_REQUIRED. | Reproducible P50/P95/P99 and query evidence. | Evidence/future benchmark work. |
| P4-27 | Feature flags and safe defaults | A/B/C | Create manifest with defaults/owners/rollback/audit; verify source defaults; production values require C and activation approval B. | Manifest, server-only enforcement tests, read-only runtime inspection, approval. | Manifest actionable; current production values unverified. |
| P4-28 | Privacy and legal boundary | B | Preserve data minimization and mark unresolved legal items; do not make legal/compliance claims without review. | Sensitive-field inventory, privacy/legal review. | Human governance boundary. |
| P4-29 | Rollback | A/C | Create non-production rollback rehearsal if local infrastructure permits; never alter production. | Rehearsal logs, OFF/STUB/false checks, authorization/audit preservation. | Local rehearsal actionable; production rollback access is C. |
| P4-30 | CI/CD | A/B/C | Record required CI and preview evidence; do not deploy. Approved merge/deployment/runtime evidence requires B/C. | CI checks, approved merge SHA, deployment/runtime/database/flag verification. | Technical evidence partial; release boundary remains B/C. |
| P4-31 | Human review and governance | B | Keep PRs open and prepare exact review questions; do not infer approval from CI. | Explicit approvals and governance decisions. | Human blocker. |
| P4-32 | Merge and production verification | B/C | Prepare release sequence and verification checklist; do not merge/deploy or alter production DB. | Approved merge, deployment from approved SHA, runtime/DB/flag evidence. | Human/environment blocker. |

## Safe execution rule

Only class `A` rows may be modified in this recovery branch. Classes `B`, `C`, and `D` remain explicitly unresolved by design and must not be converted into `PASS` by documentation alone. P5 and P5.1 remain blocked.
