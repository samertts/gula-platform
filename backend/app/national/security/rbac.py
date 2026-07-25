from __future__ import annotations

from enum import Enum


class NationalRole(Enum):
    SYSTEM_ADMIN = "system_admin"
    NATIONAL_ADMIN = "national_admin"
    DIRECTORATE_ADMIN = "directorate_admin"
    FACILITY_ADMIN = "facility_admin"
    DOCTOR = "doctor"
    NURSE = "nurse"
    TECHNICIAN = "technician"
    RECEPTIONIST = "receptionist"
    PHARMACIST = "pharmacist"
    CITIZEN = "citizen"
    GUARDIAN = "guardian"
    AUDITOR = "auditor"
    EMERGENCY_OFFICER = "emergency_officer"
    RESEARCHER = "researcher"
    MINISTRY_OFFICIAL = "ministry_official"
    INSURANCE_OFFICIAL = "insurance_official"


class NationalPermission(Enum):
    CITIZEN_CREATE = "citizen:create"
    CITIZEN_READ = "citizen:read"
    CITIZEN_UPDATE = "citizen:update"
    CITIZEN_DELETE = "citizen:delete"
    CITIZEN_MERGE = "citizen:merge"
    PATIENT_CREATE = "patient:create"
    PATIENT_READ = "patient:read"
    PATIENT_UPDATE = "patient:update"
    PATIENT_DELETE = "patient:delete"
    ENCOUNTER_CREATE = "encounter:create"
    ENCOUNTER_READ = "encounter:read"
    ENCOUNTER_UPDATE = "encounter:update"
    ENCOUNTER_DELETE = "encounter:delete"
    REFERRAL_CREATE = "referral:create"
    REFERRAL_READ = "referral:read"
    REFERRAL_UPDATE = "referral:update"
    REFERRAL_DELETE = "referral:delete"
    CONSENT_CREATE = "consent:create"
    CONSENT_READ = "consent:read"
    CONSENT_REVOKE = "consent:revoke"
    FAMILY_CREATE = "family:create"
    FAMILY_READ = "family:read"
    FAMILY_UPDATE = "family:update"
    HEALTH_CARD_CREATE = "health_card:create"
    HEALTH_CARD_READ = "health_card:read"
    HEALTH_CARD_UPDATE = "health_card:update"
    DEATH_RECORD_CREATE = "death_record:create"
    DEATH_RECORD_READ = "death_record:read"
    INSURANCE_READ = "insurance:read"
    COVERAGE_READ = "coverage:read"
    BREAK_GLASS = "break_glass"
    AUDIT_READ = "audit:read"
    SENSITIVE_ACCESS = "sensitive:access"
    VIP_ACCESS = "vip:access"
    MINOR_ACCESS = "minor:access"
    EMERGENCY_ACCESS = "emergency:access"
    REPORT_READ = "report:read"
    REPORT_GENERATE = "report:generate"
    ADMIN_ACCESS = "admin:access"


ROLE_PERMISSIONS: dict[NationalRole, set[NationalPermission]] = {
    NationalRole.SYSTEM_ADMIN: set(NationalPermission),
    NationalRole.NATIONAL_ADMIN: {
        NationalPermission.CITIZEN_CREATE,
        NationalPermission.CITIZEN_READ,
        NationalPermission.CITIZEN_UPDATE,
        NationalPermission.CITIZEN_MERGE,
        NationalPermission.FAMILY_CREATE,
        NationalPermission.FAMILY_READ,
        NationalPermission.FAMILY_UPDATE,
        NationalPermission.DEATH_RECORD_CREATE,
        NationalPermission.DEATH_RECORD_READ,
        NationalPermission.HEALTH_CARD_CREATE,
        NationalPermission.HEALTH_CARD_READ,
        NationalPermission.HEALTH_CARD_UPDATE,
        NationalPermission.AUDIT_READ,
        NationalPermission.SENSITIVE_ACCESS,
        NationalPermission.VIP_ACCESS,
        NationalPermission.ADMIN_ACCESS,
        NationalPermission.REPORT_READ,
        NationalPermission.REPORT_GENERATE,
    },
    NationalRole.DIRECTORATE_ADMIN: {
        NationalPermission.CITIZEN_READ,
        NationalPermission.CITIZEN_UPDATE,
        NationalPermission.PATIENT_CREATE,
        NationalPermission.PATIENT_READ,
        NationalPermission.PATIENT_UPDATE,
        NationalPermission.ENCOUNTER_CREATE,
        NationalPermission.ENCOUNTER_READ,
        NationalPermission.ENCOUNTER_UPDATE,
        NationalPermission.REFERRAL_CREATE,
        NationalPermission.REFERRAL_READ,
        NationalPermission.REFERRAL_UPDATE,
        NationalPermission.FAMILY_READ,
        NationalPermission.REPORT_READ,
    },
    NationalRole.FACILITY_ADMIN: {
        NationalPermission.PATIENT_CREATE,
        NationalPermission.PATIENT_READ,
        NationalPermission.PATIENT_UPDATE,
        NationalPermission.ENCOUNTER_CREATE,
        NationalPermission.ENCOUNTER_READ,
        NationalPermission.ENCOUNTER_UPDATE,
        NationalPermission.REFERRAL_CREATE,
        NationalPermission.REFERRAL_READ,
        NationalPermission.CONSENT_CREATE,
        NationalPermission.CONSENT_READ,
        NationalPermission.CONSENT_REVOKE,
        NationalPermission.FAMILY_READ,
        NationalPermission.REPORT_READ,
    },
    NationalRole.DOCTOR: {
        NationalPermission.CITIZEN_READ,
        NationalPermission.PATIENT_READ,
        NationalPermission.PATIENT_UPDATE,
        NationalPermission.ENCOUNTER_CREATE,
        NationalPermission.ENCOUNTER_READ,
        NationalPermission.ENCOUNTER_UPDATE,
        NationalPermission.REFERRAL_CREATE,
        NationalPermission.REFERRAL_READ,
        NationalPermission.CONSENT_READ,
        NationalPermission.INSURANCE_READ,
        NationalPermission.COVERAGE_READ,
    },
    NationalRole.NURSE: {
        NationalPermission.PATIENT_READ,
        NationalPermission.PATIENT_UPDATE,
        NationalPermission.ENCOUNTER_READ,
        NationalPermission.ENCOUNTER_UPDATE,
    },
    NationalRole.TECHNICIAN: {
        NationalPermission.PATIENT_READ,
        NationalPermission.ENCOUNTER_READ,
    },
    NationalRole.RECEPTIONIST: {
        NationalPermission.PATIENT_CREATE,
        NationalPermission.PATIENT_READ,
        NationalPermission.ENCOUNTER_CREATE,
        NationalPermission.ENCOUNTER_READ,
    },
    NationalRole.CITIZEN: {
        NationalPermission.CITIZEN_READ,
        NationalPermission.PATIENT_READ,
        NationalPermission.ENCOUNTER_READ,
        NationalPermission.CONSENT_READ,
        NationalPermission.HEALTH_CARD_READ,
    },
    NationalRole.GUARDIAN: {
        NationalPermission.CITIZEN_READ,
        NationalPermission.PATIENT_READ,
        NationalPermission.MINOR_ACCESS,
    },
    NationalRole.AUDITOR: {
        NationalPermission.AUDIT_READ,
        NationalPermission.REPORT_READ,
    },
    NationalRole.EMERGENCY_OFFICER: {
        NationalPermission.CITIZEN_READ,
        NationalPermission.PATIENT_READ,
        NationalPermission.EMERGENCY_ACCESS,
        NationalPermission.BREAK_GLASS,
    },
    NationalRole.RESEARCHER: {
        NationalPermission.CITIZEN_READ,
        NationalPermission.REPORT_READ,
    },
    NationalRole.MINISTRY_OFFICIAL: {
        NationalPermission.CITIZEN_READ,
        NationalPermission.REPORT_READ,
        NationalPermission.REPORT_GENERATE,
        NationalPermission.SENSITIVE_ACCESS,
    },
    NationalRole.INSURANCE_OFFICIAL: {
        NationalPermission.CITIZEN_READ,
        NationalPermission.INSURANCE_READ,
        NationalPermission.COVERAGE_READ,
    },
    NationalRole.PHARMACIST: {
        NationalPermission.PATIENT_READ,
        NationalPermission.CITIZEN_READ,
        NationalPermission.COVERAGE_READ,
        NationalPermission.INSURANCE_READ,
    },
}


class RBACEngine:
    def has_permission(self, role: NationalRole, permission: NationalPermission) -> bool:
        return permission in ROLE_PERMISSIONS.get(role, set())

    def has_any_permission(self, role: NationalRole, permissions: list[NationalPermission]) -> bool:
        return any(self.has_permission(role, p) for p in permissions)

    def has_all_permissions(
        self, role: NationalRole, permissions: list[NationalPermission],
    ) -> bool:
        return all(self.has_permission(role, p) for p in permissions)

    def get_permissions(self, role: NationalRole) -> set[NationalPermission]:
        return ROLE_PERMISSIONS.get(role, set())
