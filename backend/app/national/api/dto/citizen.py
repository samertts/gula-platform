from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass
class CitizenCreateDTO:
    first_name: str = ""
    father_name: str | None = None
    grandfather_name: str | None = None
    last_name: str = ""
    mother_name: str | None = None
    date_of_birth: date | None = None
    gender: str = "unknown"
    phone: str | None = None
    email: str | None = None
    governorate: str | None = None
    nationality: str = "Iraqi"
    marital_status: str | None = None
    blood_group: str | None = None
    occupation: str | None = None


@dataclass
class CitizenResponseDTO:
    id: str = ""
    health_number: str = ""
    first_name: str = ""
    father_name: str | None = None
    last_name: str = ""
    full_name: str = ""
    date_of_birth: str = ""
    gender: str = ""
    phone: str | None = None
    email: str | None = None
    governorate: str | None = None
    nationality: str = ""
    identity_status: str = ""
    is_deceased: bool = False
    is_vip: bool = False
    created_at: str = ""
    updated_at: str = ""


@dataclass
class NewbornCreateDTO:
    birth_certificate_number: str = ""
    first_name: str | None = None
    last_name: str | None = None
    date_of_birth: date | None = None
    gender: str = "unknown"
    mother_id: str = ""
    mother_name: str | None = None
    father_id: str | None = None
    father_name: str | None = None
    birth_weight_grams: int | None = None
    hospital_id: str | None = None


@dataclass
class ForeignerCreateDTO:
    passport_number: str = ""
    passport_country: str = ""
    visa_number: str | None = None
    first_name: str = ""
    last_name: str = ""
    date_of_birth: date | None = None
    gender: str = "unknown"
    nationality: str = ""
    phone: str | None = None
    email: str | None = None
