from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from enum import Enum


class Gender(Enum):
    MALE = "male"
    FEMALE = "female"
    UNKNOWN = "unknown"


class IdentityStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    MERGED = "merged"
    DECEASED = "deceased"
    DUPLICATE = "duplicate"


class IdentityDocumentType(Enum):
    IRAQI_NATIONAL_ID = "iraqi_national_id"
    IRAQI_RESIDENCY = "iraqi_residency"
    PASSPORT = "passport"
    HEALTH_ID = "health_id"
    BIRTH_CERTIFICATE = "birth_certificate"
    FAMILY_ID = "family_id"


@dataclass(frozen=True)
class PersonName:
    first: str = ""
    middle: str = ""
    last: str = ""
    full: str = ""
    mother_name: str = ""
    name_ar: str = ""
    name_en: str = ""

    def display(self, prefer_arabic: bool = True) -> str:
        if prefer_arabic and self.name_ar:
            return self.name_ar
        if self.full:
            return self.full
        parts = [p for p in (self.first, self.middle, self.last) if p]
        return " ".join(parts) if parts else ""

    def normalized(self) -> str:
        text = (self.name_ar or self.full or self.display(False)).lower()
        text = re.sub(r"[\u0610-\u061A\u064B-\u065F]", "", text)
        for src, dst in {"أ": "ا", "إ": "ا", "آ": "ا", "ة": "ه", "ى": "ي", "ؤ": "و", "ئ": "ي"}.items():
            text = text.replace(src, dst)
        return re.sub(r"\s+", " ", text).strip()


@dataclass(frozen=True)
class IdentityDocument:
    type: IdentityDocumentType
    value: str
    issuing_country: str = "IQ"
    verified: bool = False
    verified_at: datetime | None = None
    expires_at: date | None = None

    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return date.today() > self.expires_at


@dataclass
class PatientIdentity:
    id: str = ""
    health_id: str = ""
    national_id_hash: str = ""
    name: PersonName = field(default_factory=PersonName)
    gender: Gender = Gender.UNKNOWN
    date_of_birth: date | None = None
    phone: str = ""
    email: str = ""
    address: str = ""
    city: str = ""
    province: str = ""
    documents: list[IdentityDocument] = field(default_factory=list)
    status: IdentityStatus = IdentityStatus.ACTIVE
    lab_id: int = 0
    is_deceased: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    merged_into_id: str | None = None
    metadata: dict = field(default_factory=dict)

    def has_valid_national_id(self) -> bool:
        return bool(self.national_id_hash) and self._has_any_document_of_type(
            IdentityDocumentType.IRAQI_NATIONAL_ID
        )

    def _has_any_document_of_type(self, dtype: IdentityDocumentType) -> bool:
        return any(d.type == dtype for d in self.documents)

    def age(self) -> int | None:
        if self.date_of_birth is None:
            return None
        today = date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "health_id": self.health_id,
            "name": {
                "first": self.name.first,
                "last": self.name.last,
                "full": self.name.full,
                "name_ar": self.name.name_ar,
                "name_en": self.name.name_en,
            },
            "gender": self.gender.value,
            "date_of_birth": self.date_of_birth.isoformat() if self.date_of_birth else None,
            "phone": self.phone,
            "email": self.email,
            "city": self.city,
            "province": self.province,
            "status": self.status.value,
            "lab_id": self.lab_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
