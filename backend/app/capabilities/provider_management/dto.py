from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Provider_managementCreateRequest:
    provider_id: str
    provider_type: str
    license: str


@dataclass
class Provider_managementUpdateRequest:
    provider_id: str = None
    provider_type: str = None
    license: str = None


@dataclass
class Provider_managementResponse:
    provider_id: str
    provider_type: str
    license: str
