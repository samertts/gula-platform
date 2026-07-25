from __future__ import annotations

import logging
import threading
import time
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

from security.modules.fhir.models import BreakGlassAccess, PurposeOfUse

logger = logging.getLogger("gula.security.modules.fhir.break_glass")

_DEFAULT_DURATION_MINUTES = 30
_MAX_DURATION_MINUTES = 120
_PROLONGED_DURATION_MINUTES = 60
_NOTIFICATION_COOLDOWN = 300


class BreakGlassManager:
    def __init__(self, audit_callback: Any | None = None, notification_callback: Any | None = None) -> None:
        self._lock = threading.Lock()
        self._access_grants: dict[str, BreakGlassAccess] = {}
        self._active_grants: dict[str, list[str]] = {}
        self._audit_callback = audit_callback
        self._notification_callback = notification_callback
        self._notified: dict[str, float] = {}

    def request_access(
        self,
        accessor_id: str,
        patient_id: str,
        reason: str,
        duration_minutes: int = _DEFAULT_DURATION_MINUTES,
        approved_by: str = "",
    ) -> dict[str, Any]:
        if duration_minutes > _MAX_DURATION_MINUTES:
            return {
                "error": "duration_exceeds_maximum",
                "message": f"Break glass duration cannot exceed {_MAX_DURATION_MINUTES} minutes",
            }

        if not reason.strip():
            return {"error": "reason_required", "message": "A justification reason is required for break glass access"}

        if not accessor_id or not patient_id:
            return {"error": "missing_required_fields", "message": "Accessor and patient IDs are required"}

        grant_id = str(uuid4())
        access = BreakGlassAccess(
            accessor_id=accessor_id,
            patient_id=patient_id,
            reason=reason,
            duration_minutes=duration_minutes,
            approved_by=approved_by,
            timestamp=datetime.now(timezone.utc),
            status="active" if approved_by else "pending",
        )

        with self._lock:
            self._access_grants[grant_id] = access
            self._active_grants.setdefault(accessor_id, []).append(grant_id)

        logger.warning(
            "Break glass access requested: grant=%s accessor=%s patient=%s reason=%s",
            grant_id[:16], accessor_id, patient_id, reason,
        )

        self._notify(accessor_id, patient_id, reason)

        if self._audit_callback:
            try:
                self._audit_callback(
                    event_type="break_glass_requested",
                    user_id=accessor_id,
                    patient_id=patient_id,
                    details={"grant_id": grant_id, "reason": reason, "duration_minutes": duration_minutes},
                )
            except Exception as exc:
                logger.warning("Audit callback failed: %s", exc)

        return {
            "grant_id": grant_id,
            "status": access.status,
            "duration_minutes": duration_minutes,
            "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=duration_minutes)).isoformat(),
            "message": "Break glass access requested" if not approved_by else "Break glass access granted",
        }

    def approve_access(self, grant_id: str, approver_id: str) -> dict[str, Any]:
        with self._lock:
            access = self._access_grants.get(grant_id)
            if access is None:
                return {"error": "grant_not_found"}
            if access.status != "pending":
                return {"error": "grant_already_processed", "status": access.status}

            access.status = "active"
            access.approved_by = approver_id

        logger.info(
            "Break glass access approved: grant=%s approver=%s",
            grant_id[:16], approver_id,
        )

        return {
            "grant_id": grant_id,
            "status": "active",
            "message": "Break glass access approved",
            "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=access.duration_minutes)).isoformat(),
        }

    def verify_access(self, accessor_id: str, patient_id: str) -> dict[str, Any]:
        with self._lock:
            grant_ids = self._active_grants.get(accessor_id, [])
            now = datetime.now(timezone.utc)

            for gid in grant_ids:
                access = self._access_grants.get(gid)
                if access is None:
                    continue
                if access.patient_id != patient_id:
                    continue
                if access.status != "active":
                    continue

                created = access.timestamp
                if created is None:
                    continue
                if now - created > timedelta(minutes=access.duration_minutes):
                    access.status = "expired"
                    continue

                return {
                    "verified": True,
                    "grant_id": gid,
                    "reason": access.reason,
                    "expires_at": (created + timedelta(minutes=access.duration_minutes)).isoformat(),
                }

        return {"verified": False, "reason": "No active break glass grant found"}

    def extend_access(self, grant_id: str, additional_minutes: int = 30) -> dict[str, Any]:
        with self._lock:
            access = self._access_grants.get(grant_id)
            if access is None:
                return {"error": "grant_not_found"}
            if access.status != "active":
                return {"error": "grant_not_active", "status": access.status}

            if access.duration_minutes + additional_minutes > _MAX_DURATION_MINUTES * 2:
                return {"error": "extension_exceeds_maximum"}

            if additional_minutes >= _PROLONGED_DURATION_MINUTES:
                return {
                    "error": "dual_authorization_required",
                    "message": "Extensions over 60 minutes require dual authorization",
                }

            access.duration_minutes += additional_minutes

        return {
            "grant_id": grant_id,
            "new_duration_minutes": access.duration_minutes,
            "new_expires_at": (
                datetime.now(timezone.utc) + timedelta(minutes=access.duration_minutes)
            ).isoformat(),
        }

    def revoke_access(self, grant_id: str, revoker_id: str, reason: str = "") -> bool:
        with self._lock:
            access = self._access_grants.get(grant_id)
            if access is None:
                return False
            if access.status != "active":
                return False

            access.status = "revoked"
            access.review_notes = reason

        logger.warning("Break glass access revoked: grant=%s revoker=%s", grant_id[:16], revoker_id)

        if self._audit_callback:
            try:
                self._audit_callback(
                    event_type="break_glass_revoked",
                    user_id=revoker_id,
                    patient_id=access.patient_id,
                    details={"grant_id": grant_id, "reason": reason},
                )
            except Exception:
                pass

        return True

    def get_active_grants(self, patient_id: str | None = None) -> list[dict[str, Any]]:
        now = datetime.now(timezone.utc)
        result: list[dict[str, Any]] = []

        with self._lock:
            for gid, access in self._access_grants.items():
                if access.status != "active":
                    continue
                if patient_id and access.patient_id != patient_id:
                    continue

                created = access.timestamp
                if created and now - created > timedelta(minutes=access.duration_minutes):
                    access.status = "expired"
                    continue

                result.append({
                    "grant_id": gid,
                    "accessor_id": access.accessor_id,
                    "patient_id": access.patient_id,
                    "reason": access.reason,
                    "duration_minutes": access.duration_minutes,
                    "approved_by": access.approved_by,
                    "created_at": access.timestamp.isoformat() if access.timestamp else "",
                })

        return result

    def get_access_history(self, patient_id: str) -> list[dict[str, Any]]:
        history: list[dict[str, Any]] = []
        with self._lock:
            for gid, access in self._access_grants.items():
                if access.patient_id != patient_id:
                    continue
                history.append({
                    "grant_id": gid,
                    "accessor_id": access.accessor_id,
                    "reason": access.reason,
                    "status": access.status,
                    "duration_minutes": access.duration_minutes,
                    "approved_by": access.approved_by,
                    "timestamp": access.timestamp.isoformat() if access.timestamp else "",
                    "reviewed": access.reviewed,
                })
        return sorted(history, key=lambda x: x["timestamp"], reverse=True)

    def review_access(self, grant_id: str, reviewer_id: str, notes: str = "") -> bool:
        with self._lock:
            access = self._access_grants.get(grant_id)
            if access is None:
                return False
            access.reviewed = True
            access.review_notes = notes

        if self._audit_callback:
            try:
                self._audit_callback(
                    event_type="break_glass_reviewed",
                    user_id=reviewer_id,
                    patient_id=access.patient_id,
                    details={"grant_id": grant_id, "notes": notes},
                )
            except Exception:
                pass

        return True

    def cleanup_expired(self) -> int:
        now = datetime.now(timezone.utc)
        count = 0
        with self._lock:
            for gid, access in list(self._access_grants.items()):
                created = access.timestamp
                if created and now - created > timedelta(minutes=access.duration_minutes):
                    if access.status == "active":
                        access.status = "expired"
                        count += 1
                    elif access.status == "expired":
                        pass
        return count

    def _notify(self, accessor_id: str, patient_id: str, reason: str) -> None:
        now = time.time()
        notify_key = f"{patient_id}:{accessor_id}"
        if notify_key in self._notified:
            if now - self._notified[notify_key] < _NOTIFICATION_COOLDOWN:
                return

        self._notified[notify_key] = now

        if self._notification_callback:
            try:
                self._notification_callback(
                    event="break_glass_access",
                    accessor_id=accessor_id,
                    patient_id=patient_id,
                    reason=reason,
                )
            except Exception as exc:
                logger.warning("Notification callback failed: %s", exc)
