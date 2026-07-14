from app.national.reference.base import ReferenceEntity
from sqlalchemy import Column, String


class ICD11Code(ReferenceEntity):
    __tablename__ = "ref_icd11_codes"
    icd11_id = Column(String(20), nullable=False, unique=True, index=True)
    chapter = Column(String(10), nullable=True)
    chapter_name = Column(String(200), nullable=True)
    parent_id = Column(String(20), nullable=True)
    who_status = Column(String(20), nullable=True)
