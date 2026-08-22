from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, relationship

from app._compat import UTC

from ..database import Base

if TYPE_CHECKING:
    from .organization import Organization


class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(100), unique=True, nullable=False, index=True)
    name_en = Column(String(200), nullable=False)
    name_ar = Column(String(200), nullable=False)
    domain = Column(String(200), nullable=True, unique=True)
    tenant_type = Column(String(50), nullable=False, default="governorate")
    parent_tenant_id = Column(Integer, nullable=True, index=True)
    phone = Column(String(30), nullable=True)
    address = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    max_users = Column(Integer, nullable=True)
    feature_flags = Column(JSON, nullable=True)
    settings = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    organizations: Mapped[list[Organization]] = relationship("Organization", backref="tenant")
