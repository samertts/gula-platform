from sqlalchemy import Column, Integer, String, DateTime, Text
from datetime import datetime, timezone
from ..database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True, index=True)
    user_role = Column(String(50), nullable=True)
    action = Column(String(50), nullable=False, index=True)  # view, create, update, delete
    resource_type = Column(String(50), nullable=False)  # patient, test, result
    resource_id = Column(Integer, nullable=True)
    details = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    # Tamper-detection: SHA-256(prev_chain_hash + this_record_data)
    # Any modification to a record or its predecessors breaks the chain.
    chain_hash = Column(String(64), nullable=True, index=True)
