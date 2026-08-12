from sqlalchemy import Boolean, Column, Integer, String, Text

from app.national_data.base import BaseEntity


class DataQualityRule(BaseEntity):
    __tablename__ = "dp_data_quality_rules"

    rule_name = Column(String(200), nullable=False, unique=True)
    rule_type = Column(String(50), nullable=False, index=True)
    rule_category = Column(String(50), nullable=False)

    entity_type = Column(String(100), nullable=False)
    field_name = Column(String(100), nullable=True)
    condition_expression = Column(Text, nullable=True)
    severity = Column(String(20), default="error", nullable=False)

    description = Column(Text, nullable=True)
    remediation_sql = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_auto_remediable = Column(Boolean, default=False, nullable=False)

    threshold_warning = Column(Integer, default=95, nullable=True)
    threshold_error = Column(Integer, default=90, nullable=True)

    __table_args__ = (
        {"extend_existing": True},
    )
