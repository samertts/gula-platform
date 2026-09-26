"""The laboratory's core journey, end to end over real HTTP against PostgreSQL.

Register a specimen, walk it through its state machine to ``verified``, enter a
result, validate it and release it — the sequence a laboratory actually performs,
and the one the product exists to do.

Every mutating step carries ``If-Match`` and ``Idempotency-Key``, because the
LIMS command routes enforce both, and each step asserts committed state rather
than trusting a 2xx. The journey is written as one test because a later step is
meaningless if an earlier one did not really happen.
"""

from __future__ import annotations

import datetime as dt
import os
import uuid
from typing import Any

import pytest
from sqlalchemy import text

from . import harness

pytestmark = harness.requires_postgres()

LAB_ID = 995001
ACTOR_ID = 75001

# The state machine path from a freshly registered specimen to one a result may
# be entered against (app/lims/state_machine.py::_SPECIMEN_TRANSITIONS).
TO_VERIFIED = ("registered", "collected", "received", "accepted", "analyzing",
               "analyzed", "verified")

# The LIMS command routes sit behind a fail-closed release policy
# (app/core/release_capabilities.py). Enabling it here is the deployment
# configuration a real tenant would be given, read from the environment on every
# call — not a bypass: the gate still runs, and
# ``test_an_unapproved_tenant_is_still_refused`` proves it refuses without this.
# The ``starter`` tier, which is the default when a lab has no subscription row,
# already carries the ``sample_tracking`` and ``basic_results`` entitlements.
RELEASE_CAPABILITIES = (
    "phase1.lims.orders",
    "phase1.lims.sample_tracking",
    "phase1.lims.result_entry",
    "phase1.lims.result_approval",
)


@pytest.fixture()
def release_policy_enabled() -> Any:
    previous = {
        key: os.environ.get(key)
        for key in ("GULA_RELEASE_ENABLED_CAPABILITIES", "GULA_RELEASE_APPROVED_TENANT_IDS")
    }
    os.environ["GULA_RELEASE_ENABLED_CAPABILITIES"] = ",".join(RELEASE_CAPABILITIES)
    os.environ["GULA_RELEASE_APPROVED_TENANT_IDS"] = str(LAB_ID)
    yield
    for key, value in previous.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value


def _now() -> dt.datetime:
    return dt.datetime.now(dt.UTC)


@pytest.fixture()
def Session() -> Any:
    S = harness.session_factory(pool_size=4)
    yield S
    harness.dispose(S)


def _purge(S: Any) -> None:
    with S() as s:
        for table in ("lims_results", "lims_specimens", "clinical_command_receipts",
                      "lab_orders", "patients"):
            s.execute(text(f"DELETE FROM {table} WHERE lab_id = :l"), {"l": LAB_ID})
        s.execute(text("DELETE FROM lab_users WHERE lab_id = :l"), {"l": LAB_ID})
        s.execute(text("DELETE FROM labs WHERE id = :l"), {"l": LAB_ID})
        s.commit()


@pytest.fixture()
def seeded(Session: Any) -> dict[str, Any]:
    _purge(Session)
    with Session() as s:
        s.execute(text("INSERT INTO labs (id,name,is_active) VALUES (:l,'Journey Lab',true)"),
                  {"l": LAB_ID})
        s.execute(
            text("INSERT INTO lab_users (id,lab_id,name,email,password_hash,role,is_active,"
                 "perm_version) VALUES (:i,:l,'Journey Actor',:e,'!synthetic','master_admin',true,1)"),
            {"i": ACTOR_ID, "l": LAB_ID, "e": f"journey-{uuid.uuid4().hex[:8]}@example.invalid"},
        )
        patient_id = s.execute(
            text("INSERT INTO patients (lab_id,full_name,phone) VALUES (:l,'Journey Patient',:p) "
                 "RETURNING id"),
            {"l": LAB_ID, "p": f"0771{uuid.uuid4().hex[:7]}"},
        ).scalar_one()
        order_id = s.execute(
            text("INSERT INTO lab_orders (lab_id,patient_id) VALUES (:l,:p) RETURNING id"),
            {"l": LAB_ID, "p": patient_id},
        ).scalar_one()
        s.commit()
    return {"order_id": order_id, "patient_id": patient_id}


def _actor() -> harness.Actor:
    return harness.Actor(user_id=ACTOR_ID, lab_id=LAB_ID, role="master_admin")


def _cmd_headers(version: int) -> dict[str, str]:
    return {"If-Match": str(version), "Idempotency-Key": uuid.uuid4().hex}


def _specimen_row(Session: Any, specimen_id: int) -> dict[str, Any]:
    rows = harness.committed(
        Session,
        "SELECT id, status, version FROM lims_specimens WHERE id = :i AND lab_id = :l",
        i=specimen_id, l=LAB_ID,
    )
    assert rows, f"specimen {specimen_id} is not committed"
    return rows[0]


def test_specimen_to_released_result(
    Session: Any, seeded: dict[str, Any], release_policy_enabled: Any
) -> None:
    barcode = f"JRN-{uuid.uuid4().hex[:10].upper()}"
    with harness.client(Session, _actor()) as client:
        # 1. Register the specimen against a real order.
        created = client.post("/lims/specimens", json={
            "order_id": seeded["order_id"],
            "barcode": barcode,
            "specimen_type": "whole_blood",
            "container_type": "edta",
            "volume_ml": 4.0,
        })
        assert created.status_code == 201, f"register failed: {created.text[:400]}"
        specimen_id = created.json()["id"]
        row = _specimen_row(Session, specimen_id)
        assert row["status"], "a registered specimen must have a status"

        # 2. Walk the state machine to ``verified``.
        for target in TO_VERIFIED:
            current = _specimen_row(Session, specimen_id)
            response = client.put(
                f"/lims/specimens/{specimen_id}/status",
                json={"target_status": target},
                headers=_cmd_headers(current["version"]),
            )
            assert response.status_code == 200, (
                f"{current['status']} -> {target} failed: {response.status_code} "
                f"{response.text[:300]}"
            )
            after = _specimen_row(Session, specimen_id)
            assert after["status"] == target, (
                f"the route answered 200 but committed state is {after['status']!r}, not {target!r}"
            )
            assert after["version"] > current["version"], (
                "a committed transition must advance the optimistic lock: "
                f"{current['version']} -> {after['version']}"
            )

        # 3. An invalid transition must be refused from ``verified``.
        current = _specimen_row(Session, specimen_id)
        bad = client.put(
            f"/lims/specimens/{specimen_id}/status",
            json={"target_status": "collected"},
            headers=_cmd_headers(current["version"]),
        )
        assert bad.status_code == 409, f"verified -> collected must be refused, got {bad.status_code}"
        assert _specimen_row(Session, specimen_id)["status"] == "verified", (
            "a refused transition must not change committed state"
        )

        # 4. Enter a result against the verified specimen.
        current = _specimen_row(Session, specimen_id)
        result = client.post("/lims/results", json={
            "specimen_id": specimen_id,
            "test_code": "HGB",
            "test_name": "Haemoglobin",
            "value_numeric": 13.4,
            "unit": "g/dL",
            "loinc_code": "718-7",
        }, headers=_cmd_headers(current["version"]))
        assert result.status_code == 201, f"result entry failed: {result.text[:400]}"
        result_id = result.json()["id"]

        committed = harness.committed(
            Session,
            "SELECT id, validation_status, result_status, value_numeric, version "
            "FROM lims_results WHERE id = :i AND lab_id = :l", i=result_id, l=LAB_ID)
        assert len(committed) == 1, f"the result is not durable: {committed}"
        assert float(committed[0]["value_numeric"]) == 13.4

        # 5. Validate, then release. Validation demands an electronic signature —
        # a clinical control, so the journey supplies one rather than avoiding it.
        bodies = {
            "validate": {"action": "validate",
                         "signature_hash": uuid.uuid4().hex,
                         "notes": "reviewed against the delta check"},
            "release": {},
        }
        for step in ("validate", "release"):
            if step == "release":
                # Releasing a result also advances its specimen, and the specimen
                # machine requires verified -> validated -> released. The laboratory
                # signs off the specimen before the result leaves the building.
                specimen_now = _specimen_row(Session, specimen_id)
                moved = client.put(
                    f"/lims/specimens/{specimen_id}/status",
                    json={"target_status": "validated"},
                    headers=_cmd_headers(specimen_now["version"]),
                )
                assert moved.status_code == 200, (
                    f"specimen verified -> validated failed: {moved.text[:300]}"
                )
                assert _specimen_row(Session, specimen_id)["status"] == "validated"
            before = harness.committed(
                Session, "SELECT validation_status, version FROM lims_results WHERE id = :i",
                i=result_id)[0]
            response = client.post(
                f"/lims/results/{result_id}/{step}",
                json=bodies[step],
                headers=_cmd_headers(before["version"]),
            )
            assert response.status_code == 200, (
                f"{step} failed from validation_status {before['validation_status']!r}: "
                f"{response.status_code} {response.text[:300]}"
            )
            after = harness.committed(
                Session, "SELECT validation_status, version FROM lims_results WHERE id = :i",
                i=result_id)[0]
            assert after["version"] > before["version"], (
                f"{step} must advance the result version: {before} -> {after}"
            )
            assert after["validation_status"] != before["validation_status"], (
                f"{step} answered 200 but the committed validation_status is still "
                f"{after['validation_status']!r}"
            )

        final = harness.committed(
            Session, "SELECT validation_status FROM lims_results WHERE id = :i", i=result_id)[0]
        assert final["validation_status"] == "released", (
            f"final result validation_status is {final['validation_status']!r}"
        )

    # 6. The journey's own audit trail must be tenant-scoped and truthfully attributed.
    # These rows are what the positional log_action() calls used to corrupt: the
    # description landed in ``lab_id`` (an integer column), so the INSERT raised and
    # the command failed; and the role was hardcoded to "lab_tech" whoever acted.
    rows = harness.committed(
        Session,
        "SELECT action, resource_type, user_id, user_role, lab_id, details "
        "FROM audit_logs WHERE lab_id = :l AND resource_type IN "
        "('lims_specimen','lims_result') ORDER BY id",
        l=LAB_ID,
    )
    assert rows, "the journey wrote no tenant-scoped audit rows"
    assert {r["resource_type"] for r in rows} == {"lims_specimen", "lims_result"}, (
        f"both the specimen and the result must be audited: {sorted({r['resource_type'] for r in rows})}"
    )
    for row in rows:
        assert row["lab_id"] == LAB_ID, f"audit row is not tenant-scoped: {row}"
        assert row["user_id"] == ACTOR_ID, f"audit row names the wrong actor: {row}"
        assert row["user_role"] == "master_admin", (
            f"audit row must record the actor's real role, not a hardcoded one: {row}"
        )
        assert row["details"], f"audit row lost its description: {row}"


def test_an_unapproved_tenant_is_still_refused(Session: Any, seeded: dict[str, Any]) -> None:
    """Without the release approval the same call must be refused, not served.

    This is the control for the fixture above: it proves the journey passes
    because the tenant is entitled and approved, not because the gate was removed.
    """
    with harness.client(Session, _actor()) as client:
        response = client.post("/lims/specimens", json={
            "order_id": seeded["order_id"],
            "barcode": f"JRN-DENY-{uuid.uuid4().hex[:6].upper()}",
            "specimen_type": "whole_blood",
        })
    assert response.status_code == 403, (
        f"an unapproved tenant must be refused, got {response.status_code}: {response.text[:300]}"
    )
    assert harness.committed(
        Session, "SELECT id FROM lims_specimens WHERE lab_id = :l", l=LAB_ID
    ) == [], "a refused registration must leave no specimen behind"
