"""Seed and bootstrap functions for GULA Platform startup.

Extracted from routes/admin.py and routes/tiers.py so that core/startup_guard.py
does not depend on presentation-layer modules. Route modules re-export these
functions for backward compatibility.
"""

from __future__ import annotations

import hashlib
import hmac as _hmac
import logging
import os

from sqlalchemy.orm import Session

from app.config import NID_HMAC_KEY
from app.database import SessionLocal
from app.models.lab import Lab
from app.models.lab_user import LabUser
from app.models.subscription import LabSubscription
from app.security.auth import hash_password

logger = logging.getLogger("gula.seeds")


# =============================================================================
# National ID hashing (shared utility)
# =============================================================================


def hash_nid(nid: str) -> str:
    """HMAC-SHA256 of a national ID — never store raw NID.

    Uses the same NID_HMAC_KEY as the rest of the platform for consistent hashes.
    """
    key = NID_HMAC_KEY.encode()
    return _hmac.new(key, nid.strip().encode(), hashlib.sha256).hexdigest()


# =============================================================================
# Master Admin Bootstrap
# =============================================================================


def ensure_master_admin() -> None:
    """Seed the MASTER_ADMIN account on a brand-new database.

    Environment variables consumed:
      GULA_ADMIN_EMAIL         — email for login (default: admin@gula-platform.org)
      GULA_ADMIN_NAME          — display name
      GULA_ADMIN_PASSWORD      — plaintext password (hashed at runtime)
      GULA_ADMIN_PASSWORD_HASH — pre-hashed password (takes priority)
      MASTER_ADMIN_NID         — national ID to associate (raw, hashed server-side)

    Rules:
    - Runs only when no master_admin row exists (fresh DB).
    - Skips silently if password is not configured.
    - If master_admin already exists AND MASTER_ADMIN_NID is set but not yet
      linked, this function will link the NID to the existing account.
    """
    db = SessionLocal()
    try:
        existing = db.query(LabUser).filter(LabUser.role == "master_admin").first()

        if not existing:
            email = os.getenv("GULA_ADMIN_EMAIL", "admin@gula-platform.org")
            name = os.getenv("GULA_ADMIN_NAME", "GULA Admin")

            password_hash = os.getenv("GULA_ADMIN_PASSWORD_HASH", "").strip() or None
            if not password_hash:
                plaintext = os.getenv("GULA_ADMIN_PASSWORD", "").strip() or None
                if not plaintext:
                    logger.error(
                        "Bootstrap SKIPPED: GULA_ADMIN_PASSWORD not set. "
                        "Set it in .env and restart."
                    )
                    return
                password_hash = hash_password(plaintext)

            platform_lab = db.query(Lab).filter(Lab.name == "GULA Platform").first()
            if not platform_lab:
                platform_lab = Lab(name="GULA Platform", city="Platform", is_active=True)
                db.add(platform_lab)
                db.flush()

            existing = LabUser(
                lab_id=platform_lab.id,
                name=name,
                email=email,
                password_hash=password_hash,
                role="master_admin",
                is_active=True,
            )
            db.add(existing)
            db.flush()
            logger.info("Bootstrap: master_admin created (%s, id=%d)", email, existing.id)

        # ── Link national ID if provided and not yet set ──
        nid_raw = os.getenv("MASTER_ADMIN_NID", "").strip()
        if nid_raw and not existing.national_id_hash:
            nid_hash = hash_nid(nid_raw)
            conflict = (
                db.query(LabUser)
                .filter(
                    LabUser.national_id_hash == nid_hash,
                    LabUser.id != existing.id,
                )
                .first()
            )
            if conflict:
                logger.error(
                    "Bootstrap: MASTER_ADMIN_NID hash already belongs to user %d — skipping NID link",
                    conflict.id,
                )
            else:
                existing.national_id_hash = nid_hash
                logger.info("Bootstrap: national_id linked to master_admin (id=%d)", existing.id)

        db.commit()

    except Exception as exc:
        db.rollback()
        logger.error("Bootstrap: failed — %s", exc)
    finally:
        db.close()


# =============================================================================
# Default Subscriptions
# =============================================================================


def seed_default_subscriptions(db: Session) -> None:
    """Ensure every active lab has a LabSubscription row.

    Called during startup seeding — safe to run multiple times.
    """
    from app.core.feature_flags import get_tier_limits

    labs_without_sub = (
        db.query(Lab)
        .outerjoin(LabSubscription, Lab.id == LabSubscription.lab_id)
        .filter(LabSubscription.id is None, Lab.is_active)
        .all()
    )
    for lab in labs_without_sub:
        sub = LabSubscription(
            lab_id=lab.id,
            tier="starter",
            deployment_mode="single",
            security_level="standard",
            **get_tier_limits("starter"),
        )
        db.add(sub)

    if labs_without_sub:
        db.commit()
        logger.info("[SEEDS] Seeded default subscriptions for %d labs", len(labs_without_sub))
