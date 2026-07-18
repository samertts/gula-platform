from __future__ import annotations

import logging

from fastapi import FastAPI

from app.research_platform.routes import router as research_router
from app.research_platform.sdk import ResearchSDK

logger = logging.getLogger("gula.research_platform.integration")

_sdk: ResearchSDK | None = None


def get_research_sdk() -> ResearchSDK:
    global _sdk
    if _sdk is None:
        _sdk = ResearchSDK()
    return _sdk


def register_routes(app: FastAPI) -> None:
    app.include_router(research_router)
    logger.info("Research Platform routes registered")


def seed_default_kpis(sdk: ResearchSDK | None = None) -> None:
    from app.research_platform.enums import KpiCategory
    from app.research_platform.kpi_engine import KPIDefinition as KpiDefinition

    svc = sdk or get_research_sdk()
    default_kpis = [
        KpiDefinition(code="CLIN_MORTALITY_RATE", name="In-hospital Mortality Rate", category=KpiCategory.CLINICAL, unit="%", target=2.0, direction="lower_is_better"),
        KpiDefinition(code="CLIN_READMISSION_RATE", name="30-day Readmission Rate", category=KpiCategory.CLINICAL, unit="%", target=15.0, direction="lower_is_better"),
        KpiDefinition(code="LAB_TAT_STAT", name="STAT TAT (minutes)", category=KpiCategory.LAB, unit="min", target=60.0, direction="lower_is_better"),
        KpiDefinition(code="LAB_TAT_ROUTINE", name="Routine TAT (hours)", category=KpiCategory.LAB, unit="hrs", target=24.0, direction="lower_is_better"),
        KpiDefinition(code="LAB_CRITICAL_RATE", name="Critical Results Rate", category=KpiCategory.LAB, unit="%", target=5.0),
        KpiDefinition(code="OPS_BED_OCCUPANCY", name="Bed Occupancy Rate", category=KpiCategory.OPERATIONAL, unit="%", target=85.0),
        KpiDefinition(code="OPS_AVG_LOS", name="Average Length of Stay", category=KpiCategory.OPERATIONAL, unit="days", target=5.0, direction="lower_is_better"),
        KpiDefinition(code="FIN_COST_PER_CASE", name="Cost per Case", category=KpiCategory.FINANCIAL, unit="IQD"),
        KpiDefinition(code="POP_INFANT_MORTALITY", name="Infant Mortality Rate", category=KpiCategory.POPULATION, unit="per_1000", target=10.0, direction="lower_is_better"),
        KpiDefinition(code="POP_MATERNAL_MORTALITY", name="Maternal Mortality Ratio", category=KpiCategory.POPULATION, unit="per_100k", target=50.0, direction="lower_is_better"),
        KpiDefinition(code="POP_VACCINATION_COVERAGE", name="Vaccination Coverage Rate", category=KpiCategory.POPULATION, unit="%", target=95.0),
        KpiDefinition(code="QUAL_QC_IN_CONTROL", name="QC In-Control Rate", category=KpiCategory.QUALITY, unit="%", target=95.0),
        KpiDefinition(code="QUAL_EQA_ACCEPTABLE", name="EQA Acceptable Rate", category=KpiCategory.QUALITY, unit="%", target=90.0),
        KpiDefinition(code="QUAL_ADVERSE_EVENTS", name="Adverse Events per 1000", category=KpiCategory.QUALITY, unit="per_1000", target=3.0, direction="lower_is_better"),
        KpiDefinition(code="SEC_AUDIT_COMPLETION", name="Audit Completion Rate", category=KpiCategory.SECURITY, unit="%", target=100.0),
    ]
    for kpi in default_kpis:
        if not svc.kpi_registry.get(kpi.code):
            svc.kpi_registry.register(kpi)
    logger.info("Default KPIs seeded: %d", len(default_kpis))


def seed_data_catalog(sdk: ResearchSDK | None = None) -> None:
    from app.health_data.enums import DataClassification, DataQuality

    svc = sdk or get_research_sdk()
    catalog_datasets = [
        ("clinical_encounters", "Clinical encounter records", DataClassification.CONFIDENTIAL, DataQuality.CURATED),
        ("lab_results", "Laboratory test results", DataClassification.CONFIDENTIAL, DataQuality.CURATED),
        ("lab_orders", "Laboratory order records", DataClassification.INTERNAL, DataQuality.VALIDATED),
        ("patient_demographics", "Patient demographic data", DataClassification.RESTRICTED, DataQuality.MASTER),
        ("population_stats", "Population health statistics", DataClassification.PUBLIC, DataQuality.ENRICHED),
        ("registry_cancer", "National cancer registry data", DataClassification.RESTRICTED, DataQuality.CURATED),
        ("registry_birth", "National birth registry data", DataClassification.CONFIDENTIAL, DataQuality.CURATED),
        ("registry_death", "National death registry data", DataClassification.CONFIDENTIAL, DataQuality.CURATED),
    ]
    for name, desc, classification, quality in catalog_datasets:
        if not svc.data_catalog.get(name):
            svc.data_catalog.register_dataset(
                name=name,
                description=desc,
                classification=classification,
                quality=quality,
                owner="NRAP",
                tags=["research", "national"],
            )
    logger.info("Data catalog seeded: %d datasets", len(catalog_datasets))


def initialize(app: FastAPI | None = None) -> ResearchSDK:
    sdk = get_research_sdk()
    seed_default_kpis(sdk)
    seed_data_catalog(sdk)
    if app is not None:
        register_routes(app)
    logger.info("National Research, Analytics & Population Health Intelligence Platform initialized")
    return sdk
