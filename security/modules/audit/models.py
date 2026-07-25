from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class AuditEvent(BaseModel):
    event_id: str = ""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    actor_id: str = ""
    actor_type: str = "user"
    action: str = ""
    resource_type: str = ""
    resource_id: str = ""
    outcome: str = "success"
    request_id: str | None = None
    session_id: str | None = None
    source_ip: str | None = None
    user_agent: str | None = None
    changes: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    hash: str = ""
    previous_hash: str = ""


class AuditPolicy(BaseModel):
    retention_days: int = 365
    required_events: list[str] = Field(default_factory=lambda: [
        "authentication.login", "authentication.logout", "authorization.deny",
        "data.access", "data.modify", "data.delete", "admin.config_change",
        "user.create", "user.delete", "user.role_change",
        "security.breach", "compliance.violation",
    ])
    immutable_storage: bool = True
    encryption_required: bool = True
    alert_on: list[str] = Field(default_factory=lambda: [
        "security.breach", "authorization.deny", "authentication.failure",
    ])
    export_format: str = "json"
