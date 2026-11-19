"""care_continuum: one laboratory could read and drive another's records.

CLAUDE.md security invariant 1: "All patient-data queries MUST filter by
lab_id = current_user.lab_id". care_continuum_service.py already had the
primitive for it — _apply_lab_filter(query, model, lab_id) — and the whole
list_* family used it correctly. Several functions did not:

  * get_primary_care_encounter, get_care_journey, get_pregnancy_record,
    get_referral_timeline, get_referral_analytics took no tenant at all and
    fetched by id alone.
  * accept_referral (already took lab_id) and detect_care_gaps ACCEPTED
    lab_id and never read it, so every call site looked tenant-aware while
    the query was not — the worst shape of the three: the route passes
    _lab_id(current_user), so the code reads as correct at exactly the
    place a reviewer looks.
  * reject_referral and complete_referral had neither.

create_primary_care_encounter took lab_id and built
PrimaryCareEncounter(**data), so the encounter's owner came from the request
body while the caller's real tenant was discarded.

The tenth spot is in the route module: api_update_primary_care_encounter is
the one handler that queries a model directly instead of calling the
service, and it lost the tenant twice: no lab_id on the lookup, and an
exclusion tuple that guarded id/created_at/updated_at/is_deleted while
leaving lab_id assignable — so a request body could MOVE an encounter to
another lab.

LATENT, NOT LIVE — AND THE DIFFERENCE IS ASSERTED, NOT ASSUMED
----------------------------------------------------------------
No migration in this repo creates cc_primary_care_encounters,
cc_referral_requests, or cc_care_journeys (checked below). The whole
care-continuum surface therefore 500s against a migrated database today, so
none of this is reachable by a live caller. It is repaired anyway because it
becomes live the moment the domain is built, and because the repair reuses a
primitive the module already had. test_z_this_domain_is_still_unbuilt pins
that state so a later reader cannot mistake this suite for proof of a live
fix.

A real two-lab behavioural test (create a row in Lab A, read/write as Lab
B, assert 404/no-op) is not possible either, and that is proved rather than
assumed below: PrimaryCareEncounter's foreign keys
(department_id -> national_departments, practitioner_id ->
national_practitioners) point at tables outside CareContinuumBase.metadata,
so CareContinuumBase.metadata.create_all() cannot even build the table in
SQLite. The regression guards below are therefore source/signature-based —
proving the control exists in the code, not exercising it end-to-end — and
say so rather than presenting a signature check as behavioural proof.
"""
from __future__ import annotations

import inspect
import pathlib

import pytest
from app.services import care_continuum_service as svc


def test_the_cross_base_fk_topology_blocks_a_behavioural_test():
    """Confirms the limitation above by triggering it, rather than asserting
    it from a comment. If this ever stops raising, the finding above should
    be re-proved with real two-lab rows instead of via source inspection."""
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


@pytest.mark.parametrize("name", [
    "get_primary_care_encounter", "get_care_journey", "get_pregnancy_record",
    "get_referral_timeline", "get_referral_analytics", "detect_care_gaps",
    "accept_referral", "reject_referral", "complete_referral",
    "create_primary_care_encounter",
])
def test_every_repaired_function_still_takes_a_tenant(name):
    """Pins the signature so lab_id cannot be silently dropped in a later edit."""
    assert "lab_id" in inspect.signature(getattr(svc, name)).parameters, (
        f"{name} lost its lab_id parameter"
    )


@pytest.mark.parametrize("name", [
    "get_primary_care_encounter", "get_care_journey", "get_pregnancy_record",
    "get_referral_timeline", "get_referral_analytics", "detect_care_gaps",
    "accept_referral", "reject_referral", "complete_referral",
])
def test_every_repaired_function_actually_uses_the_tenant(name):
    """Taking the parameter is what the broken ones already did — accept_referral
    and detect_care_gaps accepted lab_id and never read it, which is exactly
    why a signature check alone would pass while the control did not exist.
    Asserts the function body actually constrains a query with it."""
    source = inspect.getsource(getattr(svc, name))
    assert "_apply_lab_filter" in source or ".lab_id ==" in source, (
        f"{name} accepts lab_id but never constrains a query with it"
    )


def test_create_primary_care_encounter_uses_the_server_derived_lab_id():
    """The one create path in this set: must build the row from the
    server-derived lab_id, not the caller-supplied data dict alone."""
    source = inspect.getsource(svc.create_primary_care_encounter)
    assert '"lab_id": lab_id' in source, (
        "create_primary_care_encounter no longer overrides lab_id with the "
        "server-derived value — the request body could set it again"
    )


def test_route_handler_excludes_lab_id_from_the_settable_keys_and_scopes_the_lookup():
    """The update handler bypasses the service, so its guard is asserted here."""
    from app.routes import care_continuum as routes

    source = inspect.getsource(routes.api_update_primary_care_encounter)
    assert '"lab_id"' in source, (
        "api_update_primary_care_encounter no longer excludes lab_id, so a "
        "request body can move an encounter between laboratories"
    )
    assert "PrimaryCareEncounter.lab_id ==" in source, (
        "the update lookup no longer constrains the tenant"
    )


def test_z_this_domain_is_still_unbuilt():
    """No migration creates these tables, so nothing above is a live fix.

    Asserted separately and explicitly. If a migration ever builds them,
    this test fails and the finding must be re-read as live rather than
    latent — "unreachable" must never quietly become "verified".
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
        f"care_continuum tables are now built by {sorted(set(built))} — this "
        f"finding is no longer latent and must be re-classified as live"
    )
