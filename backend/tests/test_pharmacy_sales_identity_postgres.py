"""M3: Sales/Substitution identity against the migration-built schema.

These entities were the last Generation B holdouts in the P0-2 scope. They
carried a ``String(26)`` ``_ulid()`` primary key and two ORM-only FHIR columns,
which made every ORM ``INSERT`` fail with ``UndefinedColumn`` before a row could
be created, and they named integer-keyed catalog rows through ``VARCHAR(26)``
columns that PostgreSQL could not constrain (P0-2-SUBBLOCKER-A Group A).

The tests below are the evidence that both are fixed, and the guard that keeps
the two things M3 deliberately did *not* do — inventing a batch or prescription
identity — from being quietly done later without M4.

Set ``PHARMACY_POSTGRES_URL`` to a disposable migrated database to run them.
"""

from __future__ import annotations

import os
import uuid
from collections.abc import Iterator
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import pytest
from app.pharmacy.models import (
    DrugCatalog,
    DrugSubstitutionRequest,
    DrugSubstitutionRule,
    PharmacySale,
    PharmacySaleLine,
)
from sqlalchemy import Integer, String, create_engine, inspect, text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

POSTGRES_URL = os.getenv("PHARMACY_POSTGRES_URL")
pytestmark = pytest.mark.skipif(
    not POSTGRES_URL, reason="PHARMACY_POSTGRES_URL is not configured"
)

LAB_A = 980101
LAB_B = 980202

M3_MODELS = (PharmacySale, PharmacySaleLine, DrugSubstitutionRule, DrugSubstitutionRequest)

# entity -> its public identifier column
PUBLIC_IDS = {
    PharmacySale: "sale_id",
    PharmacySaleLine: "sale_line_id",
    DrugSubstitutionRule: "substitution_rule_id",
    DrugSubstitutionRequest: "substitution_request_id",
}


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


def _labs(db: Session) -> None:
    for lab_id in (LAB_A, LAB_B):
        db.execute(
            text(
                "INSERT INTO labs (id, name, is_active) VALUES (:i, :n, true) "
                "ON CONFLICT (id) DO NOTHING"
            ).bindparams(i=lab_id, n=f"M3 Synthetic Lab {lab_id}")
        )
    db.flush()


def _batch(db: Session, drug: DrugCatalog, *, lab_id: int = LAB_A, number: str = "M3-BATCH") -> Any:
    from datetime import date, timedelta

    from app.pharmacy.models import DrugBatch

    batch = DrugBatch(
        lab_id=lab_id,
        drug_id=drug.id,
        batch_number=number,
        expiry_date=date.today() + timedelta(days=180),
        quantity_received=100,
        quantity_remaining=100,
        received_date=datetime.now(UTC),
        status="active",
    )
    db.add(batch)
    db.flush()
    return batch


def _drug(db: Session, code: str) -> DrugCatalog:
    drug = DrugCatalog(
        drug_code=code, drug_name="M3 Synthetic Drug", dosage_form="tablet", drug_id=uuid.uuid4()
    )
    db.add(drug)
    db.flush()
    return drug


def _sale(db: Session, *, lab_id: int = LAB_A, number: str = "M3-SALE-1", **kwargs: Any) -> PharmacySale:
    sale = PharmacySale(
        lab_id=lab_id,
        sale_number=number,
        subtotal=Decimal("10.00"),
        discount=Decimal("0.00"),
        total_amount=Decimal("10.00"),
        cost_amount=Decimal("4.00"),
        gross_profit=Decimal("6.00"),
        **kwargs,
    )
    db.add(sale)
    db.flush()
    return sale


def _line(db: Session, sale: PharmacySale, drug: DrugCatalog, **kwargs: Any) -> PharmacySaleLine:
    batch = kwargs.pop("batch", None) or _batch(db, drug, number=f"M3-B-{drug.drug_code}")
    line = PharmacySaleLine(
        lab_id=sale.lab_id,
        sale_id=sale.id,
        drug_catalog_id=drug.id,
        # M4 resolved Group B: this is now an enforced Integer foreign key.
        batch_id=batch.id,
        line_number=kwargs.pop("line_number", 1),
        medication_name="M3 Synthetic Drug",
        quantity=1,
        unit_price=Decimal("10.00"),
        unit_cost=Decimal("4.00"),
        discount=Decimal("0.00"),
        line_total=Decimal("10.00"),
        line_cost=Decimal("4.00"),
        **kwargs,
    )
    db.add(line)
    db.flush()
    return line


# ── ORM ↔ physical parity ──────────────────────────────────────────────────


@pytest.mark.parametrize("model", M3_MODELS)
def test_orm_matches_the_physical_table(engine: Any, model: Any) -> None:
    physical = {c["name"] for c in inspect(engine).get_columns(model.__tablename__)}
    mapped = {c.name for c in model.__table__.columns}
    assert mapped - physical == set(), f"{model.__tablename__}: ORM-only columns"
    assert physical - mapped == set(), f"{model.__tablename__}: unmapped columns"


@pytest.mark.parametrize("model", M3_MODELS)
def test_no_orm_only_fhir_columns(engine: Any, model: Any) -> None:
    """Regression for the defect that made these tables unwritable.

    ``fhir_id``/``fhir_resource_type`` came from the Generation B base and were
    never in any migration for these four tables, so every ORM INSERT failed
    with ``UndefinedColumn``. Seven other Pharmacy tables do carry them
    physically; these four deliberately do not.
    """
    mapped = {c.name for c in model.__table__.columns}
    physical = {c["name"] for c in inspect(engine).get_columns(model.__tablename__)}
    assert "fhir_id" not in mapped and "fhir_id" not in physical
    assert "fhir_resource_type" not in mapped and "fhir_resource_type" not in physical


# ── canonical identity ──────────────────────────────────────────────────────


@pytest.mark.parametrize("model", M3_MODELS)
def test_internal_key_is_integer(engine: Any, model: Any) -> None:
    assert isinstance(model.__table__.c.id.type, Integer)
    physical = {c["name"]: c for c in inspect(engine).get_columns(model.__tablename__)}
    assert isinstance(physical["id"]["type"], Integer)


@pytest.mark.parametrize("model", M3_MODELS)
def test_public_identity_is_a_distinct_immutable_uuid(engine: Any, model: Any) -> None:
    """Contract §3: the internal key is never an entity's public identity."""
    column = PUBLIC_IDS[model]
    physical = {c["name"]: c for c in inspect(engine).get_columns(model.__tablename__)}
    assert column in physical, f"{model.__tablename__} has no public identifier"
    assert isinstance(physical[column]["type"], PGUUID)
    assert physical[column]["nullable"] is False
    uniques = {
        tuple(u["column_names"]) for u in inspect(engine).get_unique_constraints(model.__tablename__)
    }
    assert (column,) in uniques, f"{model.__tablename__}.{column} is not unique"


def test_public_identifiers_are_server_side_and_unique(session: Session) -> None:
    _labs(session)
    first = _sale(session, number="M3-SALE-A")
    second = _sale(session, number="M3-SALE-B")
    assert first.sale_id != second.sale_id
    # Version 4 is the whole point: the public identity is random, so it carries
    # nothing about the row's internal key, its creation order or its content
    # (contract §10, "never derived").
    assert first.sale_id.version == 4
    assert second.sale_id.version == 4
    # The internal key is an ordinary sequence value, and the two are separate
    # identities rather than two spellings of one.
    assert isinstance(first.id, int)
    issued = first.sale_id
    session.expire(first)
    assert first.sale_id == issued, "a public identity must never be regenerated"


# ── writability: the defect that blocked every row ──────────────────────────


def test_a_sale_and_its_lines_round_trip_through_the_orm(session: Session) -> None:
    _labs(session)
    drug = _drug(session, "M3-RT-001")
    sale = _sale(session, number="M3-SALE-RT")
    line = _line(session, sale, drug)
    session.expire_all()

    stored = session.query(PharmacySale).filter(PharmacySale.sale_id == sale.sale_id).one()
    assert stored.sale_number == "M3-SALE-RT"
    assert len(stored.lines) == 1
    assert stored.lines[0].drug_catalog_id == drug.id
    assert stored.lines[0].sale_line_id == line.sale_line_id
    # The relationship resolves through the real foreign key, so the line can
    # produce the drug's public identity without a second lookup.
    assert stored.lines[0].drug.drug_id == drug.drug_id


def test_a_substitution_request_round_trips_through_the_orm(session: Session) -> None:
    _labs(session)
    original = _drug(session, "M3-SUB-ORIG")
    alternative = _drug(session, "M3-SUB-ALT")
    rule = DrugSubstitutionRule(
        lab_id=LAB_A,
        original_drug_catalog_id=original.id,
        alternative_drug_catalog_id=alternative.id,
    )
    session.add(rule)
    session.flush()
    request = DrugSubstitutionRequest(
        lab_id=LAB_A,
        rule_id=rule.id,
        original_drug_catalog_id=original.id,
        alternative_drug_catalog_id=alternative.id,
        quantity=1,
        reason="original medication unavailable",
    )
    session.add(request)
    session.flush()
    session.expire_all()

    stored = session.query(DrugSubstitutionRequest).filter(
        DrugSubstitutionRequest.substitution_request_id == request.substitution_request_id
    ).one()
    assert stored.rule.substitution_rule_id == rule.substitution_rule_id
    assert stored.original_drug_catalog_id == original.id
    assert stored.consumed_sale is None


# ── Group A: the references PostgreSQL could never constrain ────────────────


GROUP_A = (
    ("pharmacy_sale_lines", "drug_catalog_id"),
    ("pharmacy_drug_substitution_requests", "original_drug_catalog_id"),
    ("pharmacy_drug_substitution_requests", "alternative_drug_catalog_id"),
)


@pytest.mark.parametrize(("table", "column"), GROUP_A)
def test_group_a_reference_is_an_enforced_integer_foreign_key(
    engine: Any, table: str, column: str
) -> None:
    physical = {c["name"]: c for c in inspect(engine).get_columns(table)}
    assert isinstance(physical[column]["type"], Integer), f"{table}.{column} is not Integer"
    targets = {
        (tuple(fk["constrained_columns"]), fk["referred_table"])
        for fk in inspect(engine).get_foreign_keys(table)
    }
    assert ((column,), "pharmacy_drug_catalog") in targets, (
        f"{table}.{column} has no foreign key onto the drug catalog"
    )


def test_a_sale_line_cannot_name_a_drug_that_does_not_exist(session: Session) -> None:
    """The constraint that was impossible while the column was VARCHAR(26).

    Before M3 this row was accepted: ``drug_catalog_id`` was an unconstrained
    ``VARCHAR(26)``, so any string at all could be stored as a drug reference.
    """
    _labs(session)
    real_drug = _drug(session, "M3-FK-REAL")
    batch = _batch(session, real_drug, number="M3-FK-BATCH")
    sale = _sale(session, number="M3-SALE-FK")
    missing_drug_pk = 2_000_000_001
    assert session.query(DrugCatalog).filter(DrugCatalog.id == missing_drug_pk).first() is None
    with pytest.raises(IntegrityError), session.begin_nested():
        session.add(
            PharmacySaleLine(
                lab_id=sale.lab_id,
                sale_id=sale.id,
                drug_catalog_id=missing_drug_pk,
                batch_id=batch.id,
                line_number=1,
                medication_name="M3 Synthetic Drug",
                quantity=1,
                unit_price=Decimal("10.00"),
                unit_cost=Decimal("4.00"),
                discount=Decimal("0.00"),
                line_total=Decimal("10.00"),
                line_cost=Decimal("4.00"),
            )
        )
        session.flush()


def test_a_substitution_request_cannot_name_a_rule_that_does_not_exist(session: Session) -> None:
    _labs(session)
    original = _drug(session, "M3-FK-ORIG")
    alternative = _drug(session, "M3-FK-ALT")
    with pytest.raises(IntegrityError), session.begin_nested():
        session.add(
            DrugSubstitutionRequest(
                lab_id=LAB_A,
                rule_id=2_000_000_002,
                original_drug_catalog_id=original.id,
                alternative_drug_catalog_id=alternative.id,
                quantity=1,
                reason="no such rule",
            )
        )
        session.flush()


def test_deleting_a_sale_removes_its_lines(session: Session) -> None:
    _labs(session)
    drug = _drug(session, "M3-CASCADE")
    sale = _sale(session, number="M3-SALE-CASCADE")
    _line(session, sale, drug)
    sale_pk = sale.id
    session.execute(text("DELETE FROM pharmacy_sales WHERE id = :i").bindparams(i=sale_pk))
    remaining = session.execute(
        text("SELECT count(*) FROM pharmacy_sale_lines WHERE sale_id = :i").bindparams(i=sale_pk)
    ).scalar_one()
    assert remaining == 0


# ── Group B: explicitly unresolved, and guarded against being guessed ───────


# P0-2-SUBBLOCKER-A Group B was deferred by M3 and resolved by M4. The guard
# that these three columns stay unconstrained lived here; it now lives in
# tests/test_pharmacy_inventory_identity_postgres.py as
# test_group_b_reference_is_now_an_enforced_integer_foreign_key, which asserts
# the opposite because M4 established the canonical batch and prescription
# targets they needed.


@pytest.mark.parametrize("model", (PharmacySaleLine, DrugSubstitutionRequest))
def test_the_orm_declares_no_impossible_foreign_key(model: Any) -> None:
    """The ORM previously named foreign keys the database could not hold.

    ``PharmacySaleLine.batch_id`` and both ``prescription_id`` columns declared
    ``ForeignKey`` onto integer-keyed tables while typed ``String(26)``.
    """
    for column in model.__table__.columns:
        for fk in column.foreign_keys:
            target = fk.column
            assert type(column.type) is type(target.type), (
                f"{model.__tablename__}.{column.name} declares a foreign key onto "
                f"{target.table.name}.{target.name} with a different type"
            )


# ── tenancy and idempotency ────────────────────────────────────────────────


def test_a_sale_is_tenant_scoped(session: Session) -> None:
    _labs(session)
    _sale(session, lab_id=LAB_A, number="M3-TENANT-A")
    _sale(session, lab_id=LAB_B, number="M3-TENANT-B")
    visible = session.query(PharmacySale).filter(PharmacySale.lab_id == LAB_A).all()
    assert [s.sale_number for s in visible] == ["M3-TENANT-A"]


def test_the_idempotency_key_is_unique_within_a_tenant(session: Session) -> None:
    _labs(session)
    _sale(session, number="M3-IDEM-1", idempotency_key="same-key")
    # The same key in another tenant is a different sale, not a conflict.
    _sale(session, lab_id=LAB_B, number="M3-IDEM-2", idempotency_key="same-key")
    with pytest.raises(IntegrityError), session.begin_nested():
        _sale(session, number="M3-IDEM-3", idempotency_key="same-key")
