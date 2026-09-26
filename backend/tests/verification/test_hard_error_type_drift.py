"""No new ORM column may land in a type family PostgreSQL refuses to compare.

This is the generalisation of ``test_boolean_column_drift.py``.  That guard was
written after four Boolean-vs-Integer columns took the entire OAuth2/OIDC
provider down with::

    operator does not exist: boolean = integer

Widening the same measurement to every type family found 477 cross-family
ORM/physical disagreements, of which **162** are combinations PostgreSQL rejects
outright rather than coercing.  Each is a latent 500 on whichever query first
touches the column.

WHY THIS GUARD PINS RATHER THAN DEMANDS ZERO.

Repairing the 162 is not a code change.  The root cause is not scattered
sloppiness: eight domain base classes -- pharmacy, nursing, radiology, nhdw,
clinical, ehr, national and care_continuum -- each declare

    id = Column(String(26), primary_key=True, default=_ulid)

a ULID identity model, while the migrated database uses integer sequences for 70
of those tables and character varying for 11.  ``pharmacy_`` straddles the line
inside one domain: 4 tables carry varchar ids and 23 carry integer.  Choosing
which identity model is canonical is a data-migration decision with
platform-wide foreign-key consequences, and it is recorded as a human gate
(NR-062), not taken here.

So this guard does the one thing that needs no decision: it holds the line.

SUBSET, NOT EQUALITY -- a deliberate divergence from the house pattern.

``test_schema_drift_guard.py`` pins its known drift with ``==``.  That makes
*fixing* drift fail the suite, which is how six of its parametrised cases are
currently red.  This guard asserts the measured set is a **subset** of the pin
instead: repairing a column passes, introducing one fails, and the count of
pinned-but-now-clean columns is reported as information rather than as an error.
A tripwire that fires when someone improves the codebase trains people to
ignore tripwires.
"""

from __future__ import annotations

import importlib

import pytest
from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    Float,
    Integer,
    LargeBinary,
    Numeric,
    String,
    Text,
    Time,
    inspect,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSON, JSONB, UUID

from tests.verification import harness

pytestmark = harness.requires_postgres()

_BASES: tuple[tuple[str, str], ...] = (
    ("app.database", "Base"),
    ("app.identity.base", "IdentityBase"),
    ("app.radiology.base", "RadiologyBase"),
    ("app.governance.base", "GovernanceBase"),
    ("app.financial.models", "FinBase"),
    ("app.hospital.base", "HospitalBase"),
    ("app.health_data.base", "HealthDataBase"),
    ("app.insurance.domain.models", "InsBase"),
    ("app.clinical.base", "ClinicalBase"),
    ("app.ehr.base", "EHRBase"),
    ("app.national.base", "NationalBase"),
    ("app.care_continuum.base", "CareContinuumBase"),
    ("app.nursing.base", "NursingBase"),
    ("app.document_intelligence.infrastructure.models", "DocIntelBase"),
    ("app.nhdw.base", "NHDWBase"),
    ("app.trust.base", "TrustBase"),
    ("app.pharmacy.base", "PharmacyBase"),
    ("app.national_data.base", "DataPlatformBase"),
)

# Pairs PostgreSQL refuses rather than coerces, as (ORM family, physical family).
# Kept narrow on purpose: a benign width or affinity difference produces a
# correct query, and folding those in here would bury the ones that do not.
_HARD_ERROR_PAIRS: frozenset[tuple[str, str]] = frozenset({
    ("integer", "string"), ("string", "integer"),
    ("boolean", "integer"), ("integer", "boolean"),
    ("boolean", "string"), ("string", "boolean"),
    ("json", "string"), ("string", "json"),
    ("integer", "json"), ("json", "integer"),
    ("uuid", "integer"), ("integer", "uuid"),
    ("numeric", "string"), ("string", "numeric"),
    ("datetime", "string"), ("string", "datetime"),
})

# Measured on gula_canon at migration head 20260909_0001, 423 physical tables.
# To add an entry here you must record a finding explaining why it is acceptable.
# Removing one is always welcome and never fails this suite.
_PINNED_HARD_ERRORS: frozenset[str] = frozenset({
    "blood_bank_discards.created_by",
    "blood_bank_patient_samples.created_by",
    "blood_bank_reactions.created_by",
    "blood_bank_reservations.created_by",
    "blood_bank_returns.created_by",
    "blood_bank_traceability_events.created_by",
    "fin_providers.id",
    "fin_subscriptions.id",
    "fin_subscriptions.provider_id",
    "fin_transactions.id",
    "fin_transactions.provider_id",
    "nhdw_admissions.id",
    "nhdw_care_plans.id",
    "nhdw_clinical_tasks.id",
    "nhdw_dashboard_configurations.id",
    "nhdw_discharges.admission_id",
    "nhdw_discharges.discharged_by",
    "nhdw_discharges.id",
    "nhdw_hospital_alerts.id",
    "nhdw_hospital_messages.id",
    "nhdw_hospital_messages.parent_message_id",
    "nhdw_queue_entries.id",
    "nhdw_resource_schedules.id",
    "nhdw_shift_reports.id",
    "nhdw_telemedicine_sessions.id",
    "nhdw_transfers.id",
    "nhdw_transfers.transferred_by",
    "nhdw_waiting_list_entries.id",
    "nhdw_ward_rounds.id",
    "nursing_care_plans.created_by",
    "nursing_care_plans.id",
    "nursing_delegations.delegated_by",
    "nursing_delegations.delegated_to",
    "nursing_delegations.id",
    "nursing_fall_risk_assessments.assessed_by",
    "nursing_fall_risk_assessments.id",
    "nursing_fluid_balance.id",
    "nursing_fluid_balance.recorded_by",
    "nursing_notes.id",
    "nursing_nutrition_assessments.assessed_by",
    "nursing_nutrition_assessments.id",
    "nursing_pain_assessments.assessed_by",
    "nursing_pain_assessments.id",
    "nursing_patient_assignments.id",
    "nursing_patient_assignments.nurse_id",
    "nursing_pressure_injury_assessments.assessed_by",
    "nursing_pressure_injury_assessments.id",
    "nursing_shift_handovers.from_nurse_id",
    "nursing_shift_handovers.from_shift_id",
    "nursing_shift_handovers.id",
    "nursing_shift_handovers.to_nurse_id",
    "nursing_shift_handovers.to_shift_id",
    "nursing_shifts.id",
    "nursing_shifts.nurse_id",
    "nursing_tasks.assigned_by",
    "nursing_tasks.assigned_to",
    "nursing_tasks.completed_by",
    "nursing_tasks.id",
    "nursing_vital_signs.id",
    "nursing_vital_signs.recorded_by",
    "pharmacy_allergy_rules.id",
    "pharmacy_clinical_guidelines.id",
    "pharmacy_contraindication_rules.id",
    "pharmacy_dispense_queue.assigned_to",
    "pharmacy_dispense_queue.id",
    "pharmacy_dispense_queue.prescription_id",
    "pharmacy_dispense_queue.priority",
    "pharmacy_dispense_records.batch_id",
    "pharmacy_dispense_records.dispensed_by",
    "pharmacy_dispense_records.id",
    "pharmacy_dispense_records.patient_id",
    "pharmacy_dispense_records.prescription_id",
    "pharmacy_dispense_records.prescription_item_id",
    "pharmacy_dispense_records.verified_by",
    "pharmacy_dose_guidelines.dose_max",
    "pharmacy_dose_guidelines.dose_min",
    "pharmacy_dose_guidelines.id",
    "pharmacy_dose_guidelines.max_daily_dose",
    "pharmacy_drug_batches.id",
    "pharmacy_drug_batches.received_by",
    "pharmacy_drug_catalog.id",
    "pharmacy_drug_interaction_rules.id",
    "pharmacy_drug_monitoring.id",
    "pharmacy_drug_returns.batch_id",
    "pharmacy_drug_returns.id",
    "pharmacy_drug_returns.patient_id",
    "pharmacy_drug_returns.returned_by",
    "pharmacy_drug_substitution_rules.alternative_drug_catalog_id",
    "pharmacy_drug_substitution_rules.original_drug_catalog_id",
    "pharmacy_drug_suppliers.id",
    "pharmacy_inventory_forecasts.id",
    "pharmacy_inventory_transfer_items.batch_id",
    "pharmacy_inventory_transfer_items.id",
    "pharmacy_inventory_transfer_items.transfer_id",
    "pharmacy_inventory_transfers.approved_by",
    "pharmacy_inventory_transfers.from_store_id",
    "pharmacy_inventory_transfers.from_warehouse_id",
    "pharmacy_inventory_transfers.id",
    "pharmacy_inventory_transfers.to_store_id",
    "pharmacy_inventory_transfers.to_warehouse_id",
    "pharmacy_prescription_items.duration",
    "pharmacy_prescription_items.id",
    "pharmacy_prescription_items.prescription_id",
    "pharmacy_prescriptions.id",
    "pharmacy_prescriptions.patient_id",
    "pharmacy_recalls.batch_id",
    "pharmacy_recalls.id",
    "pharmacy_recalls.initiated_by",
    "pharmacy_stock_levels.batch_id",
    "pharmacy_stock_levels.id",
    "pharmacy_stock_levels.store_id",
    "pharmacy_stock_levels.warehouse_id",
    "pharmacy_stock_movements.batch_id",
    "pharmacy_stock_movements.id",
    "pharmacy_stock_movements.performed_by",
    "pharmacy_stock_movements.reference_id",
    "pharmacy_stores.id",
    "pharmacy_stores.warehouse_id",
    "pharmacy_warehouses.id",
    "pharmacy_waste_records.batch_id",
    "pharmacy_waste_records.id",
    "radiology_appointments.id",
    "radiology_appointments.order_id",
    "radiology_appointments.patient_id",
    "radiology_critical_findings.acknowledged_by",
    "radiology_critical_findings.exam_id",
    "radiology_critical_findings.id",
    "radiology_critical_findings.report_id",
    "radiology_dicom_storage.id",
    "radiology_dicom_storage.patient_id",
    "radiology_dicom_studies.id",
    "radiology_dicom_studies.patient_id",
    "radiology_exams.appointment_id",
    "radiology_exams.id",
    "radiology_exams.order_id",
    "radiology_exams.patient_id",
    "radiology_exams.protocol_id",
    "radiology_image_annotations.exam_id",
    "radiology_image_annotations.id",
    "radiology_image_annotations.image_id",
    "radiology_image_measurements.exam_id",
    "radiology_image_measurements.id",
    "radiology_image_measurements.image_id",
    "radiology_image_shares.id",
    "radiology_image_shares.shared_by",
    "radiology_images.id",
    "radiology_images.series_id",
    "radiology_modality_devices.id",
    "radiology_mpps.exam_id",
    "radiology_mpps.id",
    "radiology_orders.id",
    "radiology_orders.patient_id",
    "radiology_protocols.id",
    "radiology_protocols.version",
    "radiology_report_templates.id",
    "radiology_reports.exam_id",
    "radiology_reports.id",
    "radiology_reports.patient_id",
    "radiology_series.exam_id",
    "radiology_series.id",
    "radiology_worklist_entries.id",
    "radiology_worklist_entries.patient_id",
})


def _family(sqla_type: object) -> str:
    """Bucket a SQLAlchemy type into the family that decides comparability."""
    if isinstance(sqla_type, Boolean):
        return "boolean"
    if isinstance(sqla_type, (JSONB, JSON)):
        return "json"
    if isinstance(sqla_type, UUID):
        return "uuid"
    if isinstance(sqla_type, ARRAY):
        return "array"
    if isinstance(sqla_type, Enum):
        return "enum"
    # Boolean is a subclass of Integer in some dialects, so it is tested first.
    if isinstance(sqla_type, Integer):
        return "integer"
    if isinstance(sqla_type, (Numeric, Float)):
        return "numeric"
    if isinstance(sqla_type, (String, Text)):
        return "string"
    if isinstance(sqla_type, DateTime):
        return "datetime"
    if isinstance(sqla_type, Date):
        return "date"
    if isinstance(sqla_type, Time):
        return "time"
    if isinstance(sqla_type, LargeBinary):
        return "binary"
    return f"other:{type(sqla_type).__name__}"


@pytest.fixture(scope="module")
def Session():
    factory = harness.session_factory()
    yield factory
    harness.dispose(factory)


@pytest.fixture(scope="module")
def survey(Session):
    import app.main  # importing the app registers every model

    insp = inspect(Session.kw["bind"])
    physical = set(insp.get_table_names())

    columns: dict[str, dict[str, object]] = {}
    hard: dict[str, tuple[str, str]] = {}
    compared: set[str] = set()
    unloadable: list[str] = []

    for module_name, attr in _BASES:
        try:
            base = getattr(importlib.import_module(module_name), attr)
        except Exception as exc:  # pragma: no cover - reported, not swallowed
            unloadable.append(f"{module_name}.{attr}: {type(exc).__name__}: {exc}")
            continue

        for table_name, table in base.metadata.tables.items():
            if table_name not in physical:
                continue
            compared.add(table_name)
            if table_name not in columns:
                columns[table_name] = {
                    c["name"]: c["type"] for c in insp.get_columns(table_name)
                }
            for col in table.columns:
                physical_type = columns[table_name].get(col.name)
                if physical_type is None:
                    continue
                pair = (_family(col.type), _family(physical_type))
                if pair in _HARD_ERROR_PAIRS:
                    hard[f"{table_name}.{col.name}"] = pair

    return {
        "hard": hard,
        "compared": compared,
        "physical": physical,
        "unloadable": unloadable,
    }


def test_every_declarative_base_is_importable(survey):
    """A base this guard cannot import is a base it cannot check."""
    assert survey["unloadable"] == []


def test_the_guard_still_covers_the_platform(survey):
    """Guard against passing because the survey compared almost nothing."""
    assert len(survey["compared"]) > 350, (
        f"only {len(survey['compared'])} of {len(survey['physical'])} physical "
        "tables were compared; this guard is no longer measuring the platform"
    )


def test_no_new_hard_error_column_appears(survey):
    """The whole point: the 162 may shrink, never grow."""
    measured = set(survey["hard"])
    new = sorted(measured - _PINNED_HARD_ERRORS)
    assert new == [], (
        "new ORM column(s) in a type family PostgreSQL refuses to compare. Any "
        "query touching one of these raises rather than returning a wrong "
        "answer, so this is a latent 500:\n  "
        + "\n  ".join(f"{name}: ORM={survey['hard'][name][0]} physical={survey['hard'][name][1]}" for name in new)
    )


def test_the_pin_is_reported_not_silently_stale(survey):
    """Repairs are welcome; this only reports them so the pin can be trimmed.

    Deliberately not an equality assertion. See this module's docstring.
    """
    repaired = sorted(_PINNED_HARD_ERRORS - set(survey["hard"]))
    if repaired:
        print(
            f"\n{len(repaired)} pinned column(s) are now clean and can be removed "
            f"from _PINNED_HARD_ERRORS:\n  " + "\n  ".join(repaired)
        )
    # Always passes. The assertion is that the guard ran, not that nothing moved.
    assert isinstance(repaired, list)


def test_the_boolean_family_stays_at_zero(survey):
    """NR-053 is closed and must stay closed.

    The boolean family is the one that has actually been repaired
    platform-wide, so unlike the rest it is held at zero rather than pinned.
    """
    boolean_drift = sorted(
        name for name, pair in survey["hard"].items()
        if "boolean" in pair
    )
    assert boolean_drift == [], (
        "boolean/non-boolean drift has returned; this is what took the OAuth2 "
        "provider down:\n  " + "\n  ".join(boolean_drift)
    )
