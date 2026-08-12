"""Shared declarative base for all NHOP ORM models.

We re-export the declarative base from ``app.core.database`` so that models
defined via ``app.models.base.Base`` share a single ``MetaData`` with models
defined via ``app.core.database.Base``. Cross-metadata foreign keys cannot
be resolved at ``create_all`` time, so a single shared metadata is required.
"""
from ..core.database import Base

__all__ = ["Base"]
