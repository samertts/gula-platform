from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class VerificationRequest(_StrictModel):
    method: str = Field(pattern="^(SYNTHETIC|OTP|OCR|NFC|LIVENESS|GOVERNMENT)$")
    purpose: str = Field(min_length=1, max_length=160)


class VerificationCompleteRequest(_StrictModel):
    operation_id: str = Field(min_length=8, max_length=100)
    proof: str = Field(min_length=8, max_length=200)
    verified_attributes: dict[str, Any] | None = None


class HealthIdIssueRequest(_StrictModel):
    verification_operation_id: str = Field(min_length=8, max_length=100)


class DeviceRegisterRequest(_StrictModel):
    device_fingerprint: str = Field(min_length=16, max_length=255)
    device_name: str | None = Field(default=None, max_length=200)
    device_type: str | None = Field(default=None, max_length=50)


class DeviceTrustRequest(_StrictModel):
    device_id: str = Field(min_length=1, max_length=26)
    verification_operation_id: str = Field(min_length=8, max_length=100)


class ConsentGrantRequest(_StrictModel):
    grantee_account_id: str = Field(min_length=1, max_length=26)
    purpose: str = Field(min_length=1, max_length=80)
    resource_domain: str = Field(min_length=1, max_length=120)
    scope: dict[str, Any]
    expires_at: datetime
    reason: str | None = Field(default=None, max_length=1000)

    @model_validator(mode="after")
    def bounded_scope(self):
        serialized = str(self.scope).lower()
        if "*" in serialized or "public" in serialized:
            raise ValueError("wildcard and public consent scopes are not allowed")
        return self


class ConsentRevokeRequest(_StrictModel):
    consent_id: str = Field(min_length=1, max_length=26)
    reason: str = Field(min_length=1, max_length=1000)


class RecoveryRequest(_StrictModel):
    purpose: str = Field(min_length=1, max_length=160)


class RecoveryCompleteRequest(_StrictModel):
    operation_id: str = Field(min_length=8, max_length=100)
    proof: str = Field(min_length=8, max_length=200)
