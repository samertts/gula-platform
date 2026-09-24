"""Every mutating blood bank route writes an attributable audit row (NR-027).

CLAUDE.md Security Invariant #2 requires every mutation to write to the audit
log. Fourteen of the twenty-one mutating blood bank routes went through
`ClinicalCommandGuard`, which audits. Six did not, and wrote no audit record at
all: donor registration, donor deferral, donation registration, donation
completion, component processing and blood request creation. A blood component
could be processed and issued with no trail of who did it.

`BloodBankService` had `lab_id` but no actor, so there was nothing to attribute
an audit row to; the actor is now threaded in from `get_current_user` and each
of those methods writes its audit row BEFORE its own commit, so the row and the
clinical effect share one transaction.

Two further defects surfaced while proving this by execution, both fixed here
and both covered below:

* `_update_donor` -- reachable from `POST /donors` whenever the citizen already
  has a donor record -- mass-assigned the request body onto the row, including
  `lab_id`. `_owned()` exists precisely to stop a caller attributing a row to
  another laboratory (NR-021), but this update path did not use it.
* `defer_donor` never set `blood_bank_donor_deferrals.deferred_from`, which is
  NOT NULL with no default, so `POST /donors/{donor_id}/defer` raised
  NotNullViolation on every call. That is a clinical safety failure, not a
  cosmetic one: `register_donation` refuses a donation only when an ACTIVE
  deferral row exists, so while no deferral row could be written the
  donor-deferral gate could never fire.

The structural tests run everywhere. The execution proof needs the real
PostgreSQL schema -- the append-only `audit_logs` trigger and the NOT NULL
constraints are what the proof is about -- and skips otherwise.
"""
from __future__ import annotations

import ast
import os
from pathlib import Path

import pytest

_BACKEND = Path(__file__).resolve().parents[1]
_ROUTES = _BACKEND / "app" / "blood_bank" / "api" / "routes.py"
_SERVICE = _BACKEND / "app" / "blood_bank" / "application" / "service.py"

_MUTATING = {"post", "put", "patch", "delete"}

# Mutating-verb blood bank routes that legitimately write no audit row.
# This ledger may SHRINK, never GROW. Adding an entry means a clinical write
# lost its audit trail, which is what NR-027 was.
DECLARED_UNAUDITED: frozenset[str] = frozenset({
    # Declared with a POST verb but a pure calculation: it calls
    # check_compatibility(patient_group, unit_group), takes no Session, touches
    # no model and persists nothing. There is no state change to audit.
    "/crossmatch/check",
})

# A floor so a scan that silently stops finding routes cannot pass vacuously.
# Measured at 21 on 2026-09-18.
MINIMUM_MUTATING_ROUTES = 21


def _service_methods_that_audit() -> set[str]:
    """Service methods whose body calls self._audit (directly or via a callee)."""
    tree = ast.parse(_SERVICE.read_text(encoding="utf-8"))
    bodies: dict[str, str] = {}
    for cls in tree.body:
        if not isinstance(cls, ast.ClassDef) or cls.name != "BloodBankService":
            continue
        for fn in cls.body:
            if isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
                bodies[fn.name] = ast.unparse(fn)
    direct = {name for name, src in bodies.items() if "self._audit(" in src}
    # One hop: a method that delegates to a method that audits.
    for name, src in bodies.items():
        if any(f"self.{a}(" in src for a in direct):
            direct = direct | {name}
    return direct


def _mutating_routes() -> list[dict[str, object]]:
    source = _ROUTES.read_text(encoding="utf-8")
    tree = ast.parse(source)
    audits = _service_methods_that_audit()
    rows: list[dict[str, object]] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for dec in node.decorator_list:
            if not isinstance(dec, ast.Call):
                continue
            fn = dec.func
            if not (isinstance(fn, ast.Attribute) and fn.attr in _MUTATING):
                continue
            path = dec.args[0].value if dec.args and isinstance(dec.args[0], ast.Constant) else ""
            body = ast.unparse(node)
            via_guard = "guard." in body or "ClinicalCommandGuard" in body
            via_log = "log_action(" in body
            via_service = any(f"service.{m}(" in body for m in audits)
            rows.append({
                "path": path, "handler": node.name, "line": node.lineno,
                "audited": via_guard or via_log or via_service,
            })
    return rows


# --------------------------------------------------------------------------
# Structural proof
# --------------------------------------------------------------------------

def test_the_scan_still_sees_the_routes_it_is_supposed_to_check() -> None:
    """Guard the guard: a scan that finds nothing must not pass."""
    rows = _mutating_routes()
    assert len(rows) >= MINIMUM_MUTATING_ROUTES, (
        f"only {len(rows)} mutating blood bank routes found, expected at least "
        f"{MINIMUM_MUTATING_ROUTES}. Either routes were removed -- lower the "
        f"floor deliberately -- or this scan has stopped seeing them, in which "
        f"case every assertion below is vacuous."
    )
    assert _service_methods_that_audit(), (
        "no BloodBankService method calls self._audit, so the delegation arm of "
        "this scan can never fire and the audit coverage it reports is fiction."
    )


def test_no_mutating_route_writes_without_an_audit_row() -> None:
    unaudited = sorted(
        str(r["path"]) for r in _mutating_routes() if not r["audited"]
    )
    undeclared = sorted(set(unaudited) - DECLARED_UNAUDITED)
    assert not undeclared, (
        "these mutating blood bank routes write no audit record, violating "
        f"CLAUDE.md Security Invariant #2: {undeclared}"
    )


def test_the_unaudited_ledger_has_not_rotted() -> None:
    """Every declared exemption must still be a real mutating route."""
    paths = {str(r["path"]) for r in _mutating_routes()}
    stale = sorted(DECLARED_UNAUDITED - paths)
    assert not stale, (
        f"DECLARED_UNAUDITED names routes that no longer exist: {stale}. "
        "Remove them so the ledger keeps meaning something."
    )


def test_the_ledger_cannot_be_grown_to_cover_a_new_gap() -> None:
    """The ledger is a ratchet: exactly one entry, and it is the calculation."""
    assert frozenset({"/crossmatch/check"}) == DECLARED_UNAUDITED, (
        "DECLARED_UNAUDITED changed. It may only shrink. If a new mutating "
        "route needs an entry, that route is missing its audit row -- write "
        "the audit, do not widen the ledger."
    )


def test_the_server_owns_tenant_and_identity_fields_on_every_write_path() -> None:
    from app.blood_bank.application import service as svc

    assert {"lab_id", "id"} <= set(svc._SERVER_OWNED_FIELDS), (
        "a request body that can set lab_id can attribute a row to another "
        "laboratory; one that can set id can hijack an existing row."
    )
    assert set(svc._SERVER_OWNED_FIELDS) <= set(svc._DONOR_UPDATE_EXCLUDED), (
        "the donor UPDATE path must exclude at least what the CREATE path "
        "excludes, or the control exists on one entry point and not the other."
    )


def test_the_varchar_primary_key_is_normalised_for_the_integer_audit_column() -> None:
    """audit_logs.resource_id is INTEGER; blood bank keys are varchar.

    The service used to carry its own copy of this rule, and so did
    ClinicalCommandGuard. NR-109 consolidated both onto
    audit_service.normalize_resource_id, because two copies of one rule is
    what let the blood bank create and update paths disagree under NR-105.
    This test follows the rule to its single home rather than pinning a
    duplicate back into place.
    """
    from app.blood_bank.application import service as blood_bank
    from app.services.audit_service import normalize_resource_id

    assert normalize_resource_id(None) is None
    assert normalize_resource_id(41) == 41
    assert normalize_resource_id("41") == 41
    # The real shape of a blood bank key. Passing it through raises DataError
    # from inside the audit writer and takes the clinical transaction with it.
    assert normalize_resource_id("FB038B3AF71045168A6F3437C1") is None
    # And the blood bank genuinely reaches it -- a consolidation that left the
    # service calling something else would still pass the three lines above.
    assert blood_bank.normalize_resource_id is normalize_resource_id


def test_every_not_null_column_without_a_default_is_set_at_its_write_site() -> None:
    """The defect class behind the broken deferral endpoint.

    `deferred_from` was NOT NULL with no default and never assigned, so the
    endpoint could not succeed. Check the deferral model's own write site
    rather than trusting that it is still correct.
    """
    from app.blood_bank.infrastructure.models import DonorDeferralModel

    required = {
        c.name for c in DonorDeferralModel.__table__.columns
        if not c.nullable and c.default is None and c.server_default is None
        and not c.primary_key and c.name not in {"lab_id"}
    }
    tree = ast.parse(_SERVICE.read_text(encoding="utf-8"))
    site = ""
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) \
                and node.func.id == "DonorDeferralModel":
            site = ast.unparse(node)
    assert site, "DonorDeferralModel is never constructed -- this check is vacuous"
    missing = sorted(c for c in required if f"{c}=" not in site)
    assert not missing, (
        f"DonorDeferralModel is constructed without {missing}, which are NOT "
        f"NULL with no default. The endpoint cannot succeed. Construction "
        f"site: {site}"
    )


# --------------------------------------------------------------------------
# Execution proof (PostgreSQL only)
# --------------------------------------------------------------------------

_PG_URL = os.environ.get("MIGRATION_DATABASE_URL", "")

pg_only = pytest.mark.skipif(
    "postgres" not in _PG_URL,
    reason="needs the real PostgreSQL schema (append-only audit trigger, NOT NULL)",
)

LAB_A = 990001
LAB_B = 990002
ACTOR = 770001


@pytest.fixture()
def pg_session():
    """A session inside an outer transaction that is always rolled back.

    The service methods commit internally, so the session joins the outer
    transaction through savepoints. Nothing survives, which matters because
    `audit_logs` denies DELETE by trigger and could not otherwise be cleaned.
    """
    # The factory is the only place that imports every model, and the mapper
    # registry is not resolvable without all of them.
    from app.factory import create_app
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session, configure_mappers

    create_app()
    configure_mappers()

    engine = create_engine(_PG_URL, future=True)
    conn = engine.connect()
    outer = conn.begin()
    session = Session(bind=conn, join_transaction_mode="create_savepoint")
    try:
        yield session
    finally:
        session.close()
        outer.rollback()
        conn.close()
        engine.dispose()


def _audit_rows(session, action: str) -> list:
    from app.models.audit_log import AuditLog

    return session.query(AuditLog).filter(AuditLog.action == action).all()


def _service(session, **kw):
    from app.blood_bank.application.service import BloodBankService

    kw.setdefault("lab_id", LAB_A)
    kw.setdefault("user_id", ACTOR)
    return BloodBankService(db=session, **kw)


def _donor(svc, citizen: str = "NR027-CITIZEN-1"):
    return svc.register_donor({
        "citizen_id": citizen, "full_name": "NR027 Probe Donor", "blood_group": "O+",
    })


@pg_only
@pytest.mark.integration
def test_each_legacy_mutation_writes_one_attributed_audit_row(pg_session) -> None:
    from sqlalchemy import text

    svc = _service(pg_session)
    donor = _donor(svc)

    rows = _audit_rows(pg_session, "bloodbank.donor.register")
    assert len(rows) == 1
    assert rows[0].user_id == ACTOR, "the audit row is not attributed to the actor"
    assert rows[0].lab_id == LAB_A, "the audit row is not attributed to the laboratory"
    assert rows[0].chain_hash, "the audit row is outside the hash chain"
    assert donor.id in (rows[0].details or ""), (
        "the varchar key is normalised to NULL in resource_id, so it must be "
        "preserved in details or the row names no resource at all"
    )

    deferral = svc.defer_donor(donor.id, {"reason": "low_haemoglobin", "deferral_days": 30})
    assert len(_audit_rows(pg_session, "bloodbank.donor.defer")) == 1

    pg_session.execute(
        text("update blood_bank_donors set status='active' where id=:i"),
        {"i": donor.id},
    )
    pg_session.execute(
        text("update blood_bank_donor_deferrals set is_active=false where id=:i"),
        {"i": deferral.id},
    )

    donation = svc.register_donation({
        "donor_id": donor.id, "volume_ml": 450,
        "collection_date": "2026-09-18T00:00:00+00:00",
    })
    assert len(_audit_rows(pg_session, "bloodbank.donation.register")) == 1

    svc.complete_donation(donation.id)
    done = _audit_rows(pg_session, "bloodbank.donation.complete")
    assert len(done) == 1
    assert "state_before" in (done[0].details or ""), (
        "a state transition audited without its prior state cannot be reviewed"
    )

    svc.process_component({"donation_id": donation.id, "component": "prbc"})
    assert len(_audit_rows(pg_session, "bloodbank.component.process")) == 1

    svc.create_blood_request({"patient_id": "NR027-PATIENT-1", "blood_group": "O+",
                              "units_requested": 2})
    assert len(_audit_rows(pg_session, "bloodbank.request.create")) == 1

    # False-positive check: an action nobody wrote must come back empty, or the
    # assertions above would pass against any string.
    assert _audit_rows(pg_session, "bloodbank.donor.NEVER_WRITTEN") == []


@pg_only
@pytest.mark.integration
def test_the_request_body_cannot_hand_a_donor_to_another_laboratory(pg_session) -> None:
    from sqlalchemy import text

    svc = _service(pg_session)
    donor = _donor(svc)

    svc.register_donor({
        "citizen_id": "NR027-CITIZEN-1", "full_name": "NR027 Renamed",
        "lab_id": LAB_B, "id": "HIJACKED",
    })

    rows = pg_session.execute(
        text("select lab_id, id, full_name from blood_bank_donors "
             "where citizen_id=:c"),
        {"c": "NR027-CITIZEN-1"},
    ).all()
    assert len(rows) == 1, "the upsert created a second row instead of updating"
    assert rows[0][0] == LAB_A, (
        f"a client-supplied lab_id reassigned the donor to laboratory "
        f"{rows[0][0]} -- this is a tenant reassignment through the request body"
    )
    assert rows[0][1] == donor.id, "a client-supplied id reassigned the primary key"
    # Positive control: the update path still applies the fields it should.
    assert rows[0][2] == "NR027 Renamed", (
        "nothing changed at all, so the two assertions above prove nothing "
        "about the update path"
    )

    audit = _audit_rows(pg_session, "bloodbank.donor.update")
    assert len(audit) == 1, "the donor update wrote no audit row"
    assert "lab_id" not in (audit[0].details or ""), (
        "lab_id is recorded as a changed field, so it was applied after all"
    )


@pg_only
@pytest.mark.integration
def test_a_deferred_donor_is_actually_refused_a_donation(pg_session) -> None:
    """The deferral row must persist, or the safety gate can never fire."""
    from app.blood_bank.exceptions import DonorDeferredError
    from sqlalchemy import text

    svc = _service(pg_session)
    donor = _donor(svc)
    deferral = svc.defer_donor(donor.id, {"reason": "low_haemoglobin",
                                          "deferral_days": 30})

    persisted = pg_session.execute(
        text("select deferred_from, is_active from blood_bank_donor_deferrals "
             "where id=:i"),
        {"i": deferral.id},
    ).all()
    assert len(persisted) == 1, "the deferral row did not persist"
    assert persisted[0][0] is not None, "deferred_from is NULL"
    assert persisted[0][1] is True, "the deferral is not active"

    with pytest.raises(DonorDeferredError):
        svc.register_donation({
            "donor_id": donor.id, "volume_ml": 450,
            "collection_date": "2026-09-18T00:00:00+00:00",
        })


@pg_only
@pytest.mark.integration
def test_an_audit_row_cannot_survive_a_rolled_back_mutation(pg_session) -> None:
    """The audit write is atomic with the clinical effect, not merely adjacent."""
    from app.models.audit_log import AuditLog

    svc = _service(pg_session)
    donor = _donor(svc)

    before = pg_session.query(AuditLog).count()
    savepoint = pg_session.begin_nested()

    original_commit = pg_session.commit

    def _fail_after_the_audit_write() -> None:
        raise RuntimeError("simulated failure after the audit write")

    pg_session.commit = _fail_after_the_audit_write  # type: ignore[method-assign]
    seen_inside = None
    try:
        with pytest.raises(RuntimeError):
            svc.register_donation({
                "donor_id": donor.id, "volume_ml": 450,
                "collection_date": "2026-09-18T00:00:00+00:00",
            })
        # Flushed, not committed.
        seen_inside = pg_session.query(AuditLog).count()
    finally:
        pg_session.commit = original_commit  # type: ignore[method-assign]

    assert seen_inside == before + 1, (
        f"the audit row was never written inside the transaction "
        f"({before} -> {seen_inside}), so its disappearance below would prove "
        f"nothing about atomicity"
    )
    if savepoint.is_active:
        savepoint.rollback()
    assert pg_session.query(AuditLog).count() == before, (
        "an audit row outlived the mutation it describes"
    )


@pg_only
@pytest.mark.integration
def test_a_service_built_without_an_actor_audits_visibly_unattributed(pg_session) -> None:
    """Fail loud, not silent: no actor must not mean a borrowed actor."""
    svc_with = _service(pg_session)
    svc_with.create_blood_request({"patient_id": "NR027-P1", "blood_group": "O+",
                                   "units_requested": 1})
    svc_without = _service(pg_session, user_id=None)
    svc_without.create_blood_request({"patient_id": "NR027-P2", "blood_group": "A+",
                                      "units_requested": 1})

    rows = _audit_rows(pg_session, "bloodbank.request.create")
    assert len(rows) == 2
    actors = [r.user_id for r in rows]
    assert ACTOR in actors, "the attributed write lost its actor"
    assert None in actors, (
        f"the unattributed write borrowed an actor instead of recording NULL: "
        f"{actors}"
    )
