from sqlalchemy import Column, String

from app.national.reference.base import ReferenceEntity


class Profession(ReferenceEntity):
    __tablename__ = "ref_professions"
    category = Column(String(100), nullable=True)
