"""NC013-C04 — unverified NIDs must not disclose or merge identities."""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from app.routes import register
from app.services.mpi import resolver
from app.services.mpi.models import Citizen


class _FakeQuery:
    def __init__(self, first: object = None, rows: list | None = None) -> None:
        self._first = first
        self._rows = rows or []
        self.recorded_filters: list[object] = []

    def filter_by(self, *_args: object, **_kwargs: object) -> _FakeQuery:
        return self

    def filter(self, *args: object, **_kwargs: object) -> _FakeQuery:
        self.recorded_filters.extend(args)
        return self

    def order_by(self, *_args: object, **_kwargs: object) -> _FakeQuery:
        return self

    def limit(self, *_args: object, **_kwargs: object) -> _FakeQuery:
        return self

    def first(self) -> object:
        return self._first

    def all(self) -> list:
        return self._rows


class _FakeDB:
    def __init__(self, citizen_first: object = None, citizen_rows: list | None = None) -> None:
        self.citizen_query = _FakeQuery(citizen_first, citizen_rows)
        self.added: list[object] = []

    def query(self, model: object) -> _FakeQuery:
        if model is resolver.Citizen:
            return self.citizen_query
        return _FakeQuery()

    def add(self, obj: object) -> None:
        self.added.append(obj)

    def flush(self) -> None:
        return None


def test_self_registration_never_returns_victim_ulid_or_stores_unverified_nid() -> None:
    victim = Citizen(
        id=1,
        citizen_ulid="VICTIM00000000000000000001",
        nid_hash="victim-hash",
        nid_verified=True,
        status="active",
    )
    db = _FakeDB(citizen_first=victim)

    # The module must not import MPI's NID hasher at all; a self-asserted NID
    # is never authoritative and must not enter the verified MPI index.
    assert not hasattr(register, "mpi_hash_nid")

    returned_ulid = register._mint_citizen_from_self_registration(
        db,
        full_name="Synthetic Person",
        phone="+9647000000000",
        birth_date="1990-01-01",
        national_id="SYNTHETIC-VICTIM-NID",
    )

    assert returned_ulid is not None
    assert returned_ulid != victim.citizen_ulid
    assert len(db.added) == 1
    minted = db.added[0]
    assert minted.nid_hash is None
    assert minted.nid_verified is False


def test_unverified_resolve_ignores_nid(monkeypatch: pytest.MonkeyPatch) -> None:
    db = _FakeDB(citizen_rows=[])

    def fail_if_hashed(_value: str) -> str:
        raise AssertionError("unverified NID must not be hashed or used for matching")

    monkeypatch.setattr(resolver, "hash_national_id", fail_if_hashed)

    outcome = resolver.resolve_identity(
        db,
        lab_id=1,
        local_patient_id=100,
        name="Synthetic Person",
        national_id="SYNTHETIC-NID",
        claimed_by_user_id=7,
    )

    assert outcome.created is True
    assert outcome.match_method == "new"
    assert outcome.citizen.nid_hash is None


def test_verified_nid_fast_path_requires_verified_citizen(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    victim = SimpleNamespace(
        id=2,
        citizen_ulid="VERIFIED0000000000000000001",
        name_canonical="synthetic person",
        phone_last10=None,
        birth_year=None,
        birth_month=None,
        birth_day=None,
        gender=None,
        nid_hash="verified-hash",
        family_id_hash=None,
        merged_into_id=None,
        nid_verified=True,
        status="active",
        canonical=lambda: victim,
    )
    db = _FakeDB(citizen_first=victim)
    monkeypatch.setattr(resolver, "hash_national_id", lambda _value: "verified-hash")

    outcome = resolver.resolve_identity(
        db,
        lab_id=1,
        local_patient_id=101,
        name="Synthetic Person",
        national_id="SYNTHETIC-VERIFIED-NID",
        claimed_by_user_id=7,
        nid_verified=True,
    )

    assert outcome.match_method == "nid_exact"
    assert outcome.citizen is victim
    assert any("nid_verified" in str(item) for item in db.citizen_query.recorded_filters)
