from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date
from typing import Any

from app.health_data.warehouse.service import WarehouseQuery, WarehouseService

logger = logging.getLogger("gula.research_platform.population_health")


@dataclass
class PopulationIndicator:
    name: str
    value: float
    unit: str = ""
    period: str = ""
    benchmark: float | None = None
    trend: str = "stable"
    metadata: dict[str, Any] = field(default_factory=dict)


class PopulationAnalytics:
    def __init__(self, warehouse: WarehouseService | None = None):
        self._warehouse = warehouse or WarehouseService()

    def disease_burden(
        self,
        icd10_codes: list[str] | None = None,
        governorate: str | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> dict[str, Any]:
        query = WarehouseQuery(
            dimensions=["encounter_type", "diagnosis_count"],
            measures=["diagnosis_count"],
            filters={},
            group_by=["encounter_type"],
            date_from=date_from,
            date_to=date_to,
        )
        if icd10_codes:
            query.filters["encounter_type"] = icd10_codes[0]
        if governorate:
            self._warehouse.get_dimension("hd_wh_dim_facility")
            query.filters["governorate"] = governorate
        result = self._warehouse.query(query)
        return {
            "scope": "disease_burden",
            "icd10_codes": icd10_codes,
            "governorate": governorate,
            "period": {"from": date_from.isoformat() if date_from else None, "to": date_to.isoformat() if date_to else None},
            "summary": result,
            "indicators": self._compute_morbidity_indicators(result),
        }

    def mortality_analytics(
        self,
        cause: str | None = None,
        governorate: str | None = None,
        period: str = "annual",
    ) -> dict[str, Any]:
        return {
            "scope": "mortality_analytics",
            "cause": cause,
            "governorate": governorate,
            "period": period,
            "note": "Delegates to death registry for actual mortality counts",
            "requires_integration": True,
        }

    def morbidity_analytics(
        self,
        condition: str | None = None,
        governorate: str | None = None,
        age_group: str | None = None,
    ) -> dict[str, Any]:
        query = WarehouseQuery(
            dimensions=["age_group", "encounter_type"],
            measures=["diagnosis_count"],
            group_by=["age_group", "encounter_type"],
        )
        if governorate:
            query.filters["governorate"] = governorate
        if condition:
            query.filters["encounter_type"] = condition
        result = self._warehouse.query(query)
        return {
            "scope": "morbidity",
            "condition": condition,
            "governorate": governorate,
            "age_group": age_group,
            "results": result,
        }

    def _compute_morbidity_indicators(self, query_result: dict) -> list[PopulationIndicator]:
        rows = query_result.get("rows", [])
        total = sum(r.get("diagnosis_count", 0) or 0 for r in rows)
        return [
            PopulationIndicator(name="total_cases", value=total, unit="cases", trend="stable"),
            PopulationIndicator(name="unique_conditions", value=len(rows), unit="conditions"),
        ]

    def health_status_summary(self, governorate: str | None = None) -> dict[str, Any]:
        return {
            "scope": "health_status",
            "governorate": governorate,
            "indicators": [
                {"name": "life_expectancy", "value": None, "note": "Requires death registry integration"},
                {"name": "healthy_life_expectancy", "value": None, "note": "Requires death registry integration"},
            ],
        }

    def demographic_analysis(self, governorate: str | None = None) -> dict[str, Any]:
        dims = self._warehouse.get_dimension("hd_wh_dim_patient")
        patients = dims
        if governorate:
            patients = [p for p in patients if p.get("governorate") == governorate]

        age_groups: dict[str, int] = {}
        gender_dist: dict[str, int] = {}
        for p in patients:
            ag = p.get("age_group", "unknown")
            age_groups[ag] = age_groups.get(ag, 0) + 1
            g = p.get("gender", "unknown")
            gender_dist[g] = gender_dist.get(g, 0) + 1

        return {
            "total_population": len(patients),
            "age_distribution": age_groups,
            "gender_distribution": gender_dist,
            "governorate": governorate,
        }


class MaternalHealthAnalytics:
    def __init__(self, warehouse: WarehouseService | None = None):
        self._warehouse = warehouse or WarehouseService()

    def maternal_mortality_ratio(self, governorate: str | None = None, year: int | None = None) -> dict[str, Any]:
        return {
            "scope": "maternal_mortality",
            "governorate": governorate,
            "year": year,
            "note": "Requires death registry with cause-of-death coding",
            "requires_integration": True,
        }

    def antenatal_coverage(self, governorate: str | None = None) -> dict[str, Any]:
        return {
            "scope": "antenatal_coverage",
            "governorate": governorate,
            "note": "Requires encounter data with antenatal coding",
        }

    def facility_delivery_rate(self, governorate: str | None = None) -> dict[str, Any]:
        query = WarehouseQuery(
            dimensions=["encounter_type"],
            measures=["encounter_type"],
            filters={"encounter_type": "delivery"},
            group_by=["encounter_type"],
        )
        if governorate:
            query.filters["governorate"] = governorate
        result = self._warehouse.query(query)
        return {"scope": "facility_delivery_rate", "governorate": governorate, "results": result}


class ChildHealthAnalytics:
    def __init__(self, warehouse: WarehouseService | None = None):
        self._warehouse = warehouse or WarehouseService()

    def under_five_mortality(self, governorate: str | None = None) -> dict[str, Any]:
        return {
            "scope": "under_five_mortality",
            "governorate": governorate,
            "note": "Requires death registry integration",
            "requires_integration": True,
        }

    def infant_mortality_rate(self, governorate: str | None = None) -> dict[str, Any]:
        return {
            "scope": "infant_mortality",
            "governorate": governorate,
            "note": "Requires death registry with age-at-death coding",
            "requires_integration": True,
        }

    def malnutrition_prevalence(self, governorate: str | None = None) -> dict[str, Any]:
        query = WarehouseQuery(
            dimensions=["encounter_type"],
            measures=["diagnosis_count"],
            filters={"encounter_type": "malnutrition"},
            group_by=["encounter_type"],
        )
        if governorate:
            query.filters["governorate"] = governorate
        result = self._warehouse.query(query)
        return {"scope": "malnutrition", "governorate": governorate, "results": result}


class NCDAnalytics:
    def __init__(self, warehouse: WarehouseService | None = None):
        self._warehouse = warehouse or WarehouseService()

    def diabetes_prevalence(self, governorate: str | None = None) -> dict[str, Any]:
        query = WarehouseQuery(
            dimensions=["encounter_type"],
            measures=["diagnosis_count"],
            filters={"encounter_type": "diabetes"},
            group_by=["encounter_type"],
        )
        if governorate:
            query.filters["governorate"] = governorate
        result = self._warehouse.query(query)
        return {"scope": "diabetes_prevalence", "governorate": governorate, "results": result}

    def hypertension_prevalence(self, governorate: str | None = None) -> dict[str, Any]:
        query = WarehouseQuery(
            dimensions=["encounter_type"],
            measures=["diagnosis_count"],
            filters={"encounter_type": "hypertension"},
            group_by=["encounter_type"],
        )
        if governorate:
            query.filters["governorate"] = governorate
        result = self._warehouse.query(query)
        return {"scope": "hypertension_prevalence", "governorate": governorate, "results": result}

    def cardiovascular_burden(self, governorate: str | None = None) -> dict[str, Any]:
        return {
            "scope": "cardiovascular_burden",
            "governorate": governorate,
            "note": "Requires cardiovascular registry integration",
            "requires_integration": True,
        }

    def cancer_incidence(self, governorate: str | None = None, cancer_type: str | None = None) -> dict[str, Any]:
        return {
            "scope": "cancer_incidence",
            "governorate": governorate,
            "cancer_type": cancer_type,
            "note": "Requires cancer registry integration",
            "requires_integration": True,
        }

    def ncd_risk_factors(self, governorate: str | None = None) -> dict[str, Any]:
        return {
            "scope": "ncd_risk_factors",
            "governorate": governorate,
            "indicators": ["smoking_rate", "obesity_rate", "physical_inactivity", "unhealthy_diet"],
            "note": "Requires population survey data",
        }


class CommunicableDiseaseAnalytics:
    def __init__(self, warehouse: WarehouseService | None = None):
        self._warehouse = warehouse or WarehouseService()

    def disease_incidence(self, disease: str | None = None, governorate: str | None = None) -> dict[str, Any]:
        query = WarehouseQuery(
            dimensions=["encounter_type"],
            measures=["diagnosis_count"],
            group_by=["encounter_type"],
        )
        if disease:
            query.filters["encounter_type"] = disease
        if governorate:
            query.filters["governorate"] = governorate
        result = self._warehouse.query(query)
        return {"scope": "disease_incidence", "disease": disease, "governorate": governorate, "results": result}

    def outbreak_monitoring(self, region: str | None = None) -> dict[str, Any]:
        return {
            "scope": "outbreak_monitoring",
            "region": region,
            "note": "Delegates to epidemiology intelligence for real-time monitoring",
            "requires_integration": True,
        }

    def notifiable_disease_reporting(self, disease: str | None = None) -> dict[str, Any]:
        return {
            "scope": "notifiable_disease_reporting",
            "disease": disease,
            "note": "Requires notifiable disease surveillance integration",
        }


class VaccinationAnalytics:
    def __init__(self, warehouse: WarehouseService | None = None):
        self._warehouse = warehouse or WarehouseService()

    def coverage_rates(
        self,
        vaccine: str | None = None,
        governorate: str | None = None,
        age_group: str | None = None,
    ) -> dict[str, Any]:
        query = WarehouseQuery(
            dimensions=["encounter_type"],
            measures=["diagnosis_count"],
            filters={"encounter_type": "vaccination"},
            group_by=["encounter_type"],
        )
        if vaccine:
            query.filters["vaccine_type"] = vaccine
        if governorate:
            query.filters["governorate"] = governorate
        result = self._warehouse.query(query)
        return {
            "scope": "vaccination_coverage",
            "vaccine": vaccine,
            "governorate": governorate,
            "age_group": age_group,
            "results": result,
        }

    def immunization_schedule_compliance(self, governorate: str | None = None) -> dict[str, Any]:
        return {
            "scope": "immunization_compliance",
            "governorate": governorate,
            "note": "Requires immunization registry integration",
        }

    def vaccine_effectiveness(self, vaccine: str) -> dict[str, Any]:
        return {
            "scope": "vaccine_effectiveness",
            "vaccine": vaccine,
            "note": "Requires epidemiological study design integration",
        }


class MentalHealthAnalytics:
    def __init__(self, warehouse: WarehouseService | None = None):
        self._warehouse = warehouse or WarehouseService()

    def prevalence(self, condition: str | None = None, governorate: str | None = None) -> dict[str, Any]:
        query = WarehouseQuery(
            dimensions=["encounter_type"],
            measures=["diagnosis_count"],
            filters={"encounter_type": condition or "mental_health"},
            group_by=["encounter_type"],
        )
        if governorate:
            query.filters["governorate"] = governorate
        result = self._warehouse.query(query)
        return {"scope": "mental_health_prevalence", "condition": condition, "governorate": governorate, "results": result}

    def suicide_rates(self, governorate: str | None = None) -> dict[str, Any]:
        return {
            "scope": "suicide_rates",
            "governorate": governorate,
            "note": "Requires death registry with cause-of-death coding",
            "requires_integration": True,
        }

    def service_coverage(self, governorate: str | None = None) -> dict[str, Any]:
        return {
            "scope": "mental_health_service_coverage",
            "governorate": governorate,
            "indicators": ["psychiatrists_per_capita", "psychologists_per_capita", "beds_per_capita"],
        }
