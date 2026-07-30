"""GSF-019: Threat Detection Module — Threat detection and monitoring.

Provides real-time threat detection and security monitoring for the
GULA platform including anomaly detection, behavioral analytics,
and automated incident response.

The primary implementation lives in threat_detection/ module:
- engine.py — Core threat detection engine
- risk_engine.py — Risk scoring engine
- dashboard.py — Security metrics and dashboard
"""

from security.modules.threat_detection.engine import ThreatDetectionEngine
from security.modules.threat_detection.risk_engine import RiskEngine
from security.modules.threat_detection.dashboard import SecurityMetricsCollector

__all__ = [
    "ThreatDetectionEngine",
    "RiskEngine",
    "SecurityMetricsCollector",
]
