from __future__ import annotations

import os

os.environ.setdefault("ENV", "test")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production-" + "x" * 32)
os.environ.setdefault("ENCRYPTION_KEY", "6TJUTgJxBREYK9_yDy6VMXBw1HPwwxv1kiynV0WaAdw=")
os.environ.setdefault("NID_HMAC_KEY", "a" * 64)
os.environ.setdefault("REDIS_URL", "")

import threading

from app.services import metrics_service


def setup_function() -> None:
    metrics_service._requests_total.clear()
    metrics_service._request_errors_total.clear()
    metrics_service._latency_buckets.clear()
    metrics_service._latency_sum.clear()
    metrics_service._latency_count.clear()


def test_empty_exposition() -> None:
    assert metrics_service.request_metrics_exposition() == ""


def test_record_and_counters() -> None:
    metrics_service.record_request("GET", "/orders", 200, 0.05)
    metrics_service.record_request("GET", "/orders", 200, 0.05)
    metrics_service.record_request("GET", "/orders", 500, 0.2)
    metrics_service.record_request("POST", "/orders", 201, 0.3)
    exp = metrics_service.request_metrics_exposition()
    assert 'gula_requests_total{method="GET",route="/orders",status="2xx"} 2' in exp
    assert 'gula_requests_total{method="GET",route="/orders",status="5xx"} 1' in exp
    assert 'gula_requests_total{method="POST",route="/orders",status="2xx"} 1' in exp
    assert 'gula_request_errors_total{method="GET",route="/orders"} 1' in exp


def test_histogram_buckets() -> None:
    metrics_service.record_request("GET", "/health/deep", 200, 0.004)
    metrics_service.record_request("GET", "/health/deep", 200, 0.06)
    metrics_service.record_request("GET", "/health/deep", 200, 12.0)
    exp = metrics_service.request_metrics_exposition()
    assert 'gula_request_duration_seconds_bucket{le="0.005",method="GET",route="/health/deep"} 1' in exp
    assert 'gula_request_duration_seconds_bucket{le="0.1",method="GET",route="/health/deep"} 2' in exp
    assert 'gula_request_duration_seconds_bucket{le="+Inf",method="GET",route="/health/deep"} 3' in exp
    assert 'gula_request_duration_seconds_sum{method="GET",route="/health/deep"} 12.064' in exp
    assert 'gula_request_duration_seconds_count{method="GET",route="/health/deep"} 3' in exp


def test_label_escaping() -> None:
    metrics_service.record_request("GET", '/weird"route\\x', 200, 0.01)
    exp = metrics_service.request_metrics_exposition()
    assert 'route="/weird\\"route\\\\x"' in exp


def test_concurrent_recording_is_safe() -> None:
    errors: list[Exception] = []

    def worker() -> None:
        try:
            for _ in range(200):
                metrics_service.record_request("GET", "/x", 200, 0.01)
        except Exception as exc:  # pragma: no cover - assertion only
            errors.append(exc)

    threads = [threading.Thread(target=worker) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert not errors
    assert metrics_service._latency_count[("GET", "/x")] == 800
