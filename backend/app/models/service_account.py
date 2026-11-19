from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text

from app._compat import UTC

from ..database import Base


class ServiceAccount(Base):
    __tablename__ = "service_accounts"

    id = Column(Integer, primary_key=True, index=True)
    # Machine identities used for interoperability must be bound to one lab.
    # Nullable preserves existing administrative accounts; interop routes reject
    # unbound accounts explicitly.
    lab_id = Column(Integer, ForeignKey("labs.id", ondelete="SET NULL"), nullable=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    api_key_hash = Column(String(255), nullable=False)
    roles = Column(Text, nullable=True)
    scopes = Column(Text, nullable=True)
    # Boolean, not Integer: migration 20260716_0015 created this column as
    # ``sa.Boolean()``. The callers in app/security/service_accounts.py already
    # use boolean semantics (``.is_(True)``, ``= False``), so this declaration
    # was a latent trap rather than a live failure -- one ``== 1`` away from the
    # ``operator does not exist: boolean = integer`` that took OAuth2 down.
    is_active = Column(Boolean, default=True, index=True)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    created_by = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    expires_at = Column(DateTime(timezone=True), nullable=True)
