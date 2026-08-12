from sqlalchemy import Boolean, Column, Date, ForeignKey, Index, String
from sqlalchemy import Enum as SAEnum

from app.national.base import AuditEntity
from app.national.enums import Gender


class Employee(AuditEntity):
    __tablename__ = "national_employees"

    employee_code = Column(String(50), nullable=False, unique=True, index=True)
    full_name = Column(String(200), nullable=False)
    full_name_ar = Column(String(200), nullable=True)

    date_of_birth = Column(Date, nullable=True)
    gender = Column(SAEnum(Gender), nullable=True)
    nationality = Column(String(100), default="Iraqi")

    national_id_hash = Column(String(255), nullable=True)
    phone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)

    organization_id = Column(String(26), ForeignKey("national_organizations.id", ondelete="RESTRICT"), nullable=False, index=True)
    facility_id = Column(String(26), ForeignKey("national_facilities.id", ondelete="RESTRICT"), nullable=True, index=True)
    department_id = Column(String(26), ForeignKey("national_departments.id", ondelete="RESTRICT"), nullable=True, index=True)

    job_title = Column(String(200), nullable=True)
    job_type = Column(String(50), nullable=True)
    department = Column(String(200), nullable=True)

    hire_date = Column(Date, nullable=True)
    is_active = Column(Boolean, default=True)
    is_healthcare_worker = Column(Boolean, default=False)

    emergency_contact_name = Column(String(200), nullable=True)
    emergency_contact_phone = Column(String(20), nullable=True)

    __table_args__ = (
        Index("ix_national_employees_org", "organization_id"),
        Index("ix_national_employees_facility", "facility_id"),
        Index("ix_national_employees_department", "department_id"),
        {"extend_existing": True},
    )
