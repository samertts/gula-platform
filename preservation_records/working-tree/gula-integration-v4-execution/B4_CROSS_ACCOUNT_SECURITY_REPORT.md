# B4 — Cross-Account Security Administration Report

**Document:** `B4_CROSS_ACCOUNT_SECURITY_REPORT.md`
**Repository:** `gula-integration` — branch `integration/gula-unification-v1`
**Baseline HEAD:** `2206654dc713ea2de8c564a3207dfe05fde23549`
**Owner authority:** `GULA-MASTER-AUTH-2026-11-19` §4 (explicit implementation authorization)
**Date:** 2026-11-19
**Status vocabulary:** `IMPLEMENTED / TESTED / INTEGRATED / INDEPENDENTLY VERIFIED / PRODUCTION READY / BLOCKED / NOT IMPLEMENTED`.
`PRODUCTION READY` is **not** awarded. Independent verification by fresh-context Team C is
**COMPLETE** — verdict `INDEPENDENTLY VERIFIED` at engineering scope
(`GOVERNANCE/ADVERSARIAL_ASSURANCE/INDEPENDENT_VERIFICATION_TEAM_C_B4.md`, 2026-11-19: 0 real
bypasses, 4 residual risks R-1…R-4 recorded).

---

## 1. Scope

Implement and test B4 under the owner's exact model:

- Self-service: a user may access/manage only their own authentication settings.
- MFA challenge and verification are strictly self-only.
- Cross-account administration only for **active** `master_admin` / `security_administrator`
  accounts holding an explicitly assigned, verifiable authorization.
- Server-side authorization; account/MFA/session identifiers resolved server-side; client-supplied
  identifiers are never proof of authorization.
- Fresh NIAM step-up evidence for every cross-account administrative action.
- Reject ineligible actors; deny by default; audit every cross-account action.
- Prevent IDOR, account substitution, privilege escalation, replay and confused-deputy.
- No new roles/permissions, competing authorization engine, or duplicate Phase 1 protection.

Out of scope (unchanged): clinical validation, production infrastructure, Iraqi legal approvals,
release/v1.0.0 declaration, commit/push/PR/deploy.

## 2. Baseline preservation

| Invariant | Observed | Result |
|---|---|---|
| 20 staged `R100` renames under `archive/legacy/workflow_runtime/` | 20 | preserved |
| Protected MD5s (`FINAL_DECISION.md`, MPI audit reports) | `effdfeaf…`, `1a02c015…`, `ea3969d0…` | unchanged |
| `production_ready_items` | 0 | unchanged |
| Sibling `gula-platform` HEAD | `f478676b6fc375338648dde46fbf076c015a3f91` | untouched, read-only |

No commit, push, history rewrite, git-add of ambiguous files, operational DB/Redis access, real
patient data, or external integration was used.

## 3. Implemented behavior

### 3.1 New policy layer — `backend/app/identity/adaptive_auth/b4_guard.py`

A thin policy layer over canonical primitives (no new engine):

| Primitive | Reuse |
|---|---|
| Identity + active session | `NiamActor` / `get_current_niam_actor` (AUD-SEC-007 predicates) |
| Cross-account authority | canonical `niam_roles` / `niam_role_assignments` |
| Recent proof of possession | `StepUpService.assert_fresh` (300 s owner-approved window) |
| Audit | canonical `AuditService` / immutable `niam_audit_entries` |

Enforced decisions:

1. `authorize_account_operation()` re-reads actor account + session from the DB. Ineligible actors
   (non-active status, inactive, locked, substituted session, revoked/expired session) are denied.
2. No target or target == actor ⇒ self-service (no elevated role/step-up required).
3. Any other target is cross-account:
   - `mfa_self_only=True` ⇒ denied even for an authorized administrator.
   - actor must hold an **active, unexpired, unrevoked** assignment to a role whose key is exactly
     `master_admin` or `security_administrator` in the canonical RBAC catalog. The broader
     AUD-SEC-001 control-plane set (`ministry_admin`, `organization_administrator`,
     `compliance_officer`) is deliberately **not** sufficient.
   - actor must have fresh own-account step-up evidence for the specific purpose.
   - a success audit record (`AUTHZ_ALLOW_SENSITIVE`) is **required**: if the audit write fails, the
     action fails closed.
4. Denials are audited (`AUTHZ_PRIVILEGE_ESCALATION_ATTEMPT`, `STEP_UP_FAILED`, `AUTHZ_DENY`).
5. `resolve_own_mfa_challenge()` returns an MFA challenge only if its owning account is the actor.
6. `resolve_session_target()` derives the owning account from the session row before authorizing,
   eliminating session-ID IDOR.

### 3.2 HTTP surface — `backend/app/identity/adaptive_auth/routes.py`

All nine account-scoped endpoints now declare `actor = Depends(get_current_niam_actor)` and route
through the guard before any service call; the resolved target `id` is used downstream, never the
client hint. Global policy endpoints are unchanged and remain behind the router-level AUD-SEC-001
control-plane guard. Router mounting in `identity/api/router.py` was not modified.

The OpenAPI surface is unchanged: `app.main.app` still exposes **1815 paths**.

## 4. Tests executed and exact results

| Check | Command (pinned Python 3.12) | Result |
|---|---|---|
| B4 adversarial suite | `pytest tests/unit/test_b4_cross_account_security.py -q` | **24 passed, 1 warning, EXIT=0 (35.46 s)** |
| Related regressions | `pytest tests/unit/test_niam_step_up.py tests/unit/test_aud_sec_001_control_plane_authorization.py -q` | **51 passed, 1 warning, EXIT=0 (187.42 s)** |
| Static analysis | `ruff check app/identity/adaptive_auth/ tests/unit/test_b4_cross_account_security.py` | **All checks passed!** |
| Import + OpenAPI probe | `python -c '… app.openapi() …'` | imports OK; **1815 paths**, 16 adaptive-auth routes |

Adversarial coverage: unauthorized cross-account reads/writes; account-identifier substitution;
weak control-plane role; expired/revoked/disabled role assignments; missing/expired step-up;
revoked session; suspended administrator; MFA challenge self-only; verification of another
account's challenge; audit completeness (actor/target/purpose/action/result/session/evidence);
structural proof that every account-scoped route binds actor + guard.

No test was deleted, skipped, weakened, xfailed, or had a threshold changed.

## 5. Security implications

- Confused-deputy is closed: authorization subject is the authenticated principal, not a client id.
- Privilege escalation is closed at the role narrowness boundary and by step-up.
- Replay is handled by the already-independently-verified step-up service; B4 consumes its
  fail-closed `assert_fresh` result and records the evidence event id in the audit metadata.
- MFA remains self-only across both challenge and verification.
- No competing engine: authority comes from canonical RBAC; no role catalog was extended.

## 6. Remaining defects / risks

- Fresh-context Team C adversarial verification is **pending**; B4 is `TESTED`, not
  `INDEPENDENTLY VERIFIED`.
- The full backend suite has not been re-run after these changes (targeted + regression gates were
  run). This must be done before any release-level claim.
- Global adaptive-auth policy endpoints are not account-scoped; they remain under the coarse
  AUD-SEC-001 control-plane guard without step-up. This is pre-existing behavior and is recorded as
  a residual, not represented as B4 coverage.
- No production/clinical/legal claim is made.

## 7. Dependencies and blockers

- Team C independent verdict (Wave 8) — not a blocker to implementation, but required before
  `INDEPENDENTLY VERIFIED`.
- Full-suite gate and later waves (2–7) before any acceptance claim.

## 8. Updated acceptance status

- Workstream B4 (`MASTER_EXECUTION_STATUS.md` §2 item 4): `TESTED` (engineering scope).
- Acceptance criterion 7: `TESTED` with B4 evidence; criterion 2 remains `BLOCKED` while Tier B is
  incomplete; criterion 5 unchanged until Team C reports.
- `FINAL_DECISION.md`, protected ADRs and audit evidence were not modified.

## 9. Next executable tasks

1. Record Team C's B4 verdict and update this report / master status accordingly.
2. Implement Tier B B1/B2/B3/B5 using canonical primitives (in progress; primitive map underway).
3. Run the full backend suite on the final tree.
4. Continue Waves 2–7 per directive §15.
