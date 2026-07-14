from app.national.reference.base import ReferenceEntity
from sqlalchemy import Column, String


class Profession(ReferenceEntity):
    __tablename__ = "ref_professions"
    category = Column(String(100), nullable=True)
