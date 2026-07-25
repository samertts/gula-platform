from sqlalchemy import Boolean, Column, String, Text

from app.national_data.base import BaseEntity


class DataClassification(BaseEntity):
    __tablename__ = "dp_data_classifications"

    entity_name = Column(String(200), nullable=False)
    field_name = Column(String(100), nullable=True)

    classification_level = Column(String(50), nullable=False, index=True)
    classification_category = Column(String(50), nullable=True)
    sensitivity = Column(String(20), nullable=False)

    is_pii = Column(Boolean, default=False, nullable=False)
    is_phi = Column(Boolean, default=False, nullable=False)
    is_financial = Column(Boolean, default=False, nullable=False)
    is_confidential = Column(Boolean, default=False, nullable=False)

    access_restrictions = Column(Text, nullable=True)
    encryption_required = Column(Boolean, default=True, nullable=False)
    masking_required = Column(Boolean, default=False, nullable=False)
    retention_guideline = Column(String(100), nullable=True)

    notes = Column(Text, nullable=True)

    __table_args__ = ({"extend_existing": True},)
