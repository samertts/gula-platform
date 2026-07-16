from sqlalchemy import Column, Index, String, Text

from app.national.reference.base import ReferenceEntity


class FHIRTerminology(ReferenceEntity):
    __tablename__ = "ref_fhir_terminology"
    system = Column(String(500), nullable=False, index=True)
    version = Column(String(20), nullable=True)
    concept_code = Column(String(100), nullable=False)
    display = Column(String(500), nullable=True)
    definition = Column(Text, nullable=True)
    designation = Column(Text, nullable=True)
    parent_code = Column(String(100), nullable=True)

    __table_args__ = (
        Index("ix_ref_fhir_terminology_system_code", "system", "concept_code", unique=True),
    )
