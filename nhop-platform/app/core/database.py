"""SQLAlchemy engine / session for nhop-platform.

The NHOP registry uses its own logical database (the citizen view), separate
from the per-lab GULA schema. In production this points at a Postgres DSN;
in tests it defaults to an in-memory SQLite URL for fast unit runs.
"""
import os
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


DATABASE_URL = os.getenv("NHOP_DATABASE_URL", "sqlite:///./nhop.db")

_connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, future=True, connect_args=_connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


class Base(DeclarativeBase):
    """Declarative base for all nhop-platform ORM models."""


def get_db() -> Iterator[Session]:
    """FastAPI dependency yielding a request-scoped SQLAlchemy session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
