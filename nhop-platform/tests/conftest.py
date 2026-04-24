"""Shared pytest fixtures for the nhop-platform unit tests.

The default engine points at a file SQLite DB; tests bind to an in-memory
database so runs are fully isolated and don't touch the developer's dev file.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Make the nhop-platform package importable regardless of where pytest is run.
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

os.environ.setdefault("NHOP_DATABASE_URL", "sqlite:///:memory:")


@pytest.fixture()
def db_session():
    from app.core.database import Base
    # Import models so their tables register on Base.metadata before create_all.
    from app.models import audit_log, citizen, lab_test  # noqa: F401
    from app.models import antibiotic_sensitivity, disease_case  # noqa: F401

    engine = create_engine(
        "sqlite:///:memory:",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    session = Session()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()
