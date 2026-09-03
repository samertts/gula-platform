"""Safety guard for clinical state-changing commands.

The guard is deliberately service-layer friendly: routes extract transport
headers, while the guard enforces durable idempotency, optimistic locking, and
structured audit details before a clinical state is changed.  Callers must keep
``claim`` and ``complete`` in the same database transaction as the state write.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app._compat import UTC
from app.clinical.observability import clinical_safety_metrics, reason_code
from app.models.clinical_command import ClinicalCommandReceipt
from app.services.audit_service import log_action


class ClinicalCommandGuard:
    """Enforce non-bypassable preconditions for a clinical command."""

    def __init__(self, db: Session, *, actor_user_id: int, lab_id: int, actor_role: str) -> None:
        self.db = db
        self.actor_user_id = actor_user_id
        self.lab_id = lab_id
        self.actor_role = actor_role

    @staticmethod
    def require_idempotency_key(idempotency_key: str | None) -> str:
        if not idempotency_key or not idempotency_key.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "idempotency_key_required",
                    "message": "Idempotency-Key header is required for this clinical operation.",
                    "message_ar": "ترويسة Idempotency-Key مطلوبة لهذه العملية السريرية.",
                },
            )
        key = idempotency_key.strip()
        if len(key) > 128:
            raise HTTPException(status_code=400, detail="Idempotency-Key exceeds 128 characters")
        return key

    @staticmethod
    def require_expected_version(if_match: str | None, *, current_version: int, resource_name: str) -> int:
        if if_match is None:
            raise HTTPException(
                status_code=status.HTTP_428_PRECONDITION_REQUIRED,
                detail={
                    "error": "if_match_required",
                    "message": f"If-Match version is required to change this {resource_name}.",
                    "message_ar": f"ترويسة If-Match مطلوبة لتغيير {resource_name}.",
                },
            )
        try:
            expected_version = int(if_match.strip().strip('"'))
        except (AttributeError, ValueError) as exc:
            raise HTTPException(
                status_code=400,
                detail="If-Match must contain an integer resource version",
            ) from exc
        if expected_version != current_version:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error": "clinical_version_conflict",
                    "expected_version": expected_version,
                    "current_version": current_version,
                    "message": "The clinical record changed before this operation could be applied.",
                    "message_ar": "تم تغيير السجل السريري قبل تطبيق هذه العملية.",
                },
            )
        return expected_version

    @staticmethod
    def _fingerprint(operation: str, resource_type: str, resource_id: str | int, payload: Any) -> str:
        canonical = json.dumps(
            {
                "operation": operation,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "payload": payload,
            },
            sort_keys=True,
            ensure_ascii=False,
            default=str,
            separators=(",", ":"),
        )
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def claim(
        self,
        *,
        operation: str,
        resource_type: str,
        resource_id: str | int,
        idempotency_key: str,
        payload: Any,
    ) -> ClinicalCommandReceipt:
        """Claim an idempotency key before changing clinical state.

        Reusing a key never repeats side effects.  A key reused for a different
        command is rejected explicitly; a matching replay receives a conflict
        because the present routes do not yet persist response payloads.
        """
        fingerprint = self._fingerprint(operation, resource_type, resource_id, payload)
        existing = (
            self.db.query(ClinicalCommandReceipt)
            .filter(
                ClinicalCommandReceipt.lab_id == self.lab_id,
                ClinicalCommandReceipt.actor_user_id == self.actor_user_id,
                ClinicalCommandReceipt.operation == operation,
                ClinicalCommandReceipt.idempotency_key == idempotency_key,
            )
            .first()
        )
        if existing:
            error = "idempotency_key_reused" if existing.request_fingerprint != fingerprint else "clinical_command_already_processed"
            clinical_safety_metrics.record_command(
                operation=operation,
                resource_type=resource_type,
                outcome="rejected",
                reason="duplicate_command",
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error": error,
                    "message": "This clinical command was already claimed and will not be repeated.",
                    "message_ar": "تمت معالجة هذا الأمر السريري أو حجزه مسبقاً ولن يُكرر.",
                },
            )

        receipt = ClinicalCommandReceipt(
            lab_id=self.lab_id,
            actor_user_id=self.actor_user_id,
            operation=operation,
            idempotency_key=idempotency_key,
            request_fingerprint=fingerprint,
            resource_type=resource_type,
            resource_id=str(resource_id),
            status="claimed",
        )
        self.db.add(receipt)
        try:
            self.db.flush()
        except IntegrityError as exc:
            # A concurrent transaction won the unique-key race.  Roll back the
            # claim and fail closed rather than repeating the clinical write.
            self.db.rollback()
            clinical_safety_metrics.record_command(
                operation=operation,
                resource_type=resource_type,
                outcome="rejected",
                reason="idempotency_race",
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error": "clinical_command_in_progress_or_complete",
                    "message": "This clinical command is already being processed or was completed.",
                    "message_ar": "هذا الأمر السريري قيد المعالجة أو اكتمل بالفعل.",
                },
            ) from exc
        clinical_safety_metrics.record_command(
            operation=operation,
            resource_type=resource_type,
            outcome="claimed",
        )
        return receipt

    @staticmethod
    def _audit_resource_id(resource_id: str | int | None) -> int | None:
        """Map legacy integer audit IDs without losing string resource identity."""
        if resource_id is None:
            return None
        try:
            return int(resource_id)
        except (TypeError, ValueError):
            return None

    def reject(
        self,
        *,
        operation: str,
        resource_type: str,
        resource_id: str | int,
        state_before: str | None,
        version_before: int,
        reason: str,
    ) -> None:
        """Record a rejected command after the failed transaction is rolled back."""
        try:
            log_action(
                self.db,
                action=f"clinical.{operation}.rejected",
                resource_type=resource_type,
                resource_id=self._audit_resource_id(resource_id),
                user_id=self.actor_user_id,
                user_role=self.actor_role,
                lab_id=self.lab_id,
                details={
                    "operation": operation,
                    "resource_id": str(resource_id),
                    "state_before": state_before,
                    "version_before": version_before,
                    "reason": reason,
                },
            )
        except Exception:
            clinical_safety_metrics.record_audit_failure(operation=operation, resource_type=resource_type)
            raise
        clinical_safety_metrics.record_command(
            operation=operation,
            resource_type=resource_type,
            outcome="rejected",
            reason=reason_code(reason),
        )

    def complete(
        self,
        receipt: ClinicalCommandReceipt,
        *,
        resource_type: str,
        resource_id: str | int,
        state_before: str | None,
        state_after: str | None,
        version_before: int,
        version_after: int,
        reason: str | None = None,
    ) -> None:
        """Finish the receipt and emit a structured, tamper-evident audit event."""
        receipt.status = "completed"
        receipt.resource_type = resource_type
        receipt.resource_id = str(resource_id)
        receipt.completed_at = datetime.now(UTC)
        self.db.flush()
        try:
            log_action(
                self.db,
                action=f"clinical.{receipt.operation}",
                resource_type=resource_type,
                resource_id=self._audit_resource_id(resource_id),
                user_id=self.actor_user_id,
                user_role=self.actor_role,
                lab_id=self.lab_id,
                details={
                    "operation": receipt.operation,
                    "resource_id": str(resource_id),
                    "idempotency_key": receipt.idempotency_key,
                    "state_before": state_before,
                    "state_after": state_after,
                    "version_before": version_before,
                    "version_after": version_after,
                    "reason": reason,
                },
            )
        except Exception:
            clinical_safety_metrics.record_audit_failure(
                operation=receipt.operation,
                resource_type=resource_type,
            )
            raise
        clinical_safety_metrics.record_command(
            operation=receipt.operation,
            resource_type=resource_type,
            outcome="completed",
        )
