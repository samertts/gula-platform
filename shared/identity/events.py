from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional


@dataclass
class IdentityEvent:
    event_type: str = ""
    entity_id: str = ""
    actor_id: str = ""
    lab_id: int = 0
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    payload: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "event_type": self.event_type,
            "entity_id": self.entity_id,
            "actor_id": self.actor_id,
            "lab_id": self.lab_id,
            "timestamp": self.timestamp.isoformat(),
            "payload": self.payload,
        }


@dataclass
class PatientCreated(IdentityEvent):
    event_type: str = "patient.created"


@dataclass
class IdentityVerified(IdentityEvent):
    event_type: str = "identity.verified"


@dataclass
class PatientDuplicatesMerged(IdentityEvent):
    event_type: str = "patient.duplicates_merged"


@dataclass
class IdentityClaimCreated(IdentityEvent):
    event_type: str = "identity.claim_created"


@dataclass
class IdentityClaimMerged(IdentityEvent):
    event_type: str = "identity.claim_merged"
