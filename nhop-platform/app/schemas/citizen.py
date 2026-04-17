from __future__ import annotations

from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from ..models.citizen import Gender


class _CitizenCore(BaseModel):
    national_id: str = Field(..., min_length=1, max_length=20)
    first_name: str = Field(..., min_length=1, max_length=100)
    father_name: Optional[str] = Field(default=None, max_length=100)
    grandfather_name: Optional[str] = Field(default=None, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    mother_name: Optional[str] = Field(default=None, max_length=100)
    birth_date: date
    gender: Optional[Gender] = None
    blood_type: Optional[str] = Field(default=None, max_length=5)
    phone: Optional[str] = Field(default=None, max_length=20)
    province: Optional[str] = Field(default=None, max_length=100)
    district: Optional[str] = Field(default=None, max_length=100)
    is_alive: bool = True


class CitizenCreate(_CitizenCore):
    """Payload used to register a new citizen.

    `id`, `health_id`, `created_at`, and `updated_at` are assigned by the server.
    """


class CitizenRead(_CitizenCore):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    health_id: str
    created_at: datetime
    updated_at: datetime


class CitizenBrief(BaseModel):
    """Minimal citizen projection for lists and lookup responses."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    health_id: str
    first_name: str
    last_name: str
    birth_date: date
