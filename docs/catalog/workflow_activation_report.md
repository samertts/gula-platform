# Workflow Activation Report — PROGRAM-03 v3.0

**Status:** COMPLETE — all production clinical workflows activated against the FastAPI backend. No read-only viewers remain for backend-backed entities; every backend capability exposed in the UI.

## Activated Workflows

| # | Workflow | Page | Backend Contract | Verified |
|---|---|---|---|---|
| 1 | Create order (manual) | OrdersPage | `POST /orders` | ✅ |
| 2 | Batch create orders (bulk intake) | OrdersPage | `POST /batch/orders` | ✅ |
| 3 | Validate order | OrdersPage | `POST /orders/{id}/validate` | ✅ |
| 4 | Cancel order | OrdersPage | `POST /orders/{id}/cancel` | ✅ |
| 5 | Order timeline + notify history | OrdersPage | `GET /orders/{id}`, `GET /notify/history/{id}` | ✅ |
| 6 | Send result notification (share) | OrdersPage | `POST /notify/send` | ✅ |
| 7 | Create patient | PatientsPage | `POST /patients` | ✅ |
| 8 | Update patient | PatientsPage | `PUT /patients/{id}` | ✅ |
| 9 | Merge patients (canonical) | PatientsPage | `POST /api/v1/canonical-patients/merge` | ✅ |
| 10 | Patient history drawer | PatientsPage | `GET /patient-history/{id}` | ✅ |
| 11 | Result timeline | PatientsPage | `GET /test-results/citizen/{health_id}/timeline` | ✅ |
| 12 | Family / children lookup | PatientsPage | `GET /patients/{id}/children` | ✅ |
| 13 | QR card download | PatientsPage | `GET /patient-card/{id}/qr.png` | ✅ |
| 14 | Patient card print | PatientsPage | `GET /patient-card/{id}/print` | ✅ |
| 15 | Register sample | SamplesPage | `POST /samples` | ✅ |
| 16 | Sample status transition | SamplesPage | `PUT /samples/{barcode}` | ✅ |
| 17 | Barcode copy quick action | SamplesPage | clipboard (client) | ✅ |
| 18 | Verify test result (senior) | ResultsPage | `PUT /test-results/{id}/verify` | ✅ |
| 19 | LIMS validate / reject / flag | ResultsPage | `POST /lims/results/{id}/validate` | ✅ |
| 20 | LIMS release result | ResultsPage | `POST /lims/results/{id}/release` | ✅ |
| 21 | Manual result entry (analyzer/device) | ResultsPage | `POST /device/results` | ✅ |
| 22 | LIMS worklist by validation status | ResultsPage | `GET /lims/results?validation_status=` | ✅ |
| 23 | Generate lab report | ResultsPage | `POST /lims/reports` | ✅ |
| 24 | Finalize report (pathologist) | ResultsPage | `POST /lims/reports/{id}/finalize` | ✅ |
| 25 | Correct report | ResultsPage | `POST /lims/reports/{id}/correct` | ✅ |
| 26 | Print + CSV export | ResultsPage | browser print / client-side CSV | ✅ |
| 27 | QC data entry (core) | QCPage | `POST /qc` | ✅ |
| 28 | QC summary | QCPage | `GET /qc/summary` | ✅ |
| 29 | LIMS QC programs CRUD | QCPage | `GET/POST /lims/qc/programs` | ✅ |
| 30 | IQC run | QCPage | `POST /lims/qc/run` | ✅ |
| 31 | LIMS QC results history | QCPage | `GET /lims/qc/results` | ✅ |
| 32 | Instrument CRUD | LimsPage | `GET/POST /lims/instruments` | ✅ |
| 33 | Analyzer online/offline queue | LimsPage | `POST /lims/instruments/{id}/online|offline` | ✅ |
| 34 | Maintenance scheduling | LimsPage | `POST /lims/instruments/{id}/maintenance` | ✅ |
| 35 | Calibration recording | LimsPage | `POST /lims/instruments/{id}/calibrations` | ✅ |
| 36 | ASTM / HL7 import | LimsPage | `POST /lims/integration/astm|hl7/receive` | ✅ |
| 37 | Specimen storage + temperature | LimsPage | `GET /lims/storage`, `POST /lims/storage/temperature` | ✅ |
| 38 | Public result lookup + PDF | PublicResultPage | `GET /r/{token}` + PDF | ✅ |
| 39 | MFA login challenge | LoginPage | `POST /login` → `POST /mfa-verify` | ✅ |
| 40 | NID lookup + link | IdentityPage | `GET /identity/lookup/{nid}` + link | ✅ |

## Previously Read-Only Pages Now Operational

- **ResultsPage** — was verify-only; now full LIMS lifecycle (validate/reject/flag/release, reports, manual device entry).
- **OrdersPage** — was single create; now batch intake + timeline + notify share.
- **PatientsPage** — was CRUD; now merge + history/timeline + children + QR.
- **QCPage** — was core entry; now LIMS programs + IQC runs + results history.
- **New `/lims` page** — instruments, import, storage (previously zero frontend for entire LIMS module).

## Read-Only by Design (tracked)

Dormant bounded-context template pages (edge, hospital, financial, national-data, etc.) remain intentionally read-only; their bounded contexts are not part of the core clinical workflow activation. MPI merge review (`/mpi/review`) deferred pending Postgres-backed MPI tables.

## Validation Evidence

- Backend full suite: **2764 passed / 0 failed** (489s)
- Frontend: tsc clean, ESLint max-warnings-0 clean, 84 vitest tests, vite build OK
- i18n parity maintained ar ↔ en (each key group added symmetrically)
