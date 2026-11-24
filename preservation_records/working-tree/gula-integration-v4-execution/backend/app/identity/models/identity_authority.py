"""ORM mirror of the migrated ``niam_identity_authorities`` table.

Migration ``20261114_0001_unify_foundation.py`` creates this table because the
preserved professional registry, trust frameworks and trust proofing tables
reference it by foreign key. Before this model existed those three FKs (plus a
fourth mistyped FK in ``adaptive_auth``) pointed at tables absent from the ORM
metadata, so cross-metadata FK resolution failed whenever the route-only model
modules were imported first (e.g. when ``tests/identity`` was co-collected
with the NR-011 metadata-discovery test).

This module is imported from ``app.identity.models`` so both the application
factory and ``migrations/env.py`` register the table on ``IdentityBase``.
No migration is generated or applied by this change: the table already exists
in the migration chain. Data class: synthetic engineering metadata only.
"""

from __future__ import annotations

from sqlalchemy import Boolean, Column, String

from app.identity.base import IdentityBaseEntity


class IdentityAuthorityRecord(IdentityBaseEntity):
    """A national identity authority referenced by identity governance records.

    Column names/types mirror ``niam_identity_authorities`` in migration
    20261114_0001; ``id``, ``created_at`` and ``updated_at`` are inherited from
    ``IdentityBaseEntity``. Software records are NOT official licensing or
    government-authority evidence.
    """

    __tablename__ = "niam_identity_authorities"

    uuid = Column(String(36), unique=True, nullable=False, index=True)
    authority_id = Column(String(100), unique=True, nullable=False, index=True)

    name_en = Column(String(300), nullable=False)
    name_ar = Column(String(300), nullable=True)

    authority_type = Column(String(50), nullable=False, index=True)
    jurisdiction = Column(String(30), nullable=False)

    status = Column(String(20), nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
