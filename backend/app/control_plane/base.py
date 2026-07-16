from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Column, DateTime, String

from app._compat import UTC

from .enums import ComponentStatus, PlatformComponent


def generate_control_id() -> str:
    return f"cp_{uuid.uuid4().hex[:24]}"


class ControlPlaneBaseMixin:
    id = Column(String(36), primary_key=True, default=generate_control_id)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    def to_dict(self) -> dict[str, Any]:
        result = {}
        for col in self.__table__.columns:
            val = getattr(self, col.name)
            if isinstance(val, datetime):
                val = val.isoformat()
            result[col.name] = val
        return result

    def __repr__(self) -> str:
        pk = getattr(self, "id", "no-id")
        return f"<{self.__class__.__name__}(id={pk})>"


class TenantAwareMixin:
    tenant_id = Column(String(36), nullable=True, index=True)
    tenant_level = Column(String(50), nullable=True)


class ComponentAwareMixin:
    component_type = Column(String(50), nullable=False, default=PlatformComponent.SERVICE)
    component_status = Column(String(50), nullable=False, default=ComponentStatus.REGISTERED)
    component_version = Column(String(20), nullable=True)
