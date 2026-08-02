# P5.6 — Role Dashboard Catalog

Program: PROGRAM-05 (Role Experience Certification)
Date: 2026-08-02
Method: live-login per role (`demo.{role}@demo.local`), `GET /dashboard` with real tokens (incl. TOTP MFA for auditor/security_officer/pathologist).

## Gate

`/dashboard` requires `dashboard:read`. Roles without it receive **403**:
`citizen` (0 perms), `patient` (2 perms), `api_client` (2 perms).

## Widgets (identical payload shape for all allowed roles)

| Widget key | Meaning |
|---|---|
| `greeting` | Arabic greeting with user name |
| `lab_name` | Active lab context |
| `today` | Orders today |
| `this_week` | Orders this week |
| `orders` | Total orders |
| `patients` | Total patients |
| `tests` | Total tests |
| `critical` | Critical-value alerts |
| `abnormal_results` | Abnormal result count |
| `recent_orders` | Latest orders feed |

## Access matrix (25 roles)

| Role | Status | perms | Widgets |
|---|---|---|---|
| master_admin | 200 | 16 | all 11 |
| admin | 200 | 13 | all 11 |
| lab_admin | 200 | 13 | all 11 |
| lab_manager | 200 | 13 | all 11 |
| hospital_admin | 200 | 11 | all 11 |
| phc_admin | 200 | 11 | all 11 |
| lab_supervisor | 200 | 10 | all 11 |
| ministry_admin | 200 | 9 | all 11 |
| organization_admin | 200 | 9 | all 11 |
| directorate_admin | 200 | 9 | all 11 |
| province_admin | 200 | 9 | all 11 |
| lab_staff | 200 | 8 | all 11 |
| staff | 200 | 8 | all 11 |
| security_officer | 200 | 7 | all 11 |
| nurse | 200 | 7 | all 11 |
| auditor | 200 (mfa) | 6 | all 11 |
| pathologist | 200 (mfa) | 6 | all 11 |
| quality_manager | 200 | 6 | all 11 |
| technician | 200 | 6 | all 11 |
| receptionist | 200 | 5 | all 11 |
| doctor | 200 | 4 | all 11 |
| cashier | 200 | 3 | all 11 |
| api_client | **403** | 2 | — |
| patient | **403** | 2 | — |
| citizen | **403** | 0 | — |

## Findings

1. Dashboard is permission-gated correctly (only `dashboard:read` holders reach it).
2. Widget payload is uniform — no role-specific data leakage differences at the key level; per-lab isolation is enforced by the service layer (tested in PROGRAM-011/unit tests).
3. 22/25 roles have dashboard access; the 3 denied roles match the declared permission model exactly.
4. Auditor + security_officer + pathologist access required TOTP MFA (enforced per DB `requires_mfa`).

Source: `/tmp/opencode/p5_dashboard_catalog.json` (live capture).
