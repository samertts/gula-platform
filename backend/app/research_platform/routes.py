from __future__ import annotations

import logging
from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.health_data.warehouse.service import WarehouseQuery
from app.research_platform.kpi_engine import KpiDefinition
from app.research_platform.sdk import AnalyticsSDK, ResearchSDK

logger = logging.getLogger("gula.research_platform.routes")

router = APIRouter(prefix="/research", tags=["Research Platform"])

_sdk: ResearchSDK | None = None


def get_sdk() -> ResearchSDK:
    global _sdk
    if _sdk is None:
        _sdk = ResearchSDK()
    return _sdk


def get_db_session(db: Session = Depends(get_db)) -> Session:
    return db


# ── Research Projects ──────────────────────────────────────────────────────────


@router.get("/projects")
def list_projects(
    status: str | None = Query(None),
    institution_id: str | None = Query(None),
    sdk: ResearchSDK = Depends(get_sdk),
):
    return sdk.studies.list_projects(status=status, institution_id=institution_id)


@router.post("/projects")
def create_project(body: dict[str, Any], sdk: ResearchSDK = Depends(get_sdk)):
    return sdk.studies.create_project(
        title=body.get("title", ""),
        title_ar=body.get("title_ar", ""),
        description=body.get("description", ""),
        study_type=body.get("study_type"),
        principal_investigator=body.get("principal_investigator", ""),
        institution_id=body.get("institution_id", ""),
    )


@router.get("/projects/{project_id}")
def get_project(project_id: str, sdk: ResearchSDK = Depends(get_sdk)):
    project = sdk.studies.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


# ── Datasets ────────────────────────────────────────────────────────────────────


@router.get("/datasets")
def list_datasets(
    category: str | None = Query(None),
    sdk: ResearchSDK = Depends(get_sdk),
):
    return sdk.datasets.list(category=category)


@router.post("/datasets")
def register_dataset(body: dict[str, Any], sdk: ResearchSDK = Depends(get_sdk)):
    return sdk.datasets.register(
        name=body.get("name", ""),
        description=body.get("description", ""),
        category=body.get("category"),
        owner=body.get("owner", ""),
        tags=body.get("tags"),
    )


@router.get("/datasets/search")
def search_datasets(query: str, sdk: ResearchSDK = Depends(get_sdk)):
    return sdk.datasets.search(query)


# ── Institutions ────────────────────────────────────────────────────────────────


@router.get("/institutions")
def list_institutions(
    governorate: str | None = Query(None),
    sdk: ResearchSDK = Depends(get_sdk),
):
    return sdk.institutions.list(governorate=governorate)


@router.post("/institutions")
def register_institution(body: dict[str, Any], sdk: ResearchSDK = Depends(get_sdk)):
    return sdk.institutions.register(
        name=body.get("name", ""),
        name_ar=body.get("name_ar", ""),
        institution_type=body.get("institution_type", "university"),
        city=body.get("city", ""),
        governorate=body.get("governorate", ""),
        contact_email=body.get("contact_email", ""),
    )


# ── Publications ────────────────────────────────────────────────────────────────


@router.get("/publications")
def list_publications(
    project_id: str | None = Query(None),
    sdk: ResearchSDK = Depends(get_sdk),
):
    if project_id:
        return sdk.publications.list_by_project(project_id)
    return list(sdk.publications._publications.values())


@router.post("/publications")
def register_publication(body: dict[str, Any], sdk: ResearchSDK = Depends(get_sdk)):
    return sdk.publications.register(
        title=body.get("title", ""),
        authors=body.get("authors", []),
        journal=body.get("journal", ""),
        doi=body.get("doi", ""),
        pmid=body.get("pmid", ""),
        project_id=body.get("project_id", ""),
        publication_type=body.get("publication_type", "journal_article"),
        abstract=body.get("abstract", ""),
        keywords=body.get("keywords"),
    )


# ── Sandbox ─────────────────────────────────────────────────────────────────────


@router.post("/sandboxes")
def create_sandbox(body: dict[str, Any], sdk: ResearchSDK = Depends(get_sdk)):
    return sdk.sandbox.create(
        project_id=body.get("project_id", ""),
        name=body.get("name", ""),
        datasets=body.get("datasets"),
        max_records=body.get("max_records", 10000),
        retention_hours=body.get("retention_hours", 72),
    )


@router.delete("/sandboxes/{sandbox_id}")
def destroy_sandbox(sandbox_id: str, sdk: ResearchSDK = Depends(get_sdk)):
    if not sdk.sandbox.destroy(sandbox_id):
        raise HTTPException(status_code=404, detail="Sandbox not found")
    return {"status": "destroyed"}


# ── Population Health ───────────────────────────────────────────────────────────


@router.get("/population/disease-burden")
def disease_burden(
    icd10_codes: str | None = Query(None),
    governorate: str | None = Query(None),
    date_from: str | None = Query(None),
    date_to: str | None = Query(None),
    sdk: ResearchSDK = Depends(get_sdk),
):
    codes = icd10_codes.split(",") if icd10_codes else None
    return sdk.population.disease_burden(
        icd10_codes=codes,
        governorate=governorate,
        date_from=date.fromisoformat(date_from) if date_from else None,
        date_to=date.fromisoformat(date_to) if date_to else None,
    )


@router.get("/population/demographics")
def demographics(
    governorate: str | None = Query(None),
    sdk: ResearchSDK = Depends(get_sdk),
):
    return sdk.population.demographic_analysis(governorate=governorate)


@router.get("/population/ncd")
def ncd_statistics(
    condition: str | None = Query(None),
    governorate: str | None = Query(None),
    sdk: ResearchSDK = Depends(get_sdk),
):
    return sdk.ncd.diabetes_prevalence(governorate=governorate)


@router.get("/population/vaccination")
def vaccination_coverage(
    vaccine: str | None = Query(None),
    governorate: str | None = Query(None),
    sdk: ResearchSDK = Depends(get_sdk),
):
    return sdk.vaccination.coverage_rates(vaccine=vaccine, governorate=governorate)


# ── Epidemiology ────────────────────────────────────────────────────────────────


@router.get("/epidemiology/surveillance")
def surveillance(
    disease: str,
    region: str = "",
    window_days: int = 7,
    sdk: ResearchSDK = Depends(get_sdk),
):
    return sdk.surveillance.monitor_disease(disease, region, window_days)


@router.get("/epidemiology/outbreak-detection")
def outbreak_detection(
    disease: str,
    region: str = "",
    method: str = "cusum",
    sdk: ResearchSDK = Depends(get_sdk),
):
    if method == "cusum":
        return sdk.outbreak.cusum_alert(disease, region)
    return sdk.outbreak.moving_average_alert(disease, region)


@router.get("/epidemiology/trends")
def trends(
    metric: str,
    disease: str = "",
    region: str = "",
    granularity: str = "weekly",
    periods: int = 12,
    sdk: ResearchSDK = Depends(get_sdk),
):
    return sdk.trends.time_series(metric, disease, region, granularity, periods)


@router.get("/epidemiology/forecast")
def forecast(
    disease: str,
    region: str = "",
    horizon_weeks: int = 4,
    sdk: ResearchSDK = Depends(get_sdk),
):
    return sdk.forecasting.simple_forecast(disease, region, horizon_weeks)


@router.get("/epidemiology/early-warning")
def early_warning(
    disease: str,
    region: str = "",
    sdk: ResearchSDK = Depends(get_sdk),
):
    return sdk.early_warning.evaluate(disease, region)


# ── KPIs ────────────────────────────────────────────────────────────────────────


@router.get("/kpis")
def list_kpis(
    category: str | None = Query(None),
    sdk: ResearchSDK = Depends(get_sdk),
):
    return sdk.kpi_registry.list(category=category)


@router.post("/kpis")
def register_kpi(body: dict[str, Any], sdk: ResearchSDK = Depends(get_sdk)):
    kpi = KpiDefinition(
        code=body.get("code", ""),
        name=body.get("name", ""),
        name_ar=body.get("name_ar", ""),
        description=body.get("description", ""),
        category=body.get("category"),
        unit=body.get("unit", ""),
        target=body.get("target"),
        direction=body.get("direction", "higher_is_better"),
        frequency=body.get("frequency", "monthly"),
    )
    sdk.kpi_registry.register(kpi)
    return kpi


@router.get("/kpis/evaluate")
def evaluate_kpis(
    category: str | None = Query(None),
    sdk: ResearchSDK = Depends(get_sdk),
):
    if category:
        return sdk.kpi_engine.evaluate_category(category)
    return sdk.kpi_engine.evaluate_all()


@router.get("/kpis/dashboard")
def kpi_dashboard(
    category: str | None = Query(None),
    sdk: ResearchSDK = Depends(get_sdk),
):
    return sdk.kpi_dashboard.render(category=category)


# ── Dashboards ──────────────────────────────────────────────────────────────────


@router.get("/dashboards/executive")
def executive_dashboard(sdk: ResearchSDK = Depends(get_sdk)):
    return sdk.executive_dashboard.render()


@router.get("/dashboards/directorate/{directorate_id}")
def directorate_dashboard(directorate_id: str, sdk: ResearchSDK = Depends(get_sdk)):
    return sdk.directorate_dashboard.render(directorate_id)


@router.get("/dashboards/hospital/{hospital_id}")
def hospital_dashboard(hospital_id: str, sdk: ResearchSDK = Depends(get_sdk)):
    return sdk.hospital_dashboard.render(hospital_id)


@router.get("/dashboards/laboratory/{lab_id}")
def laboratory_dashboard(lab_id: str, sdk: ResearchSDK = Depends(get_sdk)):
    return sdk.lab_dashboard.render(lab_id)


@router.get("/dashboards/population")
def population_dashboard(
    region: str = "national",
    sdk: ResearchSDK = Depends(get_sdk),
):
    return sdk.population_dashboard.render(region)


# ── Registries ──────────────────────────────────────────────────────────────────


@router.get("/registries")
def list_registries(sdk: ResearchSDK = Depends(get_sdk)):
    return sdk.registries.count_by_type()


@router.get("/registries/{registry_type}")
def query_registry(
    registry_type: str,
    governorate: str | None = Query(None),
    diagnosis_code: str | None = Query(None),
    limit: int = 100,
    sdk: ResearchSDK = Depends(get_sdk),
):
    from app.research_platform.enums import RegistryType

    try:
        rt = RegistryType(registry_type)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid registry type: {registry_type}") from e
    return sdk.registries.query(rt, governorate=governorate, diagnosis_code=diagnosis_code, limit=limit)


# ── GIS ─────────────────────────────────────────────────────────────────────────


@router.get("/gis/heatmap")
def heatmap(
    metric: str,
    region: str = "",
    sdk: ResearchSDK = Depends(get_sdk),
):
    return sdk.heatmaps.generate(metric, region)


@router.get("/gis/hotspots")
def hotspots(
    disease: str,
    min_cases: int = 10,
    sdk: ResearchSDK = Depends(get_sdk),
):
    return sdk.hotspots.detect(disease, min_cases)


@router.get("/gis/facilities")
def list_facilities(
    governorate: str | None = Query(None),
    facility_type: str | None = Query(None),
    sdk: ResearchSDK = Depends(get_sdk),
):
    return sdk.gis.list_facilities(governorate=governorate, facility_type=facility_type)


# ── Data Science ────────────────────────────────────────────────────────────────


@router.post("/notebooks")
def create_notebook(body: dict[str, Any], sdk: ResearchSDK = Depends(get_sdk)):
    return sdk.notebooks.create(
        name=body.get("name", ""),
        kernel=body.get("kernel", "python3"),
        dependencies=body.get("dependencies"),
    )


@router.post("/experiments")
def create_experiment(body: dict[str, Any], sdk: ResearchSDK = Depends(get_sdk)):
    return sdk.experiments.create_experiment(
        name=body.get("name", ""),
        description=body.get("description", ""),
        tags=body.get("tags"),
    )


@router.post("/experiments/{experiment_id}/runs")
def log_run(
    experiment_id: str,
    body: dict[str, Any],
    sdk: ResearchSDK = Depends(get_sdk),
):
    run_id = sdk.experiments.log_run(
        experiment_id=experiment_id,
        run_name=body.get("run_name", ""),
        params=body.get("params"),
        metrics=body.get("metrics"),
    )
    return {"run_id": run_id}


# ── Privacy ──────────────────────────────────────────────────────────────────────


@router.post("/privacy/deidentify")
def deidentify(
    body: dict[str, Any],
    sdk: ResearchSDK = Depends(get_sdk),
):
    records = body.get("records", [])
    phi_fields = body.get("phi_fields")
    return {"deidentified_records": sdk.deid.deidentify_batch(records, phi_fields)}


@router.post("/privacy/pseudonymize")
def pseudonymize(
    body: dict[str, Any],
    sdk: ResearchSDK = Depends(get_sdk),
):
    records = body.get("records", [])
    fields = body.get("fields")
    return {"pseudonymized_records": sdk.pseudonymization.pseudonymize_batch(records, fields)}


@router.post("/privacy/consent")
def record_consent(body: dict[str, Any], sdk: ResearchSDK = Depends(get_sdk)):
    return sdk.consent.record_consent(
        patient_ulid=body.get("patient_ulid", ""),
        project_id=body.get("project_id", ""),
        scope=body.get("scope"),
        status=body.get("status", "granted"),
    )


@router.post("/privacy/approvals")
def submit_approval(body: dict[str, Any], sdk: ResearchSDK = Depends(get_sdk)):
    return sdk.approvals.submit(
        project_id=body.get("project_id", ""),
        researcher_id=body.get("researcher_id", ""),
        purpose=body.get("purpose", ""),
    )


@router.post("/privacy/ethics-review")
def submit_ethics_review(body: dict[str, Any], sdk: ResearchSDK = Depends(get_sdk)):
    return sdk.ethics.submit_for_review(
        project_id=body.get("project_id", ""),
        protocol_document=body.get("protocol_document", ""),
        researcher_id=body.get("researcher_id", ""),
    )


# ── Data Lake ────────────────────────────────────────────────────────────────────


@router.get("/data-lake/catalog")
def list_data_catalog(
    pattern: str | None = Query(None),
    sdk: ResearchSDK = Depends(get_sdk),
):
    return sdk.data_catalog.list(pattern=pattern)


@router.get("/data-lake/lineage/{dataset}")
def get_lineage(dataset: str, sdk: ResearchSDK = Depends(get_sdk)):
    return sdk.lineage.trace(dataset)


@router.get("/data-lake/versions/{dataset}")
def get_versions(dataset: str, sdk: ResearchSDK = Depends(get_sdk)):
    return sdk.versioning.list_versions(dataset)


# ── Search ────────────────────────────────────────────────────────────────────────


@router.get("/search")
def search_resources(
    query: str,
    sdk: ResearchSDK = Depends(get_sdk),
):
    return sdk.search_resources(query)


# ── SDK direct access ────────────────────────────────────────────────────────────


@router.get("/analytics/tables")
def list_analytics_tables(sdk: ResearchSDK = Depends(get_sdk)):
    analytics_sdk = AnalyticsSDK()
    return {
        "facts": analytics_sdk.list_fact_tables(),
        "dimensions": analytics_sdk.list_dimension_tables(),
    }


@router.post("/analytics/query")
def query_analytics(body: dict[str, Any], sdk: ResearchSDK = Depends(get_sdk)):
    wq = WarehouseQuery(
        dimensions=body.get("dimensions", []),
        measures=body.get("measures", []),
        filters=body.get("filters", {}),
        group_by=body.get("group_by", []),
        limit=body.get("limit", 100),
        offset=body.get("offset", 0),
    )
    analytics_sdk = AnalyticsSDK()
    return analytics_sdk.query_warehouse(wq)
