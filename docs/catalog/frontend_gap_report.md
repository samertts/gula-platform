# Frontend Gap Report

> PROGRAM-02 — definitive frontend↔backend gap analysis (read-only).

## 1. Summary metrics

| Metric | Value |
|---|---|
| page files | 78 |
| page directories | 49 |
| routes | 85 |
| routes guarded | 77 |
| components | 14 |
| hooks | 2 |
| contexts | 3 |
| layouts | 3 |
| api groups | 57 |
| api calls total | 567 |
| api calls resolve to backend | 344 |
| api call resolution pct | 60.7 |
| backend routes connected | 553 |
| backend routes not connected | 1431 |
| backend routes internal | 2 |
| backend route coverage pct | 27.8 |
| classification counts | {'CONNECTED': 70, 'PARTIALLY-CONNECTED': 1, 'PRODUCTION-READY': 4, 'DISCONNECTED': 3} |
| firebase dependencies | 0 |
| mock files | 0 |
| i18n keys | 240 |
| pages using i18n | 8 |

## 2. Page classification

| Classification | Count | Files |
|---|---|---|
| PRODUCTION-READY | 4 | pages/edge/EdgePage.tsx, pages/hospital/HospitalPage.tsx, pages/notifications/NotificationsPage.tsx, pages/security/SecurityPage.tsx |
| CONNECTED | 69 | pages/admin/AdminPages.tsx, pages/ai-fabric/AiFabricPage.tsx, pages/ai-platform/AiPlatformPage.tsx, pages/alerts/CriticalAlertsPage.tsx, pages/auth/LoginPage.tsx, pages/biomedical/BiomedicalApiPage.tsx, pages/blood-bank/BloodBankApiPage.tsx, pages/capabilities/clinical-foundation/CapabilitiesClinicalFoundationPage.tsx, pages/capabilities/document-management/CapabilitiesDocumentManagementPage.tsx, pages/capabilities/encounter-management/CapabilitiesEncounterManagementPage.tsx, pages/capabilities/healthcare-consent/CapabilitiesHealthcareConsentPage.tsx, pages/capabilities/provider-management/CapabilitiesProviderManagementPage.tsx, pages/capabilities/reporting-service/CapabilitiesReportingServicePage.tsx, pages/capabilities/search-service/CapabilitiesSearchServicePage.tsx, pages/capabilities/storage-service/CapabilitiesStorageServicePage.tsx, pages/capabilities/workflow-engine/CapabilitiesWorkflowEnginePage.tsx, pages/certification/CertificationPage.tsx, pages/citizen-platform/CitizenPlatformPage.tsx, pages/command-center/CommandCenterApiPage.tsx, pages/command-intelligence/CommandIntelligencePage.tsx, pages/compliance/CompliancePage.tsx, pages/control-plane/ControlPlanePage.tsx, pages/critical-care/CriticalCareApiPage.tsx, pages/dashboard/DashboardPage.tsx, pages/ehr/EhrPage.tsx, pages/ems/EmsApiPage.tsx, pages/fhir/FhirExplorerPage.tsx, pages/fhir/FhirObservationPage.tsx, pages/fhir/FhirPage.tsx, pages/fhir/FhirPatientPage.tsx, pages/fhir/FhirReportPage.tsx, pages/financial/FinancialPage.tsx, pages/health-data/HealthDataPage.tsx, pages/integration/IntegrationPage.tsx, pages/integration/connectors/IntegrationConnectorsPage.tsx, pages/kernel/KernelPage.tsx, pages/labs/LabsPage.tsx, pages/lifecycle-platform/LifecyclePlatformApiPage.tsx, pages/national/background-platform/NationalBackgroundPlatformApiPage.tsx, pages/national/document-platform/NationalDocumentPlatformApiPage.tsx, pages/national/ecosystem/NationalEcosystemPage.tsx, pages/national/ecosystem/gateway/NationalEcosystemGatewayPage.tsx, pages/national/notification-platform/NationalNotificationPlatformApiPage.tsx, pages/national/observability/NationalObservabilityApiPage.tsx, pages/national/rules-engine/NationalRulesEngineApiPage.tsx, pages/national/scheduling-platform/NationalSchedulingPlatformApiPage.tsx, pages/national/search-platform/NationalSearchPlatformApiPage.tsx, pages/national/task-engine/NationalTaskEngineApiPage.tsx, pages/national-data/NationalDataPage.tsx, pages/niam/AdaptiveAuthPage.tsx, pages/niam/CertificatesPage.tsx, pages/niam/FederationPage.tsx, pages/niam/GovernancePage.tsx, pages/niam/LifecyclePage.tsx, pages/niam/TrustPage.tsx, pages/niam/WorkflowsPage.tsx, pages/ops-metrics/OpsMetricsPage.tsx, pages/orders/OrdersPage.tsx, pages/patient-card/PatientCardPage.tsx, pages/patients/PatientsPage.tsx, pages/pharmacy/PharmacyPage.tsx, pages/pilot-platform/PilotPlatformApiPage.tsx, pages/platform/PlatformPage.tsx, pages/public-health/PublicHealthApiPage.tsx, pages/qc/QCPage.tsx, pages/results/ResultsPage.tsx, pages/samples/SamplesPage.tsx, pages/stats/StatsPage.tsx, pages/tiers/TiersPage.tsx |
| PARTIALLY-CONNECTED | 1 | pages/ai/AIPage.tsx |
| DISCONNECTED | 3 | pages/identity/IdentityPage.tsx, pages/profile/ProfilePage.tsx, pages/settings/SettingsPage.tsx |
| PLACEHOLDER | 0 | — |
| MOCK | 0 | — |

## 3. Missing pages / features

| Missing | Detail |
|---|---|
| Order creation form | orders page is read-only; no create/edit/validate/cancel |
| Sample registration + status transitions | no collected→received→processing→analyzed UI |
| Device (analyzer) results submission | deviceApi.submitResults unused |
| Result entry + verify/validate actions | resultsApi.verify/validate unused |
| Public result page /r/:token + PDF | publicResultsApi/qrApi unused; no SPA route |
| QC control data entry + batch + summary | qcApi.submit/submitBatch/summary unused |
| Referral workflow UI (create/inbox/timeline) | careContinuumApi referral methods unused |
| EHR clinical records CRUD | 35 ehrApi endpoints unused; /ehr page is a lab timeline |
| Care continuum community UI | 60 careContinuumApi endpoints unused |
| Registration forms (lab/citizen/staff/doctor) | authApi.register* unused |
| MFA challenge step at login + WebAuthn enrollment | mfaApi.webauthn* unused |
| Consent grant/revoke screens | consentApi unused |
| Claims creation/validate/submit UI | claimsApi + insuranceApi unused |
| FHIR resource create/edit + batch import | ehrFhirApi unused |
| MPI resolve/merge/pending-review UI | canonicalPatientApi unused |
| Streaming ingestion UI (FHIR/HL7 push) | nationalStreamingApi unused |
| Offline sync / conflict resolution UI | integrationsApi unused |
| National notification template editor + batch send | national notification page read-only |
| Missing CRUD everywhere: no page has create/edit for core entities | all core lists read-only |
| Missing dashboards: no role-aware dashboard (ministry/province/citizen variants) | single lab KPI dashboard |
| Missing reports: no chart anywhere (0 recharts usage) | stats page is tables only |
| Missing navigation for technician/ministry/province (menu-route drift) | ~30 dead menu items for technician |
| Missing search/filter/pagination: search not sent to API (results, samples); no pagination anywhere | all lists cap at 50 |
| Missing export: no CSV/PDF export button anywhere in UI | backend export endpoints exist |
| Missing print: only patient-card has print link | no print buttons |
| Missing validation: zero client-side validation | no zod/yup |
| Missing error handling: 52/78 pages show 'no data' on API failure | no ErrorBoundary |
| Missing citizen self-service portal | citizen role lands on lab dashboard |

## 4. Quality gaps

- Loading: 17/78 explicit spinners (DataTable covers most lists)
- Empty states: 10/78 explicit
- Error/retry: 19/78 explicit; 52/78 silently show 'no data'
- Validation: none
- Accessibility: 1 aria attribute; no dialog semantics; no focus trap; no aria-live; no a11y tests
- RTL: mostly logical props but 31 `rounded-l` + 8 other LTR residues
- Dark mode: complete (oklch tokens + .dark)
- Responsive: no mobile nav; fixed w-64 sidebar; fixed-width search inputs
- i18n: 70/78 hardcode Arabic; en.ts unused
- Error boundary: none
- Authorization: dual gating (menu permissions vs route roles) drifts; technician/ministry/province broken

## 5. Dead code / bugs

- Dead buttons: labs '+ add lab', admin '+ add lab/user', profile 'edit', tiers 'upgrade'
- IntegrationConnectorsPage double-slash path /integration/connectors//health
- ResultsPage + SamplesPage: search state in query key but not sent to API
- 28/54 sidebar icons fall back to LayoutDashboard
- Two dead CSS files (App.css, theme.css) never imported
- Generated OpenAPI client (src/api/generated) unused
- mobileApi path drift: /auth/refresh vs authApi /auth/refresh-token
- financialApi calls dormant backend module (all 5 used calls fail at runtime)
