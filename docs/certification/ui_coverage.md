# UI / Frontend Coverage Certification — PROGRAM-06

> Generated: 2026-08-02

## Page inventory — production surface (all routed + guarded + i18n)

| Area | Pages | Status |
|---|---|---|
| Auth | LoginPage, PublicResultPage `/r/:token` | ✅ |
| Core workflows | Dashboard, Patients, Orders, Samples, Results, QC, LIMS | ✅ |
| Platform | Labs, Tiers, PatientCard, Alerts, Stats, Notifications, Identity (MFA + service accounts), Profile, Settings, Security, Compliance | ✅ |
| Admin | AdminLabs, AdminUsers, AdminAudit, AdminPendingLabs, AdminControl | ✅ |
| FHIR/EHR | FhirPage + Explorer/Patient/Observation/Report, EhrPage | ✅ |
| AI | AIPage, AiPlatformPage, AiFabricPage | ✅ |
| Enterprise | Hospital, Edge, Financial (dormant), NationalData, Integration + connectors | ✅ |
| NIAM | Governance, Trust, Lifecycle, Federation, Certificates, Workflows, AdaptiveAuth | ✅ |
| National | background/document/ecosystem(+gateway)/notification/observability/rules/scheduling/search/task platforms, OpsMetrics | ✅ |
| Capabilities | clinical-foundation, document-management, encounter-management, healthcare-consent, provider-management, reporting-service, search-service, storage-service, workflow-engine | ✅ |
| Systems (dormant gated) | ai-fabric, biomedical, blood-bank, certification, citizen-platform, command-center, command-intelligence, control-plane, critical-care, ems, health-data, kernel, lifecycle-platform, pharmacy, pilot-platform, platform, public-health | ✅ routed |

## Quality indicators (this certification run)

| Check | Result |
|---|---|
| Production build (vite) | ✅ PASS (~5.9 s) |
| `tsc --noEmit` | ✅ 0 errors |
| ESLint (`--max-warnings 0`) | ✅ 0 errors |
| Vitest | ✅ 122/122 pass (9 files) |
| Lazy loading | ✅ all pages lazy + Suspense |
| RTL/Arabic-first | ✅ `dir=rtl`, i18n 399 keys ar↔en identical |
| Error boundary | ✅ global ErrorBoundary + toast system |
| API client | ✅ axios with token refresh, 401 retry, timeout, error normalization (now Arabic-first `detail_ar`) |
| UI components | ✅ shared component library (Card, Button, Badge, Dialog, Table, Input, …) |

## Type coverage

- Backend 26 SQLAlchemy models → all referenced by frontend types/pages (snake/camel aware scan).
- Frontend `types/` mirror backend Pydantic contracts (PaginatedResponse, DashboardData, LabOrder, …).

## Verdict

**UI/FRONTEND COVERAGE: production surface fully routed, guarded, translated, typed, and tested.**
