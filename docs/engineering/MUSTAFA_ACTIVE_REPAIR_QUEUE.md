# Mustafa — Active Repair Queue

Tracks findings authorized for direct implementation on
`claude/mustafa-parallel-engineering`, per "GULA — MUSTAFA ACTIVE REPAIR &
ACCELERATION MODE" (uploaded directive, superseding the prior "do not fix
F5 on this branch" instruction). One row per item; update in place, do not
fork a new report document for the same defect.

| ID | SEVERITY | ROOT CAUSE | OWNER | STATUS | CURRENT COMMIT | BLOCKER | NEXT ACTION |
|----|----------|------------|-------|--------|----------------|---------|-------------|
| F5 | P0 (authorization) | `can_manage_user()` in `backend/app/security/rbac.py` returned `True` for every actor role except `province_admin`, with no `lab_id` check — a lab-scoped `admin`/`lab_admin` could toggle-activate or change the role of a user in **any other lab** via `PUT /admin/users/{id}/toggle` and `PATCH /admin/users/{id}/role`. | Mustafa | **FIXED — VERIFIED** | (pending push, this commit) | none | Continue continuous-assurance verification of Abu Ali's milestones; re-assess F2 once a canonical lab-scoped identity context lands on his branch. |

## F5 — Evidence

- **Fix**: `can_manage_user()` now mirrors the existing canonical
  `require_own_lab()` pattern — `master_admin`/`ministry_admin` bypass,
  `province_admin` keeps its existing province-scoped check, and every other
  role (the lab-scoped `admin`/`lab_admin` tier that actually reaches this
  function) must have `actor.lab_id == target_user.lab_id`. No new
  authorization mechanism was introduced; no second identity/RBAC system was
  created. The two existing callers (`toggle_user`, `change_user_role` in
  `backend/app/routes/admin.py`) are unchanged.
- **Tests**: `backend/tests/test_rbac_tenant_scope.py` — 8 tests, one per
  required property:
  - A: same-lab admin → toggle → ALLOWED
  - B: cross-lab admin → toggle → DENIED, target `is_active`/`perm_version` unchanged after
  - C: same-lab admin → permitted role change → ALLOWED
  - D/E/F: cross-lab admin → role change → DENIED; target role unchanged; target `perm_version` unchanged (no session invalidation); a pre-existing token for the target is still accepted afterward
  - G: `province_admin` reaches only same-province targets, denied cross-province, no side effect
  - H: a client-supplied `province_id` in the request body cannot expand cross-lab authority
  - I: an unauthenticated request is denied (401/403) before any mutation
  - J: IDOR via path `user_id` (real cross-lab id and a nonexistent id) is denied/404, no mutation
- **Negative proof**: temporarily reverted `rbac.py` to the pre-fix
  fallthrough (`git stash` of the fix), re-ran the suite — tests B, D/E/F, H,
  J failed against the vulnerable code (200 where 403 was expected); A, C, G,
  I still passed (they test same-lab/authenticated paths, which were never
  broken). Restored the fix via `git stash pop`, confirmed the diff was
  byte-identical to before the revert, and re-ran the full suite — all 8
  pass again.
- **Regression check**: `test_abac.py`, `test_tenant_isolation_matrix.py`,
  `test_security.py`, `test_feature_flags.py` (127 tests) all pass unchanged
  under the fix.
- **Caller audit**: `can_manage_user` has exactly two reachable callers in
  the entire repo (`backend/app/routes/admin.py:830,882`); both are covered
  by the new test file.
