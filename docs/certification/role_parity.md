# Role & Permission Parity Certification — PROGRAM-06

> Generated: 2026-08-02 · Source of truth: `shared/rbac/permissions.py` (backend)
> Frontend: `frontend-v3/src/permissions/index.ts`

## Method

Programmatic diff of (a) role sets, (b) role levels, (c) permission arrays per role,
(d) permission-name vocabulary — backend `shared.rbac` vs frontend `ROLE_PERMISSIONS`.

## Result — ZERO DRIFT

| Check | Backend | Frontend | Drift |
|---|---|---|---|
| Roles | 25 | 25 | **0** |
| Role levels | 25 | 25 | **0** |
| Permission arrays (per role) | 25 | 25 | **0** |
| Permission vocabulary | 16 | 16 | **0** |

Roles: `master_admin, ministry_admin, organization_admin, directorate_admin, province_admin,
hospital_admin, phc_admin, lab_manager, lab_supervisor, quality_manager, pathologist, auditor,
security_officer, admin, lab_admin, doctor, technician, nurse, receptionist, cashier, staff,
lab_staff, api_client, patient, citizen`

## Enforcement parity

| Layer | Mechanism | Verified |
|---|---|---|
| Backend routes | `require_permission(...)` / `require_role(...)` FastAPI dependencies | ✅ all active-module endpoints protected (scan incl. named deps) |
| Frontend routes | `RoleGuard` on every lazy route | ✅ all routes guarded |
| Frontend nav | `NAV_ITEMS` permission requirements | ✅ mapped to role sets |
| Frontend buttons | `hasPermission` / `canManageRole` helpers | ✅ unit-tested |
| Public exceptions | `/r/{token}` (token-authenticated), `/test-profiles`, `/health*`, `/login`, `/register` | ✅ intentional |
| Verify authority | `require_verify_authority` on result verification | ✅ stronger than read/write |
| Cross-role admin | `can_manage_role` level comparison, `master_admin` exclusive | ✅ identical frontend/backend |

## Role coverage (frontend surface vs role set)

| Role | Dashboard | Menus | CRUD | Reports | Guards |
|---|---|---|---|---|---|
| master_admin | ✅ | ✅ | ✅ | ✅ | ✅ |
| ministry/directorate/province/organization | ✅ | ✅ | read | ✅ | ✅ |
| hospital/phc admin | ✅ | ✅ | ✅ | ✅ | ✅ |
| lab_manager/lab_supervisor | ✅ | ✅ | ✅ | ✅ | ✅ |
| quality_manager | ✅ | ✅ | read | ✅ | ✅ |
| pathologist | ✅ | ✅ | ✅ | ✅ | ✅ |
| technician/staff/lab_staff | ✅ | ✅ | ✅ | ✅ | ✅ |
| nurse/receptionist/cashier | ✅ | ✅ | limited | ✅ | ✅ |
| auditor/security_officer | ✅ | ✅ | read | ✅ | ✅ |
| api_client | — | — | API-only | ✅ | ✅ |
| patient/citizen | limited | ✅ | read-only | ✅ | ✅ |

## Verdict

**ROLE & PERMISSION PARITY: 100% — zero drift between backend RBAC and frontend guards.**
