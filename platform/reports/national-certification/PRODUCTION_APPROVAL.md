# Production Approval Checklist

## GULA National Health Platform — National Rollout Sign-Off

**Version:** 2.1.0
**Date:** July 2026

---

## Instructions

Each domain lead must review and sign off on their respective section. The Program Director makes the final Go/No-Go decision. All items must be marked ✅ before production deployment.

---

## 1. Quality Gates

| # | Gate | Criteria | Status | Signed By | Date |
|---|------|----------|--------|-----------|------|
| QG-01 | TypeScript compilation | `tsc -b` passes for all apps | ✅ PASS | Platform Lead | 2026-07-15 |
| QG-02 | Linting | ESLint 0 errors, 0 warnings | ✅ PASS | Platform Lead | 2026-07-15 |
| QG-03 | Unit tests | All pass, coverage >= 95% | ✅ PASS | QA Lead | 2026-07-15 |
| QG-04 | Integration tests | All critical workflows pass | ✅ PASS | QA Lead | 2026-07-15 |
| QG-05 | E2E tests | 135 tests, 98.5% pass rate | ✅ PASS | QA Lead | 2026-07-15 |
| QG-06 | Bundle size | All apps under 300KB (gzip) | ✅ PASS | Frontend Lead | 2026-07-15 |
| QG-07 | Lighthouse PWA | >= 90 score | ✅ PASS | Frontend Lead | 2026-07-15 |
| QG-08 | Cross-browser testing | Chrome, Firefox, Safari, Edge | ✅ PASS | QA Lead | 2026-07-15 |
| QG-09 | Visual regression | No unexpected changes | ✅ PASS | QA Lead | 2026-07-14 |
| QG-10 | API contract testing | OpenAPI spec validated | ✅ PASS | Backend Lead | 2026-07-15 |

---

## 2. Security Gates

| # | Gate | Criteria | Status | Signed By | Date |
|---|------|----------|--------|-----------|------|
| SG-01 | SAST (Static Analysis) | Bandit + ESLint security rules pass | ✅ PASS | Security Lead | 2026-07-14 |
| SG-02 | SCA (Dependency Audit) | 0 critical, 0 high in pnpm audit | ✅ PASS | Security Lead | 2026-07-15 |
| SG-03 | Container scan | Trivy: 0 critical, 0 high | ✅ PASS | Security Lead | 2026-07-14 |
| SG-04 | DAST (Dynamic Scan) | OWASP ZAP weekly: 0 high findings | ✅ PASS | Security Lead | 2026-07-14 |
| SG-05 | Secret scan | Gitleaks: 0 findings | ✅ PASS | Security Lead | 2026-07-15 |
| SG-06 | IaC scan | Checkov: 0 high findings | ✅ PASS | Platform Lead | 2026-07-14 |
| SG-07 | Penetration test | 0 critical, 2 high → remediated | ✅ PASS | External Auditor | 2026-07-12 |
| SG-08 | Access control audit | All roles reviewed, no excessive permissions | ✅ PASS | Security Lead | 2026-07-15 |
| SG-09 | Encryption verification | TLS 1.3, AES-256, KMS confirmed | ✅ PASS | Security Lead | 2026-07-15 |
| SG-10 | Rate limiting validation | All endpoints rate-limited appropriately | ✅ PASS | Backend Lead | 2026-07-14 |

---

## 3. Clinical Safety Gates

| # | Gate | Criteria | Status | Signed By | Date |
|---|------|----------|--------|-----------|------|
| CSG-01 | Drug interaction checking | 100% of 450K+ pairs verified | ✅ APPROVED | Clinical Lead | 2026-07-14 |
| CSG-02 | Critical value detection | All panic values within national ranges | ✅ APPROVED | Clinical Lead | 2026-07-14 |
| CSG-03 | Medication safety | Dose, route, frequency checks validated | ✅ APPROVED | Clinical Lead | 2026-07-14 |
| CSG-04 | Patient identification | Multi-factor ID verified in all workflows | ✅ APPROVED | Clinical Lead | 2026-07-14 |
| CSG-05 | Allergy checking | 100% coverage on prescription workflow | ✅ APPROVED | Clinical Lead | 2026-07-14 |
| CSG-06 | Decision support rules | 250+ CDS rules validated clinically | ✅ APPROVED | Clinical Lead | 2026-07-14 |
| CSG-07 | Clinical pathways | 273 pathways reviewed and accepted | ✅ APPROVED | Clinical Lead | 2026-07-14 |
| CSG-08 | Human-in-the-loop | All critical decisions require human review | ✅ APPROVED | Clinical Lead | 2026-07-14 |
| CSG-09 | Safety incident reporting | 23 near misses analyzed, 0 adverse events | ✅ APPROVED | Clinical Safety Officer | 2026-07-15 |
| CSG-10 | MoH clinical safety certificate | Certificate issued | ✅ APPROVED | MoH | 2026-07-15 |

---

## 4. Performance Gates

| # | Gate | Target | Actual | Status | Signed By | Date |
|---|------|--------|--------|--------|-----------|------|
| PG-01 | API P95 response time | < 500ms | 220ms | ✅ PASS | Platform Lead | 2026-07-14 |
| PG-02 | Lighthouse Performance | >= 85 | 88 | ✅ PASS | Frontend Lead | 2026-07-14 |
| PG-03 | Lighthouse PWA | >= 90 | 93 | ✅ PASS | Frontend Lead | 2026-07-14 |
| PG-04 | FCP target | < 2.0s | 1.6s | ✅ PASS | Frontend Lead | 2026-07-14 |
| PG-05 | TTI target | < 3.0s | 2.4s | ✅ PASS | Frontend Lead | 2026-07-14 |
| PG-06 | Error rate | < 1% | 0.08% | ✅ PASS | Platform Lead | 2026-07-14 |
| PG-07 | Concurrent users | 500 | 1500 | ✅ PASS | Platform Lead | 2026-07-14 |
| PG-08 | Load test P95 stability | No regression | Stable | ✅ PASS | Platform Lead | 2026-07-14 |
| PG-09 | Offline load time | < 500ms | 200ms | ✅ PASS | Frontend Lead | 2026-07-14 |
| PG-10 | Sync latency | < 5s | 3.2s | ✅ PASS | Frontend Lead | 2026-07-14 |

---

## 5. Documentation Gates

| # | Gate | Criteria | Status | Signed By | Date |
|---|------|----------|--------|-----------|------|
| DG-01 | Architecture documentation | Complete and reviewed | ✅ PASS | Tech Writer | 2026-07-15 |
| DG-02 | API documentation (OpenAPI) | All endpoints documented | ✅ PASS | Backend Lead | 2026-07-15 |
| DG-03 | Deployment guide | Step-by-step for all environments | ✅ PASS | Platform Lead | 2026-07-15 |
| DG-04 | Operations guide | Monitoring, alerting, incident response | ✅ PASS | Ops Lead | 2026-07-15 |
| DG-05 | Disaster recovery plan | RPO/RTO, failover, failback, drills | ✅ PASS | Ops Lead | 2026-07-15 |
| DG-06 | User manuals | All 8 apps documented | ✅ PASS | Tech Writer | 2026-07-14 |
| DG-07 | Release notes | Comprehensive with known issues | ✅ PASS | Product Manager | 2026-07-15 |
| DG-08 | SBOM | All dependencies listed with licenses | ✅ PASS | Security Lead | 2026-07-15 |
| DG-09 | Training materials | Video + written for all roles | ✅ PASS | Product Manager | 2026-07-14 |
| DG-10 | Arabic translations | All user-facing docs in Arabic | ✅ PASS | Tech Writer | 2026-07-14 |

---

## 6. Operations Gates

| # | Gate | Criteria | Status | Signed By | Date |
|---|------|----------|--------|-----------|------|
| OG-01 | Monitoring dashboards | 8 dashboards verified operational | ✅ PASS | Ops Lead | 2026-07-14 |
| OG-02 | Alerting configured | 25 alert rules, all channels tested | ✅ PASS | Ops Lead | 2026-07-14 |
| OG-03 | Backup verification | Daily backup confirmed successful | ✅ PASS | DB Admin | 2026-07-15 |
| OG-04 | DR drill completed | Monthly drill passed | ✅ PASS | Ops Lead | 2026-07-12 |
| OG-05 | On-call rotation | 24/7 coverage established | ✅ PASS | Ops Lead | 2026-07-15 |
| OG-06 | Capacity plan | Q3-Q4 projections validated | ✅ PASS | Platform Lead | 2026-07-15 |
| OG-07 | Incident response runbooks | 12 runbooks documented | ✅ PASS | Ops Lead | 2026-07-14 |
| OG-08 | Rollback procedure | Tested in staging | ✅ PASS | Platform Lead | 2026-07-14 |
| OG-09 | Health check endpoints | /health, /health/ready, /health/deep verified | ✅ PASS | Ops Lead | 2026-07-14 |
| OG-10 | Log shipping | Loki + Promtail confirmed operational | ✅ PASS | Ops Lead | 2026-07-14 |

---

## 7. Domain Lead Sign-Off

| Domain | Lead | Signature | Date | Status |
|--------|------|-----------|------|--------|
| **Backend** | Backend Lead | ✅ | 2026-07-15 | All backend gates passed |
| **Frontend** | Frontend Lead | ✅ | 2026-07-15 | All frontend gates passed |
| **AI/ML** | AI Lead | ✅ | 2026-07-15 | All AI gates passed |
| **Quality Assurance** | QA Lead | ✅ | 2026-07-15 | All testing gates passed |
| **Security** | Security Lead | ✅ | 2026-07-15 | All security gates passed |
| **Clinical** | Clinical Lead | ✅ | 2026-07-15 | All clinical safety gates passed |
| **Operations** | Ops Lead | ✅ | 2026-07-15 | All operations gates passed |
| **Product** | Product Manager | ✅ | 2026-07-15 | Product requirements met |
| **Data** | DB Admin | ✅ | 2026-07-15 | Database readiness confirmed |

---

## 8. Final Approval

| Role | Name | Decision | Signature | Date |
|------|------|----------|-----------|------|
| **Program Director** | Dr. Samer T. | ✅ **GO** | <signed> | 2026-07-16 |
| **Ministry Liaison** | MoH IT Director | ✅ **APPROVED** | <signed> | 2026-07-16 |
| **Clinical Safety Officer** | Clinical Committee | ✅ **APPROVED** | <signed> | 2026-07-15 |

---

## 9. Post-Approval Actions

| # | Action | Owner | Due Date |
|---|--------|-------|----------|
| 1 | Announce national rollout to stakeholders | Program Director | 2026-07-17 |
| 2 | Deploy to production environment | Ops Lead | 2026-07-18 |
| 3 | Run post-deployment smoke tests | QA Lead | 2026-07-18 |
| 4 | Monitor for 48-hour stabilization period | Ops Lead | 2026-07-20 |
| 5 | Begin Phase 1 site onboarding | Program Director | 2026-08-01 |
