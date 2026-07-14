from app.national.reference.base import ReferenceEntity
from sqlalchemy import Column, Index, String


class Subdistrict(ReferenceEntity):
    __tablename__ = "ref_subdistricts"
    district_code = Column(String(10), nullable=False, index=True)
    governorate_code = Column(String(10), nullable=True)

    __table_args__ = (
        Index("ix_ref_subdistricts_district", "district_code"),
    )
