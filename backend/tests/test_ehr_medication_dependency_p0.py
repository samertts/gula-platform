"""NR-032: six domains depend on EHR medication tables that were never built.

BATCH-3 recorded this as a Nursing finding. Tracing it in BATCH-3.1 showed the
Nursing endpoints are one consumer of five: Pharmacy's point-of-sale path,
the Citizen Platform, the National FHIR exporters and the National Data
canonical-medication view all import the same four ORM models, and no
migration creates any of their tables.

These tests assert the *defect*, with the evidence that decides ownership:

* the four ``ehr_medication_*`` tables do not exist at head, and no migration
  builds them;
* the models are keyed on ``String(26)`` and point at four ``national_*``
  tables that do not exist either (NR-022), so they cannot be created without
  first building the National Core;
* they carry no ``lab_id`` at all, while every caller filters on one — so the
  tenant isolation those callers believe they apply is not expressible;
* meanwhile Pharmacy's equivalent tables *do* exist, are lab-scoped and are
  INTEGER-keyed, which is what makes Pharmacy the canonical owner of
  prescribing and dispensing rather than EHR.

When the ownership decision in
docs/architecture/nursing-medication-ownership.md is executed these tests
fail. That is the signal to close NR-032 and rewrite them to pin the
resolution — not to weaken them.
"""

from __future__ import annotations

import os

import pytest
from sqlalchemy import create_engine, inspect, text


def _schema_database_url() -> str:
    """The database these assertions read, migrated to head.

    DATABASE_URL cannot supply it: conftest pins that variable to in-memory
    SQLite for the whole suite. MIGRATION_DATABASE_URL is the one CI already
    exports for its migrated PostgreSQL service.
    """
    return (os.environ.get("GULA_SCHEMA_DATABASE_URL")
            or os.environ.get("MIGRATION_DATABASE_URL", ""))


SCHEMA_DATABASE_URL = _schema_database_url()
pytestmark = pytest.mark.skipif(
    not SCHEMA_DATABASE_URL,
    reason="GULA_SCHEMA_DATABASE_URL/MIGRATION_DATABASE_URL is not configured",
)

EHR_MEDICATION_TABLES = (
    "ehr_medication_statements",
    "ehr_medication_requests",
    "ehr_medication_dispenses",
    "ehr_medication_administrations",
)

# The National Core tables the EHR medication models declare foreign keys to.
# All four are NR-022: depended upon, never built.
NATIONAL_CORE_TABLES = (
    "national_patients",
    "national_citizens",
    "national_encounters",
    "national_practitioners",
)

# Pharmacy's equivalents, which do exist.
PHARMACY_MEDICATION_TABLES = (
    "pharmacy_drug_catalog",
    "pharmacy_prescriptions",
    "pharmacy_prescription_items",
    "pharmacy_dispense_records",
)


@pytest.fixture(scope="module")
def engine():
    eng = create_engine(SCHEMA_DATABASE_URL, future=True)
    try:
        yield eng
    finally:
        eng.dispose()


def _tables(engine) -> set[str]:
    return set(inspect(engine).get_table_names())


def test_no_ehr_medication_table_exists_at_head(engine) -> None:
    present = _tables(engine) & set(EHR_MEDICATION_TABLES)
    assert not present, (
        f"{sorted(present)} now exist. If the EHR medication domain was "
        "adopted, close NR-032 and rewrite this guard rather than deleting it."
    )


def test_the_national_core_the_models_reference_does_not_exist_either(engine) -> None:
    """Why the tables cannot simply be created: their parents are missing.

    Every ``ehr_medication_*`` model points at ``national_patients``,
    ``national_citizens``, ``national_encounters`` or ``national_practitioners``
    with a real ``ForeignKey``. Creating the medication tables therefore means
    building the National Core first — an architecture decision (NR-022), not a
    migration.
    """
    present = _tables(engine) & set(NATIONAL_CORE_TABLES)
    assert not present, (
        f"{sorted(present)} now exist; NR-022 has moved and NR-032's dependency "
        "argument must be re-derived"
    )


def test_the_models_cannot_express_the_tenant_filter_their_callers_apply(engine) -> None:
    """The isolation defect underneath the missing tables.

    ``app/nursing/medication.py`` filters ``MedicationAdministration.lab_id``
    and ``MedicationRequest.lab_id`` in six places, and Pharmacy's POS path
    treats a dispense as institutional. Neither model has a ``lab_id`` column:
    EHR is national-scoped, keyed on citizen and patient. Creating these tables
    as declared would give six lab-scoped callers a table with no tenant column.
    """
    from app.ehr.models.medication import (
        MedicationAdministration,
        MedicationDispense,
        MedicationRequest,
        MedicationStatement,
    )

    for model in (MedicationStatement, MedicationRequest,
                  MedicationDispense, MedicationAdministration):
        columns = {column.name for column in model.__table__.columns}
        assert "lab_id" not in columns, (
            f"{model.__tablename__} gained a lab_id column; the tenancy half of "
            "NR-032 has changed and the ownership decision must be revisited"
        )
        assert str(model.__table__.c.id.type) == "VARCHAR(26)", (
            f"{model.__tablename__} is no longer String(26)-keyed; re-derive "
            "the identity mismatch against the INTEGER-keyed Pharmacy domain"
        )


@pytest.mark.parametrize("table", PHARMACY_MEDICATION_TABLES)
def test_the_canonical_medication_owner_is_built_and_lab_scoped(engine, table) -> None:
    """Pharmacy is the domain that actually exists.

    Prescribing (``pharmacy_prescriptions`` + ``pharmacy_prescription_items``),
    the drug catalogue and dispensing are all present, lab-scoped and
    INTEGER-keyed. That is the evidence for Nursing consuming Pharmacy rather
    than a second medication model being created for it.
    """
    inspector = inspect(engine)
    assert table in _tables(engine), f"{table} is missing; Pharmacy is not intact"

    columns = {c["name"]: c for c in inspector.get_columns(table)}
    assert str(columns["id"]["type"]).upper().startswith("INTEGER")

    # Tenancy is deliberately uneven, and the shape is itself evidence:
    # the drug catalogue is shared reference data (a drug is a drug), while
    # prescriptions and dispenses are a laboratory's own records.
    # prescription_items carries tenancy through its parent prescription.
    tenant_scoped = {"pharmacy_prescriptions", "pharmacy_dispense_records"}
    if table in tenant_scoped:
        assert "lab_id" in columns, f"{table} is not lab-scoped"
    else:
        assert "lab_id" not in columns, (
            f"{table} gained a lab_id; it was shared reference data, and making "
            "it tenant-scoped changes who owns the drug catalogue"
        )


def test_medication_administration_has_no_owner_in_any_built_domain(engine) -> None:
    """The one genuine gap.

    Prescribing and dispensing both have a built owner. The medication
    *administration* record — the nurse giving the drug at the bedside, which
    is what three of the four Nursing endpoints are about — has none: no table
    in any domain records it. This is why NR-032 cannot be resolved purely by
    redirecting Nursing at Pharmacy.
    """
    administration_tables = {
        name for name in _tables(engine)
        if "administration" in name or name.endswith("_medication_admin")
    }
    assert not administration_tables, (
        f"a medication administration table now exists ({sorted(administration_tables)}); "
        "it is the canonical owner and NR-032's recommendation must be updated"
    )


def test_every_dependent_domain_is_named(engine) -> None:
    """Blast radius, pinned so it cannot quietly grow.

    NR-032 was recorded as a Nursing finding. It is not: five domains import
    these models. A sixth appearing without this list changing would hide the
    real scope again.
    """
    import pathlib
    import re

    app_root = pathlib.Path(__file__).resolve().parents[1] / "app"
    importers = set()
    for path in app_root.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        if re.search(r"from app\.ehr\.models\.medication import", path.read_text(encoding="utf-8", errors="ignore")):
            importers.add(str(path.relative_to(app_root)))

    expected = {
        "ehr/models/__init__.py",
        "national/fhir/medication_statement.py",
        "national/fhir/medication_request.py",
        "nursing/services.py",
        "nursing/medication.py",
        "pharmacy/services.py",
        "national_data/models/canonical_medication.py",
        "citizen_platform/medications.py",
        "citizen_platform/routes.py",
    }
    assert importers == expected, (
        "the set of modules depending on the unbuilt EHR medication tables "
        f"changed.\n  added: {sorted(importers - expected)}\n"
        f"  removed: {sorted(expected - importers)}\n"
        "Update docs/architecture/nursing-medication-ownership.md with the new scope."
    )


def test_pharmacy_point_of_sale_writes_to_a_table_that_does_not_exist(engine) -> None:
    """The reachable P0 this trace uncovered outside Nursing.

    ``PharmacyService`` builds an EHR ``MedicationDispense`` for every sale
    line whenever the caller supplies ``patient_id`` or ``citizen_id`` — both
    accepted by the POS request model. The INSERT targets
    ``ehr_medication_dispenses``, so such a sale cannot commit.
    """
    import pathlib

    from app.pharmacy import services as pharmacy_services

    source = pathlib.Path(pharmacy_services.__file__).read_text(encoding="utf-8")
    assert "from app.ehr.models.medication import MedicationDispense" in source, (
        "Pharmacy no longer imports the EHR dispense model; if the POS path was "
        "redirected at pharmacy_dispense_records, close this finding"
    )
    assert "dispense = MedicationDispense(" in source, (
        "the POS write path changed; re-derive whether a patient-context sale "
        "can still reach an unbuilt table"
    )

    with engine.connect() as conn:
        exists = conn.execute(text(
            "SELECT to_regclass('public.ehr_medication_dispenses') IS NOT NULL"
        )).scalar_one()
    assert not exists, "ehr_medication_dispenses now exists; re-verify the POS path"
