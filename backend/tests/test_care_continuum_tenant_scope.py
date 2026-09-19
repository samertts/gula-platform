"""NR-146 — care continuum: one laboratory could read and drive another's records.

CLAUDE.md security invariant 1: "All patient-data queries MUST filter by
lab_id = current_user.lab_id". `care_continuum_service.py` already had the
primitive for it -- `_apply_lab_filter(query, model, lab_id)` -- and the whole
`list_*` family used it correctly. Nine functions did not:

  * `get_primary_care_encounter`, `get_care_journey`, `get_pregnancy_record`,
    `get_referral_timeline`, `get_referral_analytics` took no tenant at all and
    fetched by id alone.
  * `accept_referral` and `detect_care_gaps` ACCEPTED `lab_id` and never read
    it, so every call site looked tenant-aware while the query was not. That is
    the worst shape of the three: the route passes `_lab_id(current_user)`, so
    the code reads as correct at exactly the place a reviewer looks.
  * `reject_referral` and `complete_referral` had neither.

And `create_primary_care_encounter` took `lab_id` and built
`PrimaryCareEncounter(**data)`, so the encounter's owner came from the request
body while the caller's real tenant was discarded.

The tenth is in the route module. `api_update_primary_care_encounter` is the
one handler that queries a model directly instead of calling the service, and
it lost the tenant twice: no `lab_id` on the lookup, and an exclusion tuple
that guarded `id`, `created_at`, `updated_at` and `is_deleted` while leaving
`lab_id` assignable -- so a request body could MOVE an encounter to another lab.

These tests exercise the control at the service layer, where the defect was.
Each denial is paired with a positive control, because a function that refused
everything would satisfy the denials alone and look secure while being broken.

PROVED BY EXECUTION SINCE NR-086
--------------------------------
The first version of this module could not run a behavioural test at all. Its
tables' foreign keys pointed at `national_practitioners` and
`national_departments`, which belonged to a different declarative base, so
`create_all` raised `NoReferencedTableError` and the control was proved by
reading the source. That limit was recorded here rather than hidden, as
`test_y_behavioural_proof_is_blocked_by_the_cross_base_topology`, with the note
that its failure would be the signal to come back.

NR-086 gave the seven mutually-referencing bases one shared MetaData. The tables
build, the rows insert, and the `test_y*` family below is the two-lab suite that
test promised: two laboratories, real rows, real queries, in both directions.
Negative-proved — neutering `_apply_lab_filter` fails `y1` and `y3`; restoring
`PrimaryCareEncounter(**data)` so the body wins fails `y2`; the service was
restored byte-identical after each.

LATENT, NOT LIVE -- AND THE DIFFERENCE IS ASSERTED, NOT ASSUMED
---------------------------------------------------------------
No migration creates `cc_primary_care_encounters`, `cc_referral_requests` or
`cc_care_journeys`. The whole care-continuum surface therefore 500s against a
migrated database, so none of these holes is reachable by a caller today. They
are repaired now because they become live the moment the domain is built, and
because the repair uses a primitive the module already had -- not because
anything was being exploited. `test_z_this_domain_is_still_unbuilt` pins that
state so a later reader cannot mistake this suite for proof of a live fix.

The tables are still not built by the shared `db` fixture, which is a different
question from whether they *can* be: this module builds its own SQLite schema
from the shared MetaData, with the cross-base constraints intact.
"""
from __future__ import annotations

import os

os.environ["RUNTIME_MODE"] = "test"
os.environ["FEATURE_BACKGROUND_TASKS"] = "false"
os.environ.setdefault("ENV", "test")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production-" + "x" * 32)
os.environ.setdefault("ENCRYPTION_KEY", "6TJUTgJxBREYK9_yDy6VMXBw1HPwwxv1kiynV0WaAdw=")
os.environ.setdefault("NID_HMAC_KEY", "a" * 64)
os.environ.setdefault("REDIS_URL", "")

import inspect
import pathlib

import pytest
from app.services import care_continuum_service as svc

# ─── the behavioural proof NR-086 was blocking ──────────────────────────────
#
# This module used to carry `test_y_behavioural_proof_is_blocked_by_the_cross_base_topology`,
# which asserted `pytest.raises(NoReferencedTableError)` on `create_all` and said
# in its docstring: "When NR-078 lands, this test fails, and that is the signal
# to come back and write the two-lab behavioural suite this finding deserves."
#
# NR-086 landed. `cc_primary_care_encounters.practitioner_id` pointed at
# `national_practitioners`, `department_id` at `national_departments`, and
# neither was in `CareContinuumBase.metadata`; the seven bases now share one, so
# both resolve and the tables build. What follows is that suite, and it replaces
# a proof-by-source with a proof by execution.


@pytest.fixture()
def cc_db():
    """Two laboratories, real rows, a real session.

    Only the care-continuum tables and the tables their foreign keys name are
    built -- `create_all` over the whole shared namespace is a different
    assertion, and SQLite cannot render every column type in it.

    No request tenant is established, so NR-147's `TenantMixin` guard is inert
    here by design (see shared/models/tenant_context.py). That is what makes it
    possible to seed two laboratories in one session, and it is also why this
    test proves the *service's* control rather than that guard's: the control
    under test is `_apply_lab_filter`, not defence in depth.
    """
    import sqlalchemy as sa
    from app.care_continuum.models.care_journey import CareJourney
    from app.care_continuum.models.primary_care import PrimaryCareEncounter
    from app.factory import import_all_models
    from app.orm_topology import SHARED_METADATA
    from sqlalchemy.orm import Session

    # One shared MetaData resolves a foreign key only once the target's module
    # has been imported -- the namespace is as complete as the import graph, and
    # this module imports one service. `import_all_models()` is what the
    # application itself calls at startup for exactly this reason; using it here
    # rather than a hand-listed set of imports is what keeps the two from
    # drifting.
    import_all_models()

    wanted = [PrimaryCareEncounter.__table__, CareJourney.__table__]
    for table in list(wanted):
        for fk in table.foreign_keys:
            target = SHARED_METADATA.tables.get(fk.target_fullname.split(".")[0])
            if target is not None and target not in wanted:
                wanted.append(target)

    engine = sa.create_engine("sqlite://", future=True)
    try:
        SHARED_METADATA.create_all(engine, tables=wanted, checkfirst=True)
        with Session(engine) as session:
            yield session
    finally:
        engine.dispose()


def _encounter(db, lab_id, patient_id="PAT-1"):
    from datetime import datetime

    from app.national.enums import EncounterType

    return svc.create_primary_care_encounter(
        db,
        {
            "patient_id": patient_id,
            "encounter_type": EncounterType.CONSULTATION,
            "encounter_date": datetime(2026, 9, 1, 10, 0),
        },
        lab_id=lab_id,
    )


def test_y1_an_encounter_is_invisible_to_the_other_laboratory(cc_db):
    """The control, executed. NR-146 said this; nothing had ever run it."""
    mine = _encounter(cc_db, lab_id=1)

    assert svc.get_primary_care_encounter(cc_db, mine["id"], lab_id=1) is not None
    assert svc.get_primary_care_encounter(cc_db, mine["id"], lab_id=2) is None, (
        "laboratory 2 can read laboratory 1's primary-care encounter (NR-146)"
    )


def test_y2_the_body_cannot_choose_the_laboratory(cc_db):
    """The half a read-side test cannot reach.

    `create_primary_care_encounter` accepted `lab_id` and dropped it, so the
    owner came from the request body. The server-derived value has to win over a
    body that names a different one -- not merely be present.
    """
    from datetime import datetime

    from app.national.enums import EncounterType

    created = svc.create_primary_care_encounter(
        cc_db,
        {
            "patient_id": "PAT-2",
            "encounter_type": EncounterType.CONSULTATION,
            "encounter_date": datetime(2026, 9, 1, 11, 0),
            "lab_id": 999,          # a hostile body
        },
        lab_id=7,                    # the authenticated caller
    )
    assert created["lab_id"] == 7, (
        "the request body chose the encounter's laboratory (NR-146/NR-107)"
    )
    assert svc.get_primary_care_encounter(cc_db, created["id"], lab_id=999) is None


def test_y3_the_two_laboratories_do_not_see_each_others_rows(cc_db):
    """Both directions, because one direction passing can be an accident."""
    first = _encounter(cc_db, lab_id=1, patient_id="PAT-A")
    second = _encounter(cc_db, lab_id=2, patient_id="PAT-B")

    assert svc.get_primary_care_encounter(cc_db, first["id"], lab_id=2) is None
    assert svc.get_primary_care_encounter(cc_db, second["id"], lab_id=1) is None
    assert svc.get_primary_care_encounter(cc_db, first["id"], lab_id=1) is not None
    assert svc.get_primary_care_encounter(cc_db, second["id"], lab_id=2) is not None


def test_y4_a_null_tenant_is_unscoped_and_that_is_a_convention_not_an_accident(cc_db):
    """`_apply_lab_filter` no-ops on None, so callers with no lab see everything.

    That is the cross-tenant-role convention this module's functions follow, and
    it is asserted here rather than left implicit: it is exactly the behaviour a
    future change would break silently, and exactly the behaviour that makes the
    service's `lab_id` parameter load-bearing at every call site.
    """
    mine = _encounter(cc_db, lab_id=1, patient_id="PAT-C")
    assert svc.get_primary_care_encounter(cc_db, mine["id"], lab_id=None) is not None


# ─── regression guards ──────────────────────────────────────────────────────

@pytest.mark.parametrize("name", [
    "get_primary_care_encounter", "get_care_journey", "get_pregnancy_record",
    "get_referral_timeline", "get_referral_analytics", "detect_care_gaps",
    "accept_referral", "reject_referral", "complete_referral",
    "create_primary_care_encounter",
])
def test_j_every_repaired_function_still_takes_a_tenant(name):
    """Pins the signature, so the parameter cannot be dropped in a later edit."""
    assert "lab_id" in inspect.signature(getattr(svc, name)).parameters, (
        f"{name} lost its lab_id parameter (NR-146)"
    )


@pytest.mark.parametrize("name", [
    "get_primary_care_encounter", "get_care_journey", "get_pregnancy_record",
    "get_referral_timeline", "get_referral_analytics", "detect_care_gaps",
    "accept_referral", "reject_referral", "complete_referral",
])
def test_k_every_repaired_function_actually_uses_it(name):
    """Taking the parameter is what the broken ones already did.

    `accept_referral` and `detect_care_gaps` accepted `lab_id` and never read
    it, which is precisely why a signature check alone would have passed while
    the control did not exist. This asserts the body constrains the tenant.
    """
    source = inspect.getsource(getattr(svc, name))
    assert "_apply_lab_filter" in source or ".lab_id ==" in source, (
        f"{name} accepts lab_id but never constrains a query with it (NR-146)"
    )


def test_l_the_route_handler_excludes_lab_id_from_the_settable_keys():
    """The update handler bypasses the service, so its guard is asserted here."""
    from app.routes import care_continuum as routes

    source = inspect.getsource(routes.api_update_primary_care_encounter)
    assert '"lab_id"' in source, (
        "api_update_primary_care_encounter no longer excludes lab_id, so a "
        "request body can move an encounter between laboratories (NR-146)"
    )
    assert "PrimaryCareEncounter.lab_id ==" in source, (
        "the update lookup no longer constrains the tenant (NR-146)"
    )


# ─── the state this suite must never be mistaken for ────────────────────────

def test_z_this_domain_is_still_unbuilt():
    """No migration creates these tables, so nothing above is a live fix.

    Asserted separately and explicitly. If a migration ever builds them, this
    test fails and the finding is re-read as live rather than latent -- which
    is the point: "unreachable" must never quietly become "verified".
    """
    versions = pathlib.Path(__file__).resolve().parents[1] / "migrations" / "versions"
    assert versions.is_dir(), "migration directory moved; this guard is now blind"

    built = [
        path.name
        for path in versions.glob("*.py")
        for table in ("cc_primary_care_encounters", "cc_referral_requests",
                      "cc_care_journeys")
        if table in path.read_text(encoding="utf-8")
    ]
    assert not built, (
        f"care_continuum tables are now built by {sorted(set(built))} -- NR-146 "
        f"is no longer latent and must be re-classified as a live P0"
    )
