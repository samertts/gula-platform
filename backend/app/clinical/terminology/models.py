from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app._compat import UTC
from app.clinical.base import BaseEntity
from app.clinical.enums import TerminologyStatus, TerminologySystem


class TerminologyCode(BaseEntity):
    __tablename__ = "clinical_terminology_codes"
    __table_args__ = (
        Index("ix_terminology_code_system_code", "system", "code"),
        Index("ix_terminology_code_parent", "parent_id"),
    )

    code = Column(String(64), nullable=False, index=True)
    display = Column(String(512), nullable=False)
    system = Column(Enum(TerminologySystem), nullable=False)
    version_id = Column(String(26), ForeignKey("clinical_terminology_versions.id", ondelete="SET NULL"), nullable=True)
    parent_id = Column(String(26), ForeignKey("clinical_terminology_codes.id"), nullable=True)
    definition = Column(Text, nullable=True)
    is_leaf = Column(Boolean, default=True, nullable=False)
    effective_date = Column(Date, nullable=True)
    status = Column(Enum(TerminologyStatus), default=TerminologyStatus.ACTIVE, nullable=False)

    version = relationship("TerminologyVersion", back_populates="codes", foreign_keys=[version_id])
    parent = relationship("TerminologyCode", remote_side="TerminologyCode.id", backref="children")
    mappings_source = relationship("TerminologyMapping", foreign_keys="TerminologyMapping.source_code_id", back_populates="source_code")
    mappings_target = relationship("TerminologyMapping", foreign_keys="TerminologyMapping.target_code_id", back_populates="target_code")


class TerminologyVersion(BaseEntity):
    __tablename__ = "clinical_terminology_versions"
    __table_args__ = (
        Index("ix_terminology_version_system_version", "system", "version"),
    )

    system = Column(Enum(TerminologySystem), nullable=False)
    version = Column(String(64), nullable=False)
    release_date = Column(Date, nullable=True)
    description = Column(Text, nullable=True)
    is_current = Column(Boolean, default=False, nullable=False)
    codes_count = Column(Integer, default=0, nullable=False)
    imported_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)

    codes = relationship("TerminologyCode", back_populates="version", foreign_keys="TerminologyCode.version_id")


class TerminologyMapping(BaseEntity):
    __tablename__ = "clinical_terminology_mappings"
    __table_args__ = (
        Index("ix_terminology_mapping_source", "source_system", "source_code_id"),
        Index("ix_terminology_mapping_target", "target_system", "target_code_id"),
    )

    source_system = Column(Enum(TerminologySystem), nullable=False)
    source_code_id = Column(String(26), ForeignKey("clinical_terminology_codes.id"), nullable=False)
    target_system = Column(Enum(TerminologySystem), nullable=False)
    target_code_id = Column(String(26), ForeignKey("clinical_terminology_codes.id"), nullable=False)
    mapping_relationship = Column(String(32), default="equivalent", nullable=False)
    mapping_priority = Column(Integer, default=0, nullable=False)
    evidence = Column(Text, nullable=True)

    source_code = relationship("TerminologyCode", foreign_keys=[source_code_id], back_populates="mappings_source")
    target_code = relationship("TerminologyCode", foreign_keys=[target_code_id], back_populates="mappings_target")


class ValueSet(BaseEntity):
    __tablename__ = "clinical_value_sets"
    __table_args__ = (
        Index("ix_value_set_oid", "oid"),
    )

    name = Column(String(256), nullable=False)
    oid = Column(String(64), nullable=True, unique=True)
    description = Column(Text, nullable=True)
    purpose = Column(Text, nullable=True)
    is_extensible = Column(Boolean, default=True, nullable=False)
    is_experimental = Column(Boolean, default=False, nullable=False)
    steward = Column(String(128), nullable=True)
    source = Column(Enum(TerminologySystem), nullable=True)
    version = Column(String(64), nullable=True)
    effective_start = Column(Date, nullable=True)
    effective_end = Column(Date, nullable=True)

    members = relationship("ValueSetMember", back_populates="value_set", cascade="all, delete-orphan")


class ValueSetMember(BaseEntity):
    __tablename__ = "clinical_value_set_members"
    __table_args__ = (
        Index("ix_value_set_member_vs_code", "value_set_id", "code_id"),
    )

    value_set_id = Column(String(26), ForeignKey("clinical_value_sets.id", ondelete="CASCADE"), nullable=False)
    code_id = Column(String(26), ForeignKey("clinical_terminology_codes.id"), nullable=False)
    inclusion = Column(Boolean, default=True, nullable=False)
    order = Column(Integer, default=0, nullable=False)

    value_set = relationship("ValueSet", back_populates="members")
    code = relationship("TerminologyCode")


class CodeSystem(BaseEntity):
    __tablename__ = "clinical_code_systems"
    __table_args__ = (
        Index("ix_code_system_name", "name"),
    )

    name = Column(String(128), nullable=False)
    system = Column(Enum(TerminologySystem), nullable=False)
    uri = Column(String(512), nullable=True)
    oid = Column(String(64), nullable=True)
    description = Column(Text, nullable=True)
    publisher = Column(String(256), nullable=True)
    contact = Column(String(256), nullable=True)
    copyright = Column(Text, nullable=True)
    version = Column(String(64), nullable=True)
    total_codes = Column(Integer, default=0, nullable=False)
    is_case_sensitive = Column(Boolean, default=True, nullable=False)
    hierarchy_meaning = Column(String(32), nullable=True)


class ICD10Code(BaseEntity):
    __tablename__ = "clinical_icd10_codes"
    __table_args__ = (
        Index("ix_icd10_chapter", "chapter"),
        Index("ix_icd10_block", "block"),
    )

    code = Column(String(16), nullable=False, unique=True, index=True)
    short_description = Column(String(256), nullable=False)
    long_description = Column(Text, nullable=True)
    chapter = Column(String(8), nullable=True)
    chapter_description = Column(String(256), nullable=True)
    block = Column(String(16), nullable=True)
    block_description = Column(String(256), nullable=True)
    category = Column(String(8), nullable=True)
    is_billable = Column(Boolean, default=False, nullable=False)
    is_principal_diagnosis = Column(Boolean, default=True, nullable=False)
    sex_specific = Column(String(1), nullable=True)
    manifestation_code = Column(Boolean, default=False, nullable=False)
    valid_from = Column(Date, nullable=True)
    valid_until = Column(Date, nullable=True)


class ICD11Code(BaseEntity):
    __tablename__ = "clinical_icd11_codes"
    __table_args__ = (
        Index("ix_icd11_chapter", "chapter"),
    )

    code = Column(String(32), nullable=False, unique=True, index=True)
    title = Column(String(512), nullable=False)
    definition = Column(Text, nullable=True)
    chapter = Column(String(8), nullable=True)
    chapter_title = Column(String(256), nullable=True)
    block = Column(String(32), nullable=True)
    is_leaf = Column(Boolean, default=True, nullable=False)
    parent_code = Column(String(32), nullable=True)
    coding_note = Column(Text, nullable=True)
    post_coordination = Column(Text, nullable=True)
    valid_from = Column(Date, nullable=True)


class SNOMEDCTCode(BaseEntity):
    __tablename__ = "clinical_snomed_ct_codes"
    __table_args__ = (
        Index("ix_snomed_concept_id", "concept_id"),
    )

    concept_id = Column(String(64), nullable=False, unique=True, index=True)
    fully_specified_name = Column(String(512), nullable=False)
    preferred_term = Column(String(512), nullable=True)
    definition_status = Column(String(32), nullable=True)
    module_id = Column(String(64), nullable=True)
    effective_time = Column(String(16), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    semantic_tag = Column(String(128), nullable=True)


class LOINCCode(BaseEntity):
    __tablename__ = "clinical_loinc_codes"
    __table_args__ = (
        Index("ix_loinc_class", "class_name"),
        Index("ix_loinc_component", "component"),
    )

    loinc_num = Column(String(16), nullable=False, unique=True, index=True)
    component = Column(String(512), nullable=True)
    property = Column(String(64), nullable=True)
    timing = Column(String(64), nullable=True)
    system = Column(String(128), nullable=True)
    scale = Column(String(32), nullable=True)
    method = Column(String(256), nullable=True)
    class_name = Column(String(128), nullable=True)
    version_last_changed = Column(String(16), nullable=True)
    definition_description = Column(Text, nullable=True)
    status = Column(String(16), nullable=True)
    consumer_name = Column(String(512), nullable=True)
    example_units = Column(String(256), nullable=True)
    related_names = Column(Text, nullable=True)
    short_name = Column(String(64), nullable=True)
    long_common_name = Column(String(512), nullable=True)


class UCUMCode(BaseEntity):
    __tablename__ = "clinical_ucum_codes"

    code = Column(String(32), nullable=False, unique=True, index=True)
    name = Column(String(128), nullable=True)
    description = Column(Text, nullable=True)
    property = Column(String(64), nullable=True)
    is_metric = Column(Boolean, default=False, nullable=False)
    is_si = Column(Boolean, default=False, nullable=False)
    conversion_factor = Column(String(64), nullable=True)


class ATCCode(BaseEntity):
    __tablename__ = "clinical_atc_codes"
    __table_args__ = (
        Index("ix_atc_level", "level"),
    )

    code = Column(String(16), nullable=False, unique=True, index=True)
    name = Column(String(512), nullable=False)
    level = Column(Integer, nullable=False)
    parent_code = Column(String(16), nullable=True)
    ddd_value = Column(String(32), nullable=True)
    ddd_unit = Column(String(32), nullable=True)
    anatomical_group = Column(String(256), nullable=True)
    therapeutic_group = Column(String(256), nullable=True)


class RxNormCode(BaseEntity):
    __tablename__ = "clinical_rxnorm_codes"

    rxcui = Column(String(16), nullable=False, unique=True, index=True)
    name = Column(String(512), nullable=False)
    synonym = Column(String(512), nullable=True)
    tty = Column(String(16), nullable=True)
    language = Column(String(8), default="en", nullable=False)
    suppress = Column(String(1), nullable=True)
    umlscui = Column(String(16), nullable=True)
    atom_id = Column(String(32), nullable=True)


class CPTCode(BaseEntity):
    __tablename__ = "clinical_cpt_codes"
    __table_args__ = (
        Index("ix_cpt_category", "category"),
    )

    code = Column(String(16), nullable=False, unique=True, index=True)
    short_description = Column(String(256), nullable=False)
    medium_description = Column(String(512), nullable=True)
    long_description = Column(Text, nullable=True)
    category = Column(String(8), nullable=True)
    category_description = Column(String(256), nullable=True)
    section = Column(String(8), nullable=True)
    is_imaging = Column(Boolean, default=False, nullable=False)
    is_lab = Column(Boolean, default=False, nullable=False)
    is_surgical = Column(Boolean, default=False, nullable=False)
    effective_date = Column(Date, nullable=True)
    status = Column(String(16), default="active", nullable=False)
