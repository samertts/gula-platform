# CLINICAL WORKFLOW AUDIT — A03 (frontend-v3 pages)

**Program:** PROGRAM-GULA-PARALLEL-001 · **Wave:** A (READ-ONLY AUDIT)
**Agent:** A03 — Frontend Clinical Workflows
**Date:** 2026-11-19
**Reference project:** `frontend-v3` (sole FE reference)
**Scope:** `frontend-v3/src/pages/**` and page co-located tests.
**Companion report:** `docs/parallel-program/frontend/CLINICAL_WORKFLOW_REMEDIATION.md`
**Excluded by mandate:** all code writes; shared components/tokens/theme/config; routes/API endpoints (read-only evidence only); all git state changes; builds/tests/servers.

> Path convention: all `src/...` paths below are relative to `frontend-v3/`. Paths outside that tree are written in full.

---

## 0. Executive summary

Reviewed **97 `.ts/.tsx` files / 13,771 lines** under `frontend-v3/src/pages/`, including **3 co-located page tests**. No source, test, config, or git state was changed. No build, test runner, or server was executed.

**Counts:** 16 findings — **P0: 1 · P1: 10 · P2: 4 · P3: 1**. 5 SCOPE_REQUESTs are recorded in the companion remediation report.

The dominant risk is not a single broken page but a **boundary inconsistency**: some clinical reads are deliberately governed (`workspaceScopedReads`, `WorkspaceReadBlockedError`, `LegacyRouteBridge`, safe-empty states), while other routed pages render realistic clinical data through direct REST, raw numeric IDs, synthetic fixtures, or client-only mutations. The most acute finding is `A03-003`: a real pharmacy substitution API request is created and approved by one button press, with no distinct approval gate in the page.

Positive controls verified:
- `src/pages/results/ResultsPage.tsx:1-9`, `src/pages/samples/SamplesPage.tsx:1-9`, and `src/pages/ehr/EhrPage.tsx:1-10` intentionally render `LegacyRouteBridge` instead of direct REST clinical reads.
- `src/pages/reports/ReportsPage.tsx:3-25` and `src/pages/notifications/NotificationsPage.tsx:8-30` are explicit safe-empty surfaces (`data-contract-status="unbound"`, `data-governance-state="safe-empty"`).
- `src/pages/patients/PatientsPage.tsx:4,27-32,37-39` and `src/pages/orders/OrdersPage.tsx:4,29-34` use `workspaceScopedReads` and surface `WorkspaceReadBlockedError`.
- `src/pages/ehr/EhrPage.test.tsx:5-10`, `src/pages/migration/LegacyRouteBridge.test.ts:19-25`, and `src/pages/patient-visit/PatientVisitReadinessPage.test.tsx:5-14` assert non-operational boundaries.

**Constitution check (PROGRAM-CONSTITUTION-001):** No commercial software is required by any finding or candidate. No vendor-specific SDK or paid API is introduced. Candidates reuse the existing open-source React/React Query stack and existing `ErrorDisplay`/`EmptyState`/`DataTable` primitives. No clinical procedure, result interpretation, medication choice, or approval rule was invented — findings only identify missing gates, inconsistent state, or unbound contracts.

---

## 1. Evidence base and method

| Area | Key paths reviewed |
|---|---|
| Governed clinical reads | `src/pages/patients/PatientsPage.tsx`, `src/pages/orders/OrdersPage.tsx`, `src/pages/migration/LegacyRouteBridge.tsx`, `src/pages/migration/frontendSurfaceCatalog.ts` |
| Deliberately unbound clinical pages | `src/pages/results/ResultsPage.tsx`, `src/pages/samples/SamplesPage.tsx`, `src/pages/ehr/EhrPage.tsx`, `src/pages/reports/ReportsPage.tsx`, `src/pages/notifications/NotificationsPage.tsx` |
| Direct-REST clinical pages | `src/pages/labs/LabsPage.tsx`, `src/pages/qc/QCPage.tsx`, `src/pages/patient-card/PatientCardPage.tsx` |
| Synthetic clinical workspaces | `src/pages/patients/PatientManagementWorkspacePage.tsx`, `src/pages/lab/LabOperationsWorkspacePage.tsx`, `src/pages/pharmacy/PharmacyOperationsWorkspacePage.tsx`, `src/pages/pharmacy/PharmacyPosPanel.tsx` |
| FHIR pages | `src/pages/fhir/FhirPage.tsx`, `FhirExplorerPage.tsx`, `FhirPatientPage.tsx`, `FhirObservationPage.tsx`, `FhirReportPage.tsx` |
| Citizen surfaces | `src/pages/citizen-platform/CitizenPlatformPage.tsx`, `CitizenWorkspacePage.tsx` |
| Live-capable synthetic workspaces | `src/pages/devices/DeviceIntegrationWorkspacePage.tsx`, `src/pages/billing/BillingInsuranceWorkspacePage.tsx`, `src/pages/financial-governance/FinancialGovernancePage.tsx` |
| Generated API-stub pages | `src/pages/critical-care/CriticalCareApiPage.tsx`, `src/pages/public-health/PublicHealthApiPage.tsx`, `src/pages/capabilities/clinical-foundation/CapabilitiesClinicalFoundationPage.tsx`, `src/pages/health-data/HealthDataPage.tsx` |
| National / AI / governance | `src/pages/national-data/NationalDataPage.tsx`, `src/pages/ai-platform/AiPlatformPage.tsx`, `src/pages/niam/*.tsx`, `src/pages/compliance/CompliancePage.tsx`, `src/pages/tiers/TiersPage.tsx` |
| Read-only route evidence | `frontend-v3/src/routes/index.tsx` |
| Read-only API evidence | `frontend-v3/src/api/endpoints.ts:1305` |
| Co-located tests | `src/pages/ehr/EhrPage.test.tsx`, `src/pages/patient-visit/PatientVisitReadinessPage.test.tsx`, `src/pages/migration/LegacyRouteBridge.test.ts` |

Read-only cleanliness check: `git status --porcelain -- frontend-v3/src/pages/` returned **no output**. `frontend-v3/src/components/navigation/MobileBottomNav.test.tsx` is protected user work owned by A02 and was not touched.

Speculation convention: where server-side enforcement or clinical intent cannot be observed from page code, it is explicitly labelled **Speculation (unverified)** and routed as a SCOPE_REQUEST. No such speculation is treated as a confirmed defect.

---

## 2. Findings

Format per assignment: ID · Severity · Title · Evidence · Affected components · Root cause · Safe-fix possible? · Approval required?

---

### A03-001 — P1 — Routed synthetic patient workspace presents realistic patient registry data and local-only registration as an operational workflow

**Evidence:**
- `src/pages/patients/PatientManagementWorkspacePage.tsx:63-81` defines `INITIAL_PATIENTS`, `INITIAL_APPOINTMENTS`, and `INITIAL_QUEUE` with realistic names, `GULA-*` health IDs, phone numbers, birth dates, cities, care paths, clinicians, and appointment locations.
- `:101-104` initializes component state directly from those constants; `:179-182` renders the directory/registration/appointments/queue tabs from local state.
- `:117-140` `submitRegistration` generates a new `GULA-*` ID and calls only `setPatients(...)`; `:139` reports `تم إنشاء ملف تجريبي للمريض ...` (“a trial patient file was created”).
- `:153-154` labels the fixture synthetic/isolated; `:184` states registration and selection are local to the preview only and must later pass through a server contract, workspace permissions, and an audit trail.
- `frontend-v3/src/routes/index.tsx:119,146` includes `demo_viewer` in `readonlyRoles` and guards `/patient-management` with that list.

**Affected components:** `PatientManagementWorkspacePage`, `/patient-management` route, role guard policy.

**Root cause:** An explicitly isolated demo fixture was implemented as a production-looking routed page with operational labels (“patient management”, registration form, queue) and state-only mutations. The labels reduce clinical risk, but the route/role surface makes the distinction easy to miss.

**Safe-fix possible?** **Yes, partially.** Page-local: keep the synthetic banner visible in every tab, disable registration in non-demo mode, and label the generated ID as non-clinical. Route guard changes are not A03-owned.

**Approval required?** **Yes.** Determining whether `demo_viewer` may reach this surface and whether synthetic patient data may be displayed outside a demo environment is an access-policy decision (A04/orchestrator).

---

### A03-002 — P1 — Synthetic lab results, critical alert, and local-only “verification” are presented as an operational laboratory workflow

**Evidence:**
- `src/pages/lab/LabOperationsWorkspacePage.tsx:79-103` seeds samples, results, analyzers, and QC records, including `Troponin I` with value `0.88 ng/mL`, reference `< 0.04`, state `حرجة` (critical), and a QC TSH record `يحتاج مراجعة`.
- `:117-121` holds these fixtures in component state; `:143-150` `simulateVerify` and `advanceSample` change only local React state and emit notices saying the action was simulated locally.
- `:160` says the data are synthetic and are not sent to OpenELIS or any external system; `:176` states verification/transition buttons only change UI state and require a server contract, lab permissions, and an audit trail.
- `frontend-v3/src/routes/index.tsx:119,147` grants `/lab-operations` to `readonlyRoles`, including `demo_viewer`.

**Affected components:** `LabOperationsWorkspacePage`, `/lab-operations` route, role guard policy.

**Root cause:** Same isolated-demo pattern as A03-001, applied to higher-risk content: numeric results, reference ranges, a critical flag, and verification controls.

**Safe-fix possible?** **Yes, partially.** Page-local: persist a visible “synthetic / non-operational” marker in the results tab and disable/relabel verify/advance actions outside demo mode. No clinical interpretation should be added.

**Approval required?** **Yes.** Any change to who can see or act on lab-style verification controls requires clinical and access-policy approval (A04/A05).

---

### A03-003 — P0 — Pharmacy substitution request and approval are executed by the same client click on a real API path

**Evidence:**
- `src/pages/pharmacy/PharmacyPosPanel.tsx:52-70` defines `substitutionMutation`; its `mutationFn` calls `pharmacyApi.createSubstitutionRequest({...})` and then immediately `await pharmacyApi.approveSubstitution(request.id)`.
- `:59` hardcodes `reason: "original medication unavailable"`.
- `:158` renders the action button with the label `طلب واعتماد` (“request and approve”), directly calling `substitutionMutation.mutate({ candidate, line: substitutionTarget })`; the consent checkbox only gates buttons for candidates where `candidate.requires_patient_consent` is true.
- `frontend-v3/src/routes/index.tsx:222-223` exposes pharmacy surfaces under `adminRoles` and `readonlyRoles` (`readonlyRoles` includes `demo_viewer`, `:119`).

**Affected components:** `PharmacyPosPanel`, pharmacy substitution API calls, pharmacy routes.

**Root cause:** The page collapses “request created” and “request approved” into one mutation and one button. There is no distinct visible approval step, approver identity check, or confirmation of the generated request before the approval API call. **Speculation (unverified):** the backend may independently enforce approver authorization; that cannot be confirmed from page code and requires A04/A07 review.

**Safe-fix possible?** **Yes, for the UI control boundary only:** create the request first, display a pending state, and require a separate explicit approve action. This does **not** define which substitute is clinically appropriate and does not replace server-side authorization.

**Approval required?** **Yes.** This is a real mutation on a medication-substitution workflow. Clinical governance and server-side authorization must approve any change before Wave C. **P0 blocks pharmacy-surface remediation until resolved or formally downgraded.**

---

### A03-004 — P1 — Real sale mutation is built from fabricated encounter/payment identifiers and an unvalidated billing patient ID

**Evidence:**
- `src/pages/pharmacy/PharmacyPosPanel.tsx:72-77` `saleMutation` calls `pharmacyApi.createSale(payload, ...)`.
- `:91-104` `submitSale` checks only that the cart is non-empty and `billingPatientId.trim()` is truthy, then sets `billing_patient_id: Number(billingPatientId)`, `encounter_ref: \`PHARMACY-POS-${new Date().toISOString().slice(0, 10)}\``, `payment_method: "synthetic_settlement"`, and `issue_invoice: true`.
- `:163` success text claims inventory, invoice, and dispense log were recorded; `:167` only conditionally notes that the report uses synthetic records.

**Affected components:** `PharmacyPosPanel`, sale/invoice API contract, billing integration.

**Root cause:** Required clinical/billing linkage fields are synthesized in the client instead of being supplied by an approved encounter/payment context; `Number(...)` can also produce a non-finite value without page-level validation.

**Safe-fix possible?** **Partial.** The page can validate the numeric ID and stop claiming settlement/audit outcomes it cannot verify. Removing fabricated identifiers requires an approved source contract.

**Approval required?** **Yes.** Encounter references, payment methods, and invoice issuance are contract and financial-control decisions (A07 + governance), not page-local inventions.

---

### A03-005 — P1 — Permission-gated display is inconsistent: governed reads exist beside direct REST clinical pages with no visible workspace contract

**Evidence:**
- Governed pattern: `src/pages/patients/PatientsPage.tsx:4,27-32,37-39` imports `workspaceScopedReads`/`WorkspaceReadBlockedError`, uses `patients.read`, sets `retry: false`, and declares `data-contract-id`, `data-permission`, `data-workspace-context="required"`. `src/pages/orders/OrdersPage.tsx:4,29-34` uses the same pattern for `orders.read`.
- Deliberately blocked pattern: `src/pages/results/ResultsPage.tsx:3-9`, `src/pages/samples/SamplesPage.tsx:3-9`, and `src/pages/ehr/EhrPage.tsx:3-10` explain why direct REST is not used and render `LegacyRouteBridge`.
- Direct REST pattern still present: `src/pages/labs/LabsPage.tsx:2,12-15` calls `adminApi.labs` and renders names, phones, license numbers, and director names (`:17-31`); `src/pages/qc/QCPage.tsx:2,24-27` calls `qcApi.list` and renders measured/expected values (`:29-43`); `src/pages/patient-card/PatientCardPage.tsx:5,12-20,54-55` calls `patientCardApi.get(activeId!)` and opens `/api/patient-card/${activeId}/print` from a raw numeric ID.
- `frontend-v3/src/routes/index.tsx:145-152,159,171-172` shows these surfaces guarded by different role lists; `/results`, `/samples`, and `/ehr` use the bridge while `/labs`, `/qc`, and `/patient-card` render live data components.

**Affected components:** `PatientsPage`, `OrdersPage`, `LabsPage`, `QCPage`, `PatientCardPage`, `LegacyRouteBridge`, route guards.

**Root cause:** Two read architectures coexist. The governed pattern is explicit about contract and workspace context; the direct-REST pages are not. **Speculation (unverified):** backend endpoints may still enforce tenant/workspace scope, but no such guarantee is visible in these pages.

**Safe-fix possible?** **No, not fully page-local.** Migrating direct reads to `workspaceScopedReads` or an approved contract requires A04/A07 approval; A03 can only add explanatory state markers.

**Approval required?** **Yes.** This is a data-boundary and authorization decision, not a presentation-only change.

---

### A03-006 — P1 — FHIR Explorer offers 13 resource types but silently substitutes a Patient lookup for 10 of them

**Evidence:**
- `src/pages/fhir/FhirExplorerPage.tsx:19-33` lists 13 selectable `RESOURCE_TYPES`, including `Encounter`, `Condition`, `MedicationRequest`, `Immunization`, `AllergyIntolerance`, `Composition`, `DocumentReference`, `Procedure`, `CarePlan`, and `Bundle`.
- `:37-48` `fhirLookup` handles only `Patient`, `Observation`, and `DiagnosticReport`; the `default` branch returns `complianceApi.fhirPatient(Number(id))`.
- `:55-58` the query calls `fhirLookup(resourceType, searchId)`; `:133-144` renders the selected `resourceType/searchId` as the title while the badge shows the actual `data.resourceType`.

**Affected components:** `FhirExplorerPage`, `complianceApi` FHIR lookups.

**Root cause:** Incomplete switch with a permissive fallback. The visible actual-resource badge may reveal a mismatch to an expert user, but the fetch and display of a Patient record still occur when another type was requested.

**Safe-fix possible?** **Yes.** Page-local: disable unsupported options or render an explicit “resource lookup not bound” state; no API contract change is required to stop the silent fallback.

**Approval required?** **Yes.** Removing or disabling advertised FHIR lookup options changes a user-visible capability and must be coordinated with A05/A07 on the intended resource mapping.

---

### A03-007 — P1 — FHIR detail pages read arbitrary numeric IDs with no visible workspace context

**Evidence:**
- `src/pages/fhir/FhirPatientPage.tsx:71-78`, `src/pages/fhir/FhirObservationPage.tsx:72-79`, and `src/pages/fhir/FhirReportPage.tsx:76-83` each store a free-text ID and call `complianceApi.fhirPatient/fhirObservation/fhirDiagnosticReport(Number(searchId))`.
- Read-only grep across `src/pages/fhir/*.tsx` found **no** `workspaceScopedReads`, `WorkspaceReadBlockedError`, or `data-workspace-context` usage.
- Contrast: `src/pages/patients/PatientsPage.tsx:27-39` shows the governed pattern used elsewhere in the same application.
- `frontend-v3/src/routes/index.tsx:171` guards `/fhir` with `adminRoles`.

**Affected components:** `FhirPatientPage`, `FhirObservationPage`, `FhirReportPage`, FHIR API layer.

**Root cause:** Detail pages accept raw identifiers and rely entirely on implicit server behavior; no workspace-scope signal or blocked-read state is present in the page. **Speculation (unverified):** the backend may enforce scope; A04/A07 must verify.

**Safe-fix possible?** **No, not for enforcement.** A03 can add explanatory context or remove free-form lookup, but tenant/PHI boundary enforcement belongs to the server and route policy.

**Approval required?** **Yes.** Any lookup or display change touches PHI access semantics.

---

### A03-008 — P1 — Admin citizen page calls non-`/me` endpoints while the citizen workspace uses `/me`, and renders generic clinical columns

**Evidence:**
- `src/pages/citizen-platform/CitizenPlatformPage.tsx:36-59` calls `/citizen-platform/dashboard`, `/profile`, `/health-summary`, `/appointments`, `/medications`, and `/lab-results` (no `/me`).
- `src/pages/citizen-platform/CitizenWorkspacePage.tsx:37-64` calls the corresponding `/citizen-platform/me/...` endpoints.
- `frontend-v3/src/routes/index.tsx:198-199` routes `/citizen` to role `["citizen"]` and `/citizen-platform` to `adminRoles`.
- `CitizenPlatformPage.tsx:61-96` renders health summary, appointments, medications, and lab results with generic columns `id`, `name`, `status`, `created_at`; `:98-105` binds those columns directly to the query results.

**Affected components:** `CitizenPlatformPage`, `CitizenWorkspacePage`, citizen-platform API contracts, role guards.

**Root cause:** Two citizen surfaces with different endpoint families and identical generic schemas. **Speculation (unverified):** the non-`/me` endpoints may be intentional administrative aggregate endpoints; alternatively they may expose cross-citizen records. Page code alone cannot resolve this.

**Safe-fix possible?** **No, not for endpoint selection.** A03 can stop rendering clinical labels over unvalidated generic columns, but endpoint intent and authorization require A04/A07.

**Approval required?** **Yes.** Citizen PHI scope and admin access semantics must be confirmed before any change.

---

### A03-009 — P1 — Live-capable workspaces initialize from synthetic fixtures and retain them when backend loading fails

**Evidence:**
- `src/pages/devices/DeviceIntegrationWorkspacePage.tsx:380-388` initializes devices, summary, protocols, events, jobs, connectors, profiles, simulators, and monitoring from synthetic constants; `:400-401` loads live data only when `!demoMode && isInstitutional`; `:425-426` catch sets only an error while leaving synthetic state; `:601` labels the page `Live + guarded` outside demo mode.
- `src/pages/billing/BillingInsuranceWorkspacePage.tsx:175-180` seeds invoices, claims, policies, payments, and alerts from `INITIAL_*`; `:186-205` loads live data in non-demo mode; `:201` catch sets only an error saying existing data was not automatically replaced.
- `src/pages/financial-governance/FinancialGovernancePage.tsx:74-75` seeds summary and requests from synthetic constants; `:79-103` loads live data in non-demo mode; `:95` catch says no alternative numbers were displayed, while `:74-75` state remains; `:130` shows the synthetic-data warning only when `demoMode` is true.

**Affected components:** `DeviceIntegrationWorkspacePage`, `BillingInsuranceWorkspacePage`, `FinancialGovernancePage`.

**Root cause:** Synthetic fixtures are used as initial state for pages that also attempt live loading; failure paths do not clear, hide, or explicitly invalidate those fixtures. Error copy in two pages asserts a substitution did not occur while synthetic values remain visible.

**Safe-fix possible?** **Yes, page-local:** on live-load failure, switch to an explicit error/empty state and disable actions/metrics derived from synthetic state. Do not invent replacement clinical, device, or financial data.

**Approval required?** **Yes.** Display of synthetic operational data in a live context is a governance decision (A04/A05/orchestrator).

---

### A03-010 — P1 — Clinical/public-health API-stub pages render placeholder `id/name/status/created_at` schemas for domain endpoints

**Evidence:**
- `src/pages/critical-care/CriticalCareApiPage.tsx:36-59` queries admissions, bed availability, vitals, ventilator, dashboard, and health endpoints; `:61-96` every column set is only `id`, `name`, `status`, `created_at`; `:98-105` binds query data to those columns; `:124` renders the table.
- `src/pages/public-health/PublicHealthApiPage.tsx:36-59` queries disease cases, stats, outbreak alerts, surveillance signals, vaccinations, and coverage; `:61-96` uses the same four-column schema; `:124` renders the table.
- `src/pages/capabilities/clinical-foundation/CapabilitiesClinicalFoundationPage.tsx:31-45` queries `/clinical-foundation` and uses the same schema; `:64` renders it.
- `frontend-v3/src/routes/index.tsx:188,203,228` exposes these surfaces under `readonlyRoles`/`adminRoles` as real product pages, not labelled prototypes.

**Affected components:** `CriticalCareApiPage`, `PublicHealthApiPage`, `CapabilitiesClinicalFoundationPage`; representative of the generated API-stub page family.

**Root cause:** A generic CRUD table template was applied to clinical domains without response-contract validation. Vitals, cases, alerts, or foundation capabilities cannot be meaningfully represented by `id/name/status/created_at`.

**Safe-fix possible?** **No, not to a clinically valid state.** A page can hide the table until a contract is approved, but correct columns require A05/A07 input.

**Approval required?** **Yes.** Clinical contract definition and display semantics are outside A03 authority.

---

### A03-011 — P2 — Generated API-stub pages ignore query errors, so failed clinical reads look like empty tables

**Evidence:**
- Read-only grep for `error|ErrorDisplay|EmptyState|onRetry` in `CriticalCareApiPage.tsx`, `PublicHealthApiPage.tsx`, and `CapabilitiesClinicalFoundationPage.tsx` returned **no matches**.
- The pages destructure only `data` and `isLoading` (e.g. `CriticalCareApiPage.tsx:36-59`; `PublicHealthApiPage.tsx:36-59`; `CapabilitiesClinicalFoundationPage.tsx:31-34`) and pass only `columns`, `data`, and `loading` to `DataTable` (`:124`, `:124`, `:64`).

**Affected components:** The same generated API-stub page family as A03-010.

**Root cause:** Query error state is dropped at the page boundary. A failed critical-care or public-health read is indistinguishable from a successful empty response.

**Safe-fix possible?** **Yes.** Page-local: destructure `error`/`refetch` and render the existing `ErrorDisplay` used elsewhere (for example `src/pages/qc/QCPage.tsx:4,24-27`). Shared pattern changes belong to A02.

**Approval required?** **No** for using the existing error primitive without changing data semantics; **Yes** if error text is customised or shared components are modified.

---

### A03-012 — P1 — National data quality “read” is actually a POST mutation inside `useQuery`, and retry can create another check

**Evidence:**
- `src/pages/national-data/NationalDataPage.tsx:92-95` defines `qualityQuery` with `queryFn: () => nationalDataApi.recordDataQualityCheck({})`.
- `frontend-v3/src/api/endpoints.ts:1305` (read-only evidence) shows `recordDataQualityCheck` is `api.post("/national-data/data-quality-checks", data)`.
- `NationalDataPage.tsx:270-281` renders `LoadingSpinner`, `ErrorDisplay`, and `EmptyState` from this query; `:275` `onRetry={() => qualityQuery.refetch()}` can invoke the POST again.
- `frontend-v3/src/routes/index.tsx:177` restricts this route to `master_admin`, `ministry_admin`, and `province_admin`.

**Affected components:** `NationalDataPage`, national data-quality API.

**Root cause:** A mutating endpoint is used as a read/query source; React Query refetch/stale behavior can therefore create audit records as a side effect of viewing or retrying a tab.

**Safe-fix possible?** **Yes, partially.** A03 can stop calling the mutation in `useQuery` and render an explicit empty/unbound state, but the correct read endpoint or intended trigger policy must be supplied by A07/governance.

**Approval required?** **Yes.** Mutation semantics and audit-record creation require backend/API approval.

---

### A03-013 — P2 — National golden-record table displays raw `national_id` values

**Evidence:**
- `src/pages/national-data/NationalDataPage.tsx:109-132` defines `goldenRecordColumns`, including `{ accessorKey: "national_id", header: "الرقم الوطني" }` at `:112`, alongside patient name and confidence score.
- `frontend-v3/src/routes/index.tsx:177` limits the route to senior national/admin roles, but the page has no masking, truncation, or purpose/audit notice around the identifier.

**Affected components:** `NationalDataPage`, national golden-record display.

**Root cause:** A sensitive national identifier is rendered verbatim with the same treatment as ordinary table fields.

**Safe-fix possible?** **Yes, page-local** for a non-reversible masked display or removal of the column. The exact masking policy must not be invented by A03.

**Approval required?** **Yes.** PHI minimization and identifier-display policy belong to A04/governance.

---

### A03-014 — P2 — AI platform exposes free-text search/RAG/agent execution with raw JSON output and no visible advisory or provenance boundary

**Evidence:**
- `src/pages/ai-platform/AiPlatformPage.tsx:127-155` sends arbitrary `searchQuery`/`ragQuery` text to `aiPlatformApi.search` and `aiPlatformApi.ragQuery`.
- `:320-339` builds `{ tool, input }`, parses user text as JSON when possible, and calls `aiPlatformApi.agentExecute`.
- `:397-400` renders the full response with `JSON.stringify(execResult, null, 2)`.
- Read-only grep for `advisory|تنبيه|غير تشغيلي|provenance|مصدر|تجريبي` in this file returned **no matches**.
- `frontend-v3/src/routes/index.tsx:156` exposes `/ai-platform` to `readonlyRoles`, including `demo_viewer` (`:119`).

**Affected components:** `AiPlatformPage`, AI platform API calls.

**Root cause:** An unconstrained execution/query surface is presented without a page-level advisory marker, provenance display, or output-scope notice. **Speculation (unverified):** guardrails may exist in the self-hosted backend; nothing in the page makes them visible.

**Safe-fix possible?** **Partial.** A03 can add a clear advisory/non-decisional banner and collapse raw JSON behind an explicit “show raw response” control. Output filtering or provenance requires A05/backend approval.

**Approval required?** **Yes.** AI output presentation and access for `demo_viewer` are clinical-safety and policy decisions.

---

### A03-015 — P2 — Clinical and audit action buttons are inert

**Evidence:**
- `src/pages/fhir/FhirReportPage.tsx:154-157` renders `<Button variant="outline" size="sm"><Download />تحميل</Button>` with no `onClick`.
- `src/pages/labs/LabsPage.tsx:40-44` renders `<Button><Plus />مختبر جديد</Button>` with no `onClick`.
- `src/pages/compliance/CompliancePage.tsx:41-52` renders `عرض` for التدقيق/Aمان and `تصدير` for FHIR with no `onClick`; `:57-59` also shows a future-tense performance placeholder.

**Affected components:** `FhirReportPage`, `LabsPage`, `CompliancePage`.

**Root cause:** Scaffolded controls were shipped without handlers or disabled states, so users can perceive an available download/create/export action that cannot complete.

**Safe-fix possible?** **Yes.** Page-local: either disable with an explicit “not bound” reason or remove the control. Implementing real export/create behavior is not page-local.

**Approval required?** **Yes** for any real export/creation behavior (API + permission contract); **No** for a clearly disabled state that preserves the layout.

---

### A03-016 — P3 — Governance tabs and a tier action contain hardcoded empty states or dead controls

**Evidence:**
- `src/pages/niam/WorkflowsPage.tsx:67-71` sets `approvals: { columns: instanceCols, data: [], loading: false }` while the page header advertises الموافقات (`:75`).
- `src/pages/niam/AdaptiveAuthPage.tsx:81-86` sets `travel: { columns: eventCols, data: [] as Record<string, unknown>[], loading: false }` while the page header advertises risk events/sessions/MFA (`:90`).
- `src/pages/tiers/TiersPage.tsx:68-70` renders a `ترقية` button with no `onClick`.
- `frontend-v3/src/routes/index.tsx:162,183-184` shows these routes use `readonlyRoles`/`adminRoles`.

**Affected components:** `WorkflowsPage`, `AdaptiveAuthPage`, `TiersPage`.

**Root cause:** Placeholder tabs and buttons were rendered as if bound, with no explicit empty/unbound explanation.

**Safe-fix possible?** **Yes.** Page-local: render the existing `EmptyState` with an explicit “source not bound” message, or disable the upgrade button with a reason.

**Approval required?** **No** for explanatory empty/disabled states; **Yes** if a real data source or upgrade mutation is added.

---

## 3. Non-findings and deliberate boundaries

The following were reviewed and are **not** reported as defects:
- `ResultsPage`, `SamplesPage`, `EhrPage`: intentionally non-functional bridges with explanatory comments; this is the governed state, not an incomplete page.
- `ReportsPage`, `NotificationsPage`: intentionally safe-empty with explicit `unbound`/`safe-empty` markers.
- `PatientVisitReadinessPage`: test at `src/pages/patient-visit/PatientVisitReadinessPage.test.tsx:5-14` asserts `Prototype آمن وغير تشغيلي` and absence of patient/API data.
- Synthetic workspaces that explicitly state advisory-only/non-operational boundaries (for example `src/pages/pharmacy/PharmacyOperationsWorkspacePage.tsx:164`) are lower risk than the live-facing patterns in A03-001/002/009.
- Shared-component, token, theme, route-guard, and endpoint defects are outside A03 write ownership and are not “fixed” here; they appear only as SCOPE_REQUESTs in the companion report.

No findings were closed by assumption. No source file was modified to make a page appear compliant.
