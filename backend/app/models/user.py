from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, relationship

from app._compat import UTC

from ..database import Base

if TYPE_CHECKING:
    from .authorization import RoleAssignment
    from .lab import Lab
    from .organization import Organization


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(100), unique=True, nullable=True, index=True)
    phone = Column(String(20), unique=True, nullable=True, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(200), nullable=False)
    role = Column(String(50), nullable=False, default="citizen")
    lab_id = Column(Integer, ForeignKey("labs.id", ondelete="SET NULL"), nullable=True)
    user_type = Column(String(50), nullable=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True, index=True)
    facility_id = Column(Integer, ForeignKey("facilities.id", ondelete="SET NULL"), nullable=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="SET NULL"), nullable=True, index=True)
    governorate_id = Column(String(50), nullable=True, index=True)
    directorate_id = Column(String(50), nullable=True, index=True)
    department_id = Column(String(100), nullable=True)
    specialty = Column(String(200), nullable=True)
    license_number = Column(String(100), nullable=True)
    national_id_hash = Column(String(255), nullable=True, index=True)
    is_active = Column(Boolean, default=True)
    failed_login_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(DateTime(timezone=True), nullable=True)
    is_verified = Column(Boolean, default=False)
    mfa_enabled = Column(Boolean, default=False)
    perm_version = Column(Integer, default=1)
    preferences = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    last_login = Column(DateTime(timezone=True), nullable=True)

    lab: Mapped[Lab | None] = relationship("Lab", backref="staff_users")
    organization: Mapped[Organization | None] = relationship(
        "Organization", backref="users", foreign_keys=[organization_id]
    )
    role_assignments: Mapped[list[RoleAssignment]] = relationship(
        "RoleAssignment", backref="user", foreign_keys="RoleAssignment.user_id"
    )
