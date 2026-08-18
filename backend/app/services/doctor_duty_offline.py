"""Offline clinical policy: verified Duty first, encrypted bounded dataset second.

This module intentionally returns only an authorization descriptor. The actual
clinical payload must be encrypted by the mobile/offline subsystem and synced
through its existing outbox/conflict-resolution workflow.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime

from app.services.doctor_duty_service import DutyAuthorizationError


@dataclass(frozen=True)
class OfflineDutyAuthorization:
    duty_context_id: str
    organization_id: int
    facility_id: int
    department_id: str | None
    ward_id: str | None
    expires_at: datetime
    dataset_fingerprint: str
    encryption_required: bool = True
    sync_required_on_reconnect: bool = True


def authorize_verified_offline_context(*, duty_context, now: datetime, requested_patient_ids: list[int]) -> OfflineDutyAuthorization:
    """Authorize only an already-started online context; never starts a new Duty."""
    if duty_context is None or duty_context.status != "ACTIVE":
        raise DutyAuthorizationError("OFFLINE_DUTY_NOT_VERIFIED")
    if duty_context.started_at > now or duty_context.expires_at <= now:
        raise DutyAuthorizationError("OFFLINE_DUTY_EXPIRED")
    if not requested_patient_ids or len(requested_patient_ids) > 500:
        raise DutyAuthorizationError("OFFLINE_DATASET_INVALID")
    assigned = set((duty_context.assigned_patient_ids or []))
    if assigned and not set(requested_patient_ids).issubset(assigned):
        raise DutyAuthorizationError("OFFLINE_PATIENT_SCOPE_DENIED")
    canonical = json.dumps({"duty_context_id": duty_context.id, "patients": sorted(requested_patient_ids), "expires_at": duty_context.expires_at.isoformat()}, sort_keys=True).encode()
    return OfflineDutyAuthorization(
        duty_context_id=duty_context.id,
        organization_id=duty_context.organization_id,
        facility_id=duty_context.facility_id,
        department_id=duty_context.department_id,
        ward_id=duty_context.ward_id,
        expires_at=duty_context.expires_at,
        dataset_fingerprint=hashlib.sha256(canonical).hexdigest(),
    )
