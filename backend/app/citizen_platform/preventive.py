from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

from app._compat import UTC

logger = logging.getLogger("gula.citizen.preventive")


@dataclass
class VaccinationRecord:
    id: str = ""
    citizen_id: str = ""
    vaccine_name: str = ""
    vaccine_name_ar: str = ""
    dose_number: int = 1
    total_doses: int = 1
    date_administered: str = ""
    next_due_date: str = ""
    facility_name: str = ""
    administered_by: str = ""
    lot_number: str = ""
    status: str = "completed"
    notes: str = ""


@dataclass
class ScreeningRecommendation:
    screening_id: str = ""
    citizen_id: str = ""
    screening_type: str = ""
    screening_name: str = ""
    frequency_months: int = 12
    last_performed: str = ""
    next_due: str = ""
    status: str = "due"
    risk_level: str = "normal"


class VaccinationService:
    def __init__(self) -> None:
        self._records: dict[str, list[VaccinationRecord]] = {}

    def get_vaccination_history(self, citizen_id: str) -> list[VaccinationRecord]:
        records = self._records.get(citizen_id, [])
        records.sort(key=lambda r: r.date_administered, reverse=True)
        return records

    def add_vaccination_record(self, citizen_id: str, record: VaccinationRecord) -> None:
        if citizen_id not in self._records:
            self._records[citizen_id] = []
        self._records[citizen_id].append(record)

    def get_upcoming_vaccinations(self, citizen_id: str) -> list[VaccinationRecord]:
        records = self._records.get(citizen_id, [])
        today = date.today().isoformat()
        return [r for r in records if r.next_due_date and r.next_due_date >= today and r.status == "completed"]

    def get_missed_vaccinations(self, citizen_id: str) -> list[VaccinationRecord]:
        records = self._records.get(citizen_id, [])
        today = date.today().isoformat()
        return [r for r in records if r.next_due_date and r.next_due_date < today and r.status != "completed"]


class ScreeningService:
    def __init__(self) -> None:
        self._screenings: dict[str, list[ScreeningRecommendation]] = {}

    def get_due_screenings(self, citizen_id: str) -> list[ScreeningRecommendation]:
        return [s for s in self._screenings.get(citizen_id, []) if s.status == "due"]

    def get_overdue_screenings(self, citizen_id: str) -> list[ScreeningRecommendation]:
        return [s for s in self._screenings.get(citizen_id, []) if s.status == "overdue"]

    def complete_screening(self, citizen_id: str, screening_id: str) -> bool:
        screenings = self._screenings.get(citizen_id, [])
        for s in screenings:
            if s.screening_id == screening_id:
                s.status = "completed"
                s.last_performed = date.today().isoformat()
                from dateutil.relativedelta import relativedelta
                next_date = date.today() + relativedelta(months=s.frequency_months)
                s.next_due = next_date.isoformat()
                return True
        return False

    def add_screening_recommendation(self, citizen_id: str, screening: ScreeningRecommendation) -> None:
        if citizen_id not in self._screenings:
            self._screenings[citizen_id] = []
        self._screenings[citizen_id].append(screening)

    def get_screening_summary(self, citizen_id: str) -> dict[str, Any]:
        screenings = self._screenings.get(citizen_id, [])
        return {
            "total": len(screenings),
            "completed": sum(1 for s in screenings if s.status == "completed"),
            "due": sum(1 for s in screenings if s.status == "due"),
            "overdue": sum(1 for s in screenings if s.status == "overdue"),
            "declined": sum(1 for s in screenings if s.status == "declined"),
        }


class HealthCampaignService:
    def __init__(self) -> None:
        self._campaigns: list[dict[str, Any]] = []
        self._enrollments: dict[str, list[str]] = {}

    def create_campaign(
        self,
        title: str,
        title_ar: str,
        description: str,
        campaign_type: str,
        start_date: str,
        end_date: str,
        target_audience: str = "",
    ) -> dict[str, Any]:
        campaign = {
            "id": str(uuid.uuid4()),
            "title": title,
            "title_ar": title_ar,
            "description": description,
            "campaign_type": campaign_type,
            "start_date": start_date,
            "end_date": end_date,
            "target_audience": target_audience,
            "is_active": True,
            "created_at": datetime.now(UTC).isoformat(),
        }
        self._campaigns.append(campaign)
        return campaign

    def get_active_campaigns(self) -> list[dict[str, Any]]:
        today = date.today().isoformat()
        return [
            c
            for c in self._campaigns
            if c["is_active"] and c["start_date"] <= today <= c["end_date"]
        ]

    def enroll_citizen(self, campaign_id: str, citizen_id: str) -> bool:
        if citizen_id not in self._enrollments:
            self._enrollments[citizen_id] = []
        if campaign_id in self._enrollments[citizen_id]:
            return False
        self._enrollments[citizen_id].append(campaign_id)
        return True

    def is_enrolled(self, citizen_id: str, campaign_id: str) -> bool:
        return campaign_id in self._enrollments.get(citizen_id, [])


class RiskAssessment:
    def __init__(self) -> None:
        self._assessments: dict[str, list[dict[str, Any]]] = {}

    def assess_risk(
        self,
        citizen_id: str,
        age: int = 0,
        bmi: float = 0.0,
        smoking_status: str = "never",
        family_history: list[str] | None = None,
        chronic_conditions: list[str] | None = None,
    ) -> dict[str, Any]:
        score = 0
        factors: list[str] = []

        if age > 60:
            score += 2
            factors.append("advanced_age")
        elif age > 45:
            score += 1
            factors.append("middle_age")

        if bmi > 30:
            score += 2
            factors.append("obesity")
        elif bmi > 25:
            score += 1
            factors.append("overweight")

        if smoking_status == "current":
            score += 2
            factors.append("active_smoker")
        elif smoking_status == "former":
            score += 1
            factors.append("former_smoker")

        fh = family_history or []
        if "diabetes" in fh:
            score += 1
            factors.append("family_history_diabetes")
        if "heart_disease" in fh:
            score += 2
            factors.append("family_history_heart_disease")

        cc = chronic_conditions or []
        if "diabetes" in cc:
            score += 2
            factors.append("diabetes")
        if "hypertension" in cc:
            score += 2
            factors.append("hypertension")

        risk_level = "low"
        if score >= 5:
            risk_level = "high"
        elif score >= 3:
            risk_level = "moderate"

        assessment = {
            "id": str(uuid.uuid4()),
            "citizen_id": citizen_id,
            "score": score,
            "risk_level": risk_level,
            "factors": factors,
            "assessed_at": datetime.now(UTC).isoformat(),
        }
        if citizen_id not in self._assessments:
            self._assessments[citizen_id] = []
        self._assessments[citizen_id].append(assessment)
        return assessment

    def get_latest_assessment(self, citizen_id: str) -> dict[str, Any] | None:
        assessments = self._assessments.get(citizen_id, [])
        if not assessments:
            return None
        return max(assessments, key=lambda a: a["assessed_at"])

    def get_assessment_history(self, citizen_id: str) -> list[dict[str, Any]]:
        assessments = self._assessments.get(citizen_id, [])
        assessments.sort(key=lambda a: a["assessed_at"], reverse=True)
        return assessments
