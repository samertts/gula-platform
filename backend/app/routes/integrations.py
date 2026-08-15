"""Integrations health + probe API.

Endpoints:

  GET  /integrations/status            — snapshot of every adapter's mode, circuit
                                         state, and trust level. Admin-only.
  POST /integrations/{name}/probe      — force a live probe against ``name``
                                         (currently: national_identity, insurance,
                                         residency, cloudflare). Admin-only.

Design:
  - Never exposes raw API keys or identifiers, only mode + health flags.
  - STUB mode is the safe default — the probe runs against the stub unless
    the operator has set GULA_ADAPTER_MODE_* + the adapter's credentials.
  - The registry is declarative: adding a new gateway means adding one
    line to ``_REGISTRY``.
"""

from __future__ import annotations

import logging
import os
from collections.abc import Callable
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field

from ..contracts.integration import IntegrationEventEnvelope
from ..database import get_db
from ..gateways.base import CircuitState, ExternalGateway
from ..gateways.cloudflare_gateway import (
    get_cloudflare_gateway,
    probe_cloudflare,
)
from ..gateways.insurance_gateway import (
    check_insurance,
    get_insurance_gateway,
)
from ..gateways.national_identity_gateway import (
    get_national_identity_gateway,
    verify_national_id,
)
from ..gateways.residency_gateway import (
    get_residency_gateway,
    verify_residency,
)
from ..integration.identity_bundle import verify_identity_bundle
from ..integration.inbox import reject_event, stage_event
from ..models.integration_inbox import IntegrationInboxEvent
from ..models.lab_user import LabUser
from ..models.service_account import ServiceAccount
from ..security.dependencies import require_service_account
from ..security.rbac import require_role
from ..security.service_accounts import has_service_account_scope
from ..services.audit_service import log_action

logger = logging.getLogger("gula.integrations.router")

router = APIRouter(prefix="/integrations", tags=["integrations"])


_PROBE_KWARGS: dict[str, dict[str, Any]] = {
    "national_identity": {"national_id": "000000000000"},
    "insurance": {"insurance_id": "probe-placeholder"},
    "residency": {"passport_no": "PROBE123"},
    "cloudflare": {},
}

_GETTERS: dict[str, Callable[[], ExternalGateway]] = {
    "national_identity": get_national_identity_gateway,
    "insurance": get_insurance_gateway,
    "residency": get_residency_gateway,
    "cloudflare": get_cloudflare_gateway,
}

_PROBES: dict[str, Callable[[], Any]] = {
    "national_identity": lambda: verify_national_id("000000000000"),
    "insurance": lambda: check_insurance("probe-placeholder"),
    "residency": lambda: verify_residency("PROBE123"),
    "cloudflare": probe_cloudflare,
}


def _snapshot(name: str, gw: ExternalGateway) -> dict:
    """Serialize one gateway's health signal without exposing secrets."""
    # `mode` is set in __init__ on mode-aware gateways; fall back to "n/a".
    mode = getattr(gw, "mode", None)
    mode_value = mode.value if mode is not None else "n/a"

    circuit = gw._circuit  # introspection only; no mutation
    return {
        "name": name,
        "trust_level": gw.trust_level.value,
        "mode": mode_value,
        "circuit": circuit.state.value,
        "healthy": circuit.state is not CircuitState.OPEN,
        "cache_size": len(gw._cache),
        "cache_ttl": gw.cache_ttl,
        "timeout": gw.timeout,
    }


def _authorize_event_ingress(principal: Any) -> Any:
    """Only scoped service accounts or platform administrators may publish."""
    if isinstance(principal, ServiceAccount):
        if not has_service_account_scope(principal, "integration:events:write"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Service account lacks integration:events:write scope",
            )
        return principal
    if getattr(principal, "role", None) not in {"master_admin", "ministry_admin"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Integration event ingress requires an authorized service principal",
        )
    return principal


# ── POST /integrations/events ────────────────────────────────────────────────


@router.post("/events", status_code=status.HTTP_202_ACCEPTED, summary="Stage an external event")
def receive_integration_event(
    envelope: IntegrationEventEnvelope,
    principal=Depends(require_service_account),
    db=Depends(get_db),
) -> dict:
    """Validate and durably stage an event; clinical approval remains in GULA."""
    _authorize_event_ingress(principal)
    try:
        result = stage_event(db, envelope)
        db.commit()
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except Exception as exc:
        db.rollback()
        logger.exception("Integration event staging failed event_id=%s", envelope.event_id)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Event staging unavailable",
        ) from exc

    return {
        "event_id": result.event_id,
        "idempotency_key": result.idempotency_key,
        "status": result.status,
        "inbox_id": result.inbox_id,
        "clinical_approval": "not_performed",
    }


class InboxRejectionRequest(BaseModel):
    reason: str = Field(min_length=3, max_length=2000)


# ── GET /integrations/inbox ───────────────────────────────────────────────────


@router.get("/inbox", summary="List staged integration events")
def list_inbox_events(
    event_status: str | None = Query(default=None, alias="status"),
    source_service: str | None = Query(default=None, min_length=1, max_length=80),
    limit: int = Query(default=50, ge=1, le=100),
    _user: LabUser = Depends(require_role("master_admin", "ministry_admin")),
    db=Depends(get_db),
) -> dict:
    """Return event metadata for reconciliation; payloads are not exposed in list views."""
    query = db.query(IntegrationInboxEvent)
    if event_status is not None:
        query = query.filter(IntegrationInboxEvent.status == event_status)
    if source_service is not None:
        query = query.filter(IntegrationInboxEvent.source_service == source_service)
    rows = query.order_by(IntegrationInboxEvent.received_at.desc()).limit(limit).all()
    return {
        "events": [
            {
                "inbox_id": row.id,
                "event_id": row.event_id,
                "event_type": row.event_type,
                "source_service": row.source_service,
                "tenant_id": row.tenant_id,
                "entity_id": row.entity_id,
                "status": row.status,
                "received_at": row.received_at,
                "processed_at": row.processed_at,
                "rejection_reason": row.rejection_reason,
            }
            for row in rows
        ],
        "clinical_approval": "not_performed",
    }


# ── POST /integrations/inbox/{inbox_id}/reject ────────────────────────────────


@router.post("/inbox/{inbox_id}/reject", summary="Reject an integration event")
def reject_inbox_event(
    inbox_id: int,
    request_body: InboxRejectionRequest,
    request: Request,
    reviewer: LabUser = Depends(require_role("master_admin", "ministry_admin")),
    db=Depends(get_db),
) -> dict:
    """Quarantine an event with an explicit reason; this never approves clinical data."""
    try:
        record = reject_event(db, inbox_id, request_body.reason)
        log_action(
            db,
            action="integration_inbox_rejected",
            resource_type="integration_inbox_event",
            resource_id=record.id,
            user_id=reviewer.id,
            user_role=reviewer.role,
            lab_id=getattr(reviewer, "lab_id", None),
            details={
                "event_id": record.event_id,
                "event_type": record.event_type,
                "source_service": record.source_service,
                "reason": record.rejection_reason,
            },
            ip_address=request.client.host if request.client else None,
        )
        db.commit()
    except HTTPException:
        db.rollback()
        raise
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    except Exception as exc:
        db.rollback()
        logger.exception("Integration inbox rejection failed inbox_id=%s", inbox_id)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Inbox review unavailable",
        ) from exc

    return {
        "inbox_id": record.id,
        "event_id": record.event_id,
        "status": record.status,
        "clinical_approval": "not_performed",
    }


# ── POST /integrations/identity-bundles ──────────────────────────────────────


@router.post("/identity-bundles", status_code=status.HTTP_202_ACCEPTED, summary="Import a signed offline identity bundle")
def receive_identity_bundle(
    bundle: dict[str, Any],
    principal=Depends(require_service_account),
    db=Depends(get_db),
) -> dict:
    """Verify an offline identity bundle before staging its minimum claims."""
    _authorize_event_ingress(principal)
    encoded_key = os.getenv("GULA_IDENTITY_PUBLIC_KEY_PEM", "")
    if not encoded_key.strip():
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Identity public key is not configured")
    public_key_pem = encoded_key.replace("\\n", "\n").encode("utf-8")
    try:
        envelope = verify_identity_bundle(bundle, public_key_pem)
        result = stage_event(db, envelope)
        db.commit()
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except Exception as exc:
        db.rollback()
        logger.exception("Signed identity bundle import failed")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Identity bundle import unavailable",
        ) from exc

    return {
        "event_id": result.event_id,
        "idempotency_key": result.idempotency_key,
        "status": result.status,
        "inbox_id": result.inbox_id,
        "clinical_approval": "not_performed",
    }


# ── GET /integrations/status ─────────────────────────────────────────────────


@router.get("/status")
def integrations_status(
    _user: LabUser = Depends(require_role("master_admin", "ministry_admin")),
) -> dict:
    """Snapshot of every registered adapter — mode + circuit + trust level."""
    return {
        "adapters": [_snapshot(name, getter()) for name, getter in _GETTERS.items()],
    }


# ── POST /integrations/{name}/probe ──────────────────────────────────────────


@router.post("/{name}/probe")
def integrations_probe(
    name: str,
    _user: LabUser = Depends(require_role("master_admin", "ministry_admin")),
) -> dict:
    """Force a probe call against a single adapter."""
    if name not in _PROBES:
        raise HTTPException(status_code=404, detail=f"unknown adapter: {name}")

    try:
        result = _PROBES[name]()
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Probe failed") from exc

    # Result is ExternalDataResult — reduce to safe dict
    return {
        "name": name,
        "source": result.source,
        "is_stale": result.is_stale,
        "requires_verification": result.requires_verification,
        "trust_level": result.trust_level.value,
        "data": result.data,
    }
