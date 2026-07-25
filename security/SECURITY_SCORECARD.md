# GSF Security Scorecard

**Document ID**: GSF-SC-001  
**Version**: 1.0.0  
**Effective Date**: 2026-07-25  

---

## 1. Scoring Methodology

### 1.1 Scoring Scale

Each security domain is scored on a scale of 0-100, where:

| Score | Rating | Meaning |
|-------|--------|---------|
| 90-100 | A (Excellent) | Exceeds requirements, best practice implemented |
| 75-89 | B (Good) | Meets requirements, minor improvements needed |
| 60-74 | C (Fair) | Partially meets requirements, gaps identified |
| 40-59 | D (Poor) | Significant gaps, action required |
| 0-39 | F (Failing) | Critical gaps, immediate action required |

### 1.2 Weight Categories

| Category | Weight | Rationale |
|----------|--------|-----------|
| Effectiveness | 40% | Can the control prevent/detect the threat? |
| Coverage | 25% | How much of the attack surface does it cover? |
| Maturity | 20% | How mature is the implementation? |
| Automation | 15% | Is the control automated or manual? |

### 1.3 Scoring Formula

```
Domain Score = (Effectiveness × 0.40) + (Coverage × 0.25) + (Maturity × 0.20) + (Automation × 0.15)
Overall Score = Average of all domain scores
```

---

## 2. Module Security Scores

### 2.1 Core Security Modules

| Module | Effectiveness | Coverage | Maturity | Automation | Score | Rating |
|--------|-------------|----------|----------|------------|-------|--------|
| GSF-001 Identity | 85 | 80 | 70 | 75 | 79.3 | B |
| GSF-002 Secrets | 90 | 85 | 75 | 80 | 83.8 | B |
| GSF-003 Crypto | 95 | 90 | 85 | 85 | 89.8 | B |
| GSF-004 Authentication | 90 | 85 | 80 | 85 | 85.8 | B |
| GSF-005 Authorization | 85 | 80 | 75 | 80 | 80.8 | B |
| GSF-006 Audit | 90 | 85 | 80 | 80 | 84.5 | B |
| GSF-007 Compliance | 80 | 75 | 70 | 70 | 74.5 | C |
| GSF-008 Headers | 85 | 80 | 85 | 90 | 84.8 | B |
| GSF-009 Network | 80 | 75 | 70 | 75 | 75.8 | B |
| GSF-010 Database | 85 | 75 | 70 | 75 | 77.0 | B |
| **Core Average** | **86.5** | **81.0** | **76.0** | **79.0** | **81.6** | **B** |

### 2.2 Infrastructure Security Modules

| Module | Effectiveness | Coverage | Maturity | Automation | Score | Rating |
|--------|-------------|----------|----------|------------|-------|--------|
| GSF-011 Container | 80 | 75 | 65 | 75 | 74.5 | C |
| GSF-012 Kubernetes | 80 | 75 | 65 | 75 | 74.5 | C |
| GSF-013 Terraform | 75 | 70 | 60 | 70 | 69.5 | C |
| GSF-014 GitHub | 80 | 75 | 70 | 80 | 76.5 | B |
| GSF-015 CI/CD | 80 | 75 | 70 | 80 | 76.5 | B |
| GSF-016 Supply Chain | 75 | 70 | 60 | 70 | 69.5 | C |
| GSF-020 Integrity | 75 | 70 | 60 | 65 | 68.3 | C |
| **Infra Average** | **77.9** | **72.9** | **64.3** | **73.6** | **72.8** | **C** |

### 2.3 Healthcare Security Modules

| Module | Effectiveness | Coverage | Maturity | Automation | Score | Rating |
|--------|-------------|----------|----------|------------|-------|--------|
| GSF-017 FHIR | 85 | 80 | 70 | 75 | 78.8 | B |
| GSF-018 Privacy | 80 | 75 | 65 | 70 | 73.5 | C |
| GSF-019 Threat Detection | 75 | 70 | 60 | 70 | 69.5 | C |
| **Healthcare Average** | **80.0** | **75.0** | **65.0** | **71.7** | **73.9** | **C** |

---

## 3. Overall Score

| Category | Average Score | Weight | Weighted Score |
|----------|--------------|--------|---------------|
| Core Security Modules | 81.6 | 50% | 40.8 |
| Infrastructure Security | 72.8 | 30% | 21.8 |
| Healthcare Security | 73.9 | 20% | 14.8 |
| **Overall GSF Score** | | | **77.4 (B)** |

---

## 4. Score Breakdown by Security Function

```
Authentication & Authorization     ████████████████████░░  82
Cryptography                       █████████████████████░  90
Identity Management               ████████████████████░░  79
Audit & Monitoring                ████████████████████░░  85
Compliance                        ████████████████░░░░░░  75
Network Security                  ██████████████████░░░░  76
Container Security                ████████████████░░░░░░  75
Kubernetes Security               ████████████████░░░░░░  75
Infrastructure as Code            ██████████████░░░░░░░░  70
CI/CD Security                    ██████████████████░░░░  77
Supply Chain Security             ██████████████░░░░░░░░  70
FHIR Security                     ████████████████████░░  79
Privacy & Consent                 ████████████████░░░░░░  74
Threat Detection                  ██████████████░░░░░░░░  70
Integrity                         ██████████████░░░░░░░░  68
```

---

## 5. Target Scores

### 5.1 Next Quarter Targets (Q3 2026)

| Module | Current | Target | Gap | Priority |
|--------|---------|--------|-----|----------|
| GSF-007 Compliance | 74.5 | 80 | +5.5 | High |
| GSF-011 Container | 74.5 | 80 | +5.5 | High |
| GSF-012 Kubernetes | 74.5 | 80 | +5.5 | High |
| GSF-019 Threat Detection | 69.5 | 75 | +5.5 | High |
| GSF-020 Integrity | 68.3 | 75 | +6.7 | High |

### 5.2 Year-End Targets (Q4 2026)

| Module | Current | Target | Gap | Priority |
|--------|---------|--------|-----|----------|
| GSF-013 Terraform | 69.5 | 80 | +10.5 | Medium |
| GSF-016 Supply Chain | 69.5 | 80 | +10.5 | Medium |
| GSF-018 Privacy | 73.5 | 85 | +11.5 | Medium |
| GSF-019 Threat Detection | 69.5 | 80 | +10.5 | Medium |

### 5.3 Long-Term Targets (2027)

| Category | Current | Q3 2026 | Q4 2026 | Q2 2027 | Q4 2027 |
|----------|---------|---------|---------|---------|---------|
| Core | 81.6 | 85 | 88 | 92 | 95 |
| Infrastructure | 72.8 | 76 | 82 | 88 | 92 |
| Healthcare | 73.9 | 77 | 83 | 88 | 93 |
| **Overall** | **77.4** | **81** | **85** | **90** | **94** |

---

## 6. Quarterly Review Process

### 6.1 Review Timeline

| Activity | Timeline | Participants |
|----------|----------|-------------|
| Data collection | Last week of quarter | Module owners |
| Score calculation | First week of new quarter | Security Lead |
| Gap analysis | First week of new quarter | Security Lead + Module owners |
| Remediation planning | Second week | Security Lead |
| Executive review | Second week | CISO, Engineering Lead |
| Scorecard publication | Third week | Security Lead |
| Remediation execution | Following quarter | Module owners |

### 6.2 Data Sources

| Metric | Data Source | Collection Method |
|--------|-------------|-------------------|
| SAST coverage | CI/CD pipeline | Automated report |
| SCA scan results | CI/CD pipeline | Automated report |
| Penetration test results | External pentest | Manual report |
| Dependency freshness | Dependabot/Renovate | Automated |
| Container vulnerabilities | Trivy | Automated |
| K8s compliance | OPA Gatekeeper | Automated |
| Audit log completeness | GSF-006 | Automated |
| MFA adoption | GSF-004 | Automated |
| Access review completion | GSF-005 | Manual verification |
| Training completion | HR system | Automated |
| Incident metrics | IR tracker | Manual aggregation |
| DR test results | DR exercise | Manual evaluation |

---

## 7. Remediation Tracker

| Issue ID | Module | Finding | Severity | Assigned | Target | Status |
|----------|--------|---------|----------|----------|--------|--------|
| SCP-001 | GSF-019 | No SIEM correlation rules for FHIR access | High | SOC Lead | Q3 2026 | In Progress |
| SCP-002 | GSF-020 | FIM not deployed on K8s node hosts | High | Integrity Lead | Q3 2026 | In Progress |
| SCP-003 | GSF-011 | Container images not all Cosign-signed | High | Container Lead | Q3 2026 | Planned |
| SCP-004 | GSF-012 | OPA Gatekeeper not enforcing all PSS | Medium | K8s Lead | Q4 2026 | Planned |
| SCP-005 | GSF-016 | SBOM generation not mandatory in all builds | Medium | CI Lead | Q4 2026 | Planned |
| SCP-006 | GSF-013 | Terraform state not encrypted for all workspaces | Medium | Infra Lead | Q4 2026 | In Progress |

---

## 8. Scorecard Governance

| Role | Responsibility |
|------|---------------|
| GSF Security Lead | Scorecard ownership, quarterly publication |
| Module Owners | Domain score data, remediation execution |
| CISO | Scorecard approval, resource allocation |
| Engineering Lead | Remediation implementation oversight |
| Compliance Officer | Regulatory alignment validation |

---

**Document History**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-07-25 | GULA Security Team | Initial scorecard |
