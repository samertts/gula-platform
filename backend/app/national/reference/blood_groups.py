from sqlalchemy import Column, String

from app.national.reference.base import ReferenceEntity


class BloodGroup(ReferenceEntity):
    __tablename__ = "ref_blood_groups"
    rh_factor = Column(String(1), nullable=True)
    abo_group = Column(String(2), nullable=True)
