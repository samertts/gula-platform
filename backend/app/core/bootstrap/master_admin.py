from __future__ import annotations

import hashlib
import hmac as _hmac
import logging
import os

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.lab import Lab
from app.models.lab_user import LabUser
from app.security.auth import hash_password

from .config import load_bootstrap_config
from .models import PLATFORM_LAB_NAME

logger = logging.getLogger("gula.bootstrap.master_admin")


def hash_nid(nid: str) -> str:
    from app.config import NID_HMAC_KEY
    key = NID_HMAC_KEY.encode()
    return _hmac.new(key, nid.strip().encode(), hashlib.sha256).hexdigest()


def ensure_master_admin() -> None:
    db = SessionLocal()
    try:
        _ensure_master_admin(db)
        db.commit()
    except Exception as exc:
        db.rollback()
        logger.error("Bootstrap: master_admin failed — %s", exc)
    finally:
        db.close()


def _ensure_master_admin(db: Session) -> LabUser | None:
    existing = db.query(LabUser).filter(LabUser.role == "master_admin").first()
    if existing:
        nid_raw = os.getenv("MASTER_ADMIN_NID", "").strip()
        if nid_raw and not existing.national_id_hash:
            nid_hash = hash_nid(nid_raw)
            conflict = (
                db.query(LabUser)
                .filter(LabUser.national_id_hash == nid_hash, LabUser.id != existing.id)
                .first()
            )
            if conflict:
                logger.error("MASTER_ADMIN_NID hash already belongs to user %d", conflict.id)
            else:
                existing.national_id_hash = nid_hash
                logger.info("National ID linked to master_admin (id=%d)", existing.id)
        return existing

    cfg = load_bootstrap_config()
    email = cfg.admin_email
    name = cfg.admin_name

    password_hash = cfg.admin_password_hash.strip() or None
    if not password_hash:
        plaintext = cfg.admin_password.strip() or None
        if not plaintext:
            logger.error(
                "Bootstrap SKIPPED: GULA_ADMIN_PASSWORD not set. Set it in .env and restart."
            )
            return None
        password_hash = hash_password(plaintext)

    platform_lab = db.query(Lab).filter(Lab.name == PLATFORM_LAB_NAME).first()
    if not platform_lab:
        platform_lab = Lab(name=PLATFORM_LAB_NAME, city="Platform", is_active=True)
        db.add(platform_lab)
        db.flush()

    user = LabUser(
        lab_id=platform_lab.id,
        name=name,
        email=email,
        password_hash=password_hash,
        role="master_admin",
        is_active=True,
    )
    db.add(user)
    db.flush()

    nid_raw = cfg.master_admin_nid.strip()
    if nid_raw:
        nid_hash = hash_nid(nid_raw)
        user.national_id_hash = nid_hash

    logger.info("Master admin created (%s, id=%d)", email, user.id)
    return user
