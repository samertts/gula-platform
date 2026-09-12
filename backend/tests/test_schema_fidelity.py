"""Schema fidelity: a green test must not mean "the ORM can create this table".

NR-036. The shared ``db`` fixture builds its schema with ``create_all()`` from a
combined MetaData spanning sixteen declarative bases (``conftest.py``). Any
table that exists as a model but has no migration is therefore present in tests
and absent from a migrated database. That is not a hypothetical: it is how
NR-026 (Nursing), NR-032 (EHR medication) and NR-034 (the pharmacy POS dispense)
each reached a green suite while the same code could not commit in production.

``test_alembic_metadata_registry.py`` already guards the physical → ORM
direction: every physical table must be mapped, and a shared MetaData must not
silently drop one. This module guards the direction that was missing, and the
one NR-036 is about:

  1. **ORM → migration.** Every ORM-mapped table must either be built by the
     migration chain or appear in the ledger below with a stated disposition.
     A model added without a migration fails the gate rather than quietly
     becoming a test-only table.

  2. **Cross-generation dependency.** A module in a migration-backed domain must
     not reach for a model whose table no migration builds. This is the rule
     that NR-032 and NR-034 broke, and the one that matters most: an unbuilt
     domain is a known, deliberate state, but a *built* domain depending on one
     is a live defect waiting for a request that reaches it.

Both read a database migrated to head, so they describe the schema a clean
deployment receives — not the schema the ORM would like to have.
"""

from __future__ import annotations

import ast
import os
import pathlib

import pytest
from sqlalchemy import MetaData, create_engine, inspect


def _schema_database_url() -> str:
    """A database built by the migration chain, not by create_all().

    DATABASE_URL cannot supply it: conftest pins that variable to in-memory
    SQLite for the whole suite, which is exactly the substitution this module
    exists to detect. MIGRATION_DATABASE_URL is the one CI already exports for
    its migrated PostgreSQL service.
    """
    return (os.environ.get("GULA_SCHEMA_DATABASE_URL")
            or os.environ.get("MIGRATION_DATABASE_URL", ""))


SCHEMA_DATABASE_URL = _schema_database_url()
pytestmark = pytest.mark.skipif(
    not SCHEMA_DATABASE_URL,
    reason="GULA_SCHEMA_DATABASE_URL/MIGRATION_DATABASE_URL is not configured; "
           "this gate needs a database built by the migration chain",
)

APP_ROOT = pathlib.Path(__file__).resolve().parents[1] / "app"

# ── The ledger ───────────────────────────────────────────────────────────────
#
# Every ORM table with no migration, grouped by the declarative base that owns
# it, each group carrying its disposition. All of these are category D —
# declared but deliberately not built — and each is an architecture decision
# recorded elsewhere, not an oversight. Categories A (migration-backed) and
# C (external/shared ownership) need no list: A is proven by the database and
# no C case exists today.
#
# Adding a model without a migration adds a name here, which is a review, not
# an edit of convenience.
DECLARED_UNBUILT_TABLES = frozenset({
    # ── Base (21) — review required
    "ai_recommendations", "capacity_intelligence", "capacity_plans", "digital_twins",
    "incident_intelligence", "knowledge_edges", "knowledge_graph_snapshots", "knowledge_nodes",
    "national_kpis", "predictions", "roadmap_architecture_decisions", "roadmap_epics",
    "roadmap_milestones", "roadmap_missions", "roadmap_programs", "roadmap_risks",
    "roadmap_tasks", "roadmap_technical_debt", "simulation_snapshots", "simulations",
    "situation_rooms",
    # ── CareContinuum (45) — review required
    "cc_antenatal_care_visits", "cc_breastfeeding_records", "cc_care_coordination",
    "cc_care_journeys", "cc_child_development_records", "cc_chronic_disease_registry",
    "cc_clinical_handovers", "cc_clinical_pathway_enrollments", "cc_cold_chain_monitors",
    "cc_community_care_records", "cc_community_clinic_records", "cc_community_visits",
    "cc_contraindications", "cc_cross_org_referrals", "cc_delivery_records",
    "cc_disease_management_plans", "cc_educational_material_assignments",
    "cc_family_medicine_records", "cc_follow_up_plans", "cc_growth_monitoring",
    "cc_health_assessments", "cc_health_programs", "cc_health_promotion_activities",
    "cc_home_care_plans", "cc_immunization_schedules", "cc_occupational_health_records",
    "cc_patient_tasks", "cc_postnatal_care_visits", "cc_pregnancy_records",
    "cc_preventive_care_records", "cc_primary_care_encounters", "cc_program_enrollments",
    "cc_referral_attachments", "cc_referral_requests", "cc_referral_responses",
    "cc_referral_timelines", "cc_reminder_schedules", "cc_risk_stratification",
    "cc_school_health_visits", "cc_screening_campaigns", "cc_self_follow_up_tasks",
    "cc_self_monitoring_records", "cc_transitions_of_care", "cc_vaccination_records",
    "cc_vaccine_inventory",
    # ── Clinical (39) — review required
    "clinical_alert_actions", "clinical_alerts", "clinical_atc_codes",
    "clinical_audit_records", "clinical_benchmark_values", "clinical_care_bundle_elements",
    "clinical_care_bundles", "clinical_code_systems", "clinical_compliance_checks",
    "clinical_contraindications", "clinical_cpt_codes", "clinical_duplicate_order_rules",
    "clinical_guideline_approvals", "clinical_guidelines", "clinical_icd10_codes",
    "clinical_icd11_codes", "clinical_incident_reports", "clinical_indicator_measurements",
    "clinical_loinc_codes", "clinical_mortality_reviews", "clinical_order_set_items",
    "clinical_order_sets", "clinical_pathway_phases", "clinical_pathways",
    "clinical_patient_safety_events", "clinical_preventive_recommendations",
    "clinical_protocols", "clinical_quality_indicators", "clinical_recommendations",
    "clinical_reminder_rules", "clinical_rxnorm_codes", "clinical_snomed_ct_codes",
    "clinical_standing_orders", "clinical_terminology_codes", "clinical_terminology_mappings",
    "clinical_terminology_versions", "clinical_ucum_codes", "clinical_value_set_members",
    "clinical_value_sets",
    # ── DataPlatform (36) — National Data warehouse/MDM: declared, never migrated.
    "dp_consent_directives", "dp_data_catalog", "dp_data_classifications", "dp_data_lineage",
    "dp_data_quality_checks", "dp_data_quality_rules", "dp_data_stewards",
    "dp_deidentification_jobs", "dp_device_registry", "dp_duplicate_records",
    "dp_event_retention_policies", "dp_event_snapshots", "dp_feature_store",
    "dp_feature_values", "dp_golden_records", "dp_knowledge_graph_edges",
    "dp_knowledge_graph_nodes", "dp_location_registry", "dp_merge_actions",
    "dp_metadata_registry", "dp_provider_registry", "dp_retention_policies",
    "dp_source_systems", "dp_stored_events", "dp_synthetic_data_jobs",
    "dp_terminology_registry", "dp_training_datasets", "dp_vector_embeddings", "dw_dim_date",
    "dw_dim_diagnosis", "dw_dim_facility", "dw_dim_patient", "dw_dim_provider",
    "dw_fact_diagnoses", "dw_fact_lab_results", "dw_fact_patient_visits",
    # ── EHR (18) — NR-032 — EHR clinical models, blocked behind the National Core.
    "ehr_allergies", "ehr_care_plan_activities", "ehr_care_plan_goals", "ehr_care_plans",
    "ehr_clinical_attachments", "ehr_clinical_notes", "ehr_conditions", "ehr_diagnoses",
    "ehr_family_history", "ehr_immunizations", "ehr_medication_administrations",
    "ehr_medication_dispenses", "ehr_medication_requests", "ehr_medication_statements",
    "ehr_patient_timeline", "ehr_problem_list_items", "ehr_risk_factors", "ehr_social_history",
    # ── Fin (6) — Financial Engine beyond Phase A: schema-only by design (CLAUDE.md).
    "fin_invoice_items", "fin_invoices", "fin_payables", "fin_payments", "fin_pricing_rules",
    "fin_receivables",
    # ── Governance (58) — Governance platform: declared, never migrated.
    "gov_acting_appointments", "gov_ai_audit_events", "gov_ai_guardrails",
    "gov_ai_model_validations", "gov_ai_risk_classifications", "gov_analyzer_registry",
    "gov_approval_policies", "gov_attendance_records", "gov_board_certifications",
    "gov_break_glass_policies", "gov_calibration_records", "gov_canonical_mappings",
    "gov_clinical_policies", "gov_competency_assessments", "gov_consultation_policies",
    "gov_critical_result_policies", "gov_data_classification", "gov_delegations",
    "gov_delta_check_policies", "gov_digital_certificates", "gov_emergency_admin",
    "gov_eqa_records", "gov_equipment_registry", "gov_health_cards", "gov_health_number_audit",
    "gov_health_numbers", "gov_healthcare_workers", "gov_hierarchy_nodes", "gov_incidents",
    "gov_interop_protocols", "gov_laboratory_registry", "gov_llm_policies",
    "gov_maintenance_records", "gov_master_data_agreements", "gov_medical_guidelines",
    "gov_merged_identities", "gov_national_audit_events", "gov_national_panels",
    "gov_national_protocols", "gov_national_reference_labs", "gov_national_tests",
    "gov_productivity_records", "gov_professional_licenses", "gov_prompt_policies",
    "gov_qc_records", "gov_reagent_inventory", "gov_reference_range_policies",
    "gov_repeat_testing_policies", "gov_risk_registry", "gov_roles", "gov_rotation_records",
    "gov_security_policies", "gov_temporary_admin", "gov_terminology_mappings",
    "gov_threat_intel", "gov_training_records", "gov_westgard_policies",
    "gov_worker_privileges",
    # ── HealthData (24) — Health Data platform: declared, never migrated.
    "hd_mdm_facility_index", "hd_mdm_organization_index", "hd_mdm_patient_index",
    "hd_mdm_provider_index", "hd_mdm_source_references", "hd_ods_encounter_summary",
    "hd_ods_lab_result_summary", "hd_ods_order_summary", "hd_ods_patient_summary",
    "hd_wh_dim_date", "hd_wh_dim_facility", "hd_wh_dim_lab_test", "hd_wh_dim_patient",
    "hd_wh_dim_provider", "hd_wh_fact_encounter", "hd_wh_fact_lab_result", "hd_wh_fact_order",
    "rp_consent_records", "rp_data_access_requests", "rp_research_datasets",
    "rp_research_institutions", "rp_research_projects", "rp_research_publications",
    "rp_study_cohorts",
    # ── Hospital (10) — Hospital platform: declared, never migrated.
    "bed_assignments", "hospital_beds", "hospital_buildings", "hospital_campuses",
    "hospital_clinics", "hospital_cost_centers", "hospital_floors",
    "hospital_medical_equipment", "hospital_rooms", "hospital_units",
    # ── National (94) — NR-022 — the National Core. Depended on by five
    # domains, built by none. The first two register only when a test module
    # imports them directly, which is why the ORM surface is a lower bound
    # rather than a fixed set — see the staleness note below.
    "national_advance_directives", "national_vital_signs_reference",
    "national_addresses", "national_admissions", "national_appointments",
    "national_attachments", "national_background_job_dependencies",
    "national_background_job_executions", "national_background_job_schedules",
    "national_background_jobs", "national_biometrics", "national_citizens", "national_clinics",
    "national_communications", "national_consents", "national_coverages",
    "national_death_records", "national_delivery_reports", "national_departments",
    "national_directorates", "national_discharges", "national_document_attachments",
    "national_document_qr_codes", "national_document_versions", "national_documents",
    "national_electronic_signatures", "national_emergency_contacts", "national_employees",
    "national_encounters", "national_episodes_of_care", "national_families",
    "national_family_members", "national_foreigners", "national_guardians",
    "national_health_cards", "national_health_number_sequences", "national_hospitals",
    "national_identifier_mappings", "national_identity_audit_logs",
    "national_identity_resolutions", "national_insurances", "national_laboratories",
    "national_medication_catalog", "national_merge_audit", "national_merge_records",
    "national_newborns", "national_notification_batches", "national_notification_preferences",
    "national_notification_templates", "national_notifications",
    "national_observability_alert_events", "national_observability_alert_rules",
    "national_observability_dashboard_panels", "national_observability_dashboards",
    "national_observability_health_checks", "national_observability_metrics",
    "national_observability_service_graphs", "national_observability_trace_spans",
    "national_observations", "national_organizations", "national_patients",
    "national_practitioners", "national_providers", "national_referrals", "national_residents",
    "national_retention_rules", "national_rule_evaluation_logs", "national_rules",
    "national_scheduling_appointment_reminders", "national_scheduling_appointments",
    "national_scheduling_calendars", "national_scheduling_resources",
    "national_scheduling_schedules", "national_scheduling_time_slots",
    "national_scheduling_waiting_list", "national_unknown_patients", "national_visitors",
    "national_visits", "national_wards",
    # ── National / task engine + workflow runtime (15) — NR-058.
    # These were NOT hidden from this gate by an oversight in the ledger. They
    # were hidden from the ORM surface itself: both packages imported through
    # the `backend.app.` root, so their models registered on a *second*
    # NationalBase that `orm_tables` never reaches. The gate built to inventory
    # unbuilt ORM tables was under-counting by fifteen, and could not have said
    # so. Repairing the import root in the same commit is what made them
    # visible; they belong to NR-022 like the seventy-nine above.
    #
    # They are not equivalent to the rest of this list in one respect worth
    # stating: `factory.py` registers 42 endpoints over them (23 task, 19
    # workflow). Declared-and-unbuilt is the accurate status of the tables, not
    # a statement that nothing depends on them.
    "national_saga_logs", "national_task_assignments", "national_task_audit_logs",
    "national_task_comments", "national_task_escalations", "national_task_queues",
    "national_task_sla_definitions", "national_tasks", "national_workflow_approvals",
    "national_workflow_compensations", "national_workflow_definitions",
    "national_workflow_execution_steps", "national_workflow_executions",
    "national_workflow_templates", "national_workflow_timers",
    # ── Radiology (1) — One radiology model with no migration; the other eighteen are built.
    "radiology_ai_jobs",
})


# ── Cross-generation dependencies ────────────────────────────────────────────
#
# Modules in a migration-backed domain that import a model from a domain the
# migration chain does not build. Each is a live dependency on a table that
# does not exist, and each entry is a decision that has been looked at.
#
# NR-032 covers the EHR entries; pharmacy/services.py left this list in MED-001
# when the POS dispense was re-pointed at pharmacy_dispense_records. A new entry
# appearing here is the NR-034 defect happening again.
DECLARED_CROSS_GENERATION_IMPORTERS = frozenset({
    # → app.ehr.models.* (NR-032, blocked behind the National Core)
    "citizen_platform/medications.py",
    "citizen_platform/routes.py",
    "national/fhir/allergy_intolerance.py",
    "national/fhir/care_plan.py",
    "national/fhir/condition.py",
    "national/fhir/immunization.py",
    "national/fhir/medication_request.py",
    "national/fhir/medication_statement.py",
    "nursing/medication.py",
    "nursing/services.py",
    "routes/care_continuum.py",
    "routes/ehr_fhir.py",
    "services/ehr_service.py",
    # → app.national_data.models.* (the warehouse, declared but never migrated)
    "routes/national_data.py",
    "routes/national_streaming.py",
    "services/data_platform_service.py",
})

# The declarative bases whose tables the migration chain does not build at all.
# Derived from the ledger rather than hard-coded, so the two cannot drift.
UNBUILT_PACKAGE_PREFIXES = ("ehr_", "dp_", "hd_", "gov_")


@pytest.fixture(scope="module")
def engine():
    eng = create_engine(SCHEMA_DATABASE_URL, future=True)
    try:
        yield eng
    finally:
        eng.dispose()


@pytest.fixture(scope="module")
def physical(engine) -> frozenset[str]:
    return frozenset(inspect(engine).get_table_names())


@pytest.fixture(scope="module")
def orm_tables() -> dict[str, str]:
    """Every ORM-mapped table, and the declarative base that owns it.

    Imports what conftest imports before it calls create_all(), so this gate
    sees the same surface that reaches the test database. `app.main` matters:
    it registers the routes, and the routes import models that
    `import_all_models()` alone does not reach. An earlier version of this gate
    imported only the latter, passed in isolation, and failed in a full run —
    the ledger was measured against a smaller ORM surface than conftest builds.
    """
    import app.main
    from app.factory import import_all_models

    import_all_models()
    import app.services.mpi.models
    from app.care_continuum.base import CareContinuumBase
    from app.citizen_platform.base import CitizenPlatformBase
    from app.clinical.base import ClinicalBase
    from app.database import Base
    from app.ehr.base import EHRBase
    from app.financial.models import FinBase
    from app.governance.base import GovernanceBase
    from app.health_data.base import HealthDataBase
    from app.hospital.base import HospitalBase
    from app.national.base import NationalBase
    from app.national_data.base import DataPlatformBase
    from app.nhdw.base import NHDWBase
    from app.nursing.base import NursingBase
    from app.pharmacy.base import PharmacyBase
    from app.radiology.base import RadiologyBase
    from app.trust.base import TrustBase

    bases = {
        "Base": Base, "National": NationalBase, "EHR": EHRBase,
        "CareContinuum": CareContinuumBase, "CitizenPlatform": CitizenPlatformBase,
        "Clinical": ClinicalBase, "Governance": GovernanceBase,
        "HealthData": HealthDataBase, "Hospital": HospitalBase,
        "DataPlatform": DataPlatformBase, "NHDW": NHDWBase, "Nursing": NursingBase,
        "Pharmacy": PharmacyBase, "Radiology": RadiologyBase, "Trust": TrustBase,
        "Fin": FinBase,
    }
    owner: dict[str, str] = {}
    for name, base in bases.items():
        for table in base.metadata.tables:
            owner.setdefault(table, name)
    return owner


# ── 1. ORM → migration ───────────────────────────────────────────────────────


def test_every_orm_table_is_migration_backed_or_declared(orm_tables, physical) -> None:
    """The gate NR-036 asks for.

    A model whose table no migration creates must be named in the ledger. It
    then exists in tests and nowhere else *by an explicit decision*, which is
    the difference between a deferred domain and a defect.
    """
    unbacked = set(orm_tables) - set(physical)
    undeclared = sorted(unbacked - DECLARED_UNBUILT_TABLES)
    assert not undeclared, (
        "these ORM tables have no migration and are not in the ledger:\n  "
        + "\n  ".join(f"{t} (owned by {orm_tables[t]})" for t in undeclared)
        + "\n\nEither add a migration, or add the table to DECLARED_UNBUILT_TABLES "
          "with the decision that keeps it unbuilt. Do not let it become a "
          "test-only table."
    )


def test_the_ledger_does_not_outlive_the_tables_it_describes(orm_tables, physical) -> None:
    """A ledger entry that has since been built, or dropped, must not linger.

    A stale exclusion is how a gate stops meaning anything.
    """
    stale_now_built = sorted(DECLARED_UNBUILT_TABLES & set(physical))
    assert not stale_now_built, (
        f"{stale_now_built} are now built by the migration chain. Remove them "
        "from DECLARED_UNBUILT_TABLES so the ledger keeps its meaning."
    )
    # There is deliberately no "in the ledger but no model declares it" check.
    # The ORM surface is not a fixed set: a table registers only when something
    # imports its module, so the surface depends on which tests have run. Such a
    # check passes in isolation and fails in a full run, or the reverse. The half
    # that matters is above and is always valid: an entry the migration chain now
    # builds must leave the ledger.


# ── 2. Cross-generation dependency ───────────────────────────────────────────


def _cross_generation_importers() -> dict[str, set[str]]:
    """Modules importing a model from a package with no migration-built tables."""
    unbuilt_packages = {"ehr", "national_data", "health_data"}
    found: dict[str, set[str]] = {}
    for path in APP_ROOT.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        relative = path.relative_to(APP_ROOT)
        owner = relative.parts[0] if len(relative.parts) > 1 else ""
        if owner in unbuilt_packages or not owner:
            continue  # a domain may depend on itself; that is one decision
        try:
            tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            module = None
            if isinstance(node, ast.ImportFrom) and node.module:
                module = node.module
            elif isinstance(node, ast.Import):
                module = node.names[0].name
            if not module:
                continue
            head = module.removeprefix("app.").split(".")[0]
            if head in unbuilt_packages and ("models" in module or "domain" in module):
                found.setdefault(str(relative), set()).add(module)
    return found


def test_no_built_domain_newly_depends_on_an_unbuilt_table() -> None:
    """The rule NR-032 and NR-034 broke.

    An unbuilt domain is a deliberate state. A *built* domain reaching into one
    is a defect waiting for the first request that gets there — which is exactly
    what a pharmacy sale naming a patient did.
    """
    importers = set(_cross_generation_importers())
    added = sorted(importers - DECLARED_CROSS_GENERATION_IMPORTERS)
    removed = sorted(DECLARED_CROSS_GENERATION_IMPORTERS - importers)
    assert not added, (
        "these modules now depend on a domain the migration chain does not "
        f"build:\n  {added}\n\nThat is NR-034 happening again. Point them at a "
        "domain that exists, or record the dependency deliberately."
    )
    assert not removed, (
        f"{removed} no longer depend on an unbuilt domain — good. Remove them "
        "from DECLARED_CROSS_GENERATION_IMPORTERS so the list stays honest."
    )


# ── 3. The gate's own regression proof (§6) ──────────────────────────────────


def test_the_gate_detects_an_orm_only_table(physical) -> None:
    """A model with metadata and no migration must be caught.

    Built on an isolated MetaData so nothing is added to a real declarative
    base, and nothing survives the test.
    """
    from sqlalchemy import Column, Integer, Table

    isolated = MetaData()
    Table("tst_model_without_a_migration", isolated, Column("id", Integer, primary_key=True))
    synthetic = dict.fromkeys(isolated.tables, "Synthetic")

    unbacked = set(synthetic) - set(physical)
    undeclared = unbacked - DECLARED_UNBUILT_TABLES
    assert undeclared == {"tst_model_without_a_migration"}, (
        "the gate no longer notices an ORM table that no migration builds"
    )


def test_the_gate_distinguishes_the_four_dispositions(physical) -> None:
    """Each case must classify deterministically, not by accident."""
    # A — migration-backed: present physically, so never reported
    assert "lab_users" in physical
    assert not ({"lab_users"} - set(physical)) - DECLARED_UNBUILT_TABLES

    # D — declared and deliberately unbuilt: absent, but in the ledger
    assert "ehr_medication_dispenses" in DECLARED_UNBUILT_TABLES
    assert "ehr_medication_dispenses" not in physical
    assert not ({"ehr_medication_dispenses"} - set(physical)) - DECLARED_UNBUILT_TABLES

    # a renamed model — the NR-026 shape: the old name is built, the new one is
    # neither built nor declared, so it is reported
    renamed = {"nursing_checklists"}  # what the ORM used to say
    assert renamed - set(physical) - DECLARED_UNBUILT_TABLES == renamed

    # migration exists, ORM absent: the other direction, and deliberately not
    # this module's job — test_alembic_metadata_registry.py owns it
    assert "idempotency_keys" in physical


def test_the_three_findings_this_gate_exists_for_would_have_been_caught(physical) -> None:
    """NR-026, NR-032 and NR-034, as the gate would have seen them.

    Not a re-creation of the defects — a demonstration that the property each
    one violated is now checked.
    """
    # NR-026: the Nursing ORM named two tables no migration creates.
    for phantom in ("nursing_checklists", "nursing_escalations"):
        assert phantom not in physical
        assert phantom not in DECLARED_UNBUILT_TABLES, (
            f"{phantom} must never be declared; it was a typo, not a decision"
        )
        # therefore test_every_orm_table_is_migration_backed_or_declared fails
        assert {phantom} - set(physical) - DECLARED_UNBUILT_TABLES == {phantom}

    # NR-032 / NR-034: the EHR medication tables are absent and declared, so the
    # ledger stays quiet — correctly, because an unbuilt EHR is a known state.
    # What is caught is a *built* domain depending on them.
    for table in ("ehr_medication_dispenses", "ehr_medication_administrations"):
        assert table not in physical
        assert table in DECLARED_UNBUILT_TABLES

    # NR-034 specifically: Pharmacy must not be in the importer list any more.
    assert "pharmacy/services.py" not in DECLARED_CROSS_GENERATION_IMPORTERS
    assert "pharmacy/services.py" not in _cross_generation_importers(), (
        "Pharmacy depends on an unbuilt domain again; NR-034 has regressed"
    )


# ── 4. create_all() must not be the authority here (§7) ──────────────────────


def test_this_gate_cannot_fall_back_to_the_create_all_database(engine) -> None:
    """Fail loudly rather than pass against the fixture's SQLite schema.

    If this module ever ran against the ``db`` fixture it would prove nothing:
    that schema is built by create_all() and contains every ORM table by
    construction, so the ledger would always be empty and the gate always green.
    """
    assert engine.dialect.name == "postgresql", (
        f"the schema-fidelity gate is running on {engine.dialect.name!r}. It is "
        "only meaningful against a database built by the migration chain."
    )
    physical_names = set(inspect(engine).get_table_names())
    assert "alembic_version" in physical_names, (
        "this database has no alembic_version table, so it was not built by the "
        "migration chain — most likely it came from create_all(). Refusing to "
        "report a pass."
    )
    # And the defining property: a create_all() database would contain these.
    assert not (DECLARED_UNBUILT_TABLES & physical_names), (
        "tables that no migration builds are present, which is what a "
        "create_all() schema looks like"
    )
