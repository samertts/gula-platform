from app.national.reference.base import ReferenceEntity
from sqlalchemy import Column, Index, String


class District(ReferenceEntity):
    __tablename__ = "ref_districts"
    governorate_code = Column(String(10), nullable=False, index=True)
    country_code = Column(String(2), default="IQ")

    __table_args__ = (
        Index("ix_ref_districts_governorate", "governorate_code"),
    )
