"""Application factory — create_app() with mode-specific initialization.

Supports runtime modes:
    production   — full stack: DB, Redis, background tasks, monitoring
    development  — full stack with relaxed security, auto-docs
    testing      — minimal: DB only, no background tasks, no external services
    migration    — Alembic-only: no app routes, no background tasks
    openapi      — OpenAPI generation: no DB, Redis, AI, Financial Engine
    worker       — background worker: DB + Redis + task queues
    cli          — one-shot scripts: minimal init, no background tasks
"""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from .config import APP_NAME, APP_VERSION, IS_PRODUCTION, RUNTIME_MODE

logger = logging.getLogger("gula.factory")


def _is_openapi_mode() -> bool:
    return RUNTIME_MODE == "openapi" or os.getenv("OPENAPI_EXPORT", "").lower() == "true"


def _is_migration_mode() -> bool:
    return RUNTIME_MODE == "migration" or os.getenv("ALEMBIC_RUNNING", "").lower() == "true"


def _should_init_db() -> bool:
    if _is_openapi_mode():
        return False
    return True


def _should_init_redis() -> bool:
    if _is_openapi_mode() or _is_migration_mode():
        return False
    return True


def _should_init_background_tasks() -> bool:
    if _is_openapi_mode() or _is_migration_mode():
        return False
    from .config import background_tasks_enabled as _bg_enabled
    return _bg_enabled()


def _should_init_ai() -> bool:
    if _is_openapi_mode():
        return False
    return True


def _should_init_financial() -> bool:
    if _is_openapi_mode():
        return False
    from .config import ENABLE_FINANCIAL_ENGINE
    return ENABLE_FINANCIAL_ENGINE


def _should_init_monitoring() -> bool:
    if _is_openapi_mode() or _is_migration_mode():
        return False
    return True


def _should_init_sentry() -> bool:
    if _is_openapi_mode() or _is_migration_mode():
        return False
    return bool(os.getenv("SENTRY_DSN"))


def configure_sentry() -> None:
    import logging

    _SENTRY_DSN = os.getenv("SENTRY_DSN")
    if _SENTRY_DSN:
        try:
            import sentry_sdk
            from sentry_sdk.integrations.fastapi import FastApiIntegration
            from sentry_sdk.integrations.logging import LoggingIntegration
            from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

            sentry_sdk.init(
                dsn=_SENTRY_DSN,
                environment=os.getenv("ENVIRONMENT", "production"),
                release=os.getenv("APP_VERSION", "unknown"),
                integrations=[
                    FastApiIntegration(),
                    SqlalchemyIntegration(),
                    LoggingIntegration(level=logging.ERROR, event_level=logging.ERROR),
                ],
                traces_sample_rate=float(os.getenv("SENTRY_TRACES_RATE", "0.05")),
            )
            logger.info("Sentry initialized (env=%s)", os.getenv("ENVIRONMENT", "production"))
        except ImportError:
            logger.warning("SENTRY_DSN set but sentry-sdk not installed; skipping")


def import_all_models() -> None:
    """Import every model so SQLAlchemy Base.metadata is fully populated.

    Called once at startup. Must be idempotent.
    """
    from .hospital.models import (  # noqa: F401
        Bed, BedAssignment, Building, Campus, Clinic, CostCenter,
        Floor, HospitalDepartment, HospitalMaster, MedicalEquipment,
        OperationTheater, Room, Unit,
    )
    from .lims.models import (  # noqa: F401
        EQA, IQC, AutoValidationRule, Calibration, ChainOfCustody,
        Consumable, DeltaCheckRule, ElectronicSignature, EquipmentLog,
        Instrument, InstrumentModel, LabReport, Lot, Maintenance,
        Manufacturer, Order, Panel, PanelTest, QCProgram, Reagent,
        ReferenceRangeDef, ReportAttachment, Result, ResultRelease,
        ResultValidation, Section, Specimen, SpecimenCatalog, Storage,
        Supplier, TemperatureLog, Transportation, Workstation,
    )
    from .models import (  # noqa: F401
        AuditLog, Lab, LabOrder, LabResult, LabUser, Patient,
        QualityControl, Sample, TestType, User,
    )
    from .models.outbox import OutboxEvent  # noqa: F401
    from .nhdw.models import (  # noqa: F401
        Admission, CarePlan, ClinicalTask, DashboardConfiguration,
        Discharge, HospitalAlert, HospitalMessage, QueueEntry,
        ResourceSchedule, ShiftReport, TelemedicineSession, Transfer,
        WaitingListEntry, WardRound,
    )
    from .nursing.models import (  # noqa: F401
        ClinicalChecklist, Delegation, EscalationRecord, FallRiskAssessment,
        FluidBalance, NursingCarePlan, NursingNote, NursingShift,
        NursingTask, NutritionAssessment, PainAssessment, PatientAssignment,
        PressureInjuryAssessment, ShiftHandover,
    )
    from .pharmacy.models import (  # noqa: F401
        AllergyRule, ClinicalGuideline, ContraindicationRule, DispenseQueue,
        DispenseRecord, DoseGuideline, DrugBatch, DrugCatalog,
        DrugInteractionRule, DrugMonitoring, DrugReturn, DrugSupplier,
        InventoryForecast, InventoryTransfer, InventoryTransferItem,
        Prescription, PrescriptionItem, Recall, StockLevel, StockMovement,
        Store, Warehouse, WasteRecord,
    )
    from .radiology.ai import AIAnalysisJob  # noqa: F401
    from .radiology.models import (  # noqa: F401
        MPPS, CriticalFinding, DICOMStorage, DICOMStudy, ImageAnnotation,
        ImageMeasurement, ImageShare, ModalityDevice, Protocol,
        RadiologyAppointment, RadiologyExam, RadiologyImage, RadiologyOrder,
        RadiologyReport, RadiologySeries, ReportTemplate, WorklistEntry,
    )
    from .models.subscription import (  # noqa: F401
        FeatureFlag, LabSubscription, UpgradeDemandScore, UpgradeRequest,
    )
    from .models.edge import (  # noqa: F401
        EdgeDevice, EdgeEvent, EdgeModel, EdgeModelAssignment,
        EdgePolicy, EdgeTask, EdgeTelemetry,
    )
    from .national_data.models import (  # noqa: F401
        CanonicalDocument, CanonicalEncounter, CanonicalMedication,
        CanonicalObservation, CanonicalPatient, CanonicalProcedure,
    )
    from .national_data.models.ai_data import (  # noqa: F401
        DeidentificationJob, FeatureStore, FeatureValue,
        KnowledgeGraphEdge, KnowledgeGraphNode, SyntheticDataJob,
        TrainingDataset, VectorEmbedding,
    )
    from .national_data.models.event_store import (  # noqa: F401
        EventRetentionPolicy, EventSnapshot, StoredEvent,
    )
    from .national_data.models.governance import (  # noqa: F401
        ConsentDirective, DataCatalogEntry, DataClassification,
        DataLineageEntry, DataQualityCheck, DataQualityRule,
        DataSteward, MetadataEntry, RetentionPolicy,
    )
    from .national_data.models.mdm import (  # noqa: F401
        DeviceRegistry, DuplicateRecord, GoldenRecord, LocationRegistry,
        MergeAction, ProviderRegistry, SourceSystem, TerminologyRegistry,
    )
    from .national_data.models.warehouse import (  # noqa: F401
        DimDate, DimDiagnosis, DimFacility, DimPatient, DimProvider,
        FactDiagnosis, FactLabResult, FactPatientVisit,
    )
    from .models.ai_interaction import (  # noqa: F401
        AIFeedback, AIInteraction, AIRetrievalRef,
        AIUnresolvedQuestion, MedicalTerminologyNormalized,
    )
    from .national.ecosystem.partners.models import (  # noqa: F401
        Partner, PartnerAgreement, PartnerAuditLog, PartnerCertificate,
        PartnerCredential, PartnerRateLimit,
    )
    from .document_intelligence.infrastructure.models import (  # noqa: F401
        ScannedDocumentModel, OcrResultModel, ExtractedEntityModel,
        ExtractedFieldModel, ExtractedTableModel, ClassificationResultModel,
        PipelineResultModel, DocumentVersionModel, GovernmentDocumentModel,
        DocumentReviewModel, DocumentAnnotationModel, DigitalPreservationRecordModel,
        GovernancePolicyModel, GovernanceEventModel, DocumentEventModel,
        DocumentLifecycleModel, WebhookRegistrationModel, KnowledgeGraphEdgeModel,
        PipelineHealthModel, AccessControlModel, DocumentRetentionModel,
    )


def _build_middleware_stack(app: FastAPI) -> None:
    """Register all middleware in the correct order."""
    from .config import MAX_REQUEST_BODY_MB

    from app.middleware import (  # noqa: E402
        ConcurrencyLimitMiddleware, KernelMiddleware, MaxBodySizeMiddleware,
        ReadinessMiddleware, RequestIDMiddleware, RequestTimingMiddleware,
        SecurityHeadersMiddleware,
    )
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.middleware.gzip import GZipMiddleware

    app.add_middleware(MaxBodySizeMiddleware, max_size_mb=MAX_REQUEST_BODY_MB)
    app.add_middleware(RequestIDMiddleware)

    if IS_PRODUCTION:
        from .security.auth import decode_token
        from starlette.middleware.base import BaseHTTPMiddleware

        class _DocsAuthMiddleware(BaseHTTPMiddleware):
            _PROTECTED = {"/docs", "/redoc", "/openapi.json"}

            async def dispatch(self, request, call_next):
                if request.url.path not in self._PROTECTED:
                    return await call_next(request)
                token = request.cookies.get("access_token")
                if not token:
                    auth_header = request.headers.get("Authorization", "")
                    if auth_header.startswith("Bearer "):
                        token = auth_header[7:]
                if not token:
                    return JSONResponse(status_code=401, content={"detail": "Authentication required"})
                payload = decode_token(token)
                if not payload or payload.get("role") not in ("admin", "master_admin"):
                    return JSONResponse(status_code=403, content={"detail": "Admin access required"})
                return await call_next(request)

        app.add_middleware(_DocsAuthMiddleware)

    _allowed_origins = os.getenv("CORS_ORIGINS", "").split(",")
    _allowed_origins = [o.strip() for o in _allowed_origins if o.strip()]
    if not _allowed_origins:
        _allowed_origins = ["https://gula-platform.org"]
        if os.getenv("ENV", "production") in ("development", "test"):
            _allowed_origins += [
                "http://localhost:8080", "http://localhost:80",
                "http://localhost:3000", "http://localhost:5173",
                "http://localhost:4173", "http://localhost:8000",
                "https://aistudio.google.com", "https://claude.ai",
            ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=_allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID",
                       "X-Device-ID", "X-App-Version", "Idempotency-Key"],
        expose_headers=["X-Request-ID", "X-Response-Time", "X-API-Version"],
    )

    app.add_middleware(RequestTimingMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    from .core.self_healing import DegradedModeMiddleware
    app.add_middleware(DegradedModeMiddleware)

    if not _is_openapi_mode():
        app.add_middleware(ReadinessMiddleware)

    app.add_middleware(KernelMiddleware)

    if not _is_openapi_mode():
        app.add_middleware(ConcurrencyLimitMiddleware)


def _register_routes(app: FastAPI) -> None:
    """Register all API routes on the application.

    In openapi mode, we still register routes (they define the OpenAPI schema)
    but skip any route module that requires DB/AI/external service imports.
    """
    from .routes import (  # noqa: E402
        admin, batch, compliance, critical_alerts, dashboard,
        device_results, ehr, ehr_fhir, id_scan, identity, insurance,
        labs, login, metrics, mobile, national_identity, notifications,
        patients, qr, quality_control, register, results, samples,
        security, setup, test_results,
    )
    from .routes import admin_log_level
    from .routes import ai as ai_routes
    from .routes import citizen_portal as citizen_portal_routes
    from .routes import optimizer as optimizer_routes
    from .routes import tiers as tiers_routes

    core_routes = [
        login, register, setup, metrics, patients, results,
        test_results, dashboard, labs, samples,
    ]
    feature_routes = [
        qr, id_scan, identity, notifications, ehr, ehr_fhir,
        security, device_results,
    ]
    advanced_routes = [quality_control, critical_alerts, batch]
    admin_routes = [admin, admin_log_level]
    mobile_routes = [mobile]
    compliance_routes = [compliance]

    for r in core_routes + feature_routes + advanced_routes + admin_routes + mobile_routes + compliance_routes:
        app.include_router(r.router)

    app.include_router(tiers_routes.router)

    from .financial import register_routes as register_financial_routes
    register_financial_routes(app)

    app.include_router(citizen_portal_routes.router)

    from .routes import claims as claims_routes
    app.include_router(claims_routes.router)

    app.include_router(national_identity.router)
    app.include_router(insurance.router)

    app.include_router(ai_routes.router)
    app.include_router(optimizer_routes.router)

    from .routes import ai_platform as ai_platform_routes
    app.include_router(ai_platform_routes.router)

    from .routes import stats as stats_routes
    app.include_router(stats_routes.router)

    from .services.mpi import router as mpi_router
    app.include_router(mpi_router)

    from .routes import canonical_patient as canonical_patient_routes
    app.include_router(canonical_patient_routes.router)

    from .routes import consent as consent_routes
    app.include_router(consent_routes.router)

    from .routes import mfa as mfa_routes
    app.include_router(mfa_routes.router)

    from .routes import password_reset as password_reset_routes
    app.include_router(password_reset_routes.router)

    from .routes import oauth2 as oauth2_routes
    app.include_router(oauth2_routes.router)

    from .routes import saml as saml_routes
    app.include_router(saml_routes.router)

    from .routes import service_accounts as service_accounts_routes
    app.include_router(service_accounts_routes.router)

    from .routes import integrations as integrations_routes
    app.include_router(integrations_routes.router)

    from .routes import edge as edge_routes
    app.include_router(edge_routes.router)

    from .routes import patient_card as patient_card_routes
    app.include_router(patient_card_routes.router)

    from .routes import care_continuum as care_continuum_routes
    app.include_router(care_continuum_routes.router)

    if not _is_openapi_mode():
        from .routes import ai_telemetry as ai_telemetry_routes
        app.include_router(ai_telemetry_routes.router)

    from .routes import clinical as clinical_routes
    from .routes import clinical_documentation as clinical_documentation_routes
    from .routes import clinical_orders as clinical_orders_routes
    from .routes import clinical_quality as clinical_quality_routes
    app.include_router(clinical_routes.router)
    app.include_router(clinical_orders_routes.router)
    app.include_router(clinical_documentation_routes.router)
    app.include_router(clinical_quality_routes.router)

    from .kernel import routes as kernel_routes
    app.include_router(kernel_routes.router)

    from .governance.routes import analytics_router, governance_router
    app.include_router(governance_router)
    app.include_router(analytics_router)

    from .lims import routes as lims_routes
    app.include_router(lims_routes.router)

    from .national.rules_engine.api.routes import router as rules_router
    app.include_router(rules_router)

    from .national.background_platform.api.routes import router as background_router
    app.include_router(background_router)

    from .national.workflow_runtime.api.routes import router as workflow_router
    app.include_router(workflow_router)

    from .national.task_engine.api.routes import router as task_router
    app.include_router(task_router)

    from .national.notification_platform.api.routes import router as notification_platform_router
    app.include_router(notification_platform_router)

    from .national.document_platform.api.routes import router as document_router
    app.include_router(document_router)

    from .national.scheduling_platform.api.routes import router as scheduling_router
    app.include_router(scheduling_router)

    from .national.search_platform.api.routes import router as search_router
    app.include_router(search_router)

    from .national.observability.api.routes import router as observability_router
    app.include_router(observability_router)

    if not _is_openapi_mode():
        from .routes import national_data as national_data_routes
        from .routes import national_streaming as national_streaming_routes
        app.include_router(national_data_routes.router)
        app.include_router(national_streaming_routes.router)

    from .platform.routes import router as platform_router
    app.include_router(platform_router)

    from .contracts.routes import router as contracts_router
    app.include_router(contracts_router)

    from .integration.connectors.routes import router as connectors_router
    app.include_router(connectors_router)

    from .routes import hospital as hospital_routes
    app.include_router(hospital_routes.router)

    from .nhdw.routes import router as nhdw_router
    app.include_router(nhdw_router)

    from .nursing.routes import router as nursing_router
    app.include_router(nursing_router)

    from .pharmacy.routes import router as pharmacy_router
    app.include_router(pharmacy_router)

    from .radiology.routes import router as radiology_router
    app.include_router(radiology_router)

    from .simulation.routes import router as simulation_router
    app.include_router(simulation_router)

    from .command_intelligence.routes import router as command_intelligence_router
    app.include_router(command_intelligence_router)

    from .knowledge_graph.routes import router as knowledge_graph_router
    app.include_router(knowledge_graph_router)

    from .roadmap.routes import router as roadmap_router
    app.include_router(roadmap_router)

    from .health_data.routes import router as health_data_router
    app.include_router(health_data_router)

    from .control_plane.routes import router as control_plane_router
    app.include_router(control_plane_router)

    from .kernel.runtime_routes import router as runtime_kernel_router
    app.include_router(runtime_kernel_router)

    from .integration.integration import IntegrationPlatform
    IntegrationPlatform().initialize(app)

    from .citizen_platform.routes import router as citizen_platform_router
    app.include_router(citizen_platform_router)

    from .ai_fabric.routes import router as ai_fabric_router
    app.include_router(ai_fabric_router)

    from .research_platform.routes import router as research_platform_router
    app.include_router(research_platform_router)

    from .certification.routes import router as certification_router
    app.include_router(certification_router)

    from .national.ecosystem.gateway.routes import router as ecosystem_gateway_router
    from .national.ecosystem.routes import router as ecosystem_router
    app.include_router(ecosystem_router)
    app.include_router(ecosystem_gateway_router)

    from .national.intelligence.routes import router as intelligence_router
    app.include_router(intelligence_router)

    from .ems.api.routes import router as ems_router
    app.include_router(ems_router)

    from .document_intelligence.api.routes import router as doc_intel_router
    app.include_router(doc_intel_router)

    from .blood_bank.api.routes import router as blood_bank_router
    app.include_router(blood_bank_router)

    from .critical_care.api.routes import router as critical_care_router
    app.include_router(critical_care_router)

    from .biomedical.api.routes import router as biomedical_router
    app.include_router(biomedical_router)

    from .public_health.api.routes import router as public_health_router
    app.include_router(public_health_router)

    from .command_center.api.routes import router as command_center_router
    app.include_router(command_center_router)

    from .pilot_platform.api.routes import router as pilot_platform_router
    app.include_router(pilot_platform_router)

    from .lifecycle_platform.api.routes import router as lifecycle_router
    app.include_router(lifecycle_router)

    from .trust.routes import router as trust_router
    app.include_router(trust_router)

    logger.info("All platform routes registered")


def _build_lifespan():
    """Return a lifespan context manager appropriate to the current runtime mode."""

    @asynccontextmanager
    async def _lifespan(_app: FastAPI):
        if not _should_init_background_tasks():
            logger.info("Runtime mode '%s' — skipping background task init", RUNTIME_MODE)
        else:
            from .main import start_background_workers, warmup
            await start_background_workers()
            await warmup()

        if _should_init_db():
            from .core.startup_guard import run_startup_guard
            await run_startup_guard()

        if not _is_openapi_mode():
            try:
                from .kernel.integration import warmup_kernel
                await warmup_kernel()
            except Exception as exc:
                logger.warning("Kernel warmup skipped: %s", exc)

        yield

        if _should_init_background_tasks():
            from .main import _bg_tasks
            logger.info("Shutting down %d background task(s)...", len(_bg_tasks))
            from .kernel.integration import stop_kernel
            try:
                await stop_kernel()
            except Exception as exc:
                logger.error("Kernel shutdown error: %s", exc)
            for task in list(_bg_tasks):
                task.cancel()
            if _bg_tasks:
                import asyncio
                await asyncio.gather(*list(_bg_tasks), return_exceptions=True)

        if _should_init_db():
            from .database import engine
            engine.dispose()
            logger.info("Database connections closed")

    return _lifespan


def _exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch unhandled errors - return friendly JSON instead of 500 stack trace."""
    request_id = getattr(request.state, "request_id", "unknown")
    from .core.startup_guard import is_system_ready

    ready, reason = is_system_ready()

    if not ready and IS_PRODUCTION:
        logger.error(
            "[%s] Unhandled exception during unready state: %s %s (Reason: %s)",
            request_id,
            request.method,
            request.url.path,
            reason,
        )
        return JSONResponse(
            status_code=503,
            content={
                "detail": f"Service Unavailable: System not ready. Reason: {reason}",
                "detail_ar": f"الخدمة غير متاحة: النظام غير جاهز. السبب: {reason}",
                "request_id": request_id,
            },
        )
    if IS_PRODUCTION:
        logger.error(
            "[%s] Unhandled exception: %s %s", request_id, request.method, request.url.path
        )
        return JSONResponse(
            status_code=500,
            content={
                "detail": "An unexpected error occurred. Please try again later.",
                "detail_ar": "حدث خطأ غير متوقع. يرجى المحاولة لاحقاً.",
                "request_id": request_id,
            },
        )
    # In development, log full exception and return more details
    logger.exception("[%s] %s %s: %s", request_id, request.method, request.url.path, exc)
    return JSONResponse(
        status_code=500,
        content={
            "detail": str(exc),
            "detail_ar": "حدث خطأ: " + str(exc),
            "request_id": request_id,
        },
    )


def create_app(override_mode: str | None = None) -> FastAPI:
    """Create and configure a FastAPI application instance.

    Args:
        override_mode: Optional override for RUNTIME_MODE. If None, uses the
                      configured RUNTIME_MODE from config.py.
    """
    if override_mode:
        os.environ["RUNTIME_MODE"] = override_mode

    from .core.logging_config import configure_logging
    configure_logging(is_production=IS_PRODUCTION, log_level="INFO")

    if _should_init_sentry():
        configure_sentry()

    import_all_models()

    _docs_url = None
    _redoc_url = None
    from .config import ENABLE_API_DOCS
    if not IS_PRODUCTION or ENABLE_API_DOCS:
        _docs_url = "/docs"
        _redoc_url = "/redoc"

    lifespan = _build_lifespan()

    app = FastAPI(
        title=APP_NAME,
        version=APP_VERSION,
        lifespan=lifespan,
        description=(
            "**GULA** - منصة غولا الصحية الذكية للمختبرات\n\n"
            "Smart Health Platform for Medical Laboratories in Iraq.\n\n"
            "**Authentication:** Use `Bearer <token>` header "
            "(obtain token from `POST /login`).\n\n"
            "**Mobile:** Refresh tokens available via `POST /auth/refresh`.\n\n"
            "**Version:** " + APP_VERSION
        ),
        docs_url=_docs_url,
        redoc_url=_redoc_url,
        contact={
            "name": "GULA Platform Support",
            "url": "https://gula-platform.org",
            "email": "support@gula-platform.org",
        },
        license_info={"name": "Proprietary - Ministry of Health Iraq Compliant"},
    )

    app.exception_handler(Exception)(_exception_handler)

    _build_middleware_stack(app)

    _register_routes(app)
    if _is_openapi_mode():
        logger.info("OpenAPI mode — routes registered for schema generation only")

    return app
