# AUTONOMOUS ENGINES INVENTORY — Phase 3 (GULA approval activation)

**Repository:** `/home/samertts/workspace/projects/gula-integration`
**Branch / HEAD:** `integration/gula-unification-v1` @ `2827c1ff1032918aa2541aa0b47bb7f2e5d6cac0` (unchanged)
**Date:** 2026-11-17 · **Category:** A (documentation-only, append-only) · **Change record:** CC-005
**Companions:** `AUTONOMOUS_ENGINES_VERIFICATION.md` · `AUTONOMOUS_ENGINES_FINDINGS.md` ·
`AUTONOMOUS_ENGINES_REMEDIATION_PLAN.md` · `AUTONOMOUS_ENGINES_DEPENDENCY_MAP.md`
**Status of `GOVERNANCE/FINAL_DECISION.md`:** **HOLD** (md5 `effdfeaf…`, unchanged).
**Mandate:** resume task §2 — read-only, bounded discovery of engines that exist in this repository;
no new engine is created merely to fill a gap; no production/runtime claim without authorized evidence.

---

## 1. Classification system (the ten statuses used in this report)

This audit uses one fixed ten-status vocabulary. Status **7–9 are never assigned in this report**:
no runtime observation and no production evidence were produced or authorized here. "Code exists"
is deliberately distinct from "unit verified", "integration verified", "runtime verified" and
"production verified".

| # | Status | Meaning | Minimum evidence required to assign it |
|---:|---|---|---|
| 1 | `SOURCE_PRESENT` | Real source file(s) located and read; no behavioral test for this component was executed in this audit | path + entry point read from source |
| 2 | `UNIT_VERIFIED` | Isolated synthetic unit tests executed here and passed | log + test count, SQLite in-memory harness, no operational DB |
| 3 | `INTEGRATION_VERIFIED` | Isolated synthetic integration tests executed here and passed (TestClient / DB fixtures) | log + test count; still **not** runtime or production verification |
| 4 | `PARTIAL_VERIFIED` | Only a subset of the component's paths executed; the remainder stays UNKNOWN | log + explicit scope note naming the untested paths |
| 5 | `BROKEN` | A defect was reproduced by an executed test or deterministic reproduction | failing log or deterministic repro; never inferred from reading alone |
| 6 | `DORMANT` | Source exists but has no external references or is not mounted; deliberately not activated | reference/mount scan recorded |
| 7 | `RUNTIME_VERIFIED` | Exercised in a booted application/worker with live runtime observation | **not claimed in this audit** |
| 8 | `PRODUCTION_VERIFIED` | Exercised under authorized production evidence | **not claimed in this audit** |
| 9 | `UNVERIFIABLE` | Verification blocked by a missing dependency, decision or authorization; no PASS inferred | blocker/finding ID and reason |
| 10 | `NOT_APPLICABLE` | A scoring dimension does not apply to the component (used only in the dimension matrix) | reason in matrix note |

*Status numbering follows the mandate's "ten statuses" requirement; the widely used label order is
`SOURCE_PRESENT / UNIT_VERIFIED / INTEGRATION_VERIFIED / PARTIAL_VERIFIED / BROKEN / DORMANT /
UNVERIFIABLE / NOT_APPLICABLE / RUNTIME_VERIFIED / PRODUCTION_VERIFIED`. Status counts in this
report use the labels, never the row numbers, to avoid ambiguity.*

**Score dimensions** (scored per engine in `AUTONOMOUS_ENGINES_VERIFICATION.md §4`):
contract/interface · error handling · retry/backoff · concurrency/locking · recovery/fail-safe ·
authorization/tenant · idempotency · existing test coverage. Each cell is
`VERIFIED` (evidence from this audit) · `UNKNOWN` (not exercised here) · `NOT_APPLICABLE` (with reason).
No numeric quality score is invented.

## 2. Discovery method and boundaries

- Sources read in `backend/app/**` with bounded `find`/`grep` on real files only; no generative assumptions.
- Entry points taken from actual imports, `app/factory.py` router registration, `Bootloader` phases,
  `app/core/startup.py`, `app/worker.py`, and capability/route modules.
- Existing tests located by filename and symbol search; only seven bounded targeted batches were
  executed (E-046…E-052, 740 tests total). A test file that exists but was not executed is reported as
  `SOURCE_PRESENT`, never as verified here.
- Operational DB `gula` and `gula-platform` were not touched. All execution used the SQLite test
  harness with synthetic data (`ENV=test PYTHONPATH=..`). No DDL, migration, fixture, conftest or
  production module was edited.

## 3. Category A — workflow / orchestration / rules / decision engines

| ID | Engine (source) | LOC | Entry points / wiring | Key dependencies | Existing tests (executed here unless noted) | Status |
|---|---|---:|---|---|---|---|
| ENG-A01 | Canonical workflow engine `app/workflows/engine.py` | 237 | `app/identity/api/router.py:59` (`workflows_routes`), `app/national/workflows/base.py` and referral/encounter/registration workflows | Kernel, RBAC, DB session | `test_identity_workflows_canonical.py` 10, `test_citizen_relationship_workflow.py` 5, `test_side_door_hardening.py` 6, 4 P0 workflow files (E-048: 65 passed total) | `PARTIAL_VERIFIED` |
| ENG-A02 | Background scheduler + retry + cron + worker pool `app/kernel/background/{scheduler,job_retry,cron,worker_pool}.py` | 36/32/29/23 | `Bootloader._phase_initialize_background` (`app/kernel/runtime/bootloader.py:30,135`); `KERNEL_ENABLE_BACKGROUND` gate | `DistributedLockManager`, `JobRetry`, Kernel | `tests/kernel/test_scheduler.py` 4, `test_retry.py` 2, `test_cron.py` 3, `test_worker_pool.py` 2 (E-046, E-049) | `UNIT_VERIFIED` |
| ENG-A03 | Priority + task queues `app/kernel/background/{priority_queue,task_queue}.py` | 53/49 | Bootloader background phase | `PriorityTask`, `Task`, `JobRetry` | `tests/kernel/test_priority_queue.py` 3, `test_retry_queue.py` 2 (E-046, E-049) | `UNIT_VERIFIED` |
| ENG-A04 | Distributed locks `app/kernel/background/distributed_locks.py` | 47 | `Scheduler.__init__` (`distributed_locks` field) | in-process lock state | `tests/kernel/test_locks.py` 3 (E-049) | `UNIT_VERIFIED` |
| ENG-A05 | Event bus family `app/kernel/event_bus/{bus,outbox,retry_queue,dead_letter_queue,store,replay}.py` | 52/57/41/40/27/23 | `Bootloader` line 131 (`EventBus(self.kernel)`); consumers in `app/services/outbox_service.py` and national scheduling/observability/document/rules services | Kernel, outbox, DB session | `tests/kernel/test_event_bus.py` 2, `test_outbox.py` 2, `test_event_store.py` 2, `test_retry_queue.py` 2 (E-046) | `UNIT_VERIFIED` |
| ENG-A06 | Event recovery `app/kernel/event_bus/recovery.py` | 214 | EventBus recovery path (`RecoveryEngine`) | EventStore, DLQ, retry queue | no dedicated test module located; reached only indirectly by the event-bus batch (E-046) | `SOURCE_PRESENT` |
| ENG-A07 | Rules runtime `app/kernel/rules_runtime.py` | 299 | `app/kernel/runtime_routes.py`, `app/kernel/runtime_integration.py` | Kernel rule registry, DB | **no dedicated test module found** → F-066 | `SOURCE_PRESENT` |
| ENG-A08 | Policy runtime `app/kernel/policy_runtime.py` | 220 | `app/kernel/runtime_routes.py`, `app/kernel/runtime_integration.py` | Policy engine, Kernel | **no dedicated test module found** → F-066 | `SOURCE_PRESENT` |
| ENG-A09 | Control-layer policy + risk `app/core/{policy_engine,risk_engine}.py` | 275/145 | control-plane routes / repair assessment | `ActionType`, `RiskLevel`, `PolicyDecision` | `tests/test_control_layer.py` 55 (E-052) | `UNIT_VERIFIED` |
| ENG-A10 | National rules expression engine `app/national/rules_engine/domain/expression_engine.py` | 200 | `app/factory.py:692` includes national rules router | national rules domain, DB | no dedicated test module found → F-066 | `SOURCE_PRESENT` |
| ENG-A11 | Task queue / worker `app/tasks/{queue,worker}.py` | 168/157 | task queue factory called by worker process | `build_queue`, Redis-backed queue, retry | `tests/test_task_queue.py` 15 (E-052) | `UNIT_VERIFIED` |
| ENG-A12 | Generated capability scaffold `app/capabilities/workflow_engine/` (service 24, routes 51, capability 51, repository 48, entities 15) | 189 total | **no references outside its own directory** (grep over `app/**/*.py`) | generated base classes | `tests/test_unit.py` 2 + `test_integration.py` 1 assert trivial `success=True` / `validate=True` | `DORMANT` (F-071) |

## 4. Category B — AI / RAG / FHIR / event / data engines

| ID | Engine (source) | LOC | Entry points / wiring | Key dependencies | Existing tests (executed here unless noted) | Status |
|---|---|---:|---|---|---|---|
| ENG-B01 | RAG pipeline + vector store `app/ai/{rag_pipeline,vector_store}.py` | 184/231 | `app/routes/ai.py` (`ai_routes` in feature routes) | `VectorStore`, `generate_chat` gateway | `test_ai_platform.py` 85, `test_ai_integration.py` 22 (E-047: 291 passed batch) | `INTEGRATION_VERIFIED` |
| ENG-B02 | Healthcare CDS `app/ai/healthcare_cds.py` | 143 | `app/routes/ai.py` CDS endpoints | RAG pipeline, guardrails | `test_ai_integration.py` CDS cases (E-047) | `INTEGRATION_VERIFIED` — output safety **not certified** (D-021 pending) |
| ENG-B03 | AI orchestrator + guardrails `app/ai/{orchestrator,guardrails}.py` | 164/180 | AI routes, sandbox approval flow | approval store, guardrail registry | `test_ai_guardrails.py` 27 (E-046), `test_ai_evaluation.py` 8 (E-047) | `UNIT_VERIFIED` |
| ENG-B04 | AI-fabric RAG `app/ai_fabric/rag.py` | 436 | `ai_platform_routes` (`app/factory.py:611`) | vector DB abstraction, embeddings | `test_ai_fabric_access.py` 4 (E-047) | `INTEGRATION_VERIFIED` |
| ENG-B05 | HL7 ORU→FHIR `app/capabilities/fhir_interoperability/hl7.py` | 157 | FHIR interoperability route (`/fhir-interoperability/hl7/convert`) | `HL7Message`, `to_fhir_bundle` | `test_fhir_interoperability.py` 4 (E-051), `test_fhir_interoperability_hardening.py` 8 (E-046) | `INTEGRATION_VERIFIED` |
| ENG-B06 | FHIR resource service + search `app/capabilities/fhir_interoperability/service.py`, `app/national/fhir/search.py` | 122/56 | FHIR capability router, national FHIR search | FHIR R4 models | `test_fhir_comprehensive.py` 14, `test_fhir_r4_exchange.py` 10 (E-047) | `INTEGRATION_VERIFIED` |
| ENG-B07 | MDM service + matching `app/health_data/mdm/{service,matching}.py` | 132/318 | health-data MDM API | `ExactMatcher`, `FuzzyMatcher`, `ProbabilisticMatcher` | **no dedicated behavioral test** (only a metadata-import reference in E-045) → F-067 | `SOURCE_PRESENT` |
| ENG-B08 | Health-data streaming `app/health_data/streaming/pipeline.py` | 150 | `national_streaming_routes` (`app/factory.py:721-722`) | `EventBusSource`, `StreamProcessor`, filters | no dedicated test module located | `SOURCE_PRESENT` |
| ENG-B09 | National CDS engine `app/national/services/cds_engine.py` | 983 | route module `app/national/api/routes/cds.py` exists in `national_router`, **not mounted by `app/factory.py`** in observed wiring | DB session, drug/allergy/guideline rules | **no dedicated test suite found**; 9 permissive swallowed-exception paths → F-068 | `UNVERIFIABLE` (F-068) |
| ENG-B10 | Outbox worker `app/services/outbox_service.py` | 249 | `app/core/startup.py:270-272`, `app/worker.py:86-100` (`OutboxWorker.background_loop`) | DB session, event outbox | `test_outbox_service.py` 20 (E-047) | `INTEGRATION_VERIFIED` (the background loop itself was **not** runtime-observed) |
| ENG-B11 | Search service `app/capabilities/search_service/search.py` + national search routes | 60 + routes | `app/factory.py:712` (`search_router`) | `DefaultSearchService`, indexer | tests exist but **not executed in this audit** | `SOURCE_PRESENT` |
| ENG-B12 | Document-intelligence wiring `app/document_intelligence/application/wiring.py` | 1054 | document-intelligence capability composition | search, PDF adapter, events | `test_document_intelligence.py` 62 (E-052) | `UNIT_VERIFIED` |

## 5. Category C — security / governance / offline / resilience engines

| ID | Engine (source) | LOC | Entry points / wiring | Key dependencies | Existing tests (executed here unless noted) | Status |
|---|---|---:|---|---|---|---|
| ENG-C01 | Rate limiter `app/security/rate_limit.py` | 249 | security middleware / factory | `RateLimiter`, client-IP resolution | dedicated tests **not executed in this audit** | `SOURCE_PRESENT` |
| ENG-C02 | Tenant/collection policy helpers `app/security/policy.py` | 50 | used by security + data access layers | `tenant_collection`, `sanitize_request_id` | `test_tenant_isolation_matrix.py` 21 (E-046) | `UNIT_VERIFIED` |
| ENG-C03 | Self-healing + circuit breakers `app/core/self_healing.py`, `app/kernel/gateway/{circuit_breaker,rate_limiting}.py` | 459/71/32 | `DegradedModeMiddleware` in `app/factory.py`; `app/core/self_healing.py` | `CircuitBreaker`, `DegradationLevel` | `tests/kernel/test_circuit_breaker.py` 4 (E-046), `test_runtime_isolation.py` 8 (E-047) | `UNIT_VERIFIED` |
| ENG-C04 | Offline sync engine `app/core/sync_engine.py` | 102 | offline sync call sites | `SyncEvent`, `OfflineSyncEngine` | `test_offline_sync.py` 20 (E-046) | `UNIT_VERIFIED` |
| ENG-C05 | Offline sync service / conflict resolution `app/services/offline_sync_service.py` | ~260 | offline sync API | `ConflictResolution` enum, operation log | `test_offline_sync.py` 20 (E-046) covers LWW/timestamp/manual; **`CRDT_MERGE` path not covered** → F-069 | `PARTIAL_VERIFIED` |
| ENG-C06 | ABAC / identity policy `app/identity/policy_engine.py` | 129 | identity authorization path | `PolicyContext`, `PolicyEngine` | `test_abac.py` 7 (E-046) | `UNIT_VERIFIED` |
| ENG-C07 | Canonical audit `app/identity/services/canonical_audit.py` | 260 | audit routes + governance authorization | hash chain, redaction | `test_governance_audit_authorization.py` 6, `test_national_governance_authorization.py` 19 (E-047) | `INTEGRATION_VERIFIED` — append-only trigger behavior **not** verified on migrated schema (F-008) |
| ENG-C08 | Lab device gateway `app/gateways/lab_device_gateway.py` | 219 | HL7/analyzer ingress | HL7 parser, result service | **no direct test module found** → F-070 | `SOURCE_PRESENT` |
| ENG-C09 | National security rules `app/national/security/{guardian_rules,foreign_patient_rules}.py` | 40/32 | national security services | `GuardianRule`, foreign-patient policy | no dedicated test module located | `SOURCE_PRESENT` |

## 6. Category D — laboratory automation / monitoring / platform operations

| ID | Engine (source) | LOC | Entry points / wiring | Key dependencies | Existing tests (executed here unless noted) | Status |
|---|---|---:|---|---|---|---|
| ENG-D01 | Westgard QC engine `app/services/quality_control_service.py` | 292 | QC routes (`app/factory.py` advanced routes) | QC rules, DB | `tests/unit/test_quality_control_service.py` 26 (E-046) | `UNIT_VERIFIED` |
| ENG-D02 | LIMS workflow automation `app/lims/workflows.py` | 349 | results/samples routes, LIMS quality routes | `auto_validate_result`, `process_critical` | `test_lims_tenant_isolation.py` 5, `test_lims_quality_authorization.py` 3 (E-046) | `INTEGRATION_VERIFIED` |
| ENG-D03 | Test-result engine `app/services/test_result_service.py` | 437 | `app/routes/test_results.py` (core routes) | result validation, Westgard flags, audit | `test_test_result_service.py` 19 (E-052) | `UNIT_VERIFIED` |
| ENG-D04 | Metrics engine `app/services/metrics_service.py` + `app/routes/metrics.py` | 544/343 | metrics routes (`core_routes`) | DB ping, Redis ping, Prometheus | `tests/unit/test_metrics_service.py` 16 (E-046) | `UNIT_VERIFIED` |
| ENG-D05 | Runtime observability `app/kernel/runtime_observability.py` | 274 | Kernel runtime surfaces | Kernel metrics/tracing | `tests/kernel_hardening/test_observability.py` 6, `test_observability_invariants.py` 23 (E-047) | `INTEGRATION_VERIFIED` |
| ENG-D06 | Certification engine `app/certification/engine.py` + `app/certification/dimensions/offline.py` | 117/204 | certification routes | dimension evaluators | no dedicated test module located → F-072 | `SOURCE_PRESENT` |

**Totals:** 39 engines inventoried — A 12 · B 12 · C 9 · D 6. Status distribution (reconciled with the
per-engine rows above after E-052):
`INTEGRATION_VERIFIED` 9 · `UNIT_VERIFIED` 15 · `PARTIAL_VERIFIED` 2 · `SOURCE_PRESENT` 11 ·
`DORMANT` 1 · `UNVERIFIABLE` 1. **`RUNTIME_VERIFIED` 0 · `PRODUCTION_VERIFIED` 0.**

*Reconciliation note:* the pre-E-052 summary line carried an 8/16 integration/source split that was
one off from the actual rows (9 integration / 15 source). E-052 converted four source-only engines
(A09, A11, B12, D03) to `UNIT_VERIFIED`; the correct post-E-052 split is therefore 9 / 15 / 2 / 11 / 1 / 1.
No per-engine status was downgraded and no engine was newly claimed as runtime- or production-verified.

## 7. What this inventory does not claim

1. No engine was activated, enabled, mounted, or refactored. ENG-A12 (generated scaffold) and
   ENG-B09 (national CDS) remain exactly as found.
2. `INTEGRATION_VERIFIED` means *isolated synthetic TestClient/DB-fixture tests passed here*; it is
   **not** runtime verification, clinical-safety certification, migration-schema verification, or
   production evidence. The strict W1 gate remains FAILED (119/872, E-001) and is not re-evaluated here.
3. Existing-but-unexecuted test files are recorded as such; their presence is not a PASS.
4. Source presence and route registration do not prove a health service is ready — see
   `NATIONAL_SERVICE_INVENTORY.md` §2 taxonomy (Phase 4).
5. No clinical behavior, authentication/authorization behavior, migration, DDL, operational DB,
   `gula-platform`, Platform-Core, test, fixture, conftest or production module was changed.
6. `FINAL_DECISION.md` remains **HOLD**; D-020 and D-021 remain PENDING; no approval is inferred.
