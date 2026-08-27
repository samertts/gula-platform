from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class GrantAccessRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    workspace_id: str = Field(min_length=1, max_length=26)
    resource_type: str = Field(default="lab_result", pattern="^lab_result$")
    resource_id: str = Field(min_length=1, max_length=26)
    grantee_account_id: str = Field(min_length=1, max_length=26)
    purpose: str = Field(pattern="^(TREATMENT|RESEARCH|BILLING|AUDIT|PUBLIC_HEALTH)$")
    scope: dict[str, Any] = Field(min_length=1, max_length=10)
    duration_hours: int = Field(default=24, ge=1, le=72)

    @field_validator("scope")
    @classmethod
    def scope_must_be_explicit(cls, value: dict[str, Any]) -> dict[str, Any]:
        clean = {str(key): item for key, item in value.items() if isinstance(key, str) and str(key).strip()}
        if not clean or "read_result" not in clean:
            raise ValueError("scope must explicitly include read_result")
        if clean.get("read_result") is not True:
            raise ValueError("read_result scope must be true")
        if any(key not in {"read_result", "read_summary"} for key in clean):
            raise ValueError("scope contains an unsupported field")
        return clean


class RevokeAccessRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    workspace_id: str = Field(min_length=1, max_length=26)
    reason: str = Field(min_length=3, max_length=500)

    @field_validator("reason")
    @classmethod
    def reason_not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("reason is required")
        return value


class AccessHistoryQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")

    workspace_id: str = Field(min_length=1, max_length=26)
    provider_account_id: str | None = Field(default=None, max_length=26)
    resource_type: str | None = Field(default=None, max_length=40)
    purpose: str | None = Field(default=None, max_length=40)
    action: str | None = Field(default=None, max_length=48)
    limit: int = Field(default=50, ge=1, le=100)
    offset: int = Field(default=0, ge=0, le=1_000_000)
