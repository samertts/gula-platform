"""The bind parameter that PostgreSQL's cast operator swallowed.

Boot-time AI model seeding failed on every startup. ``text()`` scans for
``:name`` bind parameters, and PostgreSQL's cast operator is ``::``, so in
``:caps::jsonb`` SQLAlchemy declines to treat ``:caps`` as a parameter. The
literal text reached the driver and psycopg2 rejected it, leaving the
statement permanently unexecutable rather than merely wrong.

``CAST(:caps AS jsonb)`` is the same cast written so the two syntaxes cannot
collide. Recorded as MCM-P1-3.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

APP = Path(__file__).resolve().parents[1] / "app"

# ``:name`` immediately followed by ``::type``. Deliberately repository-wide:
# the same defect appeared in three files, so a test naming only the one that
# broke startup would let the next one through.
COLLISION = re.compile(r":[A-Za-z_]\w*::\w+")

POSTGRES_URL = os.getenv("PHARMACY_POSTGRES_URL")


def test_no_bind_parameter_is_followed_by_a_postgresql_cast() -> None:
    """The guard. Any reintroduction fails here, in any module."""
    offenders: list[str] = []
    for path in sorted(APP.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        for number, line in enumerate(
            path.read_text(encoding="utf-8", errors="replace").splitlines(), 1
        ):
            if COLLISION.search(line):
                offenders.append(f"{path.relative_to(APP.parent)}:{number}")
    assert offenders == [], (
        "a bind parameter is followed by a PostgreSQL '::' cast, which "
        "SQLAlchemy will not bind; write CAST(:name AS type) instead: "
        + ", ".join(offenders)
    )


@pytest.mark.skipif(not POSTGRES_URL, reason="PHARMACY_POSTGRES_URL is not configured")
def test_the_seeding_statement_actually_executes() -> None:
    """The defect, proven fixed against a real database rather than by reading.

    The guard above is a syntax check; it cannot show that the corrected
    statement runs. This inserts through the exact shape ``_sync_to_db`` uses
    and rolls back, so it leaves nothing behind.
    """
    assert POSTGRES_URL is not None
    engine = create_engine(POSTGRES_URL, future=True)
    statement = text(
        "INSERT INTO ai_model_registry (name, provider, model_type, version, "
        "capabilities, config, is_active, max_tokens) "
        "VALUES (:name, :p, :mt, :v, CAST(:caps AS jsonb), CAST(:cfg AS jsonb), "
        ":active, :mtok) RETURNING id"
    )
    with Session(engine) as session:
        row = session.execute(
            statement,
            {
                "name": "regression-probe",
                "p": "test",
                "mt": "chat",
                "v": "1.0",
                "caps": json.dumps(["chat"]),
                "cfg": json.dumps({"temperature": 0.5}),
                "active": 1,
                "mtok": 8192,
            },
        ).fetchone()
        assert row is not None and row[0] > 0
        stored = session.execute(
            text("SELECT capabilities, config FROM ai_model_registry WHERE id = :i"),
            {"i": row[0]},
        ).fetchone()
        assert stored is not None
        # Bound and cast, not stored as a quoted string.
        assert stored[0] == ["chat"]
        assert stored[1] == {"temperature": 0.5}
        session.rollback()


@pytest.mark.skipif(not POSTGRES_URL, reason="PHARMACY_POSTGRES_URL is not configured")
def test_the_original_syntax_still_fails() -> None:
    """Proves the guard protects against something real.

    Without this, a test suite that only exercises the corrected form cannot
    show the original form was broken at all.
    """
    assert POSTGRES_URL is not None
    engine = create_engine(POSTGRES_URL, future=True)
    with Session(engine) as session, pytest.raises(Exception) as caught:
        session.execute(
            text("SELECT CAST('[]' AS jsonb) @> :caps::jsonb"),
            {"caps": json.dumps([])},
        )
    assert "caps" in str(caught.value) or "syntax" in str(caught.value).lower()
