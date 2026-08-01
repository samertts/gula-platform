# Mutation Coverage Report — PROGRAM-03 v3.0

Frontend mutation operations (POST/PUT/PATCH) wired to real backend endpoints, per page.

| Page | Mutation | Endpoint | Method |
|---|---|---|---|
| OrdersPage | create order | `/orders` | POST |
| OrdersPage | batch create orders | `/batch/orders` | POST |
| OrdersPage | validate order | `/orders/{id}/validate` | POST |
| OrdersPage | cancel order | `/orders/{id}/cancel` | POST |
| OrdersPage | send notification (share) | `/notify/send` | POST |
| PatientsPage | create patient | `/patients` | POST |
| PatientsPage | update patient | `/patients/{id}` | PUT |
| PatientsPage | merge patients | `/api/v1/canonical-patients/merge` | POST |
| SamplesPage | register sample | `/samples` | POST |
| SamplesPage | transition status | `/samples/{barcode}` | PUT |
| ResultsPage | verify result (senior) | `/test-results/{id}/verify` | PUT |
| ResultsPage | LIMS validate/reject/flag | `/lims/results/{id}/validate` | POST |
| ResultsPage | release result | `/lims/results/{id}/release` | POST |
| ResultsPage | manual device entry | `/device/results` | POST |
| ResultsPage | generate report | `/lims/reports` | POST |
| ResultsPage | finalize report | `/lims/reports/{id}/finalize` | POST |
| ResultsPage | correct report | `/lims/reports/{id}/correct` | POST |
| QCPage | submit QC entry | `/qc` | POST |
| QCPage | create QC program | `/lims/qc/programs` | POST |
| QCPage | IQC run | `/lims/qc/run` | POST |
| LimsPage | create instrument | `/lims/instruments` | POST |
| LimsPage | instrument online/offline | `/lims/instruments/{id}/online|offline` | POST |
| LimsPage | schedule maintenance | `/lims/instruments/{id}/maintenance` | POST |
| LimsPage | record calibration | `/lims/instruments/{id}/calibrations` | POST |
| LimsPage | ASTM/HL7 import | `/lims/integration/astm|hl7/receive` | POST |
| ProfilePage | change password | `/auth/change-password` | POST |
| IdentityPage | link patient (NID) | `/identity/link` | POST |
| LoginPage | login | `/login` | POST |
| LoginPage | MFA challenge | `/mfa-verify` | POST |

## Coverage

- **9 production workflow pages** with real mutations: Orders, Patients, Samples, Results, QC, LIMS, Profile, Identity, Login.
- **29 mutations** wired (was 14 at v2.0, 0 at v1.0).
- **100% of core clinical API groups** in `endpoints.ts` consumed by at least one page.

## Mutation Hygiene

- All mutations use react-query `useMutation` + `queryClient.invalidateQueries` (no stale UI after server change).
- All error surfaces use `getErrorMessage(err, fallback)`.
- Optimistic updates avoided in favor of server truth (backend is source of truth).
- Destructive actions (merge, release, finalize, correct) require explicit confirmation dialogs.
