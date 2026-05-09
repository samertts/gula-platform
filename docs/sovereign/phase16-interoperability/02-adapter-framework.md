# Phase 16-02 — Adapter Framework

The adapter framework is intentionally minimal. The whole point of bounded
interop is to keep the contract small enough to audit.

## The Contract

```python
class AdapterBase(abc.ABC):
    domain: TrustDomain                     # immutable manifest
    name: str                               # human label, e.g. "moh-fhir"

    @abc.abstractmethod
    async def health(self) -> AdapterHealth: ...

    @abc.abstractmethod
    async def call_outbound(
        self,
        operation: str,
        payload: Mapping[str, Any],
        context: AdapterContext,
    ) -> AdapterResult: ...

    @abc.abstractmethod
    async def handle_inbound(
        self,
        operation: str,
        payload: Mapping[str, Any],
        context: AdapterContext,
    ) -> AdapterResult: ...

    @abc.abstractmethod
    async def replay_outbox(self) -> int: ...
```

Every method is `async`. Every method runs through:

1. **Capability check** — `operation` must be present in
   `domain.allowed_operations`. Missing capability → fail closed, audit event
   `interop.capability_denied`.
2. **Tenant scoping** — `context.lab_id` is required for any operation whose
   data class includes patient data. National-aggregator domains skip this
   check but only run on de-identified flows.
3. **Audit emission** — every call (success, fail, deny) emits exactly one
   `InteropAuditEvent`.
4. **Failure isolation** — calls run inside the adapter's circuit breaker; a
   tripped breaker rejects immediately.

## Adapter Lifecycle

```
[register] -> [validate manifest] -> [load credentials]
   -> [open circuit / breaker]
   -> [serve outbound + inbound]
   -> [drain outbox on shutdown]
   -> [unregister]
```

Adapters are loaded from `INTEROP_ADAPTER_ALLOWLIST`. Loading is **explicit
import-by-name**, never eval/dynamic discovery, to keep the trust surface
auditable.

## Manifest Schema

```yaml
adapter:
  domain_id: 6f1a2c4d-...                     # opaque UUID
  name: moh-fhir
  institution_type: ministry
  tenancy_mode: single_tenant_proxy
  allowed_operations:
    - fhir.read.Patient
    - fhir.read.Observation
    - fhir.write.DiagnosticReport
  data_classes_in: [observation, diagnostic_report]
  data_classes_out: [patient_summary]
  audit_topic: interop.moh.fhir
  failure_policy:
    mode: fail_closed
    max_retries: 5
    backoff: exponential_jitter
    circuit:
      half_open_after_s: 60
      open_threshold_failures: 5
  endpoints:
    base_url: https://fhir.moh.gov.iq/v1
    auth: oauth2_client_credentials
  signing:
    require_jws: true
    require_jwe_for_classes: [observation]
```

The manifest is *the* source of truth. A code path that contradicts the
manifest is a defect. There is no "manifest override" environment variable.

## Inbound Mounting (Reserved)

When `ENABLE_INTEROP=true`, an `interop_router` (FastAPI APIRouter) is
mounted at `/interop/{adapter_name}/{operation}`. The router:

- Authenticates inbound peers via mTLS or signed JWT (per manifest)
- Calls `adapter.handle_inbound`
- Emits the same `InteropAuditEvent`
- Returns 503 if the adapter is in degraded state (fail-closed)

Until `ENABLE_INTEROP=true`, no such route exists in the OpenAPI surface.

## Adapter Implementation Notes

- Adapters live in `backend/app/interoperability/<adapter_name>/`.
- Each adapter folder has its own `manifest.yaml`, `client.py`,
  `mapper.py`, and `tests/`.
- Adapters MUST NOT import from `routes/` (static check). They are leaves of
  the dependency graph.
- Adapters MAY import from `services/`, `models/` (read-only), and the
  `interoperability/` core types.

## Manifest Validation

Manifest validation is performed at adapter registration:

- All `allowed_operations` are registered in the operation registry.
- `data_classes_in/out` only reference declared classes.
- No two adapters share the same `domain_id`.
- The audit topic exists in the audit-chain registry.
- Failure-policy mode is `fail_closed`. (No other mode is currently allowed.)

Validation failure aborts startup. There is no "run anyway" path.
