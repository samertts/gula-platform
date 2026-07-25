# GSF Incident Response Plan

**Document ID**: GSF-IR-001  
**Version**: 1.0.0  
**Effective Date**: 2026-07-25  
**Classification**: Confidential — GULA Security Team  

---

## 1. Purpose

This Incident Response Plan (IRP) defines the procedures for detecting, analyzing,
containing, eradicating, and recovering from security incidents affecting the
GULA National Healthcare Platform. The plan is aligned with NIST SP 800-61 Rev 2
and incorporates requirements from HIPAA, GDPR, and Iraqi national healthcare
regulations.

---

## 2. IR Team Structure

### 2.1 Core IR Team

| Role | Assignment | Primary | Secondary |
|------|------------|---------|-----------|
| IR Lead | Overall incident coordination | SOC Lead | Security Lead |
| Technical Lead | Technical analysis and containment | Platform Eng Lead | K8s Lead |
| Communications Lead | Internal/external communications | Comms Lead | CISO |
| Legal Counsel | Legal and regulatory matters | Legal Team | CISO |
| Forensic Analyst | Digital forensics and evidence | Security Team | External Consultant |
| Compliance Officer | Regulatory notification obligations | Compliance Lead | Privacy Officer |
| Clinical Liaison | Clinical impact assessment | Chief Medical Info Officer | Clinical Safety Officer |
| HR Representative | Personnel-related incidents | HR Director | — |

### 2.2 Extended Team

| Role | When Engaged |
|------|-------------|
| National CERT (Iraq) | Critical incidents, nation-state actors |
| External Forensics | Advanced investigation, chain-of-custody |
| Cloud Provider (AWS/on-prem) | Infrastructure-level incidents |
| Vendor Security Teams | Incidents involving third-party software |
| Law Enforcement | Criminal activity, national security |
| Iraqi Ministry of Health | Healthcare-specific incidents, patient safety |

---

## 3. Incident Classification

### 3.1 Severity Levels

| Level | Name | Definition | Response Time |
|-------|------|------------|---------------|
| SEV-1 | Critical | Active breach, confirmed PHI exfiltration, system-wide outage, ransomware | Immediate (15 min) |
| SEV-2 | High | Suspected breach, malware outbreak, single-service compromise, privilege escalation | 1 hour |
| SEV-3 | Medium | Policy violation, scanning activity, phishing campaign, non-critical malware | 4 hours |
| SEV-4 | Low | Phishing email (single), failed login anomalies, configuration deviation | 24 hours |
| SEV-5 | Informational | Security improvement opportunity, minor observation | Next business day |

### 3.2 Incident Types

| Type | Code | Examples |
|------|------|----------|
| Unauthorized Access | IA | Account compromise, credential theft, session hijacking |
| Malware | MAL | Ransomware, trojan, cryptominer |
| Denial of Service | DOS | DDoS, resource exhaustion, application DoS |
| Data Breach | DB | PHI exfiltration, unauthorized data access |
| Policy Violation | PV | Security policy non-compliance, unauthorized changes |
| Social Engineering | SE | Phishing, spear-phishing, vishing, impersonation |
| Physical Security | PS | Unauthorized physical access, theft |
| Insider Threat | IT | Malicious insider activity, data exfiltration |
| Supply Chain | SC | Compromised dependency, vendor incident |
| Compliance | CMP | Regulatory violation discovery |

---

## 4. Incident Response Phases

### 4.1 Preparation

| Activity | Owner | Frequency |
|----------|-------|-----------|
| Maintain IR playbooks | IR Lead | Quarterly review |
| Conduct tabletop exercises | IR Lead | Quarterly |
| Deploy detection tools | SOC Lead | Continuous |
| Maintain contact lists | IR Lead | Monthly review |
| Train all staff on reporting | Security Lead | Annually |
| Prepare forensic workstations | Forensic Analyst | Monthly check |
| Maintain evidence repository | Forensic Analyst | Continuous |
| Legal hold process documentation | Legal Counsel | Annually |

### 4.2 Detection & Analysis

```
┌──────────────┐
│ Alert/Report │  ← Automated alert, user report, SOC observation
└──────┬───────┘
       ▼
┌──────────────────┐
│ Initial Triage   │  ← 15 min (SEV-1), 60 min (SEV-2)
│ ─ Verify alert   │
│ ─ Classify       │
│ ─ Assign level   │
└──────┬───────────┘
       ▼
┌──────────────────┐
│ Containment      │  ← Immediate
│ Decision ────────┤
│ Isolate / run    │
└──────────────────┘
```

#### Detection Sources

- **GSF-019 (Threat Detection)**: Anomaly detection alerts, SIEM correlation
- **GSF-006 (Audit)**: Audit log anomalies, chain verification failures
- **GSF-020 (Integrity)**: FIM alerts, configuration drift alerts
- **WAF/CDN**: Web attack detection, rate limit violations
- **Endpoint Protection**: EDR alerts, malware detection
- **Cloud Provider**: CloudTrail, GuardDuty, Security Hub
- **User Reports**: Phishing reports, suspicious activity reports
- **Third Party**: Vendor security notifications, threat intelligence feeds

#### Analysis Activities

1. Collect all relevant logs (sources, timestamps, affected systems)
2. Determine scope (systems, users, data affected)
3. Identify the attack vector and entry point
4. Determine if the incident is active or contained
5. Assess data impact (PHI exposure assessment)
6. Document all findings with timestamps

### 4.3 Containment

| Action | SEV-1 | SEV-2 | SEV-3 |
|--------|-------|-------|-------|
| Isolate affected system from network | Immediate | 1 hour | 4 hours |
| Revoke compromised credentials | Immediate | 30 min | 2 hours |
| Block malicious IP/domain | Immediate | 15 min | 1 hour |
| Take snapshot for forensics | Immediate | 1 hour | 4 hours |
| Apply temporary WAF rules | Immediate | 30 min | 2 hours |
| Disable compromised user accounts | Immediate | 15 min | 1 hour |
| Activate DR site (if needed) | 1 hour | — | — |
| Preserve evidence (chain of custody) | Immediate | 1 hour | 4 hours |

#### Containment Strategies

- **Short-term**: Isolate affected systems, block network access, suspend accounts
- **Long-term**: Apply patches, rebuild from known-good image, rotate all credentials
- **Forensic**: Full memory capture, disk imaging, network capture before containment

### 4.4 Eradication

| Activity | Owner | Timeline |
|----------|-------|----------|
| Remove malware/backdoors | Technical Lead | 4 hours (SEV-1) |
| Patch vulnerabilities | Technical Lead | 24 hours |
| Rotate all affected credentials | Security Lead | 4 hours |
| Rebuild compromised systems | Platform Eng | 24 hours |
| Verify complete removal | Forensic Analyst | 48 hours |
| Update detection signatures | SOC Lead | 24 hours |
| Implement additional controls | Security Lead | 7 days |

### 4.5 Recovery

| Activity | Owner | Timeline |
|----------|-------|----------|
| Restore from clean backup | Platform Eng | 4 hours |
| Verify data integrity | Forensic Analyst | 4 hours |
| Gradual service restoration | Platform Eng | 8 hours |
| Monitor for recurrence | SOC Lead | 7 days |
| Re-enable normal operations | IR Lead | After monitoring |
| Communicate service status | Comms Lead | Continuous |

### 4.6 Post-Mortem

| Activity | Timeline | Deliverable |
|----------|----------|-------------|
| Internal post-mortem meeting | 5 business days | Draft report |
| Root cause analysis | 5 business days | RCA document |
| Lessons learned document | 10 business days | Lessons learned |
| Remediation plan | 10 business days | Action items with owners |
| Update playbooks | 15 business days | Updated playbooks |
| Executive summary | 15 business days | Executive summary |
| Regulatory notification (if required) | Per regulatory timeline | Notification letter |

---

## 5. Communication Plan

### 5.1 Internal Communications

| Audience | Channel | Timing |
|----------|---------|--------|
| IR Team | Secure chat (Signal/Mattermost) | Immediate |
| CISO | Phone + Secure chat | 15 min (SEV-1/2) |
| Executive Team | Phone + Email | 1 hour (SEV-1) |
| Engineering Team | Slack #security-incidents | 1 hour |
| All Staff | Email + Slack | 4 hours (if applicable) |
| Board of Directors | Email + Phone | 24 hours (SEV-1) |

### 5.2 External Communications

| Audience | Channel | Timing | Template |
|----------|---------|--------|----------|
| Affected patients | Email/Letter | 72 hours (minimum) | IR-COMM-001 |
| Iraqi MOH | Phone + Formal letter | 24 hours (SEV-1) | IR-COMM-002 |
| Iraqi CERT | Phone + Email | 24 hours (SEV-1/2) | IR-COMM-003 |
| Regulatory bodies (HIPAA/GDPR) | Formal notification | Per regulation | IR-COMM-004 |
| Law enforcement | Phone + Formal | Per decision | IR-COMM-005 |
| Media (if public) | Press release | Per CISO approval | IR-COMM-006 |
| Partners/vendors | Email | 48 hours | IR-COMM-007 |

### 5.3 Communication Guidelines

- All external communications must be approved by CISO + Legal Counsel
- Single spokesperson designated (Comms Lead or CISO)
- No technical details shared before forensic completion
- Transparency without compromising investigation
- Regular updates every 4 hours during active incidents

---

## 6. Escalation Matrix

```
                       CISO
                         │
                    ┌────┴────┐
                    │         │
              IR Lead      Legal Counsel
                 │              │
           ┌─────┼─────┐        │
           │     │     │        │
        Tech    Foren  Comms    │
        Lead    sics   Lead     │
           │     │              │
           └─────┼──────────────┘
                 │
           ┌─────┴─────┐
           │           │
        External      External
        Forensics     Legal
```

### Escalation Triggers

| Trigger | Escalate To |
|---------|-------------|
| Service unavailable > 15 min | Platform Eng Lead |
| PHI confirmed exfiltrated | CISO + Legal + MOH |
| Nation-state actor suspected | CISO + Iraqi CERT |
| Ransomware with patient impact | CISO + Executive Team |
| Law enforcement required | CISO + Legal |
| Media inquiry received | CISO + Comms Lead |

---

## 7. Forensics Procedures

### 7.1 Evidence Collection

| Evidence Type | Collection Method | Tooling |
|---------------|------------------|---------|
| Memory dump | Live acquisition | LiME, AVML, MemProcFS |
| Disk image | Forensic image | dd, FTK Imager, Guymager |
| Network traffic | PCAP capture | tcpdump, Wireshark, netsniff-ng |
| Logs | Centralized logs | ELK, Splunk |
| Container logs | kubectl logs + sidecar | Fluentd, Loki |
| Cloud trails | API pull | AWS CloudTrail, Azure Monitor |
| Process list | ps/tasklist output | Volatility, Rekall |

### 7.2 Chain of Custody

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ Collector    │────►│ Custodian    │────►│ Analyst      │
│ (Name, time) │     │ (Name, time) │     │ (Name, time) │
└──────────────┘     └──────────────┘     └──────────────┘
```

Each transfer must be documented with:
- Evidence ID (EVID-YYYYMMDD-NNN)
- Description of evidence
- Collector name, date, time
- Hash of evidence (SHA-256)
- Transfer history (each transfer must be signed)
- Storage location
- Access log

### 7.3 Forensic Environment

- Dedicated forensic workstation (not connected to production network)
- Write blockers for disk imaging
- Immutable storage for evidence
- Time synchronization (NTP)
- Documented forensic tools and versions

---

## 8. Integration with GULA Runbook

The IR plan integrates with the existing GULA incident runbook through:

1. **Alert forwarding**: GSF-019 sends IR-triggered alerts to the central runbook
2. **Unified ticketing**: All IR activities tracked in existing incident management system
3. **Shared escalation**: GULA runbook escalation paths extended with IR-specific roles
4. **Automated containment**: Pre-approved automated responses for common scenarios
5. **Post-mortem integration**: Findings feed into GULA continuous improvement process

---

## 9. Healthcare Data Breach Notification

### 9.1 Regulatory Timelines

| Regulation | Notification Trigger | Deadline | Notification To |
|------------|---------------------|----------|-----------------|
| Iraqi MOH Regulations | PHI breach confirmed | 24 hours | Iraqi Ministry of Health |
| HIPAA Breach Rule | PHI breach affecting > 500 patients | 60 days | HHS OCR + Affected individuals |
| HIPAA Breach Rule | PHI breach affecting < 500 patients | Annual report | HHS OCR |
| GDPR | Personal data breach | 72 hours | Relevant DPA |
| GDPR | High risk to individuals | Without delay | Affected data subjects |
| Iraqi Data Protection Law | Personal data breach | 72 hours | National Data Protection Authority |

### 9.2 Breach Notification Content

1. Description of the breach
2. Date of breach and date of discovery
3. Type of data involved (PHI/PII categories)
4. Steps individuals should take to protect themselves
5. Actions GULA is taking in response
6. Contact information for questions
7. Credit monitoring offer (if applicable)

---

## 10. Playbook Index

| Playbook ID | Incident Type | Last Updated |
|-------------|---------------|-------------|
| IR-PB-001 | Ransomware | 2026-07-25 |
| IR-PB-002 | PHI Data Breach | 2026-07-25 |
| IR-PB-003 | Account Compromise | 2026-07-25 |
| IR-PB-004 | DDoS Attack | 2026-07-25 |
| IR-PB-005 | Malware Outbreak | 2026-07-25 |
| IR-PB-006 | Insider Threat | 2026-07-25 |
| IR-PB-007 | Supply Chain Incident | 2026-07-25 |
| IR-PB-008 | Physical Security | 2026-07-25 |
| IR-PB-009 | Cloud Security Incident | 2026-07-25 |
| IR-PB-010 | Social Engineering | 2026-07-25 |

---

## 11. Testing and Training

| Exercise Type | Frequency | Participants |
|---------------|-----------|-------------|
| Tabletop exercise | Quarterly | IR Team + Stakeholders |
| Simulated phishing | Monthly | All staff |
| Malware simulation | Semi-annually | SOC Team |
| Full-scale drill | Annually | All teams |
| DR failover test | Semi-annually | Platform Engineering |
| Forensic exercise | Annually | Forensic team |

---

## 12. References

- NIST SP 800-61 Rev 2: Computer Security Incident Handling Guide
- NIST SP 800-86: Guide to Integrating Forensic Techniques into Incident Response
- HIPAA Breach Notification Rule (45 CFR §§ 164.400-414)
- GDPR Articles 33-34: Personal Data Breach Notification
- Iraqi MOH Circular 47/2023: Healthcare Cybersecurity Incident Reporting
- FIRST PSIRT Services Framework
- OASIS CACAO Security Playbooks Standard

---

**Document History**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-07-25 | GULA Security Team | Initial IR plan |
