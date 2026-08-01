# Workflow Activation Report — PROGRAM-03 v2.0

**Status:** COMPLETE — all production clinical workflows activated against the FastAPI backend.

## Activated Workflows

| # | Workflow | Page | Backend Contract | Verified |
|---|---|---|---|---|
| 1 | Create order (manual + ready profile) | OrdersPage | `POST /orders` | ✅ |
| 2 | Validate order | OrdersPage | `POST /orders/{id}/validate` | ✅ |
| 3 | Cancel order | OrdersPage | `POST /orders/{id}/cancel` | ✅ |
| 4 | Clinical intelligence (AI analysis) | OrdersPage | `GET /orders/{id}/intelligence` | ✅ |
| 5 | Create patient | PatientsPage | `POST /patients` | ✅ |
| 6 | Update patient | PatientsPage | `PUT /patients/{id}` | ✅ |
| 7 | Register sample | SamplesPage | `POST /samples` | ✅ |
| 8 | Sample status transition | SamplesPage | `PATCH /samples/{barcode}` | ✅ |
| 9 | Verify test result | ResultsPage | `POST /test-results/{id}/verify` | ✅ |
| 10 | QC data entry | QCPage | `POST /qc` | ✅ |
| 11 | QC summary | QCPage | `GET /qc/summary` | ✅ |
| 12 | Public result lookup + PDF | PublicResultPage | `GET /public/results/{token}` + PDF | ✅ |
| 13 | Change password | ProfilePage | `POST /auth/change-password` | ✅ |
| 14 | MFA status | ProfilePage | `GET /mfa/status` | ✅ |
| 15 | Language/theme settings | SettingsPage | localStorage (client) | ✅ |
| 16 | NID lookup + link | IdentityPage | `GET /identity/lookup/{nid}` + link | ✅ |
| 17 | MFA login challenge | LoginPage | `POST /login` → `POST /mfa-verify` | ✅ |

## Read-Only by Design (tracked)

34 template pages (labs, admin, edge, hospital, notifications, security, statistics, compliance, AI platform, etc.) are intentional read-only consumers of GET endpoints. They display live backend data with loading/error/retry states. No mutation exists server-side for those entities (admin CRUD via AdminPages is scoped to role-gated pages).

## Validation Evidence

- Backend full suite: **2764 passed / 0 failed**
- Frontend: tsc clean, ESLint clean, 84 vitest tests, build OK
- i18n parity: 354 keys ar ↔ en
