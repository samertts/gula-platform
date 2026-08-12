from __future__ import annotations

from sqlalchemy import JSON, Boolean, Column, Float, ForeignKey, Index, String, Text
from sqlalchemy import Enum as SAEnum

from app.health_data.base import TenantAuditHealthDataEntity
from app.health_data.enums import DataQuality


class SourceReference(TenantAuditHealthDataEntity):
    __tablename__ = "hd_mdm_source_references"

    golden_record_id = Column(String(26), ForeignKey("hd_mdm_patient_index.id", ondelete="CASCADE"), nullable=False, index=True)
    source_system = Column(String(64), nullable=False)
    source_id = Column(String(128), nullable=False)
    source_url = Column(String(512), nullable=True)
    confidence = Column(Float, default=1.0)
    is_primary = Column(Boolean, default=False)
    raw_data = Column(JSON, nullable=True)

    __table_args__ = (
        Index("ix_hd_mdm_src_system", "source_system", "source_id", unique=True),
        {"extend_existing": True},
    )


class MasterPatientIndex(TenantAuditHealthDataEntity):
    __tablename__ = "hd_mdm_patient_index"

    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    full_name = Column(String(400), nullable=True)
    date_of_birth = Column(String(10), nullable=True)
    gender = Column(String(10), nullable=True)
    phone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)
    national_id_hash = Column(String(255), nullable=True)
    health_number = Column(String(20), nullable=True)

    address_line = Column(String(500), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    country = Column(String(100), default="IQ")

    confidence_score = Column(Float, default=0.0)
    quality = Column(SAEnum(DataQuality), default=DataQuality.MASTER)
    is_golden = Column(Boolean, default=True)
    merged_into_id = Column(String(26), nullable=True, index=True)
    merge_reason = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)

    source_systems = Column(JSON, default=list)
    tags = Column(JSON, nullable=True)
    extension = Column(JSON, nullable=True)

    __table_args__ = (
        Index("ix_hd_mdm_patient_name", "last_name", "first_name"),
        Index("ix_hd_mdm_patient_nid", "national_id_hash"),
        Index("ix_hd_mdm_patient_health_number", "health_number"),
        Index("ix_hd_mdm_patient_merged", "merged_into_id"),
        Index("ix_hd_mdm_patient_active", "is_active"),
        {"extend_existing": True},
    )


class MasterProviderIndex(TenantAuditHealthDataEntity):
    __tablename__ = "hd_mdm_provider_index"

    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    full_name = Column(String(400), nullable=True)
    specialty = Column(String(200), nullable=True)
    license_number = Column(String(50), nullable=True)
    national_id_hash = Column(String(255), nullable=True)
    phone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)

    confidence_score = Column(Float, default=0.0)
    quality = Column(SAEnum(DataQuality), default=DataQuality.MASTER)
    is_golden = Column(Boolean, default=True)
    merged_into_id = Column(String(26), nullable=True, index=True)
    is_active = Column(Boolean, default=True)

    source_systems = Column(JSON, default=list)
    extension = Column(JSON, nullable=True)

    __table_args__ = (
        Index("ix_hd_mdm_provider_name", "last_name", "first_name"),
        Index("ix_hd_mdm_provider_license", "license_number"),
        {"extend_existing": True},
    )


class MasterOrganizationIndex(TenantAuditHealthDataEntity):
    __tablename__ = "hd_mdm_organization_index"

    name = Column(String(300), nullable=False)
    name_ar = Column(String(300), nullable=True)
    organization_type = Column(String(50), nullable=True)
    tax_id = Column(String(50), nullable=True)
    registration_number = Column(String(50), nullable=True)
    phone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)
    website = Column(String(255), nullable=True)

    address_line = Column(String(500), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    country = Column(String(100), default="IQ")

    confidence_score = Column(Float, default=0.0)
    quality = Column(SAEnum(DataQuality), default=DataQuality.MASTER)
    is_golden = Column(Boolean, default=True)
    merged_into_id = Column(String(26), nullable=True, index=True)
    is_active = Column(Boolean, default=True)

    source_systems = Column(JSON, default=list)
    extension = Column(JSON, nullable=True)

    __table_args__ = (
        Index("ix_hd_mdm_org_name", "name"),
        Index("ix_hd_mdm_org_registration", "registration_number"),
        {"extend_existing": True},
    )


class MasterFacilityIndex(TenantAuditHealthDataEntity):
    __tablename__ = "hd_mdm_facility_index"

    name = Column(String(300), nullable=False)
    name_ar = Column(String(300), nullable=True)
    facility_type = Column(String(50), nullable=True)
    facility_code = Column(String(50), nullable=True)
    organization_id = Column(String(26), nullable=True, index=True)
    phone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)

    address_line = Column(String(500), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    country = Column(String(100), default="IQ")
    coordinates = Column(JSON, nullable=True)

    confidence_score = Column(Float, default=0.0)
    quality = Column(SAEnum(DataQuality), default=DataQuality.MASTER)
    is_golden = Column(Boolean, default=True)
    merged_into_id = Column(String(26), nullable=True, index=True)
    is_active = Column(Boolean, default=True)

    source_systems = Column(JSON, default=list)
    extension = Column(JSON, nullable=True)

    __table_args__ = (
        Index("ix_hd_mdm_facility_name", "name"),
        Index("ix_hd_mdm_facility_code", "facility_code"),
        {"extend_existing": True},
    )
