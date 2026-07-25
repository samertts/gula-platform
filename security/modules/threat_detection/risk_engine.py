from __future__ import annotations

import json
import logging
import math
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from pydantic import BaseModel, Field

from security.modules.threat_detection.models import ThreatEvent

logger = logging.getLogger(__name__)

DEFAULT_RISK_WEIGHTS: Dict[str, float] = {
    "severity_critical": 10.0,
    "severity_high": 5.0,
    "severity_medium": 2.0,
    "severity_low": 1.0,
    "repetition": 0.5,
    "temporal_decay_hours": 24.0,
    "mitre_impact": 1.5,
    "confidence": 1.0,
}

RISK_THRESHOLDS: Dict[str, float] = {
    "low": 0.0,
    "medium": 20.0,
    "high": 50.0,
    "critical": 80.0,
}


class EntityRisk(BaseModel):
    entity_id: str
    entity_type: str
    current_score: float = 0.0
    base_score: float = 0.0
    max_score: float = 0.0
    score_history: List[Dict[str, Any]] = Field(default_factory=list)
    last_event: Optional[datetime] = None
    event_count: int = 0
    risk_level: str = "low"


class RiskAssessment(BaseModel):
    assessment_id: str = ""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    overall_score: float = 0.0
    risk_level: str = "low"
    entity_risks: Dict[str, EntityRisk] = Field(default_factory=dict)
    top_contributors: List[str] = Field(default_factory=list)


class RiskEngine:
    def __init__(self, weights: Optional[Dict[str, float]] = None):
        self.weights = weights or DEFAULT_RISK_WEIGHTS
        self._entity_risks: Dict[str, EntityRisk] = {}
        self._event_history: List[ThreatEvent] = []
        self._risk_history: List[Dict[str, Any]] = []

    def calculate_risk_score(self, entity_id: str, events: Optional[List[ThreatEvent]] = None) -> float:
        all_events = events or [e for e in self._event_history if e.source == entity_id]
        if not all_events:
            return 0.0

        now = datetime.now(timezone.utc)
        total_risk = 0.0
        decay_hours = self.weights.get("temporal_decay_hours", 24)

        for event in all_events:
            severity_key = f"severity_{event.severity.lower()}"
            base = self.weights.get(severity_key, 1.0)

            hours_ago = (now - event.timestamp).total_seconds() / 3600 if event.timestamp else 0
            decay = math.exp(-hours_ago / max(decay_hours, 1))
            confidence = self.weights.get("confidence", 1.0) * event.confidence_score

            mitre_impact = self.weights.get("mitre_impact", 1.0) if event.mitre_attack_id else 1.0

            score = base * decay * confidence * mitre_impact
            total_risk += score

        repetition_factor = 1.0 + (len(all_events) - 1) * self.weights.get("repetition", 0.5)
        total_risk *= min(repetition_factor, 10.0)

        return round(total_risk, 2)

    def update_entity_risk(self, entity_id: str, entity_type: str, event: ThreatEvent) -> EntityRisk:
        if entity_id not in self._entity_risks:
            self._entity_risks[entity_id] = EntityRisk(
                entity_id=entity_id,
                entity_type=entity_type,
            )

        risk = self._entity_risks[entity_id]
        score = self.calculate_risk_score(entity_id)

        risk.current_score = score
        risk.base_score = score * 0.7 + risk.base_score * 0.3
        risk.max_score = max(risk.max_score, score)
        risk.last_event = event.timestamp
        risk.event_count += 1
        risk.risk_level = self._determine_risk_level(score)

        risk.score_history.append({
            "timestamp": event.timestamp.isoformat() if event.timestamp else datetime.now(timezone.utc).isoformat(),
            "score": score,
            "event_id": event.event_id,
            "severity": event.severity,
        })

        if len(risk.score_history) > 100:
            risk.score_history = risk.score_history[-100:]

        return risk

    def process_event(self, event: ThreatEvent) -> EntityRisk:
        self._event_history.append(event)
        return self.update_entity_risk(event.source, "ip", event)

    def process_events(self, events: List[ThreatEvent]) -> Dict[str, EntityRisk]:
        for event in events:
            self.process_event(event)
        return self._entity_risks

    def aggregate_risk(self, entity_ids: Optional[List[str]] = None) -> RiskAssessment:
        entities = list(self._entity_risks.values())
        if entity_ids:
            entities = [e for e in entities if e.entity_id in entity_ids]

        if not entities:
            return RiskAssessment(assessment_id=str(uuid4()))

        total_score = sum(e.current_score for e in entities)
        avg_score = total_score / len(entities)

        top_contributors = sorted(
            entities, key=lambda e: e.current_score, reverse=True
        )[:5]

        assessment = RiskAssessment(
            assessment_id=str(uuid4()),
            overall_score=round(avg_score, 2),
            risk_level=self._determine_risk_level(avg_score),
            entity_risks={e.entity_id: e for e in entities},
            top_contributors=[e.entity_id for e in top_contributors],
        )

        self._risk_history.append({
            "timestamp": assessment.timestamp.isoformat(),
            "overall_score": assessment.overall_score,
            "risk_level": assessment.risk_level,
            "entity_count": len(entities),
        })

        return assessment

    def get_entity_risk(self, entity_id: str) -> Optional[EntityRisk]:
        return self._entity_risks.get(entity_id)

    def get_risk_threshold_action(self, score: float) -> str:
        if score >= RISK_THRESHOLDS["critical"]:
            return "IMMEDIATE_BLOCK"
        elif score >= RISK_THRESHOLDS["high"]:
            return "REQUIRE_MFA_AND_NOTIFY"
        elif score >= RISK_THRESHOLDS["medium"]:
            return "REQUIRE_MFA"
        else:
            return "MONITOR_ONLY"

    def _determine_risk_level(self, score: float) -> str:
        if score >= RISK_THRESHOLDS["critical"]:
            return "critical"
        elif score >= RISK_THRESHOLDS["high"]:
            return "high"
        elif score >= RISK_THRESHOLDS["medium"]:
            return "medium"
        else:
            return "low"

    def generate_risk_report(self, entity_id: Optional[str] = None) -> str:
        if entity_id and entity_id in self._entity_risks:
            risk = self._entity_risks[entity_id]
            assessment = self.aggregate_risk([entity_id])
            data = {
                "entity": risk.model_dump(mode="json"),
                "assessment": assessment.model_dump(mode="json"),
                "threshold_action": self.get_risk_threshold_action(risk.current_score),
            }
        else:
            assessment = self.aggregate_risk()
            data = {
                "assessment": assessment.model_dump(mode="json"),
                "risk_history": self._risk_history[-20:],
                "top_entities": sorted(
                    [(e.entity_id, e.current_score, e.risk_level) for e in self._entity_risks.values()],
                    key=lambda x: x[1], reverse=True
                )[:10],
            }

        return json.dumps(data, indent=2, default=str)

    def get_historical_trend(self, entity_id: Optional[str] = None,
                              hours: int = 168) -> Dict[str, Any]:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

        if entity_id and entity_id in self._entity_risks:
            risk = self._entity_risks[entity_id]
            history = [h for h in risk.score_history if h.get("timestamp", "") >= cutoff.isoformat()]
            return {
                "entity_id": entity_id,
                "current_score": risk.current_score,
                "trend": "increasing" if len(history) >= 2 and history[-1]["score"] > history[0]["score"] else "stable",
                "data_points": len(history),
            }

        return {
            "total_entities": len(self._entity_risks),
            "assessments": len(self._risk_history),
        }
