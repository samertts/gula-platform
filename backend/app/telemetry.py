"""OpenTelemetry tracing export — GULA Platform
==============================================
Zero lock-in tracing: exports OTLP/HTTP spans to any OTLP-compatible
collector (self-hosted Jaeger, Tempo, OpenTelemetry Collector, ...).

Enabled only when `OTEL_EXPORTER_OTLP_ENDPOINT` is set (e.g.
``http://jaeger:4318`` in the full compose stack). When unset the module
is a no-op — zero runtime cost, zero changes for existing deployments.

The FastAPI + SQLAlchemy instrumentations attach to the provider at
startup (see app/factory.py) and honor the standard ``OTEL_*`` env vars.
"""

from __future__ import annotations

import logging
import os

logger = logging.getLogger("gula.telemetry")

_OTLP_ENDPOINT = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "").strip().rstrip("/")
_SERVICE_NAME = os.getenv("OTEL_SERVICE_NAME", "gula-backend")

_tracer_provider = None
_tracer = None


def init_tracing() -> None:
    """Initialize the OTLP trace pipeline (no-op unless endpoint is set)."""
    global _tracer_provider, _tracer

    if not _OTLP_ENDPOINT:
        logger.info("[OTEL] OTEL_EXPORTER_OTLP_ENDPOINT not set — tracing disabled")
        return

    if _tracer_provider is not None:
        return  # already initialized

    try:
        from opentelemetry import trace as _otel_trace
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        resource = Resource.create(
            {"service.name": _SERVICE_NAME, "service.version": os.getenv("APP_VERSION", "dev")},
        )
        exporter = OTLPSpanExporter(endpoint=f"{_OTLP_ENDPOINT}/v1/traces", timeout=5)
        processor = BatchSpanProcessor(
            exporter,
            max_queue_size=8_192,
            max_export_batch_size=512,
            schedule_delay_millis=5_000,
            export_timeout_millis=5_000,
        )

        _tracer_provider = TracerProvider(resource=resource)
        _tracer_provider.add_span_processor(processor)
        _otel_trace.set_tracer_provider(_tracer_provider)
        _tracer = _otel_trace.get_tracer(_SERVICE_NAME)

        logger.info(
            "[OTEL] tracing enabled → OTLP %s/v1/traces (service=%s)",
            _OTLP_ENDPOINT,
            _SERVICE_NAME,
        )
    except Exception as exc:  # pragma: no cover — defensive only
        logger.error("[OTEL] failed to initialize tracing: %s", exc)


def instrument_app(app) -> None:
    """Attach FastAPI/SQLAlchemy instrumentations when tracing is enabled."""
    if _tracer_provider is None:
        return
    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

        FastAPIInstrumentor.instrument_app(app, tracer_provider=_tracer_provider)
        try:
            from app.database import engine

            SQLAlchemyInstrumentor().instrument(engine=engine, tracer_provider=_tracer_provider)
        except Exception:
            pass  # engine not yet initialized — instrument at first call instead
        logger.info("[OTEL] FastAPI + SQLAlchemy instrumented")
    except Exception as exc:  # pragma: no cover — defensive only
        logger.error("[OTEL] instrumentation failed: %s", exc)


def is_enabled() -> bool:
    return _tracer_provider is not None
