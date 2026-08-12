from sqlalchemy import Boolean, Column, Integer, String, Text

from app.national_data.base import BaseEntity


class TerminologyRegistry(BaseEntity):
    __tablename__ = "dp_terminology_registry"

    system_name = Column(String(100), nullable=False)
    system_code = Column(String(20), nullable=False, unique=True, index=True)
    system_uri = Column(String(500), nullable=True)
    oid = Column(String(64), nullable=True, unique=True)

    version = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    publisher = Column(String(200), nullable=True)

    total_codes = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_case_sensitive = Column(Boolean, default=True, nullable=False)
    hierarchy_type = Column(String(20), nullable=True)

    release_date = Column(String(50), nullable=True)
    license = Column(String(200), nullable=True)
    usage_notes = Column(Text, nullable=True)

    __table_args__ = {"extend_existing": True}
