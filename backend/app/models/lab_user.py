from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from ..database import Base


class LabUser(Base):
    __tablename__ = "lab_users"

    id = Column(Integer, primary_key=True, index=True)
    lab_id = Column(Integer, ForeignKey("labs.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), default="staff", index=True)
    is_active = Column(Boolean, default=True, index=True)
    perm_version = Column(Integer, default=1, nullable=False)  # bump on role/permission change
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # ── Extended fields (migration: 20250322_roles_hierarchy) ─────────────────
    # national_id_hash: HMAC-SHA256 of the user's national ID — used to link
    # the MASTER_ADMIN account to a real person; nullable for all other accounts.
    national_id_hash = Column(String(255), nullable=True, unique=True, index=True)

    # province_id: For PROVINCE_ADMIN — restricts authority to one province.
    # Nullable for roles that are not province-scoped.
    province_id = Column(Integer, nullable=True, index=True)

    # created_by: who created this account (for audit trail)
    created_by = Column(Integer, ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True)

    lab = relationship("Lab", back_populates="users")
