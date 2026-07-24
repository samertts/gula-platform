from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app._compat import UTC
from app.ehr.models.medication import MedicationStatement

logger = logging.getLogger("gula.citizen.medications")


@dataclass
class MedicationSummary:
    medication_id: str = ""
    medication_name: str = ""
    medication_name_ar: str = ""
    dosage_text: str = ""
    frequency: str = ""
    route: str = ""
    status: str = ""
    date_started: str = ""
    prescriber: str = ""


@dataclass
class DrugInteraction:
    severity: str = ""
    description: str = ""
    medications: list[str] = field(default_factory=list)
    recommendation: str = ""


class MedicationService:
    def __init__(self) -> None:
        self._statements: dict[str, list[MedicationStatement]] = {}

    def get_active_medications(self, citizen_id: str) -> list[MedicationSummary]:
        statements = self._statements.get(citizen_id, [])
        active = [s for s in statements if s.status == "active"]
        return [
            MedicationSummary(
                medication_id=s.id,
                medication_name=s.medication_name,
                medication_name_ar=s.medication_name_ar or "",
                dosage_text=s.dosage_text or "",
                frequency=s.frequency or "",
                route=s.route or "",
                status=s.status,
                date_started=s.date_started.isoformat() if s.date_started else "",
                prescriber=str(s.practitioner_id) if s.practitioner_id else "",
            )
            for s in active
        ]

    def get_medication_history(self, citizen_id: str) -> list[MedicationSummary]:
        statements = self._statements.get(citizen_id, [])
        return [
            MedicationSummary(
                medication_id=s.id,
                medication_name=s.medication_name,
                medication_name_ar=s.medication_name_ar or "",
                dosage_text=s.dosage_text or "",
                frequency=s.frequency or "",
                route=s.route or "",
                status=s.status,
                date_started=s.date_started.isoformat() if s.date_started else "",
            )
            for s in statements
        ]

    def add_medication_statement(self, statement: MedicationStatement) -> None:
        cid = statement.citizen_id
        if cid not in self._statements:
            self._statements[cid] = []
        self._statements[cid].append(statement)


class DrugInteractionChecker:
    _KNOWN_INTERACTIONS: dict[tuple[str, str], str] = {
        ("warfarin", "aspirin"): "high",
        ("warfarin", "ibuprofen"): "high",
        ("lisinopril", "spironolactone"): "moderate",
        ("metformin", "contrast_dye"): "moderate",
    }

    def check_interaction(
        self, medication_a: str, medication_b: str,
    ) -> DrugInteraction | None:
        key = (medication_a.lower(), medication_b.lower())
        reverse = (medication_b.lower(), medication_a.lower())
        severity = self._KNOWN_INTERACTIONS.get(key) or self._KNOWN_INTERACTIONS.get(reverse)
        if not severity:
            return None
        return DrugInteraction(
            severity=severity,
            description=f"Potential {severity}-severity interaction between {medication_a} and {medication_b}",
            medications=[medication_a, medication_b],
            recommendation="Consult prescriber before concurrent use",
        )

    def check_polypharmacy(
        self, active_medications: list[str],
    ) -> list[DrugInteraction]:
        interactions: list[DrugInteraction] = []
        for i in range(len(active_medications)):
            for j in range(i + 1, len(active_medications)):
                result = self.check_interaction(active_medications[i], active_medications[j])
                if result:
                    interactions.append(result)
        return interactions


class MedicationAdherence:
    def __init__(self) -> None:
        self._adherence: dict[str, dict[str, Any]] = {}

    def record_dose(
        self, citizen_id: str, medication_id: str, taken: bool, scheduled_time: str = "",
    ) -> None:
        key = f"{citizen_id}:{medication_id}"
        if key not in self._adherence:
            self._adherence[key] = {"taken": 0, "missed": 0, "total": 0, "history": []}
        record = self._adherence[key]
        record["total"] += 1
        if taken:
            record["taken"] += 1
        else:
            record["missed"] += 1
        record["history"].append(
            {"taken": taken, "scheduled_time": scheduled_time, "recorded_at": datetime.now(UTC).isoformat()},
        )

    def get_adherence_rate(self, citizen_id: str, medication_id: str) -> float:
        key = f"{citizen_id}:{medication_id}"
        record = self._adherence.get(key)
        if not record or record["total"] == 0:
            return 0.0
        return record["taken"] / record["total"]

    def get_adherence_summary(self, citizen_id: str) -> dict[str, Any]:
        summary: dict[str, Any] = {"medications": {}, "overall_rate": 0.0, "total_doses": 0}
        total_taken = 0
        total_doses = 0
        for key, record in self._adherence.items():
            if key.startswith(f"{citizen_id}:"):
                med_id = key.split(":", 1)[1]
                rate = record["taken"] / record["total"] if record["total"] > 0 else 0
                summary["medications"][med_id] = {
                    "adherence_rate": round(rate, 2),
                    "taken": record["taken"],
                    "missed": record["missed"],
                    "total": record["total"],
                }
                total_taken += record["taken"]
                total_doses += record["total"]
        if total_doses > 0:
            summary["overall_rate"] = round(total_taken / total_doses, 2)
        summary["total_doses"] = total_doses
        return summary
