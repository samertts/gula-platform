from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy import Enum as SAEnum

from app.national.base import TenantAuditEntity
from app.national.enums import HealthCardStatus


class HealthCard(TenantAuditEntity):
    __tablename__ = "national_health_cards"

    status = Column(SAEnum(HealthCardStatus), nullable=False, default=HealthCardStatus.ACTIVE)

    citizen_id = Column(String(26), ForeignKey("national_citizens.id", ondelete="RESTRICT"), nullable=False, index=True)
    health_number = Column(String(20), nullable=False, index=True)

    card_number = Column(String(50), nullable=False, unique=True, index=True)
    card_type = Column(String(50), nullable=False)

    issued_at = Column(DateTime(timezone=True), nullable=False)
    expires_at = Column(Date, nullable=True)
    renewed_at = Column(DateTime(timezone=True), nullable=True)
    suspended_at = Column(DateTime(timezone=True), nullable=True)
    suspension_reason = Column(Text, nullable=True)

    qr_code_data = Column(Text, nullable=True)
    barcode_data = Column(String(200), nullable=True)
    has_pin = Column(Boolean, default=False)
    pin_hash = Column(String(255), nullable=True)

    is_lost = Column(Boolean, default=False)
    lost_reported_at = Column(DateTime(timezone=True), nullable=True)

    is_active = Column(Boolean, default=True)
    version = Column(Integer, default=1, nullable=False)

    __table_args__ = (
        Index("ix_national_health_cards_citizen", "citizen_id"),
        {"extend_existing": True},
    )
