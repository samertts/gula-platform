from sqlalchemy import Boolean, Column, ForeignKey, Index, String

from app.national.base import AuditEntity


class Directorate(AuditEntity):
    __tablename__ = "national_directorates"

    name = Column(String(200), nullable=False)
    name_ar = Column(String(200), nullable=True)
    code = Column(String(20), nullable=False, unique=True, index=True)

    organization_id = Column(
        String(26),
        ForeignKey("national_organizations.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    parent_directorate_id = Column(String(26), nullable=True, index=True)

    phone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)

    governorate = Column(String(100), nullable=False)
    address_line = Column(String(500), nullable=True)

    director_name = Column(String(200), nullable=True)
    is_active = Column(Boolean, default=True)

    __table_args__ = (
        Index("ix_national_directorates_org", "organization_id"),
        Index("ix_national_directorates_parent", "parent_directorate_id"),
        {"extend_existing": True},
    )
