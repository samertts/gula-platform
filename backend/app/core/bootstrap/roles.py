from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.authorization import Role, RolePermission

from .models import RoleDef
from .permissions import define_permissions

logger = logging.getLogger("gula.bootstrap.roles")


def define_enterprise_roles() -> list[RoleDef]:
    return [
        RoleDef(
            role_id="master_admin",
            name_en="Master Administrator",
            name_ar="مدير عام",
            description="Platform super-administrator with unrestricted system access",
            level=100,
            scope="global",
        ),
        RoleDef(
            role_id="ministry_admin",
            name_en="Ministry Administrator",
            name_ar="مدير وزارة",
            description="Ministry-level administrator overseeing national health operations",
            level=90,
            scope="ministry",
        ),
        RoleDef(
            role_id="organization_admin",
            name_en="Organization Administrator",
            name_ar="مدير منظمة",
            description="Organization-level administrator managing subordinate entities",
            level=80,
            scope="organization",
        ),
        RoleDef(
            role_id="directorate_admin",
            name_en="Directorate Administrator",
            name_ar="مدير مديرية",
            description="Health directorate administrator managing facilities in a region",
            level=70,
            scope="directorate",
        ),
        RoleDef(
            role_id="auditor",
            name_en="Auditor",
            name_ar="مدقق",
            description="System auditor with read-only access to audit logs, reports, and configurations",
            level=70,
            scope="global",
            requires_mfa=True,
        ),
        RoleDef(
            role_id="security_officer",
            name_en="Security Officer",
            name_ar="ضابط أمان",
            description="Security officer managing security policies, incident response, and access control",
            level=70,
            scope="global",
            requires_mfa=True,
        ),
        RoleDef(
            role_id="hospital_admin",
            name_en="Hospital Administrator",
            name_ar="مدير مستشفى",
            description="Hospital-level administrator managing clinical and administrative operations",
            level=60,
            scope="hospital",
        ),
        RoleDef(
            role_id="phc_admin",
            name_en="PHC Administrator",
            name_ar="مدير مركز رعاية أولية",
            description="Primary Healthcare Center administrator",
            level=55,
            scope="phc",
        ),
        RoleDef(
            role_id="lab_manager",
            name_en="Lab Manager",
            name_ar="مدير مختبر",
            description="Laboratory manager with full lab operational control",
            level=50,
            scope="lab",
        ),
        RoleDef(
            role_id="quality_manager",
            name_en="Quality Manager",
            name_ar="مدير جودة",
            description="Quality control manager overseeing lab quality processes",
            level=45,
            scope="lab",
        ),
        RoleDef(
            role_id="lab_supervisor",
            name_en="Lab Supervisor",
            name_ar="مشرف مختبر",
            description="Laboratory supervisor overseeing daily lab operations",
            level=45,
            scope="lab",
        ),
        RoleDef(
            role_id="pathologist",
            name_en="Pathologist",
            name_ar="أخصائي علم الأمراض",
            description="Medical pathologist responsible for result verification and interpretation",
            level=40,
            scope="lab",
            requires_mfa=True,
        ),
        RoleDef(
            role_id="doctor",
            name_en="Doctor",
            name_ar="طبيب",
            description="Medical doctor with order placement and result review capabilities",
            level=35,
            scope="any",
        ),
        RoleDef(
            role_id="technician",
            name_en="Laboratory Technician",
            name_ar="فني مختبر",
            description="Lab technician performing sample analysis and result entry",
            level=30,
            scope="lab",
        ),
        RoleDef(
            role_id="nurse",
            name_en="Nurse",
            name_ar="ممرض",
            description="Nurse supporting sample collection and patient care",
            level=25,
            scope="facility",
        ),
        RoleDef(
            role_id="receptionist",
            name_en="Receptionist",
            name_ar="موظف استقبال",
            description="Front-desk receptionist managing patient intake and appointments",
            level=20,
            scope="facility",
        ),
        RoleDef(
            role_id="cashier",
            name_en="Cashier",
            name_ar="أمين صندوق",
            description="Cashier handling billing and payment processing",
            level=20,
            scope="facility",
        ),
        RoleDef(
            role_id="api_client",
            name_en="API Client",
            name_ar="عميل API",
            description="Machine-to-machine API client with scoped programmatic access",
            level=5,
            scope="api",
            is_delegatable=False,
        ),
        RoleDef(
            role_id="patient",
            name_en="Patient",
            name_ar="مريض",
            description="Patient with self-service access to own health records",
            level=10,
            scope="self",
        ),
    ]


def seed_roles(db: Session | None = None) -> int:
    if db is None:
        db = SessionLocal()
        own_session = True
    else:
        own_session = False

    created = 0
    try:
        roles = define_enterprise_roles()
        for rdef in roles:
            existing = db.query(Role).filter(Role.role_id == rdef.role_id).first()
            if existing:
                continue
            role = Role(
                role_id=rdef.role_id,
                name_en=rdef.name_en,
                name_ar=rdef.name_ar,
                description=rdef.description,
                level=str(rdef.level),
                parent_role_id=rdef.parent_role_id,
                is_delegatable=rdef.is_delegatable,
                requires_mfa=rdef.requires_mfa,
                is_active=True,
            )
            db.add(role)
            created += 1

        if created:
            db.commit()
            logger.info("Seeded %d roles", created)

        link_role_permissions(db)

    except Exception as exc:
        db.rollback()
        logger.error("Failed to seed roles: %s", exc)
        raise
    finally:
        if own_session:
            db.close()

    return created


def link_role_permissions(db: Session) -> None:
    from app.models.authorization import Permission as PermissionModel

    perms = define_permissions()
    linked = 0
    for pdef in perms:
        perm_row = (
            db.query(PermissionModel)
            .filter(
                PermissionModel.permission_id == pdef.permission_id,
            )
            .first()
        )
        if not perm_row:
            continue
        for role_id in pdef.default_roles:
            existing = (
                db.query(RolePermission)
                .filter(
                    RolePermission.role_id == role_id,
                    RolePermission.permission_id == pdef.permission_id,
                )
                .first()
            )
            if existing:
                continue
            rp = RolePermission(
                role_id=role_id,
                permission_id=pdef.permission_id,
            )
            db.add(rp)
            linked += 1

    if linked:
        db.commit()
        logger.info("Linked %d role-permission mappings", linked)
