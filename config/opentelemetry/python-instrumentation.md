# GULA Platform - Python OpenTelemetry Instrumentation Guide

## Installation

```bash
pip install opentelemetry-distro opentelemetry-exporter-otlp
opentelemetry-bootstrap -a install
```

## Environment Variables

```bash
# OTLP exporter targets the OpenTelemetry Collector
OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
OTEL_EXPORTER_OTLP_PROTOCOL=grpc
OTEL_SERVICE_NAME=gula-backend
OTEL_RESOURCE_ATTRIBUTES=environment=production,region=me-central-1

# Sampling
OTEL_TRACES_SAMPLER=traceidratio
OTEL_TRACES_SAMPLER_ARG=0.1

# Metrics export interval
OTEL_METRIC_EXPORT_INTERVAL=30000
OTEL_METRIC_EXPORT_TIMEOUT=10000
```

## FastAPI Middleware Integration

Add to `backend/app/main.py` lifespan startup:

```python
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

# After app creation
FastAPIInstrumentor.instrument_app(app, excluded_urls="/health,/health/.*,/metrics")
```

## Automatic Instrumentation

These are auto-instrumented via `opentelemetry-bootstrap -a install`:

| Library     | Package                                      |
|-------------|----------------------------------------------|
| SQLAlchemy  | opentelemetry-instrumentation-sqlalchemy     |
| httpx       | opentelemetry-instrumentation-httpx           |
| Redis       | opentelemetry-instrumentation-redis           |
| Uvicorn     | opentelemetry-instrumentation-uvicorn         |
| Requests    | opentelemetry-instrumentation-requests        |
| Logging     | opentelemetry-instrumentation-logging         |

## Manual Instrumentation for Business Logic

### Order Processing

```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

def process_order(order_id: str, lab_id: str):
    with tracer.start_as_current_span("order.process") as span:
        span.set_attribute("order.id", order_id)
        span.set_attribute("lab.id", lab_id)
        span.set_attribute("order.type", "lab_test")

        # Validate order
        with tracer.start_as_current_span("order.validate") as validate_span:
            validate_span.set_attribute("validation.rules", 5)
            result = validate_order(order_id)
            validate_span.set_attribute("validation.passed", result)

        # Save to database
        with tracer.start_as_current_span("order.persist") as persist_span:
            persist_span.set_attribute("db.table", "lab_orders")
            save_order(order_id)

        return result
```

### Result Validation

```python
def validate_result(result_id: str, technician_id: str):
    with tracer.start_as_current_span("result.validate") as span:
        span.set_attribute("result.id", result_id)
        span.set_attribute("technician.id", technician_id)

        # Check critical values
        with tracer.start_as_current_span("result.check_critical") as check_span:
            critical = check_critical_values(result_id)
            check_span.set_attribute("critical.found", critical)
            if critical:
                check_span.add_event("critical_value_detected", {
                    "result.id": result_id,
                    "severity": "high"
                })

        # Validate against reference ranges
        with tracer.start_as_current_span("result.reference_check") as ref_span:
            ref_span.set_attribute("ref.ranges.checked", True)
            check_reference_ranges(result_id)
```

## Propagating Trace Context via HTTP Headers

The OpenTelemetry propagator automatically injects context into outgoing HTTP requests:

```python
# Propagated headers (auto-injected):
# traceparent: 00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01
# tracestate: rojo=00f067aa0ba902b7,congo=t61rcWkgMzE

from opentelemetry import propagate
from opentelemetry.propagators.cloud_trace_propagator import CloudTraceFormatPropagator

# Configure propagator
propagate.set_global_textmap(CloudTraceFormatPropagator())
```

## Span Attributes for Tenant Isolation

Always attach tenant context to every span:

```python
from contextvars import ContextVar

current_lab_id: ContextVar[str] = ContextVar("lab_id")
current_user_id: ContextVar[str] = ContextVar("user_id")

def instrumented_endpoint(request):
    span = trace.get_current_span()
    span.set_attribute("gula.lab_id", current_lab_id.get())
    span.set_attribute("gula.user_id", current_user_id.get())
    span.set_attribute("gula.tenant", current_lab_id.get())
```

## Running with Instrumentation

```bash
# Direct
opentelemetry-instrument \
    --exporter_otlp_endpoint http://otel-collector:4317 \
    --service_name gula-backend \
    uvicorn app.main:app --host 0.0.0.0 --port 8000

# Docker (add to Dockerfile CMD or entrypoint)
ENTRYPOINT ["opentelemetry-instrument", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Verifying Instrumentation

Check traces are flowing:

```bash
# Via OTel Collector health
curl http://localhost:13133/health

# Via Tempo search
curl http://localhost:3200/api/search?q=gula-backend

# Via Prometheus metrics
curl http://localhost:8889/metrics | grep otel_spans
```
