"""Wave A CRUD evidence on disposable PostgreSQL 16.

Set ``GULA_V4_PG_DSN`` to a throwaway database migrated to Alembic head. The
test uses only synthetic lab/user identifiers and never touches a live service.
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from typing import Any

import app.services.mpi.models  # noqa: F401 - registers an unrelated HEAD relationship
import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

DSN = os.getenv("GULA_V4_PG_DSN", "")
pytestmark = pytest.mark.skipif(not DSN, reason="GULA_V4_PG_DSN is required for PG16 CRUD evidence")

CAPABILITY = "clinical_foundation"
ACTOR = {"user_id": 99001, "lab_id": 88001, "role": "admin"}
OTHER_ACTOR = {"user_id": 99002, "lab_id": 88002, "role": "admin"}


@pytest.fixture(scope="module")
def engine() -> Iterator[Any]:
    eng = create_engine(DSN)
    with eng.connect() as conn:
        assert conn.dialect.name == "postgresql"
        assert "PostgreSQL 16" in conn.execute(text("SELECT version()")).scalar_one()
        db_name = conn.execute(text("SELECT current_database()")).scalar_one()
        assert db_name.startswith("gula_") and (
            "test" in db_name or "gate" in db_name or "crud" in db_name
        )
        assert conn.execute(text("SELECT version_num FROM alembic_version")).scalar_one() == (
            "20261124_0002"
        )
    yield eng
    eng.dispose()


@pytest.fixture()
def sessions(engine: Any) -> Iterator[Any]:
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE capability_records, audit_logs RESTART IDENTITY"))
    yield sessionmaker(bind=engine)


def test_migration_created_ownership_columns_and_jsonb(engine: Any) -> None:
    with engine.connect() as conn:
        columns = {
            row[0]: row[1]
            for row in conn.execute(
                text(
                    "SELECT column_name, data_type FROM information_schema.columns "
                    "WHERE table_name = 'capability_records'"
                )
            )
        }
        indexes = {
            row[0]
            for row in conn.execute(
                text("SELECT indexname FROM pg_indexes WHERE tablename = 'capability_records'")
            )
        }
    assert columns["lab_id"] == "integer"
    assert columns["owner_user_id"] == "integer"
    assert columns["payload"] == "jsonb"
    assert "ix_capability_records_lab_capability" in indexes


def test_crud_lifecycle_is_durable_and_lab_scoped(sessions: Any) -> None:
    from app.capabilities._shared import crud

    with sessions() as db:
        record = crud.create_record(
            db, CAPABILITY, {"name": "pg-record", "status": "active"}, ACTOR
        )
    assert record["lab_id"] == ACTOR["lab_id"]
    assert record["owner_user_id"] == ACTOR["user_id"]

    with sessions() as db:
        listed = crud.list_records(db, CAPABILITY, ACTOR)
        assert listed["total"] == 1
        assert crud.list_records(db, CAPABILITY, OTHER_ACTOR)["total"] == 0
        with pytest.raises(HTTPException) as exc:
            crud.get_record(db, CAPABILITY, record["id"], OTHER_ACTOR)
        assert exc.value.status_code == 404

    with sessions() as db:
        updated = crud.update_record(
            db, CAPABILITY, record["id"], {"name": "pg-updated"}, ACTOR
        )
    assert updated["name"] == "pg-updated"

    with sessions() as db:
        deleted = crud.delete_record(db, CAPABILITY, record["id"], ACTOR)
    assert deleted["success"] is True

    with sessions() as db:
        assert crud.list_records(db, CAPABILITY, ACTOR)["total"] == 0


def test_failed_validation_does_not_write_record_or_audit(sessions: Any, engine: Any) -> None:
    from app.capabilities._shared import crud

    db = sessions()
    with pytest.raises(HTTPException) as exc:
        crud.create_record(db, CAPABILITY, {"lab_id": 999}, ACTOR)
    assert exc.value.status_code == 422
    db.rollback()
    db.close()

    with engine.connect() as conn:
        assert conn.execute(text("SELECT COUNT(*) FROM capability_records")).scalar_one() == 0
        assert conn.execute(text("SELECT COUNT(*) FROM audit_logs")).scalar_one() == 0


def test_explicit_rollback_leaves_no_partial_record(sessions: Any, engine: Any) -> None:
    try:
        with sessions() as db:
            with db.begin():
                db.execute(
                    text(
                        "INSERT INTO capability_records "
                        "(capability, record_id, lab_id, owner_user_id, payload) "
                        "VALUES (:capability, :record_id, :lab_id, :owner, '{}'::jsonb)"
                    ),
                    {
                        "capability": CAPABILITY,
                        "record_id": "rollback-0001",
                        "lab_id": ACTOR["lab_id"],
                        "owner": ACTOR["user_id"],
                    },
                )
                raise RuntimeError("forced rollback")
    except RuntimeError:
        pass

    with engine.connect() as conn:
        assert conn.execute(text("SELECT COUNT(*) FROM capability_records")).scalar_one() == 0


def test_audit_events_use_the_authenticated_actor(sessions: Any, engine: Any) -> None:
    from app.capabilities._shared import crud

    with sessions() as db:
        record = crud.create_record(db, CAPABILITY, {"name": "audit"}, ACTOR)
    with sessions() as db:
        rows = db.execute(
            text(
                "SELECT user_id, lab_id, action FROM audit_logs "
                "WHERE resource_type = :capability ORDER BY id"
            ),
            {"capability": CAPABILITY},
        ).mappings().all()
    assert rows == [
        {
            "user_id": ACTOR["user_id"],
            "lab_id": ACTOR["lab_id"],
            "action": "capability_record.create",
        }
    ]

    with engine.begin() as conn:
        conn.execute(text("DELETE FROM capability_records WHERE record_id = :id"), {"id": record["id"]})
