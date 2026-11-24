"""Backward-compatible adapters into the single authoritative event fabric.

Each historical stack keeps its own shape and call signature. Translation is
one-way into :class:`CanonicalEventEnvelope`; no adapter implements delivery
semantics of its own.
"""
from __future__ import annotations

import hashlib
import re
import uuid
from datetime import datetime
from typing import Any

from app._compat import UTC as GULA_UTC
from app.eventing.authority import CanonicalEventEnvelope, NationalEventAuthority
from app.models.outbox import OutboxEvent

_NAMESPACE = uuid.UUID("6f7d6a1e-8c2b-4a3f-9b4e-1d5e0a2c7f91")
_EVENT_TYPE_RE = re.compile(r"^[a-z][a-z0-9_.-]{2,119}$")


def _now() -> datetime:
    return datetime.now(GULA_UTC)


def _stable_id(prefix: str, material: str) -> str:
    digest = hashlib.sha256(material.encode("utf-8")).hexdigest()[:20]
    return f"{prefix}-{digest}"[:120]


def _normalize_event_type(raw: str) -> str:
    candidate = re.sub(r"[^a-z0-9_.-]+", ".", str(raw).strip().lower()).strip(".")
    candidate = re.sub(r"\.+", ".", candidate)
    if len(candidate) < 3:
        candidate = f"event.{candidate or 'unknown'}"
    if not _EVENT_TYPE_RE.fullmatch(candidate):
        candidate = f"event.{hashlib.sha256(candidate.encode()).hexdigest()[:24]}"
    return candidate[:120]


def _aware_timestamp(value: Any) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, (int, float)):
        parsed = datetime.fromtimestamp(float(value), tz=GULA_UTC)
    elif isinstance(value, str) and value:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    else:
        parsed = _now()
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        parsed = parsed.replace(tzinfo=GULA_UTC)
    return parsed


def _build(
    *,
    event_id: str,
    event_type: str,
    aggregate_type: str,
    aggregate_id: str,
    tenant_id: str,
    occurred_at: datetime,
    actor_id: str,
    correlation_id: str,
    payload: dict[str, Any],
    sequence: int | None = None,
    source_service: str = "gula-adapter",
    schema_version: int = 1,
) -> CanonicalEventEnvelope:
    return CanonicalEventEnvelope.model_validate(
        {
            "event_id": event_id[:120],
            "event_type": _normalize_event_type(event_type),
            "schema_version": schema_version,
            "source_service": source_service,
            "tenant_id": tenant_id,
            "occurred_at": occurred_at,
            "actor_id": actor_id,
            "entity_id": aggregate_id[:160],
            "correlation_id": correlation_id[:160],
            "idempotency_key": event_id[:200],
            "payload": payload,
            "aggregate_type": aggregate_type,
            "aggregate_id": aggregate_id,
            "sequence": sequence,
        }
    )


def from_legacy_call(
    event_type: str,
    payload: dict[str, Any],
    aggregate_type: str | None = None,
    aggregate_id: int | None = None,
) -> CanonicalEventEnvelope:
    """Adapt the historical ``emit_to_outbox`` signature without changing it."""
    material = f"legacy|{event_type}|{aggregate_type}|{aggregate_id}|{uuid.uuid4()}"
    event_id = f"legacy-{uuid.uuid5(_NAMESPACE, material)}"
    entity = str(aggregate_id) if aggregate_id is not None else event_id
    return _build(
        event_id=event_id,
        event_type=event_type,
        aggregate_type=aggregate_type or "unknown",
        aggregate_id=entity,
        tenant_id="system",
        occurred_at=_now(),
        actor_id="system",
        correlation_id=f"legacy-{event_id}",
        payload=dict(payload),
        source_service="legacy-outbox",
    )


def legacy_emit_to_outbox(
    db: Any,
    event_type: str,
    payload: dict[str, Any],
    aggregate_type: str | None = None,
    aggregate_id: int | None = None,
) -> OutboxEvent:
    """Compatibility entry point used by the historical outbox service."""
    return NationalEventAuthority.publish(
        db,
        from_legacy_call(event_type, payload, aggregate_type, aggregate_id),
    )


def legacy_run_once(db: Any, dispatcher: Any = None) -> dict[str, int]:
    """Compatibility drain: historically acknowledged zero-handler events."""
    return NationalEventAuthority.drain(
        db, require_handler=False, dispatcher=dispatcher
    )


def from_kernel_event(
    event: Any,
    *,
    tenant_id: str = "system",
    actor_id: str = "system",
) -> CanonicalEventEnvelope:
    """Adapt ``app.kernel.event_bus.events.Event`` to the canonical envelope."""
    raw_id = str(getattr(event, "id", "") or uuid.uuid4())
    event_id = _stable_id("kernel", raw_id)
    aggregate_id = str(
        getattr(event, "aggregate_id", None)
        or getattr(event, "name", "kernel")
    )
    correlation = getattr(event, "correlation_id", "") or f"kernel-{event_id}"
    return _build(
        event_id=event_id,
        event_type=str(getattr(event, "name", "kernel.event")),
        aggregate_type=str(getattr(event, "aggregate_type", "kernel")),
        aggregate_id=aggregate_id,
        tenant_id=str(getattr(event, "tenant_id", "") or tenant_id),
        occurred_at=_aware_timestamp(getattr(event, "timestamp", None)),
        actor_id=actor_id,
        correlation_id=correlation,
        payload=dict(getattr(event, "data", {}) or {}),
        sequence=getattr(event, "version", None),
        source_service="kernel-event-bus",
    )


def from_health_domain_event(
    event: Any,
    *,
    actor_id: str = "system",
) -> CanonicalEventEnvelope:
    """Adapt frozen synthetic Health Core ``DomainEvent`` records."""
    raw = event.to_dict() if hasattr(event, "to_dict") else dict(event.__dict__)
    source_schema = str(raw.get("schema_version", "1.0.0"))
    payload = dict(raw.get("payload", {}) or {})
    payload["source_schema_version"] = source_schema
    return _build(
        event_id=str(raw.get("event_id") or uuid.uuid4()),
        event_type=str(raw.get("event_type") or "health.event"),
        aggregate_type=str(raw.get("aggregate_type") or "health"),
        aggregate_id=str(raw.get("aggregate_id") or "unknown"),
        tenant_id=str(raw.get("tenant_id") or "system"),
        occurred_at=_aware_timestamp(raw.get("occurred_at")),
        actor_id=actor_id,
        correlation_id=str(raw.get("correlation_id") or f"health-{raw.get('event_id')}"),
        payload=payload,
        sequence=int(raw.get("version") or 1),
        source_service="health-core",
    )


def from_sync_engine_event(
    event: Any,
    *,
    tenant_id: str = "system",
    actor_id: str = "system",
) -> CanonicalEventEnvelope:
    """Adapt ``core.sync_engine.SyncEvent`` (LWW stack) to canonical form."""
    entity_type = str(getattr(event, "entity_type", "entity"))
    action = str(getattr(event, "action", "update"))
    entity_id = str(getattr(event, "entity_id", uuid.uuid4()))
    return _build(
        event_id=str(getattr(event, "event_id") or uuid.uuid4()),
        event_type=f"sync.{entity_type}.{action}",
        aggregate_type=entity_type,
        aggregate_id=entity_id,
        tenant_id=tenant_id,
        occurred_at=_aware_timestamp(getattr(event, "timestamp", None)),
        actor_id=actor_id,
        correlation_id=f"sync-{getattr(event, 'event_id', '')}",
        payload=dict(getattr(event, "data", {}) or {}),
        sequence=int(getattr(event, "version", 1) or 1),
        source_service="core-sync-engine",
    )


def from_offline_operation(
    operation: Any,
    *,
    tenant_id: str = "system",
    actor_id: str | None = None,
) -> CanonicalEventEnvelope:
    """Adapt ``services.offline_sync_service.SyncOperation`` to canonical form."""
    raw = operation.to_dict() if hasattr(operation, "to_dict") else dict(operation.__dict__)
    entity_type = str(raw.get("entity_type") or "entity")
    op_name = str(raw.get("operation") or "update")
    entity_id = str(raw.get("entity_id") or uuid.uuid4())
    resolved_actor = actor_id or str(raw.get("user_id") or "offline-device")
    vector = raw.get("vector_clock") or {}
    sequence = sum(int(v) for v in vector.values()) if isinstance(vector, dict) else None
    return _build(
        event_id=str(raw.get("operation_id") or uuid.uuid4()),
        event_type=f"offline.{entity_type}.{op_name}",
        aggregate_type=entity_type,
        aggregate_id=entity_id,
        tenant_id=tenant_id,
        occurred_at=_aware_timestamp(raw.get("timestamp")),
        actor_id=resolved_actor,
        correlation_id=str(raw.get("device_id") or f"offline-{raw.get('operation_id')}"),
        payload=raw,
        sequence=sequence,
        source_service="offline-sync-service",
    )
