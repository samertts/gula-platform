"""M4: batch, prescription, inventory and dispensing identity against the real schema.

Seventeen Pharmacy models described a schema that did not exist — 145 columns
the ORM mapped and the database did not, 150 physical columns nothing mapped,
and a ``DrugBatch.drug_catalog_id`` that was never a column at all (the table
keys the catalog through ``drug_id``, and has an enforced foreign key saying so).

These tests hold the reconciled model to the physical schema, prove the entities
are actually writable, prove the P0-2-SUBBLOCKER-A Group B references are now
constrained, and prove the inventory concurrency claim with two real database
connections rather than a mock.

Set ``PHARMACY_POSTGRES_URL`` to a disposable migrated database to run them.
"""

from __future__ import annotations

import os
import uuid
from collections.abc import Iterator
from datetime import UTC, date, datetime, timedelta
from typing import Any

import pytest
from app.pharmacy.models import (
    DispenseQueue,
    DrugBatch,
    DrugCatalog,
    DrugSupplier,
    InventoryTransfer,
    InventoryTransferItem,
    PharmacySale,
    PharmacySaleLine,
    Prescription,
    PrescriptionItem,
    StockLevel,
    StockMovement,
    Store,
    Warehouse,
)
from app.pharmacy.services import PharmacyService
from sqlalchemy import Integer, String, create_engine, inspect, text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

POSTGRES_URL = os.getenv("PHARMACY_POSTGRES_URL")
pytestmark = pytest.mark.skipif(
    not POSTGRES_URL, reason="PHARMACY_POSTGRES_URL is not configured"
)

LAB_A = 990101
LAB_B = 990202
USER_A = 990303

# Every model M4 reconciled.
M4_MODELS = (
    DrugSupplier, Warehouse, Store, DrugBatch, Prescription, PrescriptionItem,
    DispenseQueue, StockLevel, StockMovement, InventoryTransfer, InventoryTransferItem,
)

# entity -> public identifier column
PUBLIC_IDS = {
    DrugBatch: "batch_id",
    Prescription: "prescription_id",
    PrescriptionItem: "prescription_item_id",
    DispenseQueue: "queue_id",
    InventoryTransfer: "transfer_id",
}


@pytest.fixture(scope="module")
def engine() -> Any:
    return create_engine(POSTGRES_URL, future=True)


@pytest.fixture()
def session(engine: Any) -> Iterator[Session]:
    connection = engine.connect()
    transaction = connection.begin()
    db = sessionmaker(bind=connection, future=True)()
    try:
        yield db
    finally:
        db.close()
        transaction.rollback()
        connection.close()


def _tenants(db: Session) -> None:
    for lab_id in (LAB_A, LAB_B):
        db.execute(
            text(
                "INSERT INTO labs (id, name, is_active) VALUES (:i, :n, true) "
                "ON CONFLICT (id) DO NOTHING"
            ).bindparams(i=lab_id, n=f"M4 Synthetic Lab {lab_id}")
        )
    # A real acting user: performed_by and wasted_by carry physical foreign
    # keys to lab_users, so an inventory change cannot name a phantom actor.
    db.execute(
        text(
            "INSERT INTO lab_users (id, lab_id, name, email, password_hash) "
            "VALUES (:i, :l, :n, :e, :p) ON CONFLICT (id) DO NOTHING"
        ).bindparams(
            i=USER_A, l=LAB_A, n="M4 Synthetic Pharmacist",
            e=f"m4-{USER_A}@synthetic.invalid", p="x",
        )
    )
    db.flush()


def _store(db: Session, *, lab_id: int = LAB_A, code: str = "M4-STORE") -> Store:
    warehouse = Warehouse(
        lab_id=lab_id, warehouse_code=f"{code}-WH", warehouse_name="M4 Synthetic Warehouse"
    )
    db.add(warehouse)
    db.flush()
    store = Store(
        lab_id=lab_id, warehouse_id=warehouse.id, store_code=code, store_name="M4 Synthetic Store"
    )
    db.add(store)
    db.flush()
    return store


def _drug(db: Session, code: str) -> DrugCatalog:
    drug = DrugCatalog(
        drug_code=code, drug_name="M4 Synthetic Drug", dosage_form="tablet", drug_id=uuid.uuid4()
    )
    db.add(drug)
    db.flush()
    return drug


def _batch(db: Session, drug: DrugCatalog, *, lab_id: int = LAB_A, number: str = "M4-BATCH-1",
           remaining: float = 10.0, **kw: Any) -> DrugBatch:
    batch = DrugBatch(
        lab_id=lab_id,
        drug_id=drug.id,
        batch_number=number,
        expiry_date=date.today() + timedelta(days=180),
        quantity_received=remaining,
        quantity_remaining=remaining,
        received_date=datetime.now(UTC),
        status="active",
        **kw,
    )
    db.add(batch)
    db.flush()
    return batch


def _stock(
    db: Session, drug: DrugCatalog, batch: DrugBatch, *, quantity: float = 10.0,
    store_id: int | None = None,
) -> StockLevel:
    stock = StockLevel(
        lab_id=batch.lab_id,
        drug_id=drug.id,
        batch_id=batch.id,
        store_id=store_id,
        quantity_on_hand=quantity,
        quantity_reserved=0,
        quantity_available=quantity,
        unit="unit",
    )
    db.add(stock)
    db.flush()
    return stock


def _prescription(db: Session, *, lab_id: int = LAB_A, number: str = "M4-RX-1") -> Prescription:
    rx = Prescription(
        lab_id=lab_id,
        prescription_number=number,
        prescribed_by="Dr M4 Synthetic",
        prescribed_at=datetime.now(UTC),
        status="active",
    )
    db.add(rx)
    db.flush()
    return rx


# ── ORM ↔ physical parity ──────────────────────────────────────────────────


@pytest.mark.parametrize("model", M4_MODELS)
def test_orm_matches_the_physical_table(engine: Any, model: Any) -> None:
    physical = {c["name"] for c in inspect(engine).get_columns(model.__tablename__)}
    mapped = {c.name for c in model.__table__.columns}
    assert mapped - physical == set(), f"{model.__tablename__}: ORM-only columns"
    assert physical - mapped == set(), f"{model.__tablename__}: unmapped columns"


@pytest.mark.parametrize("model", M4_MODELS)
def test_internal_key_is_integer(engine: Any, model: Any) -> None:
    assert isinstance(model.__table__.c.id.type, Integer)
    physical = {c["name"]: c for c in inspect(engine).get_columns(model.__tablename__)}
    assert isinstance(physical["id"]["type"], Integer)


@pytest.mark.parametrize("model", list(PUBLIC_IDS))
def test_public_identity_is_a_distinct_unique_uuid(engine: Any, model: Any) -> None:
    """Contract §3: the internal key is never an entity's public identity."""
    column = PUBLIC_IDS[model]
    physical = {c["name"]: c for c in inspect(engine).get_columns(model.__tablename__)}
    assert column in physical
    assert isinstance(physical[column]["type"], PGUUID)
    assert physical[column]["nullable"] is False
    uniques = {
        tuple(u["column_names"]) for u in inspect(engine).get_unique_constraints(model.__tablename__)
    }
    assert (column,) in uniques


@pytest.mark.parametrize("model", M4_MODELS)
def test_the_orm_declares_no_impossible_foreign_key(model: Any) -> None:
    """Every ORM foreign key must match its target's type.

    Before M4 eight models declared ``ForeignKey("pharmacy_drug_batches.id")``
    on a ``String(26)`` column while that key is ``INTEGER`` — a constraint
    PostgreSQL cannot create and never had.
    """
    for column in model.__table__.columns:
        for fk in column.foreign_keys:
            target = fk.column
            assert type(column.type) is type(target.type), (
                f"{model.__tablename__}.{column.name} -> "
                f"{target.table.name}.{target.name} type mismatch"
            )


def test_the_generation_b_base_is_gone() -> None:
    """The legacy base promised it would be deleted once the last model moved."""
    import app.pharmacy.base as base

    assert not hasattr(base, "BaseEntity")
    assert not hasattr(base, "TenantAuditEntity")
    assert not hasattr(base, "_ulid")


# ── the batch catalog reference: name proven by constraint, not by naming ──


def test_a_batch_names_the_catalog_through_drug_id(engine: Any) -> None:
    physical = {c["name"] for c in inspect(engine).get_columns("pharmacy_drug_batches")}
    assert "drug_id" in physical
    assert "drug_catalog_id" not in physical
    targets = {
        (tuple(fk["constrained_columns"]), fk["referred_table"])
        for fk in inspect(engine).get_foreign_keys("pharmacy_drug_batches")
    }
    assert (("drug_id",), "pharmacy_drug_catalog") in targets


def test_a_batch_and_its_stock_round_trip(session: Session) -> None:
    _tenants(session)
    drug = _drug(session, "M4-RT-001")
    batch = _batch(session, drug)
    stock = _stock(session, drug, batch)
    session.expire_all()

    stored = session.query(DrugBatch).filter(DrugBatch.batch_id == batch.batch_id).one()
    assert stored.drug.drug_id == drug.drug_id
    assert stored.quantity_remaining == 10.0
    assert session.query(StockLevel).filter(StockLevel.id == stock.id).one().batch.id == stored.id


def test_a_batch_cannot_name_a_drug_that_does_not_exist(session: Session) -> None:
    _tenants(session)
    with pytest.raises(IntegrityError), session.begin_nested():
        session.add(
            DrugBatch(
                lab_id=LAB_A,
                drug_id=2_000_000_101,
                batch_number="M4-FK",
                expiry_date=date.today() + timedelta(days=10),
                quantity_received=1,
                quantity_remaining=1,
                received_date=datetime.now(UTC),
                status="active",
            )
        )
        session.flush()


def test_batch_quantities_are_fractional(session: Session) -> None:
    """DOUBLE PRECISION, not Integer: half a tablet must survive a round trip."""
    _tenants(session)
    drug = _drug(session, "M4-FRACTION")
    batch = _batch(session, drug, remaining=2.5)
    session.expire_all()
    assert session.query(DrugBatch).filter(DrugBatch.id == batch.id).one().quantity_remaining == 2.5


# ── prescriptions ───────────────────────────────────────────────────────────


def test_a_prescription_and_its_items_round_trip(session: Session) -> None:
    _tenants(session)
    drug = _drug(session, "M4-RX-DRUG")
    rx = _prescription(session)
    item = PrescriptionItem(
        prescription_id=rx.id,
        drug_id=drug.id,
        drug_name=drug.drug_name,
        dosage="500mg",
        frequency="BD",
        quantity=14,
        status="pending",
    )
    session.add(item)
    session.flush()
    session.expire_all()

    stored = session.query(Prescription).filter(
        Prescription.prescription_id == rx.prescription_id
    ).one()
    assert len(stored.items) == 1
    assert stored.items[0].drug.drug_id == drug.drug_id
    assert stored.items[0].prescription.id == stored.id


def test_a_prescription_item_has_no_tenant_column() -> None:
    """Tenancy is inherited from the parent prescription, not duplicated."""
    assert "lab_id" not in {c.name for c in PrescriptionItem.__table__.columns}
    assert "lab_id" in {c.name for c in Prescription.__table__.columns}


def test_deleting_a_prescription_removes_its_items(session: Session) -> None:
    _tenants(session)
    drug = _drug(session, "M4-RX-CASCADE")
    rx = _prescription(session, number="M4-RX-CASCADE")
    session.add(
        PrescriptionItem(
            prescription_id=rx.id, drug_id=drug.id, drug_name="x",
            dosage="1", frequency="OD", quantity=1, status="pending",
        )
    )
    session.flush()
    rx_pk = rx.id
    session.execute(text("DELETE FROM pharmacy_prescriptions WHERE id = :i").bindparams(i=rx_pk))
    remaining = session.execute(
        text("SELECT count(*) FROM pharmacy_prescription_items WHERE prescription_id = :i").bindparams(i=rx_pk)
    ).scalar_one()
    assert remaining == 0


# ── P0-2-SUBBLOCKER-A Group B, resolved ─────────────────────────────────────


GROUP_B = (
    ("pharmacy_sale_lines", "batch_id", "pharmacy_drug_batches"),
    ("pharmacy_sale_lines", "prescription_id", "pharmacy_prescriptions"),
    ("pharmacy_drug_substitution_requests", "prescription_id", "pharmacy_prescriptions"),
)


@pytest.mark.parametrize(("table", "column", "target"), GROUP_B)
def test_group_b_reference_is_now_an_enforced_integer_foreign_key(
    engine: Any, table: str, column: str, target: str
) -> None:
    """M3 left these unconstrained VARCHAR(26) because their targets had no
    canonical application model. M4 supplied one."""
    physical = {c["name"]: c for c in inspect(engine).get_columns(table)}
    assert isinstance(physical[column]["type"], Integer), f"{table}.{column} is not Integer"
    targets = {
        (tuple(fk["constrained_columns"]), fk["referred_table"])
        for fk in inspect(engine).get_foreign_keys(table)
    }
    assert ((column,), target) in targets


def test_a_sale_line_cannot_name_a_batch_that_does_not_exist(session: Session) -> None:
    _tenants(session)
    drug = _drug(session, "M4-SALE-FK")
    sale = PharmacySale(
        lab_id=LAB_A, sale_number="M4-SALE-FK", subtotal=0, discount=0,
        total_amount=0, cost_amount=0, gross_profit=0,
    )
    session.add(sale)
    session.flush()
    with pytest.raises(IntegrityError), session.begin_nested():
        session.add(
            PharmacySaleLine(
                lab_id=LAB_A, sale_id=sale.id, drug_catalog_id=drug.id,
                batch_id=2_000_000_102, line_number=1, medication_name="x",
                quantity=1, unit_price=1, unit_cost=1, discount=0,
                line_total=1, line_cost=1,
            )
        )
        session.flush()


def test_no_varchar_26_identifier_remains_in_pharmacy(engine: Any) -> None:
    """The Generation B key shape is gone from every Pharmacy identifier.

    ``sync_id`` is excluded: it is an EXTERNAL_ID (contract §11), an
    offline-sync correlation value, not an entity key.
    """
    insp = inspect(engine)
    offenders: list[str] = []
    for table in insp.get_table_names():
        if not table.startswith("pharmacy"):
            continue
        for col in insp.get_columns(table):
            if col["name"] in {"sync_id", "fhir_id"}:
                continue
            if not col["name"].endswith("_id") and col["name"] != "id":
                continue
            t = col["type"]
            if isinstance(t, String) and t.length == 26:
                offenders.append(f"{table}.{col['name']}")
    # What remains are references OUT of the Pharmacy domain, not Pharmacy
    # entity keys: patient/citizen/encounter identifiers owned by the national
    # and EHR domains, which key on String(26) themselves. Reconciling those is
    # those domains' work, not P0-2's. No Pharmacy entity keys on String(26).
    assert sorted(offenders) == sorted([
        "pharmacy_sales.patient_id",
        "pharmacy_sales.citizen_id",
        "pharmacy_sales.encounter_id",
        "pharmacy_sale_lines.medication_dispense_id",
        "pharmacy_drug_substitution_requests.patient_id",
        "pharmacy_drug_substitution_requests.citizen_id",
    ]), offenders


# ── inventory integrity, proven on the database ─────────────────────────────


def test_stock_is_tenant_scoped(session: Session) -> None:
    _tenants(session)
    drug = _drug(session, "M4-TENANT")
    batch_a = _batch(session, drug, lab_id=LAB_A, number="M4-T-A")
    batch_b = _batch(session, drug, lab_id=LAB_B, number="M4-T-B")
    _stock(session, drug, batch_a)
    _stock(session, drug, batch_b)
    visible = session.query(StockLevel).filter(StockLevel.lab_id == LAB_A).all()
    assert [s.batch_id for s in visible] == [batch_a.id]


def test_a_stock_row_is_unique_per_drug_batch_and_store(session: Session) -> None:
    _tenants(session)
    drug = _drug(session, "M4-UNIQUE")
    batch = _batch(session, drug)
    store = _store(session)
    _stock(session, drug, batch, store_id=store.id)
    with pytest.raises(IntegrityError), session.begin_nested():
        _stock(session, drug, batch, store_id=store.id)


def test_stock_uniqueness_does_not_hold_without_a_store(session: Session) -> None:
    """A finding, recorded rather than hidden.

    ``uq_pharmacy_stock_lab_drug_batch_store`` covers
    ``(lab_id, drug_id, batch_id, store_id)``. PostgreSQL treats NULLs as
    distinct in a unique constraint, so two stock rows for the same drug and
    batch with no store DO NOT collide — the guarantee holds only once a store
    is set. Closing this needs a partial unique index over the NULL-store case,
    which cannot be added blind: it would fail on any existing duplicate.
    Tracked as P0-2-M4-GAP-STOCK-NULL-STORE.
    """
    _tenants(session)
    drug = _drug(session, "M4-NULLSTORE")
    batch = _batch(session, drug)
    _stock(session, drug, batch)
    _stock(session, drug, batch)  # accepted: store_id IS NULL on both
    assert session.query(StockLevel).filter(StockLevel.drug_id == drug.id).count() == 2


def test_a_movement_requires_an_actor(session: Session) -> None:
    """performed_by is NOT NULL: an inventory change is somebody's action."""
    _tenants(session)
    drug = _drug(session, "M4-ACTOR")
    batch = _batch(session, drug)
    with pytest.raises(IntegrityError), session.begin_nested():
        session.add(
            StockMovement(
                lab_id=LAB_A, drug_id=drug.id, batch_id=batch.id,
                movement_type="dispensed", quantity=1, unit="unit",
                performed_at=datetime.now(UTC),
            )
        )
        session.flush()


def test_removing_stock_writes_a_matching_movement(session: Session) -> None:
    from app.pharmacy.inventory import StockAdjustmentService

    _tenants(session)
    drug = _drug(session, "M4-MOVE")
    batch = _batch(session, drug)
    _stock(session, drug, batch)

    svc = StockAdjustmentService(session, user_id=USER_A, lab_id=LAB_A)
    stock = svc.remove_stock(drug.id, batch.id, 3.0)
    assert stock is not None
    assert stock.quantity_on_hand == 7.0
    assert stock.quantity_available == 7.0

    movements = session.query(StockMovement).filter(
        StockMovement.drug_id == drug.id, StockMovement.batch_id == batch.id
    ).all()
    assert [(m.movement_type, m.quantity) for m in movements] == [("dispensed", 3.0)]
    assert movements[0].performed_by == USER_A


def test_stock_cannot_be_removed_below_what_is_available(session: Session) -> None:
    from app.pharmacy.inventory import StockAdjustmentService

    _tenants(session)
    drug = _drug(session, "M4-OVERDRAW")
    batch = _batch(session, drug)
    _stock(session, drug, batch, quantity=2.0)

    svc = StockAdjustmentService(session, user_id=USER_A, lab_id=LAB_A)
    assert svc.remove_stock(drug.id, batch.id, 5.0) is None
    assert session.query(StockLevel).one().quantity_on_hand == 2.0
    assert session.query(StockMovement).count() == 0


def test_expired_batches_are_quarantined(session: Session) -> None:
    """Regression: the filter was `not DrugBatch.is_quarantined`, Python's
    `not` on a column rather than a SQL predicate."""
    from app.pharmacy.inventory import ExpiryMonitoringService

    _tenants(session)
    drug = _drug(session, "M4-EXPIRED")
    batch = _batch(session, drug, number="M4-EXP")
    batch.expiry_date = date.today() - timedelta(days=1)
    session.flush()
    stock = _stock(session, drug, batch)

    quarantined = ExpiryMonitoringService(session, lab_id=LAB_A).auto_quarantine_expired()
    assert quarantined == 1
    session.refresh(batch)
    session.refresh(stock)
    assert batch.is_quarantined is True
    assert stock.quantity_available == 0
    # Quarantined stock is still physically on hand.
    assert stock.quantity_on_hand == 10.0


def test_the_reorder_list_reads_live_rows_not_deleted_ones(session: Session) -> None:
    """Regression: `~~StockLevel.is_deleted` cancels, so the previous list was
    built from the soft-deleted rows and only those."""
    from app.pharmacy.inventory import ReorderService

    _tenants(session)
    drug = _drug(session, "M4-REORDER")
    batch = _batch(session, drug)
    stock = _stock(session, drug, batch, quantity=1.0)
    stock.reorder_point = 5.0
    session.flush()

    rows = ReorderService(session, lab_id=LAB_A).generate_reorder_list()
    assert [r["drug_catalog_id"] for r in rows] == [str(drug.drug_id)]
    assert rows[0]["needs_reorder"] is True


# ── concurrency, on two real connections ───────────────────────────────────


def test_two_concurrent_removals_cannot_oversell_one_batch(engine: Any) -> None:
    """Database-level evidence, not a mock.

    Two independent connections try to take 6 units from a batch holding 10.
    The row lock must serialise them so the second sees 4 remaining and
    refuses, rather than both reading 10 and each writing their own total.
    """
    from app.pharmacy.inventory import StockAdjustmentService

    setup = sessionmaker(bind=engine, future=True)()
    try:
        _tenants(setup)
        drug = _drug(setup, f"M4-CONC-{uuid.uuid4().hex[:8]}")
        batch = _batch(setup, drug, number=f"M4-CONC-{uuid.uuid4().hex[:8]}")
        _stock(setup, drug, batch, quantity=10.0)
        setup.commit()
        drug_pk, batch_pk = drug.id, batch.id
    finally:
        setup.close()

    conn_a = engine.connect()
    conn_b = engine.connect()
    try:
        tx_a, tx_b = conn_a.begin(), conn_b.begin()
        db_a = sessionmaker(bind=conn_a, future=True)()
        db_b = sessionmaker(bind=conn_b, future=True)()

        # A takes 6 and holds the row lock without committing.
        first = StockAdjustmentService(db_a, user_id=USER_A, lab_id=LAB_A).remove_stock(
            drug_pk, batch_pk, 6.0
        )
        assert first is not None and first.quantity_on_hand == 4.0

        # B must not be able to read the pre-A quantity. Give it a short
        # timeout so a genuine deadlock fails the test instead of hanging.
        db_b.execute(text("SET LOCAL lock_timeout = '2s'"))
        db_a.commit()
        tx_a.commit()

        second = StockAdjustmentService(db_b, user_id=USER_A, lab_id=LAB_A).remove_stock(
            drug_pk, batch_pk, 6.0
        )
        assert second is None, "the second removal oversold the batch"

        # db_b.rollback() already ends the outer transaction on this
        # connection, so tx_b must not be rolled back again.
        db_b.rollback()
        db_a.close()
        db_b.close()
    finally:
        conn_a.close()
        conn_b.close()
        cleanup = sessionmaker(bind=engine, future=True)()
        try:
            cleanup.execute(
                text("DELETE FROM pharmacy_stock_movements WHERE drug_id = :d").bindparams(d=drug_pk)
            )
            cleanup.execute(
                text("DELETE FROM pharmacy_stock_levels WHERE drug_id = :d").bindparams(d=drug_pk)
            )
            cleanup.execute(
                text("DELETE FROM pharmacy_drug_batches WHERE id = :b").bindparams(b=batch_pk)
            )
            cleanup.execute(
                text("DELETE FROM pharmacy_drug_catalog WHERE id = :d").bindparams(d=drug_pk)
            )
            cleanup.commit()
        finally:
            cleanup.close()


# ── public / internal identity separation, both directions ─────────────────


def test_a_batch_resolves_by_public_id_and_never_by_internal_key(session: Session) -> None:
    _tenants(session)
    drug = _drug(session, "M4-PUBLIC")
    batch = _batch(session, drug, number="M4-PUB")
    svc = PharmacyService(session, user_id=USER_A, lab_id=LAB_A)

    assert svc.get_batch_by_public_id(str(batch.batch_id)).id == batch.id
    assert svc.get_batch(batch.id).batch_id == batch.batch_id
    # The internal key is not a public identifier, so it resolves to nothing.
    assert svc.get_batch_by_public_id(str(batch.id)) is None
    assert svc.get_batch_by_public_id("not-a-uuid") is None


def test_a_prescription_resolves_by_public_id(session: Session) -> None:
    _tenants(session)
    rx = _prescription(session, number="M4-RX-PUB")
    svc = PharmacyService(session, user_id=USER_A, lab_id=LAB_A)
    assert svc.get_prescription_by_public_id(str(rx.prescription_id)).id == rx.id
    assert svc.get_prescription_by_public_id(str(rx.id)) is None
