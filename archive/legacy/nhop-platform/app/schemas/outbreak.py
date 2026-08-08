"""Pydantic v2 schemas for the outbreak detection API."""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

Severity = Literal["info", "warning", "critical"]


class OutbreakAlert(BaseModel):
    disease_code: str
    disease_name: str | None = None
    province: str
    current_count: int = Field(..., ge=0, description="Positives in the last 24h")
    baseline_avg: float = Field(..., ge=0, description="Avg 24h count over the 30d window")
    ratio: float = Field(..., ge=0, description="current_count / max(baseline_avg, 1)")
    severity: Severity
    detected_at: datetime


class AlertsResponse(BaseModel):
    generated_at: datetime
    alerts: list[OutbreakAlert]


class ProvinceCount(BaseModel):
    province: str
    count: int = Field(..., ge=0)


class HeatmapResponse(BaseModel):
    disease_code: str
    days: int = Field(..., ge=1, le=365)
    window_start: datetime
    window_end: datetime
    total: int
    by_province: list[ProvinceCount]


class ResistancePair(BaseModel):
    bacterium: str
    antibiotic: str
    province: str | None = None
    tested: int = Field(..., ge=1)
    resistant: int = Field(..., ge=0)
    resistance_rate: float = Field(..., ge=0.0, le=1.0)


class ResistanceResponse(BaseModel):
    generated_at: datetime
    province_filter: str | None = None
    total_pairs: int
    pairs: list[ResistancePair]
