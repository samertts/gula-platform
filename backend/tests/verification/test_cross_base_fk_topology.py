"""NR-086 / NR-078 / NR-006 — the cross-base foreign-key topology, re-measured.

SQLAlchemy resolves a ``ForeignKey`` inside the ``MetaData`` that owns the
*referring* table, and it resolves all of them while sorting a mapper's tables
during ``flush``. A target in a different ``MetaData`` cannot be found, so the
write raises ``NoReferencedTableError`` before emitting any SQL. Reads never
sort tables, which is why a table in that state answers ``SELECT`` perfectly and
fails the first time anything tries to persist.

These tests **measure** rather than trust. The docstring in
``app/orm_topology.py`` quotes numbers taken on 2026-09-26; a docstring cannot
notice a twelfth base appearing, so the assertions below recompute from the live
registry every run.

Deliberately NOT asserted: that any particular domain's writes now succeed.
Resolving the topology is necessary for a write, not sufficient -- the nursing
tables, for one, then fail on ORM-to-physical column drift, which is a separate
finding. Conflating the two would be exactly the "route existence means
functional capability" claim the platform's evidence rules forbid.
"""

from __future__ import annotations

import collections

import pytest
from app.orm_topology import (
    AUTOGENERATE_BASE_LABELS,
    SHARED_BASE_LABELS,
    SHARED_METADATA,
    own_tables,
)

# Every declarative base in the repository, by the label the topology module and
# migrations/env.py both use. Listed rather than discovered so that a new base
# has to be added here consciously.
ALL_BASES: dict[str, tuple[str, str]] = {
    "Base": ("app.database", "Base"),
    "CareContinuumBase": ("app.care_continuum.base", "CareContinuumBase"),
    "CitizenPlatformBase": ("app.citizen_platform.base", "CitizenPlatformBase"),
    "ClinicalBase": ("app.clinical.base", "ClinicalBase"),
    "DocIntelBase": ("app.document_intelligence.infrastructure.models", "DocIntelBase"),
    "EHRBase": ("app.ehr.base", "EHRBase"),
    "FinBase": ("app.financial.models", "FinBase"),
    "GovernanceBase": ("app.governance.base", "GovernanceBase"),
    "HealthDataBase": ("app.health_data.base", "HealthDataBase"),
    "HospitalBase": ("app.hospital.base", "HospitalBase"),
    "IdentityBase": ("app.identity.base", "IdentityBase"),
    "InsBase": ("app.insurance.domain.models", "InsBase"),
    "NationalBase": ("app.national.base", "NationalBase"),
    "DataPlatformBase": ("app.national_data.base", "DataPlatformBase"),
    "NHDWBase": ("app.nhdw.base", "NHDWBase"),
    "NursingBase": ("app.nursing.base", "NursingBase"),
    "PharmacyBase": ("app.pharmacy.base", "PharmacyBase"),
    "RadiologyBase": ("app.radiology.base", "RadiologyBase"),
    "TrustBase": ("app.trust.base", "TrustBase"),
}


@pytest.fixture(scope="module")
def assembled_app():
    """Import the app the way it is actually served.

    This matters and is not incidental. A shared ``MetaData`` only resolves a
    foreign key once the *target's* mapper module has been imported; a process
    that imports ``app.nursing`` alone still raises, because nothing has put
    ``patients`` in the namespace. So the measurement that means anything is the
    one taken against the assembled application, which is what
    ``import app.main`` produces.
    """
    import app.main

    return SHARED_METADATA


@pytest.fixture(scope="module")
def bases(assembled_app):
    import importlib

    loaded = {}
    for label, (mod, attr) in ALL_BASES.items():
        loaded[label] = getattr(importlib.import_module(mod), attr)
    return loaded


def _unresolvable(namespace) -> dict[str, list[str]]:
    """FK columns in ``namespace`` whose target table is not in ``namespace``."""
    missing: dict[str, list[str]] = collections.defaultdict(list)
    for tname, table in namespace.tables.items():
        for col in table.columns:
            for fk in col.foreign_keys:
                target = str(fk._colspec)
                ttab = target.rsplit(".", 1)[0]
                if ttab not in namespace.tables:
                    missing[ttab].append(f"{tname}.{col.name}")
    return dict(missing)


def test_the_assembled_app_has_no_unresolvable_foreign_key(bases):
    """The whole point. 374 unresolvable FK columns on 2026-09-26; now zero.

    Every base's **own** namespace is walked, not just the shared one. That
    distinction is load-bearing and was found by negative proof: reverting
    ``NursingBase`` to a bare ``declarative_base()`` takes its fifteen tables out
    of the shared namespace altogether, so a shared-namespace-only scan sees a
    clean namespace and passes while every nursing write is broken. Measuring
    per base is what makes this assertion mean "the ORM can write", rather than
    "the tables that happen to be in one namespace agree with each other".

    A failure names the target table that no loaded mapper declares, which is
    the actual diagnostic -- either a base sits outside the shared closure, or a
    ``ForeignKey`` string names a table that does not exist. Both were real: the
    closure was missing NursingBase, PharmacyBase and InsBase, and three strings
    named ``niam_identity_authorities`` and ``niam_user_sessions``, which exist
    in no model, no migration and no database.
    """
    offenders: dict[str, dict[str, list[str]]] = {}
    for label, base in sorted(bases.items()):
        missing = _unresolvable(base.metadata)
        # Only count FKs declared by tables this base itself maps, so a base is
        # never blamed for a neighbour's dangling reference in a shared object.
        keys = {t.key for t in own_tables(base)}
        mine = {
            tgt: [c for c in cols if c.rsplit(".", 1)[0] in keys]
            for tgt, cols in missing.items()
        }
        mine = {t: c for t, c in mine.items() if c}
        if mine:
            offenders[label] = mine
    assert offenders == {}, (
        "Unresolvable foreign-key targets. Every write to a listed table raises "
        "NoReferencedTableError before emitting any SQL:\n"
        + "\n".join(
            f"  {label}:\n"
            + "\n".join(
                f"      {tgt}: {len(cols)} column(s), e.g. {cols[:4]}"
                for tgt, cols in sorted(m.items())
            )
            for label, m in sorted(offenders.items())
        )
    )


def test_every_base_declaring_a_cross_base_foreign_key_is_in_the_closure(bases):
    """The closure is recomputed, not trusted.

    ``SHARED_BASE_LABELS`` is a hand-maintained list, so it can go stale the
    moment a base outside it grows its first cross-base foreign key -- which is
    precisely how NursingBase came to be broken while the mechanism that would
    have fixed it already existed. This recomputes membership from the live
    registry and fails if the list no longer covers it.
    """
    outside = {
        label: base
        for label, base in bases.items()
        if label not in SHARED_BASE_LABELS
    }
    # What each non-shared base's own namespace can see.
    offenders: dict[str, list[str]] = {}
    for label, base in outside.items():
        ns = base.metadata
        bad = []
        for table in own_tables(base):
            for col in table.columns:
                for fk in col.foreign_keys:
                    ttab = str(fk._colspec).rsplit(".", 1)[0]
                    if ttab not in ns.tables:
                        bad.append(f"{table.key}.{col.name} -> {ttab}")
        if bad:
            offenders[label] = bad
    assert offenders == {}, (
        "These bases are outside the shared namespace but declare foreign keys "
        "their own MetaData cannot resolve, so every write to them raises "
        "NoReferencedTableError. Add them to SHARED_BASE_LABELS and construct "
        "them against SHARED_METADATA:\n"
        + "\n".join(f"  {k}: {v}" for k, v in sorted(offenders.items()))
    )


def test_the_shared_bases_really_share_one_metadata_object(bases):
    """Membership of ``SHARED_BASE_LABELS`` must be a fact, not a claim.

    A base could be listed and still call a bare ``declarative_base()``, which
    would leave it broken while the list said otherwise -- a false green of
    exactly the kind that is forbidden here.
    """
    for label in sorted(SHARED_BASE_LABELS):
        base = bases[label]
        assert base.metadata is SHARED_METADATA, (
            f"{label} is listed in SHARED_BASE_LABELS but its metadata is not "
            f"SHARED_METADATA. It must be constructed as "
            f"declarative_base(metadata=SHARED_METADATA)."
        )
    for label, base in bases.items():
        if label not in SHARED_BASE_LABELS:
            assert base.metadata is not SHARED_METADATA, (
                f"{label} shares SHARED_METADATA but is not listed in "
                f"SHARED_BASE_LABELS. Either list it or give it its own "
                f"MetaData -- an unlisted member puts its tables in front of "
                f"autogenerate without a recorded decision."
            )


def test_no_table_is_mapped_by_more_than_one_class(bases):
    """NR-006, and the guard that keeps it closed.

    ``national_facilities`` was mapped by ``clinical_scope.NationalFacility`` on
    ``Base`` and by ``national.domain.facility.Facility`` on ``NationalBase``.
    In separate namespaces they never met. In one namespace the second carried
    ``extend_existing=True``, so it did not raise -- it silently unioned itself
    into the first, producing a 30-column ``Table`` of which 24 columns do not
    exist in the database, and breaking the owner that had been correct.

    A silent union is the worst available outcome, so this asserts the invariant
    directly: one physical table, one mapped class.
    """
    owners: dict[str, list[str]] = collections.defaultdict(list)
    for label, base in bases.items():
        for mapper in base.registry.mappers:
            for table in mapper.tables:
                owners[table.key].append(f"{label}:{mapper.class_.__name__}")
    dupes = {t: sorted(set(o)) for t, o in owners.items() if len(set(o)) > 1}
    assert dupes == {}, (
        "These physical tables are mapped by more than one class. Under one "
        "shared MetaData a second declaration with extend_existing=True unions "
        "itself into the first instead of raising, so this cannot be left to "
        "SQLAlchemy to catch:\n"
        + "\n".join(f"  {t}: {o}" for t, o in sorted(dupes.items()))
    )


def test_the_retired_national_facility_owner_stays_retired(bases):
    """NR-006's decision, pinned where a reintroduction would land.

    Reaching for the retired name must fail with the explanation rather than
    silently binding to the EHR scope resource, which is a different clinical
    concept -- ``app/models/clinical_scope.py`` says so in Arabic directly above
    the owner, and forbids inferring a relationship from identifier similarity.
    """
    import app.national.domain.facility as retired

    with pytest.raises(AttributeError) as exc:
        retired.Facility  # noqa: B018
    message = str(exc.value)
    assert "retired" in message and "NR-006" in message
    assert "app.models.clinical_scope.NationalFacility" in message, (
        "The retirement message must name the single owner, or the next person "
        "to hit it has to rediscover which of three facility concepts is which."
    )

    from app.models.clinical_scope import NationalFacility

    assert NationalFacility.__tablename__ == "national_facilities"
    assert {c.name for c in NationalFacility.__table__.columns} == {
        "id", "facility_code", "name", "status", "created_at", "updated_at",
    }, (
        "The owner's column set drifted from the six the physical table has. If "
        "the table genuinely gained columns, that is a migration and this pin "
        "should be updated with it."
    )


def test_autogenerate_scope_is_not_silently_widened_by_the_merge(bases):
    """NR-018 is about what Alembic sees; NR-086 is about whether writes work.

    Sharing a ``MetaData`` would otherwise sweep five bases into autogenerate's
    comparison that NR-018 recorded a decision to keep out. This asserts the two
    sets stay distinct and that the excluded five are genuinely excluded, so the
    write repair cannot quietly become a scope change.
    """
    assert AUTOGENERATE_BASE_LABELS != SHARED_BASE_LABELS, (
        "If these two sets have become equal, either NR-018's scope was widened "
        "or the closure shrank. Both need a recorded decision."
    )
    must_stay_out = {
        "HospitalBase", "InsBase", "DataPlatformBase", "NursingBase", "PharmacyBase",
    }
    assert must_stay_out <= SHARED_BASE_LABELS, (
        "These are in the measured closure -- they declare cross-base foreign "
        "keys and must share the namespace."
    )
    assert not (must_stay_out & AUTOGENERATE_BASE_LABELS), (
        "NR-018 keeps these out of autogenerate. Sharing a MetaData must not "
        "change that; migrations/env.py filters on AUTOGENERATE_BASE_LABELS."
    )

    from app.orm_topology import authorized_table_names, make_include_name

    authorized = authorized_table_names()
    include_name = make_include_name(authorized)

    excluded_tables = {
        table.key for label in must_stay_out for table in own_tables(bases[label])
    }
    leaked = sorted(excluded_tables & authorized)
    assert leaked == [], (
        f"Tables owned only by NR-018-excluded bases reached autogenerate's "
        f"scope: {leaked[:10]}"
    )
    for tname in sorted(excluded_tables)[:5]:
        assert include_name(tname, "table", {}) is False
    assert include_name(None, "schema", {}) is True, (
        "The default schema must be admitted or nothing is compared at all."
    )
