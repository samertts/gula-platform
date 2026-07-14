from app.national.reference.base import ReferenceEntity
from sqlalchemy import Column, String


class Language(ReferenceEntity):
    __tablename__ = "ref_languages"
    iso639_1 = Column(String(2), nullable=False)
    iso639_2 = Column(String(3), nullable=True)
    native_name = Column(String(100), nullable=True)
    is_rtl = Column(String(1), default="0")
