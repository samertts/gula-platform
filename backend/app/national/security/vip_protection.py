from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from app._compat import UTC


@dataclass
class VIPAccessAttempt:
    citizen_id: str = ""
    user_id: str = ""
    user_role: str = ""
    access_type: str = ""
    granted: bool = False
    reason: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))


class VIPProtectionService:
    def __init__(self) -> None:
        self._attempts: list[VIPAccessAttempt] = []

    def check_access(self, citizen_id: str, user_id: str, user_role: str, access_type: str) -> bool:
        allowed_roles = {"system_admin", "national_admin", "vip_attending_physician"}
        granted = user_role in allowed_roles
        attempt = VIPAccessAttempt(
            citizen_id=citizen_id,
            user_id=user_id,
            user_role=user_role,
            access_type=access_type,
            granted=granted,
            reason="Authorized" if granted else "VIP protection: role not authorized",
        )
        self._attempts.append(attempt)
        return granted

    def get_access_log(self, citizen_id: str | None = None) -> list[VIPAccessAttempt]:
        if citizen_id:
            return [a for a in self._attempts if a.citizen_id == citizen_id]
        return self._attempts
