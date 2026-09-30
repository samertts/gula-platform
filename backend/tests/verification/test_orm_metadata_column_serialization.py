"""IA-005 — a column named `metadata` must serialise to its value, never to the registry.

A declarative class already owns the attribute `metadata`: SQLAlchemy puts the
base's `MetaData` registry there. A model that needs a *column* called `metadata`
must therefore map it under another Python name (`metadata_`, or `extra_metadata`).

`to_dict()` used to read `getattr(self, col.name)`, so for those models it returned
the MetaData registry instead of the column value. FastAPI's `jsonable_encoder`
then walked the whole ORM topology until the stack was exhausted.

These tests pin the contract:

* the output key stays the **physical column name** (`metadata`) — that is what
  every base has always emitted and what clients see;
* the output value is the **mapped column value**;
* no SQLAlchemy schema object ever reaches a response.

They are dialect-free: `to_dict()` needs no database.
"""

from __future__ import annotations

import pytest
from fastapi.encoders import jsonable_encoder
from sqlalchemy import Column, Integer, MetaData, String
from sqlalchemy.orm import declarative_base

from shared.models import BaseEntityMixin

_MD = MetaData()
_Base = declarative_base(metadata=_MD)


class _WithMetadataColumn(BaseEntityMixin, _Base):
    """Mirrors the real shape: physical column `metadata`, attribute `metadata_`."""

    __tablename__ = "ia005_with_metadata"
    id = Column(Integer, primary_key=True)
    name = Column(String(32))
    metadata_ = Column("metadata", String(256))


class _WithAliasedMetadataColumn(BaseEntityMixin, _Base):
    """The other real spelling: physical column `metadata`, attribute `extra_metadata`."""

    __tablename__ = "ia005_aliased_metadata"
    id = Column(Integer, primary_key=True)
    extra_metadata = Column("metadata", String(256))


class _WithoutMetadataColumn(BaseEntityMixin, _Base):
    __tablename__ = "ia005_without_metadata"
    id = Column(Integer, primary_key=True)
    name = Column(String(32))


def _assert_no_schema_objects(value, where="payload"):
    """No SQLAlchemy schema object may appear anywhere in a serialised payload."""
    from sqlalchemy import Table
    from sqlalchemy.sql.schema import SchemaItem

    assert not isinstance(value, (MetaData, Table, SchemaItem)), (
        f"{where} carries a SQLAlchemy schema object ({type(value).__name__})"
    )
    if isinstance(value, dict):
        for k, v in value.items():
            _assert_no_schema_objects(v, f"{where}[{k!r}]")
    elif isinstance(value, (list, tuple, set)):
        for i, v in enumerate(value):
            _assert_no_schema_objects(v, f"{where}[{i}]")


# ── the defect itself ────────────────────────────────────────────────────────

def test_metadata_column_serialises_its_value_not_the_registry():
    row = _WithMetadataColumn(id=1, name="n", metadata_="the-column-value")
    payload = row.to_dict()
    assert payload["metadata"] == "the-column-value"
    assert not isinstance(payload["metadata"], MetaData)


def test_metadata_column_payload_is_json_encodable():
    """The regression that killed the process: jsonable_encoder must terminate."""
    row = _WithMetadataColumn(id=1, name="n", metadata_="v")
    encoded = jsonable_encoder(row.to_dict())   # recursed before the fix
    assert encoded["metadata"] == "v"


def test_aliased_metadata_column_also_resolves():
    """The fix must be mapper-driven, not a hard-coded `metadata_` special case."""
    row = _WithAliasedMetadataColumn(id=2, extra_metadata="aliased-value")
    payload = row.to_dict()
    assert payload["metadata"] == "aliased-value"
    assert "extra_metadata" not in payload, "the key must stay the physical column name"


def test_none_metadata_stays_none():
    row = _WithMetadataColumn(id=3, name="n")
    payload = row.to_dict()
    assert payload["metadata"] is None
    jsonable_encoder(payload)


def test_no_sqlalchemy_schema_object_reaches_a_payload():
    for row in (_WithMetadataColumn(id=4, name="n", metadata_="v"),
                _WithMetadataColumn(id=5, name="n"),
                _WithAliasedMetadataColumn(id=6, extra_metadata="v"),
                _WithoutMetadataColumn(id=7, name="n")):
        _assert_no_schema_objects(row.to_dict(), type(row).__name__)


# ── no collateral change ─────────────────────────────────────────────────────

def test_model_without_a_metadata_column_is_unaffected():
    row = _WithoutMetadataColumn(id=8, name="ordinary")
    payload = row.to_dict()
    assert payload == {"id": 8, "name": "ordinary"}


def test_ordinary_columns_keep_their_values_and_keys():
    row = _WithMetadataColumn(id=9, name="ordinary", metadata_="v")
    payload = row.to_dict()
    assert payload["id"] == 9
    assert payload["name"] == "ordinary"
    assert set(payload) == {"id", "name", "metadata"}, "no key added or dropped"


def test_keys_are_exactly_the_physical_column_names():
    for cls in (_WithMetadataColumn, _WithAliasedMetadataColumn, _WithoutMetadataColumn):
        row = cls(id=10)
        assert set(row.to_dict()) == {c.name for c in cls.__table__.columns}


# ── the real platform models ─────────────────────────────────────────────────

def _affected_real_models():
    """Every mapped class in the app whose table has a physical `metadata` column."""
    import gc

    import app.main
    from sqlalchemy.orm import Mapper

    out, seen = [], set()
    for obj in gc.get_objects():
        if not isinstance(obj, Mapper):
            continue
        cls = obj.class_
        key = f"{cls.__module__}.{cls.__qualname__}"
        if key in seen:
            continue
        seen.add(key)
        table = getattr(cls, "__table__", None)
        if table is None or "metadata" not in table.columns:
            continue
        if not hasattr(cls, "to_dict"):
            continue
        out.append(cls)
    return out


def test_the_affected_real_model_population_is_not_empty():
    """Guards the two tests below from passing vacuously."""
    models = _affected_real_models()
    assert len(models) > 100, (
        f"expected the measured population of affected models, found {len(models)}"
    )


def test_every_affected_real_model_serialises_metadata_safely():
    failures = []
    for cls in _affected_real_models():
        try:
            row = cls()
        except Exception:
            continue          # a model whose __init__ demands arguments
        try:
            payload = row.to_dict()
        except Exception as exc:                        # pragma: no cover
            failures.append(f"{cls.__name__}: to_dict() raised {type(exc).__name__}: {exc}")
            continue
        if isinstance(payload.get("metadata"), MetaData):
            failures.append(f"{cls.__name__}.to_dict()['metadata'] is a MetaData registry")
            continue
        try:
            jsonable_encoder(payload)
        except RecursionError:
            failures.append(f"{cls.__name__}: jsonable_encoder recursed")
    joined = "\n  ".join(failures[:20])
    assert not failures, f"IA-005 still present on {len(failures)} model(s):\n  {joined}"


@pytest.mark.parametrize("model_name", ["AllergyIntolerance", "ClinicalNote", "ConditionRecord"])
def test_real_ehr_models_serialise_metadata_safely(model_name):
    """A real affected EHR model — the surface RB-3 audited."""
    import app.ehr.models as ehr_models

    cls = getattr(ehr_models, model_name)
    assert "metadata" in cls.__table__.columns, f"{model_name} no longer carries the column"
    row = cls(patient_id="01ARZ3NDEKTSV4RRFFQ69G5FAV", metadata_={"k": "v"})
    payload = row.to_dict()
    assert payload["metadata"] == {"k": "v"}
    assert jsonable_encoder(payload)["metadata"] == {"k": "v"}


# ── every column-walking serializer in the codebase, not just the ORM bases ───

def _column_walking_serializers():
    """Source sites that iterate `__table__.columns` and read values off an instance.

    Such a site must resolve through the mapper. Both `getattr(obj, col.name)` and
    `getattr(obj, col.key)` are the IA-005 defect: for
    `metadata_ = Column("metadata", ...)` **both** attributes are `"metadata"`, so
    either lookup returns the registry. Only the mapper knows the value lives under
    `metadata_`.
    """
    import pathlib
    import re

    hits = []
    for path in sorted(pathlib.Path("app").rglob("*.py")):
        try:
            src = path.read_text()
        except OSError:
            continue
        for match in re.finditer(r"for (\w+) in [\w.]*__table__\.columns", src):
            var = match.group(1)
            window = src[match.end():match.end() + 400]
            pattern = r"getattr\(\s*\w+\s*,\s*" + re.escape(var) + r"\.(name|key)\s*\)"
            if re.search(pattern, window):
                line = src[: match.start()].count("\n") + 1
                hits.append(f"{path}:{line}")
    return hits


def test_no_serializer_reads_a_column_value_by_its_physical_name():
    """`getattr(obj, col.name)` yields the MetaData registry for a `metadata` column.

    Five sites carried this beyond the ORM bases: `app/nhdw/offline.py` (all 13
    offline-sync tables have the column), the three `_model_to_dict` route helpers in
    nursing / nhdw / hospital, and the blood-bank fallback. Pinned as an empty set: a
    new copy anywhere fails here.
    """
    offenders = _column_walking_serializers()
    assert offenders == [], (
        "these sites read a column value by its physical name instead of through the "
        f"mapper, so a column named `metadata` yields the registry: {offenders}"
    )


def test_offline_sync_payload_carries_the_column_value():
    """The nhdw offline-sync serialiser must emit the value, keyed by column name."""
    from shared.models import serialize_columns

    row = _WithMetadataColumn(id=11, name="n", metadata_={"unit": "mg"})
    payload = serialize_columns(row)
    assert payload["metadata"] == {"unit": "mg"}
    _assert_no_schema_objects(payload, "offline-sync payload")
    jsonable_encoder(payload)


def test_there_is_one_external_key_convention_and_it_is_the_column_name():
    """Every serializer emits the physical column name, so the external key is `metadata`.

    An earlier reading of this code assumed `col.key` was the mapped attribute and that
    the route helpers therefore emitted `metadata_`. That is wrong: for
    `metadata_ = Column("metadata", ...)` SQLAlchemy leaves `col.key == col.name ==
    "metadata"`, and only the mapper carries `metadata_`. There is one convention, and
    both lookups were equally defective.
    """
    row = _WithMetadataColumn(id=12, name="n", metadata_="v")
    column = row.__table__.columns["metadata"]
    assert column.name == "metadata"
    assert column.key == "metadata", "col.key is not the mapped attribute"
    assert [k for k, c in type(row).__mapper__.columns.items() if c.name == "metadata"] == [
        "metadata_"
    ], "only the mapper knows the attribute"
    assert row.to_dict()["metadata"] == "v"


def test_route_helper_shape_resolves_through_the_mapper():
    """The nursing / nhdw / hospital helper shape: excluded keys plus ISO dates."""
    from shared.models import serialize_columns

    row = _WithMetadataColumn(id=13, name="n", metadata_={"k": "v"})
    payload = serialize_columns(
        row,
        exclude={"lab_id", "is_deleted", "deleted_at", "version"},
        isoformat_dates=True,
    )
    assert payload["metadata"] == {"k": "v"}
    assert "version" not in payload
    _assert_no_schema_objects(payload, "route-helper payload")
    jsonable_encoder(payload)
