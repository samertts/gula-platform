from app.national.security.rbac import NationalPermission

PERMISSION_DEFINITIONS = {
    NationalPermission.CITIZEN_CREATE: "Create new citizen records",
    NationalPermission.CITIZEN_READ: "View citizen records",
    NationalPermission.CITIZEN_UPDATE: "Update citizen records",
    NationalPermission.CITIZEN_DELETE: "Delete citizen records",
    NationalPermission.CITIZEN_MERGE: "Merge citizen identities",
    NationalPermission.PATIENT_CREATE: "Create patient records",
    NationalPermission.PATIENT_READ: "View patient records",
    NationalPermission.PATIENT_UPDATE: "Update patient records",
    NationalPermission.PATIENT_DELETE: "Delete patient records",
    NationalPermission.ENCOUNTER_CREATE: "Create encounters",
    NationalPermission.ENCOUNTER_READ: "View encounters",
    NationalPermission.ENCOUNTER_UPDATE: "Update encounters",
    NationalPermission.ENCOUNTER_DELETE: "Delete encounters",
    NationalPermission.REFERRAL_CREATE: "Create referrals",
    NationalPermission.REFERRAL_READ: "View referrals",
    NationalPermission.REFERRAL_UPDATE: "Update referrals",
    NationalPermission.REFERRAL_DELETE: "Delete referrals",
    NationalPermission.BREAK_GLASS: "Break glass emergency access",
    NationalPermission.SENSITIVE_ACCESS: "Access sensitive records",
    NationalPermission.VIP_ACCESS: "Access VIP records",
    NationalPermission.MINOR_ACCESS: "Access minor records",
    NationalPermission.EMERGENCY_ACCESS: "Emergency access",
}

__all__ = ["PERMISSION_DEFINITIONS"]
