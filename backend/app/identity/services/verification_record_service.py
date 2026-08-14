from __future__ import annotations

from datetime import datetime

from app._compat import UTC
from app.identity.models.verification_record import VerificationRecord, VerificationRecordStatus
from app.identity.services.verification_service import (
    AssuranceLevel,
    VerificationPolicy,
    VerificationResult,
    VerificationStatus,
)

LEGAL_TRANSITIONS: dict[str, frozenset[str]] = {
    VerificationRecordStatus.not_started.value: frozenset({VerificationRecordStatus.pending.value}),
    VerificationRecordStatus.pending.value: frozenset({VerificationRecordStatus.in_progress.value, VerificationRecordStatus.failed.value}),
    VerificationRecordStatus.in_progress.value: frozenset({
        VerificationRecordStatus.verified.value,
        VerificationRecordStatus.failed.value,
        VerificationRecordStatus.requires_review.value,
    }),
    VerificationRecordStatus.verified.value: frozenset({
        VerificationRecordStatus.expired.value,
        VerificationRecordStatus.revoked.value,
    }),
    VerificationRecordStatus.failed.value: frozenset({VerificationRecordStatus.pending.value}),
    VerificationRecordStatus.expired.value: frozenset(),
    VerificationRecordStatus.revoked.value: frozenset(),
    VerificationRecordStatus.requires_review.value: frozenset({
        VerificationRecordStatus.verified.value,
        VerificationRecordStatus.failed.value,
    }),
}


class InvalidVerificationTransition(ValueError):
    """Raised when verification state is changed outside the backend state machine."""


class VerificationRecordService:
    @staticmethod
    def transition(record: VerificationRecord, target: VerificationRecordStatus) -> VerificationRecord:
        current = str(record.status)
        target_value = target.value
        if target_value not in LEGAL_TRANSITIONS.get(current, frozenset()):
            raise InvalidVerificationTransition(f"Illegal verification transition: {current} -> {target_value}")
        record.status = target_value
        now = datetime.now(UTC)
        if target == VerificationRecordStatus.in_progress:
            record.started_at = now
        elif target == VerificationRecordStatus.verified:
            record.completed_at = now
            record.valid_from = record.valid_from or now
            record.is_active = True
        elif target in {VerificationRecordStatus.expired, VerificationRecordStatus.revoked}:
            record.revoked_at = now if target == VerificationRecordStatus.revoked else record.revoked_at
            record.is_active = False
            record.assurance_level = AssuranceLevel.L0.value
        return record

    @staticmethod
    def apply_provider_result(record: VerificationRecord, result: VerificationResult) -> VerificationRecord:
        if result.status == VerificationStatus.verified:
            VerificationRecordService.transition(record, VerificationRecordStatus.verified)
            record.assurance_level = VerificationPolicy.assurance_for(result).value
            record.provider_reference = result.provider_reference
            record.verified_attributes = result.verified_attributes
        elif result.status == VerificationStatus.requires_review:
            VerificationRecordService.transition(record, VerificationRecordStatus.requires_review)
            record.assurance_level = AssuranceLevel.L0.value
        elif result.status in {VerificationStatus.failed, VerificationStatus.not_connected}:
            VerificationRecordService.transition(record, VerificationRecordStatus.failed)
            record.assurance_level = AssuranceLevel.L0.value
            record.failure_reason_code = result.reason
        return record

    @staticmethod
    def revoke(record: VerificationRecord) -> VerificationRecord:
        return VerificationRecordService.transition(record, VerificationRecordStatus.revoked)

    @staticmethod
    def expire(record: VerificationRecord) -> VerificationRecord:
        return VerificationRecordService.transition(record, VerificationRecordStatus.expired)
