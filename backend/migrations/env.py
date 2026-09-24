"""Alembic environment — GULA Platform.

Works in both online mode (direct DB connection) and offline mode (SQL script).
DATABASE_URL is read from the environment / .env via the app's own config module.
"""
import os
import sys
from contextlib import suppress
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import engine_from_config, pool
from alembic import context

# Migration mode: config.py will accept defaults for missing secrets
os.environ["RUNTIME_MODE"] = "migration"
os.environ.setdefault("ENV", "migration")
os.environ.setdefault("SECRET_KEY", "alembic-migration-key-" + "x" * 48)
os.environ.setdefault("ENCRYPTION_KEY", "6TJUTgJxBREYK9_yDy6VMXBw1HPwwxv1kiynV0WaAdw=")
os.environ.setdefault("NID_HMAC_KEY", "a" * 64)
os.environ.setdefault("REDIS_URL", "")

# The repository root must be importable: a few modules reached by
# import_all_models() use absolute `backend.app...` imports, so `backend` has to
# resolve as a package. CI exports PYTHONPATH with the workspace root, but a
# developer running `alembic upgrade head` from backend/ does not, and env.py
# must not depend on the caller's environment to import the models it needs.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

# ── Import models so their tables are visible to autogenerate ─────────────────
from app.database import Base
from app.models import (
    Lab, LabUser, User, Patient, TestType,
    LabOrder, LabResult, AuditLog, Sample, QualityControl,
    AccessibilityProfile, HealthPreference,
)
from app.models.claim import Claim, ClaimItem
from app.billing.models import (
    BillingAuditEvent,
    BillingInvoice,
    BillingInvoiceLine,
    BillingPayment,
    InsuranceCoverage,
)

# Populates every declarative base; called below, before target_metadata is
# built. Importing a *base* module registers no tables — the models live
# elsewhere — so PharmacyBase, RadiologyBase, NHDWBase and NursingBase each
# resolve to an EMPTY MetaData from a base-only import. Registering an empty
# metadata is worse than not registering it: autogenerate would compare zero
# mapped tables against a populated database and propose dropping all 74 of
# them. Reuses the application's own import_all_models() rather than a second
# list to maintain.
from app.factory import import_all_models

# Include NationalBase and other declarative bases so Alembic detects their tables
from app.national.base import NationalBase
from app.ehr.base import EHRBase
from app.citizen_platform.base import CitizenPlatformBase
from app.clinical.base import ClinicalBase
from app.health_data.base import HealthDataBase
from app.trust.base import TrustBase
from app.governance.base import GovernanceBase
from app.care_continuum.base import CareContinuumBase

# Registered in BATCH-3 preparation (NR-018). Ten declarative bases were absent
# from target_metadata, so autogenerate reported no drift for 203 mapped tables
# and an empty diff was indistinguishable from an accurate one.
from app.pharmacy.base import PharmacyBase
from app.radiology.base import RadiologyBase
from app.nhdw.base import NHDWBase
from app.nursing.base import NursingBase
from app.hospital.base import HospitalBase
from app.financial.models import FinBase
from app.national_data.base import DataPlatformBase
from app.document_intelligence.infrastructure.models import DocIntelBase

# Import EMS, Blood Bank, Critical Care, Biomedical models for Alembic autogenerate
# Wrapped in try/except: migration `upgrade head` still works if model files are
# incomplete or have changed names since the migration was written.
import importlib
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
    with suppress(ImportError):
        importlib.import_module(_mod)

# ClinicalBase models
import app.clinical.terminology.models  # noqa: E402
import app.clinical.cds.models  # noqa: E402
import app.clinical.knowledge.models  # noqa: E402
import app.clinical.quality.models  # noqa: E402
import app.clinical.research.models  # noqa: E402

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
from app.identity.base import IdentityBase  # noqa: E402
import app.identity.models  # noqa: E402

# Model modules that no other import in this file reaches. Measured, not guessed:
# with these absent, 64 physical tables were mapped by NO registered metadata,
# and a single-MetaData autogenerate would have proposed DROP TABLE for every
# one of them. A registered base being *populated* is not the same as it being
# *complete* — IdentityBase held 39 tables while 48 of its own were missing.
#
# Imported explicitly and NOT wrapped in suppress(ImportError): a module that
# stops importing must fail the migration loudly, because silently skipping it
# is exactly how the DROP-TABLE hazard returns.
import app.governance.models.citizen_platform  # noqa: E402
import app.identity.adaptive_auth.models  # noqa: E402
import app.identity.admin.models  # noqa: E402
import app.identity.compliance.models  # noqa: E402
import app.identity.federation.models  # noqa: E402
import app.identity.governance.models  # noqa: E402
import app.identity.lifecycle.models  # noqa: E402
import app.identity.notifications.models  # noqa: E402
import app.identity.trust.models  # noqa: E402
import app.identity.workflows.models  # noqa: E402
import app.models.ai  # noqa: E402
import app.models.integration_inbox  # noqa: E402
import app.models.mfa_device  # noqa: E402
import app.national.search_platform.infrastructure.models  # noqa: E402

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
    raise RuntimeError(
        "DATABASE_URL is not set. "
        "Export it or ensure backend/.env defines it."
    )

config.set_main_option("sqlalchemy.url", database_url)

# Logging — only configure if the ini file has a logging section
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Every base above is imported but not all of their models are; import_all_models()
# closes that gap so no registered metadata is empty when target_metadata is built.
import_all_models()

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
    # NR-018 registrations. Deliberately excluded and recorded instead:
    # app.national.task_engine (RETIRE: 15 tables, none physical, no reachable
    # operation) and app.insurance (DEFER: 13 tables, none physical, no
    # reachable operation, awaiting a product decision).
    PharmacyBase.metadata,
    RadiologyBase.metadata,
    NHDWBase.metadata,
    NursingBase.metadata,
    HospitalBase.metadata,
    FinBase.metadata,
    DataPlatformBase.metadata,
    DocIntelBase.metadata,
]

# NR-086 gave seven of the bases above one shared MetaData (app/orm_topology.py),
# because a ForeignKey resolves inside the MetaData that owns the *referring*
# table and 310 of them pointed elsewhere — which is why 76 mapped tables could
# not be written through the ORM at all. Seven entries in this list are now the
# same object, and Alembic rejects a multi-metadata target that claims one table
# twice, so the list is deduplicated by identity. Order is preserved, and the
# eleven bases that declare nothing across a base boundary keep their own.
_deduplicated = []
_seen_metadata = set()
for _md in target_metadata:
    if id(_md) not in _seen_metadata:
        _seen_metadata.add(id(_md))
        _deduplicated.append(_md)
target_metadata = _deduplicated


# ── Autogenerate is deliberately refused while the drift is unreconciled ─────
# The hook lives in app/orm_topology.py, beside the merge it makes safe: the
# merge is what lets autogenerate run, and this is what keeps it from writing
# a revision that drops columns nobody has classified. Importable from there,
# so it can be tested without replaying this file.
from app.orm_topology import (  # noqa: E402
    refuse_unreconciled_destructive_autogenerate,
)


# ── Offline mode (generates a .sql script) ───────────────────────────────────
def run_migrations_offline() -> None:
    context.configure(
        url=database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        process_revision_directives=refuse_unreconciled_destructive_autogenerate,
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
            process_revision_directives=refuse_unreconciled_destructive_autogenerate,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
