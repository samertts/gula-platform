import hashlib
import secrets
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app._compat import UTC

from ..enums import CardLifecycleEvent, HealthCardType, HealthNumberStatus, IdentityMergeAction
from ..models.health_number import (
    HealthCardLifecycle,
    HealthNumberAudit,
    HealthNumberRecord,
    MergedIdentityRecord,
)


class HealthNumberGovernanceService:
    def __init__(self, db: Session):
        self.db = db

    def generate_health_number(self, citizen_ulid: str, national_id_hash: str | None = None) -> str:
        raw = f"{citizen_ulid}-{secrets.token_hex(4)}-{datetime.now(UTC).strftime('%y%m')}"
        health_number = f"HN-{hashlib.sha256(raw.encode()).hexdigest()[:12].upper()}"
        record = HealthNumberRecord(
            health_number=health_number,
            citizen_ulid=citizen_ulid,
            national_id_hash=national_id_hash,
            status=HealthNumberStatus.ACTIVE,
            issued_at=datetime.now(UTC),
            activated_at=datetime.now(UTC),
        )
        self.db.add(record)
        self._audit(health_number, "issued", None, str(HealthNumberStatus.ACTIVE.value), "system")
        return health_number

    def get_health_number(self, health_number: str) -> HealthNumberRecord | None:
        return (
            self.db.query(HealthNumberRecord)
            .filter(HealthNumberRecord.health_number == health_number)
            .first()
        )

    def get_by_citizen(self, citizen_ulid: str) -> list[HealthNumberRecord]:
        return (
            self.db.query(HealthNumberRecord)
            .filter(HealthNumberRecord.citizen_ulid == citizen_ulid)
            .order_by(HealthNumberRecord.created_at.desc())
            .all()
        )

    def report_lost(self, health_number: str, reported_by: str) -> HealthNumberRecord | None:
        record = self.get_health_number(health_number)
        if record and record.status == HealthNumberStatus.ACTIVE:
            record.status = HealthNumberStatus.LOST
            self._audit(health_number, "lost", "active", "lost", reported_by)
        return record

    def reissue(self, health_number: str, citizen_ulid: str, issued_by: str) -> str | None:
        old = self.get_health_number(health_number)
        if not old:
            return None
        old.status = HealthNumberStatus.REPLACED
        old.merged_into_health_number = health_number

        new_number = self.generate_health_number(citizen_ulid, old.national_id_hash)
        new = self.get_health_number(new_number)
        if new:
            new.previous_health_number = health_number

        self._audit(
            health_number,
            "reissued",
            "active",
            "replaced",
            issued_by,
            f"Reissued as {new_number}",
        )
        self._audit(new_number, "issued", None, "active", issued_by, f"Replacement for {health_number}")
        return new_number

    def merge_identities(
        self,
        primary_hn: str,
        secondary_hn: str,
        reason: str,
        decision_by: str,
        historical_data: dict[str, Any] | None = None,
    ) -> MergedIdentityRecord:
        primary = self.get_health_number(primary_hn)
        secondary = self.get_health_number(secondary_hn)
        if not primary or not secondary:
            raise ValueError("Both health numbers must exist")

        secondary.status = HealthNumberStatus.MERGED
        secondary.merged_into_health_number = primary_hn

        merge = MergedIdentityRecord(
            primary_health_number=primary_hn,
            secondary_health_number=secondary_hn,
            primary_citizen_ulid=primary.citizen_ulid,
            secondary_citizen_ulid=secondary.citizen_ulid,
            action=IdentityMergeAction.MERGED,
            reason=reason,
            decision_by=decision_by,
            historical_data_json=str(historical_data) if historical_data else None,
        )
        self.db.add(merge)

        self._audit(secondary_hn, "merged", "active", "merged", decision_by, reason)
        return merge

    def split_identity(
        self,
        primary_hn: str,
        new_hn: str,
        reason: str,
        decision_by: str,
    ) -> MergedIdentityRecord:
        primary = self.get_health_number(primary_hn)
        if not primary:
            raise ValueError("Primary health number must exist")

        citizen_ulid = primary.citizen_ulid
        self.generate_health_number(citizen_ulid, primary.national_id_hash)
        new_number = self.get_health_number(new_hn)
        if not new_number:
            new_hn = self.generate_health_number(citizen_ulid, primary.national_id_hash)
            new_number = self.get_health_number(new_hn)

        split = MergedIdentityRecord(
            primary_health_number=primary_hn,
            secondary_health_number=new_hn,
            primary_citizen_ulid=citizen_ulid,
            secondary_citizen_ulid=citizen_ulid,
            action=IdentityMergeAction.SPLIT,
            reason=reason,
            decision_by=decision_by,
        )
        self.db.add(split)
        self._audit(primary_hn, "split", "active", "split", decision_by, f"Split into {new_hn}")
        return split

    def create_historical_link(
        self,
        primary_hn: str,
        secondary_hn: str,
        reason: str,
        decision_by: str,
    ) -> MergedIdentityRecord:
        return MergedIdentityRecord(
            primary_health_number=primary_hn,
            secondary_health_number=secondary_hn,
            primary_citizen_ulid="",
            secondary_citizen_ulid="",
            action=IdentityMergeAction.HISTORICAL_LINK,
            reason=reason,
            decision_by=decision_by,
            is_historical_link=True,
        )

    def record_card_event(
        self,
        health_number: str,
        citizen_ulid: str,
        card_type: HealthCardType,
        card_number: str,
        event: CardLifecycleEvent,
        previous_card_number: str | None = None,
        reason: str | None = None,
        issued_by: str | None = None,
    ) -> HealthCardLifecycle:
        card = HealthCardLifecycle(
            health_number=health_number,
            citizen_ulid=citizen_ulid,
            card_type=card_type,
            card_number=card_number,
            event=event,
            previous_card_number=previous_card_number,
            reason=reason,
            issued_by=issued_by,
        )
        self.db.add(card)
        return card

    def get_history(self, health_number: str) -> list[HealthNumberAudit]:
        return (
            self.db.query(HealthNumberAudit)
            .filter(HealthNumberAudit.health_number == health_number)
            .order_by(HealthNumberAudit.created_at.desc())
            .all()
        )

    def _audit(
        self,
        health_number: str,
        event: str,
        previous_status: str | None,
        new_status: str | None,
        changed_by: str | None,
        reason: str | None = None,
    ) -> None:
        audit = HealthNumberAudit(
            health_number=health_number,
            event=event,
            previous_status=previous_status,
            new_status=new_status,
            changed_by=changed_by,
            reason=reason,
        )
        self.db.add(audit)
