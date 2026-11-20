# 10 — Clinical Safety Evidence — GULA-NATIONAL-COMPLETION-013

## Scope

Critical-result identity contract, result integrity, clinical thresholds, and result delivery policy.

## Methodology

Source reproduction from `main`, targeted fix design, and regression testing on the isolated branch. No clinical policy, recipient list, response window, or threshold is invented.

## Environment

Isolated clone; synthetic results only.

## Commands and exit codes

Baseline inspection commands are recorded in `evidence/critical_defect_research.md`. Implementation commands will be appended to `evidence/implementation_log.md`.

## Evidence paths

- `evidence/critical_defect_research.md` section 1
- `evidence/implementation_log.md`
- `11_OFFLINE_AND_DISTRIBUTED_EVIDENCE.md`

## Findings

- NC013-C01: critical-result ID contract broken — `NOT FIXED` at baseline.
- Inherited finding: ~120 unapproved clinical/QC values — not re-executable here; remains human-gated.
- AUD-CLIN-001: clinical delivery blocked pending approved recipient/escalation/acknowledgement policy.

## Verification state

`HUMAN APPROVAL REQUIRED` for clinical activation; `NOT VERIFIED` for end-to-end delivery.

## Limitations

- Fixing the ID contract does not authorize a notification workflow.
- No qualified clinical reviewer is assigned in this program.

## Residual risks

- Wrong-patient critical alert remains possible until C01 is fixed and independently verified.
- Unapproved values must not silently become production rules.

## Required actions

1. Namespace result IDs by source table and refuse ambiguous consumers.
2. Keep critical-result delivery disabled until policy is approved.
3. Route thresholds and mappings to the human approval register.

## Execution update — 2026-11-20

Implemented the critical-result identity contract only:

- Namespaced references carry `result_store` (`lab_results` or `lims_results`) plus the source-table `result_id`.
- Producers emit the namespace; LIMS consumer requires it and fails closed on bare/legacy IDs.
- `lims/routes.py` accepts the store as an explicit query parameter.

Evidence:

- `evidence/test_logs/focused_nc013_py312_driftclosed.log` — 9 critical-result tests passed on Python 3.12 (22 focused tests total).
- `evidence/test_logs/focused_nc013_py310_driftclosed.log` — 9 critical-result tests passed on Python 3.10 (17 focused tests total).
- Event registry schemas `ResultPublished`, `ResultAmended`, `CriticalAlertTriggered` now forbid bare `result_id` and require `result_store` with a conditional namespaced ID; the critical-alert API and order-time `RESULT_CRITICAL` event also carry the namespaced reference.
- `evidence/implementation_log.md` — exact commands and change inventory.

No live event subscriber is wired while `AUD-CLIN-001` is `BLOCKED`; the tested consumer path fails closed on ambiguous payloads.

Verification state: **ENGINEERING FIX LOCALLY TESTED; INDEPENDENT VERIFICATION IN PROGRESS**. Critical-result notification delivery remains disabled and clinical policy, recipient, escalation, and acknowledgement rules remain human-owned and `BLOCKED`.
