# AUTONOMOUS ENGINES VERIFICATION — Phase 3 (isolated synthetic execution)

**Repository / HEAD:** `gula-integration` · `integration/gula-unification-v1` @ `2827c1ff…` (unchanged)
**Date:** 2026-11-17 · **Category:** A (documentation-only) · **Change record:** CC-005
**Scope:** execution evidence for the 39 engines inventoried in `AUTONOMOUS_ENGINES_INVENTORY.md`.
**Verdict rule:** `VERIFIED` means *this audit executed and observed the named evidence*; it never
means runtime verification, migration-schema verification, clinical certification or production readiness.

---

## 1. Execution method and isolation guarantees

All seven batches used the single approved command form:

```bash
cd /home/samertts/workspace/projects/gula-integration/backend
ENV=test PYTHONPATH=.. /home/samertts/workspace/projects/gula-platform/backend/.venv/bin/python \
  -m pytest -q --no-header -p no:cacheprovider <listed test files>
```

| Guarantee | How it was enforced |
|---|---|
| Synthetic data only | Existing suites use in-memory / SQLite fixtures and synthetic records; no patient data introduced |
| Operational DB untouched | `ENV=test`; no connection to operational DB `gula`; no migration, DDL or `alembic stamp` |
| No repo code changed | Only `GOVERNANCE/*.md` written; `git status` delta unchanged apart from governance artifacts |
| No test weakening | No test file, fixture or conftest edited; existing tests executed as found |
| No full-suite rerun | Seven bounded batches only; W1 strict suite (E-001) and full suite (E-031) not rerun |
| Reproducible logs | Full stdout/stderr captured to `/tmp/opencode/nr011_activation/phase3_*.log` (E-046…E-052) |

The Python interpreter was borrowed read-only from the sibling `gula-platform` virtualenv (its only
role is to run this repository's tests); no file in `gula-platform` was modified.

## 2. Executed batches (E-046…E-052)

| E-ID | Log | Test files | Result | Exit |
|---|---|---|---|---|
| E-046 | `phase3_engine_tests.log` | `tests/kernel/test_scheduler.py`, `test_retry.py`, `test_retry_queue.py`, `test_outbox.py`, `test_event_bus.py`, `test_event_store.py`, `test_circuit_breaker.py`, `test_tenants.py`, `test_secrets.py`, `tests/test_offline_sync.py`, `test_device_outbox.py`, `test_abac.py`, `test_tenant_isolation_matrix.py`, `test_lims_tenant_isolation.py`, `test_lims_quality_authorization.py`, `test_ai_guardrails.py`, `test_fhir_interoperability_hardening.py`, `tests/unit/test_quality_control_service.py`, `test_metrics_service.py`, `test_idempotency.py` | **205 passed / 0 failed** (19 warnings, 99.57 s) | 0 |
| E-047 | `phase3_engine_tests2.log` | `tests/test_ai_platform.py`, `test_ai_integration.py`, `test_ai_fabric_access.py`, `test_ai_evaluation.py`, `test_fhir_comprehensive.py`, `test_fhir_r4_exchange.py`, `test_outbox_service.py`, `tests/kernel_hardening/test_observability.py`, `tests/test_observability_invariants.py`, `tests/test_risk_based_auth.py`, `test_niam_registry_authorization.py`, `test_governance_audit_authorization.py`, `test_national_governance_authorization.py`, `test_runtime_isolation.py`, `test_ai_platform_authorization.py` | **291 passed / 0 failed** (1 warning, 103.96 s) | 0 |
| E-048 | `phase3_workflow_tests.log` | `tests/test_identity_workflows_canonical.py`, `test_citizen_relationship_workflow.py`, `test_side_door_hardening.py`, `test_emergency_surgery_workflow_p0.py`, `test_icu_lab_workflow_p0.py`, `test_pharmacy_radiology_workflow_p0.py` | **65 passed / 0 failed** (1 warning, 72.39 s) | 0 |
| E-049 | `phase3_kernel_extra.log` | `tests/kernel/test_cron.py`, `test_locks.py`, `test_priority_queue.py`, `test_worker_pool.py` | **11 passed / 0 failed** (0.21 s) | 0 |
| E-050 | `phase3_national_workflow.log` | `app/national/tests/unit/test_workflows.py` | **9 passed / 0 failed** (0.10 s) | 0 |
| E-051 | `phase3_hl7.log` | `tests/test_fhir_interoperability.py` (includes synthetic HL7 ORU→FHIR conversion, lines 104–128) | **4 passed / 0 failed** (2 warnings, 72.27 s) | 0 |
| E-052 | `phase3_engine_tests3.log` | `tests/test_control_layer.py` (55), `tests/test_task_queue.py` (15), `tests/test_test_result_service.py` (19), `tests/test_document_intelligence.py` (62) | **155 passed / 0 failed** (56 warnings, 1.25 s) | 0 |

**Aggregate: 740 passed / 0 failed / 0 skipped (seven batches, all exit 0).**
Warnings are pre-existing dependency deprecations (Starlette/httpx TestClient, `datetime.utcnow`) and are recorded, not suppressed.
E-052 specifically converted four previously source-only engines (ENG-A09, ENG-A11, ENG-D03, ENG-B12)
to `UNIT_VERIFIED`; it did not touch any engine whose gap is recorded as F-066…F-072.

## 3. Per-engine verification mapping

| Engine | Evidence that exercised it | Resulting status |
|---|---|---|
| ENG-A01 canonical workflow | E-048 (65), E-050 (9) | `PARTIAL_VERIFIED` |
| ENG-A02 scheduler/retry/cron/pool | E-046 (scheduler/retry 6), E-049 (cron/pool 5) | `UNIT_VERIFIED` |
| ENG-A03 priority/task queues | E-046 (retry queue 2), E-049 (priority 3) | `UNIT_VERIFIED` |
| ENG-A04 distributed locks | E-049 (locks 3) | `UNIT_VERIFIED` |
| ENG-A05 event bus family | E-046 (event bus/outbox/store/retry 8) | `UNIT_VERIFIED` |
| ENG-A06 event recovery | none executed (no dedicated test found) | `SOURCE_PRESENT` |
| ENG-A07 rules runtime | none executed | `SOURCE_PRESENT` (F-066) |
| ENG-A08 policy runtime | none executed | `SOURCE_PRESENT` (F-066) |
| ENG-A09 core policy/risk | E-052 (`test_control_layer` 55) | `UNIT_VERIFIED` |
| ENG-A10 national expression engine | none executed | `SOURCE_PRESENT` (F-066) |
| ENG-A11 task queue/worker | E-052 (`test_task_queue` 15) | `UNIT_VERIFIED` |
| ENG-A12 generated scaffold | its own 3 trivial tests were read, not executed in a batch | `DORMANT` (F-071) |
| ENG-B01 RAG/vector | E-047 (`test_ai_platform` 85, `test_ai_integration` 22) | `INTEGRATION_VERIFIED` |
| ENG-B02 healthcare CDS | E-047 (CDS cases in `test_ai_integration`) | `INTEGRATION_VERIFIED` |
| ENG-B03 orchestrator/guardrails | E-046 (`test_ai_guardrails` 27), E-047 (`test_ai_evaluation` 8) | `UNIT_VERIFIED` |
| ENG-B04 AI-fabric RAG | E-047 (`test_ai_fabric_access` 4) | `INTEGRATION_VERIFIED` |
| ENG-B05 HL7→FHIR | E-051 (`test_fhir_interoperability` 4), E-046 (hardening 8) | `INTEGRATION_VERIFIED` |
| ENG-B06 FHIR resource/search | E-047 (`test_fhir_comprehensive` 14, `test_fhir_r4_exchange` 10) | `INTEGRATION_VERIFIED` |
| ENG-B07 MDM | none executed | `SOURCE_PRESENT` (F-067) |
| ENG-B08 health-data streaming | none executed | `SOURCE_PRESENT` |
| ENG-B09 national CDS engine | none executed | `UNVERIFIABLE` (F-068) |
| ENG-B10 outbox worker | E-047 (`test_outbox_service` 20); **background loop not runtime-observed** | `INTEGRATION_VERIFIED` |
| ENG-B11 search service | none executed | `SOURCE_PRESENT` |
| ENG-B12 document-intelligence wiring | E-052 (`test_document_intelligence` 62) | `UNIT_VERIFIED` |
| ENG-C01 rate limiter | none executed | `SOURCE_PRESENT` |
| ENG-C02 tenant helpers | E-046 (`test_tenant_isolation_matrix` 21) | `UNIT_VERIFIED` |
| ENG-C03 self-healing/circuit | E-046 (`test_circuit_breaker` 4), E-047 (`test_runtime_isolation` 8) | `UNIT_VERIFIED` |
| ENG-C04 offline sync engine | E-046 (`test_offline_sync` 20) | `UNIT_VERIFIED` |
| ENG-C05 offline sync service | E-046 (`test_offline_sync` 20) — LWW/timestamp/manual only; CRDT path not exercised | `PARTIAL_VERIFIED` (F-069) |
| ENG-C06 ABAC policy | E-046 (`test_abac` 7) | `UNIT_VERIFIED` |
| ENG-C07 canonical audit | E-047 (governance audit 6, national governance 19) | `INTEGRATION_VERIFIED` |
| ENG-C08 lab device gateway | none executed | `SOURCE_PRESENT` (F-070) |
| ENG-C09 national security rules | none executed | `SOURCE_PRESENT` |
| ENG-D01 Westgard QC | E-046 (`test_quality_control_service` 26) | `UNIT_VERIFIED` |
| ENG-D02 LIMS workflows | E-046 (LIMS isolation 5, quality auth 3) | `INTEGRATION_VERIFIED` |
| ENG-D03 test-result engine | E-052 (`test_test_result_service` 19) | `UNIT_VERIFIED` |
| ENG-D04 metrics engine | E-046 (`test_metrics_service` 16) | `UNIT_VERIFIED` |
| ENG-D05 runtime observability | E-047 (observability 6 + invariants 23) | `INTEGRATION_VERIFIED` |
| ENG-D06 certification engine | none executed | `SOURCE_PRESENT` (F-072) |

## 4. Score dimensions (VERIFIED / UNKNOWN / NOT APPLICABLE)

Legend: **V** = dimension present in source *and* exercised/observed by this audit; **U** = not
exercised here (no PASS inferred); **NA** = not applicable to that component (reason: pure function,
internal helper, or no state-changing path). Codes expand to the required vocabulary
`VERIFIED / UNKNOWN / NOT_APPLICABLE`. No numeric score is computed.

| Engine | Contract | Errors | Retry | Concurrency | Recovery | Authz/tenant | Idempotency | Tests |
|---|---|---|---|---|---|---|---|---|
| ENG-A01 | V | U | U | U | U | V | U | V |
| ENG-A02 | V | U | V | U | U | NA | U | V |
| ENG-A03 | V | U | V | V | U | NA | U | V |
| ENG-A04 | V | U | NA | V | U | NA | NA | V |
| ENG-A05 | V | V | V | U | U | NA | U | V |
| ENG-A06 | U | U | U | U | U | NA | U | U |
| ENG-A07 | U | U | U | U | U | U | U | U |
| ENG-A08 | U | U | U | U | U | U | U | U |
| ENG-A09 | V | V | U | U | V | V | U | V |
| ENG-A10 | U | U | U | U | U | U | U | U |
| ENG-A11 | V | U | V | U | U | NA | U | V |
| ENG-A12 | V | NA | NA | NA | NA | U | NA | V* |
| ENG-B01 | V | U | U | NA | U | V | NA | V |
| ENG-B02 | V | U | U | NA | U | V | NA | V |
| ENG-B03 | V | V | NA | NA | V | V | NA | V |
| ENG-B04 | V | U | U | NA | U | V | NA | V |
| ENG-B05 | V | V | NA | NA | NA | V | NA | V |
| ENG-B06 | V | V | NA | NA | NA | V | NA | V |
| ENG-B07 | U | U | U | U | U | U | U | U |
| ENG-B08 | U | U | U | U | U | U | U | U |
| ENG-B09 | U | U | U | U | U | U | U | U |
| ENG-B10 | V | V | V | U | U | NA | U | V |
| ENG-B11 | U | U | U | U | U | U | U | U |
| ENG-B12 | V | V | U | U | V | U | U | V |
| ENG-C01 | U | U | U | U | U | U | U | U |
| ENG-C02 | V | U | NA | NA | NA | V | NA | V |
| ENG-C03 | V | V | V | U | V | NA | NA | V |
| ENG-C04 | V | U | U | NA | U | NA | U | V |
| ENG-C05 | V | V | U | V | U | NA | U | V |
| ENG-C06 | V | U | NA | NA | NA | V | NA | V |
| ENG-C07 | V | U | NA | U | U | V | NA | V |
| ENG-C08 | U | U | U | U | U | U | U | U |
| ENG-C09 | U | U | U | U | U | U | U | U |
| ENG-D01 | V | V | NA | NA | NA | NA | NA | V |
| ENG-D02 | V | V | U | U | V | V | U | V |
| ENG-D03 | V | V | U | U | U | U | U | V |
| ENG-D04 | V | V | NA | NA | U | NA | NA | V |
| ENG-D05 | V | U | NA | U | U | NA | NA | V |
| ENG-D06 | U | U | U | U | U | U | U | U |

\* ENG-A12's tests assert only trivial `success=True` / `validate=True`; `V` here means *those trivial
assertions ran/read*, not functional verification. Its status remains `DORMANT`.

## 5. Error / retry / concurrency / recovery / permission examination (source + tests)

- **Errors:** event bus DLQ/outbox tests (E-046), guardrail violation tracking (E-046/047), invalid HL7
  rejection (E-046), FHIR error mapping (E-047), self-healing circuit opening (E-046) and DB/Redis
  ping failure paths (E-046). Nine permissive `except (ValueError, TypeError): … pass / return True`
  paths in `app/national/services/cds_engine.py` (lines 635, 669, 679, 689, 699, 756, 769, 782, 798)
  were found by source inspection; **not exercised**, and no behavior change made (F-068).
- **Retry/backoff:** `JobRetry.should_retry/increment/get_backoff` (E-046), event retry queue (E-046),
  outbox retry tests (E-047), circuit-breaker retry policy (E-046). No Redis-backed or cross-process
  retry durability was claimed or tested.
- **Concurrency:** `DistributedLockManager`, `PriorityQueue`, `WorkerPool` tests (E-049) exercise
  in-process behavior only. Multi-worker / cross-process locking remains `UNKNOWN`.
- **Recovery:** event replay/DLQ/recovery sources read (ENG-A05/A06); outbox worker wired in
  `app/core/startup.py:270-272` and `app/worker.py:86-100`; the loops themselves were **not**
  runtime-observed. Rollback remains unsafe on the partial path (F-012/B-010) — unchanged here.
- **Permissions:** workflow routes require an authenticated user and side-door hardening tests pass
  (E-048); AI platform authorization (E-047), LIMS quality/tenant authorization (E-046) and ABAC
  (E-046) pass in isolation. These are **authorization**, not authentication substitution, and do
  not constitute D-020 sign-off. National CDS routes are collected in `national_router` but not
  mounted by `app/factory.py` in the observed wiring — no exposure claim is made.

## 6. Not verified / blocked (explicit)

| Component | Why not verified | Recorded as |
|---|---|---|
| ENG-B09 national CDS engine | no dedicated suite; 9 permissive error paths; clinical behavior change requires clinical-safety authority; route not mounted | `UNVERIFIABLE` — F-068, D-021 PENDING |
| ENG-A07/A08/A10 rules & policy runtimes | wired into kernel/national routes but no dedicated test module found; adding tests = category B | `SOURCE_PRESENT` — F-066 |
| ENG-B07 MDM, ENG-C08 device gateway, ENG-D06 certification | no dedicated behavioral tests found | `SOURCE_PRESENT` — F-067/F-070/F-072 |
| All 39 engines | no booted-app run, no migration-only schema run, no production evidence | `RUNTIME_VERIFIED 0`, `PRODUCTION_VERIFIED 0` |
| Strict W1 gate | still FAILED 119/872 (E-001); no trigger to rerun; 740 targeted passes are a **different corpus** | unchanged — B-007 |

## 7. Baseline comparison and regression statement

- The 740-test targeted corpus is **not** comparable to E-001 (872 strict tests on migration-built
  PG16) or E-031 (3,480 full-suite tests): different test sets, different schema, different purpose.
  No regression or improvement against those baselines is claimed.
- Zero failures were added by this audit; no existing test was edited; therefore no new regression
  was introduced by the documentation-only work.
- F-010/NR-011 evidence (E-041…E-045, 36 passed) is not re-executed here — no new evidence of a
  defect appeared, so the duplicate-prevention rule `REUSE_EXISTING_EVIDENCE` applies.

**Bottom line:** 39 engines discovered; 24 executed here (9 integration + 15 unit, the latter
including the four engines promoted by E-052), 2 partially verified, 11 source-only, 1 dormant,
1 unverifiable; **0 runtime-verified, 0 production-verified**.
No repair was applied to any engine; all candidate remediations need the approvals listed in
`AUTONOMOUS_ENGINES_REMEDIATION_PLAN.md`.
