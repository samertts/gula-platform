# GSF-008: Threat Detection Module

Multi-source event correlation, risk scoring, and security metrics collection.

## Components

### ThreatDetectionEngine
- Multi-source event correlation
- Real-time rule evaluation (pattern, threshold, anomaly, temporal, blocklist)
- MITRE ATT&CK mapping
- Alert prioritization and deduplication
- False positive reduction
- Automated response actions via registered handlers
- Scheduled scan mode

### RiskEngine
- Dynamic risk score calculation with temporal decay
- Entity-level risk tracking (IP, user, tenant)
- Risk thresholds with automated actions (monitor, MFA, block)
- Historical risk trend analysis
- Risk reporting

### SecurityMetricsCollector
- Predefined security KPIs (auth failures, encryption coverage, MFA adoption, etc.)
- Prometheus-compatible metric output
- Time-series data storage
- Dashboard data endpoints
- Trend analysis
- Security health score calculation
