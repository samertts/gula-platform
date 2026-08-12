from __future__ import annotations

from sqlalchemy import Boolean, Column, Date, ForeignKey, String, Text

from app._compat import StrEnum
from app.identity.base import IdentityBaseEntity


class EmploymentStatus(StrEnum):
    active = "active"
    on_leave = "on_leave"
    suspended = "suspended"
    terminated = "terminated"
    retired = "retired"
    transferred = "transferred"


class Employment(IdentityBaseEntity):
    __tablename__ = "niam_employments"

    uuid = Column(String(36), unique=True, nullable=False, index=True)
    person_id = Column(String(26), ForeignKey("niam_persons.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id = Column(String(26), ForeignKey("niam_organizations.id", ondelete="CASCADE"), nullable=False, index=True)

    employee_id = Column(String(50), nullable=True, index=True)
    employment_type = Column(String(50), nullable=False)
    status = Column(String(20), default="active", nullable=False, index=True)

    position = Column(String(200), nullable=False)
    department = Column(String(200), nullable=True)
    title = Column(String(200), nullable=True)

    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)

    contract_type = Column(String(50), nullable=True)
    contract_end_date = Column(Date, nullable=True)

    supervisor_person_id = Column(String(26), ForeignKey("niam_persons.id", ondelete="SET NULL"), nullable=True)

    is_primary_employment = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    termination_reason = Column(Text, nullable=True)
    termination_date = Column(Date, nullable=True)

    transfer_from_employment = Column(String(26), ForeignKey("niam_employments.id", ondelete="SET NULL"), nullable=True)
    transfer_to_organization = Column(String(26), ForeignKey("niam_organizations.id", ondelete="SET NULL"), nullable=True)
    transfer_date = Column(Date, nullable=True)

    notes = Column(Text, nullable=True)
