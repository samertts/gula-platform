from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text

from app._compat import UTC

from ..database import Base


class OAuth2Token(Base):
    __tablename__ = "oauth2_tokens"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(String(100), nullable=False, index=True)
    user_id = Column(Integer, nullable=True, index=True)
    token_type = Column(String(20), nullable=False)
    token_hash = Column(String(255), nullable=False, index=True)
    scope = Column(Text, nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    code_challenge = Column(String(255), nullable=True)
    code_challenge_method = Column(String(10), nullable=True)
    is_revoked = Column(Integer, default=0, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
