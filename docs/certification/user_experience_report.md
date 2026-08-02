# P5.7 — Role Experience Verification Report (User Experience)

Program: PROGRAM-05 (Role Experience Certification) — P5.3/P5.7
Date: 2026-08-02
Harness: `/tmp/opencode/p5_role_experience.py` — 25 roles × 18 checks each.

## Result: **450 / 450 checks passed**

| Check | What it verifies |
|---|---|
| `login` | plain login works; MFA roles (auditor, security_officer, pathologist) complete TOTP challenge |
| `identity` | `GET /authz/me` returns correct identity context (fixed 500: `LabUser` missing `organization_id` → `getattr` fallbacks) |
| `permissions-exact` | `/authz/me/permissions` matches declared model exactly (fixed: no-role-assignment users dropped to `[]` — now falls back to legacy `user.role` perms) |
| `menu` | `GET /authz/me/menu` builds |
| `dashboard` | `/dashboard` 200 iff `dashboard:read` declared |
| 14-route probe matrix | allowed routes return 200/201/404/422; forbidden routes return **403** — enforced by `require_permission` route gates |

## Defects found & fixed during P5

### 1. Broken Function Level Authorization (OWASP API5) — CRITICAL
- **Before**: routes authenticated any user; a `citizen` (0 permissions) received **200** on
  `/patients`, `/clinical/orders`, `/test-results`, `/samples`.
- **Fix**: permission-gated 25 route modules with `Depends(require_permission(...))`
  (patients, test_results, samples, clinical_orders, labs, results, stats,
  quality_control, canonical_patient, patient_card, authorization catalog,
  compliance, ehr, ehr_fhir, care_continuum, clinical, clinical_documentation,
  hospital, ai_platform, ai, ai_telemetry, tiers, edge, service_accounts).
- **After**: citizen → 403 on all data routes; every role's allowed/denied set matches the
  shared RBAC model exactly (probe matrix, 450/450).

### 2. `/authz/me` 500 — identity context for `LabUser`
`get_identity_context` assumed legacy `User` attributes (`organization_id`, `tenant_id`,
`facility_id`, `full_name`, `mfa_enabled`, `is_verified`, `governorate_id`); `get_current_user`
returns `LabUser`. Fixed with `getattr()` fallbacks. **Result**: identity + menu + permissions
endpoints work for every role.

### 3. `/authz/me/permissions` returned `[]` for assignment-less users
Users created via `POST /admin/users` (the standard path) have `lab_users.role` but no
`role_assignments` rows. `get_granted_permissions` returned `[]` → empty menus/frontend
breakage. Fixed: no-assignment users now fall back to legacy role permissions; assignments
still override/merge. Regression tests updated (`test_no_roles_empty`, new
`test_no_role_no_assignments_empty`).

### 4. Result verification authority — clinical sign-off policy
- `verify_result` service restricts sign-off to `admin`, `master_admin`, `doctor`
  (clinical safety, Phase 12.D, tested in `test_clinical_safety.py`).
- Route gate `require_permission("results:write")` contradicted this: **doctor** has no
  `results:write` but is a sign-off authority.
- Fix: new `require_verify_authority` dependency — allows `admin`/`master_admin`/`doctor`
  OR `results:write` holders. Harness verifies both sides (doctor allowed, technician 403
  despite `results:write`).

### 5. `/edge` permission correction
Device/task admin routes were gated `system:admin` (only master_admin). Edge devices are
facility-level: corrected to `lab:manage` (admin, hospital_admin, lab_admin, lab_manager,
lab_supervisor, master_admin, phc_admin). Frontend NAV updated to match.

## MFA verification
3 roles enforce MFA (DB `requires_mfa=true`): `auditor`, `security_officer`, `pathologist`.
All 3 completed login with live TOTP (pyotp, ±30s drift) — 3/3 passed.

## No-role edge cases
`citizen` (0 perms) → 403 on all data routes, identity-only surface. Verified.

## Regression status
- Backend full suite: **2786 passed** (2683 main + 103 comprehensive)
- Clinical safety sign-off tests: pass
- ruff clean on all changed files (379 remaining = pre-existing E402/N801/N999 baseline)
- Frontend: tsc/eslint/build clean
