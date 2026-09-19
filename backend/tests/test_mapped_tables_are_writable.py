"""NR-086 — a mapper that cannot resolve its own foreign keys cannot be written.

SQLAlchemy resolves every `ForeignKey` target during flush, when it sorts the
mapper's tables. A target that lives in a *different* `MetaData` cannot be found,
so the write raises before any SQL is emitted:

    session.add(ConsentRecord(...)); session.flush()
    NoReferencedTableError: Foreign key associated with column
    'trust_consent_records.guardian_id' could not find table 'lab_users'

Reads were unaffected, which is exactly why this hid. `SELECT` never sorts
tables, so the table looked healthy to `test_mapped_tables_are_readable.py`, to
every migration check, and to a route that only lists. It failed the first time
something tried to persist.

**It was not one table.** Asking which mappers could resolve every foreign key
target inside their own `MetaData` gave **76 tables carrying 310 unresolvable
foreign keys** — independently equal to the cross-base foreign-key population
NR-078 measured by a different route. NR-078 recorded those 310 as a *topology*
problem, something that stopped `alembic autogenerate` from running. They were
also 76 tables that **no ORM write could reach**, and that consequence had not
been stated.

Found by running the proof this repository had never run: a real `Session`, a
real model instance, a real `flush`. Every earlier NR-085 proof used Core
`select()` and raw SQL, which never trigger table sorting — so the trust
platform's write path had been described as working when it had never worked.

The live instance was `app/trust/routes.py`: 13 registered paths, of which
**six are writes** (`POST /api/v1/trust/consent`, `/consent/{id}/withdraw`,
`/sign`, `/timestamp`, `/compliance/check`, `/compliance/evidence`). All six
landed on the four trust tables carrying a cross-base foreign key, and all six
failed. Consent capture and consent withdrawal were among them.

── The repair ───────────────────────────────────────────────────────────────

`app/orm_topology.py` constructs one shared `MetaData` and the seven bases in
the closure — the five that declare cross-base foreign keys plus the two that
own their targets — are built against it. All 310 resolve. The population of
unwritable tables is **zero** and `DECLARED_UNWRITABLE` is empty.

The ledger stays, empty, because the ratchet is the point: the first mapper to
declare a foreign key across a base boundary again fails
`test_no_undeclared_table_is_unwritable` with the table named, and reads will
still work, so nothing else in this suite would notice.

**This guard is static and needs no database**, which is why it runs in the unit
job: whether a mapper's declared targets exist in its own metadata is answerable
from the registry alone. `test_the_repaired_write_path_actually_writes` is the
other half — the behavioural proof, on the exact model whose flush produced the
traceback above.
"""

from __future__ import annotations

import pytest

#: Mapped table -> number of foreign keys whose target table is absent from the
#: mapper's own MetaData. Each such table raises NoReferencedTableError on any
#: INSERT or UPDATE through the ORM. Empty since NR-086; may never grow.
DECLARED_UNWRITABLE: dict[str, int] = {}

#: Measured: all 715 distinct mapped tables resolve every target. The floor sits
#: just under it so the ledger cannot be kept empty by deleting mappers or
#: unregistering a base, and is not a round number chosen in advance.
MINIMUM_WRITABLE = 705

#: Likewise for the instrument. 715 distinct tables are registered today.
MINIMUM_PROBED = 705


@pytest.fixture(scope="module")
def registry():
    import os

    from tests.test_alembic_metadata_registry import _load_registry

    saved = dict(os.environ)
    try:
        yield _load_registry()
    finally:
        os.environ.clear()
        os.environ.update(saved)


@pytest.fixture(scope="module")
def resolution(registry):
    """Per table, how many declared FK targets are missing from its own MetaData."""
    unwritable: dict[str, int] = {}
    writable: set[str] = set()
    for _label, metadata in registry:
        own = set(metadata.tables)
        for name, table in metadata.tables.items():
            missing = sum(
                1 for fk in table.foreign_keys
                if fk.target_fullname.split(".")[0] not in own
            )
            if missing:
                unwritable.setdefault(name, missing)
            else:
                writable.add(name)
    return {"unwritable": unwritable, "writable": writable}


def test_the_probe_walked_the_registry(resolution):
    """An instrument that measures nothing agrees with every ledger."""
    total = len(resolution["writable"]) + len(resolution["unwritable"])
    assert total >= MINIMUM_PROBED, (
        f"only {total} mapped tables were walked; the registry did not load"
    )


def test_no_undeclared_table_is_unwritable(resolution):
    """The invariant. A new cross-base ForeignKey makes its table unwritable."""
    unexpected = sorted(set(resolution["unwritable"]) - set(DECLARED_UNWRITABLE))
    assert not unexpected, (
        "these mapped tables declare a ForeignKey whose target is in a different "
        f"MetaData, so every ORM INSERT and UPDATE on them raises "
        f"NoReferencedTableError before emitting SQL: {unexpected}. Reads will "
        "still work, so nothing else in this suite would notice. If the target "
        "belongs to a base outside the shared namespace, see app/orm_topology.py."
    )


def test_the_unwritable_ledger_does_not_rot(resolution):
    """A table that has been repaired must be removed from the ledger."""
    resolved = sorted(set(DECLARED_UNWRITABLE) - set(resolution["unwritable"]))
    assert not resolved, (
        f"these tables now resolve every foreign key and must be deleted from "
        f"DECLARED_UNWRITABLE: {resolved}"
    )


def test_the_recorded_counts_are_exact(resolution):
    """Half a repair is not a repair, and the ledger has to show which half."""
    drifted = {
        name: {"declared": DECLARED_UNWRITABLE[name], "measured": measured}
        for name, measured in sorted(resolution["unwritable"].items())
        if name in DECLARED_UNWRITABLE and measured != DECLARED_UNWRITABLE[name]
    }
    assert not drifted, (
        f"the number of unresolvable foreign keys has changed: {drifted}"
    )


def test_the_writable_population_never_shrinks(resolution):
    """The other half of the ratchet.

    Deleting a mapper, or unregistering a declarative base, would empty the
    ledger above while making the platform strictly worse.
    """
    assert len(resolution["writable"]) >= MINIMUM_WRITABLE, (
        f"only {len(resolution['writable'])} mapped tables resolve every foreign "
        f"key, against a floor of {MINIMUM_WRITABLE}: mappers or a registered "
        "metadata object have been removed rather than reconciled"
    )


def test_the_repaired_write_path_actually_writes(registry):
    """The behavioural half, on the model whose flush produced the traceback.

    Everything above is static: it asks the registry whether a target resolves.
    That is the right question and it is not the whole question — the defect was
    found by executing a flush, and a static ledger that agreed with a broken
    runtime is how NR-085 described six failing endpoints as working.

    So this does what NR-086 did: a real `Session`, a real `ConsentRecord`, a
    real `flush`, then a real `UPDATE` — the path that raised
    `NoReferencedTableError: ... could not find table 'lab_users'`.

    Only the tables this write touches are built. `create_all` over the whole
    shared namespace is a different assertion (and SQLite cannot render every
    column type in it), and building 447 tables to insert one row would make the
    failure mode of this test uninformative.
    """
    import sqlalchemy as sa
    from app.orm_topology import SHARED_METADATA
    from app.trust.models import ConsentRecord
    from sqlalchemy.orm import Session

    wanted = ["trust_consent_records", "patients", "lab_users", "labs"]
    tables = [SHARED_METADATA.tables[name] for name in wanted]

    engine = sa.create_engine("sqlite://")
    try:
        SHARED_METADATA.create_all(engine, tables=tables, checkfirst=True)
        with Session(engine) as session:
            record = ConsentRecord(
                patient_id=1,
                lab_id=1,
                purpose="treatment",
                status="granted",
                consent_hash="c" * 64,
                consent_version="1.0",
            )
            session.add(record)
            session.flush()          # NR-086: this is the statement that raised
            assert record.id is not None

            record.status = "withdrawn"
            session.flush()          # and the UPDATE path failed identically
            session.commit()

            assert session.query(ConsentRecord).count() == 1
    finally:
        engine.dispose()
