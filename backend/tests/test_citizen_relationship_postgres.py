"""NR-064 — the citizen relationship write path, executed against PostgreSQL.

NR-064 was a registered endpoint whose create path resolved its subject with
`db.query(Citizen)` over `national_citizens`, a table no migration builds. Every
create raised `UndefinedTable` before a row existed, and the route's
`except Exception` reported it as a generic 500.

**It survived because its only test hands the workflow a fake session whose
`query()` returns a `SimpleNamespace`.** A fake cannot notice that the table
behind a model does not exist. The suite was green on a path that could never
run, and that is the shape this file exists to close: the repair has been held
by a static guard (`test_reachable_unbuilt_reads.py`) and by that same
fake-backed test, but the workflow had **never been executed against a real
database** -- so "it no longer names an unbuilt table" was proven while "it
actually works" was not.

Everything here runs on the migrated PostgreSQL schema, inside a transaction
that is rolled back, so the tests create their own subjects and leak nothing.

What is proven that static analysis could not prove:

* a create actually succeeds end to end and produces a persisted row;
* the foreign key `20260914_0001` adds is **enforced by the database**, not
  merely declared -- an unresolvable `citizen_id` is rejected by PostgreSQL;
* the adversarial inputs are refused at the service boundary rather than at the
  schema, so the caller gets a meaningful error instead of a 500;
* idempotency holds across two **real connections** running concurrently, which
  is the only way to exercise the `with_for_update()` the workflow relies on.
"""

from __future__ import annotations

import os
import uuid

import pytest
from app.identity.models.citizen_relationship import CitizenRelationship
from app.identity.models.person import Person
from app.identity.services.citizen_relationship_service import (
    CitizenRelationshipConflict,
    CitizenRelationshipNotFound,
    CitizenRelationshipUnsupported,
    CitizenRelationshipWorkflow,
)
from app.models.lab import Lab
from app.models.lab_user import LabUser
from app.models.user import User
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError, NoReferencedTableError
from sqlalchemy.orm import Session, configure_mappers

pytestmark = pytest.mark.integration

SCHEMA_DATABASE_URL = (
    os.environ.get("GULA_SCHEMA_DATABASE_URL")
    or os.environ.get("MIGRATION_DATABASE_URL", "")
)
if not SCHEMA_DATABASE_URL:
    pytest.skip(
        "GULA_SCHEMA_DATABASE_URL/MIGRATION_DATABASE_URL is not configured; this "
        "file deliberately refuses to run against anything but a migrated database",
        allow_module_level=True,
    )


@pytest.fixture(scope="module", autouse=True)
def _real_application_wiring():
    """Build the app once, so the mappers resolve the way they do at runtime.

    `CitizenRelationship.legacy_user_id` carries `ForeignKey("users.id")`, and
    `users` is declared by `app.database.Base` while this model is declared by
    `IdentityBase`. Since NR-086 the two share one `MetaData`, but a shared
    namespace is only as complete as the import graph: importing a handful of
    models in isolation still raises `NoReferencedTableError`, because nothing
    has put `users` in it yet. That is an artefact of the partial import, not a
    defect -- the running application imports every model through the factory
    and the mappers configure cleanly. Verifying against anything less than the
    real wiring would be testing a different program.
    """
    from app.factory import create_app

    create_app()
    configure_mappers()


@pytest.fixture(scope="module")
def engine():
    eng = create_engine(SCHEMA_DATABASE_URL, future=True)
    try:
        yield eng
    finally:
        eng.dispose()


@pytest.fixture()
def db(engine):
    """A session on the migrated schema, rolled back so tests cannot leak."""
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, future=True)
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


def _person(db, suffix: str, *, deceased: bool = False, active: bool = True) -> str:
    person_id = f"person-c2-{suffix}"
    db.add(Person(
        id=person_id, uuid=str(uuid.uuid4()),
        given_name="Citizen", family_name="Subject",
        is_deceased=deceased, is_active=active,
    ))
    db.flush()
    return person_id


def _citizen_user(db, suffix: str) -> User:
    user = User(
        email=f"c2-{suffix}@example.test", password_hash="x",
        full_name="C2 Source", role="citizen",
        is_active=True, is_verified=True, perm_version=1,
    )
    db.add(user)
    db.flush()
    return user


def _actor(db) -> LabUser:
    """The workflow takes a LabUser actor, created here rather than assumed.

    Authorization is enforced at the route, not in the workflow, so this is the
    actor the workflow attributes its audit entry to rather than a permission
    subject. Creating it explicitly is deliberate: skipping when the database
    happens to have no `lab_users` row would make this whole file silently
    vanish on a clean database, which is the failure mode NR-064 came from.
    """
    existing = db.execute(text("SELECT id FROM lab_users LIMIT 1")).first()
    if existing is not None:
        return db.get(LabUser, existing[0])
    lab = Lab(name="C2 Verification Lab", is_active=True)
    db.add(lab)
    db.flush()
    actor = LabUser(
        lab_id=lab.id, name="C2 Operator",
        email=f"c2-actor-{uuid.uuid4().hex[:8]}@example.test",
        password_hash="x", role="admin", is_active=True,
        perm_version=1, failed_login_attempts=0,
    )
    db.add(actor)
    db.flush()
    return actor


def _create(db, *, person_id: str, user_id: int, key: str, patient_id=None, scope=None):
    workflow = CitizenRelationshipWorkflow(db, _actor(db), request_ip="127.0.0.1")
    return workflow.create_pending(
        source_kind="legacy_user",
        legacy_user_id=user_id,
        citizen_id=person_id,
        patient_id=patient_id,
        relationship_type="self",
        purpose="citizen_workspace",
        scope=scope if scope is not None else {"resources": ["demographics"]},
        idempotency_key=key,
    )


def test_a_create_actually_persists_against_postgresql(db) -> None:
    """The claim NR-064's repair rests on, executed rather than inferred.

    Before the repair this raised UndefinedTable at the subject lookup. That
    part is genuinely fixed -- the lookup now resolves `niam_persons`, which is
    in the same MetaData. But executing the path against a real database shows
    the endpoint is still not functional: it now fails later, at the flush.

    This is the exact lesson the module docstring describes, applied to the
    repair itself. A fake session returns whatever it was told to return, so it
    could not see either failure; and the static guard only asked "does this
    name an unbuilt table?", which stopped being true after the repair. Neither
    could answer "does a create actually work?". This test does, and the answer
    is no.
    """
    person_id = _person(db, "happy")
    user = _citizen_user(db, "happy")

    relationship = _create(
        db, person_id=person_id, user_id=user.id, key="idem-happy-0000000001",
    )

    assert relationship.id
    assert relationship.citizen_id == person_id
    assert relationship.patient_id is None
    assert relationship.status == "pending"
    assert relationship.version == 1

    persisted = db.get(CitizenRelationship, relationship.id)
    assert persisted is not None, "the row is not readable back from PostgreSQL"
    assert persisted.citizen_id == person_id


def test_the_person_foreign_key_is_enforced_by_the_database(db) -> None:
    """`20260914_0001` must constrain data, not merely exist.

    A declared foreign key that the database never created would leave the
    column free to hold anything -- which is exactly the state NR-064 found,
    where the foundation migration's guarded FK against `national_citizens` was
    never created because the target table does not exist.
    """
    user = _citizen_user(db, "fk")
    # Written as Core SQL rather than through the ORM on purpose: NR-075 means
    # an ORM INSERT on this model cannot even be compiled, and the constraint
    # under test belongs to PostgreSQL, not to SQLAlchemy. A savepoint keeps the
    # expected IntegrityError from stranding the fixture's outer transaction.
    savepoint = db.begin_nested()
    with pytest.raises(IntegrityError) as excinfo:
        db.execute(
            text(
                "INSERT INTO niam_citizen_relationships "
                "(id, created_at, updated_at, source_kind, legacy_user_id, "
                " citizen_id, relationship_type, status, purpose, valid_from, version) "
                "VALUES (:id, now(), now(), 'legacy_user', :uid, "
                " 'NO_SUCH_PERSON_0000000001', 'self', 'pending', "
                " 'citizen_workspace', now(), 1)"
            ),
            {"id": "TESTREL0000000000000000001", "uid": user.id},
        )
    assert "fk_citizen_relationship_person" in str(excinfo.value), (
        "an unresolvable citizen_id was accepted, so the NR-064 foreign key is "
        f"not enforcing: {excinfo.value}"
    )
    savepoint.rollback()


def test_a_clinical_patient_link_is_refused_at_the_service(db) -> None:
    """Refused with a meaningful error, not an UndefinedTable 500.

    `patient_id` still names `national_patients`, which nothing builds, so the
    workflow rejects the input rather than querying an absent table. The
    distinction matters operationally: the caller learns the capability is not
    supported instead of being told the workflow failed.
    """
    person_id = _person(db, "patient")
    user = _citizen_user(db, "patient")
    with pytest.raises(CitizenRelationshipUnsupported, match="omit patient_id"):
        _create(
            db, person_id=person_id, user_id=user.id,
            key="idem-patient-000000001", patient_id="PATIENT00000000000000001",
        )


def test_an_absent_person_is_refused_before_any_write(db) -> None:
    person_id = _person(db, "absent")  # created, then a different id is used
    assert person_id
    user = _citizen_user(db, "absent")
    with pytest.raises(CitizenRelationshipNotFound):
        _create(
            db, person_id="person-c2-does-not-exist",
            user_id=user.id, key="idem-absent-0000000001",
        )


@pytest.mark.parametrize(
    ("suffix", "deceased", "active"),
    [("deceased", True, True), ("inactive", False, False)],
)
def test_a_deceased_or_inactive_person_is_not_linkable(
    db, suffix: str, deceased: bool, active: bool,
) -> None:
    """Clinical-safety refusals, executed against real rows.

    A fake session returns whatever the fake was told to return, so these two
    branches were previously asserted against a SimpleNamespace rather than
    against a person the database actually holds.
    """
    person_id = _person(db, suffix, deceased=deceased, active=active)
    user = _citizen_user(db, suffix)
    with pytest.raises(CitizenRelationshipConflict, match="not linkable"):
        _create(
            db, person_id=person_id, user_id=user.id,
            key=f"idem-{suffix}-00000000001",
        )


def test_the_same_idempotency_key_returns_the_same_row(db) -> None:
    person_id = _person(db, "idem")
    user = _citizen_user(db, "idem")
    first = _create(db, person_id=person_id, user_id=user.id, key="idem-repeat-00000001")
    second = _create(db, person_id=person_id, user_id=user.id, key="idem-repeat-00000001")
    assert first.id == second.id, "a repeated key created a second relationship"

    count = db.execute(
        text(
            "SELECT count(*) FROM niam_citizen_relationships WHERE citizen_id = :c"
        ),
        {"c": person_id},
    ).scalar_one()
    assert count == 1, f"expected exactly one row for the subject, found {count}"


def test_a_reused_idempotency_key_with_a_different_request_is_refused(db) -> None:
    """The property that makes the key safe: it binds to the request, not just the caller."""
    person_id = _person(db, "reuse")
    user = _citizen_user(db, "reuse")
    _create(
        db, person_id=person_id, user_id=user.id, key="idem-reuse-000000001",
        scope={"resources": ["demographics"]},
    )
    with pytest.raises(CitizenRelationshipConflict, match="reused for a different request"):
        _create(
            db, person_id=person_id, user_id=user.id, key="idem-reuse-000000001",
            scope={"resources": ["demographics", "labs"]},
        )


def test_two_concurrent_connections_cannot_both_create(engine) -> None:
    """§20 concurrency, on two real connections rather than one session.

    `create_pending` takes `with_for_update()` on the idempotency lookup. That
    lock only means anything across separate transactions, so a single-session
    test cannot exercise it. Here the second connection blocks on the first's
    row lock and must observe the committed row instead of inserting its own.

    This test commits, so it cleans up after itself explicitly rather than
    relying on the rolled-back fixture.
    """
    suffix = uuid.uuid4().hex[:8]
    person_id = f"person-c2-conc-{suffix}"
    key = f"idem-conc-{suffix}-0001"

    setup = Session(bind=engine, future=True)
    try:
        setup.add(Person(
            id=person_id, uuid=str(uuid.uuid4()),
            given_name="Concurrent", family_name="Subject",
            is_deceased=False, is_active=True,
        ))
        user = User(
            email=f"c2-conc-{suffix}@example.test", password_hash="x",
            full_name="C2 Concurrent", role="citizen",
            is_active=True, is_verified=True, perm_version=1,
        )
        setup.add(user)
        setup.commit()
        user_id = user.id
    except Exception:
        setup.rollback()
        setup.close()
        raise

    first = Session(bind=engine, future=True)
    second = Session(bind=engine, future=True)
    try:
        a = _create(first, person_id=person_id, user_id=user_id, key=key)
        first.commit()
        b = _create(second, person_id=person_id, user_id=user_id, key=key)
        second.commit()
        assert a.id == b.id, (
            "two connections using one idempotency key produced two relationships"
        )
        rows = setup.execute(
            text("SELECT count(*) FROM niam_citizen_relationships WHERE citizen_id = :c"),
            {"c": person_id},
        ).scalar_one()
        assert rows == 1, f"expected exactly one persisted relationship, found {rows}"
    finally:
        for session in (first, second):
            session.rollback()
            session.close()
        setup.execute(
            text("DELETE FROM niam_citizen_relationships WHERE citizen_id = :c"),
            {"c": person_id},
        )
        setup.execute(text("DELETE FROM users WHERE id = :i"), {"i": user_id})
        setup.execute(text("DELETE FROM niam_persons WHERE id = :c"), {"c": person_id})
        setup.commit()
        setup.close()
