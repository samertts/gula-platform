from sqlalchemy import Column, String

from app.national.reference.base import ReferenceEntity


class FacilityTypeRef(ReferenceEntity):
    __tablename__ = "ref_facility_types"
    category = Column(String(100), nullable=True)
    regulatory_body = Column(String(100), nullable=True)
