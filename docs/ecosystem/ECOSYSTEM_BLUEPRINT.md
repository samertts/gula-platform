# GULA Platform Ecosystem Blueprint

**Version:** 2.1.0  
**Status:** DRAFT  
**Last Updated:** 2026-07-17  
**Owner:** Platform Architecture Team

---

## 1. Ecosystem Vision

### 1.1 The National Healthcare OS

GULA is evolving from a laboratory information management system (LIMS) into the
**national healthcare operating system for Iraq** — a composable, extensible platform
that any healthcare domain can build upon. The vision spans three horizons:

| Horizon | Timeline | Scope | Key Milestone |
|---------|----------|-------|---------------|
| **H1: Iraq National OS** | 2026–2027 | Iraq only | 500+ labs, SNDHS integration, NHOP live |
| **H2: MENA Regional Platform** | 2027–2029 | KSA, UAE, Jordan, Egypt, Kuwait | 5 country packs, 3 language packs, regional clouds |
| **H3: Global Healthcare OS** | 2029–2032 | UK, EU, SE Asia, Africa | 12 country packs, 7 languages, openEHR/FHIR everywhere |

### 1.2 Platform Principles

1. **Kernel stability is inviolable** — the core runtime never breaks backward compatibility
2. **Everything is a pack** — no special treatment for any domain module
3. **Tenant isolation always** — every pack respects `lab_id` scoping
4. **Audit-first** — every operation through every pack writes to the hash chain
5. **Arabic-first, multilingual** — platform UI defaults to Arabic, packs provide translations
6. **Offline-capable** — edge mode degrades gracefully; packs declare offline behavior
7. **Self-healing** — every pack participates in the circuit breaker / degraded mode runtime

---

## 2. Platform Core (The Kernel)

The kernel at `backend/app/kernel/` is the permanent, never-changing foundation.
Nothing outside the kernel team modifies it. All extension happens *through* the
kernel's defined extension points.

### 2.1 Kernel Components

```
Kernel (singleton)
├── Bootloader              — 12-phase boot sequence (config → DB → plugins → modules → services)
├── LifecycleManager        — component start/stop lifecycle
├── ServiceRegistry         — named service locator
├── CapabilityRegistry      — feature capability registration with dependency graph
├── DIContainer             — DI (singleton/scoped/transient)
├── ApplicationContext      — per-request context (request_id, tenant_id, lab_id)
├── StartupManager          — ordered startup tasks
├── ShutdownManager         — priority-ordered shutdown handlers
├── PluginSystem            — sandboxed plugin loading with permission model
├── ModuleSystem            — module discovery and dependency resolution
├── EventBus                — pub/sub with outbox, inbox, DLQ, replay, snapshots
├── BackgroundProcessing    — scheduler, cron, task queue, worker pool, locks
├── FeatureManagement       — flags, kill switch, regional/tenant features
├── ConfigEngine            — validated config, secrets, runtime reload, versioning
├── MultiTenantEngine       — tenant registry, quotas, isolation
└── InternalGateway         — service discovery, routing, circuit breakers, rate limiting
```

### 2.2 What Lives in the Kernel (Never Changes)

| Component | Location | Purpose | Extension Point |
|-----------|----------|---------|-----------------|
| Authentication | `backend/app/security/auth.py` | JWT + refresh tokens, Redis JTI blacklist | Auth middleware hooks |
| Authorization (RBAC) | `backend/app/security/rbac.py` | 9 roles × 13+ permissions | Custom permission resolver |
| Multi-tenancy | `backend/app/kernel/tenant/` | Tenant registry, isolation, quotas | Tenant config hooks |
| Audit | `backend/app/models/audit_log.py` | SHA-256 hash chain, HMAC checkpoints | Audit event hooks |
| Encryption | `backend/app/core/encryption.py` | Fernet-based PII encryption | Custom field encryptors |
| Event Bus | `backend/app/kernel/event_bus/` | Pub/sub + outbox + inbox + DLQ | Custom event handlers |
| Plugin Runtime | `backend/app/kernel/plugin/` | Loader, sandbox, registry, version manager | Plugin SDK hooks |
| Feature Flags | `backend/app/kernel/features/` | Per-tenant + deployment-wide flags | Custom flag resolvers |
| API Gateway | `backend/app/kernel/gateway/` | Routing, circuit breaker, rate limiting | Custom routes |
| Config Engine | `backend/app/kernel/config/` | Validated config, secrets, runtime reload | Custom providers |
| Background Processing | `backend/app/kernel/background/` | Task queue, cron, locks, scheduler | Custom job types |
| Observability | `backend/app/kernel/` (observability) | Metrics, tracing, logging SDK | Custom metrics |

### 2.3 Kernel Config (`backend/app/kernel/integration.py`)

All kernel features enable/disable via environment variables:
```
KERNEL_ENABLE_PLUGINS=true       KERNEL_PLUGIN_DIR=/var/lib/gula/plugins
KERNEL_ENABLE_EVENT_BUS=true     KERNEL_MODULE_DIR=/var/lib/gula/modules
KERNEL_ENABLE_FEATURES=true      KERNEL_DATA_DIR=/var/lib/gula/kernel
KERNEL_ENABLE_TENANT=true        KERNEL_KILL_SWITCH=false
```

---

## 3. Extension Mechanisms

### 3.1 Plugin Architecture (Runtime-Loaded Modules)

Plugins are Python packages loaded at runtime into a sandboxed environment.
Each plugin declares its dependencies, permissions, and entry points via a
standard `Plugin` class.

**Location:** `backend/app/kernel/plugin/`  
**SDK:** `RuntimeSDK` (`backend/app/kernel/runtime_sdk.py`)

```python
# Example plugin: my_plugin/__init__.py
from app.kernel.runtime_sdk import RuntimeSDK, PluginHook

class Plugin:
    name = "my_plugin"
    version = "1.0.0"
    dependencies = ["authentication", "audit_logging"]
    permissions = ["read:patients", "write:results"]

    def initialize(self, sdk: RuntimeSDK):
        sdk.plugins.register_hook(
            self.name,
            PluginHook(name="after_result_saved", handler=self.on_result_saved)
        )

    def on_result_saved(self, context):
        result = context.get("result")
        # Custom business logic
```

**Sandbox Restrictions:** No access to `os`, `subprocess`, `socket`, `ctypes`, `multiprocessing`
(defined in `backend/app/kernel/plugin/sandbox.py`).

### 3.2 Module System (Compile-Time Modules)

Modules are Python packages registered at startup through the `ModuleRegistry`.
Unlike plugins, modules are deployed as part of the application image.

**Location:** `backend/app/kernel/module/`  
**Registration:** `ModuleRuntimeAPI.register()` via `RuntimeSDK`

### 3.3 Microservice Extensions (Separate Services)

Independent services in `services/` communicate with the monolith via:

- **REST API** — HTTP calls to `gula-backend` routes
- **Event Bus** — Shared Redis pub/sub (via `services/shared/messaging.py`)
- **Outbox Pattern** — Transactional outbox for guaranteed delivery
- **Adapter Framework** — `backend/app/interoperability/adapter_base.py` abstraction

Existing microservices: `services/device_bridge` (mature), `services/ai`, `services/lab`,
`services/order`, `services/patient`, `services/result`, `services/sample`, `services/notification`,
`services/autonomous_manager`.

### 3.4 Connector Framework (Protocol Adapters)

For integrating with external healthcare systems, the `AdapterBase` abstract class
at `backend/app/interoperability/adapter_base.py` provides:

- `AdapterBase.health()` — health check
- `AdapterBase.call_outbound()` — outbound call
- `AdapterBase.handle_inbound()` — inbound handler
- `AdapterBase.replay_outbox()` — outbox draining
- `CapabilityDenied` / `AdapterUnavailable` exceptions
- `TrustDomain`, `InteropPrincipal`, `InteropAuditEvent` — security traceability

### 3.5 AI Skill Framework (Model Plugins)

AI capabilities extend via the AI Fabric at `backend/app/ai_fabric/`:

- **AIServiceProvider protocol** — any model provider implementing `chat()` and `embed()`
- **Agent Registry** — custom agents via `AgentRegistry` (`backend/app/ai_fabric/agents/`)
- **Skill Catalog** — discoverable skills at `backend/app/skills/catalog/`
- **Local AI Engine** — `LocalAIEngine` for on-premise models

```python
# Custom AI skill
from app.ai_fabric.base import AIServiceProvider, InferenceRequest, InferenceResponse

class CustomDiagnosticModel:
    def analyze(self, patient_data: dict) -> dict:
        # Returns diagnostic suggestions
        pass

# Register with the SDK
from app.ai_fabric.sdk import UnifiedAISDK
sdk = UnifiedAISDK()
sdk.agent_registry.register(CustomDiagnosticModel, "diagnostic_assistant")
```

### 3.6 UI Extension Points

| Extension Point | Frontend | Mechanism |
|-----------------|----------|-----------|
| Dashboard Widgets | `frontend-v2/` | Plugin widget registry |
| Custom Pages | `frontend-v2/` | Route-based page injection |
| Report Templates | `backend/app/reports/` | Jinja2 template loading |
| Theme Overrides | All frontends | CSS variable injection |
| Menu Items | `frontend-v2/` | Plugin menu registration |
| Notification Templates | `backend/app/notifications/` | Template hooks |
| Patient Card Layouts | `backend/app/routes/patient_card.py` | Card template registry |

### 3.7 Data Extension Points

| Extension Point | Location | Mechanism |
|-----------------|----------|-----------|
| Custom Fields | `backend/app/models/` | JSONB metadata columns per entity |
| Custom Entities | `backend/app/kernel/module/` | SQLAlchemy table registration |
| Custom Schemas | `backend/app/validation/` | Pydantic schema injection |
| Custom Indexes | `backend/migrations/` | Alembic revision hooks |
| Report Schemas | `backend/app/reports/` | Custom report data sources |

### 3.8 Workflow Extension

The workflow engine at `backend/app/kernel/runtime_sdk.py` (`WorkflowRuntimeAPI`):

- **Custom Steps** — `WorkflowStep` with handler + compensation (Saga support)
- **Custom State Machines** — registered via `WorkflowRuntimeAPI.create_workflow()`
- **Escalation Rules** — custom escalation hooks
- **Notifications** — per-step notification handlers

```python
from app.kernel.runtime_sdk import WorkflowStep, WorkflowInstance

steps = [
    WorkflowStep(name="validate_order", handler=validate_order),
    WorkflowStep(name="process_payment", handler=process_payment, compensation=refund_payment),
]

wf = sdk.workflows.create_workflow("lab_order_fulfillment", steps, saga=True)
```

---

## 4. Pack Structure

Every pack lives in a standardized directory structure:

```
pack_<name>/
├── __init__.py                  # Plugin entry point
├── pack.json                    # Pack manifest
├── routes/                      # FastAPI routes
├── models/                      # SQLAlchemy models
├── services/                    # Business logic
├── migrations/                  # Alembic revisions
├── frontend/                    # UI widgets/components
├── templates/                   # Jinja2/HTML templates
├── i18n/                        # Translation files (ar, en, ku, tr, fa, fr)
├── tests/                       # Test suite
├── docs/                        # Pack documentation
└── assets/                      # Static assets, screenshots
```

### 4.1 Healthcare Packs

| Pack | Domain | Dependencies | Status |
|------|--------|--------------|--------|
| **LIMS Pack** | Laboratory | kernel only | **Built-in** (existing monolith) |
| **EHR Pack** | Patient Records | Patient + Result management | **Built-in** (`backend/app/ehr/`) |
| **Radiology Pack** | Imaging | Patient + Storage + Workflow | Planned |
| **Pharmacy Pack** | Dispensing | Patient + Clinical Foundation | Planned (`backend/app/pharmacy/` stub) |
| **Nursing Pack** | Clinical Care | Patient + Encounter | Planned |
| **Blood Bank Pack** | Transfusion | Patient + Sample + QC | Planned (`backend/app/blood_bank/` stub) |
| **Critical Care Pack** | ICU | Encounter + Clinical Foundation | `backend/app/critical_care/` |
| **Public Health Pack** | Surveillance | Patient + Population Health | Via AI Fabric |
| **EMS Pack** | Emergency | Encounter + Location | Planned |
| **Hospital Pack** | Facility Mgmt | Provider + Encounter + Beds | `backend/app/hospital/` |

### 4.2 Government Packs

| Pack | Description | Dependencies |
|------|-------------|--------------|
| **SNDHS Pack** | Iraqi National Health Data System | Patient + Audit + Encryption |
| **NHOP Pack** | National Health Oversight Platform | SNDHS + Analytics |
| **Compliance Pack** | Regulatory reporting | Audit + Patient |
| **Audit Pack** | Government auditing | Audit + Workflow |
| **National ID Pack** | National ID card integration | Patient + Encryption |

### 4.3 Education Packs

| Pack | Description |
|------|-------------|
| **Learning Pack** | CME/CPD tracking, e-learning modules |
| **Training Pack** | Lab technician simulation, proficiency testing |
| **Certification Pack** | Credentialing, license management |

### 4.4 Research Packs

| Pack | Description |
|------|-------------|
| **Population Health Pack** | Cohort analysis, epidemiological studies |
| **Clinical Trials Pack** | Trial management, patient enrollment, data collection |
| **Analytics Pack** | Advanced BI, ML model training |

### 4.5 Industry Packs

| Pack | Description |
|------|-------------|
| **Pharma Pack** | Drug trial recruitment, adverse event reporting |
| **Insurance Pack** | Claims management, prior authorization, billing |
| **Device Manufacturer Pack** | Instrument monitoring, predictive maintenance |

### 4.6 Country Packs

| Country | Code | Regulatory Challenges |
|---------|------|----------------------|
| Iraq | IQ | SNDHS, National ID, Arabic-first |
| Saudi Arabia | SA | NPHIES, Sehhaty, CBAHI |
| UAE | AE | NABIDH, Malaffi, Riayati |
| Jordan | JO | HAK, National EHR |
| Egypt | EG | Unified Medical Record |
| Kuwait | KW | KICS, National Health ID |
| UK | GB | NHS Digital, GP Connect |
| EU | EU | GDPR, openEHR, EHDS |

### 4.7 Language Packs

| Language | Code | RTL | Status |
|----------|------|-----|--------|
| Arabic | ar | Yes | **Complete** |
| English | en | No | **Complete** |
| Kurdish (Sorani) | ku | Yes | In Development |
| Turkish | tr | No | Planned |
| Farsi | fa | Yes | Planned |
| French | fr | No | Planned |

---

## 5. Marketplace Architecture

### 5.1 Marketplace Components

```
gula-marketplace (microservice)
├── Catalog Service           — Pack search, browse, recommendations
├── Listing Service           — CRUD for pack listings, versions
├── Pricing Service           — Pricing tiers, currencies, discounts
├── Payment Service           — Payment gateway integration
├── Subscription Service      — Billing, renewals, upgrades
├── Download Service          — Secure pack distribution
├── Licensing Service         — License key generation, DRM
├── Rating Service            — Reviews, ratings, verified purchases
├── Security Scanner          — Automated malware/vulnerability scanning
└── Analytics Service         — Sales, usage, developer analytics
```

### 5.2 Pack Distribution Flow

1. Developer creates pack → packs into `.gpk` (GULA Pack)
2. Developer uploads to marketplace staging
3. Automated security scan + compatibility check runs
4. Platform certification review (manual for paid packs)
5. Pack published → available on `gula-marketplace`
6. Customer discovers, purchases, installs
7. Runtime verifies license → loads pack
8. Usage telemetry sent (opt-in)

### 5.3 Versioning

All packs follow strict SemVer:
- **MAJOR** — breaking API/model changes (requires migration)
- **MINOR** — backward-compatible feature additions
- **PATCH** — bug fixes, security patches

Dependency resolution via `backend/app/kernel/module/resolver.py`:
```
pack_radiology v1.2.0 depends on pack_storage >=2.0.0, <3.0.0
```

### 5.4 Monetization

| Model | Description | Platform Commission |
|-------|-------------|---------------------|
| Free | Open-source packs, community | 0% |
| One-Time | Single purchase, perpetual | 20% |
| Subscription | Monthly/yearly billing | 15% |
| Usage-Based | Per-transaction, per-patient | 10% |
| Freemium | Free tier + paid upgrade | 20% (on paid) |
| Enterprise | Custom pricing, volume license | Negotiable |

---

## 6. Platform Governance

### 6.1 Governance Board

| Role | Appointment | Responsibilities |
|------|-------------|-----------------|
| Platform Architect | Kernel team lead | Core architecture decisions |
| Security Officer | CISO | Security review, vulnerability disclosure |
| Clinical Lead | Chief Medical Informatics Officer | Clinical safety, regulatory compliance |
| Marketplace Manager | Product | Pack certification, quality gates |
| Community Lead | Developer relations | Community standards, Code of Conduct |

### 6.2 Pack Certification Levels

| Level | Requirements | Review Type | SLA |
|-------|--------------|-------------|-----|
| **Community** | Open source, passes security scan | Automated | <1 hour |
| **Verified** | Community + documentation complete + tests pass | Automated + spot-check | <24 hours |
| **Certified** | Verified + clinical safety review + performance testing | Full manual review | <1 week |
| **Enterprise** | Certified + SLA + audit trail + dedicated support | Full review + legal | <2 weeks |

### 6.3 Quality Gates

1. **Security Scan** — no critical/high CVEs, no hardcoded secrets, no malware
2. **Compatibility Check** — declared deps resolve, no kernel API conflicts
3. **Migration Idempotency** — Alembic revisions pass downgrade/upgrade round-trip
4. **Tenant Isolation** — all queries filter by `lab_id`
5. **Audit Coverage** — all mutations write audit log entries
6. **Performance Benchmark** — p99 latency <500ms for declared critical endpoints
7. **i18n Baseline** — Arabic translations for all user-facing strings

---

## 7. Ecosystem Roles

### 7.1 Platform Owner (GULA)

- Maintains the kernel (`backend/app/kernel/`)
- Operates the marketplace (`gula-marketplace`)
- Certifies packs
- Provides platform SDK and documentation
- Manages data sovereignty and compliance

### 7.2 Pack Developer

- Builds packs using the Plugin SDK or Microservice SDK
- Submits to marketplace for certification
- Maintains pack versions and migrations
- Responds to security vulnerabilities
- Can be: internal team, partner ISV, government agency, open-source contributor

### 7.3 System Integrator

- Deploys and configures packs for end customers
- Builds custom connectors using `AdapterBase`
- Provides local implementation and training
- Maintains country-specific customizations

### 7.4 End Customer

- Laboratory, hospital, clinic, or government health authority
- Purchases packs from marketplace
- Operates GULA instance (self-hosted or managed)
- Can be single-tenant or multi-tenant

---

## 8. Revenue Model

### 8.1 Marketplace Commission

| Transaction Type | Commission | Platform Provides |
|------------------|------------|-------------------|
| Pack sale | 20% | Distribution, certification, hosting |
| Subscription | 15% | Billing, support, marketplace visibility |
| Enterprise deal | Negotiable | Co-selling, compliance, SLA |

### 8.2 Platform Licensing

| Tier | Price (IQD/mo) | Labs | Features |
|------|----------------|------|----------|
| Starter | Free | 1 | Core LIMS, 3 device integrations |
| Growth | 500,000 | 5 | All packs, AI, analytics, 10 devices |
| Enterprise | Custom | Unlimited | Everything, SLA, dedicated support, on-prem |

### 8.3 Implementation Services

- Standard implementation: $X per laboratory
- Custom integration: T&M based
- Training: Per-seat pricing

### 8.4 Revenue Projections (3-Year)

| Stream | Year 1 | Year 2 | Year 3 |
|--------|--------|--------|--------|
| SaaS subscriptions | $120K | $480K | $1.2M |
| Marketplace commission | $10K | $120K | $600K |
| Implementation services | $80K | $200K | $400K |
| Enterprise licensing | $50K | $300K | $1.0M |
| **Total** | **$260K** | **$1.1M** | **$3.2M** |

---

## 9. Technical Requirements

### 9.1 Runtime Isolation

| Isolation Level | Mechanism | Use Case |
|-----------------|-----------|----------|
| Process | Docker container | Microservice packs |
| Python import | Plugin sandbox (`sandbox.py`) | Plugin packs |
| Tenant | `lab_id` filters | Multi-tenant packs |
| Data | Separate DB schemas | Government/enterprise packs |
| Network | Network policies | Microservice packs |

### 9.2 Versioning Strategy

- **Kernel version** — MAJOR.MINOR.PATCH (`2.1.0`)
- **API version** — URL-based versioning (`/api/v1/`, `/api/v2/`)
- **Event versioning** — `Event.version` field for schema evolution
- **Capability versioning** — Each `CapabilityDescriptor` carries its own version
- **Plugin/Module versioning** — SemVer in `Plugin.version` / `ModuleDescriptor.version`
- **Database migration versioning** — Alembic revision IDs (timestamps)

### 9.3 Dependency Management

Dependency resolution follows topological sort via `CapabilityRegistry.topological_sort()`.
Circular dependencies are detected and rejected.

```mermaid
digraph G {
    "authentication" -> "authorization_rbac"
    "authorization_rbac" -> "patient_management"
    "patient_management" -> "order_management"
    "order_management" -> "result_management"
    "result_management" -> "critical_alerting"
    "patient_management" -> "master_patient_index"
    "order_management" -> "sample_tracking"
}
```

### 9.4 Resource Budget

Each pack declares its resource profile in `pack.json`:
```json
{
    "resources": {
        "cpu": "0.5",
        "memory": "512Mi",
        "storage": "1Gi",
        "connections": 10
    }
}
```

Runtime enforces quotas via the MultiTenantEngine (`backend/app/kernel/tenant/quotas.py`).

### 9.5 Health Integration

Every pack must expose a health endpoint registered in `CapabilityAPI`:
```python
CapabilityAPI(
    path="/health/pack/{pack_name}",
    method="GET",
    auth_required=False
)
```

The kernel aggregates all pack health into `/health/deep`.

### 9.6 Feature Flag Integration

Packs declare feature flags in `pack.json`:
```json
{
    "features": {
        "advanced_qc": {
            "description": "Enable Westgard rules and multi-rule QC",
            "default": false,
            "tier": "enterprise"
        }
    }
}
```

Runtime registers these via `FeatureFlagManager.register()`.

---

## Appendix A: Kernel API Deprecation Policy

1. **Deprecation notice** — published 2 MAJOR versions before removal
2. **Migration path** — provided for every deprecated API
3. **Backward compatibility** — maintained within MAJOR version
4. **Removal signals** — `CapabilityStatus.DEPRECATED` → `CapabilityStatus.RETIRED`

## Appendix B: Pack Template Structure

```
pack_<name>/
├── pack.json                          # Manifest: name, version, deps, permissions, features
├── __init__.py                        # Plugin class
├── routes/
│   └── __init__.py                    # Route registration via APIRouter
├── models/
│   └── __init__.py                    # SQLAlchemy models (new tables)
├── services/
│   └── __init__.py                    # Business logic
├── migrations/
│   ├── env.py                         # Alembic env (imports existing base)
│   └── versions/
│       └── 0001_<description>.py      # Alembic revision
├── frontend/
│   └── widgets/                       # UI widget components
├── templates/                         # Jinja2 templates
├── i18n/
│   ├── ar.json                        # Arabic translations
│   └── en.json                        # English translations
├── tests/
│   ├── test_routes.py
│   ├── test_services.py
│   └── test_migrations.py
├── docs/
│   ├── README.md
│   ├── API.md
│   └── DEPLOYMENT.md
└── assets/
    ├── icon.png
    └── screenshots/
```

## Appendix C: Glossary

| Term | Definition |
|------|------------|
| Pack | A versioned, independently deployable unit of healthcare functionality |
| Plugin | Runtime-loaded pack that runs inside the kernel sandbox |
| Module | Compile-time pack deployed as part of the application image |
| Connector | Protocol adapter implementing `AdapterBase` for external system integration |
| Kernel | The permanent runtime foundation at `backend/app/kernel/` |
| AI Skill | A registered AI capability in the AI Fabric |
| Capability | A registered platform feature in the CapabilityRegistry |
| Tenant | An isolated laboratory or healthcare organization |
