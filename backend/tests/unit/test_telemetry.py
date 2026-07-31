"""Tests for the OpenTelemetry export module (PROGRAM-011 WARN burn-down).

Covers the no-op-by-default contract, OTLP pipeline initialization,
idempotency, and graceful instrumentation attachment.
"""

from unittest.mock import patch

import app.telemetry as telemetry


def _reset_module():
    telemetry._OTLP_ENDPOINT = ""
    telemetry._tracer_provider = None
    telemetry._tracer = None


def test_disabled_by_default():
    _reset_module()
    assert telemetry.is_enabled() is False
    telemetry.init_tracing()
    assert telemetry.is_enabled() is False


def test_init_tracing_enables_with_endpoint():
    _reset_module()
    telemetry._OTLP_ENDPOINT = "http://jaeger:4318"
    telemetry.init_tracing()
    assert telemetry.is_enabled() is True


def test_init_tracing_is_idempotent():
    _reset_module()
    telemetry._OTLP_ENDPOINT = "http://jaeger:4318"
    telemetry.init_tracing()
    provider = telemetry._tracer_provider
    telemetry.init_tracing()  # second call must not replace the provider
    assert telemetry._tracer_provider is provider


def test_init_tracing_failure_is_graceful():
    _reset_module()
    telemetry._OTLP_ENDPOINT = "http://jaeger:4318"
    with patch(
        "opentelemetry.sdk.trace.TracerProvider", side_effect=RuntimeError("boom"),
    ):
        telemetry.init_tracing()
    assert telemetry.is_enabled() is False


def test_instrument_app_is_noop_when_disabled():
    _reset_module()
    with patch("opentelemetry.instrumentation.fastapi.FastAPIInstrumentor") as mock:
        telemetry.instrument_app(object())
    mock.instrument_app.assert_not_called()


def test_instrument_app_attaches_instrumentation():
    _reset_module()
    telemetry._OTLP_ENDPOINT = "http://jaeger:4318"
    telemetry.init_tracing()
    fake_app = object()
    with patch("opentelemetry.instrumentation.fastapi.FastAPIInstrumentor") as mock_fastapi, \
            patch("opentelemetry.instrumentation.sqlalchemy.SQLAlchemyInstrumentor") as mock_sa:
        telemetry.instrument_app(fake_app)
    mock_fastapi.instrument_app.assert_called_once()
    mock_sa.return_value.instrument.assert_called_once()


def test_instrument_app_tolerates_sa_failure():
    _reset_module()
    telemetry._OTLP_ENDPOINT = "http://jaeger:4318"
    telemetry.init_tracing()
    with patch("opentelemetry.instrumentation.fastapi.FastAPIInstrumentor"), \
            patch(
                "opentelemetry.instrumentation.sqlalchemy.SQLAlchemyInstrumentor",
                side_effect=Exception("no engine yet"),
            ):
        telemetry.instrument_app(object())  # must not raise
