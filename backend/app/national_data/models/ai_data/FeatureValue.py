from datetime import datetime

from app._compat import UTC
from app.national_data.base import BaseEntity
from sqlalchemy import Column, DateTime, Float, ForeignKey, Index, Integer, String, Text


class FeatureValue(BaseEntity):
    __tablename__ = "dp_feature_values"

    feature_id = Column(Integer, ForeignKey("dp_feature_store.id", ondelete="CASCADE"), nullable=False, index=True)
    entity_type = Column(String(100), nullable=False)
    entity_id = Column(String(100), nullable=False, index=True)

    value_numeric = Column(Float, nullable=True)
    value_text = Column(Text, nullable=True)
    value_json = Column(Text, nullable=True)

    effective_at = Column(DateTime(timezone=True), nullable=False)
    recorded_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)

    lab_id = Column(Integer, nullable=True, index=True)
    source = Column(String(100), nullable=True)

    __table_args__ = (
        Index("ix_dp_feature_val_feature", "feature_id"),
        Index("ix_dp_feature_val_entity", "entity_type", "entity_id"),
        Index("ix_dp_feature_val_effective", "effective_at"),
        {"extend_existing": True},
    )
