# A05 — Clinical Workflow Audit

**Program:** PROGRAM-GULA-PARALLEL-001 (GULA National Healthcare Platform, Iraq)  
**Agent:** A05 — Clinical Data & Interoperability Auditor  
**Wave:** A (Discovery / AUDIT ONLY)  
**Date:** 2026-11-19  
**Status:** COMPLETE — read-only; no source, config, git, service, database, migration or test-execution changes were made.

---

## 0. Governance and constraints observed

| Rule | Compliance evidence |
|---|---|
| Read-only on all source/config | Investigation used only file reads, path globs, content searches and read-only `git status --porcelain -- <paths>`. No edits outside A05's two owned report paths. |
| Write only to owned paths | Writes are limited to `docs/parallel-program/clinical/CLINICAL_WORKFLOW_AUDIT.md` and `docs/parallel-program/clinical/INTEROPERABILITY_AUDIT.md`. |
| No git state changes | No add/stage/commit/checkout/stash/merge/worktree/reset/clean operation. |
| No tests/migrations/DB execution | No pytest, Alembic, application startup, service call or DB query was executed. Findings are static, evidence-based observations. |
| 378 protected paths | Several cited files are pre-existing user work (see §1.3). All are report-only. |
| Evidence-based | Every finding cites exact `path:line` evidence or a documented repository-wide search. No clinical procedure is invented. |

**Constitution check (PROGRAM-CONSTITUTION-001):** no commercial dependency is recommended. Proposed safe directions reuse existing self-hosted/open-source components already present (PostgreSQL/outbox, SQLAlchemy, FastAPI, pytest). The only licence-sensitive area is official terminology release data (A05-005); no purchase is recommended, and any licensed acquisition would require an owner-approved cost/licence exception after free/open alternatives are documented.

---

## 1. Scope, inventory and method

### 1.1 Files reviewed (≈70 read or searched directly)

**Control plane (5):** `AGENTS.md`, `docs/parallel-program/PROGRAM_CONTROL.md`, `AGENT_ASSIGNMENTS.md`, `FILE_OWNERSHIP_MATRIX.md`, `CONFLICT_REGISTER.md`.

**Clinical workflow / LIMS (primary):**
- `backend/app/lims/{workflows.py,services.py,routes.py,models.py,events.py,fhir_mappers.py}`
- `backend/app/routes/results.py`, `backend/app/routes/quality_control.py`, `backend/app/services/order_service.py`, `backend/app/services/quality_control_service.py`
- `backend/app/clinical/command_guard.py` (release/idempotency path context)
- `backend/app/_compat.py` (UTC helper context)

**MPI / provenance (workflow-relevant):**
- `backend/app/services/mpi/{matcher.py,models.py,blocking.py,resolver.py,canonical_service.py,reliability.py,api.py,schemas.py}`
- `backend/app/services/patient_service.py`, `backend/app/routes/canonical_patient.py`

**Terminology / synthetic clinical package:**
- `backend/app/health_core/clinical/validation.py`
- `backend/app/health_core/terminology/{curated.py,validators.py,registry.py,releases.py,models.py,ports.py,checkdigit.py,__init__.py}`

**AI / RAG / evaluation:**
- `backend/app/ai_fabric/evaluation.py`, `backend/app/ai_fabric/rag.py`, `backend/app/ai/rag_pipeline.py`, `backend/app/ai/vector_store.py`, `backend/app/routes/ai.py`

**Tests read (evidence only, not executed):**
- `backend/tests/unit/test_lims_critical_result_outbox.py`
- `backend/tests/unit/test_aud_clin_003_critical_flag_persistence.py`
- `backend/tests/test_icu_lab_workflow_p0.py`
- `backend/tests/test_governance.py`
- `backend/tests/test_ai_evaluation.py`, `backend/tests/test_ai_platform.py`
- `backend/tests/test_mpi_reliability.py`, `backend/tests/test_mpi_hash_chain_integrity.py`, `backend/tests/test_mpi_audit0416_integrity.py`, `backend/tests/test_mpi_audit01_review_lifecycle.py`
- `backend/tests/health_core/**` (workflow, lab-result correction, FHIR round-trip, static guards)

### 1.2 What is implemented, what is only mentioned, and what is deliberately not production

| Surface | Verified status | Consequence for this audit |
|---|---|---|
| LIMS workflows and routes (`backend/app/lims/**`) | Implemented and registered in `backend/app/factory.py:690` (`lims_routes.router`). | Findings A05-001..003 are about this live path. |
| MPI resolver/reliability | Implemented; advisory locks are PostgreSQL-native (`backend/app/services/mpi/reliability.py:72-77`). | Reviewed for provenance; concurrency proof gap is recorded in the interoperability report (A05-008). |
| AI evaluation/RAG | Implemented modules and routes; evaluation metrics and safety signals are partly declarative only. | Finding A05-004. |
| Health Core synthetic clinical/terminology/FHIR package | Static guards assert it is **not wired into production startup** (`backend/tests/health_core/test_quality_review_static.py:118-130`). | Not reported as production-active. Terminology limitation recorded as a boundary finding (A05-005). |
| `fhir_http` implementation | Explicitly unregistered (`backend/tests/unit/test_fhir_http_endpoints.py:619-623`). | Not treated as production interoperability evidence; see companion report §3. |

### 1.3 Protection status of cited source paths (read-only `git status --porcelain`)

- **USER WORK / PROTECTED:** `backend/app/lims/workflows.py` (modified); `backend/app/health_core/clinical/validation.py`, `backend/app/health_core/terminology/**`, `backend/app/services/mpi/reliability.py` (untracked).
- Clean in the queried set: `backend/app/lims/services.py`, `backend/app/lims/routes.py`, `backend/app/ai_fabric/evaluation.py`, `backend/app/ai/vector_store.py`, `backend/app/ai/rag_pipeline.py`.
- **No file in this scope was modified by A05.**

### 1.4 Executive summary

The LIMS clinical path contains honest but incomplete safety controls. The critical-result workflow deliberately refuses to claim delivery and writes a durable outbox event, but no recipient, escalation or acknowledgement policy exists in the checkout (A05-001, P0). The auto-validation workflow documents a QC gate it does not perform, and the caller omits the patient/delta context needed by its documented checks; auto-validated results are release-eligible (A05-002, P0). A correction helper records a correction audit row without changing the stored value and has no in-repository call site (A05-003, P1). AI clinical evaluation declares safety metrics it does not compute and uses self-referential pass criteria (A05-004, P1). Terminology coverage is explicitly partial and synthetic-only (A05-005, P2).

**Counts (this report):** 5 findings — **P0: 2 · P1: 2 · P2: 1**. Across both A05 reports: **8 findings — P0: 3 · P1: 3 · P2: 2**.

---

## 2. Findings

Format: ID · Severity · Title · Evidence · Affected components · Root cause · Safe-fix possible? · Approval required?

---

### A05-001 — P0 — Critical-result alerts are durably queued but no clinician delivery or acknowledgement path exists

- **Evidence:**
  - `backend/app/lims/workflows.py:227-247` — the function docstring states the event is durable but explicitly says no clinician is contacted; actual delivery remains “BLOCKED until that owner decision and a delivery worker/adapter exist”.
  - `backend/app/lims/workflows.py:270-289` — the `CriticalResultDetected` payload sets `delivery_status: "pending_dispatch"`, `delivery_recipient: None`, `escalation_policy: "NOT_CONFIGURED"`, `acknowledgement_status: "NOT_CONFIGURED"`.
  - `backend/app/lims/workflows.py:303-318` — the API outcome is `status: "notification_pending"`, `clinician_notified: False`, and the detail text says recipient/escalation/acknowledgement await a clinical-owner decision and configured delivery worker.
  - `backend/app/lims/routes.py:2213-2229` — the route commits only the outbox event when status is `notification_pending`; it does not dispatch anything.
  - `backend/tests/unit/test_lims_critical_result_outbox.py:63-70` — the regression test asserts `notification_pending` and `clinician_notified is False`; it does not assert delivery.
  - Repository-wide search for `pending_dispatch` / `NOT_CONFIGURED` found the workflow/test sites only; no delivery worker or consumer was found in the checkout.
- **Affected components:** LIMS critical-result workflow, `/lims/workflows/critical-result/{result_id}`, transactional outbox, clinical-alert evidence, downstream notification platform integration.
- **Root cause:** The previous false-success hazard was correctly removed, but only the durable-intent half of the workflow was implemented. Recipient selection, escalation and acknowledgement are clinical-policy decisions, not engineering defaults, and no adapter consumes the queued event.
- **Safe-fix possible?** **No in Wave A.** The outbox emission and honest response are already correct. Adding delivery or escalation semantics would change clinical behaviour; it requires an approved policy and a worker/adapter design.
- **Approval required?** **Yes.** Clinical owner must define recipient, escalation and acknowledgement policy; orchestrator/A07/A09 must approve worker/contract changes. Until then, every response must remain `notification_pending` and must not be reported as “clinician alerted”.
- **SCOPE_REQUEST:** SR-A05-01.

---

### A05-002 — P0 — Auto-validation omits the documented QC gate and is invoked without patient/delta context

- **Evidence:**
  - `backend/app/lims/workflows.py:32-41` — the docstring lists five ordered checks, including “QC status check → blocks if instrument QC out-of-control”.
  - `backend/app/lims/workflows.py:61-166` — the implemented body performs only reference-range, critical, delta, auto-validation-rule and status determination. There is no QC query or QC-status branch; a repository search for `QC|qc|quality` in this file returns only the docstring at line 38.
  - `backend/app/lims/workflows.py:21-31` — `instrument_id` is accepted but unused after the function signature; `patient_age_days`, `patient_gender`, `previous_value` and `previous_days` are optional inputs that enable the documented checks.
  - `backend/app/lims/services.py:252-259` — `ResultService.create_result()` calls `auto_validate_result()` with only `value_numeric`, `test_code`, `lab_id` and `instrument_id`. It omits all four context inputs.
  - `backend/app/lims/routes.py:2158-2163` — the manual re-validation route repeats the same omission.
  - `backend/app/lims/workflows.py:147-150` — when no flags are present, the function can set `validation_status = "auto_validated"` and `auto_validated = True`.
  - `backend/app/lims/services.py:330-331` — the release service accepts `auto_validated` as release-eligible.
  - `backend/app/lims/routes.py:1346-1349` — the release route treats `auto_validated` as an already-validated sibling result; no instrument QC check exists in the release path (`backend/app/lims/routes.py:1364-1385`).
- **Affected components:** `ResultService.create_result()`, `run_auto_validation`, `ResultService.release()`, `/lims/results/{id}/release`, QC service/routes, all auto-validated patient results.
- **Root cause:** A documented fail-closed QC step was never implemented (or was removed), while the success branch remained permissive. The caller also passes insufficient demographic/delta context, so range/delta checks are selectively disabled in the primary create path.
- **Safe-fix possible?** **No in Wave A.** Introducing a QC gate or changing which results can be auto-validated/released is clinical logic. A technically small fix (query QC status by `lab_id`/`instrument_id`/`test_code` and block on out-of-control) must be designed and approved by the clinical owner, with A07/A09 contract and regression review.
- **Approval required?** **Yes.** Patient-safety logic and release eligibility; the file is also pre-existing user work (`M`) and must not be edited by A05.
- **SCOPE_REQUEST:** SR-A05-02.

---

### A05-003 — P1 — Result-correction helper records a correction but does not update the corrected value

- **Evidence:**
  - `backend/app/lims/workflows.py:372-379` — `execute_result_correction()` accepts `new_value` and `reason`.
  - `backend/app/lims/workflows.py:387-403` — after loading the tenant-scoped `Result`, the function only creates a `ResultValidation(action="corrected")` row; it never assigns to `result.value_numeric`, `result.value_text`, version or critical flags.
  - `backend/app/lims/workflows.py:405-409` — the function nevertheless returns `status: "corrected"`.
  - A repository-wide search for `execute_result_correction` found only the definition; no route, service or test calls it in this checkout. The defect is latent, not currently reachable through a registered endpoint.
  - Contrast with the synthetic (not production-active) implementation: `backend/app/health_core/lab/services.py:670-705` uses `replace(result, value=new_value, version=..., critical_flag=..., amendments=...)` and emits a `RESULT_CORRECTED` event.
- **Affected components:** LIMS correction workflow, `ResultValidation`, any future caller that assumes the return value means the stored result changed.
- **Root cause:** The helper records an intention/audit marker without applying the state transition it claims. The unused `new_value` parameter makes the function’s contract misleading.
- **Safe-fix possible?** **No in Wave A.** Correcting a clinical result requires an approved amendment model (old/new value, reason, actor, version, re-flags, event) and an owner decision about whether to wire or remove this dead helper. Reuse the existing Health Core amendment shape only as a design reference, not as production code.
- **Approval required?** **Yes.** Clinical correction semantics and result integrity; A07 for persistence/versioning and A09 for tests. The file is protected user work.
- **SCOPE_REQUEST:** SR-A05-03.

---

### A05-004 — P1 — Clinical AI evaluation declares safety metrics it does not compute; retrieval failures fail silently

- **Evidence:**
  - `backend/app/ai_fabric/evaluation.py:14-27` — `EvalMetric` declares `HALLUCINATION_RATE`, `CITATION_ACCURACY`, `SAFETY_SCORE`, `RELEVANCE`, `GROUNDEDNESS` and `HELPfulness`.
  - `backend/app/ai_fabric/evaluation.py:106` and `:135-149` — `_compute_metrics()` returns only `accuracy`, `avg_score`, `avg_latency_ms` and counts. None of the declared clinical/safety metrics is computed. The `accuracy` key is duplicated at lines 142-143.
  - `backend/app/ai_fabric/evaluation.py:117-126` — pass/score is substring containment or word-set overlap; an example with empty `expected_output` is automatically passed/scored 1.0 if there is any output.
  - `backend/tests/test_ai_evaluation.py:14-19` — the mock response is `Response to: {prompt}`; `:47-56` asserts an empty-expected example passes; `:58-70` checks suite registration only and asserts `"no_runs"`. No clinical safety metric is exercised.
  - `backend/app/ai_fabric/evaluation.py:230-247` — `ClinicalEvalSuite` contains two examples and registers a suite, but no clinical-owner-approved correctness oracle is present.
  - `backend/app/ai/rag_pipeline.py:152-181` — citation extraction requires the exact literal `[المصدر: ...]`; hallucination score is raw word overlap, not a clinical safety measurement.
  - `backend/app/ai/vector_store.py:158-184` — the non-pgvector fallback builds `lab_id = :lab` / `content_type = :ct` filters but executes the query without bound parameters, scores every row against a zero vector, and swallows all exceptions returning `[]`. Existing tests only assert that search returns a list (`backend/tests/test_ai_platform.py:62-67`).
- **Affected components:** AI evaluation harness, clinical accuracy/safety/groundedness suites, RAG pipeline citation and hallucination signals, vector search fallback, AI routes.
- **Root cause:** Metric names and suite registration were treated as evidence of evaluation. The scoring implementation measures string similarity, while the retrieval fallback can silently produce an empty context; both can make unsafe or ungrounded clinical answers look evaluated.
- **Safe-fix possible?** **Partially.** Engineering cleanup (remove duplicate key, bind fallback parameters, fail closed on retrieval error, compute the metrics that are actually defined) is feasible with existing libraries. Defining clinically meaningful pass criteria and thresholds is **not** a Wave A code task.
- **Approval required?** **Yes.** Clinical/AI owner must define approved metrics and acceptable thresholds; A09 must approve test oracles. No new commercial model/service is proposed.
- **SCOPE_REQUEST:** SR-A05-04.

---

### A05-005 — P2 — Terminology coverage is explicitly partial; do not use synthetic validators as release conformance evidence

- **Evidence:**
  - `backend/app/health_core/terminology/curated.py:3-12` — the sets are “deliberately small allowlists, NOT official release datasets”.
  - `backend/app/health_core/terminology/releases.py:40`, `:71`, `:106` — ICD-10, LOINC and UCUM coverage are all `PARTIALLY_VERIFIED`.
  - `backend/app/health_core/terminology/releases.py:73-86` — LOINC `2.81` is a declared runtime status value, not a verified release artefact; the official licensed dataset is absent; letter-prefixed codes are unverified.
  - `backend/app/health_core/terminology/validators.py:37-43` — the adapter uses a 3–6 digit LOINC pattern to accommodate curated `718-7` / `777-3`.
  - `backend/app/health_core/clinical/validation.py:23` — the offline clinical validator requires 4–6 digits; the discrepancy is documented but unresolved across validators.
  - `backend/app/health_core/terminology/curated.py:41`, `:43` — the two 3-digit codes are present in the curated set.
  - `backend/tests/health_core/test_quality_review_static.py:118-130` — the synthetic package is asserted not to be imported by `factory.py` or `main.py`; this is not a production terminology runtime.
- **Affected components:** Health Core terminology validators, release provenance records, clinical validation patterns, any future terminology conformance claim.
- **Root cause:** Offline development copied small code lists and documented their provenance honestly. No owned official release dataset exists in the checkout, and two local validators encode different LOINC structural rules.
- **Safe-fix possible?** **No in Wave A.** Resolving release versions, licence terms and canonical patterns is an owner/governance decision. No procurement is recommended here: free/open alternatives already present (curated allowlist, public Mod-10 check-digit algorithm) should be documented first; any licensed dataset needs a cost/licence exception.
- **Approval required?** **Yes.** Clinical terminology owner + governance; A05 must not change either validator family during Wave A.
- **SCOPE_REQUEST:** SR-A05-05.

---

## 3. Positive controls verified (not findings)

- Critical-result false success was removed: the workflow never returns `"alerted"` and tests pin honest delivery state (`backend/tests/unit/test_lims_critical_result_outbox.py:63-70`).
- Critical flags are persisted even when a result is not auto-validated (`backend/app/lims/routes.py:2165-2208`).
- Manual validation requires a signature and prevents re-validation of validated/released results (`backend/app/lims/services.py:280-306`).
- Release requires senior authority, verified specimen, linked-result validation, idempotency and expected version (`backend/app/lims/routes.py:1290-1385`).
- MPI unverified NID hashes are excluded from automatic claims and require review (reviewed in `backend/app/services/mpi/resolver.py`); hash-chain and advisory-lock code is present (`backend/app/services/mpi/reliability.py`).
- Health Core synthetic workflows have concrete tests for amendment value changes (`backend/tests/health_core/test_lab_results_verification.py:180-202`) but are structurally excluded from production startup.

---

## 4. SCOPE_REQUESTs

| ID | Request | Owner / approval needed |
|---|---|---|
| SR-A05-01 | Define critical-result recipient, escalation and acknowledgement policy; approve a delivery worker/adapter that consumes the existing outbox. Keep `notification_pending` until approved. | Clinical owner; orchestrator; A07/A09. |
| SR-A05-02 | Approve QC-gate semantics for auto-validation and decide whether release should hard-block on out-of-control QC and missing patient/delta context. | Clinical owner; A07; A09. Protected `lims/workflows.py`. |
| SR-A05-03 | Decide whether to wire, correct or remove `execute_result_correction()`; define amendment/version/re-flag contract. | Clinical owner; A07; A09. Protected file. |
| SR-A05-04 | Define clinical safety metrics, pass criteria and fail-closed retrieval behaviour for AI/RAG evaluation. | Clinical/AI owner; A09. |
| SR-A05-05 | Decide official terminology release/labelling and reconcile the 3–6 vs 4–6 digit LOINC rule; document free alternatives before any licence/cost exception. | Clinical terminology owner; governance. Protected untracked files. |

---

## 5. Orchestrator handoff

- **Wave C role:** A05 remains reviewer only. No clinical-logic change should be assigned to A05.
- **Blockers:** A05-001, A05-002 and A05-007 (companion report) are P0 and must be resolved or explicitly accepted before any clinical-workflow certification.
- **Cross-scope overlaps:** A07 owns backend/DB/API contracts; A04 owns identity/security aspects of MPI; A09 owns test oracles; A06 owns outbox/retry protocol evidence. A05 findings are report-only inputs to those owners.
