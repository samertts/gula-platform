# Identity Architecture — PROGRAM-05

## Principles

- **Backend is the single source of truth** — identity logic lives in `backend/app/identity/` (NIAM).
- Registration ≠ Verification ≠ Authorization (Rule 1, Appendix-A).
- Every account passes the lifecycle: pending_verification → identity_verified → active → suspended → deactivated.
- Loss of verification (expired license, suspension) automatically revokes operational permissions (Appendix-B).

## Components

| Component | Module | Notes |
|---|---|---|
| Person Registry | `identity/services/person_service.py` | citizens, workforce, external |
| Identity Records | `identity/services/identity_service.py` | 7 identity types, verification, revocation |
| Accounts | `identity/services/account_service.py` | lifecycle state machine, lockout, password policy |
| Authentication | `identity/services/authentication_service.py` | password login, refresh, logout, session policy enforcement |
| Sessions | `identity/models/session.py` + `adaptive_auth` | JTI sessions, device-aware, policy governed |
| Devices | `identity/services/device_service.py` | fingerprint, trust, revocation |
| Professional Licenses | `identity/models/license.py` | verified/expired/suspended gating |
| Assignments | `identity/models/assignment.py` | role + org/facility/dept scoping |
| Policy Engine | `identity/policy_engine.py` | ABAC conditions and obligations |
| Audit | `identity/models/audit.py` | immutable hash-chained identity events |
| Authorities | `identity/governance/models.py` | government portals, approval workflows |

## Enforcement added in this program

1. Suspended/deactivated accounts can never authenticate — checked before password verification.
2. Auditable lifecycle state machine: allowed transitions only, every transition written to the immutable audit chain.
3. Session policy enforced at login (Rule 8/9): concurrent-session limit applies whether or not concurrency is allowed; the OLDEST session terminates automatically; block when policy forbids termination; sessions record mfa_used + policy_id.
4. NIAM authorization resolves permissions through the shared RBAC model (single source of truth) with organization/facility isolation and professional-license gating.
5. Login success/failure, session start/termination, and lifecycle transitions are all audited.
6. NIAM routes now execute against the real database via the AsyncCompatSession bridge (previously async services on a sync session = 500 on every endpoint).
7. Ellipsis id placeholders in dormant-module call sites resolved at flush (before_insert) — previously a psycopg2 'can't adapt ellipsis' crash.

## Audit actions (identity domain)

```
account_created · account_locked · account_unlocked · account_password_changed
account_mfa_enabled/disabled · account_status_changed · account_suspended · account_restored
account_deactivated · login_succeeded · login_failed · logout_succeeded
session_started · session_terminated · session_terminated_by_policy · device_trusted · device_revoked
identity_verified · identity_revoked · license_issued · license_suspended
role_assigned · role_revoked · permission_granted · permission_revoked · policy_denied
```
