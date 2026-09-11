from datetime import datetime

from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app._compat import UTC

from ..database import Base


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    # NR-047: the physical columns are `organization_id` and
    # `organization_type`. This model was written in NIAMOrganization's
    # vocabulary — `org_id`/`org_type` are that model's names, and they never
    # existed here: `organizations` was created by
    # 20260722_0001_authorization_expansion with organization_id/
    # organization_type, a day *before* niam_organizations introduced the other
    # spelling. Mapping the Python attribute onto the real column keeps every
    # caller (all of app/core/bootstrap/) unchanged while the SQL becomes valid.
    org_id = Column("organization_id", String(100), unique=True, nullable=False, index=True)
    name_en = Column(String(200), nullable=False)
    name_ar = Column(String(200), nullable=False)
    org_type = Column("organization_type", String(50), nullable=False, index=True)
    # A public-identifier reference to another organization's `organization_id`
    # — the Ministry of Health above the 18 governorate health directorates.
    # Deliberately NOT NIAMOrganization's integer self-FK of the same name: the
    # bootstrap contract (OrganizationDef.parent_org_id: str | None) is a string
    # key, and the matching names are a coincidence of the same drift.
    parent_org_id = Column(String(100), nullable=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="SET NULL"), nullable=True, index=True)
    governorate_id = Column(String(50), nullable=True, index=True)
    directorate_id = Column(String(50), nullable=True, index=True)
    is_active = Column(Boolean, default=True)
    contact_email = Column(String(200), nullable=True)
    contact_phone = Column(String(30), nullable=True)
    address = Column(Text, nullable=True)
    extra_metadata = Column("metadata", JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    # NR-047: `updated_at` is deliberately absent. It never existed on this
    # table and nothing reads, writes or serialises it — adding a column purely
    # to make the ORM and the schema look alike would be drift in the other
    # direction. NIAMOrganization has one because that model maintains it.


class Facility(Base):
    __tablename__ = "facilities"

    id = Column(Integer, primary_key=True, index=True)
    facility_id = Column(String(100), unique=True, nullable=False, index=True)
    name_en = Column(String(200), nullable=False)
    name_ar = Column(String(200), nullable=False)
    facility_type = Column(String(50), nullable=False, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    contact_email = Column(String(200), nullable=True)
    contact_phone = Column(String(30), nullable=True)
    address = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    organization = relationship("Organization", backref="facilities")
