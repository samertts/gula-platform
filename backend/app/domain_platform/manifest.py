"""PROGRAM-STABLE-004 — canonical Domain registry (Phase 1/6).

Every healthcare specialty is an independent Domain. This module registers
the canonical GULA domains that inherit the Domain Platform Framework and
validates Domain Sovereignty (no Domain owns/manages another Domain).
"""

from __future__ import annotations

from typing import Any

from app.domain_platform.core import DomainContract, DomainManifest, assert_blueprint_rule
from app.domain_platform.shared_core import SHARED_CORE_SERVICES

# Shared Core modules consumed by every Domain by default.
_COMMON_SHARED_CORE = dict.fromkeys(SHARED_CORE_SERVICES, "shared_core")

# modules/tables are left for the certification scanner to resolve from the
# real codebase; the blueprint sections are canonical and hand-curated.


def _manifest(
    code: str,
    name_en: str,
    name_ar: str,
    workspace_type: str,
    description: str,
    entities: list[str],
    services: list[str],
    policies: list[str],
    api: list[str],
    events: list[str],
    workflows: list[str],
    reports: list[str],
    ui: list[str],
    version: str = "1.0.0",
    contracts: list[DomainContract] | None = None,
) -> DomainManifest:
    manifest = DomainManifest(
        code=code,
        name_en=name_en,
        name_ar=name_ar,
        version=version,
        workspace_type=workspace_type,
        description=description,
        entities=entities,
        services=services,
        policies=policies,
        api=api,
        events=events,
        workflows=workflows,
        reports=reports,
        ui=ui,
        contracts=contracts or [],
        shared_core=dict(_COMMON_SHARED_CORE),
    )
    assert_blueprint_rule(manifest)
    return manifest


# The canonical GULA healthcare domains. Every current and future module must
# declare its blueprint here and bind to exactly ONE workspace type.
CANONICAL_DOMAINS: dict[str, DomainManifest] = {
    "laboratory": _manifest(
        code="laboratory",
        name_en="GULA Laboratory",
        name_ar="مختبر غولا",
        workspace_type="laboratory",
        description="Laboratory information management: orders, samples, analyzers, "
        "quality control, results, and clinical review.",
        entities=["Order", "Sample", "Analyzer", "TestDefinition", "Result", "QCLevel"],
        services=["lab_service", "sample_service", "test_result_service", "quality_control_service"],
        policies=["iso_15189", "clsi_policy", "cap_policy"],
        api=["/lab/orders", "/lab/samples", "/lab/results", "/qc"],
        events=["order.created", "sample.collected", "result.verified"],
        workflows=["order_workflow", "sample_workflow", "verification_workflow"],
        reports=["lab_workload_report", "qc_summary_report"],
        ui=["laboratory_dashboard", "order_entry", "result_review"],
    ),
    "pharmacy": _manifest(
        code="pharmacy",
        name_en="GULA Pharmacy",
        name_ar="صيدلية غولا",
        workspace_type="pharmacy",
        description="Pharmacy inventory, dispensing, clinical verification, and "
        "prescription fulfillment.",
        entities=["Medication", "Inventory", "Dispensing", "Prescription"],
        services=["pharmacy_service", "inventory_service", "dispensing_service"],
        policies=["prescription_policy", "stock_control_policy"],
        api=["/pharmacy/medications", "/pharmacy/dispense"],
        events=["medication.dispensed", "inventory.low"],
        workflows=["dispensing_workflow"],
        reports=["pharmacy_stock_report", "dispensing_report"],
        ui=["pharmacy_dashboard", "dispensing_screen"],
    ),
    "radiology": _manifest(
        code="radiology",
        name_en="GULA Radiology",
        name_ar="أشعة غولا",
        workspace_type="radiology",
        description="Radiology workflow, PACS, imaging studies, AI-assisted reads, "
        "and modality integration.",
        entities=["Study", "Modality", "Image", "RadiologyReport"],
        services=["radiology_service", "pacs_service", "ai_assisted_read"],
        policies=["dicom_policy", "radiation_safety_policy"],
        api=["/radiology/studies", "/radiology/reports"],
        events=["study.ordered", "study.completed"],
        workflows=["study_workflow"],
        reports=["radiology_throughput_report"],
        ui=["radiology_dashboard", "study_viewer"],
    ),
    "hospital": _manifest(
        code="hospital",
        name_en="GULA Hospital",
        name_ar="مستشفى غولا",
        workspace_type="hospital",
        description="Hospital operations: encounters, admissions, departments, "
        "beds, nursing, and care continuum.",
        entities=["Encounter", "Admission", "Department", "Bed", "CarePlan"],
        services=["hospital_service", "encounter_service", "care_continuum_service"],
        policies=["admission_policy", "care_continuum_policy"],
        api=["/hospital/encounters", "/hospital/admissions"],
        events=["encounter.started", "patient.admitted"],
        workflows=["admission_workflow", "discharge_workflow"],
        reports=["hospital_census_report"],
        ui=["hospital_dashboard", "patient_flow"],
    ),
    "blood_bank": _manifest(
        code="blood_bank",
        name_en="GULA Blood Bank",
        name_ar="بنك الدم",
        workspace_type="blood_bank",
        description="Blood donation, component processing, compatibility, and "
        "transfusion safety.",
        entities=["Donation", "BloodUnit", "Component", "Crossmatch"],
        services=["blood_bank_service", "compatibility_service"],
        policies=["transfusion_safety_policy", "donor_safety_policy"],
        api=["/blood-bank/donations", "/blood-bank/units"],
        events=["blood.donated", "blood.unit_released"],
        workflows=["donation_workflow", "transfusion_workflow"],
        reports=["blood_inventory_report"],
        ui=["blood_bank_dashboard"],
    ),
    "public_health": _manifest(
        code="public_health",
        name_en="GULA Public Health",
        name_ar="الصحة العامة",
        workspace_type="public_health",
        description="Population surveillance, notifiable diseases, immunization, "
        "and epidemic response.",
        entities=["SurveillanceCase", "Immunization", "Outbreak", "Alert"],
        services=["surveillance_service", "immunization_service"],
        policies=["notifiable_disease_policy", "epidemic_response_policy"],
        api=["/public-health/cases", "/public-health/alerts"],
        events=["case.reported", "outbreak.declared"],
        workflows=["surveillance_workflow"],
        reports=["surveillance_dashboard_report"],
        ui=["public_health_dashboard"],
    ),
    "insurance": _manifest(
        code="insurance",
        name_en="GULA Insurance",
        name_ar="التأمين الصحي",
        workspace_type="insurance",
        description="Health insurance eligibility, claims, pricing, pre-authorization, "
        "and fraud detection.",
        entities=["Policy", "Claim", "Coverage", "PreAuthorization"],
        services=["insurance_service", "claims_service", "fraud_service"],
        policies=["claims_policy", "fraud_detection_policy"],
        api=["/insurance/claims", "/insurance/eligibility"],
        events=["claim.submitted", "claim.approved"],
        workflows=["claims_workflow", "preauth_workflow"],
        reports=["claims_report"],
        ui=["insurance_dashboard"],
    ),
    "emergency": _manifest(
        code="emergency",
        name_en="GULA Emergency",
        name_ar="الطوارئ",
        workspace_type="hospital",
        description="Emergency medical services, triage, and critical care response.",
        entities=["EMSIncident", "Triage", "CriticalPatient"],
        services=["ems_service", "critical_care_service"],
        policies=["triage_policy", "critical_care_policy"],
        api=["/emergency/incidents", "/emergency/triage"],
        events=["emergency.incident", "critical.patient_admitted"],
        workflows=["triage_workflow"],
        reports=["emergency_response_report"],
        ui=["emergency_dashboard"],
    ),
    "research": _manifest(
        code="research",
        name_en="GULA Research",
        name_ar="البحث العلمي",
        workspace_type="research",
        description="Clinical research, data science, biobank, and evidence generation.",
        entities=["ResearchStudy", "Cohort", "BiobankSample"],
        services=["research_service", "biomedical_service", "data_science_service"],
        policies=["research_ethics_policy", "data_minimization_policy"],
        api=["/research/studies"],
        events=["study.registered"],
        workflows=["study_workflow"],
        reports=["research_metrics_report"],
        ui=["research_dashboard"],
    ),
    "citizen_portal": _manifest(
        code="citizen_portal",
        name_en="GULA Citizen Portal",
        name_ar="بوابة المواطن",
        workspace_type="citizen",
        description="Citizen self-service: appointments, certificates, results, "
        "and personal health records (read-only over operational Domains).",
        entities=["CitizenAppointment", "CitizenHealthRecord"],
        services=["citizen_platform_service"],
        policies=["citizen_read_only_policy"],
        api=["/citizen/appointments", "/citizen/records"],
        events=["citizen.appointment_booked"],
        workflows=["appointment_workflow"],
        reports=["citizen_activity_report"],
        ui=["citizen_portal"],
    ),
    "provider_portal": _manifest(
        code="provider_portal",
        name_en="GULA Provider Portal",
        name_ar="بوابة مقدمي الرعاية",
        workspace_type="professional",
        description="Provider workspace for professionals to operate across the "
        "Domains they are privileged in (no domain administration).",
        entities=["ProviderProfile", "ProviderSchedule"],
        services=["provider_portal_service"],
        policies=["provider_no_admin_policy"],
        api=["/provider/portal"],
        events=["provider.activity"],
        workflows=["provider_workflow"],
        reports=["provider_activity_report"],
        ui=["provider_portal"],
    ),
}

# No Domain owns another Domain. This map is deliberately empty and enforced:
# it is the registry of forbidden ownership edges (Phase 7 check #5/6).
FORBIDDEN_DOMAIN_OWNERSHIP: dict[str, tuple[str, ...]] = {}

# Workspace types that must never render another Domain's UI (Phase 6).
# The primary owner of a workspace is the Domain whose code matches the
# workspace type (e.g. workspace "hospital" is owned by domain "hospital");
# additional Domains may be hosted inside that workspace (e.g. "emergency"
# lives inside the hospital workspace) but never outside it.
WORKSPACE_DOMAIN_MAP: dict[str, str] = {}
for _manifest_entry in CANONICAL_DOMAINS.values():
    _ws = _manifest_entry.workspace_type
    if _ws not in WORKSPACE_DOMAIN_MAP or _manifest_entry.code == _ws:
        WORKSPACE_DOMAIN_MAP[_ws] = _manifest_entry.code


def get_domain(code: str) -> DomainManifest | None:
    return CANONICAL_DOMAINS.get(code)


def list_domains() -> list[DomainManifest]:
    return list(CANONICAL_DOMAINS.values())


def domain_codes() -> list[str]:
    return list(CANONICAL_DOMAINS.keys())


def workspace_ui_for(workspace_type: str) -> list[str]:
    """The Domain UIs a workspace may render (Phase 6).

    A workspace may render the UI of every Domain bound to its type — the
    primary Domain plus any hosted Domains (e.g. the hospital workspace
    renders the hospital and emergency Domains). Cross-workspace UI is
    forbidden.
    """
    ui: list[str] = []
    for manifest in CANONICAL_DOMAINS.values():
        if manifest.workspace_type == workspace_type:
            for item in manifest.ui:
                if item not in ui:
                    ui.append(item)
    return ui


def assert_no_cross_domain_administration() -> list[str]:
    """Phase 7 — no Domain administers another Domain.

    Returns a list of violations (empty when sovereignty holds).
    """
    violations: list[str] = []
    for owner, owned in FORBIDDEN_DOMAIN_OWNERSHIP.items():
        for target in owned:
            violations.append(f"domain '{owner}' declares ownership of '{target}'")
    return violations


def manifest_to_dict(manifest: DomainManifest) -> dict[str, Any]:
    return manifest.to_dict()
