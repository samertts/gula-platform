from sqlalchemy import Boolean, Column, ForeignKey, Index, String

from app.national.base import AuditEntity


class Department(AuditEntity):
    __tablename__ = "national_departments"

    name = Column(String(200), nullable=False)
    name_ar = Column(String(200), nullable=True)
    code = Column(String(20), nullable=True, index=True)

    facility_id = Column(
        String(26),
        ForeignKey("national_facilities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    parent_department_id = Column(String(26), nullable=True, index=True)

    department_type = Column(String(50), nullable=True)
    phone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)

    head_of_department = Column(String(200), nullable=True)
    is_active = Column(Boolean, default=True)

    __table_args__ = (
        Index("ix_national_departments_facility", "facility_id"),
        Index("ix_national_departments_parent", "parent_department_id"),
        {"extend_existing": True},
    )
