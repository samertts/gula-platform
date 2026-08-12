from __future__ import annotations

from sqlalchemy import BigInteger, Column, DateTime, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON

from app.health_data.base import HealthDataEntity
from app.health_data.enums import DataClassification


class ResearchProject(HealthDataEntity):
    __tablename__ = "rp_research_projects"

    title = Column(String(500), nullable=False)
    title_ar = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)
    study_type = Column(String(50), nullable=True)
    status = Column(String(30), default="draft")
    institution_id = Column(String(26), nullable=True, index=True)
    principal_investigator = Column(String(300), nullable=True)
    ethics_approval_id = Column(String(100), nullable=True)
    approval_date = Column(DateTime(timezone=True), nullable=True)
    start_date = Column(DateTime(timezone=True), nullable=True)
    end_date = Column(DateTime(timezone=True), nullable=True)
    population_size = Column(Integer, nullable=True)
    inclusion_criteria = Column(JSON, default=dict)
    exclusion_criteria = Column(JSON, default=dict)
    data_classification = Column(String(30), default=DataClassification.CONFIDENTIAL.value)
    consent_required = Column(Integer, default=1)
    data_sources = Column(JSON, default=list)
    collaborators = Column(JSON, default=list)
    funding_source = Column(String(300), nullable=True)
    metadata_json = Column(JSON, default=dict)


class ResearchDataset(HealthDataEntity):
    __tablename__ = "rp_research_datasets"

    project_id = Column(String(26), nullable=False, index=True)
    name = Column(String(300), nullable=False)
    name_ar = Column(String(300), nullable=True)
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=True, index=True)
    schema_definition = Column(JSON, default=dict)
    record_count = Column(Integer, default=0)
    size_bytes = Column(BigInteger, default=0)
    data_lake_dataset = Column(String(200), nullable=True)
    source_systems = Column(JSON, default=list)
    de_identified = Column(Integer, default=0)
    pseudonymized = Column(Integer, default=0)
    differential_privacy = Column(Integer, default=0)
    privacy_budget = Column(Float, nullable=True)
    retention_days = Column(Integer, default=365)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    checksum = Column(String(64), nullable=True)
    version = Column(String(20), default="1.0.0")
    metadata_json = Column(JSON, default=dict)


class ResearchInstitution(HealthDataEntity):
    __tablename__ = "rp_research_institutions"

    name = Column(String(300), nullable=False)
    name_ar = Column(String(300), nullable=True)
    institution_type = Column(String(50), nullable=True)
    country = Column(String(100), default="Iraq")
    city = Column(String(100), nullable=True)
    governorate = Column(String(100), nullable=True)
    website = Column(String(200), nullable=True)
    contact_email = Column(String(200), nullable=True)
    contact_phone = Column(String(50), nullable=True)
    is_active = Column(Integer, default=1)
    accreditation = Column(JSON, default=list)
    metadata_json = Column(JSON, default=dict)


class ResearchPublication(HealthDataEntity):
    __tablename__ = "rp_research_publications"

    project_id = Column(String(26), nullable=True, index=True)
    title = Column(String(500), nullable=False)
    title_ar = Column(String(500), nullable=True)
    authors = Column(JSON, default=list)
    journal = Column(String(300), nullable=True)
    doi = Column(String(100), nullable=True, unique=True)
    pmid = Column(String(20), nullable=True)
    publication_date = Column(DateTime(timezone=True), nullable=True)
    publication_type = Column(String(50), nullable=True)
    abstract = Column(Text, nullable=True)
    keywords = Column(JSON, default=list)
    citation_count = Column(Integer, default=0)
    url = Column(String(500), nullable=True)
    metadata_json = Column(JSON, default=dict)


class StudyCohort(HealthDataEntity):
    __tablename__ = "rp_study_cohorts"

    project_id = Column(String(26), nullable=False, index=True)
    name = Column(String(300), nullable=False)
    description = Column(Text, nullable=True)
    inclusion_criteria = Column(JSON, default=dict)
    exclusion_criteria = Column(JSON, default=dict)
    sample_size = Column(Integer, default=0)
    patient_ulids = Column(JSON, default=list)
    demographics = Column(JSON, default=dict)
    metadata_json = Column(JSON, default=dict)


class DataAccessRequest(HealthDataEntity):
    __tablename__ = "rp_data_access_requests"

    project_id = Column(String(26), nullable=False, index=True)
    requester_name = Column(String(300), nullable=False)
    requester_email = Column(String(200), nullable=True)
    research_purpose = Column(Text, nullable=True)
    datasets_requested = Column(JSON, default=list)
    access_level = Column(String(30), default="de_identified")
    status = Column(String(30), default="pending")
    reviewed_by = Column(String(100), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    approval_notes = Column(Text, nullable=True)
    consent_confirmed = Column(Integer, default=0)
    ethics_approval_ref = Column(String(100), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    metadata_json = Column(JSON, default=dict)


class ConsentRecord(HealthDataEntity):
    __tablename__ = "rp_consent_records"

    patient_ulid = Column(String(26), nullable=False, index=True)
    project_id = Column(String(26), nullable=False, index=True)
    consent_type = Column(String(30), default="research")
    status = Column(String(20), default="granted")
    granted_at = Column(DateTime(timezone=True), nullable=True)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    scope = Column(JSON, default=list)
    metadata_json = Column(JSON, default=dict)
