# CLINICAL WORKFLOW REMEDIATION PLAN — A03 (frontend-v3 pages)

**Program:** PROGRAM-GULA-PARALLEL-001
**Agent:** A03 — Frontend Clinical Workflows
**Status:** **PROPOSED ONLY — NOT APPLIED. WAVE C BLOCKED BY PROGRAM CONTROL.**
**Companion audit:** `docs/parallel-program/frontend/CLINICAL_WORKFLOW_AUDIT.md`
**Date:** 2026-11-19

---

## 0. Authorization and gating statement

This document lists **candidates**, not commits. Per `PROGRAM_CONTROL.md` §3 and `FILE_OWNERSHIP_MATRIX.md` §5, no Wave C work may begin until:

1. `MASTER_REMEDIATION_REGISTER.md` is consolidated and approved by the orchestrator;
2. each target file is confirmed to match exactly one agent's scope (A03 = `frontend-v3/src/pages/**` plus co-located page tests; **never** shared components, routes, endpoints, theme, or config);
3. `git status --porcelain -- <file>` is **empty** for that file;
4. no open P0 blocks the affected component;
5. the change does not alter clinical logic, auth/RBAC behavior, API contracts, DB schema/migrations, or CI semantics without independent approval.

**Current A03 P0:** `A03-003` (pharmacy substitution request + approval in one click). It blocks candidates **C-01 and C-02** until the orchestrator resolves or formally downgrades the finding.

**Eligibility legend:**
- `CLEAN` = verified clean by read-only `git status --porcelain -- frontend-v3/src/pages/` on 2026-11-19 (command returned no output).
- `USER` = pre-existing user work — **PROTECTED / NEVER TOUCHED**.
- **safe-fix eligible** = CLEAN **and** page-local **and** no clinical-logic, route, shared-component, or API-contract change.
- **needs-approval** = orchestrator sign-off and, where noted, A02/A04/A05/A07 review before any Wave C edit.

Read-only cleanliness notes:
- All cited page files are CLEAN. No page file was modified.
- `frontend-v3/src/components/navigation/MobileBottomNav.test.tsx` is protected user work owned by A02 and was not touched.
- `frontend-v3/src/api/endpoints.ts` is protected user work; it was read only as evidence for `A03-012` and is **not** a candidate.
- No build, test runner, server, migration, or git state-changing command was executed.

**Constitution compliance:** every candidate reuses the already-present open-source stack (React, React Query, existing `ErrorDisplay`/`EmptyState`/`DataTable` primitives). No commercial software, paid API, new SaaS, or vendor-specific SDK is proposed. Self-hosted backend contracts are preferred; “Reuse Before Build” is applied by reusing existing primitives rather than introducing a new page-state abstraction. No medication choice, result interpretation, approval rule, clinical threshold, or identifier-masking policy is invented.

---

## 1. Candidate register (summary)

| ID | Finding | Primary file(s) | Change class | Clean? | Safe-fix eligible | Needs approval |
|---|---|---|---|---|---|---|
| C-01 | A03-003 | `src/pages/pharmacy/PharmacyPosPanel.tsx` | Split substitution request from approval into two explicit UI steps | CLEAN | Yes, **after P0 disposition** | **Yes** (clinical governance + server authz) |
| C-02 | A03-004 | `src/pages/pharmacy/PharmacyPosPanel.tsx` | Validate billing patient ID; stop fabricated encounter/payment values and overclaiming success | CLEAN | Partial | **Yes** (API/financial contract) |
| C-03 | A03-001 | `src/pages/patients/PatientManagementWorkspacePage.tsx` | Persistent synthetic banner; gate local registration outside demo mode | CLEAN | Partial | **Yes** (access/display policy) |
| C-04 | A03-002 | `src/pages/lab/LabOperationsWorkspacePage.tsx` | Persistent synthetic banner; disable/relabel simulate-verify and advance outside demo mode | CLEAN | Partial | **Yes** (lab verification display policy) |
| C-05 | A03-006 | `src/pages/fhir/FhirExplorerPage.tsx` | Remove silent Patient fallback; disable unsupported resource options | CLEAN | **Yes** | **Yes** (FHIR capability surface) |
| C-06 | A03-007 | `src/pages/fhir/FhirPatientPage.tsx`, `FhirObservationPage.tsx`, `FhirReportPage.tsx` | Mark raw-ID lookup as unbound until scoped contract; no enforcement claim | CLEAN | Partial | **Yes** (PHI/workspace scope) |
| C-07 | A03-008 | `src/pages/citizen-platform/CitizenPlatformPage.tsx` | Stop labeling unvalidated generic columns as clinical data | CLEAN | Partial | **Yes** (endpoint intent + admin PHI scope) |
| C-08 | A03-009 | `src/pages/devices/DeviceIntegrationWorkspacePage.tsx`, `src/pages/billing/BillingInsuranceWorkspacePage.tsx`, `src/pages/financial-governance/FinancialGovernancePage.tsx` | On live-load failure, hide synthetic metrics/actions and show error/empty state | CLEAN | **Yes** | **Yes** (live-mode synthetic display policy) |
| C-09 | A03-010 | `src/pages/critical-care/CriticalCareApiPage.tsx`, `src/pages/public-health/PublicHealthApiPage.tsx`, `src/pages/capabilities/clinical-foundation/CapabilitiesClinicalFoundationPage.tsx` | Replace unvalidated clinical tables with explicit unbound state pending contract | CLEAN | Partial | **Yes** (clinical response schema) |
| C-10 | A03-011 | Same generated API-stub family as C-09 | Destructure `error`/`refetch`; render existing `ErrorDisplay` | CLEAN | **Yes** | **No** for existing primitive; **Yes** if shared component changes |
| C-11 | A03-012 | `src/pages/national-data/NationalDataPage.tsx` | Stop POSTing from `useQuery`; remove retry that can create another check | CLEAN | Partial | **Yes** (read/mutation semantics) |
| C-12 | A03-013 | `src/pages/national-data/NationalDataPage.tsx` | Remove or non-reversibly mask raw `national_id` column pending policy | CLEAN | Partial | **Yes** (identifier-display policy) |
| C-13 | A03-014 | `src/pages/ai-platform/AiPlatformPage.tsx` | Add advisory/non-decisional banner; collapse raw JSON output | CLEAN | Partial | **Yes** (AI output policy) |
| C-14 | A03-015 | `src/pages/fhir/FhirReportPage.tsx`, `src/pages/labs/LabsPage.tsx`, `src/pages/compliance/CompliancePage.tsx` | Disable inert download/create/export buttons with explicit reason | CLEAN | **Yes** | **No** for disabled state; **Yes** for real behavior |
| C-15 | A03-016 | `src/pages/niam/WorkflowsPage.tsx`, `AdaptiveAuthPage.tsx`, `src/pages/tiers/TiersPage.tsx` | Replace hardcoded empty tabs/dead upgrade with explicit unbound/disabled state | CLEAN | **Yes** | **No** for explanatory state; **Yes** for new data source |

---

## 2. Concrete candidates — detail

### C-01 — Split substitution request creation from approval

**File:** `frontend-v3/src/pages/pharmacy/PharmacyPosPanel.tsx` · CLEAN · P0-blocked until `A03-003` is dispositioned.

**What would change (PROPOSED — not applied):**
- Replace the single `substitutionMutation` in `:52-70` with two page-local steps:
  1. create the request via `pharmacyApi.createSubstitutionRequest(...)` and keep the returned `request.id` in a pending state;
  2. require a second, separately labelled explicit action before calling `pharmacyApi.approveSubstitution(request.id)`.
- Keep the current consent gate at `:158` intact; do not add a new clinical rule or substitute-selection logic.
- Show a pending status instead of immediately setting `substitution_request_id` in the cart.

**Why this is the safe boundary:** it removes the one-click request+approval coupling visible in the page. It does **not** assert who is clinically authorized to approve; the backend authorization check remains mandatory and is a SCOPE_REQUEST.

**Verification (Wave D, not now):** add a page test that a click on “request” does not call `approveSubstitution`, and that approval requires the second control.

---

### C-02 — Validate pharmacy sale linkage and remove fabricated settlement markers

**File:** `frontend-v3/src/pages/pharmacy/PharmacyPosPanel.tsx` · CLEAN · partial safe-fix · needs approval.

**What would change (PROPOSED — not applied):**
- In `:91-104`, reject `billingPatientId` unless the numeric conversion produces a positive integer; show a page-level validation message.
- Stop constructing `encounter_ref: "PHARMACY-POS-${date}"` and `payment_method: "synthetic_settlement"` as if they were real context. If no approved source exists, disable sale completion with an explicit “linkage not available” state rather than inventing values.
- Narrow the success message at `:163` to what the API response actually confirms.

**Blocked portion:** the authoritative encounter/payment source is an API/financial contract decision (A07/governance). A03 will not choose one.

---

### C-03 — Make the patient workspace’s demo boundary unmissable

**File:** `frontend-v3/src/pages/patients/PatientManagementWorkspacePage.tsx` · CLEAN · partial safe-fix · needs approval.

**What would change (PROPOSED — not applied):**
- Keep the synthetic banner from `:153-154` permanently visible across all four tabs, not only in the header card.
- Gate the registration tab/submit path at `:117-140,180` on an explicit non-demo condition; in live mode, show “registration contract not bound”.
- Keep the existing limitation notice at `:184` and make it visible from the registration tab.

**Blocked portion:** deciding whether `demo_viewer` may access this route (`frontend-v3/src/routes/index.tsx:119,146`) is A04/orchestrator scope.

---

### C-04 — Make the lab workspace’s simulation boundary unmissable

**File:** `frontend-v3/src/pages/lab/LabOperationsWorkspacePage.tsx` · CLEAN · partial safe-fix · needs approval.

**What would change (PROPOSED — not applied):**
- Keep the synthetic notice from `:160` visible on the samples and results tabs, not only in the overview header.
- Relabel or disable `simulateVerify` (`:143-146`) and `advanceSample` (`:148-151`) outside an explicitly synthetic context.
- Preserve the critical-result display from `:79-90` only with its existing source label; do not add interpretation or escalation logic.

**Blocked portion:** lab verification display policy and route access are A04/A05 decisions.

---

### C-05 — Remove silent FHIR resource fallback

**File:** `frontend-v3/src/pages/fhir/FhirExplorerPage.tsx` · CLEAN · safe-fix eligible · needs approval.

**What would change (PROPOSED — not applied):**
- Remove the `default: return complianceApi.fhirPatient(Number(id))` branch at `:45-46`.
- Restrict the selector at `:83-94` to the three handled types, or render an explicit “resource lookup not bound” state for the other ten types listed at `:19-33`.
- Keep the actual `resourceType` badge at `:133-136`; it already exposes mismatches and should not be removed.

**Why safe:** no API contract change; it prevents a Patient record being fetched under a different selected resource label. Any intended mapping for the ten unsupported types must come from A05/A07.

---

### C-06 — Remove the appearance of an enforced FHIR scope that the page cannot prove

**Files:** `src/pages/fhir/FhirPatientPage.tsx`, `FhirObservationPage.tsx`, `FhirReportPage.tsx` · CLEAN · partial safe-fix · needs approval.

**What would change (PROPOSED — not applied):**
- Add a visible boundary marker (for example `data-contract-status="unbound"` plus an explanatory notice) near the raw-ID lookup forms at `FhirPatientPage.tsx:71-78`, `FhirObservationPage.tsx:72-79`, and `FhirReportPage.tsx:76-83`.
- Optionally disable free-form lookup in live mode until a scoped read contract exists.
- Do not claim workspace filtering in page copy; server enforcement is unverified.

**Blocked portion:** actual tenant/workspace enforcement and PHI policy belong to A04/A07.

---

### C-07 — Stop presenting unvalidated citizen admin columns as clinical data

**File:** `src/pages/citizen-platform/CitizenPlatformPage.tsx` · CLEAN · partial safe-fix · needs approval.

**What would change (PROPOSED — not applied):**
- Replace the clinical labels in `healthSummaryCols`, `appointmentsCols`, `medicationsCols`, and `labResultsCols` (`:73-96`) with an explicit “contract not bound” empty state until the response shape is approved.
- Do not silently switch `/citizen-platform/...` (`:36-59`) to `/citizen-platform/me/...`; the admin endpoint intent must be confirmed first.
- Keep the citizen workspace’s `/me` behavior (`:37-64`) unchanged.

---

### C-08 — Fail closed when live-capable workspace loads fail

**Files:** `src/pages/devices/DeviceIntegrationWorkspacePage.tsx`, `src/pages/billing/BillingInsuranceWorkspacePage.tsx`, `src/pages/financial-governance/FinancialGovernancePage.tsx` · CLEAN · safe-fix eligible · needs approval.

**What would change (PROPOSED — not applied):**
- Add a `liveUnavailable` render guard driven by the existing `error` states (`DeviceIntegrationWorkspacePage.tsx:398,425-426`; `BillingInsuranceWorkspacePage.tsx:184,200-201`; `FinancialGovernancePage.tsx:77,94-95`).
- When live loading fails, hide synthetic metrics/tables/actions rather than merely showing error text above them.
- Correct the error copy in device/financial pages so it does not assert that synthetic data was not displayed while synthetic state from `:380-388` / `:74-75` remains in memory.

**Why safe:** page-local render gating only; no replacement data is invented.

---

### C-09 — Hide unvalidated clinical stub tables until a contract exists

**Files:** `src/pages/critical-care/CriticalCareApiPage.tsx`, `src/pages/public-health/PublicHealthApiPage.tsx`, `src/pages/capabilities/clinical-foundation/CapabilitiesClinicalFoundationPage.tsx` · CLEAN · partial safe-fix · needs approval.

**What would change (PROPOSED — not applied):**
- Replace the generic `id/name/status/created_at` column sets (`CriticalCareApiPage.tsx:61-96`, `PublicHealthApiPage.tsx:61-96`, `CapabilitiesClinicalFoundationPage.tsx:36-41`) with an explicit unbound state carrying `data-contract-status="unbound"`.
- Do not invent clinical columns for admissions, vitals, cases, alerts, or foundation capabilities.

**Blocked portion:** correct clinical fields must be supplied by A05/A07.

---

### C-10 — Surface query errors in generated API-stub pages

**Files:** same as C-09 · CLEAN · safe-fix eligible · no approval for existing primitive use.

**What would change (PROPOSED — not applied):**
- Destructure `error` and `refetch` from each `useQuery` and render the existing `ErrorDisplay` (already used in `src/pages/qc/QCPage.tsx:4,24-27`) instead of passing only `columns/data/loading` to `DataTable` (`CriticalCareApiPage.tsx:124`, `PublicHealthApiPage.tsx:124`, `CapabilitiesClinicalFoundationPage.tsx:64`).
- Add an `EmptyState` only when the query truly has no data and no error.

**Shared-component note:** if A02 changes `DataTable`/`ErrorDisplay` themselves, that is SR-A03-04 and not an A03 edit.

---

### C-11 — Stop mutating national data quality on page read/retry

**File:** `frontend-v3/src/pages/national-data/NationalDataPage.tsx` · CLEAN · partial safe-fix · needs approval.

**What would change (PROPOSED — not applied):**
- Remove `queryFn: () => nationalDataApi.recordDataQualityCheck({})` at `:92-95` from the `useQuery`.
- Render an explicit unbound/empty state in the quality tab (`:270-281`) until an approved read endpoint exists.
- Remove or neutralize the retry at `:275` so it cannot create another POST-defined check (`frontend-v3/src/api/endpoints.ts:1305`, read-only evidence).

**Blocked portion:** the correct read endpoint or approved trigger policy is A07/governance scope.

---

### C-12 — Remove raw national identifier display pending policy

**File:** `frontend-v3/src/pages/national-data/NationalDataPage.tsx` · CLEAN · partial safe-fix · needs approval.

**What would change (PROPOSED — not applied):**
- Remove or non-reversibly mask the `national_id` column at `:112` while preserving record navigation if an approved identifier already exists.
- Add a short purpose/scope notice near the golden-record table (`:109-132`).

**Blocked portion:** the exact masking rule and retention policy must come from A04/governance; A03 will not design one.

---

### C-13 — Add a visible advisory boundary to AI execution output

**File:** `src/pages/ai-platform/AiPlatformPage.tsx` · CLEAN · partial safe-fix · needs approval.

**What would change (PROPOSED — not applied):**
- Add a persistent advisory/non-decisional banner to the search/RAG tab (`:116-155`) and agent-tools tab (`:312-339`).
- Collapse raw JSON at `:397-400` behind an explicit “show raw response” disclosure; keep the data unchanged.
- Do not add output filtering, clinical guardrails, or provenance fields without A05/backend approval.

---

### C-14 — Disable inert clinical/audit buttons with explicit reasons

**Files:** `src/pages/fhir/FhirReportPage.tsx`, `src/pages/labs/LabsPage.tsx`, `src/pages/compliance/CompliancePage.tsx` · CLEAN · safe-fix eligible.

**What would change (PROPOSED — not applied):**
- Add `disabled` plus an explanatory `title`/nearby text to `تحميل` (`FhirReportPage.tsx:154-157`), `مختبر جديد` (`LabsPage.tsx:40-44`), and `عرض`/`تصدير` (`CompliancePage.tsx:41-52`).
- Do not implement download/create/export behavior in Wave C; those need API and permission contracts.

---

### C-15 — Replace hardcoded governance empty states with explicit unbound states

**Files:** `src/pages/niam/WorkflowsPage.tsx`, `src/pages/niam/AdaptiveAuthPage.tsx`, `src/pages/tiers/TiersPage.tsx` · CLEAN · safe-fix eligible.

**What would change (PROPOSED — not applied):**
- Replace `approvals: { data: [] }` (`WorkflowsPage.tsx:67-71`) and `travel: { data: [] }` (`AdaptiveAuthPage.tsx:81-86`) with an explicit `EmptyState` saying the source is not bound.
- Disable the `ترقية` button at `TiersPage.tsx:68-70` with a reason instead of leaving it clickable and inert.
- Do not add new data sources or billing/upgrade mutations.

---

## 3. SCOPE_REQUESTs

| ID | To | Findings | Request | Why A03 cannot act |
|---|---|---|---|---|
| SR-A03-01 | A04 (Security & Identity) + orchestrator | A03-001, A03-002, A03-003, A03-005, A03-007, A03-008 | Verify and, if needed, enforce server-side workspace/tenant scope and role policy for direct REST clinical pages, raw-ID FHIR reads, citizen admin endpoints, and pharmacy substitution approval. Confirm whether `demo_viewer` should reach synthetic clinical workspaces. | Route guards, authz policy, and PHI scope are outside page ownership; page code cannot prove server enforcement. |
| SR-A03-02 | A05 (Clinical & Interoperability) | A03-003, A03-005, A03-006, A03-009, A03-010, A03-014 | Validate intended clinical resource contracts and semantics: substitution request/approval separation, FHIR resource lookup mapping, citizen lab-result fields, critical-care/public-health fields, and AI output presentation. | A03 must not invent clinical decisions, resource mappings, or output guardrails. |
| SR-A03-03 | A07 (Backend/API) | A03-004, A03-007, A03-008, A03-012 | Confirm response schemas and mutation semantics for `createSubstitutionRequest`/`approveSubstitution`, `createSale`, citizen `/me` vs admin endpoints, FHIR lookups, and `recordDataQualityCheck`. | `frontend-v3/src/api/endpoints.ts` is protected user work and API contracts are outside A03 scope. |
| SR-A03-04 | A02 (Frontend Design System) | A03-011, A03-015, A03-016 | Review a shared error/empty/disabled-control pattern so generated pages do not each hand-roll state presentation. A03 will use existing `ErrorDisplay`/`EmptyState` meanwhile. | `DataTable`, `ErrorDisplay`, and `EmptyState` are A02-owned shared components. |
| SR-A03-05 | Orchestrator + A04/A07 | A03-009 | Decide the product rule for live-capable pages whose initial state is synthetic: forbid synthetic fixtures outside demo mode, or require an explicit “synthetic” watermark on every live-mode render. | This is a governance/product decision; page-local banners alone cannot make synthetic data safe. |

---

## 4. Wave D verification candidates (not executed now)

These are page-local regression tests A03 could add **only after** Wave C authorization and per-file clean verification:

1. `PharmacyPosPanel`: creating a substitution request does not call `approveSubstitution`; approval requires the second control.
2. `DeviceIntegrationWorkspacePage`, `BillingInsuranceWorkspacePage`, `FinancialGovernancePage`: live-load rejection hides synthetic metrics/actions.
3. `FhirExplorerPage`: unsupported resource types never call `fhirPatient`.
4. `NationalDataPage`: rendering the quality tab does not call the POST-defined data-quality endpoint.
5. Generated API stubs: failed queries render an error state instead of an empty table.
6. Dead controls: `تحميل`, `مختبر جديد`, `عرض`, `تصدير`, and `ترقية` are disabled or removed with an explicit reason.

No tests were run in Wave A. `MobileBottomNav.test.tsx` remains A02/user work and is untouched.

---

## 5. Final status

- **Findings:** 16 (P0 1, P1 10, P2 4, P3 1).
- **Candidates:** 15 page-local candidates, all targeting CLEAN files.
- **Applied changes:** **none**.
- **Git state changes:** **none**.
- **Builds / tests / servers:** **none executed**.
- **Wave C:** **BLOCKED** until master register approval, P0 `A03-003` disposition, per-file clean re-verification, and resolution of the SCOPE_REQUESTs above.
