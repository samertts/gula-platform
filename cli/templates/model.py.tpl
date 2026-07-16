from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import relationship

from app._compat import UTC

from ..database import Base


class {{ class_name }}(Base):
    __tablename__ = "{{ table_name }}"

    __table_args__ = (
        Index("ix_{{ table_name }}_lab_id", "lab_id"),
    )

    id = Column(Integer, primary_key=True, index=True)
    lab_id = Column(Integer, ForeignKey("labs.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    {% for field in fields %}
    {% if field.name not in ("id", "lab_id", "name", "description", "created_at", "updated_at") %}
    {{ field.name }} = Column({{ field.type }}, nullable=True)
    {% endif %}
    {% endfor %}
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    lab = relationship("Lab", back_populates="{{ table_name }}")
