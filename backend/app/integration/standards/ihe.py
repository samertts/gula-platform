from __future__ import annotations

import logging
from dataclasses import dataclass, field

logger = logging.getLogger("gula.integration.standards.ihe")


@dataclass
class IHEProfile:
    name: str = ""
    version: str = ""
    integration_pattern: str = ""
    actors: list[str] = field(default_factory=list)
    transactions: list[str] = field(default_factory=list)


class IHEService:
    def __init__(self):
        self._profiles: dict[str, IHEProfile] = {}
        self._supported_profiles: dict[str, list[str]] = {
            "PIX": ["Patient Identity Cross-reference", "PDQ", "Patient Demographics Query"],
            "XDS": [
                "Cross-Enterprise Document Sharing",
                "Register Document Set",
                "Retrieve Document Set",
            ],
            "XCA": ["Cross-Community Access", "Cross-Community Query", "Cross-Community Retrieve"],
            "ATNA": [
                "Audit Trail and Node Authentication",
                "Record Audit Event",
                "Query Audit Event",
            ],
            "CT": ["Consistent Time", "Time Synchronization"],
            "SWF": [
                "Scheduled Workflow",
                "Order Placed",
                "Order Filled",
                "Procedure Scheduled",
                "Procedure Performed",
            ],
        }

    def get_profile(self, profile_id: str) -> IHEProfile | None:
        if profile_id in self._profiles:
            return self._profiles[profile_id]
        if profile_id in self._supported_profiles:
            info = self._supported_profiles[profile_id]
            profile = IHEProfile(
                name=profile_id,
                version="1.0",
                integration_pattern=info[0],
                actors=["Order Placer", "Order Filler", "DSS/Order Manager"],
                transactions=info[1:],
            )
            self._profiles[profile_id] = profile
            return profile
        return None

    def register_profile(self, profile: IHEProfile) -> None:
        self._profiles[profile.name] = profile
        logger.info("IHE profile registered: %s", profile.name)

    def list_profiles(self) -> list[str]:
        return list(self._supported_profiles.keys()) + [
            p.name for p in self._profiles.values() if p.name not in self._supported_profiles
        ]

    def validate_transaction(self, profile_id: str, transaction: str) -> bool:
        profile = self.get_profile(profile_id)
        if not profile:
            return False
        return transaction in profile.transactions

    def supports_profile(self, profile_id: str) -> bool:
        return profile_id in self._supported_profiles or profile_id in self._profiles
