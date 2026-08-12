# GULA Platform Extension Guide

**Version:** 2.1.0  
**Status:** DRAFT  
**Last Updated:** 2026-07-17

---

## 1. Extension Types

GULA supports eight categories of extensions. Choose the type that matches your
use case:

| Extension Type | Runtime | Difficulty | Certification | Example |
|---------------|---------|-----------|---------------|---------|
| API Extensions | Plugin / Module | Medium | Verified | Custom lab calculation endpoint |
| Data Extensions | Plugin / Module | Medium | Verified | Custom patient field for genetics |
| Workflow Extensions | Plugin / Module | High | Certified | Custom order approval workflow |
| UI Extensions | Frontend | Low | Community | Custom dashboard widget |
| Integration Extensions | Connector | High | Enterprise | PACS system adapter |
| AI Extensions | AI Skill / Agent | Medium | Certified | Custom diagnostic model |
| Report Extensions | Template / Plugin | Low | Community | Custom PDF report layout |
| Theme Extensions | CSS / Assets | Low | Community | Hospital-branded theme |

### 1.1 API Extensions

Add new REST endpoints, WebSocket handlers, or gRPC services.

**Mechanisms:**

| Mechanism | Location | Best For |
|-----------|----------|----------|
| FastAPI APIRouter | Pack `routes/` | New REST API endpoints |
| Plugin Hooks | `PluginRuntimeAPI.register_hook()` | Modify request/response lifecycle |
| Middleware Hooks | Custom ASGI middleware | Cross-cutting concerns |
| Internal Gateway Routes | `InternalRouter.register()` | Internal service-to-service APIs |

**Example — Adding a custom endpoint:**

```python
# pack_demo/routes/__init__.py
from fastapi import APIRouter, Depends
from app.security.auth import get_current_user

router = APIRouter(prefix="/api/v1/demo", tags=["demo"])

@router.get("/health")
async def demo_health():
    return {"status": "healthy", "pack": "demo", "version": "1.0.0"}

@router.get("/patients/{patient_id}/custom-score")
async def custom_patient_score(
    patient_id: str,
    user = Depends(get_current_user),
):
    # Custom business logic here
    # Must filter by user.lab_id for tenant isolation
    return {"patient_id": patient_id, "custom_score": 0.85}
```

### 1.2 Data Extensions

Extend the data model without modifying core tables.

**Mechanisms:**

| Mechanism | Description | Example |
|-----------|-------------|---------|
| JSONB metadata | All core entities have a `metadata` JSONB column | `patient.metadata["genetic_markers"]` |
| Custom SQLAlchemy tables | Register tables in separate metadata | `pack_demo.models.CustomEntity` |
| Extension tables | 1:1 extension tables with FK to core entity | `PatientExtension(patient_id FK, ...)` |
| Materialized views | Pre-joined read models | Custom analytics aggregation |
| Computed fields | Server-side SQL generated columns | `age = DATE_PART('year', AGE(dob))` |

**Example — Adding custom fields via JSONB:**

```python
# No code change needed — just use the metadata field
patient = db_session.get(Patient, patient_id)
patient.metadata["genetic_markers"] = ["BRCA1", "BRCA2"]
patient.metadata["risk_score"] = 0.75
```

**Example — Extension table:**

```python
# pack_demo/models/patient_genetics.py
from sqlalchemy import Column, String, Float, ForeignKey
from app.models.base import Base

class PatientGenetics(Base):
    __tablename__ = "patient_genetics"

    patient_id = Column(String, ForeignKey("patients.id"), primary_key=True)
    genetic_marker = Column(String, primary_key=True)
    risk_score = Column(Float, default=0.0)
    interpretation = Column(String)
```

**Migration for extension table:**

```python
# migrations/versions/0001_add_patient_genetics.py
from alembic import op
import sqlalchemy as sa

def _table_exists(name):
    conn = op.get_bind()
    return conn.dialect.has_table(conn, name)

def upgrade():
    if not _table_exists("patient_genetics"):
        op.create_table(
            "patient_genetics",
            sa.Column("patient_id", sa.String(), nullable=False),
            sa.Column("genetic_marker", sa.String(), nullable=False),
            sa.Column("risk_score", sa.Float(), default=0.0),
            sa.Column("interpretation", sa.String()),
            sa.PrimaryKeyConstraint("patient_id", "genetic_marker"),
            sa.ForeignKeyConstraint(["patient_id"], ["patients.id"]),
        )

def downgrade():
    if _table_exists("patient_genetics"):
        op.drop_table("patient_genetics")
```

### 1.3 Workflow Extensions

Custom state machines, approval chains, and automation flows.

**Mechanisms:**

| Mechanism | Location | Best For |
|-----------|----------|----------|
| WorkflowRuntimeAPI | `kernel/runtime_sdk.py` | Custom multi-step workflows |
| Order State Machine | `domain/order_state.py` | Custom order states |
| Workflow Engine | `national/workflow_runtime/` | Complex BPMN-style workflows |
| Saga Pattern | `WorkflowRuntimeAPI` with compensation | Distributed transactions |

**Example — Custom order approval workflow:**

```python
from app.kernel.runtime_sdk import WorkflowStep, WorkflowRuntimeAPI

class OrderApprovalWorkflow:
    def __init__(self, api: WorkflowRuntimeAPI):
        self.api = api

    async def create(self, order_id: str, amount: float):
        steps = [
            WorkflowStep(
                name="validate_order",
                handler=lambda ctx: self._validate(ctx),
            ),
            WorkflowStep(
                name="manager_approval",
                handler=lambda ctx: self._request_approval(ctx),
                timeout=86400.0,  # 24 hours
            ),
            WorkflowStep(
                name="process_order",
                handler=lambda ctx: self._process(ctx),
                compensation=lambda ctx: self._reverse(ctx),
            ),
        ]
        wf = self.api.create_workflow(
            f"order_approval_{order_id}",
            steps,
            saga=True,
        )
        return wf.id

    def _validate(self, ctx):
        # Validation logic
        return {"validated": True}

    def _request_approval(self, ctx):
        # Send notification to manager
        return {"approved": True}

    def _process(self, ctx):
        # Execute order
        return {"processed": True}

    def _reverse(self, ctx):
        # Compensation — reverse the order
        pass
```

### 1.4 UI Extensions

Extend the GULA frontend applications.

| Extension Point | Frontend | Mechanism |
|-----------------|----------|-----------|
| Dashboard Widgets | `frontend-v2/` | React component registry |
| Custom Pages | `frontend-v2/` | Dynamic route injection |
| Patient Card Layouts | `backend/app/routes/patient_card.py` | Card template registry |
| Report Templates | Jinja2 templates | Template loading from pack dir |
| Notification Templates | `backend/app/notifications/` | Template hooks |
| Menu Items | `frontend-v2/` | Plugin menu registration |
| Theme Overrides | CSS variables | Theme CSS injection |

**Example — Dashboard widget registration (React):**

```jsx
// frontend-v2/src/plugins/registry.js
export const widgetRegistry = {
  'demo-widget': {
    component: React.lazy(() => import('./widgets/DemoWidget')),
    title: 'Demo Widget',
    icon: 'chart',
    defaultSize: { w: 3, h: 2 },
    permissions: ['read:dashboard'],
  },
};

// widget registration hook
export function useRegisterWidget(widgetId, widgetConfig) {
  useEffect(() => {
    widgetRegistry[widgetId] = widgetConfig;
    return () => { delete widgetRegistry[widgetId]; };
  }, [widgetId]);
}
```

### 1.5 Integration Extensions

Connect GULA to external healthcare systems.

**Mandatory base class:** `AdapterBase` at `backend/app/interoperability/adapter_base.py`

**Example — PACS system connector:**

```python
from app.interoperability.adapter_base import (
    AdapterBase, AdapterHealth, AdapterStatus,
    AdapterContext, AdapterResult,
    AdapterUnavailable,
)
from app.interoperability.trust_domain import TrustDomain

class PACSAdapter(AdapterBase):
    name = "pacs_adapter"
    domain = TrustDomain(
        name="pacs_system",
        capabilities={"store_images", "retrieve_study", "schedule_acquisition"},
    )

    def __init__(self, pacs_url: str, api_key: str):
        super().__init__(name=self.name, domain=self.domain)
        self.pacs_url = pacs_url
        self.api_key = api_key

    async def health(self) -> AdapterHealth:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{self.pacs_url}/health", timeout=5)
                if resp.status_code == 200:
                    return AdapterHealth(status=AdapterStatus.OK)
                return AdapterHealth(status=AdapterStatus.DEGRADED, detail=resp.text)
        except Exception as e:
            return AdapterHealth(status=AdapterStatus.UNAVAILABLE, detail=str(e))

    async def call_outbound(
        self, operation: str, payload: dict, context: AdapterContext,
    ) -> AdapterResult:
        self.check_capability(operation)
        # Implementation...
        return AdapterResult(ok=True, payload={"study_uid": "1.2.3.4"})

    async def handle_inbound(
        self, operation: str, payload: dict, context: AdapterContext,
    ) -> AdapterResult:
        self.check_capability(operation)
        # Implementation...
        return AdapterResult(ok=True)

    async def replay_outbox(self) -> int:
        return 0
```

### 1.6 AI Extensions

Add custom AI models, agents, and skills to the AI Fabric.

**Mechanisms:**

| Mechanism | Location | Best For |
|-----------|----------|----------|
| AIServiceProvider | `ai_fabric/base.py` | Custom LLM/model provider |
| Agent Registration | `ai_fabric/agents/registry.py` | Custom AI agents |
| Skill Catalog | `skills/catalog/` | Reusable AI skills |
| RAG Collections | `ai_fabric/rag.py` | Custom knowledge bases |

**Example — Custom AI diagnostic skill:**

```python
from app.ai_fabric.base import InferenceRequest, InferenceResponse
from app.ai_fabric.sdk import UnifiedAISDK

class SepsisDetector:
    """AI skill for early sepsis detection from lab results."""

    name = "sepsis_detector"
    version = "1.0.0"
    description = "Detect early signs of sepsis from lab values"

    def __init__(self, sdk: UnifiedAISDK):
        self.sdk = sdk

    def analyze(self, patient_data: dict, lab_results: list[dict]) -> dict:
        # Custom analysis logic
        score = self._calculate_sepsis_score(lab_results)
        return {
            "sepsis_risk": score,
            "suspected": score > 0.5,
            "contributing_factors": self._find_factors(lab_results),
            "recommendation": self._get_recommendation(score),
        }

    def _calculate_sepsis_score(self, results):
        # Implement qSOFA/SIRS criteria
        return 0.0

    def _find_factors(self, results):
        return []

    def _get_recommendation(self, score):
        if score > 0.7:
            return "Immediate clinical review required"
        if score > 0.4:
            return "Monitor closely, repeat labs in 4 hours"
        return "No immediate action required"


# Register with the AI Fabric
from app.ai_fabric.sdk import UnifiedAISDK
from app.ai_fabric.agents.base import AgentContext

sdk = UnifiedAISDK()

class SepsisAgent:
    def run(self, context: AgentContext, input_data: dict) -> dict:
        detector = SepsisDetector(sdk)
        return detector.analyze(
            input_data.get("patient", {}),
            input_data.get("lab_results", []),
        )

sdk.agent_registry.register(
    "sepsis_detector",
    SepsisAgent(),
    tags=["clinical", "emergency", "sepsis"],
    task_types=["sepsis_detection", "critical_care_screening"],
)
```

### 1.7 Report Extensions

Custom reports and dashboards.

**Mechanisms:**

| Mechanism | Location | Example |
|-----------|----------|---------|
| Jinja2 Templates | Pack `templates/` | Custom PDF report |
| Chart Data Sources | Python data queries | Dashboard chart data |
| Excel Export | openpyxl-based generation | Monthly lab statistics |
| CSV Export | CSV serialization | Data export for analysts |

**Example — Custom report:**

```python
# pack_demo/services/reports.py
from jinja2 import Environment, FileSystemLoader

class MonthlyLabReport:
    def __init__(self, db_session):
        self.db = db_session
        self.env = Environment(loader=FileSystemLoader("templates"))

    async def generate(self, lab_id: str, month: str) -> str:
        data = await self._collect_data(lab_id, month)
        template = self.env.get_template("monthly_report.html")
        return template.render(**data)

    async def _collect_data(self, lab_id: str, month: str) -> dict:
        # Query results for given lab/month
        return {
            "lab_name": "Central Lab",
            "month": month,
            "total_tests": 1500,
            "by_department": {"hematology": 500, "chemistry": 600, "microbiology": 400},
            "turnaround_times": {"avg": 4.5, "p95": 8.2},
            "critical_results": 25,
            "qc_failures": 3,
        }
```

### 1.8 Theme Extensions

Custom branding and styling.

```css
/* themes/hospital_brand.css */
:root {
    --gula-primary: #1a73e8;
    --gula-secondary: #34a853;
    --gula-accent: #fbbc04;
    --gula-background: #f8f9fa;
    --gula-text: #202124;
    --gula-font-family: 'Cairo', 'Noto Sans Arabic', sans-serif;
}
```

---

## 2. Extension Points Reference

### 2.1 Kernel Extension Points

| Extension Point | Location | Method | Description |
|-----------------|----------|--------|-------------|
| Plugin Hooks | `RuntimeSDK.plugins` | `register_hook()` | Lifecycle hooks (startup, shutdown, request) |
| Module Registration | `RuntimeSDK.modules` | `register()` | Register a module with the kernel |
| Service Registration | `RuntimeSDK` | `register_service()` | Make a service available via DI |
| Event Subscriptions | `EventBus` | `subscribe()` | Subscribe to domain events |
| Routes | `InternalRouter` | `register()` | Internal routing for extensions |
| Capability Registration | `CapabilityRegistry` | `register()` | Declare platform capabilities |
| Feature Flags | `FeatureFlagManager` | `register()` | Register new feature flags |

### 2.2 Event Hooks

**Available hook points** (register via `PluginRuntimeAPI.register_hook()`):

| Hook Name | Phase | Context | Description |
|-----------|-------|---------|-------------|
| `before_startup` | startup | `{}` | Before platform starts |
| `after_startup` | startup | `{}` | After platform is ready |
| `before_shutdown` | shutdown | `{}` | Before platform shuts down |
| `after_shutdown` | shutdown | `{}` | After platform stops |
| `before_request` | request | `{request, path, method}` | Before API request processing |
| `after_request` | request | `{request, response}` | After API request completes |
| `before_db_query` | database | `{query}` | Before SQL execution |
| `after_db_query` | database | `{query, result}` | After SQL execution |
| `before_result_save` | domain | `{result, user}` | Before lab result is saved |
| `after_result_save` | domain | `{result, user}` | After lab result is saved |
| `before_order_create` | domain | `{order, user}` | Before order creation |
| `after_order_create` | domain | `{order, user}` | After order creation |

### 2.3 Domain Events (publish/subscribe via EventBus)

| Event Name | Data | Description |
|------------|------|-------------|
| `PatientCreated` | `{patient_id, lab_id}` | New patient registered |
| `PatientUpdated` | `{patient_id, lab_id, changes}` | Patient data changed |
| `OrderCreated` | `{order_id, lab_id, patient_id}` | New lab order |
| `OrderStateChanged` | `{order_id, from_state, to_state}` | Order state machine transition |
| `SampleCollected` | `{sample_id, order_id}` | Specimen collected |
| `ResultEntered` | `{result_id, order_id}` | Result entered into system |
| `ResultValidated` | `{result_id, validated_by}` | Result clinically validated |
| `CriticalAlertTriggered` | `{result_id, patient_id, value}` | Critical value alert |
| `DocumentUploaded` | `{document_id, patient_id}` | Document uploaded |
| `WorkflowCreated` | `{workflow_id, type}` | Workflow instance started |
| `WorkflowCompleted` | `{workflow_id, type, status}` | Workflow reached terminal state |
| `ConsentGranted` | `{patient_id, scope}` | Patient consent updated |
| `ConsentRevoked` | `{patient_id}` | Patient consent withdrawn |
| `DeviceResultReceived` | `{device_id, raw_data}` | Device bridge sent a result |

### 2.4 Published Event Hook Pattern

```python
# Subscribe to an event from a plugin
from app.kernel.integration import get_kernel

kernel = get_kernel()
event_bus = kernel.get_component("event_bus")

def on_critical_alert(event):
    # Custom logic — send to custom notification channel
    alert_data = event.data
    print(f"Critical alert: {alert_data}")

event_bus.subscribe("CriticalAlertTriggered", on_critical_alert)
```

---

## 3. SDK Documentation

### 3.1 Authentication

Extensions authenticate using the standard GULA JWT mechanism.

```python
from app.security.auth import get_current_user, require_permissions
from fastapi import Depends

@router.get("/secure-endpoint")
async def secure_endpoint(user = Depends(get_current_user)):
    # user.lab_id — access current lab
    # user.role — access user role
    # user.permissions — access permission set
    return {"lab_id": user.lab_id}

@router.post("/admin-only")
@require_permissions(["admin:write"])
async def admin_only(user = Depends(get_current_user)):
    return {"admin": True}
```

### 3.2 API Patterns

All API extensions should follow GULA conventions:

- **Path prefix:** `/api/v1/<pack_name>/...`
- **Tenant isolation:** All queries MUST filter by `lab_id = user.lab_id`
- **Pagination:** Use `skip`/`limit` query parameters (default: skip=0, limit=100)
- **Error format:** `{"detail": "Arabic message", "error_code": "ERR_001"}`
- **Audit:** All mutations MUST call `audit_log()` from `backend/app/models/audit_log.py`
- **Optimistic locking:** Check `version` column on `LabResult` mutations

```python
@router.get("/patients")
async def list_patients(
    skip: int = 0,
    limit: int = 100,
    user = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    patients = db.query(Patient).filter(
        Patient.lab_id == user.lab_id
    ).offset(skip).limit(limit).all()
    return patients
```

### 3.3 Event Bus Integration

```python
from app.kernel.event_bus.events import Event
from app.kernel.integration import get_kernel

kernel = get_kernel()
event_bus = kernel.get_component("event_bus")

# Publish an event
event_bus.publish(Event(
    name="CustomEventName",
    data={"my_data": "value"},
    source="my_extension",
    tenant_id="lab_123",
))

# Subscribe to events
def my_handler(event: Event):
    print(f"Received: {event.name}")

event_bus.subscribe("OrderCreated", my_handler)
```

### 3.4 Data Access Patterns

```python
from sqlalchemy.orm import Session
from app.database import get_db
from fastapi import Depends

# Read via ORM (standard approach)
@router.get("/items/{item_id}")
async def get_item(
    item_id: str,
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    item = db.query(MyModel).filter(
        MyModel.id == item_id,
        MyModel.lab_id == user.lab_id,  # ALWAYS filter by lab_id
    ).first()
    if not item:
        raise HTTPException(status_code=404)
    return item

# Write with audit logging
from app.models.audit_log import audit_log

@router.post("/items")
async def create_item(
    data: ItemCreate,
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    item = MyModel(lab_id=user.lab_id, **data.dict())
    db.add(item)
    db.flush()  # Get item.id before commit
    audit_log(
        db, action="create", entity="my_entity",
        entity_id=item.id, lab_id=user.lab_id,
        user_id=user.id, new_values=data.dict(),
    )
    db.commit()
    return item
```

### 3.5 AI Fabric Integration

```python
from app.ai_fabric.sdk import UnifiedAISDK

sdk = UnifiedAISDK()

# Chat completion
response = await sdk.chat("Analyze these lab results: ...")

# RAG query
result = await sdk.rag.query("What is the treatment for hyperkalemia?")

# Embedding
vectors = await sdk.embed(["Patient has elevated creatinine"])

# Agent execution
context = sdk.agents.create_context(user_id="user_1", lab_id="lab_1")
result = sdk.agents.run("clinical_decision_support", context, {
    "patient_id": "pat_123",
    "lab_results": [...],
})
```

---

## 4. Extension Lifecycle

### 4.1 Development

1. **Scaffold:** `gula-cli create-extension pack_demo --type plugin`
2. **Implement:** Write routes, models, services, hooks
3. **Register:** Declare in `pack.json`:
   ```json
   {
     "name": "pack_demo",
     "version": "1.0.0",
     "type": "plugin",
     "dependencies": {
       "patient_management": ">=2.0.0"
     },
     "permissions": ["read:patients", "write:results"],
     "features": {
       "advanced_scoring": {"default": false}
     }
   }
   ```
4. **Events:** Register domain events your pack publishes/subscribes to
5. **Tests:** Write pytest tests in `tests/`

### 4.2 Testing

```bash
# Unit tests
cd backend && python -m pytest tests/pack_demo/ -v

# Integration tests (requires DB)
cd backend && python -m pytest tests/pack_demo/test_integration.py -v

# Migration round-trip
cd backend && alembic downgrade -1 && alembic upgrade head

# Security scan
bandit -ll -ii pack_demo/
safety check -r pack_demo/requirements.txt
```

### 4.3 Certification

1. Submit pack via marketplace developer dashboard
2. Automated checks:
   - Security scan passes
   - Compatible kernel API version
   - All migrations idempotent
   - Tests pass
   - Audit coverage verified
3. Manual review (for Certified+):
   - Code review
   - Clinical safety review (clinical packs)
   - Performance benchmark
4. Certification result:
   - ✅ Pass → published
   - ❌ Fail → report with remediation items
   - ⏳ Conditional → minor issues, can publish as Community

### 4.4 Publishing

```bash
# Package extension
gula-cli pack build pack_demo/
# Creates: pack_demo-1.0.0.gpk

# Upload to marketplace
gula-cli pack push pack_demo-1.0.0.gpk --visibility public

# Version publish
gula-cli pack publish pack_demo@1.0.0
```

---

## 5. Best Practices

### 5.1 Security

- **Never trust user input** — validate all inputs with Pydantic
- **Always filter by `lab_id`** — even read queries
- **Audit all mutations** — use `audit_log()` for every write
- **No hardcoded secrets** — use `config.py` env vars
- **Sandbox limitations** — don't use blocked modules (os, subprocess, socket)
- **SQL injection** — use ORM parameters, never string formatting

### 5.2 Performance

- **N+1 queries** — eager-load relationships with `joinedload()`
- **Caching** — use Redis cache for expensive queries
- **Pagination** — never return unbounded result sets
- **Async** — use async endpoints for I/O-bound operations
- **Connection pool** — don't create raw connections, use `get_db` dependency

### 5.3 Compatibility

- **Pin kernel API version** in `pack.json` dependencies
- **Deprecation** — migrate to new APIs before old ones are removed
- **Backward compat** — don't remove fields from responses
- **Migration idempotency** — use `_table_exists()`, `_has_column()` guards
- **Event schema evolution** — increment `Event.version` for breaking changes

### 5.4 Internationalization (i18n)

- All user-facing strings MUST have Arabic translations
- Use the `i18n/` directory with `ar.json` and `en.json` files
- Date/time formatting: use Arabic numerals for Arabic locale
- RTL support: declare in `pack.json` as `rtl: true`

---

## 6. Packaging Guide

### 6.1 Pack Manifest Format

```json
{
  "name": "pack_name",
  "display_name": {
    "ar": "اسم الحزمة",
    "en": "Pack Name"
  },
  "version": "1.0.0",
  "type": "plugin",
  "description": {
    "ar": "وصف الحزمة بالعربية",
    "en": "English description"
  },
  "author": {
    "name": "Developer Name",
    "email": "dev@gula.health",
    "website": "https://partner.gula.health"
  },
  "license": "MIT",
  "min_kernel_version": "2.1.0",
  "max_kernel_version": "3.0.0",
  "dependencies": {
    "patient_management": ">=2.0.0",
    "audit_logging": ">=2.0.0"
  },
  "permissions": ["read:patients", "write:results"],
  "features": {
    "advanced_mode": {
      "description": {"en": "Enable advanced features"},
      "default": false,
      "tier": "enterprise"
    }
  },
  "events": {
    "publishes": ["CustomEvent"],
    "subscribes": ["OrderCreated", "ResultEntered"]
  },
  "resources": {
    "cpu": "0.25",
    "memory": "256Mi",
    "storage": "500Mi"
  },
  "certification": "community",
  "icon": "assets/icon.png",
  "screenshots": ["assets/screenshot_1.png"],
  "tags": ["laboratory", "analytics"],
  "categories": ["clinical", "analytics"],
  "rtl": true,
  "languages": ["ar", "en"]
}
```

### 6.2 .gpk Format Specification

GULA Pack (`.gpk`) is a ZIP archive containing:

```
pack_demo-1.0.0.gpk
├── pack.json                    # Manifest
├── __init__.py                  # Plugin entry point (for plugin type)
├── routes/                      # Optional: API routes
│   └── __init__.py
├── models/                      # Optional: SQLAlchemy models
│   └── __init__.py
├── services/                    # Optional: Business logic
│   └── __init__.py
├── migrations/                  # Optional: Alembic revisions
│   └── versions/
│       └── 0001_init.py
├── frontend/                    # Optional: UI components
│   └── widgets/
├── templates/                   # Optional: Jinja2 templates
├── i18n/                        # Optional: Translations
│   ├── ar.json
│   └── en.json
├── assets/                      # Optional: Static assets
│   └── icon.png
├── tests/                       # Recommended: Test suite
└── docs/                        # Recommended: Documentation
    ├── README.md
    └── API.md
```

---

## 7. Versioning Guide

All extensions MUST follow Semantic Versioning 2.0.0:

| Change | Version Bump | Example |
|--------|-------------|---------|
| Breaking API change | MAJOR | `1.2.3` → `2.0.0` |
| New feature (backward compatible) | MINOR | `1.2.3` → `1.3.0` |
| Bug fix | PATCH | `1.2.3` → `1.2.4` |
| Security fix | PATCH + advisory | `1.2.3` → `1.2.4` + CVE note |

**Pre-release tags:** `1.0.0-alpha.1`, `1.0.0-beta.2`, `1.0.0-rc.3`

**Dependency ranges:** Use `>=1.0.0,<2.0.0` for maximum compatibility

---

## 8. Complete Example

### Radiology Reporting Extension

**pack.json:**
```json
{
  "name": "pack_radiology_reporting",
  "version": "1.0.0",
  "description": {"ar": "تقارير الأشعة", "en": "Radiology reporting"},
  "dependencies": {"patient_management": ">=2.0.0", "storage_service": ">=1.0.0"},
  "permissions": ["read:patients", "write:results"]
}
```

**`__init__.py`:**
```python
from app.kernel.runtime_sdk import RuntimeSDK, PluginHook

class Plugin:
    name = "pack_radiology_reporting"
    version = "1.0.0"

    def initialize(self, sdk: RuntimeSDK):
        from .routes import router
        sdk.register_service("radiology_reporter", RadiologyReportService())
        sdk.plugins.register_hook(self.name, PluginHook(
            name="after_result_saved",
            handler=self.auto_generate_report,
            priority=10,
        ))

    def auto_generate_report(self, context):
        service = context.get("service")
        result = context.get("result")
        if result.get("test_type") == "radiology":
            service.generate_report(result["patient_id"], result["order_id"])
```

**`routes/__init__.py`:**
```python
from fastapi import APIRouter, Depends
from app.security.auth import get_current_user

router = APIRouter(prefix="/api/v1/radiology", tags=["radiology"])

@router.get("/reports/{patient_id}")
async def get_reports(patient_id: str, user = Depends(get_current_user)):
    # Must filter by lab_id
    return {"patient_id": patient_id, "reports": []}
```
