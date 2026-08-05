"""Phase 7 — Observability.

Integrate Prometheus, Grafana, Alertmanager, logs, metrics, tracing,
dashboards, and incident alerts. Deterministic configuration state; the
engine declares what is enabled and where each pipeline endpoint lives.
"""

from __future__ import annotations

from scripts.deployer.core import (
    OBSERVABILITY_SERVICES,
    ObservabilityConfig,
)

# Default observability integration map.
OBSERVABILITY_PLAN: dict[str, dict] = {
    "prometheus": {"enabled": True, "endpoint": "http://prometheus:9090", "retention_days": 15},
    "grafana": {"enabled": True, "endpoint": "http://grafana:3000", "retention_days": 30},
    "alertmanager": {"enabled": True, "endpoint": "http://alertmanager:9093", "retention_days": 30},
    "loki": {"enabled": True, "endpoint": "http://loki:3100", "retention_days": 14},
    "tempo": {"enabled": True, "endpoint": "http://tempo:3200", "retention_days": 14},
    "jaeger": {"enabled": True, "endpoint": "http://jaeger:16686", "retention_days": 7},
}

# Dashboards the platform ships.
DASHBOARDS: tuple[str, ...] = (
    "platform-overview",
    "api-latency",
    "database-health",
    "queue-depth",
    "infra-resources",
    "incident-status",
)


def observability_config(services: tuple[str, ...] = OBSERVABILITY_SERVICES) -> list[ObservabilityConfig]:
    """Produce the observability integration state for the platform."""
    configs: list[ObservabilityConfig] = []
    for service in services:
        plan = OBSERVABILITY_PLAN.get(service, {})
        configs.append(ObservabilityConfig(
            component=service,
            enabled=bool(plan.get("enabled")),
            endpoint=plan.get("endpoint", ""),
            retention_days=plan.get("retention_days", 30),
        ))
    return configs


def tracing_chain() -> dict:
    """Declare the tracing pipeline: app -> OpenTelemetry -> Tempo/Jaeger."""
    return {
        "collector": "otel-collector:4317",
        "backends": ["tempo", "jaeger"],
        "propagation": ["traceparent"],
        "sampling": {"strategy": "probabilistic", "rate": 0.1},
    }


def alert_rules() -> list[dict]:
    """Deterministic alert rules the platform monitors for incidents."""
    return [
        {"name": "HighApiLatencyP95", "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 1.0", "severity": "warning"},
        {"name": "DatabaseDown", "expr": "up{job='postgres'} == 0", "severity": "critical"},
        {"name": "QueueBacklog", "expr": "rabbitmq_queue_messages_ready > 500", "severity": "warning"},
        {"name": "DiskSpaceLow", "expr": "node_filesystem_avail_bytes / node_filesystem_size_bytes < 0.1", "severity": "critical"},
    ]


def dashboard_links(configs: list[ObservabilityConfig]) -> list[str]:
    """Return the Grafana dashboard endpoints for enabled integrations."""
    grafana = next((c for c in configs if c.component == "grafana"), None)
    if not grafana or not grafana.enabled:
        return []
    return [f"{grafana.endpoint}/d/{name}" for name in DASHBOARDS]
