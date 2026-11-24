# AUTONOMOUS ENGINES DEPENDENCY MAP — Phase 3 (entry points, dependencies, consumers)

**Repository / HEAD:** `gula-integration` · `integration/gula-unification-v1` @ `2827c1ff…` (unchanged)
**Date:** 2026-11-17 · **Category:** A (documentation-only) · **Change record:** CC-005
**Purpose:** make future repairs *safe* by recording where each engine actually enters the system and
what depends on it. This is a read-only map — no wiring was added, removed or enabled.

---

## 1. Entry-point families (verified from source)

| Family | Verified location | Engines reached | Note |
|---|---|---|---|
| HTTP router registration | `app/factory.py:579` (core+feature+advanced+admin+mobile+compliance loops), `:604` national_identity, `:607` AI routes, `:611` ai_platform, `:692` rules, `:695` background, `:698` task, `:701` notifications, `:706` document, `:709` scheduling, `:712` search, `:715` observability, `:721-722` national data/streaming | ENG-A01, A10, B01–B06, B11–B12, C07, D01–D04, D06 | Presence of a router ≠ service readiness |
| Identity workflow mount | `app/identity/api/router.py:13` import, `:59` `include_router(workflows_routes.router)` | ENG-A01 | Canonical workflow entry (not the generated scaffold) |
| Kernel boot phases | `app/kernel/runtime/bootloader.py:30` `_phase_initialize_background()`, `:131` `EventBus(self.kernel)`, `:135` method definition | ENG-A02…A06 | `KERNEL_ENABLE_BACKGROUND` / `KERNEL_ENABLE_EVENT_BUS` gates in `app/kernel/integration.py:27-28` |
| Application startup / worker loop | `app/core/startup.py:270-272` and `app/worker.py:86-100` (`OutboxWorker.background_loop`) | ENG-B10 | No runtime observation in this audit |
| National aggregator | `app/national/api/routes/__init__.py:21-36` (`national_router.include_router(…)` incl. `cds_router` at `:22`) | ENG-B09 | `app/factory.py` was read and **does not mount this aggregator** in the observed wiring — exposure UNKNOWN |
| Self-contained capability | `app/capabilities/workflow_engine/**` | ENG-A12 | Zero references outside its own directory → DORMANT |

## 2. Category A — workflow / orchestration / rules / decision

| Engine | Upstream (calls into it) | Internal dependencies | Downstream / consumers | External references outside its family |
|---|---|---|---|---|
| ENG-A01 canonical workflow | identity workflows router, national workflows (`base.py`, referral/encounter/registration/merge/death), `app/workflows/engine.py` | Kernel, RBAC, DB session | identity + national workflow handlers | yes — active (E-048/050) |
| ENG-A02 scheduler/retry/cron/pool | `Bootloader._phase_initialize_background` | `DistributedLockManager`, `JobRetry` | internal kernel background phase only | **no direct external symbol hits** (Scheduler/JobRetry/CronEngine). `WorkerPool` hits in `document_intelligence/distributed/worker_pool.py` are a **name collision, not this class** |
| ENG-A03 priority/task queues | Bootloader background phase | `PriorityTask`, `Task`, `JobRetry` | internal only. `TaskQueue` hits in `document_intelligence/distributed/task_queue.py` and `national/task_engine/**` are **separate classes** | kernel-internal |
| ENG-A04 distributed locks | `Scheduler.__init__` | in-process lock state | scheduler | none outside kernel |
| ENG-A05 event bus family | Bootloader line 131 | DB session, outbox, DLQ, store, replay | `app/services/outbox_service.py`, `app/engineering/validation/event_driven.py`, national scheduling/observability/document/rules services | **yes — fan-out to national services** (highest blast radius in category A) |
| ENG-A06 event recovery | EventBus recovery path | EventStore, DLQ, retry queue | event bus | no dedicated consumer map recorded |
| ENG-A07 rules runtime | `runtime_routes.py`, `runtime_integration.py` | Kernel rule registry, DB | kernel runtime surfaces | no direct external symbol hits |
| ENG-A08 policy runtime | `runtime_routes.py`, `runtime_integration.py` | policy engine, Kernel | kernel runtime surfaces | no direct external symbol hits |
| ENG-A09 core policy/risk | control-plane routes, repair assessment | `ActionType`, `RiskLevel` | control layer | control-plane only |
| ENG-A10 national expression engine | national rules router (`factory.py:692`) | national rules domain, DB | rule evaluation endpoints | national rules package |
| ENG-A11 task queue/worker | worker process (`build_queue`) | Redis-backed queue, retry | background tasks | worker only; Redis failure mode not tested here |
| ENG-A12 generated scaffold | **none** | generated base classes | **none** | **none — DORMANT (F-071)** |

## 3. Category B — AI / RAG / FHIR / event / data

| Engine | Upstream | Internal dependencies | Downstream / consumers | Notes |
|---|---|---|---|---|
| ENG-B01 RAG/vector | `app/routes/ai.py` (`ai_routes`) | `app/ai/vector_store.py`, `app/gateways/google_ai.py::generate_chat` | AI chat endpoints, CDS | `generate_chat` is an outbound gateway — external AI dependency, not exercised against a live provider here |
| ENG-B02 healthcare CDS | AI routes | RAG pipeline, guardrails | CDS endpoints | D-021 sign-off absent; output safety not certified |
| ENG-B03 orchestrator/guardrails | AI routes, approval flow | approval store, guardrail registry | AI sandbox, approval tracking | E-046/047 exercised approval/guardrail paths |
| ENG-B04 AI-fabric RAG | `ai_platform_routes` (`factory.py:611`) | vector DB abstraction, embeddings | AI platform endpoints | access tests only (4) — not full semantics |
| ENG-B05 HL7→FHIR | FHIR interoperability router | `HL7Message`, `to_fhir_bundle` | FHIR bundle consumers, device gateway (ENG-C08) | E-051 proves synthetic ORU→FHIR conversion |
| ENG-B06 FHIR resource/search | FHIR capability router, national FHIR search | FHIR R4 models | FHIR API clients | comprehensive/R4 exchange tests passed (E-047) |
| ENG-B07 MDM | health-data MDM API | `ExactMatcher`, `FuzzyMatcher`, `ProbabilisticMatcher` | identity/patient merge flows | no dedicated behavioral tests (F-067) |
| ENG-B08 health-data streaming | `national_streaming_routes` (`factory.py:721-722`) | `EventBusSource`, `StreamProcessor`, filters | national streaming endpoints | no dedicated tests |
| ENG-B09 national CDS engine | `cds_router` → `national_router` (unmounted by observed `factory.py`) | DB session, drug/allergy/guideline rules | none confirmed in main app | **do not enable**; F-068 + D-021 |
| ENG-B10 outbox worker | `core/startup.py`, `worker.py` | DB outbox table, event bus (ENG-A05) | event delivery | background loop not runtime-observed |
| ENG-B11 search service | `search_router` (`factory.py:712`) | `DefaultSearchService`, indexer | national search consumers | promotion work W-003 is IN_PROGRESS (env-only fail) — unchanged |
| ENG-B12 document-intelligence wiring | document capability composition | search, PDF adapter, events | document endpoints | 1054 LOC wiring; 62 tests executed (E-052) → `UNIT_VERIFIED` |

## 4. Category C — security / governance / offline / resilience

| Engine | Upstream | Internal dependencies | Downstream / consumers | Notes |
|---|---|---|---|---|
| ENG-C01 rate limiter | security middleware / factory | client-IP resolution | protected endpoints | not executed here |
| ENG-C02 tenant helpers | security + data access layers | `tenant_collection`, `sanitize_request_id` | tenant-scoped queries | E-046 tenant matrix passed (21) |
| ENG-C03 self-healing/circuit | `DegradedModeMiddleware` in `factory.py`, kernel gateway | `CircuitBreaker`, `DegradationLevel` | request degradation, worker resilience | in-process only; cross-worker state UNKNOWN |
| ENG-C04 offline sync engine | offline sync call sites | `SyncEvent`, `OfflineSyncEngine` | offline capture | in-memory (F-028) — durability not claimed |
| ENG-C05 offline sync service | offline sync API | `ConflictResolution`, operation log | conflict-resolution result | `CRDT_MERGE` first-wins (F-069); only LWW/timestamp/manual tested |
| ENG-C06 ABAC policy | identity authorization path | `PolicyContext`, `PolicyEngine` | authorization decisions | E-046 ABAC passed; not D-020 sign-off |
| ENG-C07 canonical audit | audit routes, governance authorization | hash chain, redaction | audit event store | append-only trigger on migrated schema untested (F-008) |
| ENG-C08 lab device gateway | HL7/analyzer ingress | HL7 parser, result service | result ingestion | no direct tests (F-070) |
| ENG-C09 national security rules | national security services | `GuardianRule`, foreign-patient policy | national access decisions | no dedicated tests |

## 5. Category D — laboratory automation / monitoring / platform operations

| Engine | Upstream | Internal dependencies | Downstream / consumers | Notes |
|---|---|---|---|---|
| ENG-D01 Westgard QC | QC routes (advanced routes) | QC rule set, DB | QC results/flags | 26 tests passed (E-046) |
| ENG-D02 LIMS workflows | results/samples routes, LIMS quality routes | `auto_validate_result`, `process_critical` | released results, critical alerts | authorization/tenant tests passed (E-046) |
| ENG-D03 test-result engine | `app/routes/test_results.py` | validation, Westgard flags, audit | result API | 19 tests executed (E-052) → `UNIT_VERIFIED` |
| ENG-D04 metrics engine | `core_routes` metrics | DB/Redis ping, Prometheus | `/metrics` endpoints | 16 tests passed (E-046) |
| ENG-D05 runtime observability | Kernel runtime surfaces | Kernel metrics/tracing | observability endpoints | 29 tests passed (E-047) |
| ENG-D06 certification engine | certification routes | dimension evaluators (incl. offline) | certification reports | no tests (F-072); output not release evidence |

## 6. Cross-cutting risk hotspots (analysis only, no change)

1. **Event bus fan-out (ENG-A05):** the widest consumer set (outbox + national scheduling,
   observability, document, rules). Any future change there has the highest blast radius; require
   per-consumer tests before modification.
2. **Two workflow engines, one real:** ENG-A01 is canonical; ENG-A12 is a dormant generated scaffold.
   A future agent must not wire ENG-A12 or cite its trivial tests as workflow verification.
3. **National CDS is unmounted (ENG-B09):** route collection exists but no observed `factory.py`
   mount. Do not infer a live clinical endpoint; clinical behavior changes need D-021.
4. **Offline chain (ENG-C04 → ENG-C05 → ENG-D06):** in-memory queue (F-028) feeds first-wins
   `CRDT_MERGE` (F-069), and the certification dimension lists CRDT without measuring it (F-072).
   Do not claim offline-first or CRDT convergence for any service.
5. **Audit on migrated schema (ENG-C07):** isolation tests pass in the synthetic harness, but the
   append-only trigger behavior on the migration-built schema is not verified (F-008/B-019).
6. **Name-collision false positives:** `WorkerPool`/`PriorityQueue`/`TaskQueue` hits in
   `document_intelligence/distributed/**` and `national/task_engine/**` are **distinct classes**,
   not the kernel background engines. They are not evidence of kernel engine consumers.

## 7. How the wiring facts were obtained (read-only commands)

- `grep -n "include_router" app/factory.py` and targeted `sed` reads of the registration block.
- `grep -n "Workflows\\|workflows" app/identity/api/router.py` (lines 13 and 59).
- `grep -n "_phase_initialize_background\\|EventBus(" app/kernel/runtime/bootloader.py` (30, 131, 135).
- `grep -n "OutboxWorker" app/core/startup.py app/worker.py` (270-272 and 86-100).
- `grep -rln "<symbol>" app --include='*.py'` for external-reference scans; results and false
  positives are recorded in §2/§6.
- `wc -l` and `grep -E '^(class|def|async def)'` on each source file to size and identify entry points.

**No command above modified a file, contacted an external service, or executed a migration.**

## 8. Non-claims

This map does not prove runtime availability, production exposure, clinical safety, migration
compatibility or service readiness. Router presence is not service readiness; source presence is not
verification. `FINAL_DECISION.md` remains **HOLD**, D-020/D-021 remain PENDING, and no engine was
activated or changed by this phase.
