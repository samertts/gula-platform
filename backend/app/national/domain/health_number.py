from sqlalchemy import Boolean, Column, Index, Integer, String

from app.national.base import BaseEntity


class HealthNumberSequence(BaseEntity):
    __tablename__ = "national_health_number_sequences"

    prefix = Column(String(5), nullable=False)
    sequence_number = Column(Integer, nullable=False, default=0)
    year = Column(Integer, nullable=False)
    is_depleted = Column(Boolean, default=False)

    __table_args__ = (
        Index("ix_national_hn_sequences_prefix_year", "prefix", "year", unique=True),
        {"extend_existing": True},
    )
