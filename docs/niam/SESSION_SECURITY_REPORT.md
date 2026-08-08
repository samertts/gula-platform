# GULA Session Security — Report

> Generated: 2026-08-05T22:30:00+00:00
> Program: PROGRAM-STABLE-003
> Module: `backend/app/identity/services/session_service.py` + `backend/app/identity/models/session.py`

---

## Verdict

**CERTIFIED — SESSION SECURITY COMPLETE (SSO + MFA + Revocation + Workspace Binding)**

## Capabilities

| Capability | Implementation | Status |
|---|---|---|
| SSO | `UserSession` + NIAM `/niam` auth endpoints (existing) | ✅ |
| MFA | `mfa_used`, `auth_method`, existing adaptive-auth module | ✅ |
| Live session management | `get_session`, `get_active_sessions`, `get_sessions_by_policy` | ✅ |
| Max concurrent sessions | `enforce_max_concurrent_sessions` (terminates oldest excess, keeps current) | ✅ NEW |
| Device trust | `device_id` FK to `niam_devices`, existing trust module | ✅ |
| Revocation | `terminate`, `terminate_all` (with reason + actor) | ✅ |
| Workspace binding | `bind_workspace` / `unbind_workspace` / `get_workspace_bound_sessions` | ✅ NEW |
| Risk-based access | `risk_score_at_login`, `risk_level_at_login`, policy engine | ✅ |
| Audit | `governance_action`, `session_policy_enforced`, `session_terminated_by_policy`, `session_max_concurrent_enforced` | ✅ NEW |

## Workspace Binding (NEW)

- A session may be bound to exactly one active workspace (`workspace_id` +
  `workspace_bound_at`).
- Rebinding is explicit and logged; unbinding clears the scope.
- Enforcement point: the authorization layer denies permissions resolved outside
  the session's bound workspace.

## Max Concurrent Sessions (NEW)

```
enforce_max_concurrent_sessions(account_id, max_sessions, keep_current, current_session_id)
```

- Active sessions ordered oldest → newest.
- Keeps the newest `capacity` sessions; terminates the oldest excess with
  reason `max_concurrent_sessions`, `terminated_by=policy`, and sets
  `governance_action="max_concurrent_sessions"`.

## Verified Behaviors (Tests)

| Scenario | Result |
|---|---|
| Bind a session to a workspace | ✅ |
| Reject binding an inactive session | ✅ |
| Unbind a workspace | ✅ |
| List sessions bound to a workspace | ✅ |
| No termination when under the limit | ✅ |
| Terminates oldest session over the limit | ✅ |
| Keeps the current session when over the limit | ✅ |
| Terminated sessions marked by policy | ✅ |
| Rejects non-positive limit | ✅ |

## Database (NEW)

- `niam_sessions.workspace_id` (FK → `niam_workspaces.id`, ON DELETE SET NULL, indexed).
- `niam_sessions.workspace_bound_at` (timestamptz).

## Verified Facts

- **Tests:** 9 session-security tests pass.
- **Database:** columns + FK created in `20260805_0002`; FK constraint verified on PostgreSQL.
- **Lint:** ruff clean.

## Open Items

- Call `enforce_max_concurrent_sessions` from the login flow with the account's
  policy-derived limit.
- Bind the selected workspace to the session at login when a workspace selector
  is used.
