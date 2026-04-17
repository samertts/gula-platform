from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from ..models.lab import LabType


class LabBase(BaseModel):
    name: str = Field(..., max_length=200)
    license_number: str = Field(..., max_length=100)
    lab_type: LabType
    province: str = Field(..., max_length=100)
    district: Optional[str] = Field(default=None, max_length=100)
    address: Optional[str] = Field(default=None, max_length=500)
    phone: Optional[str] = Field(default=None, max_length=30)
    email: Optional[EmailStr] = None
    is_active: bool = True


class LabCreate(LabBase):
    pass


class LabRead(LabBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    quality_rating: float = 0.0
    avg_tat_minutes: int = 0
    total_tests: int = 0
    created_at: datetime


class LabBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    lab_type: LabType
    province: str
    quality_rating: float = 0.0
    is_active: bool = True


class LabDeviceBase(BaseModel):
    device_name: str = Field(..., max_length=200)
    manufacturer: str = Field(..., max_length=100)
    model: str = Field(..., max_length=100)
    serial_number: str = Field(..., max_length=100)
    is_calibrated: bool = True
    last_calibration: Optional[datetime] = None
    next_calibration: Optional[datetime] = None
    is_active: bool = True


class LabDeviceCreate(LabDeviceBase):
    lab_id: UUID


class LabDeviceRead(LabDeviceBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    lab_id: UUID
