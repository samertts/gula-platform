# Incident Response Policy

## 1. Purpose

Establish a standardized incident response process for the GULA National
Healthcare Platform to detect, respond to, and recover from security incidents
while protecting patient health information (PHI) and ensuring regulatory
compliance.

## 2. Scope

This policy applies to all security incidents affecting the GULA platform
including data breaches, system compromises, unauthorized access, malware,
denial of service, and policy violations.

## 3. Incident Classification

### 3.1 Severity Levels

| Severity | Impact | Response Time | Examples |
|----------|--------|---------------|----------|
| **CRITICAL** | Widespread PHI exposure or system unavailability | Immediate (< 15 min) | Data breach, ransomware, full system compromise |
| **HIGH** | Limited PHI exposure or significant service degradation | < 60 min | Unauthorized access, privilege escalation, DoS |
| **MEDIUM** | No PHI exposure, limited impact | < 8 hours | Policy violation, configuration drift, failed scan |
| **LOW** | Minor security concern, no data risk | < 24 hours | User error, informational finding |

### 3.2 Incident Types

- **Unauthorized Access**: Suspicious logins, credential misuse
- **Data Breach**: PHI exposure, data exfiltration
- **Malware**: Ransomware, virus, trojan detection
- **Denial of Service**: DDoS, resource exhaustion
- **Privilege Escalation**: Unauthorized privilege gain
- **Policy Violation**: Security policy non-compliance
- **Supply Chain**: Compromised dependency or vendor
- **Physical**: Data center breach, device theft

## 4. Response Procedures

### 4.1 CRITICAL Response

1. **Detect (0-15 min)**
   - Automated alert triggers incident ticket
   - Security team notified via PagerDuty and Slack
   - CISO and on-call engineer assembled

2. **Contain (15-60 min)**
   - Isolate affected systems from network
   - Block compromised accounts
   - Preserve forensic evidence (memory, disk, logs)
   - Activate incident communication channel

3. **Eradicate (1-4 hours)**
   - Remove threat artifacts
   - Patch vulnerabilities
   - Rotate all affected credentials and keys
   - Verify containment effectiveness

4. **Recover (4-24 hours)**
   - Restore from verified clean backups
   - Validate system integrity
   - Gradual service restoration
   - Continuous monitoring post-recovery

5. **Post-Incident (24-72 hours)**
   - Root cause analysis
   - Lessons learned documentation
   - Policy and control updates
   - Regulatory notification if required

### 4.2 HIGH Response

1. Acknowledge within 60 minutes
2. Investigate using available logs and telemetry
3. Implement temporary controls
4. Determine if escalation to CRITICAL is needed
5. Document findings and close within 24 hours

### 4.3 MEDIUM Response

1. Assign to security analyst within 8 hours
2. Investigate and document findings
3. Implement remediation
4. Close within 5 business days

### 4.4 LOW Response

1. Log and track in issue tracker
2. Address during next maintenance window
3. Close within 30 days

## 5. Escalation Criteria

- Any PHI exposure → automatically CRITICAL
- Incident involving national infrastructure → escalate to CISO
- Inability to contain within 2 hours → escalate
- Legal or regulatory notification required → escalate to CISO + DPO

## 6. Communication Plan

| Audience | Method | Timing |
|----------|--------|--------|
| Security Team | Slack #security-alerts + PagerDuty | Immediate |
| CISO | Phone call | < 15 min |
| Executive Team | Email + briefing | < 2 hours |
| Legal/DPO | Email + phone | < 2 hours for PHI |
| Regulatory (MoH) | Official notification | < 72 hours (per law) |
| Affected Patients | Letter + phone | < 30 days (per HIPAA) |
| Public | Press release (if required) | Coordinated with PR |

## 7. Forensic Requirements

- Preserve chain of custody for all evidence
- Capture memory, disk, network logs before remediation
- Use write-blockers when analyzing forensic images
- Document all actions with timestamps and rationale
- Engage independent forensic team for CRITICAL incidents

## 8. Post-Incident Review

- Schedule within 5 business days of resolution
- Document: timeline, root cause, response effectiveness, improvements
- Update incident response runbook with lessons learned
- Test improved controls within 30 days

## 9. Healthcare Data Breach Notification

Per Iraqi MoH regulations and HIPAA:
1. Determine breach scope and affected individuals within 72 hours
2. Notify Iraqi Ministry of Health within 72 hours of confirmation
3. Notify affected patients within 30 days
4. Provide breach details: what happened, PHI involved, mitigation steps
5. Offer credit monitoring if financial data involved
6. Document notification process for audit

## 10. Review

This policy is reviewed quarterly and updated after any major incident.
