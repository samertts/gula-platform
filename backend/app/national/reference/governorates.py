from sqlalchemy import Column, Index, String

from app.national.reference.base import ReferenceEntity


class Governorate(ReferenceEntity):
    __tablename__ = "ref_governorates"
    country_code = Column(String(2), default="IQ", nullable=False)
    governorate_code = Column(String(10), nullable=True)

    __table_args__ = (Index("ix_ref_governorates_country", "country_code"),)
