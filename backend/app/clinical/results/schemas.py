from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, model_validator


class CreateResultRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    workspace_id: str = Field(min_length=1, max_length=26)
    specimen_id: str = Field(min_length=1, max_length=26)
    value_numeric: float | None = None
    value_text: str | None = Field(default=None, max_length=2000)
    unit: str | None = Field(default=None, max_length=40)
    reference_low: float | None = None
    reference_high: float | None = None
    source_message_id: str | None = Field(default=None, max_length=200)
    provenance_type: str = Field(default="MANUAL", pattern="^(MANUAL|IMPORTED_SYNTHETIC)$")

    @model_validator(mode="after")
    def require_value_and_valid_range(self):
        if self.value_numeric is None and not (self.value_text and self.value_text.strip()):
            raise ValueError("a numeric or text value is required")
        if self.value_numeric is not None and self.value_text is not None:
            raise ValueError("numeric and text values are mutually exclusive")
        if self.reference_low is not None and self.reference_high is not None and self.reference_high < self.reference_low:
            raise ValueError("reference_high must be greater than or equal to reference_low")
        return self


class ResultActionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    workspace_id: str = Field(min_length=1, max_length=26)


class CriticalAcknowledgeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    workspace_id: str = Field(min_length=1, max_length=26)
    reason: str = Field(min_length=3, max_length=500)

    @model_validator(mode="after")
    def non_blank_reason(self):
        self.reason = self.reason.strip()
        if not self.reason:
            raise ValueError("reason is required")
        return self


class AmendResultRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    workspace_id: str = Field(min_length=1, max_length=26)
    reason: str = Field(min_length=3, max_length=500)
    value_numeric: float | None = None
    value_text: str | None = Field(default=None, max_length=2000)
    unit: str | None = Field(default=None, max_length=40)
    reference_low: float | None = None
    reference_high: float | None = None

    @model_validator(mode="after")
    def validate_amendment(self):
        self.reason = self.reason.strip()
        if not self.reason:
            raise ValueError("reason is required")
        if self.value_numeric is None and not (self.value_text and self.value_text.strip()):
            raise ValueError("a numeric or text value is required")
        if self.value_numeric is not None and self.value_text is not None:
            raise ValueError("numeric and text values are mutually exclusive")
        if self.reference_low is not None and self.reference_high is not None and self.reference_high < self.reference_low:
            raise ValueError("reference_high must be greater than or equal to reference_low")
        return self
