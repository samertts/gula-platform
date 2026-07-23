from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class RoleDef:
    role_id: str
    name_en: str
    name_ar: str
    description: str
    level: int
    scope: str
    parent_role_id: Optional[str] = None
    requires_mfa: bool = False
    is_delegatable: bool = True
    default_permissions: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "role_id": self.role_id,
            "name_en": self.name_en,
            "name_ar": self.name_ar,
            "description": self.description,
            "level": self.level,
            "scope": self.scope,
            "parent_role_id": self.parent_role_id,
            "requires_mfa": self.requires_mfa,
            "is_delegatable": self.is_delegatable,
            "default_permissions": self.default_permissions,
        }


@dataclass
class PermissionDef:
    permission_id: str
    name_en: str
    name_ar: str
    description: str
    domain: str
    resource: str
    action: str
    risk_level: str = "low"
    is_sensitive: bool = False
    requires_mfa: bool = False
    requires_justification: bool = False
    is_audited: bool = True
    default_roles: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "permission_id": self.permission_id,
            "name_en": self.name_en,
            "name_ar": self.name_ar,
            "description": self.description,
            "domain": self.domain,
            "resource": self.resource,
            "action": self.action,
            "risk_level": self.risk_level,
            "is_sensitive": self.is_sensitive,
            "requires_mfa": self.requires_mfa,
            "requires_justification": self.requires_justification,
            "is_audited": self.is_audited,
            "default_roles": self.default_roles,
        }


@dataclass
class OrganizationDef:
    org_id: str
    name_en: str
    name_ar: str
    org_type: str
    parent_org_id: Optional[str] = None
    governorate_id: Optional[str] = None
    directorate_id: Optional[str] = None
    is_active: bool = True

    def to_dict(self) -> dict:
        return {
            "org_id": self.org_id,
            "name_en": self.name_en,
            "name_ar": self.name_ar,
            "org_type": self.org_type,
            "parent_org_id": self.parent_org_id,
            "governorate_id": self.governorate_id,
            "directorate_id": self.directorate_id,
            "is_active": self.is_active,
        }


@dataclass
class FacilityDef:
    facility_id: str
    name_en: str
    name_ar: str
    facility_type: str
    organization_id: str
    is_active: bool = True

    def to_dict(self) -> dict:
        return {
            "facility_id": self.facility_id,
            "name_en": self.name_en,
            "name_ar": self.name_ar,
            "facility_type": self.facility_type,
            "organization_id": self.organization_id,
            "is_active": self.is_active,
        }


@dataclass
class AdminAccountDef:
    email: str
    name: str
    role: str
    password_env_var: str
    password_hash_env_var: str
    lab_name: str = "GULA Platform"
    is_active: bool = True

    def to_dict(self) -> dict:
        return {
            "email": self.email,
            "name": self.name,
            "role": self.role,
            "password_env_var": self.password_env_var,
            "password_hash_env_var": self.password_hash_env_var,
            "lab_name": self.lab_name,
            "is_active": self.is_active,
        }


MASTER_ADMIN_ROLE = "master_admin"
MINISTRY_ADMIN_ROLE = "ministry_admin"
ORGANIZATION_ADMIN_ROLE = "organization_admin"
DIRECTORATE_ADMIN_ROLE = "directorate_admin"
HOSPITAL_ADMIN_ROLE = "hospital_admin"
PHC_ADMIN_ROLE = "phc_admin"
LAB_MANAGER_ROLE = "lab_manager"
LAB_SUPERVISOR_ROLE = "lab_supervisor"
TECHNICIAN_ROLE = "technician"
PATHOLOGIST_ROLE = "pathologist"
DOCTOR_ROLE = "doctor"
NURSE_ROLE = "nurse"
RECEPTIONIST_ROLE = "receptionist"
CASHIER_ROLE = "cashier"
AUDITOR_ROLE = "auditor"
QUALITY_MANAGER_ROLE = "quality_manager"
SECURITY_OFFICER_ROLE = "security_officer"
API_CLIENT_ROLE = "api_client"
PATIENT_ROLE = "patient"

ALL_BOOTSTRAP_ROLES = [
    MASTER_ADMIN_ROLE,
    MINISTRY_ADMIN_ROLE,
    ORGANIZATION_ADMIN_ROLE,
    DIRECTORATE_ADMIN_ROLE,
    HOSPITAL_ADMIN_ROLE,
    PHC_ADMIN_ROLE,
    LAB_MANAGER_ROLE,
    LAB_SUPERVISOR_ROLE,
    TECHNICIAN_ROLE,
    PATHOLOGIST_ROLE,
    DOCTOR_ROLE,
    NURSE_ROLE,
    RECEPTIONIST_ROLE,
    CASHIER_ROLE,
    AUDITOR_ROLE,
    QUALITY_MANAGER_ROLE,
    SECURITY_OFFICER_ROLE,
    API_CLIENT_ROLE,
    PATIENT_ROLE,
]

PERMISSION_DOMAINS = [
    "identity",
    "patients",
    "orders",
    "samples",
    "results",
    "billing",
    "inventory",
    "facilities",
    "users",
    "organizations",
    "analytics",
    "ai",
    "audit",
    "administration",
    "fhir",
    "interoperability",
    "reporting",
    "notifications",
    "configuration",
    "security",
]

PLATFORM_LAB_NAME = "GULA Platform"
PLATFORM_ORG_NAME_EN = "GULA Platform Organization"
PLATFORM_ORG_NAME_AR = "منظمة منصة غولا"
PLATFORM_DIRECTORATE_NAME_EN = "GULA Platform Directorate"
PLATFORM_DIRECTORATE_NAME_AR = "مديرية منصة غولا"
PLATFORM_HOSPITAL_NAME_EN = "GULA Platform Hospital"
PLATFORM_HOSPITAL_NAME_AR = "مستشفى منصة غولا"

NATIONAL_ORG_NAME_EN = "Ministry of Health"
NATIONAL_ORG_NAME_AR = "وزارة الصحة"
NATIONAL_ORG_TYPE = "ministry"
