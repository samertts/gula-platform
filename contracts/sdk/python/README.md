# GULA SDK — Python

Official Python SDK for the [GULA Platform](https://gula.health) — laboratory information management,
patient records, healthcare analytics, and clinical AI for Iraqi medical laboratories.

## Installation

```bash
pip install gula-sdk
```

With CLI tools:

```bash
pip install gula-sdk[cli]
```

Requires Python 3.10+.

## Quick Start

```python
import asyncio
from gula import GulaClient

async def main():
    async with GulaClient(base_url="https://your-lab.gula.health") as client:
        resp = await client.login("admin@lab.com", "your-password")
        client.set_token(resp["access_token"])

        patients = await client.list_patients(limit=10)
        print(patients)

asyncio.run(main())
```

## Authentication

```python
# Staff login
resp = await client.login("email@example.com", "password")
client.set_token(resp["access_token"])

# Citizen portal login
resp = await client.citizen_login("07701234567", "password")
client.set_token(resp["access_token"])

# Token refresh
resp = await client.refresh_token(refresh_token)
client.set_token(resp["access_token"])
```

Tokens are sent as `Authorization: Bearer <token>` on every request.

## Making API Calls

All methods are async and return parsed JSON dicts or typed Pydantic models.

### Pagination

List endpoints return paginated results with `page`, `limit`, `total`, and `items`:

```python
results = await client.list_patients(page=2, limit=50, gender="M")
```

### Idempotency Key

Pass an `idempotency_key` to prevent duplicate mutations:

```python
from gula.models import CreateOrderRequest, ResultItem

order = CreateOrderRequest(
    patient_id=1,
    results=[ResultItem(test_name="CBC", value=5.5, unit="10^3/µL")],
)
resp = await client.create_order(order, idempotency_key="unique-key-123")
```

### Retry Logic

The client retries on 429 (rate limit), 500, 502, 503, 504 with exponential backoff
(2s, 4s, 8s). Configure via `max_retries`:

```python
client = GulaClient(base_url="...", max_retries=5)
```

## Error Handling

```python
from gula.exceptions import (
    AuthenticationError,
    NotFoundError,
    ValidationError,
    RateLimitError,
    GulaError,
)

try:
    patient = await client.get_patient(99999)
except NotFoundError:
    print("Patient not found")
except AuthenticationError:
    print("Bad credentials — re-login required")
except ValidationError as e:
    print("Validation failed:", e.body)
except RateLimitError:
    print("Slow down!")
except GulaError as e:
    print(f"HTTP {e.status_code}: {e}")
```

| Exception | HTTP Status |
|-----------|-------------|
| `AuthenticationError` | 401 |
| `PermissionError` | 403 |
| `NotFoundError` | 404 |
| `ConflictError` | 409 |
| `ValidationError` | 422 |
| `RateLimitError` | 429 |
| `ServerError` | 500+ |
| `IdempotencyError` | 409 (idempotency) |

## Offline Sync

Queue mutations when offline and replay them when connected:

```python
from gula.sync import SyncQueue, SyncEngine, ConflictResolver

# Configure
client = GulaClient(base_url="https://api.gula.health")
resolver = ConflictResolver(strategy=ConflictResolver.STRATEGY_CLIENT_WINS)
engine = SyncEngine(client, conflict_resolver=resolver)

# Queue mutations when offline
engine.enqueue("POST", "/patients", {
    "full_name": "Ali Ahmed",
    "phone": "07701234567",
})

# Process queue
async def sync_once():
    count = await engine.process_once()
    print(f"Synced {count} mutations")

# Run continuous sync
async def sync_loop():
    await engine.run_forever()

# Later...
await engine.stop()
```

The `SyncQueue` persists to a local JSON file. The `ConflictResolver` supports
three strategies:

- `CLIENT_WINS` — local changes overwrite server (default)
- `SERVER_WINS` — server state is authoritative
- `MERGE` — custom merge function

## FHIR Support

```python
# Search patients via FHIR
bundle = await client.fhir_search("Patient", name="Ahmed", birthdate="1990-01-01")

# Read a FHIR resource
patient = await client.fhir_read("Patient", "123")

# Create a FHIR resource
new_patient = await client.fhir_create("Patient", {
    "resourceType": "Patient",
    "name": [{"family": "Ahmed", "given": ["Ali"]}],
})

# Get FHIR capability statement
caps = await client.fhir_capabilities()
```

## Domain Examples

### Patients

```python
from gula.models import PatientCreate, PatientUpdate

patient = PatientCreate(
    full_name="Ali Ahmed",
    phone="07701234567",
    birth_date="1990-05-15",
    gender="M",
)
created = await client.create_patient(patient)

updated = await client.update_patient(created["id"], PatientUpdate(phone="07707654321"))
```

### Labs

```python
from gula.models import LabUpdate

lab = await client.get_lab(1)
await client.update_lab(1, LabUpdate(name="Al-Noor Lab", city="Baghdad"))
```

### Orders & Results

```python
from gula.models import CreateOrderRequest, ResultItem

order = CreateOrderRequest(
    patient_id=1,
    doctor_name="Dr. Hassan",
    results=[
        ResultItem(test_name="Glucose", value=95.0, unit="mg/dL"),
        ResultItem(test_name="HbA1c", value=5.4, unit="%"),
    ],
)
created = await client.create_order(order, idempotency_key="order-001")

# Verify, approve, validate
await client.verify_result(created["id"])
await client.approve_result(created["id"])
```

### Samples

```python
from gula.models import SampleCreate, SampleUpdate

sample = SampleCreate(order_id=1, sample_type="blood")
created = await client.create_sample(sample)

await client.receive_sample(created["id"])
await client.reject_sample(created["id"], reason="Hemolyzed")
```

### Claims

```python
from gula.models import ClaimCreate, ClaimItemCreate

claim = ClaimCreate(
    patient_id=1,
    items=[
        ClaimItemCreate(test_code="CBC", unit_price=5000.0, amount=5000.0),
    ],
)
resp = await client.create_claim(claim)
await client.validate_claim(resp.id)
await client.submit_claim(resp.id)
```

### Edge Devices

```python
from gula.models import RegisterDeviceRequest

device = RegisterDeviceRequest(
    public_key_pem="-----BEGIN PUBLIC KEY-----\n...",
    display_name="Lab PC #1",
    agent_version="1.0.0",
)
registered = await client.edge_register_device(device)
```

### MPI

```python
from gula.models import ResolveRequest

result = await client.mpi_resolve(
    ResolveRequest(lab_id=1, patient_id=100, name="Ali Ahmed", phone="07701234567")
)
print(f"Matched to citizen: {result.citizen_ulid} (method: {result.match_method})")
```

### AI

```python
chat = await client.ai_chat("What does high glucose mean?")
print(chat["response"])

from gula.models import SuggestRequest
suggestion = await client.ai_suggest(
    SuggestRequest(
        operation="suggest_interpretation",
        entity_type="lab_result",
        entity_id=42,
        payload={"result_value": 110, "test_name": "Glucose"},
    )
)
```

### Quality Control

```python
from gula.models import QCSubmit

result = await client.qc_submit(
    QCSubmit(
        test_code="Glucose",
        level="normal",
        expected_value=100.0,
        measured_value=102.0,
        sd=2.0,
    )
)
```

### LIMS

```python
from gula.models import InstrumentCreateRequest, IQCRunRequest

instrument = await client.lims_register_instrument(
    InstrumentCreateRequest(model_id=1, instrument_code="SYS-001")
)

qc = await client.lims_qc_run(
    IQCRunRequest(
        program_id=1, test_code="Glucose",
        measured_value=102.0, expected_value=100.0, sd=2.0,
    )
)
```

### Governance

```python
from gula.models import NodeCreate, WorkerCreate

node = await client.governance_create_node(
    NodeCreate(node_type="governorate", code="BGH", name_ar="بغداد")
)

worker = await client.governance_create_worker(
    WorkerCreate(employee_code="DOC-001", full_name_ar="د. علي أحمد", profession="doctor")
)
```

### Consent

```python
from gula.models import GrantRequest

grant = GrantRequest(
    gpid="01HABCDEFGHIJKLMNOPQRSTUVWX",
    grantee_id="user:42",
    scope="lab_results:read",
    expires_in_hours=24,
)
resp = await client.grant_consent(grant)

check = await client.check_consent(gpid=grant.gpid, grantee_id=grant.grantee_id, scope=grant.scope)
if check.allowed:
    print("Consent active until", check.expires_at)
```

## Advanced Usage

### Custom Timeout

```python
client = GulaClient(base_url="...", timeout=60.0)
```

### Low-Level Request

```python
resp = await client._request("GET", "/custom/endpoint", query={"key": "value"})
```

## License

MIT
