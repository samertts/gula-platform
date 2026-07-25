from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.authorization import Permission

from .models import (
    API_CLIENT_ROLE,
    AUDITOR_ROLE,
    CASHIER_ROLE,
    DIRECTORATE_ADMIN_ROLE,
    DOCTOR_ROLE,
    HOSPITAL_ADMIN_ROLE,
    LAB_MANAGER_ROLE,
    LAB_SUPERVISOR_ROLE,
    MASTER_ADMIN_ROLE,
    MINISTRY_ADMIN_ROLE,
    NURSE_ROLE,
    ORGANIZATION_ADMIN_ROLE,
    PATHOLOGIST_ROLE,
    PATIENT_ROLE,
    PHC_ADMIN_ROLE,
    QUALITY_MANAGER_ROLE,
    RECEPTIONIST_ROLE,
    SECURITY_OFFICER_ROLE,
    TECHNICIAN_ROLE,
    PermissionDef,
)

logger = logging.getLogger("gula.bootstrap.permissions")

ALL_ROLES = [
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


def _perm(
    pid: str,
    name_en: str,
    name_ar: str,
    domain: str,
    resource: str,
    action: str,
    risk: str = "low",
    sensitive: bool = False,
    mfa: bool = False,
    justification: bool = False,
    audited: bool = True,
    roles: list[str] | None = None,
) -> PermissionDef:
    return PermissionDef(
        permission_id=pid,
        name_en=name_en,
        name_ar=name_ar,
        description=name_en,
        domain=domain,
        resource=resource,
        action=action,
        risk_level=risk,
        is_sensitive=sensitive,
        requires_mfa=mfa,
        requires_justification=justification,
        is_audited=audited,
        default_roles=roles or [],
    )


def define_permissions() -> list[PermissionDef]:
    MA = MASTER_ADMIN_ROLE
    MNA = MINISTRY_ADMIN_ROLE
    OA = ORGANIZATION_ADMIN_ROLE
    DA = DIRECTORATE_ADMIN_ROLE
    HA = HOSPITAL_ADMIN_ROLE
    PA = PHC_ADMIN_ROLE
    LM = LAB_MANAGER_ROLE
    LS = LAB_SUPERVISOR_ROLE
    TC = TECHNICIAN_ROLE
    PT = PATHOLOGIST_ROLE
    DR = DOCTOR_ROLE
    NR = NURSE_ROLE
    RC = RECEPTIONIST_ROLE
    CA = CASHIER_ROLE
    AU = AUDITOR_ROLE
    QM = QUALITY_MANAGER_ROLE
    SO = SECURITY_OFFICER_ROLE
    PG = PATIENT_ROLE

    return [
        # ── Identity domain ────────────────────────────────────────────────
        _perm("identity:read", "Read Identity", "قراءة الهوية", "identity", "identity", "read", roles=[MA, MNA, OA, DA, HA, PA, LM, LS, AU, SO]),
        _perm("identity:create", "Create Identity", "إنشاء هوية", "identity", "identity", "create", risk="high", sensitive=True, audited=True, roles=[MA, MNA, OA, DA, HA, PA, LM]),
        _perm("identity:update", "Update Identity", "تحديث الهوية", "identity", "identity", "update", risk="high", sensitive=True, audited=True, roles=[MA, MNA, OA, DA, HA, PA, LM]),
        _perm("identity:delete", "Delete Identity", "حذف الهوية", "identity", "identity", "delete", risk="critical", sensitive=True, mfa=True, audited=True, roles=[MA, MNA]),
        _perm("identity:verify", "Verify Identity", "التحقق من الهوية", "identity", "identity", "verify", risk="high", sensitive=True, roles=[MA, MNA, LM, LS, RC]),
        # ── Patients domain ────────────────────────────────────────────────
        _perm("patients:read", "Read Patients", "قراءة المرضى", "patients", "patient", "read", roles=[MA, MNA, OA, DA, HA, PA, LM, LS, TC, PT, DR, NR, RC, AU, QM]),
        _perm("patients:create", "Create Patients", "إنشاء مريض", "patients", "patient", "create", roles=[MA, LM, LS, RC, NR]),
        _perm("patients:update", "Update Patients", "تحديث المريض", "patients", "patient", "update", roles=[MA, LM, LS, DR, NR, RC]),
        _perm("patients:delete", "Delete Patients", "حذف المريض", "patients", "patient", "delete", risk="high", audited=True, roles=[MA, LM]),
        _perm("patients:merge", "Merge Patients", "دمج المرضى", "patients", "patient", "merge", risk="high", sensitive=True, mfa=True, audited=True, roles=[MA]),
        _perm("patients:export", "Export Patients", "تصدير المرضى", "patients", "patient", "export", risk="high", sensitive=True, audited=True, roles=[MA, MNA, AU]),
        # ── Orders domain ──────────────────────────────────────────────────
        _perm("orders:read", "Read Orders", "قراءة الطلبات", "orders", "order", "read", roles=[MA, MNA, OA, DA, HA, PA, LM, LS, TC, PT, DR, NR, RC, AU, QM]),
        _perm("orders:create", "Create Orders", "إنشاء طلب", "orders", "order", "create", roles=[MA, LM, LS, TC, DR, NR, RC]),
        _perm("orders:update", "Update Orders", "تحديث الطلب", "orders", "order", "update", roles=[MA, LM, LS, TC, DR]),
        _perm("orders:cancel", "Cancel Orders", "إلغاء الطلب", "orders", "order", "cancel", risk="medium", audited=True, roles=[MA, LM, LS, DR]),
        _perm("orders:delete", "Delete Orders", "حذف الطلب", "orders", "order", "delete", risk="high", audited=True, roles=[MA, LM]),
        _perm("orders:batch", "Batch Orders", "طلبات مجمعة", "orders", "order", "batch", roles=[MA, LM, LS, TC]),
        # ── Samples domain ─────────────────────────────────────────────────
        _perm("samples:read", "Read Samples", "قراءة العينات", "samples", "sample", "read", roles=[MA, LM, LS, TC, PT, DR, NR, QM]),
        _perm("samples:create", "Create Samples", "إنشاء عينة", "samples", "sample", "create", roles=[MA, LM, LS, TC, NR]),
        _perm("samples:update", "Update Samples", "تحديث العينة", "samples", "sample", "update", roles=[MA, LM, LS, TC]),
        _perm("samples:destroy", "Destroy Samples", "إتلاف العينة", "samples", "sample", "destroy", risk="high", audited=True, roles=[MA, LM, LS]),
        _perm("samples:transfer", "Transfer Samples", "نقل العينة", "samples", "sample", "transfer", risk="medium", audited=True, roles=[MA, LM, LS, TC]),
        # ── Results domain ─────────────────────────────────────────────────
        _perm("results:read", "Read Results", "قراءة النتائج", "results", "result", "read", roles=[MA, MNA, OA, DA, HA, PA, LM, LS, TC, PT, DR, NR, AU, QM, PG]),
        _perm("results:create", "Create Results", "إدخال نتيجة", "results", "result", "create", risk="high", audited=True, roles=[MA, LM, LS, TC, PT]),
        _perm("results:update", "Update Results", "تحديث النتيجة", "results", "result", "update", risk="high", audited=True, roles=[MA, LM, LS, TC, PT]),
        _perm("results:verify", "Verify Results", "التحقق من النتيجة", "results", "result", "verify", risk="high", sensitive=True, mfa=True, audited=True, roles=[MA, LM, PT]),
        _perm("results:delete", "Delete Results", "حذف النتيجة", "results", "result", "delete", risk="critical", sensitive=True, mfa=True, audited=True, roles=[MA]),
        _perm("results:release", "Release Results", "إصدار النتيجة", "results", "result", "release", risk="high", audited=True, roles=[MA, LM, PT, LS]),
        # ── Billing domain ─────────────────────────────────────────────────
        _perm("billing:read", "Read Billing", "قراءة الفواتير", "billing", "billing", "read", roles=[MA, LM, CA, AU]),
        _perm("billing:create", "Create Invoice", "إنشاء فاتورة", "billing", "invoice", "create", roles=[MA, LM, CA]),
        _perm("billing:update", "Update Invoice", "تحديث الفاتورة", "billing", "invoice", "update", roles=[MA, LM, CA]),
        _perm("billing:void", "Void Invoice", "إلغاء الفاتورة", "billing", "invoice", "void", risk="high", audited=True, roles=[MA, LM, CA]),
        _perm("billing:refund", "Process Refund", "معالجة استرداد", "billing", "invoice", "refund", risk="high", mfa=True, audited=True, roles=[MA, LM]),
        _perm("billing:read_reports", "Read Billing Reports", "تقارير الفواتير", "billing", "report", "read", roles=[MA, LM, AU, CA]),
        # ── Inventory domain ───────────────────────────────────────────────
        _perm("inventory:read", "Read Inventory", "قراءة المخزون", "inventory", "inventory", "read", roles=[MA, LM, LS, QM]),
        _perm("inventory:create", "Add Inventory", "إضافة مخزون", "inventory", "inventory", "create", roles=[MA, LM, LS]),
        _perm("inventory:update", "Update Inventory", "تحديث المخزون", "inventory", "inventory", "update", roles=[MA, LM, LS]),
        _perm("inventory:adjust", "Adjust Inventory", "تسوية المخزون", "inventory", "inventory", "adjust", risk="medium", audited=True, roles=[MA, LM, QM]),
        # ── Facilities domain ──────────────────────────────────────────────
        _perm("facilities:read", "Read Facilities", "قراءة المنشآت", "facilities", "facility", "read", roles=[MA, MNA, OA, DA, HA, PA, LM, AU]),
        _perm("facilities:create", "Create Facility", "إنشاء منشأة", "facilities", "facility", "create", roles=[MA, MNA, OA, DA]),
        _perm("facilities:update", "Update Facility", "تحديث المنشأة", "facilities", "facility", "update", roles=[MA, MNA, OA, DA, HA, PA]),
        _perm("facilities:deactivate", "Deactivate Facility", "إلغاء تنشيط المنشأة", "facilities", "facility", "deactivate", risk="high", audited=True, roles=[MA, MNA, OA]),
        # ── Users domain ───────────────────────────────────────────────────
        _perm("users:read", "Read Users", "قراءة المستخدمين", "users", "user", "read", roles=[MA, MNA, OA, DA, HA, PA, LM, LS, AU, SO]),
        _perm("users:create", "Create User", "إنشاء مستخدم", "users", "user", "create", roles=[MA, MNA, OA, DA, HA, PA, LM]),
        _perm("users:update", "Update User", "تحديث المستخدم", "users", "user", "update", roles=[MA, MNA, OA, DA, HA, PA, LM, LS]),
        _perm("users:deactivate", "Deactivate User", "إلغاء تنشيط المستخدم", "users", "user", "deactivate", risk="high", audited=True, roles=[MA, MNA, OA, DA, HA, PA, LM]),
        _perm("users:delete", "Delete User", "حذف المستخدم", "users", "user", "delete", risk="critical", sensitive=True, mfa=True, audited=True, roles=[MA, MNA]),
        _perm("users:change_role", "Change User Role", "تغيير دور المستخدم", "users", "user", "change_role", risk="high", audited=True, roles=[MA, MNA, OA, DA, HA, PA, LM]),
        # ── Organizations domain ───────────────────────────────────────────
        _perm("organizations:read", "Read Organizations", "قراءة المنظمات", "organizations", "organization", "read", roles=[MA, MNA, OA, DA, AU]),
        _perm("organizations:create", "Create Organization", "إنشاء منظمة", "organizations", "organization", "create", roles=[MA, MNA]),
        _perm("organizations:update", "Update Organization", "تحديث المنظمة", "organizations", "organization", "update", roles=[MA, MNA, OA]),
        _perm("organizations:deactivate", "Deactivate Organization", "إلغاء تنشيط المنظمة", "organizations", "organization", "deactivate", risk="high", audited=True, roles=[MA, MNA]),
        # ── Analytics domain ───────────────────────────────────────────────
        _perm("analytics:read", "Read Analytics", "قراءة التحليلات", "analytics", "analytics", "read", roles=[MA, MNA, OA, DA, HA, PA, LM, AU, QM]),
        _perm("analytics:create_report", "Create Report", "إنشاء تقرير", "analytics", "report", "create", roles=[MA, MNA, OA, DA, HA, PA, LM, AU]),
        _perm("analytics:export", "Export Analytics", "تصدير التحليلات", "analytics", "analytics", "export", roles=[MA, MNA, LM, AU]),
        # ── AI domain ──────────────────────────────────────────────────────
        _perm("ai:access", "Access AI", "الوصول للذكاء الاصطناعي", "ai", "ai", "access", risk="medium", roles=[MA, LM, PT, DR, QM]),
        _perm("ai:interpret", "AI Interpretation", "تفسير بالذكاء الاصطناعي", "ai", "interpretation", "execute", risk="medium", audited=True, roles=[MA, LM, PT, DR]),
        _perm("ai:manage_models", "Manage AI Models", "إدارة نماذج الذكاء الاصطناعي", "ai", "model", "manage", risk="high", roles=[MA]),
        _perm("ai:configure", "Configure AI", "تكوين الذكاء الاصطناعي", "ai", "ai", "configure", roles=[MA]),
        # ── Audit domain ───────────────────────────────────────────────────
        _perm("audit:read", "Read Audit Log", "قراءة سجل التدقيق", "audit", "audit_log", "read", roles=[MA, MNA, AU, SO]),
        _perm("audit:export", "Export Audit Log", "تصدير سجل التدقيق", "audit", "audit_log", "export", roles=[MA, AU]),
        _perm("audit:view_sensitive", "View Sensitive Audit", "عرض التدقيق الحساس", "audit", "audit_log", "view_sensitive", risk="high", sensitive=True, mfa=True, roles=[MA, AU]),
        _perm("audit:rotate_keys", "Rotate Audit Keys", "تدوير مفاتيح التدقيق", "audit", "audit_key", "rotate", risk="critical", sensitive=True, mfa=True, audited=True, roles=[MA]),
        # ── Administration domain ──────────────────────────────────────────
        _perm("administration:system_config", "System Configuration", "تكوين النظام", "administration", "system", "configure", risk="high", roles=[MA, SO]),
        _perm("administration:manage_tiers", "Manage Tiers", "إدارة الخطط", "administration", "subscription", "manage", risk="high", roles=[MA, MNA]),
        _perm("administration:view_health", "View System Health", "عرض صحة النظام", "administration", "health", "read", roles=[MA, MNA, OA, DA, LM, SO, AU]),
        _perm("administration:manage_backup", "Manage Backup", "إدارة النسخ الاحتياطي", "administration", "backup", "manage", risk="high", roles=[MA, SO]),
        # ── FHIR domain ────────────────────────────────────────────────────
        _perm("fhir:read", "Read FHIR Resources", "قراءة موارد FHIR", "fhir", "fhir", "read", roles=[MA, MNA, OA, DA, LM, DR, PT, AU]),
        _perm("fhir:write", "Write FHIR Resources", "كتابة موارد FHIR", "fhir", "fhir", "write", roles=[MA, LM, PT]),
        _perm("fhir:search", "Search FHIR", "بحث FHIR", "fhir", "fhir", "search", roles=[MA, MNA, OA, DA, LM, DR, PT, AU]),
        _perm("fhir:bulk_export", "Bulk FHIR Export", "تصدير FHIR بالجملة", "fhir", "fhir", "bulk_export", risk="high", sensitive=True, audited=True, roles=[MA, MNA]),
        # ── Interoperability domain ────────────────────────────────────────
        _perm("interoperability:read", "Read Integration Config", "قراءة تكامل", "interoperability", "integration", "read", roles=[MA, LM, SO]),
        _perm("interoperability:configure", "Configure Integration", "تكوين التكامل", "interoperability", "integration", "configure", risk="high", roles=[MA, SO]),
        _perm("interoperability:manage_devices", "Manage Devices", "إدارة الأجهزة", "interoperability", "device", "manage", roles=[MA, LM, LS]),
        # ── Reporting domain ───────────────────────────────────────────────
        _perm("reporting:read", "Read Reports", "قراءة التقارير", "reporting", "report", "read", roles=[MA, MNA, OA, DA, HA, PA, LM, AU, QM]),
        _perm("reporting:create", "Create Report", "إنشاء تقرير", "reporting", "report", "create", roles=[MA, MNA, OA, DA, LM, AU, QM]),
        _perm("reporting:schedule", "Schedule Report", "جدولة تقرير", "reporting", "report", "schedule", roles=[MA, MNA, LM, AU]),
        _perm("reporting:export_pdf", "Export PDF Report", "تصدير تقرير PDF", "reporting", "report", "export_pdf", roles=[MA, MNA, OA, DA, HA, PA, LM, AU]),
        # ── Notifications domain ───────────────────────────────────────────
        _perm("notifications:read", "Read Notifications", "قراءة الإشعارات", "notifications", "notification", "read", roles=[MA, LM, LS, DR, NR, RC, PT, QM]),
        _perm("notifications:send", "Send Notifications", "إرسال إشعار", "notifications", "notification", "send", roles=[MA, LM, DR, LS]),
        _perm("notifications:configure", "Configure Notifications", "تكوين الإشعارات", "notifications", "notification", "configure", roles=[MA, LM]),
        # ── Configuration domain ───────────────────────────────────────────
        _perm("configuration:read", "Read Configuration", "قراءة الإعدادات", "configuration", "config", "read", roles=[MA, LM, SO, AU]),
        _perm("configuration:update", "Update Configuration", "تحديث الإعدادات", "configuration", "config", "update", risk="high", roles=[MA, SO]),
        _perm("configuration:manage_features", "Manage Feature Flags", "إدارة ميزات النظام", "configuration", "feature_flag", "manage", risk="high", roles=[MA, MNA]),
        # ── Security domain ────────────────────────────────────────────────
        _perm("security:read_policy", "Read Security Policy", "قراءة سياسة الأمان", "security", "policy", "read", roles=[MA, SO, AU]),
        _perm("security:update_policy", "Update Security Policy", "تحديث سياسة الأمان", "security", "policy", "update", risk="critical", sensitive=True, mfa=True, audited=True, roles=[MA, SO]),
        _perm("security:manage_mfa", "Manage MFA", "إدارة المصادقة المتعددة", "security", "mfa", "manage", risk="high", sensitive=True, roles=[MA, LM, SO]),
        _perm("security:view_logs", "View Security Logs", "عرض سجلات الأمان", "security", "security_log", "read", roles=[MA, SO, AU]),
        _perm("security:manage_api_keys", "Manage API Keys", "إدارة مفاتيح API", "security", "api_key", "manage", risk="high", sensitive=True, mfa=True, audited=True, roles=[MA, SO]),
        _perm("security:break_glass", "Break Glass Access", "الوصول الطارئ", "security", "break_glass", "activate", risk="critical", sensitive=True, mfa=True, audited=True, roles=[MA, LM]),
        _perm("security:manage_rate_limits", "Manage Rate Limits", "إدارة حدود الطلبات", "security", "rate_limit", "manage", risk="medium", roles=[MA, SO]),
        _perm("security:incident_response", "Incident Response", "الاستجابة للحوادث", "security", "incident", "respond", risk="critical", sensitive=True, mfa=True, audited=True, roles=[MA, SO]),
    ]


def seed_permissions(db: Session | None = None) -> int:
    if db is None:
        db = SessionLocal()
        own_session = True
    else:
        own_session = False

    created = 0
    try:
        perms = define_permissions()
        for pdef in perms:
            existing = db.query(Permission).filter(
                Permission.permission_id == pdef.permission_id,
            ).first()
            if existing:
                continue
            perm = Permission(
                permission_id=pdef.permission_id,
                name_en=pdef.name_en,
                name_ar=pdef.name_ar,
                description=pdef.description,
                domain=pdef.domain,
                resource=pdef.resource,
                action=pdef.action,
                risk_level=pdef.risk_level,
                is_sensitive=pdef.is_sensitive,
                requires_mfa=pdef.requires_mfa,
                requires_justification=pdef.requires_justification,
                is_audited=pdef.is_audited,
            )
            db.add(perm)
            created += 1

        if created:
            db.commit()
            logger.info("Seeded %d permissions", created)
        else:
            logger.info("All permissions already exist")

    except Exception as exc:
        db.rollback()
        logger.error("Failed to seed permissions: %s", exc)
        raise
    finally:
        if own_session:
            db.close()

    return created
