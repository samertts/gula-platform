from __future__ import annotations

import hashlib
import hmac
import json
import os
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app._compat import UTC
from app.config import AUDIT_ANCHOR_KEY
from app.identity.models.citizen_relationship import (
    CitizenRelationship,
    CitizenRelationshipSource,
    CitizenRelationshipStatus,
    CitizenRelationshipType,
)
from app.models.lab_user import LabUser
from app.models.user import User
from app.national.domain.citizen import Citizen
from app.national.domain.patient import Patient
from app.services.audit_service import log_action


class CitizenRelationshipWorkflowError(ValueError):
    """Base error for explicit, operator-reviewed relationship workflows."""


class CitizenRelationshipNotFound(CitizenRelationshipWorkflowError):
    pass


class CitizenRelationshipConflict(CitizenRelationshipWorkflowError):
    pass


class CitizenRelationshipUnsupported(CitizenRelationshipWorkflowError):
    pass


REVOCATION_REASON_CODES = frozenset(
    {
        "user_request",
        "verification_failed",
        "policy_change",
        "duplicate",
        "security_event",
        "administrative_correction",
    }
)


def _workflow_key() -> bytes:
    key = os.getenv("GULA_RELATION_WORKFLOW_KEY") or AUDIT_ANCHOR_KEY
    if not key or len(key) < 32:
        raise RuntimeError(
            "GULA_RELATION_WORKFLOW_KEY or AUDIT_ANCHOR_KEY must be at least 32 characters"
        )
    return key.encode("utf-8")


def _digest(value: str) -> str:
    return hmac.new(_workflow_key(), value.encode("utf-8"), hashlib.sha256).hexdigest()


def _now() -> datetime:
    return datetime.now(UTC)


def _canonical_scope(scope: dict[str, Any]) -> dict[str, list[str]]:
    resources = scope.get("resources") if isinstance(scope, dict) else None
    if not isinstance(resources, list) or not resources:
        raise CitizenRelationshipConflict("scope.resources must contain at least one resource")
    normalized = sorted({str(resource).strip() for resource in resources if str(resource).strip()})
    if not normalized or "*" in normalized:
        raise CitizenRelationshipConflict("Wildcard relationship scope is not allowed in C2")
    if any(len(resource) > 80 for resource in normalized):
        raise CitizenRelationshipConflict("Relationship scope resource is too long")
    return {"resources": normalized}


def _request_fingerprint(payload: dict[str, Any]) -> str:
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return _digest(f"request:{serialized}")


def _serialize(relationship: CitizenRelationship) -> dict[str, Any]:
    return {
        "id": relationship.id,
        "source_kind": relationship.source_kind,
        "legacy_user_id": relationship.legacy_user_id,
        "citizen_id": relationship.citizen_id,
        "patient_id": relationship.patient_id,
        "relationship_type": relationship.relationship_type,
        "status": relationship.status,
        "purpose": relationship.purpose,
        "scope": relationship.scope,
        "valid_from": relationship.valid_from.isoformat() if relationship.valid_from else None,
        "expires_at": relationship.expires_at.isoformat() if relationship.expires_at else None,
        "verified_at": relationship.verified_at.isoformat() if relationship.verified_at else None,
        "revoked_at": relationship.revoked_at.isoformat() if relationship.revoked_at else None,
        "version": relationship.version,
    }


class CitizenRelationshipWorkflow:
    """Explicit C2 workflow; never performs matching, backfill, or dual-write."""

    def __init__(self, db: Session, actor: LabUser, request_ip: str | None = None) -> None:
        self.db = db
        self.actor = actor
        self.request_ip = request_ip

    def create_pending(
        self,
        *,
        source_kind: str,
        legacy_user_id: int,
        citizen_id: str,
        patient_id: str | None,
        relationship_type: str,
        purpose: str,
        scope: dict[str, Any],
        idempotency_key: str,
    ) -> CitizenRelationship:
        if source_kind != CitizenRelationshipSource.legacy_user.value:
            raise CitizenRelationshipUnsupported("C2 currently supports legacy_user sources only")
        if relationship_type != CitizenRelationshipType.self.value:
            raise CitizenRelationshipUnsupported("C2 currently supports self relationships only")
        if purpose != "citizen_workspace":
            raise CitizenRelationshipUnsupported("Unsupported relationship purpose")
        if not 16 <= len(idempotency_key) <= 128:
            raise CitizenRelationshipConflict("Idempotency-Key must be 16 to 128 characters")

        normalized_scope = _canonical_scope(scope)
        source = self.db.query(User).filter(User.id == legacy_user_id).first()
        if source is None or not source.is_active or source.role != "citizen":
            raise CitizenRelationshipConflict("Source account is not an active citizen account")

        citizen = self.db.query(Citizen).filter(Citizen.id == citizen_id).first()
        if citizen is None:
            raise CitizenRelationshipNotFound("Citizen record not found")
        if citizen.is_deceased or citizen.merged_into_id:
            raise CitizenRelationshipConflict("Citizen record is not linkable")

        patient = None
        if patient_id is not None:
            patient = self.db.query(Patient).filter(Patient.id == patient_id).first()
            if (
                patient is None
                or patient.citizen_id != citizen_id
                or not patient.is_active
                or patient.is_merged
            ):
                raise CitizenRelationshipConflict(
                    "Patient record is not linked to the selected citizen"
                )

        payload = {
            "source_kind": source_kind,
            "legacy_user_id": legacy_user_id,
            "citizen_id": citizen_id,
            "patient_id": patient_id,
            "relationship_type": relationship_type,
            "purpose": purpose,
            "scope": normalized_scope,
        }
        fingerprint = _request_fingerprint(payload)
        key_hash = _digest(f"idempotency:{idempotency_key}")
        existing_by_key = (
            self.db.query(CitizenRelationship)
            .filter(CitizenRelationship.idempotency_key_hash == key_hash)
            .with_for_update()
            .first()
        )
        if existing_by_key:
            if existing_by_key.request_fingerprint != fingerprint:
                raise CitizenRelationshipConflict(
                    "Idempotency-Key was reused for a different request"
                )
            return existing_by_key

        duplicate = (
            self.db.query(CitizenRelationship)
            .filter(
                CitizenRelationship.source_kind == source_kind,
                CitizenRelationship.legacy_user_id == legacy_user_id,
                CitizenRelationship.citizen_id == citizen_id,
                CitizenRelationship.patient_id == patient_id,
                CitizenRelationship.relationship_type == relationship_type,
                CitizenRelationship.purpose == purpose,
                CitizenRelationship.status.in_(
                    (
                        CitizenRelationshipStatus.pending.value,
                        CitizenRelationshipStatus.active.value,
                    )
                ),
            )
            .with_for_update()
            .first()
        )
        if duplicate:
            if duplicate.request_fingerprint != fingerprint:
                raise CitizenRelationshipConflict(
                    "An equivalent active relationship already exists with different scope"
                )
            return duplicate

        relationship = CitizenRelationship(
            source_kind=source_kind,
            legacy_user_id=legacy_user_id,
            citizen_id=citizen_id,
            patient_id=patient_id,
            relationship_type=relationship_type,
            status=CitizenRelationshipStatus.pending.value,
            purpose=purpose,
            scope=normalized_scope,
            valid_from=_now(),
            version=1,
            idempotency_key_hash=key_hash,
            request_fingerprint=fingerprint,
            metadata_={"workflow": "c2", "source_verified": bool(source.is_verified)},
        )
        self.db.add(relationship)
        self.db.flush()
        log_action(
            self.db,
            action="citizen_relationship_created",
            resource_type="citizen_relationship",
            resource_id=None,
            user_id=self.actor.id,
            user_role=self.actor.role,
            ip_address=self.request_ip,
            details=(
                f"relationship_id={relationship.id};status=pending;source_kind={source_kind};"
                f"legacy_user_id={legacy_user_id};citizen_id={citizen_id};patient_id={patient_id};"
                f"scope={json.dumps(normalized_scope, sort_keys=True)}"
            ),
        )
        self.db.commit()
        self.db.refresh(relationship)
        return relationship

    def activate(self, relationship_id: str, *, verification_reference: str) -> CitizenRelationship:
        if not 8 <= len(verification_reference.strip()) <= 255:
            raise CitizenRelationshipConflict("A non-sensitive verification reference is required")
        relationship = self._for_update(relationship_id)
        if relationship.status == CitizenRelationshipStatus.active.value:
            return relationship
        if relationship.status != CitizenRelationshipStatus.pending.value:
            raise CitizenRelationshipConflict(
                f"Cannot activate relationship from {relationship.status}"
            )
        source = self.db.query(User).filter(User.id == relationship.legacy_user_id).first()
        if source is None or not source.is_active or not source.is_verified:
            raise CitizenRelationshipConflict(
                "Source account must be active and verified before activation"
            )
        old_status = relationship.status
        if relationship.version is None:
            raise CitizenRelationshipConflict("Relationship version is required for activation")
        relationship.status = CitizenRelationshipStatus.active.value
        relationship.verified_at = _now()
        relationship.version += 1
        relationship.metadata_ = {
            **(relationship.metadata_ or {}),
            "verification_reference_digest": _digest(
                f"verification:{verification_reference.strip()}"
            ),
            "verified_by_legacy_user_id": self.actor.id,
        }
        self.db.flush()
        log_action(
            self.db,
            action="citizen_relationship_activated",
            resource_type="citizen_relationship",
            resource_id=None,
            user_id=self.actor.id,
            user_role=self.actor.role,
            ip_address=self.request_ip,
            details=f"relationship_id={relationship.id};from={old_status};to=active;version={relationship.version}",
        )
        self.db.commit()
        self.db.refresh(relationship)
        return relationship

    def revoke(self, relationship_id: str, *, reason: str) -> CitizenRelationship:
        reason = reason.strip()
        if reason not in REVOCATION_REASON_CODES:
            raise CitizenRelationshipConflict("Unsupported revocation reason code")
        relationship = self._for_update(relationship_id)
        if relationship.status == CitizenRelationshipStatus.revoked.value:
            return relationship
        if relationship.status not in {
            CitizenRelationshipStatus.pending.value,
            CitizenRelationshipStatus.active.value,
        }:
            raise CitizenRelationshipConflict(
                f"Cannot revoke relationship from {relationship.status}"
            )
        old_status = relationship.status
        if relationship.version is None:
            raise CitizenRelationshipConflict("Relationship version is required for revocation")
        relationship.status = CitizenRelationshipStatus.revoked.value
        relationship.revoked_at = _now()
        relationship.revoked_reason = reason
        relationship.version += 1
        relationship.metadata_ = {
            **(relationship.metadata_ or {}),
            "revoked_by_legacy_user_id": self.actor.id,
        }
        self.db.flush()
        log_action(
            self.db,
            action="citizen_relationship_revoked",
            resource_type="citizen_relationship",
            resource_id=None,
            user_id=self.actor.id,
            user_role=self.actor.role,
            ip_address=self.request_ip,
            details=f"relationship_id={relationship.id};from={old_status};to=revoked;version={relationship.version};reason_code={reason}",
        )
        self.db.commit()
        self.db.refresh(relationship)
        return relationship

    def _for_update(self, relationship_id: str) -> CitizenRelationship:
        relationship = (
            self.db.query(CitizenRelationship)
            .filter(CitizenRelationship.id == relationship_id)
            .with_for_update()
            .first()
        )
        if relationship is None:
            raise CitizenRelationshipNotFound("Citizen relationship not found")
        return relationship


__all__ = [
    "REVOCATION_REASON_CODES",
    "CitizenRelationshipConflict",
    "CitizenRelationshipNotFound",
    "CitizenRelationshipUnsupported",
    "CitizenRelationshipWorkflow",
    "CitizenRelationshipWorkflowError",
    "_serialize",
]
