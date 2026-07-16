from __future__ import annotations

from typing import Any


class ReferenceService:
    def lookup(self, ref_type: str, code: str) -> dict[str, Any] | None:
        models = {
            "country": ("ref_countries", "code"),
            "governorate": ("ref_governorates", "code"),
            "district": ("ref_districts", "code"),
            "icd10": ("ref_icd10_codes", "icd_code"),
            "loinc": ("ref_loinc_codes", "loinc_num"),
            "snomed": ("ref_snomed_concepts", "concept_id"),
            "ucum": ("ref_ucum_units", "ucum_code"),
        }
        table, _column = models.get(ref_type, (None, None))
        if not table:
            return None
        return {"ref_type": ref_type, "code": code}

    def list(self, ref_type: str, skip: int = 0, limit: int = 100) -> list[dict[str, Any]]:
        return []

    def search(self, ref_type: str, query: str) -> list[dict[str, Any]]:
        return []
