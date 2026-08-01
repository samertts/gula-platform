# Workflow Implementation Matrix — PROGRAM-03 v3.0 (Phase 1)

**Source of truth:** live backend route inventory (1766 routes) + frontend-v3 page/API inventory + PROGRAM-01/02 catalog reports.
**Method:** every production workflow requirement mapped to {backend capability, frontend exposure, gap, action}.

Legend: ✅ implemented · ◐ partial · ❌ missing · 🅱️ backend-ready (frontend gap) · ⚙️ backend extension required

## 1. Patient Domain

| Requirement | Backend | Frontend | Status | Action |
|---|---|---|---|---|
| Registration | `POST /patients` | PatientsPage dialog | ✅ | — |
| Update | `PUT /patients/{id}` | PatientsPage dialog | ✅ | — |
| Search | `GET /patients?search=` | search + debounce | ✅ | — |
| Merge (patients) | `POST /api/v1/canonical-patients/merge` | — | 🅱️ | Merge dialog in PatientsPage |
| Merge (citizens/MPI) | `POST /mpi/merge`, `GET /mpi/review`, `POST /mpi/review/{id}/decide`, `POST /mpi/resolve` | — | 🅱️ | MPI review tab (Phase 2b) |
| History | `GET /patient-history/{id}`, `GET /history/{phone}` | `patientHistoryApi` unused | 🅱️ | History drawer in PatientsPage |
| Timeline | `GET /test-results/citizen/{health_id}/timeline` | `resultsApi.citizenTimeline` unused | 🅱️ | Timeline view in history drawer |
| Family / children | `GET /patients/family/{id}`, `GET /patients/{id}/children` | `patientsApi` stubs unused | 🅱️ | Family tab in patient dialog |
| Documents | `document-management` CRUD | `capabilities/document-management` (template page) | ◐ | Operational docs panel |
| QR card | `GET /patient-card/{id}/qr.png`, `POST /patient-card/scan`, `GET /patient-card/{id}/history` | PatientCardPage (view/print) | ◐ | Add QR download + scan history |
| Audit | audit log endpoints (admin) | AdminPages | ✅ | — |

## 2. Order Domain

| Requirement | Backend | Frontend | Status | Action |
|---|---|---|---|---|
| Create | `POST /orders` | OrdersPage dialog | ✅ | — |
| Edit | `PUT /lims/orders/{id}/status`; no core `PUT /orders` | — | ⚙️ | Optional: status change via LIMS; edit not backend-supported (documented) |
| Approve | `POST /orders/{id}/validate` | OrdersPage | ✅ | — |
| Reject / Cancel | `POST /orders/{id}/cancel` | OrdersPage | ✅ | — |
| Priority | no priority field | — | ⚙️ | Optional additive column (deferred — not an activation) |
| Tracking | `GET /orders/{id}` status | detail dialog | ✅ | — |
| Bulk create | `POST /batch/orders` | `batchApi` unused | 🅱️ | Batch dialog in OrdersPage |
| Timeline | order statuses + audit log | — | ◐ | Order timeline in detail dialog |
| Audit | `log_action` audit trail | admin audit page | ✅ | — |

## 3. Specimen Domain

| Requirement | Backend | Frontend | Status | Action |
|---|---|---|---|---|
| Collection | `POST /samples` | SamplesPage register | ✅ | — |
| Barcode | samples carry `barcode` | table shows barcode | ✅ | Add copy/print action |
| Reception / Acceptance | status transition `received` | SamplesPage transitions | ✅ | — |
| Rejection | `rejected` + reason | SamplesPage | ✅ | — |
| Recollection | reject → new registration | possible via register | ✅ | Add "recollect" quick action |
| Tracking | status list | table + filters | ✅ | — |
| Storage / archive | `GET /lims/storage`, `POST /lims/storage/temperature`, `POST /archive/*` | — | 🅱️ | Storage panel (Phase 4b) |
| Recall | `POST /archive/preserve`, retention, purge-expired | — | 🅱️ | Archive actions |

## 4. Laboratory Domain

| Requirement | Backend | Frontend | Status | Action |
|---|---|---|---|---|
| Analyzer queue | `GET /lims/instruments` + online/offline | — | 🅱️ | Instruments page (queue) |
| Analyzer import | `POST /lims/integration/astm/receive`, `/hl7/receive`, `/simulate` | — | 🅱️ | ASTM/HL7 import panel |
| Device results | `POST /device/results` | `deviceApi` unused | 🅱️ | Manual/analyzer entry dialog on ResultsPage |
| Manual entry | `POST /lims/results`, `POST /test-results/` | `resultsApi.create` unused | 🅱️ | Manual entry dialog |
| QC submission | `POST /qc`, `POST /lims/qc/run` | QCPage (core) | ✅ | Add LIMS QC run/programs |
| QC review | `GET /lims/qc/results`, programs, statistics | — | 🅱️ | QC results history on QCPage |
| Validation | `POST /lims/results/{id}/validate` | — | 🅱️ | Validate action on ResultsPage |
| Senior validation | `POST /test-results/{id}/verify` (verify = senior) | ResultsPage verify | ✅ | — |
| Pathologist approval | `POST /lims/reports/{id}/finalize` | — | 🅱️ | Report finalize action |
| Release results | `POST /lims/results/{id}/release` | — | 🅱️ | Release action on ResultsPage |

## 5. Reporting

| Requirement | Backend | Frontend | Status | Action |
|---|---|---|---|---|
| PDF | `GET /r/{token}/pdf`; `POST /reporting-service/` | PublicResultPage PDF | ✅ | Add order/result PDF |
| Print | `GET /patient-card/{id}/print`; browser print | PatientCardPage, public page | ◐ | Print buttons on Orders/Results |
| Export | CSV client-side | — | ◐ | Export buttons |
| Share | `POST /notify/send` (+ history `GET /notify/history/{id}`) | `notificationsApi` unused | 🅱️ | Share/send dialog |
| History | `GET /lims/reports`, `GET /lims/reports/{id}` | — | 🅱️ | Reports history panel |
| Notifications | `GET /notifications/queue/{id}`, `POST .../read` | NotificationsPage read-only | ◐ | Mark-read action |
| Audit | `log_action` | admin audit | ✅ | — |

## 6. Write Operations Audit (Phase 7 pre-scan)

| Entity | Backend mutations | Frontend exposed |
|---|---|---|
| Patient | POST, PUT | ✅ |
| Canonical patient | POST, merge, link-patient, link-citizen | 🅱️ merge only |
| Order | POST, validate, cancel, batch | ◐ batch missing |
| Sample | POST, PUT status | ✅ |
| Result | POST, verify(PUT), validate(POST), LIMS validate/release | ◐ |
| QC | POST, batch, LIMS run | ◐ |
| Device | POST /device/results | 🅱️ |
| Notifications | send, queue read/sent/delivered | ◐ |
| LIMS instruments | POST, online, offline, maintenance, calibrations | 🅱️ |
| LIMS reports | POST, finalize, correct | 🅱️ |
| Archive | preserve, retention, check-integrity, purge-expired | 🅱️ |
| Document management | POST, PUT, DELETE | 🅱️ |

## Priority Order (clinical daily work)

1. **Results: validate + release + manual entry** (lab technicians/seniors daily work) — highest
2. **Orders: batch create** (receptionist bulk intake)
3. **Patients: merge + history/timeline drawer + family + QR download**
4. **QC: LIMS run + results history + programs**
5. **LIMS instruments page (analyzer queue + import)**
6. **Reporting: PDF/print/export + share/send + report finalize**
7. **Notifications: mark read**
8. **MPI merge review (Phase 2b, deferred)**

## Deferred (not activations — require new backend features, tracked)

- Order priority field (new column + schema) — ⚙️
- Core order edit (no `PUT /orders`) — ⚙️
- Sample storage UI panels (backend ready but low daily-use) — 🅱️ deferred
