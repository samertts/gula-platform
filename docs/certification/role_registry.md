# Enterprise Role Registry — PROGRAM-05

*Generated 2026-08-02 · 25 roles · 19 DB-seeded + 6 shared-model aliases*

Sources of truth: `roles` table (runtime), `shared/rbac/permissions.py` (canonical 25-role model), `frontend-v3/src/permissions/index.ts` (UX gating).

## Level parity check
- shared ↔ frontend level parity: **OK**
- DB-seeded roles: **19/25** — DB is the runtime gate (`seed_roles`); ['admin', 'citizen', 'lab_admin', 'lab_staff', 'province_admin', 'staff'] are shared-model aliases assignable in code but not pre-seeded.

## National / Platform (level 70-100) (7)

| Role | Level | DB seeded | MFA | Delegatable | Temporary | Parent | Scope / notes |
|---|---|---|---|---|---|---|---|
| `master_admin` | 100 | yes | no | yes | no | — | platform · 16 perms |
| `ministry_admin` | 90 | yes | no | yes | no | — | platform · 9 perms |
| `organization_admin` | 85 | yes | no | yes | no | — | platform · 9 perms |
| `directorate_admin` | 80 | yes | no | yes | no | — | platform · 9 perms |
| `province_admin` | 80 | alias | no | yes | no | — | platform · 9 perms |
| `security_officer` | 70 | yes | yes | yes | no | — | facility · 7 perms |
| `auditor` | 70 | yes | yes | yes | no | — | facility · 6 perms |

## Facility Management (50-60) (5)

| Role | Level | DB seeded | MFA | Delegatable | Temporary | Parent | Scope / notes |
|---|---|---|---|---|---|---|---|
| `hospital_admin` | 60 | yes | no | yes | no | — | facility · 11 perms |
| `phc_admin` | 55 | yes | no | yes | no | — | facility · 11 perms |
| `lab_manager` | 50 | yes | no | yes | no | — | facility · 13 perms |
| `admin` | 50 | alias | no | yes | no | — | self · 13 perms |
| `lab_admin` | 50 | alias | no | yes | no | — | self · 13 perms |

## Clinical (25-45) (6)

| Role | Level | DB seeded | MFA | Delegatable | Temporary | Parent | Scope / notes |
|---|---|---|---|---|---|---|---|
| `lab_supervisor` | 45 | yes | no | yes | no | — | facility · 10 perms |
| `quality_manager` | 45 | yes | no | yes | no | — | facility · 6 perms |
| `pathologist` | 40 | yes | yes | yes | no | — | facility · 6 perms |
| `doctor` | 35 | yes | no | yes | no | — | facility · 4 perms |
| `technician` | 30 | yes | no | yes | no | — | facility · 6 perms |
| `nurse` | 25 | yes | no | yes | no | — | facility · 7 perms |

## Operational (20) (4)

| Role | Level | DB seeded | MFA | Delegatable | Temporary | Parent | Scope / notes |
|---|---|---|---|---|---|---|---|
| `staff` | 20 | alias | no | yes | no | — | self · 8 perms |
| `cashier` | 20 | yes | no | yes | no | — | facility · 3 perms |
| `receptionist` | 20 | yes | no | yes | no | — | facility · 5 perms |
| `lab_staff` | 20 | alias | no | yes | no | — | self · 8 perms |

## Patient & External (5-10) (3)

| Role | Level | DB seeded | MFA | Delegatable | Temporary | Parent | Scope / notes |
|---|---|---|---|---|---|---|---|
| `citizen` | 10 | alias | no | yes | no | — | self · 0 perms |
| `patient` | 10 | yes | no | yes | no | — | self · 2 perms |
| `api_client` | 5 | yes | no | no | no | — | self · 2 perms |

## Permission universe (16)

| Permission | Roles holding it |
|---|---|
| `audit:read` | master_admin, ministry_admin, organization_admin, directorate_admin, province_admin, auditor, security_officer, hospital_admin, phc_admin, lab_manager, admin, lab_admin, quality_manager |
| `dashboard:read` | master_admin, ministry_admin, organization_admin, directorate_admin, province_admin, auditor, security_officer, hospital_admin, phc_admin, lab_manager, admin, lab_admin, lab_supervisor, quality_manager, pathologist, doctor, technician, nurse, staff, lab_staff, receptionist, cashier |
| `lab:manage` | master_admin, hospital_admin, phc_admin, lab_manager, admin, lab_admin, lab_supervisor |
| `lab:read` | master_admin, ministry_admin, organization_admin, directorate_admin, province_admin, auditor, security_officer, hospital_admin, phc_admin, lab_manager, admin, lab_admin, lab_supervisor, quality_manager, pathologist, technician, nurse, staff, lab_staff, cashier, api_client |
| `orders:read` | master_admin, ministry_admin, organization_admin, directorate_admin, province_admin, auditor, security_officer, hospital_admin, phc_admin, lab_manager, admin, lab_admin, lab_supervisor, quality_manager, pathologist, doctor, technician, nurse, staff, lab_staff, receptionist, cashier |
| `orders:write` | master_admin, hospital_admin, phc_admin, lab_manager, admin, lab_admin, lab_supervisor, technician, nurse, staff, lab_staff, receptionist |
| `patients:delete` | master_admin, lab_manager, admin, lab_admin |
| `patients:read` | master_admin, ministry_admin, organization_admin, directorate_admin, province_admin, auditor, security_officer, hospital_admin, phc_admin, lab_manager, admin, lab_admin, lab_supervisor, quality_manager, pathologist, doctor, nurse, staff, lab_staff, receptionist, patient |
| `patients:write` | master_admin, hospital_admin, phc_admin, lab_manager, admin, lab_admin, lab_supervisor, nurse, staff, lab_staff, receptionist |
| `platform:manage_labs` | master_admin, ministry_admin, organization_admin, directorate_admin, province_admin |
| `platform:manage_users` | master_admin, ministry_admin, organization_admin, directorate_admin, province_admin, security_officer, lab_manager, admin, lab_admin |
| `platform:view_stats` | master_admin, ministry_admin, organization_admin, directorate_admin, province_admin |
| `results:read` | master_admin, ministry_admin, organization_admin, directorate_admin, province_admin, auditor, security_officer, hospital_admin, phc_admin, lab_manager, admin, lab_admin, lab_supervisor, quality_manager, pathologist, doctor, technician, nurse, staff, lab_staff, patient, api_client |
| `results:write` | master_admin, hospital_admin, phc_admin, lab_manager, admin, lab_admin, lab_supervisor, pathologist, technician, staff, lab_staff |
| `staff:manage` | master_admin, hospital_admin, phc_admin, lab_manager, admin, lab_admin, lab_supervisor |
| `system:admin` | master_admin |
