from sqlalchemy import JSON, Boolean, Column, Integer, String, Text

from app.national_data.base import BaseEntity


class FeatureStore(BaseEntity):
    __tablename__ = "dp_feature_store"

    feature_name = Column(String(200), nullable=False, unique=True, index=True)
    feature_type = Column(String(50), nullable=False)
    feature_version = Column(Integer, default=1, nullable=False)

    entity_type = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    source_query = Column(Text, nullable=True)
    transformation = Column(Text, nullable=True)

    data_type = Column(String(50), nullable=False, default="float")
    default_value = Column(String(100), nullable=True)
    value_range_min = Column(String(50), nullable=True)
    value_range_max = Column(String(50), nullable=True)

    is_active = Column(Boolean, default=True, nullable=False)
    is_required = Column(Boolean, default=False, nullable=False)
    imputation_strategy = Column(String(50), nullable=True)

    tags = Column(JSON, nullable=True)
    owner = Column(String(100), nullable=True)

    __table_args__ = {"extend_existing": True}
