from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, String, Text

from app._compat import UTC, StrEnum
from app.identity.base import IdentityBaseEntity


class AssignmentStatus(StrEnum):
    active = "active"
    completed = "completed"
    cancelled = "cancelled"
    expired = "expired"


class Assignment(IdentityBaseEntity):
    __tablename__ = "niam_assignments"

    uuid = Column(String(36), unique=True, nullable=False, index=True)
    employment_id = Column(String(26), ForeignKey("niam_employments.id", ondelete="CASCADE"), nullable=False, index=True)
    person_id = Column(String(26), ForeignKey("niam_persons.id", ondelete="CASCADE"), nullable=False, index=True)

    organization_id = Column(String(26), ForeignKey("niam_organizations.id", ondelete="SET NULL"), nullable=True, index=True)
    facility_id = Column(String(26), nullable=True, index=True)
    # These resource references are deliberately separate from the legacy NIAM
    # text identifiers above. Clinical authorization never infers a facility
    # from a legacy value; it needs an explicit, FK-backed operational scope.
    clinical_organization_resource_id = Column(
        Integer,
        ForeignKey("organizations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    clinical_facility_resource_id = Column(
        Integer,
        ForeignKey("facilities.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    department_id = Column(String(26), nullable=True, index=True)
    unit = Column(String(200), nullable=True)
    committee = Column(String(200), nullable=True)
    task_force = Column(String(200), nullable=True)

    role_id = Column(String(100), nullable=False, index=True)
    assignment_type = Column(String(50), nullable=False)

    is_primary = Column(Boolean, default=False, nullable=False)
    status = Column(String(20), default="active", nullable=False, index=True)

    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    expected_end_date = Column(Date, nullable=True)

    is_temporary = Column(Boolean, default=False, nullable=False)
    is_emergency = Column(Boolean, default=False, nullable=False)
    is_delegated = Column(Boolean, default=False, nullable=False)

    delegated_from = Column(String(26), ForeignKey("niam_assignments.id", ondelete="SET NULL"), nullable=True)
    delegated_by = Column(String(26), ForeignKey("niam_persons.id", ondelete="SET NULL"), nullable=True)

    max_duration_hours = Column(Integer, nullable=True)
    requires_mfa = Column(Boolean, default=False, nullable=False)

    assigned_by = Column(String(26), ForeignKey("niam_persons.id", ondelete="SET NULL"), nullable=True)
    assigned_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)

    notes = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
