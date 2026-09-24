"""M2: clinical-rule ORM and services against the migration-built schema.

Every rule below is related to a drug by ``pharmacy_drug_catalog.id``. These
tests exist to prove that relationship is the authoritative one — in
particular that renaming a drug's business code cannot detach a clinical
safety rule (CANONICAL_DRUG_CONTRACT §7).

Set ``PHARMACY_POSTGRES_URL`` to a disposable migrated database to run them.
"""

from __future__ import annotations

import os
import uuid
from collections.abc import Iterator
from datetime import UTC, datetime
from typing import Any

import pytest
from app.pharmacy.clinical import (
    AllergyEngine,
    ContraindicationEngine,
    DoseEngine,
    DrugInteractionEngine,
    DrugResolver,
)
from app.pharmacy.models import (
    AllergyRule,
    ContraindicationRule,
    DoseGuideline,
    DrugCatalog,
    DrugInteractionRule,
    DrugMonitoring,
)
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

POSTGRES_URL = os.getenv("PHARMACY_POSTGRES_URL")
pytestmark = pytest.mark.skipif(
    not POSTGRES_URL, reason="PHARMACY_POSTGRES_URL is not configured"
)

LAB_A = 970101
LAB_B = 970202
PATIENT_A = 970303


@pytest.fixture(scope="module")
def engine() -> Any:
    return create_engine(POSTGRES_URL, future=True)


@pytest.fixture()
def session(engine: Any) -> Iterator[Session]:
    """Every test runs in a transaction that is discarded afterwards."""
    connection = engine.connect()
    transaction = connection.begin()
    db = sessionmaker(bind=connection, future=True)()
    try:
        yield db
    finally:
        db.close()
        transaction.rollback()
        connection.close()


def _drug(db: Session, code: str, name: str = "M2 Synthetic Drug") -> DrugCatalog:
    drug = DrugCatalog(
        drug_code=code, drug_name=name, dosage_form="tablet", drug_id=uuid.uuid4()
    )
    db.add(drug)
    db.flush()
    return drug


def _tenants_and_patient(db: Session) -> None:
    """Real rows for the tenant-scoped monitoring table's foreign keys."""
    for lab_id in (LAB_A, LAB_B):
        db.execute(
            text(
                "INSERT INTO labs (id, name, is_active) VALUES (:i, :n, true) "
                "ON CONFLICT (id) DO NOTHING"
            ).bindparams(i=lab_id, n=f"M2 Synthetic Lab {lab_id}")
        )
    db.execute(
        text(
            "INSERT INTO patients (id, lab_id, full_name, phone) "
            "VALUES (:i, :l, :n, :p) ON CONFLICT (id) DO NOTHING"
        ).bindparams(i=PATIENT_A, l=LAB_A, n="M2 Synthetic Patient", p="0000000000")
    )
    db.flush()


# ── Phase 1 evidence: the ORM matches the physical rule tables ──────────────


@pytest.mark.parametrize(
    "model",
    [ContraindicationRule, AllergyRule, DoseGuideline, DrugMonitoring, DrugInteractionRule],
)
def test_rule_orm_matches_physical_table(engine: Any, model: Any) -> None:
    physical = {c["name"] for c in inspect(engine).get_columns(model.__tablename__)}
    mapped = {c.name for c in model.__table__.columns}
    assert mapped - physical == set(), f"{model.__tablename__}: ORM-only columns"
    assert physical - mapped == set(), f"{model.__tablename__}: unmapped columns"


@pytest.mark.parametrize(
    "model",
    [ContraindicationRule, AllergyRule, DoseGuideline, DrugMonitoring, DrugInteractionRule],
)
def test_no_rule_table_carries_a_drug_code(engine: Any, model: Any) -> None:
    """§7: a rule is never keyed on the mutable business code."""
    physical = {c["name"] for c in inspect(engine).get_columns(model.__tablename__)}
    assert "drug_code" not in physical
    assert "drug_code" not in {c.name for c in model.__table__.columns}


def test_only_monitoring_is_tenant_scoped(engine: Any) -> None:
    """Reference rules are global; a patient observation is not."""
    insp = inspect(engine)
    for table in (
        "pharmacy_contraindication_rules",
        "pharmacy_allergy_rules",
        "pharmacy_dose_guidelines",
        "pharmacy_drug_interaction_rules",
    ):
        assert "lab_id" not in {c["name"] for c in insp.get_columns(table)}, table
    assert "lab_id" in {c["name"] for c in insp.get_columns("pharmacy_drug_monitoring")}


# ── the authoritative relationship ─────────────────────────────────────────


def test_contraindication_is_found_through_the_foreign_key(session: Session) -> None:
    drug = _drug(session, "M2-CONTRA")
    session.add(
        ContraindicationRule(
            drug_id=drug.id,
            contraindication_type="condition",
            contraindication_value="renal_failure",
            severity="major",
            recommendation="Avoid in severe renal impairment",
        )
    )
    session.flush()

    engine = ContraindicationEngine(session)
    found = engine.check_drug_condition_by_id(drug.id, "renal_failure")
    assert len(found) == 1
    assert found[0].drug_id == drug.id

    by_code = engine.check_drug_condition("M2-CONTRA", "renal_failure")
    assert [r.id for r in by_code] == [found[0].id]


def test_business_code_edit_does_not_detach_a_rule(session: Session) -> None:
    """The §7 invariant, exercised end to end."""
    drug = _drug(session, "M2-RENAME-BEFORE")
    rule = ContraindicationRule(
        drug_id=drug.id,
        contraindication_type="condition",
        contraindication_value="pregnancy",
        severity="contraindicated",
    )
    session.add(rule)
    session.flush()

    drug.drug_code = "M2-RENAME-AFTER"
    session.flush()

    engine = ContraindicationEngine(session)
    # The foreign key still resolves...
    assert len(engine.check_drug_condition_by_id(drug.id, "pregnancy")) == 1
    # ...and the rule is reachable through the drug's NEW code.
    assert len(engine.check_drug_condition("M2-RENAME-AFTER", "pregnancy")) == 1
    # The old code identifies nothing at all, rather than a stale rule.
    assert engine.check_drug_condition("M2-RENAME-BEFORE", "pregnancy") == []


def test_rules_resolve_through_the_public_drug_id(session: Session) -> None:
    drug = _drug(session, "M2-PUBLIC")
    session.add(
        AllergyRule(
            drug_id=drug.id, allergen="penicillin", allergen_code="PEN", severity="major"
        )
    )
    session.flush()

    resolved = DrugResolver(session).by_public_id(str(drug.drug_id))
    assert resolved == drug.id
    rule = AllergyEngine(session).check_drug_allergy_by_id(resolved, "PEN")
    assert rule is not None and rule.drug_id == drug.id


def test_unknown_drug_returns_no_rules(session: Session) -> None:
    """A reference that matches nothing must not fall back to a wider match."""
    drug = _drug(session, "M2-REAL")
    session.add(
        ContraindicationRule(
            drug_id=drug.id,
            contraindication_type="condition",
            contraindication_value="asthma",
            severity="major",
        )
    )
    session.flush()

    engine = ContraindicationEngine(session)
    assert engine.check_drug_condition("M2-DOES-NOT-EXIST", "asthma") == []
    assert engine.check_patient_conditions("M2-DOES-NOT-EXIST", ["asthma"]) == []
    assert AllergyEngine(session).check_drug_allergy("M2-DOES-NOT-EXIST", "PEN") is None


def test_rules_do_not_leak_between_drugs(session: Session) -> None:
    first = _drug(session, "M2-ISOLATE-A")
    second = _drug(session, "M2-ISOLATE-B")
    session.add(
        ContraindicationRule(
            drug_id=first.id,
            contraindication_type="condition",
            contraindication_value="hepatic_failure",
            severity="major",
        )
    )
    session.flush()

    engine = ContraindicationEngine(session)
    assert len(engine.check_drug_condition_by_id(first.id, "hepatic_failure")) == 1
    assert engine.check_drug_condition_by_id(second.id, "hepatic_failure") == []


def test_interaction_matches_either_column_order(session: Session) -> None:
    a = _drug(session, "M2-INT-A")
    b = _drug(session, "M2-INT-B")
    session.add(
        DrugInteractionRule(drug_id_a=a.id, drug_id_b=b.id, severity="major")
    )
    session.flush()

    engine = DrugInteractionEngine(session)
    assert engine.check_interaction_by_id(a.id, b.id) is not None
    assert engine.check_interaction_by_id(b.id, a.id) is not None
    assert engine.check_interaction("M2-INT-A", "M2-INT-B") is not None

    found = engine.check_multiple_drugs(["M2-INT-A", "M2-INT-B"])
    assert len(found) == 1
    assert found[0]["severity"] == "major"


def test_dose_guideline_reads_numeric_columns(session: Session) -> None:
    drug = _drug(session, "M2-DOSE")
    session.add(
        DoseGuideline(
            drug_id=drug.id,
            indication="fever",
            dose_min=500.0,
            dose_max=1000.0,
            dose_unit="mg",
            frequency="every 6 hours",
            age_min_years=12.0,
        )
    )
    session.flush()

    results = DoseEngine(session).calculate_dose("M2-DOSE", "fever", age_months=216)
    assert len(results) == 1
    assert results[0]["dose_min"] == 500.0
    assert results[0]["drug_id"] == drug.id
    # 6 years old is below the 12-year floor, so nothing matches.
    assert DoseEngine(session).calculate_dose("M2-DOSE", "fever", age_months=72)[0].get(
        "note"
    )


# ── database-level integrity ───────────────────────────────────────────────


def test_rule_against_a_nonexistent_drug_is_rejected(session: Session) -> None:
    with pytest.raises(IntegrityError), session.begin_nested():
        session.add(
            ContraindicationRule(
                drug_id=987_654_321,
                contraindication_type="condition",
                contraindication_value="orphan",
                severity="major",
            )
        )


def test_deleting_a_drug_cascades_to_its_rules(session: Session) -> None:
    drug = _drug(session, "M2-CASCADE")
    session.add(
        AllergyRule(drug_id=drug.id, allergen="sulfa", severity="major")
    )
    session.flush()
    drug_pk = drug.id

    session.execute(
        text("DELETE FROM pharmacy_drug_catalog WHERE id = :i").bindparams(i=drug_pk)
    )
    session.flush()
    session.expire_all()

    remaining = (
        session.query(AllergyRule).filter(AllergyRule.drug_id == drug_pk).count()
    )
    assert remaining == 0


# ── tenant scope, where the table actually has one ─────────────────────────


def test_monitoring_records_are_tenant_scoped(session: Session) -> None:
    _tenants_and_patient(session)
    drug = _drug(session, "M2-MONITOR")
    session.add(
        DrugMonitoring(
            lab_id=LAB_A,
            patient_id=PATIENT_A,
            drug_id=drug.id,
            monitoring_type="serum_level",
            monitoring_date=datetime.now(UTC),
            value_numeric=12.5,
            unit="mg/L",
        )
    )
    session.flush()

    owner = DoseEngine(session, lab_id=LAB_A)
    assert len(owner.get_monitoring_records("M2-MONITOR", PATIENT_A)) == 1

    # A different laboratory must not see another tenant's patient data.
    other = DoseEngine(session, lab_id=LAB_B)
    assert other.get_monitoring_records("M2-MONITOR", PATIENT_A) == []

    # No tenant context at all reads nothing rather than everything.
    untenanted = DoseEngine(session, lab_id=None)
    assert untenanted.get_monitoring_records("M2-MONITOR", PATIENT_A) == []


def test_global_rule_lookup_is_not_tenant_filtered(session: Session) -> None:
    """A national contraindication is visible from any tenant context."""
    drug = _drug(session, "M2-GLOBAL-RULE")
    session.add(
        ContraindicationRule(
            drug_id=drug.id,
            contraindication_type="condition",
            contraindication_value="g6pd_deficiency",
            severity="contraindicated",
        )
    )
    session.flush()

    for lab_id in (LAB_A, LAB_B, None):
        engine = ContraindicationEngine(session, lab_id=lab_id)
        assert len(engine.check_drug_condition("M2-GLOBAL-RULE", "g6pd_deficiency")) == 1
