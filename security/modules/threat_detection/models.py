from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ThreatEvent(BaseModel):
    event_id: str = ""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    threat_type: str = ""
    severity: str = "MEDIUM"
    source: str = ""
    description: str = ""
    indicators: List[str] = Field(default_factory=list)
    mitre_attack_id: Optional[str] = None
    confidence_score: float = 0.5


class DetectionRule(BaseModel):
    rule_id: str = ""
    name: str = ""
    description: str = ""
    severity: str = "MEDIUM"
    mitre_mapping: Optional[str] = None
    detection_logic: Dict[str, Any] = Field(default_factory=dict)
    response_actions: List[str] = Field(default_factory=list)


class SecurityMetric(BaseModel):
    metric_name: str = ""
    value: float = 0.0
    unit: str = "count"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    labels: Dict[str, str] = Field(default_factory=dict)
    source_module: str = ""
