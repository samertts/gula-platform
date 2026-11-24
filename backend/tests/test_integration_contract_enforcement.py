"""Executable checks for the Wave A integration-contract fixes.

Covers:
- C12/C14: ``X-Correlation-ID`` propagation and fail-safe sanitization.
- C14: a single authoritative Prometheus renderer behind ``/metrics/prom``.
"""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
from fastapi.testclient import TestClient

from app.contracts.integration import (
    CORRELATION_ID_HEADER,
    correlation_id_from_headers,
    normalize_correlation_id,
)
from app.middleware import RequestIDMiddleware

_LOG_SAFE_ID = "corr-v4-0001"


def _middleware_client():
    app = FastAPI()
    app.add_middleware(RequestIDMiddleware)

    @app.get("/probe")
    def probe(request: Request):
        return {
            "request_id": request.state.request_id,
            "correlation_id": request.state.correlation_id,
        }

    return TestClient(app, raise_server_exceptions=True)


def test_correlation_id_is_propagated_to_state_and_response():
    client = _middleware_client()
    response = client.get("/probe", headers={CORRELATION_ID_HEADER: _LOG_SAFE_ID})
    assert response.status_code == 200
    assert response.headers[CORRELATION_ID_HEADER] == _LOG_SAFE_ID
    assert response.json()["correlation_id"] == _LOG_SAFE_ID
    assert response.json()["request_id"]


def test_invalid_correlation_id_is_replaced_with_log_safe_value():
    client = _middleware_client()
    response = client.get("/probe", headers={CORRELATION_ID_HEADER: "bad value\nwith-control"})
    assert response.status_code == 200
    emitted = response.headers[CORRELATION_ID_HEADER]
    assert emitted != "bad value\nwith-control"
    assert normalize_correlation_id(emitted) == emitted
    assert response.json()["correlation_id"] == emitted


def test_missing_correlation_id_falls_back_to_request_id():
    client = _middleware_client()
    response = client.get("/probe", headers={"X-Request-ID": "req-v4-0001"})
    assert response.status_code == 200
    assert response.headers[CORRELATION_ID_HEADER] == "req-v4-0001"
    assert response.json()["correlation_id"] == "req-v4-0001"


def test_traceparent_is_mapped_when_correlation_header_is_absent():
    traceparent = "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"
    headers = {"traceparent": traceparent}
    assert correlation_id_from_headers(headers) == traceparent


def test_correlation_helper_never_emits_unsafe_text():
    assert normalize_correlation_id(None) != ""
    assert normalize_correlation_id(" PHI; DROP TABLE ") != " PHI; DROP TABLE "
    assert normalize_correlation_id("", fallback="invalid fallback") != "invalid fallback"


def test_metrics_prom_route_delegates_to_single_renderer(client, monkeypatch):
    from app.routes import metrics as metrics_routes

    def fake_renderer(request, db):
        return PlainTextResponse("# rendered by authoritative service\n")

    monkeypatch.setattr(metrics_routes, "build_prometheus_response", fake_renderer)
    response = client.get("/metrics/prom")
    assert response.status_code == 200
    assert response.text == "# rendered by authoritative service\n"
