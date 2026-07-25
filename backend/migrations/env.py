"""Alembic environment — GULA Platform.

Works in both online mode (direct DB connection) and offline mode (SQL script).
DATABASE_URL is read from the environment / .env via the app's own config module.
"""

import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

# Migration mode: config.py will accept defaults for missing secrets
os.environ["RUNTIME_MODE"] = "migration"
os.environ.setdefault("ENV", "migration")
os.environ.setdefault("SECRET_KEY", "alembic-migration-key-" + "x" * 48)
os.environ.setdefault("ENCRYPTION_KEY", "6TJUTgJxBREYK9_yDy6VMXBw1HPwwxv1kiynV0WaAdw=")
os.environ.setdefault("NID_HMAC_KEY", "a" * 64)
os.environ.setdefault("REDIS_URL", "")

# ── Import models so their tables are visible to autogenerate ─────────────────
from app.database import Base
from app.models import (
    Lab,
    LabUser,
    User,
    Patient,
    TestType,
    LabOrder,
    LabResult,
    AuditLog,
    Sample,
    QualityControl,
)

# Include NationalBase and other declarative bases so Alembic detects their tables
from app.national.base import NationalBase
from app.ehr.base import EHRBase
from app.citizen_platform.base import CitizenPlatformBase
from app.clinical.base import ClinicalBase
from app.health_data.base import HealthDataBase
from app.trust.base import TrustBase
from app.governance.base import GovernanceBase
from app.care_continuum.base import CareContinuumBase

# Import EMS, Blood Bank, Critical Care, Biomedical models for Alembic autogenerate
# Wrapped in try/except: migration `upgrade head` still works if model files are
# incomplete or have changed names since the migration was written.
import importlib
import contextlib

for _mod in [
    "app.ems.infrastructure.models",
    "app.blood_bank.infrastructure.models",
    "app.critical_care.infrastructure.models",
    "app.biomedical.infrastructure.models",
    "app.public_health.infrastructure.models",
    "app.command_center.infrastructure.models",
    "app.pilot_platform.infrastructure.models",
    "app.lifecycle_platform.infrastructure.models",
]:
    with contextlib.suppress(ImportError):
        importlib.import_module(_mod)

# ClinicalBase models
import app.clinical.terminology.models  # noqa: E402
import app.clinical.cds.models  # noqa: E402
import app.clinical.knowledge.models  # noqa: E402
import app.clinical.quality.models  # noqa: E402

# HealthDataBase models
import app.health_data.canonical.models  # noqa: E402
import app.health_data.mdm.models  # noqa: E402
import app.health_data.ods.models  # noqa: E402
import app.health_data.warehouse.models  # noqa: E402

# TrustBase models
from app.trust import models as _trust_models  # noqa: E402

# GovernanceBase models
import app.governance.models  # noqa: E402

# CareContinuumBase models
import app.care_continuum.models  # noqa: E402

# IdentityBase models (NIAM — National Identity & Access Management)
from app.identity.base import IdentityBase
import app.identity.models  # noqa: E402

# ── Alembic Config object ─────────────────────────────────────────────────────
config = context.config

# Resolve DATABASE_URL: prefer environment variable, fall back to app config
database_url = os.environ.get("DATABASE_URL")
if not database_url:
    try:
        from app.config import DATABASE_URL as _app_db_url

        database_url = _app_db_url
    except ImportError:
        pass

if not database_url:
    raise RuntimeError("DATABASE_URL is not set. Export it or ensure backend/.env defines it.")

config.set_main_option("sqlalchemy.url", database_url)

# Logging — only configure if the ini file has a logging section
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Collect all declarative base metadata for autogenerate detection
# (EHR, Clinical, Citizen, and National models use separate declarative bases)
target_metadata = [
    Base.metadata,
    NationalBase.metadata,
    EHRBase.metadata,
    CitizenPlatformBase.metadata,
    ClinicalBase.metadata,
    HealthDataBase.metadata,
    TrustBase.metadata,
    GovernanceBase.metadata,
    CareContinuumBase.metadata,
    IdentityBase.metadata,
]


# ── Offline mode (generates a .sql script) ───────────────────────────────────
def run_migrations_offline() -> None:
    context.configure(
        url=database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


# ── Online mode (applies directly to the database) ───────────────────────────
def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
