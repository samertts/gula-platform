# Team A — Clinical Safety Hazard Register (A3)

**Audit ID:** A3
**Date:** 2026-11-18
**Repository:** `gula-integration`
**Audited ref:** working tree at HEAD `2206654dc713ea2de8c564a3207dfe05fde23549`
**Mode:** read-only adversarial hazard identification; synthetic/static evidence only.
**Companion artifacts:** `MPI_AND_IDENTITY_AUDIT.md`, `FINDINGS_A3_MPI_CLINICAL.json`.

---

## 1. Scope and safety boundary

This register covers hazards in: MPI patient identity linkage, LIMS auto-validation, critical-result escalation, and pharmacy clinical rule selection. It records **control gaps and potential harm** only. It does **not** endorse, activate, or recommend any clinical decision-support output, AI treatment suggestion, medication choice, or patient-management action. No clinical owner decision is made here.

**Evidence limits:** no DB connection, runtime HTTP call, network access, test execution, real patient record, or secret was used. Reproductions are synthetic designs derived from static source inspection. Verification evidence below is therefore static/design evidence, not runtime proof.

**Rating scale:**

- **Severity:** potential harm if the hazard occurs — `CRITICAL`, `HIGH`, `MEDIUM`, `LOW`.
- **Probability:** static exposure estimate — `HIGH` (default path), `MEDIUM` (reachable under common conditions), `LOW` (latent or narrow).
- **Detectability:** ability of current controls to detect the hazard before harm — `LOW` means little or no durable signal; `MEDIUM` means partial signal; `HIGH` means strong signal.
- **Risk class:** conservative composite of the three ratings; not a formal clinical risk acceptance.

---

## 2. Hazard register

| Hazard ID | Linked finding | Workflow | Potential harm | Severity | Probability | Detectability | Risk class | Preventive controls required | Detection controls required | Recovery controls required | Verification evidence |
|---|---|---|---|---|---|---|---|---|---|---|---|
| H-MPI-001 | AUD-MPI-001 | MPI resolve / canonical claim | A lab patient is auto-linked to another person's canonical identity from an unverified NID; results, demographics, and future encounters attach to the wrong patient. | HIGH | MEDIUM | LOW | HIGH | Require authoritative NID verification before `nid_exact` score `1.0`; downgrade unverified hits to review when demographics conflict; persist verification provenance; do not copy disputed identifiers on reject. | Monitor rate of `nid_exact` claims where `nid_verified=False`; alert on NID/name/DOB disagreement; periodic synthetic negative-match probes. | Quarantine affected claims, re-open review with human adjudication, unlink/relink under advisory lock and chained audit, notify downstream LIMS consumers of corrected identity. | `backend/app/services/mpi/resolver.py:420-430`, `:476-480`; `backend/app/services/mpi/models.py:79`; no `nid_verified=True` assignment in MPI write paths. Synthetic repro/falsification in JSON finding AUD-MPI-001. |
| H-CLIN-001 | AUD-CLIN-001 | Critical-result notification | A critical/panic result is marked `alerted` with `action=notify_ordering_physician`, but no notification, event, outbox row, or audit record is produced; treating clinician is never informed. | CRITICAL | MEDIUM | LOW | CRITICAL | Implement transactional outbox/event emission with durable delivery attempt and read/ack state; fail the endpoint if no notification is enqueued; define owner-approved recipient and escalation policy. | Alert on critical results with zero notification/outbox rows; reconcile response `status=alerted` against durable delivery records; monitor undelivered/expired alerts. | Manual re-notification with timestamped audit; result quarantine until acknowledged; incident review of missed-alert window; never silently mark delivered. | `backend/app/lims/workflows.py:221-259` returns success metadata only; `backend/app/lims/events.py:113-114` defines `CriticalResultDetected` but grep found no emitter/call; `backend/app/lims/routes.py:2174-2183` returns the no-op result. Module docstring `workflows.py:1-5` promises events/outbox. |
| H-CLIN-002 | AUD-CLIN-002 | LIMS auto-validation / reference interval selection | Pediatric, neonatal, or sex-specific results are checked against an adult or wrong-sex interval; abnormal/critical values can be auto-validated as normal or receive the wrong flag. | HIGH | HIGH | MEDIUM | HIGH | Derive and pass `patient_age_days` and `patient_gender` from the patient record on every auto-validation path; fail closed when a required demographic-specific range is absent; pin range-selection rules with tests. | Assert selected `ReferenceRangeDef` matches patient demographics; log chosen range id and filter inputs; monitor auto-validated results with missing demographics. | Re-evaluate affected results with correct ranges, withdraw incorrect release state, re-issue corrected report, audit all revalidations. | `backend/app/lims/workflows.py:21-31` exposes gender/age arguments but `:70-88` only filters when supplied and orders by non-null specificity; both call sites omit them: `backend/app/lims/routes.py:2158-2163` and `backend/app/lims/services.py:252-259`. No targeted range-selection test found. |
| H-CLIN-003 | AUD-CLIN-003 | Auto-validation → critical-alert handoff | Auto-validation reports `critical_high`/`critical_low` in its response, but the route does not persist `Result.is_critical`, `flag`, or validation status; the subsequent critical-result endpoint returns `skipped` because `is_critical` is false. | HIGH | MEDIUM | LOW | HIGH | Centralize validation application so one code path persists all flags/status fields before commit; require critical flags to set `Result.is_critical=true`; block release while persistence is incomplete. | Post-commit assertion that any `critical_*` response flag has a matching persisted `is_critical` and audit row; synthetic endpoint-pair test. | Re-run validation and critical workflow for affected result, force manual escalation, record correction in audit; do not rely on the earlier `skipped` response. | `backend/app/lims/workflows.py:103-108` creates critical flags in the returned dict; `backend/app/lims/routes.py:2165-2169` persists only `validation_status`, `auto_validated`, and `auto_validated_at`; `backend/app/lims/workflows.py:245-246` skips when `Result.is_critical` is false. Contrast: `backend/app/lims/services.py:266-272` does persist flags. |
| H-CLIN-004 | AUD-CLIN-004 | Pharmacy interaction/allergy/contraindication/dose checks | Engines accept a `lab_id` but never filter clinical rules by it; `.first()` or unfiltered `.all()` can return another tenant's rule or an arbitrary conflicting rule, producing missed interactions or unsafe advice. | HIGH | MEDIUM | LOW | HIGH | Apply tenant/lab filter on every clinical rule query; add deterministic ordering and source/version pinning; reject ambiguous rule sets instead of choosing `.first()`; scope all rule reads to the caller's lab. | Cross-tenant synthetic tests with conflicting rules; assert returned rule `lab_id` equals caller `lab_id`; log rule id/version for every check. | Suspend affected rule set, re-run checks under correct tenant scope, review any dispense/order decisions made from the wrong rule, audit correction. | `backend/app/pharmacy/clinical.py:23-40` stores `lab_id` but query has no lab/tenant predicate and uses `.first()`; same pattern at `:100-110`, `:142-152`, `:198-237`, `:281-284`; classes derive from `TenantAuditEntity` (`backend/app/pharmacy/base.py:66`) whose `TenantMixin` adds only a `lab_id` column (`shared/models/base.py:25-26`), not automatic filtering; routes pass `user.lab_id` at `backend/app/pharmacy/routes.py:1061-1116`. |

---

## 3. Cross-hazard observations

1. **False-success pattern:** H-CLIN-001 and H-CLIN-003 both return a success/skip state that is not backed by a durable downstream action. Response-level success must not be treated as evidence of notification or persistence.
2. **Context loss at call boundaries:** H-CLIN-002 shows that a correctly implemented engine can still be unsafe when the caller omits patient context. Controls must assert required inputs at the boundary, not rely on optional arguments.
3. **Identity-to-clinical coupling:** H-MPI-001 can make every downstream clinical hazard worse because a correct result attached to the wrong patient is clinically equivalent to a wrong result for the intended patient.
4. **Dormancy is not absence of risk:** all hazards are reachable from existing route/service code or from an identified latent helper; none requires activating unfinished functionality.
5. **No owner decision inferred:** escalation recipient lists, reference-interval source of truth, and formulary rule ownership remain with the relevant clinical/data owners. This register only states required controls.

---

## 4. Disposition

No hazard in this register is closed, downgraded, or accepted. The protected release decision remains **HOLD** and the MPI verdict remains **REJECT**. No elevated assurance status was awarded to any workflow. All reproductions and falsification criteria are synthetic and are specified in `GOVERNANCE/ADVERSARIAL_ASSURANCE/FINDINGS_A3_MPI_CLINICAL.json`.
