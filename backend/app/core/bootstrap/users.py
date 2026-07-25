from __future__ import annotations

import logging
import os

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.lab import Lab
from app.models.lab_user import LabUser
from app.security.auth import hash_password

from .config import load_bootstrap_config
from .models import MASTER_ADMIN_ROLE, PLATFORM_LAB_NAME, AdminAccountDef

logger = logging.getLogger("gula.bootstrap.users")


ADMIN_ACCOUNTS: list[AdminAccountDef] = [
    AdminAccountDef(
        email="MINISTRY_ADMIN_EMAIL",
        name="Ministry Admin",
        role="ministry_admin",
        password_env_var="MINISTRY_ADMIN_PASSWORD",
        password_hash_env_var="MINISTRY_ADMIN_PASSWORD_HASH",
    ),
    AdminAccountDef(
        email="ORGANIZATION_ADMIN_EMAIL",
        name="Organization Admin",
        role="organization_admin",
        password_env_var="ORGANIZATION_ADMIN_PASSWORD",
        password_hash_env_var="ORGANIZATION_ADMIN_PASSWORD_HASH",
    ),
    AdminAccountDef(
        email="DIRECTORATE_ADMIN_EMAIL",
        name="Directorate Admin",
        role="directorate_admin",
        password_env_var="DIRECTORATE_ADMIN_PASSWORD",
        password_hash_env_var="DIRECTORATE_ADMIN_PASSWORD_HASH",
    ),
    AdminAccountDef(
        email="LAB_MANAGER_EMAIL",
        name="Lab Manager",
        role="lab_manager",
        password_env_var="LAB_MANAGER_PASSWORD",
        password_hash_env_var="LAB_MANAGER_PASSWORD_HASH",
    ),
    AdminAccountDef(
        email="AUDITOR_EMAIL",
        name="System Auditor",
        role="auditor",
        password_env_var="AUDITOR_PASSWORD",
        password_hash_env_var="AUDITOR_PASSWORD_HASH",
    ),
    AdminAccountDef(
        email="SECURITY_OFFICER_EMAIL",
        name="Security Officer",
        role="security_officer",
        password_env_var="SECURITY_OFFICER_PASSWORD",
        password_hash_env_var="SECURITY_OFFICER_PASSWORD_HASH",
    ),
]


def _resolve_account(acct: AdminAccountDef) -> dict | None:
    email_val = os.getenv(acct.email, "")
    if not email_val:
        email_val = acct.email.lower().replace("_", "-") + "@gula-platform.org"
        logger.debug(
            "Using default email for %s: %s",
            acct.role,
            email_val,
        )

    name_val = os.getenv(f"{acct.role.upper()}_NAME", acct.name)

    password_hash = os.getenv(acct.password_hash_env_var, "").strip()
    if password_hash:
        return {
            "email": email_val,
            "name": name_val,
            "password_hash": password_hash,
        }

    plaintext = os.getenv(acct.password_env_var, "").strip()
    if plaintext:
        return {
            "email": email_val,
            "name": name_val,
            "password_hash": hash_password(plaintext),
        }

    logger.info(
        "Account %s (%s) skipped — no password configured",
        acct.role,
        email_val,
    )
    return None


def seed_national_admin_accounts(db: Session | None = None) -> int:
    if db is None:
        db = SessionLocal()
        own_session = True
    else:
        own_session = False

    created = 0
    try:
        load_bootstrap_config()
        platform_lab = db.query(Lab).filter(Lab.name == PLATFORM_LAB_NAME).first()
        if not platform_lab:
            logger.warning("Platform lab not found — creating it")
            platform_lab = Lab(name=PLATFORM_LAB_NAME, city="Platform", is_active=True)
            db.add(platform_lab)
            db.flush()

        master_admin = (
            db.query(LabUser)
            .filter(
                LabUser.role == MASTER_ADMIN_ROLE,
                LabUser.lab_id == platform_lab.id,
            )
            .first()
        )

        for acct in ADMIN_ACCOUNTS:
            resolved = _resolve_account(acct)
            if not resolved:
                continue

            existing = (
                db.query(LabUser)
                .filter(
                    LabUser.email == resolved["email"],
                )
                .first()
            )
            if existing:
                logger.debug(
                    "Account %s (%s) already exists — skipping",
                    acct.role,
                    resolved["email"],
                )
                continue

            user = LabUser(
                lab_id=platform_lab.id,
                name=resolved["name"],
                email=resolved["email"],
                password_hash=resolved["password_hash"],
                role=acct.role,
                is_active=acct.is_active,
                created_by=master_admin.id if master_admin else None,
            )
            db.add(user)
            created += 1
            logger.info(
                "Created %s account (%s)",
                acct.role,
                resolved["email"],
            )

        if created:
            db.commit()
            logger.info("Seeded %d national admin accounts", created)
    except Exception as exc:
        db.rollback()
        logger.error("Failed to seed national admin accounts: %s", exc)
        raise
    finally:
        if own_session:
            db.close()

    return created
