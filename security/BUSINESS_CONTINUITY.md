# GSF Business Continuity Plan

**Document ID**: GSF-BCP-001  
**Version**: 1.0.0  
**Effective Date**: 2026-07-25  
**Classification**: Confidential — GULA Operations  

---

## 1. Purpose

This Business Continuity Plan (BCP) ensures that the GULA National Healthcare
Platform can maintain critical healthcare services during and after a disruptive
event. The plan covers all Iraqi governorates, including regions with limited
infrastructure.

---

## 2. Critical Business Functions

| Priority | Function | RTO | Maximum Acceptable Outage | Dependency |
|----------|----------|-----|--------------------------|------------|
| P1 | Patient identity resolution and authentication | 15 min | 1 hour | Identity (GSF-001), Auth (GSF-004) |
| P1 | Patient record access (view and update) | 15 min | 1 hour | FHIR (GSF-017), Database |
| P1 | Laboratory order entry and result access | 15 min | 2 hours | FHIR, Analyzer integration |
| P1 | Medication prescribing and dispensing | 15 min | 2 hours | FHIR, Pharmacy system |
| P2 | Clinical decision support | 1 hour | 4 hours | Analytics, Rules engine |
| P2 | Billing and claims processing | 4 hours | 24 hours | Financial system |
| P2 | Patient appointment scheduling | 1 hour | 4 hours | Scheduling service |
| P3 | Administrative reporting | 8 hours | 48 hours | Data warehouse |
| P3 | Population health analytics | 24 hours | 7 days | Data warehouse, ML |
| P3 | Research data access (anonymized) | 24 hours | 7 days | Research database |

---

## 3. Business Impact Analysis

### 3.1 Impact Categories

| Category | Criteria | Weight |
|----------|----------|--------|
| Patient Safety | Direct risk to patient health | 5 |
| Regulatory | Fines, sanctions, license impact | 4 |
| Financial | Revenue loss, recovery costs | 3 |
| Reputational | Public trust, brand damage | 4 |
| Operational | Service availability, productivity | 3 |
| Legal | Litigation risk, breach liability | 4 |

### 3.2 Maximum Tolerable Downtime

| Function | MTD | Justification |
|----------|-----|---------------|
| Patient identification | 1 hour | Risk of wrong-patient errors |
| Lab results access | 2 hours | Delayed diagnosis, treatment |
| Emergency department access | 0 (24/7) | Life-critical care |
| Inpatient medication | 2 hours | Missed doses, safety risk |
| Outpatient prescriptions | 8 hours | Patient inconvenience, no critical risk |
| Administrative functions | 24 hours | Operational backlog, no patient risk |

---

## 4. Continuity Strategies

### 4.1 Technology Continuity

| Strategy | Application | Implementation |
|----------|-------------|----------------|
| Active-Passive DR | All Tier 0-1 services | DR site at geographically separate location |
| Offline-first mode | Clinical applications | Local PWA with sync, offline FHIR cache |
| Degraded mode | Non-critical features | Disable reporting, analytics during DR |
| Paper backup | Patient registration | Printed forms for manual data entry (later digitized) |
| Mobile fallback | Essential functions | SMS-based patient lookup, result notifications |

### 4.2 Process Continuity

| Scenario | Continuity Procedure | Recovery Trigger |
|----------|---------------------|-----------------|
| System unavailable < 2 hours | Staff wait, communicate delay via radio/phone | System restored |
| System unavailable 2-8 hours | Paper-based clinical workflows, triage critical cases | Extended outage declared |
| System unavailable > 8 hours | Activate DR site, deploy mobile teams | DR activation |
| Facility inaccessible | Route patients to nearest alternate facility | Facility reopened |
| Staff unavailable | Cross-training, temporary staff, governorate mutual aid | Staff restored |

### 4.3 Clinical Workarounds

| Function | Normal Operation | Workaround (System Down) | Restoration |
|----------|-----------------|--------------------------|-------------|
| Patient registration | Digital form → FHIR API | Paper form → batch upload | Data entry from forms |
| Lab order entry | Electronic order → LIS | Paper requisition → manual entry | Batch entry |
| Result viewing | Portal / FHIR API | Phone call to lab → verbal result | Electronic reconciliation |
| Medication administration | Barcode scanning → eMAR | Manual verification → paper MAR | Reconciliation |
| Patient discharge | Digital summary → ePrescription | Paper summary → fax to pharmacy | Digital upload |

---

## 5. Communication Protocols

### 5.1 Internal Communication

| Scenario | Primary Channel | Secondary Channel | Update Frequency |
|----------|-----------------|-------------------|-----------------|
| System degradation | Slack #ops-status | Phone tree | Every 30 min |
| Major outage | Slack + SMS alert | Satellite phone | Every 15 min |
| Facility closure | SMS + phone call | Radio (VHF/UHF) | Immediate + hourly |
| Staff call-out | Automated SMS + phone | Manager phone tree | Immediate |
| DR activation | DR notification system | Satellite phone | Immediate |

### 5.2 External Communication

| Stakeholder | Channel | Contact | Timing |
|-------------|---------|---------|--------|
| Ministry of Health | Secure email + phone | MOH IT director | Within 30 min of major outage |
| Healthcare facilities | SMS + radio | Facility directors | Within 1 hour |
| Patients (if affected) | SMS + app notification | Patient contact system | Within 4 hours |
| Media | Press release (approved) | Comms team | Per CISO direction |
| Partner organizations | Email + phone | Partner contacts | Within 2 hours |

### 5.3 Communication Templates

| Template ID | Purpose | Owner |
|-------------|---------|-------|
| BCP-COMM-001 | System degradation notice | Ops team |
| BCP-COMM-002 | Major outage notification | Comms lead |
| BCP-COMM-003 | Facility closure notification | Facility mgr |
| BCP-COMM-004 | Service restoration notice | Ops team |
| BCP-COMM-005 | Patient notification (general) | Patient comms |
| BCP-COMM-006 | Regulatory notification | Compliance |

---

## 6. Testing and Maintenance

### 6.1 Exercise Schedule

| Exercise Type | Frequency | Scope | Participants |
|---------------|-----------|-------|-------------|
| Tabletop exercise (discussion) | Quarterly | BCP decision-making | BCP team |
| Technology failover test | Quarterly | DR infrastructure | IT operations |
| Clinical workaround drill | Semi-annually | Paper-based workflows | Clinical staff |
| Full-scale exercise | Annually | Complete BCP activation | All teams |
| Communication test | Monthly | Alert system, phone tree | All staff |
| Offline mode simulation | Semi-annually | Isolated facility scenario | Remote facilities |

### 6.2 BCP Maintenance

| Activity | Frequency | Owner |
|----------|-----------|-------|
| BCP document review | Quarterly | BCP Lead |
| Contact list verification | Monthly | BCP Lead |
| Vendor continuity assessment | Annually | Procurement |
| Regulatory compliance check | Quarterly | Compliance |
| Training records review | Semi-annually | HR/L&D |

---

## 7. Staff Roles and Responsibilities

| Role | Responsibility |
|------|---------------|
| BCP Lead | Overall BCP coordination and decision-making |
| IT Continuity Lead | Technology recovery, DR activation |
| Clinical Continuity Lead | Clinical workarounds, patient safety |
| Facilities Lead | Site operations, physical infrastructure |
| Communications Lead | Internal/external messaging |
| HR Lead | Staff coordination, welfare |
| Logistics Lead | Supplies, equipment, transport |
| Security Lead | Physical and information security during disruption |

---

## 8. Healthcare Service Continuity Requirements

### 8.1 Minimum Service Levels

| Service | Minimum Level | Acceptable During Disruption |
|---------|---------------|------------------------------|
| Patient identification | 100% | 95% (offline matching) |
| Lab result delivery | 100% | 80% (verbal/paper within 2 hours) |
| Medication administration | 100% | 95% (manual verification) |
| Emergency care access | 100% | 100% (zero compromise) |
| Inpatient record access | 100% | 90% (paper backup) |

### 8.2 Clinical Safety During Disruption

1. Any workaround procedure must include a safety check step
2. Verbal orders require read-back verification
3. Paper records must be reconciled against digital records within 48 hours
4. Medication administration must use two-person verification (if no barcode)
5. Emergency blood transfusion uses emergency-release protocol
6. All workaround activities must be documented in incident log

---

## 9. BCP Activation and Deactivation

### 9.1 Activation Criteria

| Condition | Action |
|-----------|--------|
| Critical system unavailable > 15 min | BCP Lead notified |
| Tier 0-1 services unavailable > 1 hour | Partial BCP activation |
| Multiple services unavailable > 2 hours | Full BCP activation |
| Facility evacuation ordered | Full BCP activation |
| Staff availability < 50% | Partial BCP activation |

### 9.2 Deactivation Criteria

1. All Tier 0-1 services restored and stable for 4 hours
2. Backlog of manual/paper work processed
3. Data reconciliation complete and verified
4. No residual risk of recurrence
5. BCP Lead approves deactivation
6. Post-incident review scheduled

---

## 10. Plan Review and Governance

| Document | Owner | Review Cycle |
|----------|-------|-------------|
| Business Continuity Plan | BCP Lead | Quarterly |
| Business Impact Analysis | BCP Lead | Annually |
| Continuity Strategy Document | IT Continuity Lead | Semi-annually |
| Exercise Reports | BCP Lead | Per exercise |
| Post-incident Reviews | BCP Lead | Per incident |

---

**Document History**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-07-25 | GULA Security Team | Initial BCP |
