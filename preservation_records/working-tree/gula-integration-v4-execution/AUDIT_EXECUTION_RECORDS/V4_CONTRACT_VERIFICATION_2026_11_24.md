# V4 API and contract verification — 2026-11-24

## Scope

Runtime verification of the C01–C15 API/contract foundation in the isolated
execution workspace. No production endpoint was contacted. All checks used the
approved Python 3.12 environment and local application objects.

## Exact commands

```bash
cd /home/samertts/workspace/projects/gula-integration-v4-execution/backend
PYTHONPATH='/home/samertts/workspace/projects/gula-integration-v4-execution:/home/samertts/workspace/projects/gula-integration-v4-execution/backend' \
ENV=test RUNTIME_MODE=test \
/home/samertts/.cache/gula-int-py312/bin/python - <<'PY'
from app.main import app
from app.contracts.generator import ContractGenerator
# compare app.openapi() paths to contracts/export/openapi.json
PY

/home/samertts/.cache/gula-int-py312/bin/python -m pytest -q --timeout=120 \
  tests/test_contract_export_live.py \
  tests/test_capability_crud.py \
  tests/test_integration_contract_enforcement.py
```

Targeted result: `22 passed, 1 warning in 94.57s`, exit code `0`.
Log: `V4_CONTRACT_DRIFT_GUARD_2026_11_24.txt`.

## Runtime values

| Check | Result |
| --- | --- |
| `app.config.APP_VERSION` | `2.5.0` |
| Runtime WSGI/ASGI entrypoint (`app.main.app`) OpenAPI version | `2.5.0` |
| Checked-in export version | `2.5.0` |
| Runtime path count | `1850` |
| Checked-in export path count | `1850` |
| Exact `paths` equality (runtime vs checked-in) | `True` |
| Export component schema count | `643` |
| Export file size | `3,955,116` bytes |
| Generated spec from `ContractGenerator().generate_openapi(app.main.app)` equals checked-in export | `True` |
| Capability CRUD operations in export | `40` (8 capabilities × 5 operations) |
| `/metrics/prom` present in OpenAPI | `False` (intentionally hidden scrape route) |

`create_app(override_mode='test')` exposes `1843` paths because it intentionally
omits seven probe/test routes. The authoritative drift guard therefore compares
against `app.main.app`, the deployment entrypoint, and enforces exact path
equality rather than a minimum count.

## Schema endpoints

`tests/test_contract_export_live.py` verifies through an authenticated client
that:

* `GET /contracts/openapi.json` returns `200` and reports `APP_VERSION`;
* the five representative registered capability prefixes are present;
* `GET /contracts/schemas/patient` returns a non-empty object schema;
* `GET /contracts/catalog` reports `APP_VERSION`;
* `GET /metrics/prom` returns `401` without the bearer token and `200` with it,
  and delegates to the single authoritative renderer.

## Correlation propagation (C12/C14)

`tests/test_integration_contract_enforcement.py` verifies:

* inbound `X-Correlation-ID` is propagated to response headers and request state;
* invalid or control-character values are replaced with a log-safe, bounded ID;
* missing values fall back to `X-Request-ID`, then `traceparent`, then a fresh UUID;
* correlation helpers never copy PHI/free text into headers or logs;
* `IntegrationEventEnvelope.correlation_id` is a required versioned event field.

## STUB/simulation scan

A lexical scan of all 1,850 exported operations found one marker hit:

* `GET /integration/standards` — the marker appears only in a negated docstring:
  "No placeholder or invented conformance data is emitted". The handler derives
  every returned field from real public accessors on the standards services.

No operation was found that silently returns a STUB/simulation response. This
scan is lexical, not a semantic proof of every downstream adapter; unresolved
adapter-level simulation remains recorded as a residual defect where known.

## CI enforcement

`.github/workflows/ci.yml` contains a V4 guard step that runs the contract,
capability CRUD, PostgreSQL P-03, correlation, envelope, and metrics tests. The
PostgreSQL tests skip cleanly when their disposable DSN variables are absent;
with the DSNs set locally the same guard produced `75 passed, 1 warning`.

The automated no-silent-STUB guard was subsequently added to
`backend/tests/test_contract_export_live.py` as
`test_exported_operations_do_not_silently_advertise_stub_responses`. It checks
all 1,850 exported operations for an actual STUB/simulation response marker and
passed with `17 passed, 1 warning in 97.60s`, exit `0`
(`V4_NO_STUB_DRIFT_GUARD_2026_11_24.txt`, SHA-256
`ec0dfd72829f09b81ec5c9fd8a55d44ed7f7cd1a1c756524379dd2610039510d`).

The CI guard was also extended with the event-authority consolidation suites
(`tests/test_event_authority_consolidation.py` and
`tests/test_event_authority_postgres.py`). The PostgreSQL suite skips cleanly
when `GULA_V4_EVENTS_PG_DSN` is absent; with the disposable PG16 DSN set it
produced `4 passed, 1 warning`, exit `0`.
