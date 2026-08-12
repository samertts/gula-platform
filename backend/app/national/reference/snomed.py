from sqlalchemy import Column, String, Text

from app.national.reference.base import ReferenceEntity


class SNOMEDConcept(ReferenceEntity):
    __tablename__ = "ref_snomed_concepts"
    concept_id = Column(String(20), nullable=False, unique=True, index=True)
    fully_specified_name = Column(Text, nullable=True)
    concept_status = Column(String(50), nullable=True)
    semantic_tag = Column(String(100), nullable=True)
    parent_ids = Column(Text, nullable=True)
