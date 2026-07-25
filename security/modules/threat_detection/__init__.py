GSF-008: Threat Detection Module — Security event monitoring and risk analysis.

Note: The directory is `threat-detection/` but Python imports use `threat_detection`.

Exports:
    ThreatEvent: Security threat event model
    DetectionRule: Detection rule model with MITRE ATT&CK mapping
    SecurityMetric: Security metric model for monitoring
    ThreatDetectionEngine: Multi-source event correlation and threat detection
    RiskEngine: Dynamic risk scoring and aggregation
    SecurityMetricsCollector: Security KPI collection and dashboard data
"""

from security.modules.threat_detection.models import ThreatEvent, DetectionRule, SecurityMetric
from security.modules.threat_detection.engine import ThreatDetectionEngine
from security.modules.threat_detection.risk_engine import RiskEngine
from security.modules.threat_detection.dashboard import SecurityMetricsCollector

__all__ = [
    "ThreatEvent",
    "DetectionRule",
    "SecurityMetric",
    "ThreatDetectionEngine",
    "RiskEngine",
    "SecurityMetricsCollector",
]
