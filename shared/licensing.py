from __future__ import annotations

import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Any
from uuid import uuid4

from backend.app._compat import UTC

logger = logging.getLogger("gula.licensing")


class Tier(Enum):
    FREE = "free"
    BASIC = "basic"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"

    def __lt__(self, other: Tier) -> bool:
        order = [Tier.FREE, Tier.BASIC, Tier.PROFESSIONAL, Tier.ENTERPRISE]
        return order.index(self) < order.index(other)


class License:
    def __init__(
        self,
        license_id: str | None = None,
        lab_id: int = 0,
        tier: Tier = Tier.FREE,
        expires_at: datetime | None = None,
        features: list[str] | None = None,
    ) -> None:
        self.id = license_id or str(uuid4())
        self.lab_id = lab_id
        self.tier = tier
        self.expires_at = expires_at or (datetime.now(UTC) + timedelta(days=365))
        self.features = features or []
        self.active = True
        self.created_at = datetime.now(UTC)

    @property
    def expired(self) -> bool:
        return datetime.now(UTC) > self.expires_at

    def can_access(self, feature: str) -> bool:
        return bool(self.active and not self.expired and (feature in self.features))

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id, "lab_id": self.lab_id, "tier": self.tier.value,
            "expires_at": self.expires_at.isoformat(), "features": self.features,
            "active": self.active, "created_at": self.created_at.isoformat(),
        }


class LicenseManager:
    def __init__(self) -> None:
        self._licenses: dict[str, License] = {}

    def register(self, license: License) -> None:
        self._licenses[license.id] = license
        logger.info("License %s registered (lab=%d, tier=%s)", license.id, license.lab_id, license.tier.value)

    def get(self, license_id: str) -> License | None:
        return self._licenses.get(license_id)

    def get_by_lab(self, lab_id: int) -> License | None:
        for lic in self._licenses.values():
            if lic.lab_id == lab_id:
                return lic
        return None

    def revoke(self, license_id: str) -> bool:
        lic = self._licenses.get(license_id)
        if not lic:
            return False
        lic.active = False
        return True

    def validate(self, lab_id: int, feature: str) -> bool:
        lic = self.get_by_lab(lab_id)
        return lic.can_access(feature) if lic else False


manager = LicenseManager()

__all__ = ["License", "LicenseManager", "Tier", "manager"]
