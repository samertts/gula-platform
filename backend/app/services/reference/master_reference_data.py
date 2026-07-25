from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from app._compat import UTC

logger = logging.getLogger("gula.reference.data")


class ReferenceDataType(Enum):
    COUNTRY = "country"
    NATIONALITY = "nationality"
    GOVERNORATE = "governorate"
    DISTRICT = "district"
    SUBDISTRICT = "subdistrict"
    HEALTHCARE_ORGANIZATION = "healthcare_organization"
    FACILITY = "facility"
    DEPARTMENT = "department"
    LABORATORY = "laboratory"
    MEDICAL_SPECIALTY = "medical_specialty"
    LANGUAGE = "language"
    CURRENCY = "currency"
    TIMEZONE = "timezone"
    UNIT = "unit"
    CONFIGURATION_SET = "configuration_set"


@dataclass
class ReferenceEntry:
    id: str = ""
    code: str = ""
    name: str = ""
    name_ar: str = ""
    type: str = ""
    parent_code: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    is_active: bool = True
    version: int = 1
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())


class MasterReferenceDataService:
    def __init__(self):
        self._data: dict[str, dict[str, ReferenceEntry]] = {}
        self._code_index: dict[str, dict[str, str]] = {}
        self._version_map: dict[str, int] = {}

    def seed_defaults(self) -> None:
        iraq_country = ReferenceEntry(
            code="IQ",
            name="Iraq",
            name_ar="العراق",
            type=ReferenceDataType.COUNTRY.value,
        )
        self.upsert(iraq_country)

        for gov_code, gov_name, gov_name_ar in [
            ("BG", "Baghdad", "بغداد"),
            ("BS", "Basra", "البصرة"),
            ("NI", "Nineveh", "نينوى"),
            ("DQ", "Dhi Qar", "ذي قار"),
            ("SU", "Sulaymaniyah", "السليمانية"),
            ("ER", "Erbil", "أربيل"),
            ("KR", "Kirkuk", "كركوك"),
            ("NA", "Najaf", "النجف"),
            ("KA", "Karbala", "كربلاء"),
            ("BB", "Babylon", "بابل"),
        ]:
            self.upsert(
                ReferenceEntry(
                    code=gov_code,
                    name=gov_name,
                    name_ar=gov_name_ar,
                    type=ReferenceDataType.GOVERNORATE.value,
                    parent_code="IQ",
                )
            )

        for lang_code, lang_name, lang_name_ar in [
            ("ar", "Arabic", "العربية"),
            ("en", "English", "الإنجليزية"),
            ("ku", "Kurdish", "الكردية"),
            ("tr", "Turkish", "التركية"),
        ]:
            self.upsert(
                ReferenceEntry(
                    code=lang_code,
                    name=lang_name,
                    name_ar=lang_name_ar,
                    type=ReferenceDataType.LANGUAGE.value,
                )
            )

        for cur_code, cur_name in [
            ("IQD", "Iraqi Dinar"),
            ("USD", "US Dollar"),
            ("EUR", "Euro"),
        ]:
            self.upsert(
                ReferenceEntry(
                    code=cur_code,
                    name=cur_name,
                    type=ReferenceDataType.CURRENCY.value,
                )
            )

        for tz_code, tz_name in [
            ("Asia/Baghdad", "Baghdad Time (UTC+3)"),
        ]:
            self.upsert(
                ReferenceEntry(
                    code=tz_code,
                    name=tz_name,
                    type=ReferenceDataType.TIMEZONE.value,
                )
            )

        specialties = [
            ("PATH", "Pathology", "علم الأمراض"),
            ("MICRO", "Microbiology", "علم الأحياء الدقيقة"),
            ("CHEM", "Clinical Chemistry", "الكيمياء السريرية"),
            ("HEMA", "Hematology", "علم الدم"),
            ("IMMU", "Immunology", "علم المناعة"),
            ("MOL", "Molecular Biology", "البيولوجيا الجزيئية"),
            ("GEN", "Genetics", "علم الوراثة"),
        ]
        for sp_code, sp_name, sp_name_ar in specialties:
            self.upsert(
                ReferenceEntry(
                    code=sp_code,
                    name=sp_name,
                    name_ar=sp_name_ar,
                    type=ReferenceDataType.MEDICAL_SPECIALTY.value,
                )
            )

        units = [
            ("mg/dL", "Milligrams per deciliter"),
            ("g/dL", "Grams per deciliter"),
            ("mmol/L", "Millimoles per liter"),
            ("U/L", "Units per liter"),
            ("mIU/mL", "Milli-international units per milliliter"),
            ("ng/mL", "Nanograms per milliliter"),
            ("pg/mL", "Picograms per milliliter"),
            ("fg/mL", "Femtograms per milliliter"),
            ("cells/uL", "Cells per microliter"),
            ("%", "Percent"),
            ("ratio", "Ratio"),
            ("IU/mL", "International units per milliliter"),
            ("mm/hr", "Millimeters per hour"),
            ("mg/24h", "Milligrams per 24 hours"),
            ("mEq/L", "Milliequivalents per liter"),
            ("mL/min", "Milliliters per minute"),
            ("mm3", "Cubic millimeters"),
            ("fl", "Femtoliters"),
            ("pg", "Picograms"),
        ]
        for u_code, u_name in units:
            self.upsert(
                ReferenceEntry(
                    code=u_code,
                    name=u_name,
                    type=ReferenceDataType.UNIT.value,
                )
            )

        logger.info(
            "Master reference data seeded: %d entries",
            sum(len(v) for v in self._data.values()),
        )

    def upsert(self, entry: ReferenceEntry) -> ReferenceEntry:
        type_key = entry.type
        if type_key not in self._data:
            self._data[type_key] = {}
            self._code_index[type_key] = {}

        existing = self._data[type_key].get(entry.code)
        if existing:
            entry.version = existing.version + 1
            entry.created_at = existing.created_at
            entry.updated_at = datetime.now(UTC)

        self._data[type_key][entry.code] = entry
        self._code_index[type_key][entry.code] = entry.id
        self._version_map[f"{type_key}:{entry.code}"] = entry.version
        return entry

    def get(self, data_type: str | ReferenceDataType, code: str) -> ReferenceEntry | None:
        if isinstance(data_type, ReferenceDataType):
            data_type = data_type.value
        return self._data.get(data_type, {}).get(code)

    def list_by_type(self, data_type: str | ReferenceDataType) -> list[ReferenceEntry]:
        if isinstance(data_type, ReferenceDataType):
            data_type = data_type.value
        return list(self._data.get(data_type, {}).values())

    def list_by_parent(self, parent_code: str) -> list[ReferenceEntry]:
        results = []
        for entries in self._data.values():
            for entry in entries.values():
                if entry.parent_code == parent_code:
                    results.append(entry)
        return results

    def get_version(self, data_type: str, code: str) -> int:
        return self._version_map.get(f"{data_type}:{code}", 1)

    def export_all(self) -> dict[str, list[dict[str, Any]]]:
        result = {}
        for type_key, entries in self._data.items():
            result[type_key] = [
                {
                    "code": e.code,
                    "name": e.name,
                    "name_ar": e.name_ar,
                    "parent_code": e.parent_code,
                    "is_active": e.is_active,
                    "version": e.version,
                }
                for e in entries.values()
            ]
        return result

    def count(self) -> int:
        return sum(len(v) for v in self._data.values())

    def count_by_type(self) -> dict[str, int]:
        return {k: len(v) for k, v in self._data.items()}
