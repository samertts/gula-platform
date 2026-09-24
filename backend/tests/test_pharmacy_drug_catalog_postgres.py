"""M1: the DrugCatalog ORM against the migration-built PostgreSQL schema.

These tests run against a database built by ``alembic upgrade head``, never by
``Base.metadata.create_all``. That distinction is the whole point: P0-2 existed
undetected precisely because the pharmacy tests built their schema from ORM
metadata, so the ORM could not disagree with the schema it had just created.

Set ``PHARMACY_POSTGRES_URL`` to a disposable migrated database to run them.
"""

from __future__ import annotations

import os
import uuid
from collections.abc import Iterator
from typing import Any

import pytest
from app.pharmacy.models import DrugCatalog
from app.pharmacy.services import PharmacyService
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.dialects import postgresql
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

POSTGRES_URL = os.getenv("PHARMACY_POSTGRES_URL")
pytestmark = pytest.mark.skipif(
    not POSTGRES_URL, reason="PHARMACY_POSTGRES_URL is not configured"
)

TABLE = "pharmacy_drug_catalog"
_MARKER = "M1TEST-"


@pytest.fixture(scope="module")
def engine() -> Any:
    return create_engine(POSTGRES_URL, future=True)


@pytest.fixture()
def session(engine: Any) -> Iterator[Session]:
    """A session whose writes are always rolled back.

    Every test runs inside a transaction that is discarded, so the shared
    migrated database is never mutated and tests cannot leak into each other.
    """
    connection = engine.connect()
    transaction = connection.begin()
    factory = sessionmaker(bind=connection, future=True)
    db = factory()
    try:
        yield db
    finally:
        db.close()
        transaction.rollback()
        connection.close()


def _service(db: Session) -> PharmacyService:
    # A lab_id is deliberately supplied: the catalog is global, so a tenant
    # context must make no difference to any catalog operation.
    return PharmacyService(db=db, user_id=None, lab_id=4242)


def _payload(code: str, **over: Any) -> dict[str, Any]:
    data: dict[str, Any] = {
        "drug_code": _MARKER + code,
        "drug_name": "Synthetic M1 Drug",
        "dosage_form": "tablet",
    }
    data.update(over)
    return data


# ── B. the physical schema is what we think it is ────────────────────────────


def test_physical_catalog_shape_is_authoritative(engine: Any) -> None:
    insp = inspect(engine)
    columns = {c["name"]: c for c in insp.get_columns(TABLE)}

    assert str(columns["id"]["type"]) == "INTEGER"
    assert columns["id"]["nullable"] is False

    drug_id = columns["drug_id"]
    assert str(drug_id["type"]) == "UUID"
    assert drug_id["nullable"] is False

    assert columns["drug_code"]["nullable"] is False
    # Contract §6: a global catalog carries no tenant column.
    assert "lab_id" not in columns

    uniques = {u["name"]: u["column_names"] for u in insp.get_unique_constraints(TABLE)}
    assert ["drug_id"] in uniques.values()
    indexes = {tuple(i["column_names"]) for i in insp.get_indexes(TABLE)}
    assert ("drug_id",) in indexes


def test_orm_declares_exactly_the_physical_columns(engine: Any) -> None:
    """The ORM must not require a column the database does not have."""
    physical = {c["name"]: c for c in inspect(engine).get_columns(TABLE)}
    mapped = {c.name: c for c in DrugCatalog.__table__.columns}

    assert set(mapped) - set(physical) == set(), "ORM declares non-existent columns"
    assert set(physical) - set(mapped) == set(), "ORM is blind to physical columns"

    def rendered(type_: Any) -> str:
        return str(type_.compile(dialect=postgresql.dialect()))

    for name, column in mapped.items():
        assert rendered(column.type) == rendered(physical[name]["type"]), name
        assert bool(column.nullable) is bool(physical[name]["nullable"]), name


# ── C/D/E. ORM round trip against the migrated schema ────────────────────────


def test_insert_and_retrieve_by_public_identity(session: Session) -> None:
    service = _service(session)
    drug = service.create_drug(_payload("INSERT"))
    session.flush()

    assert isinstance(drug.id, int), "internal key must be the integer the schema defines"
    assert isinstance(drug.drug_id, uuid.UUID)
    assert drug.drug_id.version == 4, "public identity must be a v4 UUID"

    found = service.get_drug_by_public_id(str(drug.drug_id))
    assert found is not None
    assert found.id == drug.id
    assert found.drug_code == _MARKER + "INSERT"


def test_public_identity_is_not_derived_from_any_stored_value(session: Session) -> None:
    """§10: drug_id is generated, never computed from the row's own data."""
    service = _service(session)
    drug = service.create_drug(_payload("DERIVE"))
    session.flush()

    for namespace in (uuid.NAMESPACE_DNS, uuid.NAMESPACE_URL, uuid.NAMESPACE_OID):
        for seed in (drug.drug_code, drug.drug_name, str(drug.id)):
            assert drug.drug_id != uuid.uuid5(namespace, seed)
            assert drug.drug_id != uuid.uuid3(namespace, seed)


def test_two_drugs_receive_distinct_identities(session: Session) -> None:
    service = _service(session)
    first = service.create_drug(_payload("DISTINCT-1"))
    second = service.create_drug(_payload("DISTINCT-2"))
    session.flush()
    assert first.drug_id != second.drug_id
    assert first.id != second.id


# ── F/G/H. mutability rules ──────────────────────────────────────────────────


def test_drug_code_remains_mutable(session: Session) -> None:
    """§4: the business code is editable through an authorised operation."""
    service = _service(session)
    drug = service.create_drug(_payload("MUTABLE"))
    session.flush()
    original_pk, original_identity = drug.id, drug.drug_id

    updated = service.update_drug(drug.id, {"drug_code": _MARKER + "MUTABLE-RENAMED"})
    session.flush()

    assert updated is not None
    assert updated.drug_code == _MARKER + "MUTABLE-RENAMED"
    # Editing the business code must move neither identity.
    assert updated.id == original_pk
    assert updated.drug_id == original_identity


def test_update_rejects_public_identity_mutation(session: Session) -> None:
    service = _service(session)
    drug = service.create_drug(_payload("IMMUTABLE"))
    session.flush()
    original = drug.drug_id

    with pytest.raises(ValueError, match="drug_id"):
        service.update_drug(drug.id, {"drug_id": str(uuid.uuid4())})

    assert service.get_drug(drug.id).drug_id == original


def test_update_rejects_internal_key_mutation(session: Session) -> None:
    service = _service(session)
    drug = service.create_drug(_payload("PKSTABLE"))
    session.flush()
    original = drug.id

    with pytest.raises(ValueError, match="immutable"):
        service.update_drug(drug.id, {"id": original + 10_000})

    assert service.get_drug(original) is not None


def test_client_cannot_choose_either_identity_at_creation(session: Session) -> None:
    service = _service(session)
    chosen = uuid.uuid4()
    drug = service.create_drug(
        _payload("CHOSEN", id=999_000_111, drug_id=str(chosen))
    )
    session.flush()

    assert drug.id != 999_000_111
    assert drug.drug_id != chosen


# ── I. the database, not just the service, enforces uniqueness ───────────────


def test_duplicate_public_identity_is_rejected_by_the_database(session: Session) -> None:
    service = _service(session)
    first = service.create_drug(_payload("DUP-A"))
    session.flush()

    # Inside a savepoint: the violation aborts this nested transaction only,
    # leaving the outer one usable for the fixture's rollback.
    with pytest.raises(IntegrityError), session.begin_nested():
        session.add(
            DrugCatalog(
                drug_code=_MARKER + "DUP-B",
                drug_name="Synthetic Duplicate",
                dosage_form="tablet",
                drug_id=first.drug_id,
            )
        )


def test_missing_public_identity_is_rejected_by_the_database(session: Session) -> None:
    """The column has no server default, so an omitted identity must fail."""
    with pytest.raises(IntegrityError, match="drug_id"), session.begin_nested():
        session.execute(
            text(
                "INSERT INTO pharmacy_drug_catalog "
                "(drug_code, drug_name, dosage_form, version, is_deleted,"
                " created_at, updated_at) "
                "VALUES (:c, :n, 'tablet', 1, false, now(), now())"
            ).bindparams(c=_MARKER + "NOID", n="Synthetic No Identity"),
        )


# ── J. global catalog semantics ──────────────────────────────────────────────


def test_catalog_reads_are_not_tenant_filtered(session: Session) -> None:
    """A drug created under one tenant context is visible under another."""
    creator = PharmacyService(db=session, user_id=None, lab_id=1001)
    drug = creator.create_drug(_payload("GLOBAL"))
    session.flush()

    other_tenant = PharmacyService(db=session, user_id=None, lab_id=2002)
    assert other_tenant.get_drug(drug.id) is not None
    assert other_tenant.get_drug_by_public_id(str(drug.drug_id)) is not None

    no_tenant = PharmacyService(db=session, user_id=None, lab_id=None)
    assert no_tenant.get_drug(drug.id) is not None


def test_search_is_not_tenant_filtered(session: Session) -> None:
    creator = PharmacyService(db=session, user_id=None, lab_id=1001)
    creator.create_drug(_payload("SEARCH", drug_name="Zzz Synthetic Searchable"))
    session.flush()

    other = PharmacyService(db=session, user_id=None, lab_id=2002)
    items, total = other.search_drugs(query="Zzz Synthetic Searchable")
    assert total >= 1
    assert any(d.drug_code == _MARKER + "SEARCH" for d in items)


def test_creating_a_drug_stamps_no_tenant(session: Session) -> None:
    service = _service(session)
    drug = service.create_drug(_payload("NOTENANT"))
    session.flush()
    assert not hasattr(drug, "lab_id")


def test_public_lookup_of_a_non_uuid_is_a_miss_not_a_crash(session: Session) -> None:
    assert _service(session).get_drug_by_public_id("not-a-uuid") is None
