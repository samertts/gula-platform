from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text

from app._compat import UTC

from ..database import Base


class OAuth2Client(Base):
    __tablename__ = "oauth2_clients"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(String(100), unique=True, nullable=False, index=True)
    client_secret_hash = Column(String(255), nullable=False)
    redirect_uris = Column(Text, nullable=True)
    allowed_scopes = Column(Text, nullable=True)
    grant_types = Column(Text, nullable=True)
    response_types = Column(Text, nullable=True)
    # Boolean, not Integer: migration 20260716_0015 created both of these as
    # ``sa.Boolean()``. Declaring them Integer made every comparison the routes
    # emit (``is_active == 1``) invalid SQL in PostgreSQL --
    # ``operator does not exist: boolean = integer`` -- which took the whole
    # OAuth2/OIDC provider down, /token included.
    is_confidential = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)
    token_endpoint_auth_method = Column(String(50), default="client_secret_basic")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
