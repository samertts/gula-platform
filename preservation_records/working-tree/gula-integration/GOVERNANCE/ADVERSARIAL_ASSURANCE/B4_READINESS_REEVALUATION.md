# B4 Readiness Re-Evaluation — Cross-Account Security Administration

**Document:** `GOVERNANCE/ADVERSARIAL_ASSURANCE/B4_READINESS_REEVALUATION.md`
**Repository:** `gula-integration`, branch `integration/gula-unification-v1`, HEAD `2206654dc713ea2de8c564a3207dfe05fde23549`
**Date:** 2026-11-19
**Status vocabulary:** `IMPLEMENTED / TESTED / INTEGRATED / INDEPENDENTLY VERIFIED / PRODUCTION READY / BLOCKED / NOT IMPLEMENTED`. `PRODUCTION READY` is not awarded.

## 1. Trigger

The owner selected option 4: close a bounded NIAM step-up prerequisite before B4. That prerequisite
is now complete:

- Final-tree full suite: `4984 passed, 27 skipped, 203 warnings, EXIT=0`.
- Fresh-context Team C: `INDEPENDENTLY VERIFIED` at engineering scope, 57+ probes, zero real bypasses
  (`INDEPENDENT_VERIFICATION_TEAM_C_STEP_UP.md`).

## 2. B4 surface as actually found (read-only)

`backend/app/identity/adaptive_auth/routes.py`, router prefix `/adaptive-auth`:

| Endpoint | Client-supplied identity | Auth dependency | Step-up dependency |
|---|---|---|---|
| `POST /evaluate` | `account_id` (query) | none | none |
| `GET /risk-history/{account_id}` | `account_id` (path) | none | none |
| `POST /mfa/challenge` | `account_id` (query) | none | none |
| `POST /mfa/verify` | `mfa_id`, `challenge_response` | none | none |
| policy / session-policy endpoints | policy/session ids | none | none |

These are **authentication-only cross-account endpoints** (classified as `AUD-SEC-006` in
`PHASE_2_CANDIDATE_PLAN.md`). No step-up content was introduced into this file by the step-up work
item; its only working-tree delta is a pre-existing one-line router-prefix change attributed to
an earlier phase (`GOVERNANCE/CHANGE_MANIFEST.md:94`, Team C report row 9).

## 3. Owner policy → current B4 gap analysis

| Approved policy | Current B4 state | Gap |
|---|---|---|
| Self-management always allowed | no actor binding on these routes | identity not server-derived |
| Cross-account only for active, explicitly assigned `master_admin` / `security_administrator` | no role guard; no assignment check | unauthorized cross-account access possible |
| MFA challenge/verify strictly self-only | `account_id` and `mfa_id` accepted from the client | cross-account completion possible |
| `mfa_id` / `session_id` from a trusted server source | both client-supplied | session confusion / IDOR |
| Deny by default | routes are open | fail-open |
| Step-up required for sensitive cross-account actions | `require_fresh_niam_step_up` defined but **zero consumers** | not enforced |
| Cross-account access logged | no such audit in these routes | no accountability |
| No new roles/permissions | step-up added none | no gap |

## 4. Decision — `BLOCKED`

**B4 is NOT implemented and NOT authorized in this execution.** The engineering prerequisite is
satisfied, but the owner must still explicitly approve:

1. the step-up work item itself;
2. the Self + Security Administration cross-account model under the previously selected option 4;
3. the assistant-chosen `30–3600` freshness validation bounds (only `300s` is owner-approved).

No B4 source was modified, no role/permission created, no cross-account endpoint wired, no
step-up dependency attached. No `IDOR` / privilege-escalation / session-confusion test was written
against a B4 implementation because there is no authorized implementation to test. No gap above
was "resolved" by this document.

## 5. When authorized, the required implementation shape

- Resolve actor/account/session server-side; never accept `account_id`, `mfa_id`, `session_id`,
  timestamps, or verification flags from the client on sensitive actions.
- Enforce the existing single authorization authority (`AUD-SEC-001`/`AUD-ARCH-003`) with active,
  explicitly assigned `master_admin` / `security_administrator` — role alone is insufficient.
- Attach `require_fresh_niam_step_up` to sensitive cross-account actions; self-only MFA challenge
  and verification against the actor's own account.
- Deny by default; audit every cross-account access; add adversarial IDOR/BOLA/BFLA, privilege
  escalation and session-confusion tests; then request fresh-context Team C verification.

**Final decision:** B4 `BLOCKED` pending the owner decisions in §4. No production claim, no commit,
no push/PR/merge/deploy, no operational data access, no protected decision change.
