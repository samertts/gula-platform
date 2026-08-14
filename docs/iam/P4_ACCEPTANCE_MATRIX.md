# P4 Acceptance Matrix — GULA Canonical Identity and Access Platform

**Status:** `REMEDIATION_IN_PROGRESS`

**Decision gate:** P4 may be marked `COMPLETE` only when every mandatory row has implementation, test, security, governance, human review, merge, deployment, and verification evidence. A passing test alone does not close a criterion.

**Current baseline:** `origin/main` at `779a76d04d6bf0a2f0dd42ebd680abb7f29840a5` (verified 2026-08-14). PR #188 was merged; PR #189 is documentation-only and was merged. P4 remains `REMEDIATION_IN_PROGRESS`.

## Status vocabulary

| Status | Meaning |
|---|---|
| `COMPLETE` | All required evidence exists and is linked. |
| `PARTIAL` | Some implementation or tests exist, but one or more closure dimensions remain open. |
| `BLOCKED` | A critical security, integrity, deployment, or governance condition prevents closure. |
| `UNVERIFIED` | Evidence was not available or was not independently confirmed. |
| `NOT_IN_SCOPE` | Explicitly excluded by repository governance for this phase. |
| `READY_FOR_IMPLEMENTATION` | Deliberately not implemented; no active capability may claim it. |

## Mandatory P4 acceptance matrix

| ID | P4 criterion | Required evidence | Current repository evidence | Current status | Blocking condition / next evidence |
|---|---|---|---|---|---|
| P4-01 | Canonical one-account model | Account, Person, Identity, Professional Identity, Membership and Workspace remain distinct; no duplicate authority model | Existing NIAM models include `account.py`, `person.py`, `identity.py`, `membership.py`, `workspace.py`; formal end-to-end acceptance proof is not complete | `PARTIAL` | Add end-to-end separation tests and multi-relationship proof; human review required |
| P4-02 | Account lifecycle | Server-authoritative transactional transitions for pending, active, suspended, locked, compromised, deactivated, deletion-requested and deleted; audit for privileged transitions | Account lifecycle services and phase tests exist; complete P4 transition matrix and production verification are not linked | `PARTIAL` | Complete legal/illegal/concurrent transition tests and link deployment evidence |
| P4-03 | Authentication | Valid/invalid login, rate limiting, lockout, secure password handling and audit | Authentication/session implementation exists; full P4 acceptance bundle not independently closed | `PARTIAL` | Complete security matrix and review of recovery boundary |
| P4-04 | Sessions and refresh tokens | Rotation, expiration, revocation, logout, reuse detection and stale authorization prevention | Session and security tests exist; full runtime evidence is not recorded | `PARTIAL` | Add explicit refresh reuse/revocation evidence and runtime verification |
| P4-05 | OTP/MFA/passkeys boundary | Implement only when backend, rate limits, audit, recovery and tests exist; otherwise clearly disabled/ready | No complete acceptance evidence for all methods | `UNVERIFIED` | Record each capability as `IMPLEMENTED` or `READY_FOR_IMPLEMENTATION`; remove any false active UI claims |
| P4-06 | Account recovery | Recovery is not weaker than login and high-risk recovery requires re-verification | No complete P4 recovery acceptance bundle verified | `UNVERIFIED` | Implement or formally defer with explicit non-active status and tests |
| P4-07 | Device/session management | Minimum necessary metadata, listing/revocation where supported, no surveillance expansion | Device components exist; complete acceptance and production verification are not linked | `PARTIAL` | Complete lifecycle and privacy tests |
| P4-08 | Verification levels and sources | Explicit level/source/status/method/timestamp/expiry/reference/audit; no official claim without official source | Verification foundation exists; no fabricated official integration is allowed | `PARTIAL` | Complete source/state tests and mark unavailable integrations `READY_FOR_OFFICIAL_INTEGRATION` |
| P4-09 | Identity linking and duplicate detection | Evidence-based linking, conflict detection, manual review for ambiguity; no automatic merge by weak attributes | No complete independent P4 acceptance proof verified | `UNVERIFIED` | Add review workflow or keep capability non-operational |
| P4-10 | Citizen workspace | Server-authoritative creation, activation, suspension/deactivation, context and isolation | Workspace service and citizen relationship components exist; full lifecycle and cross-citizen test evidence not closed | `PARTIAL` | Complete lifecycle and isolation tests using real authorization context |
| P4-11 | Organization workspace context | Verified membership, organization/facility scope, role and permissions determine context | Organization/facility/workspace components exist; P4 closure evidence is incomplete | `PARTIAL` | Complete context-switch and unauthorized-context tests |
| P4-12 | Membership lifecycle | Invite, accept, reject, approve, suspend, expire and revoke; no client-authoritative status/scope | Membership service/API and phase tests exist; complete P4 closure bundle is not linked | `PARTIAL` | Add full negative/replay/expiry/concurrency evidence |
| P4-13 | Membership scope | Organization, facility, department, unit and workspace scopes are explicit and non-leaking | Scope helpers and authorization tests exist | `PARTIAL` | Complete PostgreSQL cross-scope integration proof |
| P4-14 | Role and permission catalog | Canonical registry; no speculative permissions; no admin-all shortcut; deprecated behavior explicit | Role/permission and authorization components exist; full catalog closure not verified | `PARTIAL` | Verify catalog against existing capabilities and add duplicate/deprecation tests |
| P4-15 | Role assignment enforcement | Self-escalation, cross-org assignment, platform-admin restrictions and scope enforcement are denied | Authorization tests cover several negative paths | `PARTIAL` | Complete concurrent mutation and direct API tests against PostgreSQL |
| P4-16 | Delegation and temporary authority | Issuer, recipient, scope, permission, start, expiry, reason, status and audit; expiry/revocation deny | No complete P4 delegation acceptance proof verified | `UNVERIFIED` | Implement or explicitly defer; never expose active unsupported capability |
| P4-17 | Break-glass boundary | If supported, strong auth, reason, limited scope, time limit, audit and post-event review | No complete accepted break-glass capability verified | `READY_FOR_IMPLEMENTATION` | Keep disabled until separate controlled design/review |
| P4-18 | Platform administration separation | Organization/facility/clinical/government admin cannot self-escalate to platform admin | Authorization restrictions exist in source/tests; closure evidence incomplete | `PARTIAL` | Add explicit privilege-escalation matrix and review |
| P4-19 | Canonical authorization engine | Every protected action evaluates account, identity, verification, membership, role, permission, entitlement, workspace, organization, facility, delegation, resource and feature flag as applicable | `AuthorizationDecisionService` and clinical authorization components exist | `PARTIAL` | Complete action matrix and direct-route coverage; no second policy engine |
| P4-20 | Audit integrity | Server-generated, append-only/hash-protected, queryable, no secrets; before/after for sensitive state changes | Canonical audit and audit services exist; full P4 event inventory and runtime verification not closed | `PARTIAL` | Complete event coverage, integrity tests and production verification |
| P4-21 | Frontend/backend parity | Every active screen maps to real API, handler, service, permission, context, audit, flag and test | `/patients` and `/orders` are within the active clinical gate; broader screens remain blocked/bridge-only | `PARTIAL` | Generate and review final parity matrix; do not open blocked clinical surfaces |
| P4-22 | Mobile parity | Web/Android/iOS/Desktop use shared contracts and do not implement platform-specific authorization | Mobile parity not verified in this execution | `UNVERIFIED` | Run mobile gates or record `NOT_BUILT` explicitly |
| P4-23 | Error and denial behavior | 401/403/404/409/422/429/500/503/timeout handled without leakage or legacy authorization fallback | Some frontend/backend tests exist; full matrix not closed | `PARTIAL` | Add explicit client error-state tests and no-fallback assertions |
| P4-24 | PostgreSQL integrity | Migrations, FK/unique/index constraints, atomic transitions, concurrency and tenant isolation on real PostgreSQL | CI migration/schema gate passed for earlier PR chain; live database and full P4 matrix are not verified | `PARTIAL` | Run current PostgreSQL integration suite and record migration state |
| P4-25 | Security scans | SAST, dependency scan, secret scan, endpoint/tenant/privilege tests | Current CI passed CodeQL, dependency review, Python dependency audit and Gitleaks; local public-secret guard passed. Full Ruff/MyPy still fail on the repository/critical scope. | `BLOCKED` | Continue scoped Ruff/MyPy remediation; preserve CI scanners and rerun critical-path gates |
| P4-26 | Performance | P50/P95/P99 for login, registration, workspace resolution, membership lookup, authorization and verification lookup; no N+1/unbounded queries | No P4 performance evidence verified | `UNVERIFIED` | Add bounded benchmark suite and evidence; do not optimize by bypassing authorization/audit |
| P4-27 | Feature flags and safe defaults | Sensitive integrations have default, owner, scope, rollout, rollback and audit; external integrations OFF | Clinical gateway is server-controlled and OFF by default; complete P4 flag inventory is not linked | `PARTIAL` | Produce feature-flag inventory and verify production values |
| P4-28 | Privacy and legal boundary | Data minimization, purpose limitation, access, retention, privacy and legal-review markers | Repository governance prohibits fabricated legal claims; full P4 data inventory not closed | `PARTIAL` | Mark unresolved legal items `LEGAL_REVIEW_REQUIRED` and complete sensitive-field review |
| P4-29 | Rollback | Every P4 capability has rollback preserving audit, identity, clinical, membership and account integrity | No complete rollback rehearsal evidence verified | `UNVERIFIED` | Produce rollback runbook and non-production rehearsal evidence |
| P4-30 | CI/CD | Required jobs pass and production evidence is tied to the merged commit | PR #189 and PR #192 checks passed; Vercel previews succeeded. Production deployment remains on commit `5265760dcf28ba1c65bafcc9abdfca8a6917e926`, behind current `origin/main` `779a76d04d6bf0a2f0dd42ebd680abb7f29840a5`; Railway remains unknown. | `PARTIAL` | Verify approved release alignment and Railway/database/runtime evidence; do not redeploy blindly |
| P4-31 | Human review and governance | Required human approvals exist; no inferred approval from check success or `REVIEW_REQUIRED` | Human approval evidence is not sufficient in current record | `BLOCKED` | Obtain explicit reviewer approvals on P4 PRs |
| P4-32 | Merge and production verification | Correct order, merge commit, deployment from merge commit, runtime/database/flag verification | No independent P4 closure sequence is recorded | `BLOCKED` | Complete after all preceding gates pass; no automatic merge |

## Current hard blockers

| Blocker | Evidence | Required action |
|---|---|---|
| P4 acceptance not closed | Matrix rows remain `PARTIAL`, `UNVERIFIED` or `BLOCKED` | Complete only the rows required by the approved P4 scope |
| Full Ruff gate fails | Current local audit: `636` errors in `backend/app` and `2373` errors on the full repository | Remediate in scoped batches without broad suppression |
| Full MyPy gate fails | Existing backend type failures | Classify and remediate production/security typing first; document bounded exceptions only if approved |
| Full quality closure incomplete | PR #192 reduced scoped critical Ruff from 2 findings to 0. Current local audit still reports Ruff `636` in `backend/app` and `2373` full, plus MyPy `463` in identity and `7484` in `backend/app` | Continue scoped remediation without global suppressions; PR #192 is reviewable but not an automatic P4 closure |
| Railway unknown | No authenticated Railway connector | Verify read-only deployment/database evidence or record an explicit governance exception |
| Human review incomplete | Review evidence is not equivalent to successful checks | Obtain explicit human approvals |
| Production/database closure incomplete | Production is READY but behind current origin/main; live database and post-merge P4 verification are not linked | Verify against the correct approved merge commit and record database/runtime/flag evidence |

## Closure rule

P4 remains `PARTIAL` or `BLOCKED` until every mandatory row is `COMPLETE`. Only after P4 is formally `COMPLETE`, required PRs are reviewed and merged, Vercel/Railway/database/runtime evidence is verified, and repository integrity is clean may a separate task return:

```text
P4_COMPLETE
P5_READY_FOR_PLANNING
```

This document does not authorize P5 implementation.
