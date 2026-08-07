# Frontend Catalog

> GULA frontend-v3 — React SPA (Arabic-first, RTL). Read-only discovery, PROGRAM-02.

_Generated 2026-08-01. Pages: 78 files / 49 directories. Routes: 85 (77 guarded). Components: 14. API calls: 567 (57 groups)._

## 1. Tech stack

| Layer | Choice |
|---|---|
| Framework | React 18 + Vite + TypeScript |
| Routing | react-router-dom (createBrowserRouter, lazy + Suspense) |
| Server state | @tanstack/react-query (retry:1, staleTime:30s, gcTime:10min) |
| Client state | 3 React contexts: AuthContext, LocaleContext, ThemeContext |
| HTTP | axios (base `VITE_API_BASE_URL` ?? `/api`; 401 single-flight refresh) |
| Tables | @tanstack/react-table (DataTable wrapper) |
| Styling | Tailwind CSS v4 (oklch tokens, dark variant) |
| i18n | i18next, ar + en (240 keys each) |
| Icons | lucide-react |
| Tests | vitest + testing-library (54 unit tests: utils, useDebounce, useToast, ui components, DataTable) |
| Validation | none |

## 2. Routes (85, all under /login + protected dashboard layout)

| Path | Component | Guard | Roles |
|---|---|---|---|
| `/*` | NAV | — | — |
| `/admin` | NAV | — | — |
| `/admin/audit` | AdminAuditPage | RoleGuard | adminRoles |
| `/admin/control` | AdminControlPage | RoleGuard | adminRoles |
| `/admin/labs` | AdminLabsPage | RoleGuard | adminRoles |
| `/admin/pending-labs` | AdminPendingLabsPage | RoleGuard | adminRoles |
| `/admin/users` | AdminUsersPage | RoleGuard | adminRoles |
| `/ai` | AIPage | RoleGuard | readonlyRoles |
| `/ai-fabric` | AiFabricPageLazy | RoleGuard | adminRoles |
| `/ai-platform` | AiPlatformPage | RoleGuard | readonlyRoles |
| `/alerts` | CriticalAlertsPage | RoleGuard | readonlyRoles |
| `/biomedical` | BiomedicalApiPageLazy | RoleGuard | adminRoles |
| `/blood-bank` | BloodBankApiPageLazy | RoleGuard | adminRoles |
| `/capabilities/clinical-foundation` | CapabilitiesClinicalFoundationPageLazy | RoleGuard | readonlyRoles |
| `/capabilities/document-management` | CapabilitiesDocumentManagementPageLazy | RoleGuard | readonlyRoles |
| `/capabilities/encounter-management` | CapabilitiesEncounterManagementPageLazy | RoleGuard | readonlyRoles |
| `/capabilities/healthcare-consent` | CapabilitiesHealthcareConsentPageLazy | RoleGuard | readonlyRoles |
| `/capabilities/provider-management` | CapabilitiesProviderManagementPageLazy | RoleGuard | readonlyRoles |
| `/capabilities/reporting-service` | CapabilitiesReportingServicePageLazy | RoleGuard | readonlyRoles |
| `/capabilities/search-service` | CapabilitiesSearchServicePageLazy | RoleGuard | readonlyRoles |
| `/capabilities/storage-service` | CapabilitiesStorageServicePageLazy | RoleGuard | readonlyRoles |
| `/capabilities/workflow-engine` | CapabilitiesWorkflowEnginePageLazy | RoleGuard | readonlyRoles |
| `/certification` | CertificationPageLazy | RoleGuard | adminRoles |
| `/citizen-platform` | CitizenPlatformPageLazy | RoleGuard | adminRoles |
| `/command-center` | CommandCenterApiPageLazy | RoleGuard | adminRoles |
| `/command-intelligence` | CommandIntelligencePageLazy | RoleGuard | adminRoles |
| `/compliance` | CompliancePage | RoleGuard | adminRoles |
| `/control-plane` | ControlPlanePageLazy | RoleGuard | adminRoles |
| `/critical-care` | CriticalCareApiPageLazy | RoleGuard | adminRoles |
| `/dashboard` | DashboardPage | — | — |
| `/edge` | EdgePage | RoleGuard | ['master_admin', 'admin'] |
| `/ehr` | EhrPage | RoleGuard | adminRoles |
| `/ems` | EmsApiPageLazy | RoleGuard | adminRoles |
| `/fhir` | FhirPage | RoleGuard | adminRoles |
| `/fhir/explorer` | FhirExplorerPage | RoleGuard | adminRoles |
| `/fhir/observations` | FhirObservationPage | RoleGuard | adminRoles |
| `/fhir/patients` | FhirPatientPage | RoleGuard | adminRoles |
| `/fhir/reports` | FhirReportPage | RoleGuard | adminRoles |
| `/financial` | FinancialPage | RoleGuard | adminRoles |
| `/health-data` | HealthDataPageLazy | RoleGuard | adminRoles |
| `/hospital` | HospitalPage | RoleGuard | adminRoles |
| `/identity` | IdentityPage | RoleGuard | staffRoles |
| `/integration` | IntegrationPageLazy | RoleGuard | adminRoles |
| `/integration/connectors` | IntegrationConnectorsPageLazy | RoleGuard | adminRoles |
| `/kernel` | KernelPageLazy | RoleGuard | adminRoles |
| `/labs` | LabsPage | RoleGuard | readonlyRoles |
| `/lifecycle-platform` | LifecyclePlatformApiPageLazy | RoleGuard | adminRoles |
| `/login` | LoginPage | — | — |
| `/national-data` | NationalDataPage | RoleGuard | ['master_admin', 'ministry_admin', 'province_admin'] |
| `/national/background-platform` | NationalBackgroundPlatformApiPageLazy | RoleGuard | adminRoles |
| `/national/document-platform` | NationalDocumentPlatformApiPageLazy | RoleGuard | adminRoles |
| `/national/ecosystem` | NationalEcosystemPageLazy | RoleGuard | adminRoles |
| `/national/ecosystem/gateway` | NationalEcosystemGatewayPageLazy | RoleGuard | adminRoles |
| `/national/notification-platform` | NationalNotificationPlatformApiPageLazy | RoleGuard | adminRoles |
| `/national/observability` | NationalObservabilityApiPageLazy | RoleGuard | adminRoles |
| `/national/rules-engine` | NationalRulesEngineApiPageLazy | RoleGuard | adminRoles |
| `/national/scheduling-platform` | NationalSchedulingPlatformApiPageLazy | RoleGuard | adminRoles |
| `/national/search-platform` | NationalSearchPlatformApiPageLazy | RoleGuard | adminRoles |
| `/national/task-engine` | NationalTaskEngineApiPageLazy | RoleGuard | adminRoles |
| `/niam/adaptive-auth` | NiamAdaptiveAuthPage | RoleGuard | adminRoles |
| `/niam/certificates` | NiamCertificatesPage | RoleGuard | adminRoles |
| `/niam/federation` | NiamFederationPage | RoleGuard | adminRoles |
| `/niam/governance` | NiamGovernancePage | RoleGuard | adminRoles |
| `/niam/lifecycle` | NiamLifecyclePage | RoleGuard | adminRoles |
| `/niam/trust` | NiamTrustPage | RoleGuard | adminRoles |
| `/niam/workflows` | NiamWorkflowsPage | RoleGuard | adminRoles |
| `/notifications` | NotificationsPage | — | — |
| `/ops-metrics` | OpsMetricsPageLazy | RoleGuard | adminRoles |
| `/orders` | OrdersPage | RoleGuard | staffRoles |
| `/patient-card` | PatientCardPage | RoleGuard | staffRoles |
| `/patients` | PatientsPage | RoleGuard | staffRoles |
| `/pharmacy` | PharmacyPageLazy | RoleGuard | adminRoles |
| `/pilot-platform` | PilotPlatformApiPageLazy | RoleGuard | adminRoles |
| `/platform` | PlatformPageLazy | RoleGuard | adminRoles |
| `/profile` | ProfilePage | — | — |
| `/public-health` | PublicHealthApiPageLazy | RoleGuard | adminRoles |
| `/qc` | QCPage | RoleGuard | readonlyRoles |
| `/react-router-dom` | ? | — | — |
| `/results` | ResultsPage | RoleGuard | staffRoles |
| `/samples` | SamplesPage | RoleGuard | labRoles |
| `/security` | SecurityPage | RoleGuard | adminRoles |
| `/settings` | SettingsPage | — | — |
| `/stats` | StatsPage | RoleGuard | readonlyRoles |
| `/tiers` | TiersPage | RoleGuard | readonlyRoles |

## 3. Pages by classification

| Classification | Count |
|---|---|
| CONNECTED | 70 |
| PRODUCTION-READY | 4 |
| DISCONNECTED | 3 |
| PARTIALLY-CONNECTED | 1 |

## 4. Components (14 files)

| Component | Lines | API |
|---|---|---|
| `components/__tests__/DataTable.test.tsx` | 40 | — |
| `components/__tests__/ui-components.test.tsx` | 198 | — |
| `components/auth/RoleGuard.tsx` | 25 | — |
| `components/shared/PageComponents.tsx` | 77 | — |
| `components/shared/ToastContainer.tsx` | 42 | — |
| `components/ui/Badge.tsx` | 30 | — |
| `components/ui/Button.tsx` | 51 | — |
| `components/ui/Card.tsx` | 34 | — |
| `components/ui/DataTable.tsx` | 160 | — |
| `components/ui/Dialog.tsx` | 63 | — |
| `components/ui/Input.tsx` | 27 | — |
| `components/ui/Select.tsx` | 35 | — |
| `components/ui/Textarea.tsx` | 26 | — |
| `components/ui/index.ts` | 8 | — |

## 5. Hooks & contexts

- `hooks/useDebounce.ts` (10 lines): useDebounce
- `hooks/useToast.ts` (42 lines): toast, useToast

- `contexts/AuthContext.tsx` (62 lines): AuthProvider, useAuth
- `contexts/LocaleContext.tsx` (46 lines): LocaleProvider, useLocale
- `contexts/ThemeContext.tsx` (57 lines): ThemeProvider, useTheme

## 6. Quality summary

| Dimension | Status |
|---|---|
| Loading states | 17/78 explicit spinners; DataTable has built-in loading |
| Empty states | 10/78 explicit EmptyState |
| Error + retry | 19/78 explicit ErrorDisplay; 52/78 rely on DataTable 'no data' on failure |
| Validation | none (no library; unused error prop + validation namespace) |
| Accessibility | 1 aria attribute repo-wide; no dialog semantics; no aria-live; no a11y tests |
| RTL | dir=rtl on html; 241 logical props; 31 `rounded-l` LTR residue |
| Dark mode | ThemeContext + .dark class + full oklch token set |
| Responsive | md: 32, lg: 20 usages; NO mobile nav (fixed w-64 sidebar) |
| i18n | 8/78 pages use useTranslation; 70 hardcode Arabic |
| Error boundary | none; no global handler |
| Navigation | 73 sidebar items, 10 groups; every sidebar path has a route |

## 7. Key findings

- Entire write-side of the lab domain is absent: no page calls order create/validate/cancel, result create/verify, sample create/update, QC submit, batch orders, or device result submission - all core lab pages are searchable read-only tables.
- 10 of 22 backend workflows have NO frontend UI at all (device ingestion, public result links, referrals, care continuum community, consent, claims, MPI, streaming ingestion, identity governance, offline sync).
- 0/22 workflows are complete in the UI; 12/22 interrupted.
- Registration is impossible from the UI: register endpoints defined, zero forms.
- No MFA challenge at login although backend denies privileged roles without enrolled MFA.
- Citizen role lands on the lab KPI dashboard (wrong content); no citizen self-service UI in v3.
- Technician role effectively unusable: ~30 menu items render but routes bounce (excluded from labRoles and readonlyRoles).
- Menu (permission-based) and routes (role-based) gating drift: national-data, national/*, samples, hospital, security menus visible for roles whose routes deny access.
- 70/78 pages hardcode Arabic; en.ts (240 keys) effectively unused; only 8 pages use i18n.
- No client-side validation library; unused Input/Select error prop; unused validation i18n namespace.
- Accessibility: 1 aria attribute in entire app; Dialog has no role/aria-modal/focus trap; no aria-live on toasts; no a11y tests.
- No ErrorBoundary, no global error handler; render errors crash the app.
- 52/78 pages have no error/retry UI - API failures display 'no data'.
- No pagination anywhere (all lists cap at limit:50); search is not sent to API on Results and Samples pages (query-key bug).
- No mobile navigation: fixed w-64 sidebar, no drawer; unusable below ~640px.
- Dead buttons: labs '+ add lab', admin '+ add lab/user', profile 'edit', tiers 'upgrade'.
- 28 of 54 sidebar icons fall back to a generic icon (iconMap covers 29).
- EHR page is a misnomer: /ehr implements a lab orders/results timeline viewer; the real EHR workflow has no UI (35 ehrApi endpoints unused).
- IntegrationConnectorsPage calls /integration/connectors//health (double slash).
- 18 financialApi calls target a dormant backend module not registered in factory.py - all 5 used calls will 500/404 at runtime.
- 35 'ApiPage' template pages (biomedical, blood-bank, national/*, capabilities/*, etc.) are read-only GET tables with no mutations, forms, search, pagination, or export.
- Two dead CSS files (App.css, theme.css) with RTL chevron fixes never imported.
- Generated src/api/generated client (openapi) is not imported anywhere.
- receptionist role exists in types/permissions but is dead in routes/menus.
