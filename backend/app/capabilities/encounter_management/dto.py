from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Encounter_managementCreateRequest:
    encounter_id: str
    encounter_type: str
    status: str


@dataclass
class Encounter_managementUpdateRequest:
    encounter_id: str = None
    encounter_type: str = None
    status: str = None


@dataclass
class Encounter_managementResponse:
    encounter_id: str
    encounter_type: str
    status: str
