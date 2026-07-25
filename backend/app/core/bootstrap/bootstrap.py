from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.database import SessionLocal

from .config import load_bootstrap_config
from .demo_data import seed_demo_data
from .departments import seed_departments
from .directorates import seed_health_directorates
from .facilities import seed_platform_facilities
from .laboratories import seed_laboratory_types
from .master_admin import _ensure_master_admin
from .ministry import seed_ministry_of_health
from .permissions import seed_permissions
from .roles import seed_roles
from .subscriptions import seed_subscriptions
from .users import seed_national_admin_accounts

logger = logging.getLogger("gula.bootstrap")


def run_bootstrap(db: Session | None = None) -> dict[str, int]:
    if db is None:
        db = SessionLocal()
        own_session = True
    else:
        own_session = False

    cfg = load_bootstrap_config()
    counts: dict[str, int] = {}
    results: dict[str, bool] = {}

    try:
        if not cfg.enable_bootstrap:
            logger.info("Bootstrap disabled via ENABLE_BOOTSTRAP=false")
            return counts

        logger.info("=== Starting National Bootstrap ===")

        master_admin = _ensure_master_admin(db)
        db.commit()
        counts["master_admin"] = 1 if master_admin else 0
        results["master_admin"] = master_admin is not None
        logger.info("Step 1/10: Master admin — %s", "OK" if master_admin else "skipped")

        perm_count = seed_permissions(db=db)
        counts["permissions"] = perm_count
        results["permissions"] = True
        logger.info("Step 2/10: Permissions — %d created", perm_count)

        role_count = seed_roles(db=db)
        counts["roles"] = role_count
        results["roles"] = True
        logger.info("Step 3/10: Roles — %d created", role_count)

        if cfg.enable_national_bootstrap:
            ministry_ok = seed_ministry_of_health(db=db)
            counts["ministry"] = 1 if ministry_ok else 0
            results["ministry"] = ministry_ok
            logger.info("Step 4/10: Ministry of Health — %s", "OK" if ministry_ok else "failed")

            dir_count = seed_health_directorates(db=db)
            counts["directorates"] = dir_count
            results["directorates"] = True
            logger.info("Step 5/10: Health Directorates — %d created", dir_count)

            fac_count = seed_platform_facilities(db=db)
            counts["platform_facilities"] = fac_count
            results["platform_facilities"] = True
            logger.info("Step 6/10: Platform Facilities — %d created", fac_count)

            lab_type_count = seed_laboratory_types(db=db)
            counts["laboratory_types"] = lab_type_count
            results["laboratory_types"] = True
            logger.info("Step 7/10: Laboratory Types — %d created", lab_type_count)
        else:
            logger.info(
                "Steps 4-7: National bootstrap disabled via ENABLE_NATIONAL_BOOTSTRAP=false",
            )

        dept_count = seed_departments(db=db)
        counts["departments"] = dept_count
        results["departments"] = True
        logger.info("Step 8/10: Departments — %d created", dept_count)

        user_count = seed_national_admin_accounts(db=db)
        counts["admin_accounts"] = user_count
        results["admin_accounts"] = True
        logger.info("Step 9/10: Admin Accounts — %d created", user_count)

        sub_count = seed_subscriptions(db=db)
        counts["subscriptions"] = sub_count
        results["subscriptions"] = True
        logger.info("Step 10/10: Subscriptions — %d created", sub_count)

        if cfg.enable_demo_data:
            demo_counts = seed_demo_data(db=db)
            counts["demo_patients"] = demo_counts.get("patients", 0)
            counts["demo_technicians"] = demo_counts.get("technicians", 0)
            counts["demo_doctors"] = demo_counts.get("doctors", 0)
            counts["demo_orders"] = demo_counts.get("orders", 0)
            counts["demo_results"] = demo_counts.get("results", 0)
            logger.info("Demo data: %s", demo_counts)

        db.commit()
        logger.info("=== National Bootstrap Complete ===")

    except Exception as exc:
        db.rollback()
        logger.error("Bootstrap failed: %s", exc)
        raise
    finally:
        if own_session:
            db.close()

    return counts
