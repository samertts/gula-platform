from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any

from app._compat import UTC
from app.health_data.warehouse.service import WarehouseService
from app.research_platform.enums import RegistryType

logger = logging.getLogger("gula.research_platform.registries")


@dataclass
class RegistryRecord:
    registry_id: str
    registry_type: RegistryType
    patient_ulid: str
    diagnosis: str = ""
    diagnosis_code: str = ""
    diagnosis_date: date | None = None
    stage: str = ""
    morphology: str = ""
    topography: str = ""
    cause_of_death: str = ""
    date_of_birth: date | None = None
    date_of_death: date | None = None
    birth_weight_grams: float | None = None
    gestational_weeks: int | None = None
    apgar_score: int | None = None
    congenital_anomalies: list[str] = field(default_factory=list)
    risk_factors: dict[str, Any] = field(default_factory=dict)
    outcomes: dict[str, Any] = field(default_factory=dict)
    facility_id: str = ""
    governorate: str = ""
    registered_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = field(default_factory=dict)


class RegistryManager:
    def __init__(self, warehouse: WarehouseService | None = None):
        self._warehouse = warehouse or WarehouseService()
        self._registries: dict[RegistryType, list[RegistryRecord]] = {rt: [] for rt in RegistryType}

    def register_record(self, record: RegistryRecord) -> RegistryRecord:
        self._registries.setdefault(record.registry_type, []).append(record)
        logger.info(
            "Registry record added: %s (%s)",
            record.registry_id,
            record.registry_type.value,
        )
        return record

    def register_batch(self, records: list[RegistryRecord]) -> list[RegistryRecord]:
        for r in records:
            self.register_record(r)
        return records

    def query(
        self,
        registry_type: RegistryType,
        governorate: str | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        diagnosis_code: str | None = None,
        limit: int = 100,
    ) -> list[RegistryRecord]:
        records = self._registries.get(registry_type, [])
        results = list(records)
        if governorate:
            results = [r for r in results if r.governorate == governorate]
        if diagnosis_code:
            results = [r for r in results if r.diagnosis_code == diagnosis_code]
        if date_from:
            results = [
                r
                for r in results
                if (r.diagnosis_date and r.diagnosis_date >= date_from)
                or (r.registered_at and r.registered_at.date() >= date_from)
            ]
        if date_to:
            results = [
                r
                for r in results
                if (r.diagnosis_date and r.diagnosis_date <= date_to)
                or (r.registered_at and r.registered_at.date() <= date_to)
            ]
        return results[:limit]

    def count_by_type(self) -> dict[str, int]:
        return {rt.value: len(records) for rt, records in self._registries.items()}

    def count_by_governorate(self, registry_type: RegistryType) -> dict[str, int]:
        counts: dict[str, int] = {}
        for r in self._registries.get(registry_type, []):
            gov = r.governorate or "unknown"
            counts[gov] = counts.get(gov, 0) + 1
        return counts

    def statistics(self, registry_type: RegistryType) -> dict[str, Any]:
        records = self._registries.get(registry_type, [])
        return {
            "registry_type": registry_type.value,
            "total_records": len(records),
            "by_governorate": self.count_by_governorate(registry_type),
        }


class CancerRegistry:
    def __init__(self, manager: RegistryManager | None = None):
        self._manager = manager or RegistryManager()

    def register_case(
        self,
        patient_ulid: str,
        diagnosis: str,
        diagnosis_code: str,
        diagnosis_date: date,
        stage: str = "",
        morphology: str = "",
        topography: str = "",
        governorate: str = "",
        facility_id: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> RegistryRecord:
        import uuid

        record = RegistryRecord(
            registry_id=str(uuid.uuid4()).replace("-", "").upper()[:26],
            registry_type=RegistryType.CANCER,
            patient_ulid=patient_ulid,
            diagnosis=diagnosis,
            diagnosis_code=diagnosis_code,
            diagnosis_date=diagnosis_date,
            stage=stage,
            morphology=morphology,
            topography=topography,
            governorate=governorate,
            facility_id=facility_id,
            metadata=metadata or {},
        )
        return self._manager.register_record(record)

    def incidence_rates(
        self,
        cancer_type: str | None = None,
        governorate: str | None = None,
        year: int | None = None,
    ) -> dict[str, Any]:
        records = self._manager.query(
            RegistryType.CANCER,
            governorate=governorate,
            diagnosis_code=cancer_type,
        )
        return {
            "registry": "cancer",
            "cancer_type": cancer_type,
            "governorate": governorate,
            "year": year,
            "total_cases": len(records),
            "crude_rate": None,
            "age_standardized_rate": None,
        }

    def survival_analysis(self, cancer_type: str) -> dict[str, Any]:
        return {
            "registry": "cancer",
            "cancer_type": cancer_type,
            "note": "Survival analysis requires longitudinal follow-up data",
        }


class BirthRegistry:
    def __init__(self, manager: RegistryManager | None = None):
        self._manager = manager or RegistryManager()

    def register_birth(
        self,
        patient_ulid: str,
        date_of_birth: date,
        birth_weight_grams: float | None = None,
        gestational_weeks: int | None = None,
        apgar_score: int | None = None,
        congenital_anomalies: list[str] | None = None,
        governorate: str = "",
        facility_id: str = "",
    ) -> RegistryRecord:
        import uuid

        record = RegistryRecord(
            registry_id=str(uuid.uuid4()).replace("-", "").upper()[:26],
            registry_type=RegistryType.BIRTH,
            patient_ulid=patient_ulid,
            date_of_birth=date_of_birth,
            birth_weight_grams=birth_weight_grams,
            gestational_weeks=gestational_weeks,
            apgar_score=apgar_score,
            congenital_anomalies=congenital_anomalies or [],
            governorate=governorate,
            facility_id=facility_id,
        )
        return self._manager.register_record(record)

    def birth_statistics(
        self, governorate: str | None = None, year: int | None = None
    ) -> dict[str, Any]:
        records = self._manager.query(RegistryType.BIRTH, governorate=governorate)
        return {
            "registry": "birth",
            "governorate": governorate,
            "year": year,
            "total_births": len(records),
            "live_births": len(records),
            "low_birth_weight": sum(
                1 for r in records if r.birth_weight_grams and r.birth_weight_grams < 2500
            ),
            "preterm": sum(1 for r in records if r.gestational_weeks and r.gestational_weeks < 37),
        }


class DeathRegistry:
    def __init__(self, manager: RegistryManager | None = None):
        self._manager = manager or RegistryManager()

    def register_death(
        self,
        patient_ulid: str,
        date_of_death: date,
        cause_of_death: str,
        governorate: str = "",
        facility_id: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> RegistryRecord:
        import uuid

        record = RegistryRecord(
            registry_id=str(uuid.uuid4()).replace("-", "").upper()[:26],
            registry_type=RegistryType.DEATH,
            patient_ulid=patient_ulid,
            cause_of_death=cause_of_death,
            date_of_death=date_of_death,
            governorate=governorate,
            facility_id=facility_id,
            metadata=metadata or {},
        )
        return self._manager.register_record(record)

    def mortality_statistics(
        self,
        cause: str | None = None,
        governorate: str | None = None,
        year: int | None = None,
    ) -> dict[str, Any]:
        records = self._manager.query(RegistryType.DEATH, governorate=governorate)
        if cause:
            records = [r for r in records if cause.lower() in r.cause_of_death.lower()]
        return {
            "registry": "death",
            "cause": cause,
            "governorate": governorate,
            "year": year,
            "total_deaths": len(records),
            "crude_death_rate": None,
            "cause_specific_mortality": None,
        }

    def leading_causes(self, governorate: str | None = None, limit: int = 10) -> dict[str, Any]:
        records = self._manager.query(RegistryType.DEATH, governorate=governorate)
        causes: dict[str, int] = {}
        for r in records:
            cause = r.cause_of_death or "unknown"
            causes[cause] = causes.get(cause, 0) + 1
        sorted_causes = sorted(causes.items(), key=lambda x: x[1], reverse=True)[:limit]
        return {
            "registry": "death",
            "governorate": governorate,
            "leading_causes": [{"cause": c, "count": n} for c, n in sorted_causes],
        }


class DiabetesRegistry:
    def __init__(self, manager: RegistryManager | None = None):
        self._manager = manager or RegistryManager()

    def register_case(
        self,
        patient_ulid: str,
        diagnosis: str,
        diagnosis_code: str = "E10-E14",
        diagnosis_date: date | None = None,
        diabetes_type: str = "type2",
        governorate: str = "",
        facility_id: str = "",
        hba1c: float | None = None,
    ) -> RegistryRecord:
        import uuid

        record = RegistryRecord(
            registry_id=str(uuid.uuid4()).replace("-", "").upper()[:26],
            registry_type=RegistryType.DIABETES,
            patient_ulid=patient_ulid,
            diagnosis=diagnosis,
            diagnosis_code=diagnosis_code,
            diagnosis_date=diagnosis_date,
            governorate=governorate,
            facility_id=facility_id,
            risk_factors={"diabetes_type": diabetes_type, "hba1c": hba1c},
        )
        return self._manager.register_record(record)

    def prevalence(
        self,
        governorate: str | None = None,
        diabetes_type: str | None = None,
    ) -> dict[str, Any]:
        records = self._manager.query(RegistryType.DIABETES, governorate=governorate)
        if diabetes_type:
            records = [r for r in records if r.risk_factors.get("diabetes_type") == diabetes_type]
        return {
            "registry": "diabetes",
            "governorate": governorate,
            "diabetes_type": diabetes_type,
            "total_cases": len(records),
            "prevalence_rate": None,
        }


class CardiovascularRegistry:
    def __init__(self, manager: RegistryManager | None = None):
        self._manager = manager or RegistryManager()

    def register_case(
        self,
        patient_ulid: str,
        diagnosis: str,
        diagnosis_code: str,
        diagnosis_date: date | None = None,
        condition_type: str = "",
        governorate: str = "",
        facility_id: str = "",
        risk_factors: dict[str, Any] | None = None,
    ) -> RegistryRecord:
        import uuid

        record = RegistryRecord(
            registry_id=str(uuid.uuid4()).replace("-", "").upper()[:26],
            registry_type=RegistryType.CARDIOVASCULAR,
            patient_ulid=patient_ulid,
            diagnosis=diagnosis,
            diagnosis_code=diagnosis_code,
            diagnosis_date=diagnosis_date,
            governorate=governorate,
            facility_id=facility_id,
            risk_factors=risk_factors or {},
            metadata={"condition_type": condition_type},
        )
        return self._manager.register_record(record)

    def burden(
        self,
        condition_type: str | None = None,
        governorate: str | None = None,
    ) -> dict[str, Any]:
        records = self._manager.query(RegistryType.CARDIOVASCULAR, governorate=governorate)
        if condition_type:
            records = [r for r in records if r.metadata.get("condition_type") == condition_type]
        return {
            "registry": "cardiovascular",
            "condition_type": condition_type,
            "governorate": governorate,
            "total_cases": len(records),
            "hospitalization_rate": None,
        }


class RareDiseaseRegistry:
    def __init__(self, manager: RegistryManager | None = None):
        self._manager = manager or RegistryManager()

    def register_case(
        self,
        patient_ulid: str,
        diagnosis: str,
        diagnosis_code: str,
        diagnosis_date: date | None = None,
        orpha_code: str = "",
        governorate: str = "",
        facility_id: str = "",
        genetic_confirmation: bool = False,
    ) -> RegistryRecord:
        import uuid

        record = RegistryRecord(
            registry_id=str(uuid.uuid4()).replace("-", "").upper()[:26],
            registry_type=RegistryType.RARE_DISEASE,
            patient_ulid=patient_ulid,
            diagnosis=diagnosis,
            diagnosis_code=diagnosis_code,
            diagnosis_date=diagnosis_date,
            governorate=governorate,
            facility_id=facility_id,
            metadata={
                "orpha_code": orpha_code,
                "genetic_confirmation": genetic_confirmation,
            },
        )
        return self._manager.register_record(record)

    def prevalence(self, orpha_code: str | None = None) -> dict[str, Any]:
        records = self._manager.query(RegistryType.RARE_DISEASE)
        if orpha_code:
            records = [r for r in records if r.metadata.get("orpha_code") == orpha_code]
        return {
            "registry": "rare_disease",
            "orpha_code": orpha_code,
            "total_cases": len(records),
            "estimated_prevalence": None,
        }
