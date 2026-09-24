"""The writer the verification architecture never had (NR-040).

`niam_verification_records` is migration-backed, has an eight-state machine, a
provider-neutral protocol and a fail-closed adapter — and until AUTH-005 nothing
in `app/` created a row. One place *read* the table: `_professional_eligible`
gates professional workspace creation on a verified professional record. With no
writer, that query could only ever return nothing, so professional workspaces
were unreachable by construction.

This service is the missing half. It does not add a verification subsystem; it
drives the one that exists:

    request()  -> a record in `pending`, purpose and method recorded
    start()    -> `in_progress`, via the state machine
    apply()    -> the provider's result, scored by policy, never by the provider

Three rules hold throughout.

**Only a provider result can reach `verified`.** `apply_provider_result` refuses
any transition the state machine does not allow, so a record cannot be promoted
from `failed` or `pending` straight to `verified`.

**The provider does not grade its own work.** The assurance written to the row is
`VerificationPolicy`'s, computed from the method. A provider claiming L3 for an
emailed code still yields contact L1.

**`NotConnectedProvider` stays fail-closed.** It is the adapter for integrations
this deployment does not have, it returns `not_connected`, and this service maps
that to `failed` — never to success. Nothing here turns it into a stub that
passes.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from app._compat import UTC
from app.identity.models.verification_record import (
    VerificationRecord,
    VerificationRecordStatus,
    VerificationRecordType,
)
from app.identity.services.verification_record_service import VerificationRecordService
from app.identity.services.verification_service import (
    AssuranceEngine,
    AssuranceProfile,
    VerificationMethod,
    VerificationPolicy,
    VerificationPurpose,
    VerificationResult,
    VerificationStatus,
)
from app.services.audit_service import log_action


class VerificationWorkflowError(ValueError):
    """Raised when a workflow step is not permitted."""


class VerificationWorkflow:
    """Create and advance verification records for one canonical account."""

    def __init__(
        self,
        db: Session,
        *,
        actor_id: int | None = None,
        actor_role: str | None = None,
        request_ip: str | None = None,
    ) -> None:
        self.db = db
        self.actor_id = actor_id
        self.actor_role = actor_role
        self.request_ip = request_ip

    # ── creating ─────────────────────────────────────────────────────────────

    def request(
        self,
        *,
        account_id: str,
        identity_id: str,
        method: VerificationMethod,
        provider: str,
        professional_type: str | None = None,
    ) -> VerificationRecord:
        """Open a verification, recording what it is for before it is answered.

        The purpose comes from the method through the single policy, so a record
        cannot be filed under a purpose its method does not establish.
        """
        purpose = VerificationPolicy.purpose_for(method)
        record = VerificationRecord(
            uuid=str(uuid.uuid4()),
            account_id=account_id,
            identity_id=identity_id,
            record_type=self._record_type_for(purpose),
            method=method.value,
            provider=provider,
            status=VerificationRecordStatus.not_started.value,
            assurance_level="L0",
            requested_at=datetime.now(UTC),
            verification_session_id=uuid.uuid4().hex,
            professional_type=professional_type,
            is_active=True,
        )
        self.db.add(record)
        self.db.flush()
        VerificationRecordService.transition(record, VerificationRecordStatus.pending)
        self._audit("verification_requested", record, f"purpose={purpose.value};method={method.value}")
        return record

    def start(self, record: VerificationRecord) -> VerificationRecord:
        VerificationRecordService.transition(record, VerificationRecordStatus.in_progress)
        self.db.flush()
        self._audit("verification_started", record, f"method={record.method}")
        return record

    # ── answering ────────────────────────────────────────────────────────────

    def apply(self, record: VerificationRecord, result: VerificationResult) -> VerificationRecord:
        """Record a provider's answer, scored by policy rather than by the provider.

        A result for a different method than the record was opened for is
        refused: the purpose was fixed when the record was created, and letting
        the answer change it would let a contact check close an identity request.
        """
        if str(record.method) != result.method.value:
            raise VerificationWorkflowError(
                f"This record was opened for {record.method!r}; a {result.method.value!r} "
                "result cannot answer it"
            )

        VerificationRecordService.apply_provider_result(record, result)
        self.db.flush()

        outcome = str(record.status)
        detail = (
            f"method={record.method};assurance={record.assurance_level};status={outcome}"
        )
        if result.status == VerificationStatus.not_connected:
            detail += ";provider=not_connected"
        self._audit(
            "verification_verified" if outcome == VerificationRecordStatus.verified.value
            else "verification_blocked",
            record,
            detail,
        )
        return record

    def revoke(self, record: VerificationRecord, *, reason: str) -> VerificationRecord:
        VerificationRecordService.revoke(record)
        record.failure_reason_code = reason
        self.db.flush()
        self._audit("verification_revoked", record, f"reason={reason}")
        return record

    def expire(self, record: VerificationRecord) -> VerificationRecord:
        VerificationRecordService.expire(record)
        self.db.flush()
        self._audit("verification_expired", record, f"method={record.method}")
        return record

    # ── reading ──────────────────────────────────────────────────────────────

    def profile(self, account_id: str) -> AssuranceProfile:
        """What this account has proven, per purpose, from its records."""
        from app.identity.services.identity_link_policy import assurance_profile_for_account

        profile, _evidence = assurance_profile_for_account(self.db, account_id)
        return profile

    # ── internals ────────────────────────────────────────────────────────────

    _RECORD_TYPE = {
        VerificationPurpose.contact: VerificationRecordType.contact,
        VerificationPurpose.identity: VerificationRecordType.identity,
        VerificationPurpose.professional: VerificationRecordType.professional,
        VerificationPurpose.organization: VerificationRecordType.organization,
    }

    @classmethod
    def _record_type_for(cls, purpose: VerificationPurpose) -> str:
        return cls._RECORD_TYPE[purpose].value

    def _audit(self, action: str, record: VerificationRecord, detail: str) -> None:
        log_action(
            self.db,
            action=action,
            resource_type="verification_record",
            resource_id=None,
            user_id=self.actor_id,
            user_role=self.actor_role,
            ip_address=self.request_ip,
            details=f"record_id={record.id};account_id={record.account_id};{detail}",
        )


def assurance_for(db: Session, account_id: str) -> AssuranceProfile:
    """Convenience reader for callers that only need the profile."""
    from app.identity.services.identity_link_policy import assurance_profile_for_account

    profile, _ = assurance_profile_for_account(db, account_id)
    return profile


__all__ = [
    "AssuranceEngine",
    "VerificationWorkflow",
    "VerificationWorkflowError",
    "assurance_for",
]
