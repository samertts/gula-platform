# GULA Platform — Capability Factory Catalog (MISSION 7)

> Generated: 2026-07-14
> Assessment: Capability Factory Analysis — Monolith + Microservices + Shared Kernel

---

## 1. EXECUTIVE SUMMARY

The GULA Platform has a **Kernel architecture** (singleton bootloader, lifecycle, service registry, DI container, event bus, plugin/module system) and a **52-module `shared/` package**, but **zero `CapabilityDescriptor` objects are actually registered** in the `CapabilityRegistry`. The registry is a shell — it exists, it's instantiated at boot, it exposes a `/kernel/capabilities` endpoint, but no code anywhere calls `capability_registry.register()`.

Meanwhile, the **feature flag system** (`core/feature_flags.py`) defines a rich 30+ feature tier matrix, and the `shared/` package holds reusable infrastructure modules that are *de facto* capabilities (auth, events, PDF, QR, device integration, workflow, etc.).

**Core gap:** The platform has capabilities in spirit (shared libraries, services, routes, feature flags) but lacks the *Capability Factory layer* that would:
1. Package each capability as a self-describing `CapabilityDescriptor`
2. Expose a uniform contract (commands, queries, events) per capability
3. Enable capability-level versioning, dependency resolution, and lifecycle hooks
4. Allow capabilities to be deployed monolithically OR as microservices without code changes

---

## 2. CURRENTLY DEFINED / REGISTERED CAPABILITIES

### 2.1 Kernel CapabilityRegistry (runtime)

| Registry State | Detail |
|---|---|
| **Instantiated?** | Yes — `Bootloader._phase_initialize_core_components()` |
| **Registered as component?** | Yes — `kernel.register_component("capability_registry", ...)` |
| **Any `CapabilityDescriptor` registered?** | **No — zero registrations** |
| **Consumed by?** | `/kernel/capabilities` API route (returns empty list) |

The `CapabilityDescriptor` schema exists in `kernel/types.py`:
```python
@dataclass
class CapabilityDescriptor:
    name: str
    version: str
    description: str
    dependencies: list[str] = []
    required: bool = False
    enabled: bool = True
```

### 2.2 CapabilityFlagManager (kernel/features/capabilities.py)

| State | Detail |
|---|---|
| **Instantiated?** | No — not wired into bootloader or any startup sequence |
| **Used anywhere?** | No — zero imports outside its own module |
| **Relationship to CapabilityRegistry** | None — separate system, no bridge |

### 2.3 Feature Flag System (core/feature_flags.py) — Tier Matrix

This is the **de facto capability inventory** gated by subscription tier. The tier matrix defines **30 named features**:

| Tier | Features |
|---|---|
| **Starter (8)** | patient_management, basic_results, sample_tracking, pdf_reports, qr_codes, notifications, audit_log, mobile_access |
| **Growth (+9)** | quality_control, batch_import, batch_export, ehr_integration, advanced_analytics, critical_alerts, insurance_integration, national_id_lookup, device_results |
| **Enterprise (+11)** | multi_branch, government_reporting, ai_interpretation, ai_anomaly_detection, ai_epidemiology, custom_branding, api_access, sla_guarantee, white_label, priority_support |

Deployment overrides: single, multi_branch, government
Security overrides: standard, high_security, air_gapped

**Problem:** These feature flags are flat strings (no version, no contract, no dependency model). They cannot be composed, versioned, or independently deployed.

### 2.4 Capability Generator (engineering/generators/capability.py)

A code-generation scaffold exists that can produce capability stubs with:

```python
CapabilitySpec(name, description, domain, layer, commands, events, queries)
```

The generator produces:
- `{cap}/__init__.py` — module docstring
- `{cap}/contract.py` — `{Cap}Input` / `{Cap}Output` dataclasses
- `{cap}/capability.py` — `{Cap}Capability` class with `execute()` / `validate()`
- `{cap}/commands/{name}.py` — command dataclasses
- `{cap}/events/{name}.py` — event dataclasses
- `{cap}/queries/{name}.py` — query dataclasses

**Status:** Alive but not integrated. The generator is not connected to the kernel boot sequence, capability registry, or any CI pipeline.

---

## 3. SHARED PACKAGE — DE FACTO CAPABILITY FOUNDATIONS

The `backend/app/shared/` package contains **53 modules** that represent the actual reusable cross-cutting capabilities of the platform. Each can be considered a *capability seed*:

### 3.1 Infrastructure Capabilities (shared/ — 52 modules)

| Module | Domain | Capability Potential | Currently Reusable? |
|---|---|---|---|
| `auth/` | Identity & Access | Authentication (JWT, passwords) | ✅ Shared lib |
| `ai/` | Clinical AI | AI provider abstraction | ✅ Shared lib |
| `architecture/` | Governance | Knowledge graph, validator | ✅ Shared lib |
| `audit/` | Compliance | Audit trail | ✅ Shared lib |
| `backup/` | Resilience | DB/volume backup | ✅ Shared lib |
| `barcode/` | Lab Ops | Barcode generation | ✅ Shared lib |
| `booking` | Scheduling | Appointment booking | ❌ Single module |
| `cache/` | Performance | Redis/memory backends | ✅ Shared lib |
| `circuit_breaker` | Resilience | Failure isolation | ❌ Single module |
| `config/` | Infra | Config loading | ✅ Shared lib |
| `design_system/` | UX | RTL, tokens, components | ✅ Shared lib |
| `device/` | Lab Ops | ASTM/HL7 adapters | ✅ Shared lib |
| `di_container/` | Architecture | DI container engine | ✅ Shared lib |
| `documents` | Reporting | Document generation | ❌ Single module |
| `domain/` | DDD | Domain events, billing, healthcare types | ✅ Shared lib |
| `events/` | Messaging | Event bus, constants | ✅ Shared lib |
| `feature_flags` | Governance | Flag evaluation | ❌ Single module |
| `generators/` | Tooling | Code generation | ✅ Shared lib |
| `health/` | Observability | Health check logic | ✅ Shared lib |
| `identity/` | Identity | Domain, events, service for identity | ✅ Shared lib |
| `licensing` | Governance | License enforcement | ❌ Single module |
| `localization` | UX | i18n / Arabic RTL | ❌ Single module |
| `logging/` | Observability | Structured logging | ✅ Shared lib |
| `messaging` | Integration | Message bus abstraction | ❌ Single module |
| `metrics/` | Observability | Metrics collector | ✅ Shared lib |
| `middleware/` | Infra | Base middleware | ✅ Shared lib |
| `models/` | Data | Base model types | ✅ Shared lib |
| `notifications/` | Communication | Sender, template engine | ✅ Shared lib |
| `observability/` | Monitoring | Tracing infrastructure | ✅ Shared lib |
| `payments` | Financial | Payment processing | ❌ Single module |
| `pdf/` | Reporting | PDF generation | ✅ Shared lib |
| `policies/` | Governance | Policy engine | ✅ Shared lib |
| `printing` | Lab Ops | Label printing | ❌ Single module |
| `qr/` | Lab Ops | QR code generation | ✅ Shared lib |
| `rbac/` | Security | Permission model | ✅ Shared lib |
| `restore/` | Resilience | Restore from backup | ✅ Shared lib |
| `retry/` | Resilience | Retry logic | ✅ Shared lib |
| `scheduler` | Infra | Job scheduling | ❌ Single module |
| `schemas/` | API | Pagination, response wrappers | ✅ Shared lib |
| `sdk/` | API | External client SDK | ✅ Shared lib |
| `search` | Data | Search abstraction | ❌ Single module |
| `security/` | Security | Encryption, HMAC | ✅ Shared lib |
| `storage/` | Data | Storage backends | ✅ Shared lib |
| `subscriptions` | Financial | Sub tiers | ❌ Single module |
| `tracing/` | Observability | OpenTelemetry wrappers | ✅ Shared lib |
| `utilities/` | Infra | Shared utilities | ✅ Shared lib |
| `validators/` | Data | Validation helpers | ✅ Shared lib |
| `workflow/` | Process | Workflow engine | ✅ Shared lib |

### 3.2 Critical Observation

**~25 modules in `shared/` are single-file modules (not packages)** — they lack the directory structure needed for a full capability (contracts, commands, events, queries). These need to be **promoted** to proper capability packages.

---

## 4. EXISTING BUSINESS CAPABILITIES (from monolith services)

### 4.1 Backend Services (`backend/app/services/` — 24 modules)

| Service | Domain | Capability Name | Status |
|---|---|---|---|
| order_service.py | Orders | `order_management` | ✅ Concrete service |
| patient_service.py | Patients | `patient_management` | ✅ Concrete service |
| sample_management | Samples | `sample_tracking` | ✅ Concrete service |
| result_service | Results | `result_management` | ✅ Concrete service |
| clinical_engine.py | Clinical | `clinical_engine` | ✅ Concrete service |
| clinical_intelligence.py | Clinical | `clinical_intelligence` | ✅ Concrete service |
| clinical_state.py | Clinical | `clinical_state_machine` | ✅ Concrete service |
| interpretation.py | Clinical | `ai_interpretation` | ✅ Concrete service |
| epidemiology.py | Clinical | `epidemiology` | ✅ Concrete service |
| critical_alerts.py | Alerts | `critical_alerting` | ✅ Concrete service |
| identity.py | Identity | `identity_management` | ✅ Concrete service |
| identity_matching.py | MPI | `patient_matching` | ✅ Concrete service |
| mpi/ | MPI | `master_patient_index` | ✅ Concrete service |
| national_id.py | Identity | `national_id_lookup` | ✅ Concrete service |
| patient_card.py | Patient | `patient_card` | ✅ Concrete service |
| pdf_report.py | Reporting | `pdf_reporting` | ✅ Concrete service |
| consent_service.py | Legal | `consent_management` | ✅ Concrete service |
| claims_service.py | Financial | `claims_processing` | ✅ Concrete service |
| audit_service.py | Compliance | `audit_service` | ✅ Concrete service |
| outbox_service.py | Messaging | `event_outbox` | ✅ Concrete service |
| ali_reza.py | AI | `ali_reza_agent` | ✅ Concrete service |
| ali_reza_engine.py | AI | `ali_reza_engine` | ✅ Concrete service |
| samir.py | AI | `samir_agent` | ✅ Concrete service |
| samir_engine.py | AI | `samir_engine` | ✅ Concrete service |

### 4.2 Route Modules (38 modules — API layer)

Each route module in `backend/app/routes/` represents an **API surface** for a capability:

| Route | Capability Mapping |
|---|---|
| `patients.py` | → `patient_management` |
| `results.py` | → `result_management` |
| `samples.py` | → `sample_tracking` |
| `labs.py` | → `lab_management` |
| `orders.py` | → `order_management` |
| `auth.py` / `login.py` | → `authentication` |
| `admin.py` | → `admin_console` |
| `ai.py` / `ai_telemetry.py` | → `ai_capabilities` |
| `batch.py` | → `batch_operations` |
| `claims.py` | → `claims_processing` |
| `compliance.py` | → `compliance` |
| `consent.py` | → `consent_management` |
| `critical_alerts.py` | → `critical_alerting` |
| `dashboard.py` | → `dashboard` |
| `device_results.py` | → `device_integration` |
| `edge.py` | → `edge_platform` |
| `ehr.py` | → `ehr_integration` |
| `id_scan.py` | → `id_scanning` |
| `identity.py` | → `identity_management` |
| `insurance.py` | → `insurance_integration` |
| `integrations.py` | → `third_party_integrations` |
| `metrics.py` | → `metrics` |
| `mobile.py` | → `mobile_api` |
| `national_identity.py` | → `national_id_lookup` |
| `notifications.py` | → `notification_service` |
| `optimizer.py` | → `system_optimizer` |
| `patient_card.py` | → `patient_card` |
| `qr.py` | → `qr_generation` |
| `quality_control.py` | → `quality_control` |
| `register.py` | → `lab_registration` |
| `security.py` | → `security_audit` |
| `setup.py` | → `lab_setup` |
| `stats.py` | → `analytics` |
| `test_results.py` | → `test_result_management` |
| `tiers.py` | → `subscription_tiers` |

---

## 5. MICROSERVICES CAPABILITY MAPPING

The `services/` directory contains 10 services that are **candidates for capability extraction**:

| Service Dir | Domain | Capability | Shared Code? |
|---|---|---|---|
| `services/ai/` | AI | `ai_capabilities` | `shared/ai/client.py` |
| `services/autonomous_manager/` | Orchestration | `autonomous_orchestrator` | None |
| `services/device_bridge/` | Lab Ops | `device_integration` | `shared/device/` |
| `services/lab/` | Lab Mgmt | `lab_management` | None |
| `services/notification/` | Comms | `notification_service` | `shared/notifications/` |
| `services/order/` | Orders | `order_management` | `shared/events/` |
| `services/patient/` | Patients | `patient_management` | `shared/identity/` |
| `services/result/` | Results | `result_management` | None |
| `services/sample/` | Samples | `sample_tracking` | None |
| `services/shared/` | Infra | `shared_infrastructure` | Audit, circuit_breaker, messaging |

**Key finding:** Microservices duplicate business logic from the monolith (`backend/app/services/`). There is no shared-capability extraction between the monolith service and its microservice counterpart. Each pair (e.g., `order_service.py` monolith vs `services/order/` microservice) maintains independent implementations.

---

## 6. GAP ANALYSIS

### 6.1 What's Missing vs. Full Capability Factory

| Dimension | Current State | Target State | Gap |
|---|---|---|---|
| **Registry population** | Zero descriptors registered | 30-50 capability descriptors | 🔴 Critical — need to enumerate and register |
| **Capability contracts** | Ad-hoc function signatures | `{Input, Output, execute, validate}` per capability | 🔴 Critical — no uniform contract |
| **Dependency resolution** | `check_dependencies()` exists, no graph | Auto-resolve capability dependency DAG | 🟡 Medium — framework exists but unused |
| **Versioning** | App-level version only | Per-capability semver + changelog | 🔴 Critical |
| **Lifecycle hooks** | Kernel lifecycle manager | Per-capability `on_activate()`, `on_deactivate()`, `on_upgrade()` | 🟡 Medium — kernel lifecycle exists |
| **Cross-deployment** | Monolith-only OR microservice-only | Single capability binary runs in both contexts | 🔴 Critical — complete rewrite gap |
| **Commands/Queries/Events** | Ad-hoc routes | CQRS + event-sourced capability contracts | 🟡 Medium — generator scaffold exists |
| **Capability store** | None | DB-backed capability registry (Postgres + cache) | 🔴 Critical |
| **Feature flag bridge** | No bridge to CapabilityRegistry | Feature flags auto-bind to capability enable/disable | 🟡 Medium — both systems exist |
| **Capability generator** | Standalone, not wired | Generator driven from CI pipeline | 🟢 Low — generator exists, needs integration |
| **Monitoring per-capability** | App-level metrics | Per-capability latency, error rate, saturation | 🟡 Medium — metrics collector exists |
| **Capability discovery** | `/kernel/capabilities` API exists | Service mesh / internal gateway auto-discovers capabilities | 🟡 Medium — gateway exists |

### 6.2 Shared vs Monolith vs Microservice Overlap

```mermaid
graph TD
    subgraph "Shared (de jure reusable)"
        auth, events, pdf, qr, device, cache, etc.
    end
    subgraph "Monolith (de facto duplicate)"
        order_service, patient_service, result_service, etc.
    end
    subgraph "Microservices (separate impl)"
        services/order, services/patient, services/result, etc.
    end
    Shared -->|"Underutilized"| Monolith
    Shared -->|"Underutilized"| Microservices
    Monolith -->|"Duplicates"| Microservices
```

---

## 7. REUSABILITY SCORE

Scored on a 1-5 scale (5 = fully reusable across monolith + microservices):

| Capability | Current Reusability | Target Reusability | Score |
|---|---|---|---|
| `authentication` (JWT, passwords) | 4 | 5 | 🟢 |
| `audit_logging` | 4 | 5 | 🟢 |
| `event_bus` (shared `EventBus`) | 3 (monolith only) | 5 | 🟡 |
| `pdf_reporting` | 3 | 5 | 🟡 |
| `qr_generation` | 4 | 5 | 🟢 |
| `device_integration` (ASTM/HL7) | 2 (device_bridge microservice only) | 5 | 🟠 |
| `patient_management` | 1 (separate monolith + microservice) | 5 | 🔴 |
| `order_management` | 1 (separate monolith + microservice) | 5 | 🔴 |
| `result_management` | 1 (separate monolith + microservice) | 5 | 🔴 |
| `sample_tracking` | 1 (separate monolith + microservice) | 5 | 🔴 |
| `notification_service` | 3 | 5 | 🟡 |
| `clinical_intelligence` | 2 (monolith only) | 4 | 🟠 |
| `ai_interpretation` | 2 (monolith + AI microservice) | 4 | 🟠 |
| `critical_alerting` | 3 | 5 | 🟡 |
| `identity_management` | 3 | 5 | 🟡 |
| `claims_processing` | 2 (monolith only) | 4 | 🟠 |
| `consent_management` | 2 | 5 | 🟠 |
| `national_id_lookup` | 2 | 5 | 🟠 |
| `edge_platform` | 3 | 5 | 🟡 |
| `analytics` (stats) | 2 | 4 | 🟠 |
| `batch_operations` | 2 | 4 | 🟠 |
| `compliance` | 2 | 4 | 🟠 |
| `system_optimizer` | 1 | 4 | 🔴 |
| `workflow_engine` | 2 (shared/workflow exists) | 5 | 🟠 |

**Overall Reusability Score: 2.4 / 5.0** — The platform has the *foundations* for reuse (shared package) but the monolith and microservices are not consuming them in a unified capability model.

---

## 8. MIGRATION PATH: MONOLITH SERVICES → CAPABILITIES

### Phase 1 — Foundation (Weeks 1-2)

1. **Populate CapabilityRegistry** — Register all 30 feature-flag names as `CapabilityDescriptor` objects in the bootloader
2. **Wire CapabilityFlagManager** — Connect `kernel/features/capabilities.py` into the boot sequence and bridge it to `CapabilityRegistry.enable/disable`
3. **Add capability store table** — Migration to persist capability versions & states to PG

### Phase 2 — Contracts (Weeks 3-4)

4. **Promote shared/ modules** — Convert 25 single-file modules to package directories with `contract.py` + `capability.py`
5. **Define capability interface** — Each capability gets `{Name}Input`, `{Name}Output`, `execute()`, `validate()`
6. **Wire generator to CLI** — `make gen-capability name=order_management` produces a full capability package

### Phase 3 — Extraction (Weeks 5-8)

7. **Extract patient_management** — Move logic from `services/patient_service.py` + `services/patient/` into `capabilities/patient/management/`
8. **Extract order_management** — Move from `services/order_service.py` + `services/order/` into `capabilities/order/management/`
9. **Extract result_management** — Move from `services/result_service.py` + `services/result/` into `capabilities/result/management/`
10. **Extract sample_tracking** — Move from `services/sample_management` + `services/sample/` into `capabilities/sample/tracking/`

### Phase 4 — Feature Flag Bridge (Weeks 9-10)

11. **Auto-bind feature flags** — `resolve_lab_features()` returns capability states from `CapabilityRegistry`
12. **Replace `require_feature()`** — `require_feature()` now checks `capability_registry.is_enabled()`
13. **Remove feature flag redundancy** — Deprecate old string-based flag checks, unify through capability registry

### Phase 5 — Cross-Deployment (Weeks 11-12)

14. **Conditional loading** — Each capability package has `monolith.py` and `microservice.py` adapters
15. **Internal gateway routing** — Gateway decides: route to monolith's capability or microservice instance
16. **Dual-run validation** — Run both implementations, compare outputs, fail on divergence

---

## 9. PRIORITY MATRIX: BUILD vs BUY vs BORROW

| Capability | Priority (1-5) | Build | Buy | Borrow | Rationale |
|---|---|---|---|---|---|
| `patient_management` | 5 | 🟢 Build | | | Core differentiator — must own |
| `order_management` | 5 | 🟢 Build | | | Core differentiator — must own |
| `result_management` | 5 | 🟢 Build | | | Core differentiator — must own |
| `sample_tracking` | 5 | 🟢 Build | | | Core differentiator — must own |
| `authentication` | 5 | 🟢 Build | | 🔄 Borrow patterns | Integrate with Iraqi e-ID later; build JWT now |
| `audit_logging` | 5 | 🟢 Build | | | Compliance-critical, must own |
| `clinical_intelligence` | 4 | 🟢 Build | 🟡 Buy AI models | | Build orchestration, buy LLM inference |
| `ai_interpretation` | 4 | 🟡 Hybrid | 🟡 Buy LLM API | | Invest in guardrails, buy model access |
| `critical_alerting` | 4 | 🟢 Build | | | Patient safety — must own |
| `device_integration` | 4 | 🟢 Build | | 🔄 Borrow ASTM libs | ASTM/HL7 standards are fixed |
| `ehr_integration` | 4 | 🟢 Build | | | Customer-specific, must adapt |
| `notification_service` | 3 | 🟢 Build | | 🔄 Borrow Twilio | Build template engine, borrow delivery |
| `pdf_reporting` | 3 | 🟢 Build | | 🔄 Borrow WeasyPrint | Build templates, borrow rendering |
| `qr_generation` | 3 | 🟢 Build | | 🔄 Borrow qrcode | Simple library integration |
| `identity_management` | 3 | 🟢 Build | | | Integrate with national ID later |
| `national_id_lookup` | 3 | 🟡 Hybrid | 🟡 Buy gateway | 🔄 Borrow | Buy national ID gateway access |
| `batch_operations` | 3 | 🟢 Build | | | Customer workflow, must own |
| `analytics/stats` | 3 | 🟡 Hybrid | 🟡 Buy BI tool | | Build API, buy visualization |
| `compliance` | 3 | 🟢 Build | | | Regulatory, must own |
| `edge_platform` | 3 | 🟢 Build | | | Offline medical data — must own |
| `claims_processing` | 2 | 🟡 Hybrid | 🟢 Buy | | Buy insurance claim engine, integrate |
| `payments` | 2 | | 🟢 Buy | | Use Stripe/Tamara/Bank gateway |
| `workflow_engine` | 2 | 🟢 Build | | | Orchestration of lab workflows |
| `consent_management` | 2 | 🟢 Build | | | Legal requirement, must own |
| `system_optimizer` | 2 | 🟢 Build | | | Internal ops tool |
| `subscription_tiers` | 2 | 🟢 Build | | | Core business model |
| `video_consultation` | 1 | | 🟢 Buy | 🔄 Borrow Zoom API | Not core — buy or borrow |
| `telemedicine` | 1 | | 🟢 Buy | | Future expansion, not core now |
| `design_system` (UI) | 1 | 🟢 Build | | 🔄 Borrow MUI | Component library |
| `localization` | 2 | 🟢 Build | | 🔄 Borrow | Arabic RTL, i18n must be custom |
| `backup/restore` | 4 | 🟢 Build | | 🔄 Borrow pg_dump | Data integrity — must own |

### Priority Buckets

```
P0 (Critical — do first):    patient_management, order_management, result_management,
                             sample_tracking, authentication, audit_logging, backup/restore

P1 (High — weeks 3-6):       clinical_intelligence, device_integration, ehr_integration,
                             critical_alerting, notification_service, ai_interpretation

P2 (Medium — weeks 7-10):    identity_management, national_id_lookup, batch_operations,
                             analytics, pdf_reporting, qr_generation, compliance

P3 (Low — weeks 11-12):      claims_processing, workflow_engine, consent_management,
                             edge_platform, payments, subscription_tiers

P4 (Future):                  video_consultation, telemedicine, design_system, localization
```

---

## 10. RECOMMENDED CAPABILITY TAXONOMY

### Proposed grouping for the Capability Factory:

```yaml
capabilities:
  clinical:
    - patient_management
    - order_management
    - result_management
    - sample_tracking
    - clinical_intelligence
    - ai_interpretation
    - ai_anomaly_detection
    - epidemiology
    - critical_alerting
    - quality_control
    - device_integration
    - ehr_integration

  identity_security:
    - authentication
    - authorization_rbac
    - identity_management
    - national_id_lookup
    - consent_management
    - session_management
    - encryption_service

  financial:
    - claims_processing
    - payments
    - subscription_tiers
    - pricing_engine
    - fraud_detection

  communication:
    - notification_service
    - messaging
    - alerting
    - mobile_api

  infrastructure:
    - audit_logging
    - event_bus
    - workflow_engine
    - outbox_pattern
    - backup_restore
    - config_management
    - feature_flags

  observability:
    - health_checks
    - metrics_collection
    - distributed_tracing
    - logging
    - runtime_telemetry

  reporting:
    - pdf_reporting
    - qr_generation
    - barcode_generation
    - analytics
    - compliance_reports

  integration:
    - insurance_integration
    - national_id_gateway
    - ehr_gateway
    - device_gateway
    - ministry_integration

  platform:
    - multi_tenant
    - lab_management
    - admin_console
    - edge_platform
    - system_optimizer
    - batch_operations
    - api_gateway
```

---

## 11. IMPLEMENTATION CHECKLIST

- [ ] **P0:** Register all 30 feature-flag names as `CapabilityDescriptor` in bootloader
- [ ] **P0:** Add `CapabilityRegistry.register_capability()` calls for all `backend/app/services/` modules
- [ ] **P0:** Wire `CapabilityFlagManager` into boot sequence
- [ ] **P0:** Create `capabilities/` directory at repo root
- [ ] **P1:** Convert 25 single-file `shared/` modules to package directories
- [ ] **P1:** Define `CapabilityInterface` ABC with `execute()`, `validate()`, `on_activate()`, `on_deactivate()`
- [ ] **P1:** Add capability store migration (Postgres table: `capability_registry`)
- [ ] **P1:** Bridge `core/feature_flags.py` → `CapabilityRegistry` so flags control capability states
- [ ] **P2:** Extract first business capability (patient_management) from monolith+microservice into shared capability
- [ ] **P2:** Wire capability generator to `make gen-capability` CLI command
- [ ] **P2:** Add per-capability version tracking and migration support
- [ ] **P2:** Replace `require_feature()` with `capability_registry.require()`
- [ ] **P3:** Add per-capability health check endpoints
- [ ] **P3:** Add per-capability Prometheus metrics (latency, errors, saturation)
- [ ] **P3:** Conditional deployment — capability auto-selects monolith or microservice adapter
- [ ] **P4:** Internal gateway routes by capability name
- [ ] **P4:** Capability dependency graph validation at boot time
- [ ] **P4:** Zero-downtime capability hot-swap

---

*End of Capability Catalog — see `backend/app/kernel/runtime/capability_registry.py` for the registry to populate.*
