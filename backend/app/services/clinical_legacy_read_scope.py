from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ClinicalLegacyReadScope:
    """Server-derived scope required by canonical clinical read adapters."""

    legacy_lab_id: int
    legacy_lab_user_id: int
    operational_facility_id: int
    operational_organization_id: int
    tenant_id: int
    niam_organization_id: str
    niam_facility_id: str
    niam_workspace_id: str
    scope_mapping_version: int
