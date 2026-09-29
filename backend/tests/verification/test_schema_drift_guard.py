"""Regression guard: what the ORM writes must exist in the database.

This is the detector that found NR-023, generalised so the same class of defect
cannot recur unnoticed in another domain.

The existing static guard in ``tests/migrations/test_migration_graph_integrity.py``
asks a different and weaker question — does *a* migration create this table —
and NR-023 passed it comfortably: a migration does create
``critical_care_infusions``, and another migration does add its verification
columns.  What no static check could see is that the second migration sits on a
branch reachable only through ``head``, and ``head`` cannot be applied because it
fails earlier at NR-003.  Reachability is a property of the database you can
actually build, so proving it needs a database.

Three properties are asserted, and the split matters.

A **hard invariant** on the tables backing ``ClinicalCommandGuard``-protected
write paths: each is allowed only the divergence already recorded against it and
nothing more.  A missing column there does not degrade a feature — it turns a
clinical command into a 500 with no receipt and no audit row.

A **ratchet** on the platform-wide count, so a 692-column remediation programme
cannot quietly grow while it is open.  Deliberately a count, not a list: the list
belongs in the finding, and a list here would be a file nobody re-reads.

An **exactness** check on each recorded critical divergence.  Loose assertions
were rejected: ``assert drift`` keeps passing while a third column vanishes, and
``assert not drift`` is simply red.  Pinning the exact set means a repair fails
this file as loudly as a new divergence, and either way a human reads the diff.
"""

from __future__ import annotations

import collections
from typing import Any

import pytest

from . import harness

pytestmark = harness.requires_postgres()


# Measured on a database built by `alembic upgrade 20260908_0002` — the furthest
# revision that currently applies, since `head` fails at NR-003.  781 mapped ORM
# classes, 391 physical tables, 405 mapped tables with no physical table at all,
# 84 tables with column drift, 692 missing columns in total.
KNOWN_CRITICAL_DRIFT: dict[str, set[str]] = {
    # NR-023.  The high-alert infusion second-actor check cannot execute.
    "critical_care_infusions": {"verified_by", "verified_at"},
    # NR-025.  Account-lockout state has nowhere to live, on both identity tables.
    "lab_users": {"failed_login_attempts", "locked_until"},
    "users": {"failed_login_attempts", "locked_until"},
    # Tenancy and scope bindings.
    "service_accounts": {"lab_id"},
    "clinical_lab_facility_bindings": {"niam_facility_id", "niam_organization_id"},
    "organizations": {"org_id", "org_type", "parent_org_id", "updated_at"},
}

# Tables backing the eight ClinicalCommandGuard-protected domains, with the
# divergence each is currently allowed.  pharmacy_prescriptions and
# radiology_orders are recorded here because the guard found them: NR-023 is not
# one domain's accident, it reaches three of the guarded clinical write paths.
CLINICAL_COMMAND_ALLOWANCE: dict[str, set[str]] = {
    "clinical_command_receipts": set(),
    "audit_logs": set(),
    "blood_bank_units": set(),
    "blood_bank_reservations": set(),
    "critical_care_admissions": set(),
    "critical_care_infusions": {"verified_by", "verified_at"},
    "pharmacy_prescriptions": {
        "authored_on",
        "diagnosis",
        "diagnosis_system",
        "dispense_interval",
        "encounter_id",
        "intent",
        "metadata",
        "note",
        "prescriber_id",
        "priority",
        "signed_at",
        "signed_by",
        "substitution_allowed",
        "valid_from",
        "valid_to",
    },
    "radiology_orders": {
        "diagnosis_system",
        "encounter_id",
        "extra_metadata",
        "ordering_department_id",
        "ordering_provider_id",
        "requested_date",
        "scheduled_date",
    },
}

TOTAL_DRIFTED_TABLES = 84

# NR-006, RESOLVED 2026-09-26, so this set is deliberately empty.
#
# It used to hold ``national_facilities``, which was mapped by
# ``app.national.domain.facility.Facility`` (24 columns the table lacks) and by
# ``app.models.clinical_scope.NationalFacility`` (an exact match), so which
# module a caller imported decided whether the write succeeded.  NR-074's shared
# ``MetaData`` forced the choice -- the first carried ``extend_existing=True``
# and silently unioned itself into the second, producing a 30-column ``Table``
# with 24 phantom columns -- and the physical schema decided it.  The richer
# class is retired; see ``docs/architecture/NR-006-national-facilities-ownership.md``.
#
# An empty set is a stronger pin than a one-element one: any dual mapping now
# fails, including a reintroduction of this one under a different name.
KNOWN_MULTI_OWNED: set[str] = set()


def _classes_by_table() -> dict[str, list[Any]]:
    """Every mapped class, grouped by table name.

    Importing ``app.main`` is what loads the model packages; the platform has
    several declarative bases rather than one, so there is no single metadata
    object to walk.  Garbage-collector inspection is used deliberately — it sees
    every mapped class regardless of which base it belongs to, and a per-base
    walk that missed a base would silently narrow this guard.  Grouping rather
    than de-duplicating is what makes a dual-owned table visible.

    NR-081: the sweep is confined to classes declared under the ``app`` package.
    Without that, any mapped class alive anywhere in the process is counted, so a
    test module declaring its own model changes this guard's numbers — measured,
    a throwaway class on an existing table takes the drifted count from 84 to 85
    and invents a dual-owner entry. That made the count depend on which tests ran
    first, which is a ratchet that can pass for the wrong reason.

    The filter is a no-op on today's tree, and that is the point: all 780 mapped
    classes are under ``app.`` since NR-086b collapsed the duplicate
    ``backend.app.*`` import path, so nothing real is excluded and nothing
    foreign is admitted.
    """
    import gc

    import app.main

    found: dict[str, list[Any]] = collections.defaultdict(list)
    for obj in gc.get_objects():
        try:
            if isinstance(obj, type) and hasattr(obj, "__tablename__") and hasattr(obj, "__table__"):
                if not getattr(obj, "__module__", "").startswith("app."):
                    continue
                found[obj.__table__.name].append(obj)
        except Exception:
            continue
    return dict(found)


@pytest.fixture(scope="module")
def Session() -> Any:
    factory = harness.session_factory(pool_size=2)
    yield factory
    harness.dispose(factory)


@pytest.fixture(scope="module")
def report(Session: Any) -> dict[str, Any]:
    return harness.drift_report(Session, _classes_by_table())


def test_the_verification_database_was_built_by_migrations(Session: Any) -> None:
    """Fail loudly if handed a ``create_all`` database, which proves nothing.

    A database built from the ORM cannot exhibit ORM/database drift by
    construction, so every assertion below would pass vacuously.  The stamped
    Alembic revision is the evidence that migrations built this schema.
    """
    rows = harness.committed(Session, "SELECT version_num FROM alembic_version")
    assert rows, "no alembic_version row: this database was not built by migrations"


@pytest.mark.parametrize("table", sorted(KNOWN_CRITICAL_DRIFT))
def test_known_critical_drift_is_pinned_exactly(report: dict[str, Any], table: str) -> None:
    """Each recorded divergence still matches, column for column."""
    assert report["drift"].get(table, set()) == KNOWN_CRITICAL_DRIFT[table]


def test_no_clinical_command_table_gains_new_drift(report: dict[str, Any]) -> None:
    """A guarded clinical write path must not lose a column it writes.

    No tolerance parameter here on purpose.  Each table is allowed exactly the
    divergence already recorded against it; anything further is a new defect on
    a path that carries idempotency claims and audit rows.
    """
    offenders: dict[str, Any] = {}
    for table, allowed in CLINICAL_COMMAND_ALLOWANCE.items():
        if table in report["absent"]:
            offenders[table] = "table absent from the database entirely"
            continue
        unexpected = report["drift"].get(table, set()) - allowed
        if unexpected:
            offenders[table] = sorted(unexpected)
    assert offenders == {}, f"guarded clinical tables gained drift: {offenders}"


def test_platform_wide_drift_does_not_grow(report: dict[str, Any]) -> None:
    """The count of drifted tables is held at its measured value."""
    drifted = sorted(report["drift"])
    assert len(drifted) == TOTAL_DRIFTED_TABLES, (
        f"drifted table count moved from {TOTAL_DRIFTED_TABLES} to {len(drifted)}; "
        f"tables now drifting: {drifted}"
    )
    # Reported alongside rather than pinned: which tables are absent is a
    # property of the revision an operator could apply, so a fixed number here
    # would fail for a legitimate reason the day NR-003 is repaired.
    assert report["absent"], "expected mapped tables with no physical table on a partial build"


def test_only_the_known_table_is_mapped_by_more_than_one_class(report: dict[str, Any]) -> None:
    """No physical table is mapped by two classes. NR-006 was the last one.

    Still asserting the set rather than the count, so a swap — one dual mapping
    retired while another appears — cannot pass. With ``KNOWN_MULTI_OWNED`` now
    empty this is simply the invariant, and it matters more than it did: under
    NR-074's shared ``MetaData`` a second declaration carrying
    ``extend_existing=True`` does not raise, it silently unions itself into the
    first. SQLAlchemy will not catch this, so the assertion has to.
    """
    assert set(report["multi_owned"]) == KNOWN_MULTI_OWNED, (
        f"tables mapped by more than one class: {report['multi_owned']}. "
        "NR-006 closed this for national_facilities; a new entry here is a new "
        "ownership collision, and under one shared MetaData it will have merged "
        "the two column sets rather than failing."
    )
