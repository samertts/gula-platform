"""C09 event-fabric evidence on disposable PostgreSQL 16.

Set ``GULA_V4_EVENTS_PG_DSN`` to a throwaway database migrated to Alembic head
``20261124_0003``. Only synthetic identifiers and payloads are used.
"""
from __future__ import annotations

import os
from collections.abc import Iterator
from datetime import datetime
from typing import Any

import app.services.mpi.models  # noqa: F401 - registers an unrelated HEAD relationship
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from app._compat import UTC

DSN = os.getenv("GULA_V4_EVENTS_PG_DSN", "")
pytestmark = pytest.mark.skipif(
    not DSN, reason="GULA_V4_EVENTS_PG_DSN is required for PG16 event evidence"
)


@pytest.fixture(scope="module")
def engine() -> Iterator[Any]:
    eng = create_engine(DSN)
    with eng.connect() as conn:
        assert conn.dialect.name == "postgresql"
        assert "PostgreSQL 16" in conn.execute(text("SELECT version()")).scalar_one()
        assert conn.execute(text("SELECT current_database()")).scalar_one() == "gula_v4_events"
        assert conn.execute(text("SELECT version_num FROM alembic_version")).scalar_one() == (
            "20261124_0003"
        )
    yield eng
    eng.dispose()


@pytest.fixture()
def sessions(engine: Any) -> Iterator[Any]:
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE outbox_events, integration_inbox_events RESTART IDENTITY CASCADE"))
    yield sessionmaker(bind=engine)


def envelope(event_id: str, sequence: int, event_type: str = "pg.order.created"):
    from app.eventing.authority import CanonicalEventEnvelope

    return CanonicalEventEnvelope.model_validate(
        {
            "event_id": event_id,
            "event_type": event_type,
            "schema_version": 1,
            "source_service": "pg-contract-test",
            "tenant_id": "lab-pg",
            "occurred_at": datetime.now(UTC),
            "actor_id": "user-pg",
            "entity_id": f"entity-{sequence}",
            "correlation_id": f"corr-{sequence}",
            "idempotency_key": f"idem-{sequence}",
            "payload": {"sequence": sequence},
            "aggregate_type": "order",
            "aggregate_id": f"entity-{sequence}",
            "sequence": sequence,
        }
    )


def test_migration_created_canonical_outbox_columns_and_unique_id(engine: Any) -> None:
    with engine.connect() as conn:
        columns = {
            row[0]
            for row in conn.execute(
                text(
                    "SELECT column_name FROM information_schema.columns "
                    "WHERE table_name = 'outbox_events'"
                )
            )
        }
        constraints = {
            row[0]
            for row in conn.execute(
                text(
                    "SELECT conname FROM pg_constraint "
                    "WHERE conrelid = 'outbox_events'::regclass"
                )
            )
        }
    for required in (
        "event_id",
        "schema_version",
        "source_service",
        "tenant_id",
        "actor_id",
        "entity_id",
        "correlation_id",
        "idempotency_key",
        "sequence",
    ):
        assert required in columns
    assert "uq_outbox_events_event_id" in constraints


def test_publish_is_durable_ordered_and_idempotent(sessions: Any, engine: Any) -> None:
    from app.eventing.authority import NationalEventAuthority

    with sessions() as db:
        NationalEventAuthority.publish(db, envelope("pg-evt-2", 2))
        NationalEventAuthority.publish(db, envelope("pg-evt-1", 1))
        db.commit()
    with sessions() as db:
        rows = db.execute(
            text("SELECT event_id, sequence FROM outbox_events ORDER BY sequence")
        ).mappings().all()
    assert [(row["event_id"], row["sequence"]) for row in rows] == [
        ("pg-evt-1", 1),
        ("pg-evt-2", 2),
    ]

    with sessions() as db:
        with pytest.raises(IntegrityError):
            NationalEventAuthority.publish(db, envelope("pg-evt-1", 1))
    with sessions() as db:
        assert db.execute(text("SELECT COUNT(*) FROM outbox_events")).scalar_one() == 2


def test_strict_drain_acknowledges_only_delivered_events(sessions: Any) -> None:
    from app.eventing.authority import NationalEventAuthority

    with sessions() as db:
        NationalEventAuthority.publish(db, envelope("pg-strict", 3))
        db.commit()
    with sessions() as db:
        summary = NationalEventAuthority.drain(
            db, require_handler=True, dispatcher=lambda _name, _payload: 0
        )
    assert summary == {"processed": 0, "failed": 0, "skipped": 1}

    with sessions() as db:
        row = db.execute(
            text("SELECT status, attempts, last_error FROM outbox_events")
        ).mappings().one()
    assert row["status"] == "failed"
    assert row["attempts"] == 1
    assert "no registered handler" in row["last_error"]

    with sessions() as db:
        summary = NationalEventAuthority.drain(
            db, require_handler=True, dispatcher=lambda _name, _payload: 1
        )
    assert summary == {"processed": 1, "failed": 0, "skipped": 0}
    with sessions() as db:
        assert db.execute(text("SELECT status FROM outbox_events")).scalar_one() == "done"


def test_legacy_emit_and_inbound_stage_share_the_authoritative_core(sessions: Any) -> None:
    from app.contracts.integration import IntegrationEventEnvelope
    from app.eventing.authority import NationalEventAuthority
    from app.services.outbox_service import emit_to_outbox

    with sessions() as db:
        emit_to_outbox(db, "pg.legacy.event", {"legacy": True}, "order", 42)
        inbound = IntegrationEventEnvelope.model_validate(
            {
                "event_id": "pg-inbound-1",
                "event_type": "frontend.sync.requested",
                "schema_version": 1,
                "source_service": "frontend-v3",
                "tenant_id": "lab-pg",
                "occurred_at": datetime.now(UTC),
                "actor_id": "user-pg",
                "entity_id": "action-1",
                "correlation_id": "corr-pg",
                "idempotency_key": "idem-pg-inbound",
                "payload": {"action_id": "a1", "action_type": "sync", "payload": {}},
            }
        )
        first = NationalEventAuthority.stage_inbound(db, inbound)
        second = NationalEventAuthority.stage_inbound(db, inbound)
        db.commit()
    assert first.status == "staged"
    assert second.status == "duplicate"

    with sessions() as db:
        legacy = db.execute(
            text(
                "SELECT event_id, tenant_id, source_service FROM outbox_events "
                "WHERE event_type = 'pg.legacy.event'"
            )
        ).mappings().one()
    assert legacy["event_id"].startswith("legacy-")
    assert legacy["tenant_id"] == "system"
    assert legacy["source_service"] == "legacy-outbox"
