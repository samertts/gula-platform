# GSF Risk Register

**Document ID**: GSF-RR-001  
**Version**: 1.0.0  
**Effective Date**: 2026-07-25  
**Next Review Date**: 2026-10-25  
**Owner**: GULA Security Lead  

---

## 1. Risk Methodology

### 1.1 Likelihood Scale

| Level | Score | Description | Frequency |
|-------|-------|-------------|-----------|
| Very High | 5 | Almost certain | Multiple times per year |
| High | 4 | Likely | Annually |
| Medium | 3 | Possible | Every 2-5 years |
| Low | 2 | Unlikely | Every 5-10 years |
| Very Low | 1 | Rare | > 10 years |

### 1.2 Impact Scale

| Level | Score | Description | Impact |
|-------|-------|-------------|--------|
| Critical | 5 | > 10M IQD loss, patient safety, national reputation | Extreme |
| High | 4 | 1M-10M IQD loss, regulatory fine | Major |
| Medium | 3 | 100K-1M IQD loss, operational disruption | Moderate |
| Low | 2 | 10K-100K IQD loss, minor disruption | Minor |
| Very Low | 1 | < 10K IQD loss, negligible impact | Insignificant |

### 1.3 Risk Score = Likelihood × Impact

| Score Range | Risk Level | Action Required |
|-------------|------------|----------------|
| 20-25 | Critical | Immediate remediation, report to CISO |
| 15-19 | High | Remediate within 30 days |
| 10-14 | Medium | Remediate within 90 days |
| 5-9 | Low | Accept with monitoring |
| 1-4 | Very Low | Accept |

---

## 2. Risk Register

### 2.1 Technical Risks

| Risk ID | Risk Description | Category | L | I | Score | Level | Mitigation | Owner | Status | Review |
|---------|-----------------|----------|---|---|-------|-------|------------|-------|--------|--------|
| GSF-RISK-001 | Cryptographic key compromise (KEK/DEK leakage) | Technical | 2 | 5 | 10 | Medium | HSM for KEK, key wrapping, rotation policy, audit | Crypto Lead | Partially Mitigated | Q4 2026 |
| GSF-RISK-002 | PHI data breach via SQL injection in FHIR API | Technical | 3 | 5 | 15 | High | WAF, parameterized queries, ORM, DAST scanning, query monitoring | AppSec Lead | Partially Mitigated | Q3 2026 |
| GSF-RISK-003 | Authentication bypass via JWT algorithm confusion | Technical | 2 | 5 | 10 | Medium | Algorithm whitelist, JWT validation library, signature verification | Auth Lead | Partially Mitigated | Q4 2026 |
| GSF-RISK-004 | Container escape leading to host compromise | Technical | 2 | 5 | 10 | Medium | seccomp, AppArmor, read-only root FS, non-root user | K8s Lead | Mitigated | Q3 2026 |
| GSF-RISK-005 | Supply chain attack via compromised dependency | Technical | 3 | 4 | 12 | Medium | SBOM verification, dependency pinning, SCA scanning, Cosign | CI Lead | Partially Mitigated | Q3 2026 |
| GSF-RISK-006 | Kubernetes RBAC misconfiguration | Technical | 3 | 4 | 12 | Medium | Automated RBAC audit, least privilege defaults, OPA Gatekeeper | K8s Lead | Partially Mitigated | Q3 2026 |
| GSF-RISK-007 | TLS certificate expiration causing service outage | Technical | 3 | 3 | 9 | Low | Automated certificate renewal (cert-manager), monitoring, alerts | Network Lead | Mitigated | Q3 2026 |
| GSF-RISK-008 | DDoS attack on public API endpoints | Technical | 3 | 3 | 9 | Low | Rate limiting, CDN/WAF, autoscaling, DDoS protection | Network Lead | Partially Mitigated | Q4 2026 |
| GSF-RISK-009 | Audit log tampering by privileged insider | Technical | 2 | 5 | 10 | Medium | Hash chain, WORM storage, append-only, split custody | Audit Lead | Partially Mitigated | Q4 2026 |
| GSF-RISK-010 | Re-identification of anonymized patient data | Technical | 2 | 5 | 10 | Medium | k-anonymity (k=10), differential privacy, risk assessment | Privacy Lead | Partially Mitigated | Q4 2026 |

### 2.2 Operational Risks

| Risk ID | Risk Description | Category | L | I | Score | Level | Mitigation | Owner | Status | Review |
|---------|-----------------|----------|---|---|-------|-------|------------|-------|--------|--------|
| GSF-RISK-011 | Insider threat — privileged user exfiltrates PHI | Operational | 3 | 5 | 15 | High | DLP monitoring, user behavior analytics, least privilege, separation of duties | SOC Lead | Partially Mitigated | Q3 2026 |
| GSF-RISK-012 | Inadequate incident response during active breach | Operational | 3 | 4 | 12 | Medium | Incident response drills, playbooks, automated containment | IR Lead | Partially Mitigated | Q3 2026 |
| GSF-RISK-013 | Configuration drift leading to insecure deployment | Operational | 4 | 3 | 12 | Medium | GitOps, drift detection (GSF-020), automated remediation | Plat Eng Lead | Partially Mitigated | Q3 2026 |
| GSF-RISK-014 | Backup failure causing permanent data loss | Operational | 2 | 5 | 10 | Medium | Regular restore testing, 3-2-1 backup strategy, monitoring | Plat Eng Lead | Partially Mitigated | Q3 2026 |
| GSF-RISK-015 | Security monitoring team alert fatigue | Operational | 4 | 2 | 8 | Low | Alert prioritization, ML correlation, false positive reduction | SOC Lead | Not Mitigated | Q4 2026 |
| GSF-RISK-016 | Key person dependency on security operations | Operational | 3 | 3 | 9 | Low | Cross-training, documentation, rotation, redundancy | Security Lead | Partially Mitigated | Q4 2026 |
| GSF-RISK-017 | Third-party vendor security incident | Operational | 3 | 4 | 12 | Medium | Vendor security assessment, contractual security requirements, monitoring | Compliance Lead | Partially Mitigated | Q3 2026 |
| GSF-RISK-018 | Social engineering attack on clinical staff | Operational | 4 | 3 | 12 | Medium | Security awareness training, phishing simulations, reporting process | Security Lead | Partially Mitigated | Q3 2026 |

### 2.3 Compliance Risks

| Risk ID | Risk Description | Category | L | I | Score | Level | Mitigation | Owner | Status | Review |
|---------|-----------------|----------|---|---|-------|-------|------------|-------|--------|--------|
| GSF-RISK-019 | HIPAA violation due to missing audit trail | Compliance | 2 | 4 | 8 | Low | Immutable audit logging, compliance scanning (GSF-007) | Compliance Lead | Mitigated | Q3 2026 |
| GSF-RISK-020 | GDPR violation regarding patient data access | Compliance | 2 | 4 | 8 | Low | Consent management, data subject access request (DSAR) process | Privacy Lead | Mitigated | Q3 2026 |
| GSF-RISK-021 | Iraqi MOH regulation non-compliance | Compliance | 3 | 4 | 12 | Medium | Regulatory monitoring, compliance automation (GSF-007), audit | Compliance Lead | Partially Mitigated | Q3 2026 |
| GSF-RISK-022 | Cross-border data transfer violation | Compliance | 2 | 4 | 8 | Low | Data localization, data classification, transfer impact assessment | Privacy Lead | Mitigated | Q4 2026 |
| GSF-RISK-023 | ISO 27001 certification failure | Compliance | 2 | 3 | 6 | Low | Continuous compliance monitoring, internal audits, gap analysis | Compliance Lead | Mitigated | Q4 2026 |
| GSF-RISK-024 | OWASP ASVS Level 3 non-compliance in new features | Compliance | 3 | 3 | 9 | Low | Secure SDLC, security requirements in user stories, security review gate | AppSec Lead | Partially Mitigated | Q3 2026 |

### 2.4 Healthcare-Specific Risks

| Risk ID | Risk Description | Category | L | I | Score | Level | Mitigation | Owner | Status | Review |
|---------|-----------------|----------|---|---|-------|-------|------------|-------|--------|--------|
| GSF-RISK-025 | Unauthorized modification of laboratory results | Healthcare | 2 | 5 | 10 | Medium | Integrity monitoring, FHIR Provenance, audit trail, approval workflows | FHIR Lead | Partially Mitigated | Q4 2026 |
| GSF-RISK-026 | Incorrect patient identity due to NIN mismatch | Healthcare | 3 | 5 | 15 | High | Biometric verification, multi-factor identity proofing, duplicate detection | Identity Lead | Partially Mitigated | Q3 2026 |
| GSF-RISK-027 | Consent revocation not honored in real-time | Healthcare | 2 | 5 | 10 | Medium | Event-driven consent propagation, cache invalidation, audit | Privacy Lead | Partially Mitigated | Q4 2026 |
| GSF-RISK-028 | Offline mode security control bypass | Healthcare | 4 | 4 | 16 | High | Local audit queue, rate limiting, post-sync verification, tamper detection | Plat Eng Lead | Not Mitigated | Q4 2026 |
| GSF-RISK-029 | Emergency access (break-glass) abuse | Healthcare | 3 | 4 | 12 | Medium | Post-access review, immediate notification, dual authorization for continued access | Auth Lead | Partially Mitigated | Q3 2026 |
| GSF-RISK-030 | Medical device security vulnerability (analyzer integration) | Healthcare | 3 | 5 | 15 | High | Network segmentation, device authentication, input validation, monitoring | Network Lead | Partially Mitigated | Q3 2026 |
| GSF-RISK-031 | Patient data exposure through FHIR bulk data export | Healthcare | 2 | 5 | 10 | Medium | Additional authorization for bulk export, rate limiting, token binding to specific export | FHIR Lead | Partially Mitigated | Q4 2026 |

---

## 3. Risk Summary

### 3.1 Distribution by Category

| Category | Count | Critical | High | Medium | Low | Very Low |
|----------|-------|----------|------|--------|-----|----------|
| Technical | 10 | 0 | 2 | 6 | 2 | 0 |
| Operational | 8 | 0 | 1 | 5 | 2 | 0 |
| Compliance | 6 | 0 | 0 | 1 | 5 | 0 |
| Healthcare | 7 | 0 | 3 | 4 | 0 | 0 |
| **Total** | **31** | **0** | **6** | **16** | **9** | **0** |

### 3.2 Risk Heat Map

```
Impact →
  5 │ GSF-RISK-028  GSF-RISK-002  GSF-RISK-001
    │               GSF-RISK-011  GSF-RISK-003
    │ GSF-RISK-025  GSF-RISK-026  GSF-RISK-004
    │ GSF-RISK-027  GSF-RISK-030  GSF-RISK-005
    │ GSF-RISK-014  GSF-RISK-031  GSF-RISK-009
    │               GSF-RISK-029  GSF-RISK-010
  4 │ GSF-RISK-017                            
    │ GSF-RISK-021                            
    │ GSF-RISK-017                            
    │                                         
  3 │ GSF-RISK-008  GSF-RISK-006  GSF-RISK-007
    │               GSF-RISK-012              
    │               GSF-RISK-013              
    │                                         
  2 │ GSF-RISK-015  GSF-RISK-016  GSF-RISK-024
    │                                         
  1 │                                         
    └──────────────────────────────────────────
      1     2       3       4       5    Likelihood →
```

### 3.3 Mitigation Status

| Status | Count | % |
|--------|-------|---|
| Mitigated | 5 | 16% |
| Partially Mitigated | 21 | 68% |
| Not Mitigated | 5 | 16% |

---

## 4. Risk Treatment Plan

### Q3 2026 Priorities

1. **GSF-RISK-028** — Offline security control bypass: Implement local audit queue, offline attestation
2. **GSF-RISK-002** — SQL injection in FHIR API: Deploy WAF with FHIR-specific rules, enhance DAST
3. **GSF-RISK-011** — Insider threat: Deploy UBA solution, enhance DLP controls
4. **GSF-RISK-026** — NIN mismatch: Implement biometric verification for identity proofing
5. **GSF-RISK-030** — Medical device vulnerability: Network segmentation, device authentication

### Q4 2026 Priorities

1. **GSF-RISK-001** — Key compromise: HSM integration for key management
2. **GSF-RISK-003** — JWT algorithm confusion: Algorithm validation hardening
3. **GSF-RISK-009** — Audit tampering: WORM storage implementation
4. **GSF-RISK-010** — Re-identification: Differential privacy implementation
5. **GSF-RISK-015** — Alert fatigue: ML-based alert correlation

---

## 5. Risk Acceptance

| Risk ID | Accepted By | Date | Justification |
|---------|-------------|------|---------------|
| — | — | — | No risks currently accepted |

---

## 6. Review Schedule

- **Quarterly**: Full risk register review and update
- **Monthly**: High and critical risk status update
- **Per Release**: New feature risk assessment
- **Per Incident**: Post-incident risk reassessment

---

**Document History**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-07-25 | GULA Security Team | Initial risk register |
