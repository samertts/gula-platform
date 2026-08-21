from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from typing import Iterable

from .baselines import BaselineEvaluation


@dataclass(frozen=True)
class ClinicalAlert:
    alert_id: str
    patient_id: int
    metric_code: str
    severity: str
    status: str
    escalation_level: str
    title: str
    explanation: str
    created_at: datetime
    dedupe_key: str
    requires_clinician_review: bool = True


class AlertOrchestrator:
    """Deterministic alert policy; no autonomous diagnosis or treatment."""

    def __init__(self, cooldown_minutes: int = 30):
        if cooldown_minutes < 1:
            raise ValueError("cooldown_minutes must be positive")
        self.cooldown = timedelta(minutes=cooldown_minutes)
        self._active: dict[str, ClinicalAlert] = {}
        self._last_seen: dict[str, datetime] = {}

    def evaluate(
        self,
        patient_id: int,
        evaluation: BaselineEvaluation,
        *,
        now: datetime | None = None,
        corroborated: bool = False,
        signal_quality: float = 1.0,
    ) -> ClinicalAlert | None:
        timestamp = now or datetime.now(timezone.utc)
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)
        if not 0 <= signal_quality <= 1:
            raise ValueError("signal_quality must be between 0 and 1")
        if not evaluation.is_anomaly or signal_quality < 0.7:
            return None

        key = self._dedupe_key(patient_id, evaluation.metric_code, evaluation.severity)
        previous = self._last_seen.get(key)
        if previous and timestamp - previous < self.cooldown:
            return None
        self._last_seen[key] = timestamp
        level = "clinician" if corroborated and evaluation.severity == "high" else "care_team"
        alert = ClinicalAlert(
            alert_id=sha256(f"{key}:{timestamp.isoformat()}".encode()).hexdigest()[:24],
            patient_id=patient_id,
            metric_code=evaluation.metric_code,
            severity=evaluation.severity,
            status="open",
            escalation_level=level,
            title=f"Personal baseline deviation: {evaluation.metric_code}",
            explanation=evaluation.explanation,
            created_at=timestamp,
            dedupe_key=key,
            requires_clinician_review=True,
        )
        self._active[alert.alert_id] = alert
        return alert

    def acknowledge(self, alert_id: str, *, actor_id: int) -> ClinicalAlert:
        alert = self._active.get(alert_id)
        if alert is None:
            raise LookupError("Alert not found")
        if actor_id <= 0:
            raise ValueError("actor_id must be positive")
        updated = ClinicalAlert(**{**alert.__dict__, "status": "acknowledged"})
        self._active[alert_id] = updated
        return updated

    def open_alerts(self, patient_id: int | None = None) -> list[ClinicalAlert]:
        alerts = [alert for alert in self._active.values() if alert.status == "open"]
        if patient_id is not None:
            alerts = [alert for alert in alerts if alert.patient_id == patient_id]
        return sorted(alerts, key=lambda item: item.created_at, reverse=True)

    @staticmethod
    def _dedupe_key(patient_id: int, metric_code: str, severity: str) -> str:
        return f"{patient_id}:{metric_code.strip().lower()}:{severity}"
