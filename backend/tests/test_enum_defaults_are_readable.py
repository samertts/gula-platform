"""NR-085 — a column's own default must be a value its mapper can read.

The trust platform had nine `Enum` columns whose model and migration disagreed
about the same concept. SQLAlchemy persists an enum member's **name** unless
`values_callable` says otherwise; every migration wrote its `server_default` as
the member's **value**. So `trust_consent_records.status` defaulted to
``'pending'`` while its mapper only understood ``'PENDING'``, and the database's
own default was unreadable by the model that owns the column.

That is invisible to every other guard here. The column exists, so
`test_mapped_tables_are_readable.py` is satisfied; the names match, so no
migration check objects; equality against the enum member compiles fine, so
nothing raises until a row actually arrives carrying the default. Then a plain
``SELECT *`` raises for the whole table -- one bad row makes every listing fail --
and ``WHERE status == ConsentStatus.PENDING`` quietly matches only the other
spelling, which is an undercount rather than an error.

This file asserts the invariant directly and generally, so it also covers the
33 enum-mapped columns sitting on tables that are still unreadable
(NR-082 radiology, NR-074 NHDW): when those tables are reconciled, they cannot
reintroduce the same split without failing here.

The database has **no native enum types at all** -- every enum-mapped column is
`character varying` -- which is asserted below, because it is the premise the
rest of this reasoning rests on.
"""

from __future__ import annotations

import os

import pytest
import sqlalchemy as sa

pytestmark = pytest.mark.integration

DATABASE_URL = os.environ.get("GULA_SCHEMA_DATABASE_URL") or os.environ.get(
    "MIGRATION_DATABASE_URL",
)

#: Enum-mapped columns whose physical `server_default` the mapper cannot read.
#: Empty, and it must stay empty: an entry here is a column whose own default
#: value poisons any listing of the table.
DECLARED_UNREADABLE_DEFAULTS: dict[tuple[str, str], str] = {}

#: Measured: 9 enum-mapped columns on readable tables, all `trust_*`. The floor
#: sits just under it so the test cannot pass by finding nothing -- the failure
#: mode NR-079 was about.
MINIMUM_ENUM_COLUMNS = 8


def _require_database() -> str:
    if not DATABASE_URL:
        pytest.skip("GULA_SCHEMA_DATABASE_URL / MIGRATION_DATABASE_URL not set")
    return DATABASE_URL


@pytest.fixture(scope="module")
def registry():
    from tests.test_alembic_metadata_registry import _load_registry

    saved = dict(os.environ)
    try:
        yield _load_registry()
    finally:
        os.environ.clear()
        os.environ.update(saved)


@pytest.fixture(scope="module")
def enum_columns(registry):
    """Every enum-mapped column that exists physically, with its real default."""
    engine = sa.create_engine(_require_database())
    with engine.connect() as connection:
        physical: dict[str, dict[str, tuple[str, str | None]]] = {}
        for table, column, data_type, default in connection.execute(sa.text(
            "SELECT table_name, column_name, data_type, column_default "
            "FROM information_schema.columns WHERE table_schema = 'public'",
        )):
            physical.setdefault(table, {})[column] = (data_type, default)
        native = [row[0] for row in connection.execute(sa.text(
            "SELECT DISTINCT t.typname FROM pg_type t JOIN pg_enum e ON e.enumtypid = t.oid",
        ))]
    engine.dispose()

    found = []
    seen: set[str] = set()
    for _label, metadata in registry:
        for name, table in metadata.tables.items():
            if name in seen or name not in physical:
                continue
            seen.add(name)
            if {c.name for c in table.columns} - set(physical[name]):
                continue  # unreadable table; NR-083's ledger owns it
            for column in table.columns:
                if isinstance(column.type, sa.Enum):
                    data_type, default = physical[name][column.name]
                    found.append((name, column.name, column.type, data_type, default))
    return {"columns": found, "native_enum_types": native}


def _literal(server_default: str | None) -> str | None:
    """`'pending'::character varying` -> `pending`."""
    if server_default is None:
        return None
    text = server_default.split("::")[0].strip()
    return text[1:-1] if text.startswith("'") and text.endswith("'") else None


def test_the_probe_found_the_enum_columns(enum_columns):
    assert len(enum_columns["columns"]) >= MINIMUM_ENUM_COLUMNS, (
        f"only {len(enum_columns['columns'])} enum-mapped columns were found; "
        "the probe is not reaching a database at migration head"
    )


def test_the_database_has_no_native_enum_types(enum_columns):
    """The premise. If this changes, every assertion below needs rethinking."""
    assert not enum_columns["native_enum_types"], (
        "PostgreSQL now has native enum types "
        f"{enum_columns['native_enum_types']}; enum-mapped columns can no longer "
        "be assumed to be character varying"
    )


def test_every_enum_column_compiles_to_the_type_it_actually_has(enum_columns):
    from sqlalchemy.dialects import postgresql

    wrong = {
        f"{table}.{column}": (type_.compile(dialect=postgresql.dialect()), data_type)
        for table, column, type_, data_type, _default in enum_columns["columns"]
        if not type_.compile(dialect=postgresql.dialect()).upper().startswith("VARCHAR")
    }
    assert not wrong, (
        "these enum mappers compile to a native PostgreSQL enum type, which this "
        f"database does not have: {wrong}. Pass native_enum=False."
    )


def test_every_enum_column_can_read_its_own_default(enum_columns):
    """The invariant the trust platform broke."""
    engine = sa.create_engine(_require_database())
    unreadable: dict[str, str] = {}
    try:
        for table, column, type_, _data_type, default in enum_columns["columns"]:
            value = _literal(default)
            if value is None:
                continue
            processor = type_.result_processor(engine.dialect, None)
            try:
                if processor is not None:
                    processor(value)
            except Exception as exc:  # any failure to read the default is the finding
                unreadable[f"{table}.{column}"] = f"default {value!r}: {type(exc).__name__}"
    finally:
        engine.dispose()

    unexpected = {k: v for k, v in unreadable.items()
                  if tuple(k.split(".", 1)) not in DECLARED_UNREADABLE_DEFAULTS}
    assert not unexpected, (
        "these columns have a server_default their own mapper cannot read, so any "
        "row taking the default makes SELECT * raise for the whole table: "
        f"{unexpected}"
    )
