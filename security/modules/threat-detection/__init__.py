GSF-019: Threat Detection Module — Threat detection and monitoring.

Provides real-time threat detection and security monitoring for the
GULA platform including anomaly detection, behavioral analytics,
SIEM integration, alert correlation, and automated incident
response triggers. Monitors platform activity for indicators of
compromise (IOCs) and indicators of attack (IOAs).

Note:
    This module lives in the "threat-detection" directory on the filesystem
    but is imported using the underscore alias:
        from security.modules.threat_detection import ThreatDetector

Exports:
    ThreatDetector: Core threat detection engine
    AnomalyDetector: ML-based behavioral anomaly detection
    SiemConnector: SIEM integration (ELK, Splunk, Wazuh)
    AlertCorrelator: Alert correlation and deduplication
    IocManager: Indicator of Compromise management
    AutomatedResponder: Automated incident response triggers
"""

from security.modules.threat_detection.engine import ThreatDetector
from security.modules.threat_detection.anomaly import AnomalyDetector
from security.modules.threat_detection.siem import SiemConnector
from security.modules.threat_detection.correlation import AlertCorrelator
from security.modules.threat_detection.ioc import IocManager
from security.modules.threat_detection.response import AutomatedResponder

__all__ = [
    "ThreatDetector",
    "AnomalyDetector",
    "Si emConnector",
    "AlertCorrelator",
    "IocManager",
    "AutomatedResponder",
]
