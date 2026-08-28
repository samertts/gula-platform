from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class StrictLabRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class TestCatalogCreateRequest(StrictLabRequest):
    workspace_id: str = Field(min_length=1, max_length=80)
    canonical_code: str = Field(min_length=1, max_length=120)
    local_code: str | None = Field(default=None, max_length=120)
    name: str = Field(min_length=2, max_length=240)
    system: str = Field(min_length=2, max_length=120)
    specimen_type: str = Field(min_length=2, max_length=80)
    unit_ucum: str | None = Field(default=None, max_length=80)
    method: str | None = Field(default=None, max_length=160)
    reference_range: dict[str, str | float | int] = Field(default_factory=dict, max_length=12)
    critical_range: dict[str, str | float | int] = Field(default_factory=dict, max_length=12)


class AnalyzerCreateRequest(StrictLabRequest):
    workspace_id: str = Field(min_length=1, max_length=80)
    section: str = Field(min_length=2, max_length=120)
    manufacturer: str = Field(min_length=2, max_length=160)
    model: str = Field(min_length=1, max_length=160)
    serial_fingerprint: str = Field(min_length=16, max_length=128)
    protocol: Literal["SYNTHETIC", "ASTM", "HL7_V2", "FHIR", "FILE"] = "SYNTHETIC"


class AnalyzerActionRequest(StrictLabRequest):
    workspace_id: str = Field(min_length=1, max_length=80)
    target_status: Literal["VALIDATED", "ACTIVE", "MAINTENANCE", "QUARANTINED", "RETIRED"]


class AnalyzerMessageRequest(StrictLabRequest):
    workspace_id: str = Field(min_length=1, max_length=80)
    message_id: str = Field(min_length=8, max_length=160)
    analyzer_id: str = Field(min_length=1, max_length=40)
    specimen_id: str = Field(min_length=1, max_length=40)
    test_code: str = Field(min_length=1, max_length=120)
    payload_hash: str = Field(min_length=64, max_length=64)
    quality_flags: dict[str, str] = Field(default_factory=dict, max_length=20)
    source: Literal["SYNTHETIC", "HL7_V2", "ASTM", "FHIR", "FILE"] = "SYNTHETIC"
    occurred_at: datetime | None = None


class QCCreateRequest(StrictLabRequest):
    workspace_id: str = Field(min_length=1, max_length=80)
    result_id: str = Field(min_length=1, max_length=40)
    analyzer_id: str | None = Field(default=None, max_length=40)
    status: Literal["PASS", "FAILED", "OVERRIDDEN"]
    reason: str | None = Field(default=None, max_length=500)
    override_reason: str | None = Field(default=None, max_length=500)
