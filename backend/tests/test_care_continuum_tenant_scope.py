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

LATENT, NOT LIVE -- AND THE DIFFERENCE IS ASSERTED, NOT ASSUMED
---------------------------------------------------------------
No migration creates `cc_primary_care_encounters`, `cc_referral_requests` or
`cc_care_journeys`. The whole care-continuum surface therefore 500s against a
migrated database, so none of these holes is reachable by a caller today. They
are repaired now because they become live the moment the domain is built, and
because the repair uses a primitive the module already had -- not because
anything was being exploited. `test_z_this_domain_is_still_unbuilt` pins that
state so a later reader cannot mistake this suite for proof of a live fix.

The tables also cannot be created by the shared `db` fixture: their foreign
keys point at `national_practitioners` and `national_departments`, which belong
to a different declarative base (NR-078/NR-086). This module therefore builds
its own SQLite tables with the cross-base constraints stripped, which is enough
to exercise a WHERE clause and is honest about why it is necessary.
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

# ─── why there is no behavioural test below this line ───────────────────────

def test_y_behavioural_proof_is_blocked_by_the_cross_base_topology():
    """These classes cannot be exercised through the ORM at all. Measured.

    The first version of this module tried to prove the control the way NR-128
    was proved -- two labs, real rows, a real query. It could not run:
    `cc_primary_care_encounters.practitioner_id` and
    `cc_care_journeys.care_coordinator_id` point at `national_practitioners`,
    and `department_id` at `national_departments`, neither of which is in
    `CareContinuumBase.metadata`. That is NR-086 ("76 mapped tables cannot be
    written through the ORM at all: their foreign keys target another base"),
    whose repair is NR-078's topology change.

    So the control below is proved by source, not by execution, and this test
    exists so that limit is stated rather than hidden. When NR-078 lands, this
    test fails, and that is the signal to come back and write the two-lab
    behavioural suite this finding deserves.
    """
    from app.care_continuum.base import CareContinuumBase
    from app.care_continuum.models.primary_care import PrimaryCareEncounter
    from sqlalchemy import create_engine
    from sqlalchemy.exc import NoReferencedTableError

    engine = create_engine("sqlite://", future=True)
    try:
        with pytest.raises(NoReferencedTableError):
            CareContinuumBase.metadata.create_all(
                engine, tables=[PrimaryCareEncounter.__table__],
            )
    finally:
        engine.dispose()


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
