# NATIONAL CAPABILITY REGISTRY — reference-only capability index

**Repository:** `gula-integration` · **Branch:** `integration/gula-unification-v1` @ `2827c1ff1032918aa2541aa0b47bb7f2e5d6cac0` (unchanged) · **Date:** 2026-11-17 · **Work item:** W-064/W-072/W-079 · **Change control:** CC-010 · **Evidence:** E-062.

> **This registry is a reference-only, non-executing index.** It is documentation, not a service, an orchestration engine, a router, a health check or a single point of failure. The application does **not** import it and continues to work if it is absent. It records where capabilities already exist so they are not duplicated; it does **not** activate, mount, dispatch to or certify any engine.

**Verdict:** `GOVERNANCE/FINAL_DECISION.md` remains **HOLD**. D-020 and D-021 remain **PENDING_APPROVAL**. 0 commits / pushes / merges / PRs / deploys. No runtime, production, clinical-safety or release claim is made.

---

## 1. Authority and design envelope

Built under the owner's post-stabilization engineering mandate (CC-010), implementing the **GO-FOR-DESIGN, reference-only** recommendation of `STABILIZATION_PHASE_H_I_ASSESSMENT.md` §1.3. That assessment explicitly set **NO-GO for any executing registry or new engine**. This document and its machine-readable companion `national_capability_index.json` stay inside that envelope:

- No new engine is built; **ENG-A12 stays DORMANT** (F-071); **ENG-B09 stays UNMOUNTED** (F-068, D-021 PENDING).
- No service activation, mount, refactor, dependency addition, route, dispatch, or clinical behavior change; no SPOF introduced.
- Generated/checked-in static JSON + this static Markdown index; **no process, no per-request lookup, no runtime authority**.
- Every row is a pointer to existing source with its already-recorded status; **no status was re-executed or upgraded** here.

## 2. Frozen status distribution

Recomputed from the 39 index rows and cross-checked against `AUTONOMOUS_ENGINES_INVENTORY.md` §6 by the read-only verifier `scripts/verify_national_capability_registry.py` (E-062, 20/20 checks PASS).

| Status | Count | Meaning (bounded) |
|---|---:|---|
| `INTEGRATION_VERIFIED` | 9 | isolated synthetic TestClient/DB-fixture tests passed in E-046…E-052 — **not** runtime/production |
| `UNIT_VERIFIED` | 15 | isolated synthetic unit tests passed — **not** route/runtime evidence |
| `PARTIAL_VERIFIED` | 2 | some paths tested, named residual open |
| `SOURCE_PRESENT` | 11 | source on disk; no executed test evidence in the cited batches |
| `DORMANT` | 1 | generated scaffold with no external references — never activate |
| `UNVERIFIABLE` | 1 | no dedicated suite; route unmounted — cannot certify |
| `RUNTIME_VERIFIED` | 0 | **always 0 — no engine was runtime-observed** |
| `PRODUCTION_VERIFIED` | 0 | **always 0 — no production evidence exists** |
| **Total** | **39** | A 12 · B 12 · C 9 · D 6 |

## 3. Special states (version/authority invariants)

- **ENG-A12** — DORMANT — stays dormant (F-071); never activate
- **ENG-B09** — UNVERIFIABLE — national CDS route UNMOUNTED (F-068, D-021 PENDING); do not enable

## 4. Capability index (all 39 — reference-only pointers)

### Category A — workflow / orchestration / rules / decision

| ID | Capability | Canonical source | Entry point / wiring | Status | Linked findings |
|---|---|---|---|---|---|
| `ENG-A01` | Canonical workflow engine | `app/workflows/engine.py` | `app/identity/api/router.py:59` | `PARTIAL_VERIFIED` | — |
| `ENG-A02` | Background scheduler + retry + cron + worker pool | `app/kernel/background/scheduler.py` | `Bootloader._phase_initialize_background` | `UNIT_VERIFIED` | — |
| `ENG-A03` | Priority + task queues | `app/kernel/background/priority_queue.py` | `—` | `UNIT_VERIFIED` | — |
| `ENG-A04` | Distributed locks | `app/kernel/background/distributed_locks.py` | `Scheduler.__init__` | `UNIT_VERIFIED` | — |
| `ENG-A05` | Event bus family | `app/kernel/event_bus/bus.py` | `Bootloader` | `UNIT_VERIFIED` | — |
| `ENG-A06` | Event recovery | `app/kernel/event_bus/recovery.py` | `RecoveryEngine` | `SOURCE_PRESENT` | — |
| `ENG-A07` | Rules runtime | `app/kernel/rules_runtime.py` | `app/kernel/runtime_routes.py` | `SOURCE_PRESENT` | F-066 |
| `ENG-A08` | Policy runtime | `app/kernel/policy_runtime.py` | `app/kernel/runtime_routes.py` | `SOURCE_PRESENT` | F-066 |
| `ENG-A09` | Control-layer policy + risk | `app/core/policy_engine.py` | `—` | `UNIT_VERIFIED` | — |
| `ENG-A10` | National rules expression engine | `app/national/rules_engine/domain/expression_engine.py` | `app/factory.py:692` | `SOURCE_PRESENT` | F-066 |
| `ENG-A11` | Task queue / worker | `app/tasks/queue.py` | `—` | `UNIT_VERIFIED` | — |
| `ENG-A12` | Generated capability scaffold  (service 24, routes 51, capability 51, repository 48, entities 15) | `app/capabilities/workflow_engine/` | `app/**/*.py` | `DORMANT` | — |

### Category B — AI / RAG / FHIR / event / data

| ID | Capability | Canonical source | Entry point / wiring | Status | Linked findings |
|---|---|---|---|---|---|
| `ENG-B01` | RAG pipeline + vector store | `app/ai/rag_pipeline.py` | `app/routes/ai.py` | `INTEGRATION_VERIFIED` | — |
| `ENG-B02` | Healthcare CDS | `app/ai/healthcare_cds.py` | `app/routes/ai.py` | `INTEGRATION_VERIFIED` | — |
| `ENG-B03` | AI orchestrator + guardrails | `app/ai/orchestrator.py` | `—` | `UNIT_VERIFIED` | — |
| `ENG-B04` | AI-fabric RAG | `app/ai_fabric/rag.py` | `ai_platform_routes` | `INTEGRATION_VERIFIED` | — |
| `ENG-B05` | HL7 ORU→FHIR | `app/capabilities/fhir_interoperability/hl7.py` | `/fhir-interoperability/hl7/convert` | `INTEGRATION_VERIFIED` | — |
| `ENG-B06` | FHIR resource service + search , | `app/capabilities/fhir_interoperability/service.py` | `—` | `INTEGRATION_VERIFIED` | — |
| `ENG-B07` | MDM service + matching | `app/health_data/mdm/service.py` | `—` | `SOURCE_PRESENT` | F-067 |
| `ENG-B08` | Health-data streaming | `app/health_data/streaming/pipeline.py` | `national_streaming_routes` | `SOURCE_PRESENT` | — |
| `ENG-B09` | National CDS engine | `app/national/services/cds_engine.py` | `app/national/api/routes/cds.py` | `UNVERIFIABLE` | F-068 |
| `ENG-B10` | Outbox worker | `app/services/outbox_service.py` | `app/core/startup.py:270-272` | `INTEGRATION_VERIFIED` | — |
| `ENG-B11` | Search service  + national search routes | `app/capabilities/search_service/search.py` | `app/factory.py:712` | `SOURCE_PRESENT` | — |
| `ENG-B12` | Document-intelligence wiring | `app/document_intelligence/application/wiring.py` | `—` | `UNIT_VERIFIED` | — |

### Category C — security / governance / offline / resilience

| ID | Capability | Canonical source | Entry point / wiring | Status | Linked findings |
|---|---|---|---|---|---|
| `ENG-C01` | Rate limiter | `app/security/rate_limit.py` | `—` | `SOURCE_PRESENT` | — |
| `ENG-C02` | Tenant/collection policy helpers | `app/security/policy.py` | `—` | `UNIT_VERIFIED` | — |
| `ENG-C03` | Self-healing + circuit breakers , | `app/core/self_healing.py` | `DegradedModeMiddleware` | `UNIT_VERIFIED` | — |
| `ENG-C04` | Offline sync engine | `app/core/sync_engine.py` | `—` | `UNIT_VERIFIED` | — |
| `ENG-C05` | Offline sync service / conflict resolution | `app/services/offline_sync_service.py` | `—` | `PARTIAL_VERIFIED` | F-069 |
| `ENG-C06` | ABAC / identity policy | `app/identity/policy_engine.py` | `—` | `UNIT_VERIFIED` | — |
| `ENG-C07` | Canonical audit | `app/identity/services/canonical_audit.py` | `—` | `INTEGRATION_VERIFIED` | — |
| `ENG-C08` | Lab device gateway | `app/gateways/lab_device_gateway.py` | `—` | `SOURCE_PRESENT` | F-070 |
| `ENG-C09` | National security rules | `app/national/security/guardian_rules.py` | `—` | `SOURCE_PRESENT` | — |

### Category D — laboratory automation / monitoring / platform operations

| ID | Capability | Canonical source | Entry point / wiring | Status | Linked findings |
|---|---|---|---|---|---|
| `ENG-D01` | Westgard QC engine | `app/services/quality_control_service.py` | `app/factory.py` | `UNIT_VERIFIED` | — |
| `ENG-D02` | LIMS workflow automation | `app/lims/workflows.py` | `—` | `INTEGRATION_VERIFIED` | — |
| `ENG-D03` | Test-result engine | `app/services/test_result_service.py` | `app/routes/test_results.py` | `UNIT_VERIFIED` | — |
| `ENG-D04` | Metrics engine  + | `app/services/metrics_service.py` | `core_routes` | `UNIT_VERIFIED` | — |
| `ENG-D05` | Runtime observability | `app/kernel/runtime_observability.py` | `—` | `INTEGRATION_VERIFIED` | — |
| `ENG-D06` | Certification engine  + | `app/certification/engine.py` | `—` | `SOURCE_PRESENT` | F-072 |

## 5. Verification, duplicate prevention and non-claims

- **Verifier (read-only, stdlib only):** `python3 scripts/verify_national_capability_registry.py` → 20/20 checks PASS (E-062). It re-derives the status distribution, checks all 39 source paths exist, asserts ENG-A12/ENG-B09 invariants, asserts the inventory still has 39 rows, and asserts **no application module imports the index**.
- **Negative controls (E-062):** tampering with `executing=true`, inflating an engine to `RUNTIME_VERIFIED`, or flipping ENG-A12 to a verified state is **detected** by the verifier and the synthetic suite (3 dedicated tests).
- **Duplicate prevention:** this index is the single reference list for capability discoverability; a new engine proposal must first show it is not already listed here and must follow `DUPLICATE_PREVENTION.md`. The index itself never creates a capability.
- **Non-claims:** no engine was activated, mounted, refactored or re-tested here; no runtime or production evidence; no clinical-safety/security certification; no SLO/RPO/RTO; no release claim. Router presence and source presence are not readiness. `FINAL_DECISION.md` stays **HOLD**; D-020/D-021 stay **PENDING**.

**Rollback (CC-010):** delete `NATIONAL_CAPABILITY_REGISTRY.md`, `national_capability_index.json`, `scripts/verify_national_capability_registry.py` and `backend/tests/test_national_capability_registry_reference.py`; no application or DB object was created, so nothing else changes.
