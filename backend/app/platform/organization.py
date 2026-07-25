"""Standardized organization/facility/department module."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from . import PlatformRegistry

logger = logging.getLogger("gula.platform.organization")


@dataclass
class Organization:
    id: int = 0
    name: str = ""
    name_ar: str | None = None
    org_type: str = ""
    license_number: str | None = None
    phone: str | None = None
    email: str | None = None
    is_active: bool = True


@dataclass
class Facility:
    id: int = 0
    organization_id: int = 0
    name: str = ""
    name_ar: str | None = None
    facility_type: str = ""
    is_active: bool = True


@dataclass
class Department:
    id: int = 0
    facility_id: int = 0
    name: str = ""
    name_ar: str | None = None
    is_active: bool = True


class OrganizationService:
    def __init__(self, db) -> None:
        self._db = db

    def get(self, org_id: int) -> Organization | None:
        from ..models.organization import Organization as OrgModel

        org = self._db.query(OrgModel).filter(OrgModel.id == org_id).first()
        if org is None:
            return None
        return Organization(
            id=org.id,
            name=org.name,
            name_ar=org.name_ar,
            org_type=org.org_type,
            license_number=org.license_number,
            phone=org.phone,
            email=org.email,
            is_active=org.is_active,
        )

    def list(self, skip: int = 0, limit: int = 100) -> list[Organization]:
        from ..models.organization import Organization as OrgModel

        orgs = self._db.query(OrgModel).offset(skip).limit(limit).all()
        return [
            Organization(
                id=o.id, name=o.name, name_ar=o.name_ar, org_type=o.org_type, is_active=o.is_active
            )
            for o in orgs
        ]


class FacilityService:
    def __init__(self, db) -> None:
        self._db = db

    def get(self, facility_id: int) -> Facility | None:
        from ..models.organization import Facility as FacModel

        f = self._db.query(FacModel).filter(FacModel.id == facility_id).first()
        if f is None:
            return None
        return Facility(
            id=f.id,
            organization_id=f.organization_id,
            name=f.name,
            name_ar=f.name_ar,
            facility_type=f.facility_type,
            is_active=f.is_active,
        )

    def list_by_organization(self, org_id: int) -> list[Facility]:
        from ..models.organization import Facility as FacModel

        facilities = self._db.query(FacModel).filter(FacModel.organization_id == org_id).all()
        return [
            Facility(
                id=f.id,
                organization_id=f.organization_id,
                name=f.name,
                name_ar=f.name_ar,
                facility_type=f.facility_type,
                is_active=f.is_active,
            )
            for f in facilities
        ]


class DepartmentService:
    def __init__(self, db) -> None:
        self._db = db

    def list_by_facility(self, facility_id: int) -> list[Department]:
        from ..models.organization import Facility as FacModel

        facility = self._db.query(FacModel).filter(FacModel.id == facility_id).first()
        if facility is None:
            return []
        return [
            Department(
                id=0,
                facility_id=facility_id,
                name=facility.name,
                name_ar=facility.name_ar,
                is_active=facility.is_active,
            )
        ]


PlatformRegistry.register(
    "organization",
    OrganizationService,
    capabilities=[
        {"name": "organization_service", "description": "Organization CRUD and query operations"},
        {"name": "facility_service", "description": "Facility management per organization"},
        {"name": "department_service", "description": "Department management per facility"},
    ],
)
