# Workflow Parity Certification — PROGRAM-06

> Generated: 2026-08-02 · Chain verification: Page → API client → Live backend route (+ auth dependency)

Every production workflow below was traced end-to-end. **All chains resolve; zero broken steps.**

## Production Workflows (all operational)

| # | Workflow | Frontend page | API client | Backend routes | Status |
|---|---|---|---|---|---|
| 1 | Login + privileged MFA | `LoginPage` | `authApi.login/mfaVerify` | `POST /login` → `mfa_pending` → `POST /mfa-verify` | ✅ complete |
| 2 | Patient registration | `PatientsPage` | `patientsApi` (list/create/get/update/delete) | `/patients` GET/POST, `PUT /patients/{id}`, family, children | ✅ complete |
| 3 | Clinical order entry | `OrdersPage` | `ordersApi` (+`batchApi`, `notificationsApi`) | `/orders` GET/POST, GET/POST `/{id}/validate`, `/{id}/cancel`, `/orders/{id}/intelligence`, `/test-profiles` | ✅ complete |
| 4 | Sample collection & reception | `SamplesPage` | `samplesApi` | `/samples` GET/POST, PUT `/{id}`, POST `/{id}/status` | ✅ complete |
| 5 | Analyzer queue & instrument integration | `LimsPage` | `limsApi` | `/lims/results`, `/lims/instruments` + lifecycle (online/offline/maintenance/calibrations), `/lims/integration/astm/receive`, `/lims/integration/hl7/receive` | ✅ complete |
| 6 | QC (Westgard multi-rule) | `QCPage` | `qcApi`, `limsApi.qc*` | `/qc`, `/qc/summary`, `/qc/batch`, `/lims/qc/run|programs|results|statistics` | ✅ complete |
| 7 | Result entry & verification | `ResultsPage` | `resultsApi` | `/test-results` GET/POST, `PUT /test-results/{id}/verify` (require_verify_authority), `/test-results/validate` | ✅ complete |
| 8 | Clinical sign-off & release | `ResultsPage`/`LimsPage` | `limsApi.releaseResult` | `POST /lims/results/{id}/release` | ✅ complete |
| 9 | Printing / public result | `PublicResultPage` `/r/:token` | — (URL) | `GET /r/{token}`, `GET /r/{token}/pdf` (PDF report) | ✅ complete |
| 10 | Notifications | `NotificationsPage` | `notificationsApi` | `POST /notify/send`, `GET /notify/history/{id}` | ✅ complete |
| 11 | Reports | `LimsPage` | `limsApi` reports | `/lims/reports` GET/POST, `/{id}/finalize`, `/{id}/correct` | ✅ complete |
| 12 | Audit trail | `AdminAuditPage` | `adminApi.auditLogs` | `GET /admin/audit-logs` | ✅ complete |
| 13 | MFA device management | `ProfilePage`/`IdentityPage` | `mfaApi` | `/mfa/totp/setup|verify`, `/mfa/webauthn/register|authenticate/*`, `/mfa/devices` GET/DELETE, `/mfa/status` | ✅ complete |
| 14 | Service accounts | `IdentityPage` | `serviceAccountsApi` | `/service-accounts` GET/POST, DELETE `/{id}`, POST `/{id}/rotate` | ✅ complete |

## Workflow safety controls (verified present)

- **MFA challenge** enforced for privileged roles (ASVS 2.4): single-use `mfa_session`, rate-limited
  `POST /mfa-verify` (bootstrap exception for first admin only).
- **Verification authority**: `PUT /test-results/{id}/verify` guarded by `require_verify_authority`.
- **Rate limiting** per user on all write routes (`rate_limit_user`, 30–120 req/min by operation).
- **Audit logging**: `log_action` on every state-changing step (login, order, sample, result,
  verification, release, QC, admin actions).
- **Idempotency/outbox** available in service layer (P4 verified).

## E2E coverage (Playwright)

| Spec | Covers |
|---|---|
| `e2e/auth.spec.ts` | login, MFA, logout |
| `e2e/orders.spec.ts` | order create/list/validate |
| `e2e/patients.spec.ts` | patient create/list |
| `e2e/results.spec.ts` | result entry/verification |
| `e2e/samples.spec.ts` | sample create/status |
| `e2e/fhir.spec.ts` | FHIR explorer |
| `e2e/navigation.spec.ts` | menu/route integrity |

## Verdict

**WORKFLOW PARITY: 14/14 production workflows complete — every step has page, client, and live route.**
