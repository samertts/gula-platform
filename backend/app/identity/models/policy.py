from __future__ import annotations

from sqlalchemy import JSON, Boolean, Column, DateTime, Integer, String, Text

from app.identity.base import IdentityBaseEntity


class IdentityPolicy(IdentityBaseEntity):
    __tablename__ = "niam_policies"

    uuid = Column(String(36), unique=True, nullable=False, index=True)
    policy_id = Column(String(100), unique=True, nullable=False, index=True)

    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    policy_type = Column(String(50), nullable=False, index=True)
    category = Column(String(50), nullable=True, index=True)

    effect = Column(String(10), nullable=False)
    actions = Column(JSON, nullable=False)
    resources = Column(JSON, nullable=False)
    subjects = Column(JSON, nullable=True)
    conditions = Column(JSON, nullable=True)

    priority = Column(Integer, default=0, nullable=False)
    version = Column(String(20), default="1.0", nullable=False)

    applies_to_org_types = Column(JSON, nullable=True)

    start_at = Column(DateTime(timezone=True), nullable=True)
    end_at = Column(DateTime(timezone=True), nullable=True)

    created_by = Column(String(100), nullable=False)
    approved_by = Column(String(100), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)

    is_enabled = Column(Boolean, default=True, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    tags = Column(JSON, nullable=True)
