from __future__ import annotations

import os
from enum import StrEnum


class ClinicalGatewayMode(StrEnum):
    off = "OFF"
    internal = "INTERNAL"
    pilot = "PILOT"
    on = "ON"


class ClinicalGatewayRollout:
    """Server-controlled rollout gate; browser state cannot enable it."""

    def __init__(self) -> None:
        raw_mode = os.getenv("GULA_CLINICAL_GATEWAY_MODE", ClinicalGatewayMode.off.value).upper()
        self.mode = ClinicalGatewayMode(raw_mode) if raw_mode in ClinicalGatewayMode else ClinicalGatewayMode.off
        self.account_allowlist = self._csv("GULA_CLINICAL_GATEWAY_ACCOUNT_ALLOWLIST")
        self.organization_allowlist = self._csv("GULA_CLINICAL_GATEWAY_ORGANIZATION_ALLOWLIST")

    @staticmethod
    def _csv(name: str) -> frozenset[str]:
        return frozenset(item.strip() for item in os.getenv(name, "").split(",") if item.strip())

    def allows(self, *, account_id: str, organization_id: str) -> bool:
        if self.mode is ClinicalGatewayMode.off:
            return False
        if self.mode is ClinicalGatewayMode.on:
            return True
        if self.account_allowlist and account_id in self.account_allowlist:
            return True
        return bool(self.organization_allowlist and organization_id in self.organization_allowlist)
