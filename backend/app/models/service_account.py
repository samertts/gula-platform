from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text

from app._compat import UTC

from ..database import Base


class ServiceAccount(Base):
    __tablename__ = "service_accounts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    api_key_hash = Column(String(255), nullable=False)
    roles = Column(Text, nullable=True)
    scopes = Column(Text, nullable=True)
    is_active = Column(Integer, default=1, index=True)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    created_by = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    expires_at = Column(DateTime(timezone=True), nullable=True)
