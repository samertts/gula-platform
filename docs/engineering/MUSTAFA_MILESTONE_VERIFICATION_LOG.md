# GULA — Independent Milestone Verification Log (Mustafa)

Append-only log. One entry per Abu Ali milestone commit independently
verified from `claude/mustafa-parallel-engineering`. Verification is
read-only against his branch (isolated `git worktree --detach`, removed
after use) — his branch is never checked out for editing, never rebased,
never merged.

---

## Milestone: `112b2821` ("NR-126: one evicted module, eighty-six failures, all of them 503")

Range verified: `1dbca8f0..112b2821` (7 commits, 27 files,
+6576/-4579). Diff inspected file-by-file; two claims below required a
runtime check, done via a detached worktree at `112b2821`
(`git worktree add --detach <tmp> 112b2821`), removed immediately after.

### VERIFIED (no new P0/P1)

| Change | File(s) | Why it's sound |
|---|---|---|
| `not <SQLAlchemy Column>` → `~Column` / `.is_(False)` | `lims/routes.py` (18 sites), `pharmacy/routes.py`, `radiology/pacs.py`, `services/hospital_service.py` | Pure correctness fix — `not <Column>` always evaluated the Python object's truthiness (always `True`), so every affected query was silently `WHERE false` (zero rows, not a tenant leak — the opposite failure mode). `lab_id == _lab_id(current_user)` scoping is untouched everywhere this pattern appears. Regression-guarded by a new AST-based test (`test_no_sql_filter_is_handed_a_python_not`, with a "ledger only shrinks" ratchet). |
| Double `/niam/niam/...` prefix collapsed | `identity/adaptive_auth/routes.py`, `identity/governance/routes.py`, `identity/trust/routes.py` | Checked the parent mount (`identity/api/router.py`) before concluding anything: all three are `include_router(..., dependencies=_AUTH_REQUIRED)`, i.e. gated by `get_current_niam_actor` (real JWT verification via `decode_token`, plus an `Account.is_locked` check) at the mount level, invisible from the leaf route file alone. **Initial read of the leaf files in isolation looked like zero authentication — that was a false positive, retracted after checking the actual mount point.** Regression-guarded (`test_no_router_declares_a_prefix_its_parent_already_carries`). |
| `logout()` now checks `Authorization: Bearer` + `X-Refresh-Token`, not just cookies | `routes/login.py` | Real P0 fix (logout was a measured no-op for every non-cookie client). Attacked for forgery: both `decode_token`/`decode_refresh_token` perform real signature verification before anything extracted is trusted — a caller can only blacklist/invalidate a token they actually possess and that verifies, not an arbitrary claimed identity. |
| `gender` normalization (`"male"`→`"M"`) applied to `PatientCreate` and (newly) `PatientUpdate` | `routes/patients.py` | Pure correctness (was a 500, not a 422); no auth/tenant surface touched. |
| `health_id` generation reads the actual column width | `services/patient_service.py` | Pure correctness (was a 500 on Postgres). Noted, not flagged: the fix generates 40 hex chars then truncates to the column width, so entropy used is column-width-dependent rather than a fixed amount — still far more than enough for a non-secret identifier; not a security-relevant reduction. |

### FAILED — new, independently confirmed

**F5 — P0 — `admin.py`'s tenant-scope fix is incomplete: `can_manage_user()` still allows cross-lab account tampering**

- **What the milestone fixed:** `toggle_lab`, `activate_lab`,
  `list_pending_labs`, `get_lab_detail`, `create_lab`, `list_doctors`,
  `approve_doctor`, `list_citizens` all gained a
  `_require_platform_scope`/`_require_province_scope` check. Abu Ali's own
  comment on this diff states the bug class precisely: *"`platform:
  manage_users` is held by ... the tenant-level admin/lab_admin (50)
  ... enough for handlers that scope their own query by actor.lab_id,
  and NOT enough for anything acting on a lab other than the actor's
  own."*
- **What it missed:** `PUT /admin/users/{id}/toggle` and
  `PATCH /admin/users/{id}/role` — both gated only by
  `Depends(require_manage_users)` (permission-possession only, no scope)
  and `can_manage_user(actor, target)`
  (`backend/app/security/rbac.py`, **not touched by this diff**):
  ```python
  def can_manage_user(actor, target_user) -> bool:
      if not can_manage_role(actor.role, target_user.role):
          return False
      if actor.role == "province_admin":
          return actor.province_id == target_user.province_id
      return True   # <- every other role, including tenant admin/lab_admin,
                     #    falls through here with NO lab_id check at all
  ```
- **Runtime proof** (against the actual committed function, in the
  detached worktree, no DB required — `can_manage_user` takes plain
  attribute-bearing objects):
  ```python
  from types import SimpleNamespace
  from backend.app.security.rbac import can_manage_user
  actor  = SimpleNamespace(role='admin', lab_id=1, province_id=5, id=100)
  target = SimpleNamespace(role='doctor', lab_id=2, province_id=9, id=200)
  can_manage_user(actor, target)  # -> True
  ```
  A `lab_admin`/`admin` at Lab 1 can manage a `doctor` at Lab 2 — a
  different lab, a different province, no relationship declared between
  them at all.
- **Impact:** a tenant-level `admin` account (an ordinary, already-issued
  role — not a privileged foothold) can, for any user in **any lab on the
  platform** whose role sits below `admin`'s level:
  - `PUT .../toggle` — deactivate (or reactivate) that account, a
    cross-tenant availability/integrity hit;
  - `PATCH .../role` — reassign that account's role to anything below the
    actor's own level, **and** this path calls `bump_perm_version`,
    forcibly invalidating every existing JWT the target holds — an
    immediate, weaponizable disruption of another lab's staff account.
- **Why this is in scope for milestone verification, not "reopening a
  closed finding":** never examined by any prior pass on this branch;
  found specifically while attacking the trust boundary this exact
  milestone changed (tenant-vs-platform scope in `admin.py`); same file,
  same theme, same author's own stated bug class, one shared helper away
  from the routes he did fix.
- **Not fixed here:** `backend/app/security/rbac.py` is core RBAC logic
  immediately adjacent to Abu Ali's active identity work — per this
  engagement's standing rule, not modified. This is reported for him to
  fix, most likely by giving `can_manage_user` the same
  `actor.lab_id == target_user.lab_id` check `province_admin` already
  gets (for the non-platform-role branch), but that's his call on the
  exact shape.
- **Disposition: FAILED (partial).** The milestone's own stated goal —
  closing the tenant/platform scope gap in `admin.py` — is not fully
  met; two routes sharing its target vulnerability class remain
  exploitable.

### Cross-user / cross-tenant / malformed-context probes that came back clean

- NIAM auth gate (`get_current_niam_actor`): confirmed real signature
  verification + `Account.is_locked` check, not a stub.
- `logout()`'s new header-based paths: no cross-user forgery path found
  (both decode functions verify signature before trusting any extracted
  identity).
- `access_share`/`revoke_share` (`radiology/pacs.py`, part of the
  `not`-negation fix): confirmed `access_code` is still actually compared
  (`share.access_code != access_code`) post-fix, and expiry is checked —
  the fix restores intended behavior (these were unconditionally
  returning `None`/`False` before, i.e. accidentally fail-closed, not a
  new opening).

### Not chased further (would exceed "no broad scans")

- `create_user`/`list_users` (same file) already had their own inline
  `actor.role == "admin"` lab-scoping, independent of `can_manage_user`
  — confirmed correct, not part of the gap.
- `revoke_doctor`/`toggle_citizen`/`verify_citizen` restrict to
  `("master_admin", "ministry_admin")` only (excludes `province_admin`
  and tenant admin entirely) — unchanged by this diff, narrower than the
  gap above by construction, not investigated further.
- The rest of `backend/app/identity/` (persons, sessions, devices —
  Abu Ali's own NR-108 comment already documents a much larger,
  already-tracked version of the "router mounted with no actor
  dependency" pattern there) was not re-audited; his comment shows it's
  already on his own radar.

### Regression guards checked

`test_no_sql_filter_is_handed_a_python_not`,
`test_the_constant_false_ledger_{only_shrinks,does_not_rot}`,
`test_no_router_declares_a_prefix_its_parent_already_carries`,
`test_the_login_gate_still_demands_a_second_factor_for_privileged_roles`,
`test_an_out_of_band_mfa_enrolment_path_exists` — all read, all
structurally sound for what they claim to guard. None of them exercise
`can_manage_user`'s lab-scope gap (F5) — expected, since that gap is
outside what this milestone set out to fix.

### Verdict

**FAILED (partial)** — the milestone's own admin.py tenant-scope fix is
incomplete (F5, new P0). Every other change in the range: **VERIFIED**.
