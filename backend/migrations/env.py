"""Alembic environment — GULA Platform.

Works in both online mode (direct DB connection) and offline mode (SQL script).
DATABASE_URL is read from the environment / .env via the app's own config module.
"""
import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

# ── Make the app importable from migrations/env.py ───────────────────────────
# alembic.ini sets prepend_sys_path = . (backend/), so `app` is importable.
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Prevent config.py from calling sys.exit() for missing prod keys when alembic
# runs without a full app environment (e.g. the migration-gate CI step only
# sets DATABASE_URL but not SECRET_KEY/ENCRYPTION_KEY/NID_HMAC_KEY).
os.environ.setdefault("ENV", "test")

# ── Import models so their tables are visible to autogenerate ─────────────────
from app.database import Base
from app.models import (
    Lab, LabUser, User, Patient, TestType,
    LabOrder, LabResult, AuditLog, Sample, QualityControl,
)

# Include NationalBase and other declarative bases so Alembic detects their tables
from app.national.base import NationalBase
from app.ehr.base import EHRBase
from app.citizen_platform.base import CitizenPlatformBase
from app.clinical.base import ClinicalBase

# Import EMS, Blood Bank, Critical Care, Biomedical models for Alembic autogenerate
from app.ems.infrastructure.models import (  # noqa: F401, E402
    EmergencyIncidentModel, AmbulanceModel, CrewMemberModel, DispatchModel,
    DispatchAssignmentModel, TriageTagModel, MassCasualtyIncidentModel,
    SceneSafetyModel, PatientAssessmentModel, PatientTransferOfCareModel,
    PrehospitalCareReportModel, PatientEventLogModel, DispatchCommunicationModel,
    DispatchHospitalModel, ResourceRequestModel, IncidentCommandModel,
)
from app.blood_bank.infrastructure.models import (  # noqa: F401, E402
    BloodDonorModel, DonorDeferralModel, BloodDonationEventModel,
    BloodComponentModel, BloodInventoryModel, BloodOrderModel,
    CrossmatchRecordModel, BloodTransfusionRecordModel,
    TransfusionAdverseEventModel, CompatibilityRuleModel, BloodBankModel,
)
from app.critical_care.infrastructure.models import (  # noqa: F401, E402
    ICUAdmissionModel, ICUBedModel, ICUAssessmentModel, VitalSignsRecordModel,
    VentilatorSettingModel, ContinuousInfusionModel, FluidBalanceModel,
    EarlyWarningScoreModel, ICUScoreModel, CriticalAlertModel,
    DeviceIntegrationModel, DailyChecklistModel, RoundRecordModel,
)
from app.biomedical.infrastructure.models import (  # noqa: F401, E402
    MedicalDeviceModel, WorkOrderModel, CalibrationRecordModel,
    SafetyInspectionModel, DeviceIncidentModel, DeviceRecallModel,
    TechnicianModel, VendorModel, SparePartModel, ServiceContractModel,
    MaintenanceScheduleModel, PerformanceVerificationModel,
)
from app.public_health.infrastructure.models import (  # noqa: F401, E402
    DiseaseCaseModel, OutbreakAlertModel, ImmunizationRecordModel,
    PublicHealthReportModel, SurveillanceSignalModel, EnvironmentalHealthModel,
)
from app.command_center.infrastructure.models import (  # noqa: F401, E402
    EmergencyDeclarationModel, ResourceRequestModel, SituationReportModel, AfterActionReportModel,
)
from app.pilot_platform.infrastructure.models import (  # noqa: F401, E402
    PilotProgramModel, PilotFacilityModel, ReadinessChecklistModel,
    GoNoGoGateModel, DeploymentRecordModel,
)
from app.lifecycle_platform.infrastructure.models import (  # noqa: F401, E402
    ComponentRegistryModel, ReleaseModel, CompatibilityMatrixModel,
    UpgradePathModel, DeprecationNoticeModel,
)

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

# Collect all declarative base metadata for autogenerate detection
# (EHR, Clinical, Citizen, and National models use separate declarative bases)
target_metadata = [
    Base.metadata,
    NationalBase.metadata,
    EHRBase.metadata,
    CitizenPlatformBase.metadata,
    ClinicalBase.metadata,
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
