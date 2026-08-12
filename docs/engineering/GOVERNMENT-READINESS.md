# Government Readiness — GULA Platform

**Version:** 1.0.0
**Date:** 2026-07-08
**Classification:** Confidential — Engineering + Legal

---

## Overview

The GULA Platform integrates with the Iraqi National Health Data System (SNDHS — النظام الوطني للبيانات الصحية) to provide compliant health data management for medical laboratories. This document assesses readiness for government-mandated healthcare data regulations.

## Regulatory Framework

### Iraqi Healthcare Data Regulations

The platform must comply with:
1. **SNDHS-lite Phase 1** — National ID collection, health ID assignment, visit tracking, enhanced audit
2. **Iraqi Data Protection Law** — Patient data privacy and security requirements
3. **Ministry of Health Guidelines** — Laboratory data management standards
4. **International Standards** — ISO 15189 (medical laboratories), HIPAA-inspired practices

### SNDHS-lite Phase 1 Compliance

| Requirement | Status | Implementation |
|-------------|--------|---------------|
| National ID collection | Complete | `patients.national_id` — AES-256 encrypted at rest |
| Health ID assignment | Complete | `patients.sndhs_health_id` — SNDHS-assigned |
| Visit tracking | Complete | `visits` table + `lab_orders.visit_id` |
| Enhanced audit log | Complete | Audit log v2 with SNDHS correlation fields |
| Dual-read None handling | Complete | Existing rows pre-backfill gracefully return None |
| Feature flag gating | Complete | `SNDHS_ENABLE_VISITS`, `SNDHS_ENABLE_NATIONAL_ID` |

### Gap Analysis

| Area | Status | Gap | Priority |
|------|--------|-----|----------|
| Data classification | Partial | No formal data classification document | Medium |
| Retention policy | Missing | No documented data retention schedule | High |
| Deletion procedures | Missing | No documented patient data deletion process | High |
| Breach notification | Missing | No breach notification procedure | Medium |
| Consent management | Partial | Basic consent fields, no full consent workflow | Medium |
| Audit review cycle | Missing | No periodic audit log review process | Medium |
| Third-party audits | Missing | No third-party audit schedule | Low |
| Staff training | Missing | No data protection training documentation | Low |

## Security Controls for Government Compliance

### Technical Controls (Implemented)

| Control | Implementation | Standard |
|---------|---------------|----------|
| Access control | RBAC with 9 roles × 13 permissions | ISO 15189 |
| Authentication | JWT + bcrypt + refresh rotation | NIST SP 800-63 |
| Encryption at rest | AES-256 for national_id | NIST SP 800-111 |
| Encryption in transit | TLS enforced | NIST SP 800-52 |
| Audit logging | Immutable hash chain | ISO 15189 |
| Tenant isolation | lab_id filtering on all queries | ISO 15189 |
| Rate limiting | Per-user, per-endpoint | OWASP |
| Input validation | All endpoints validated | OWASP ASVS |

### Administrative Controls (Partial)

| Control | Status | Action Required |
|---------|--------|-----------------|
| Security policy | Complete | Documented in SECURITY.md |
| Risk assessment | Complete | Documented in RISK-REGISTER.md |
| Incident response | Partial | Document, need tabletop exercise |
| Business continuity | Partial | DR scripts exist, need full BCP |
| Data protection impact assessment | Missing | Required for SNDHS compliance |
| Vendor management | Missing | Required for cloud/SaaS providers |

### Physical Controls (Not Applicable)

The platform is a SaaS solution. Physical security is managed by the cloud infrastructure provider (DigitalOcean).

## Government Integration Architecture

### SNDHS-lite Data Flow

```
Lab → Patient Registration → national_id encrypted → Audit Log
  → SNDHS Health ID assignment (when enabled)
  → Visit creation (when enabled)
  → Lab Order with optional visit_id
  → Results → Audit Log v2 (hash chain)
```

### Feature Flag Control

| Flag | Default | Purpose |
|------|---------|---------|
| `SNDHS_ENABLE_VISITS` | false | Visit tracking |
| `SNDHS_ENABLE_NATIONAL_ID` | false | National ID fields |
| `ENABLE_FINANCIAL_ENGINE` | false | Financial routes (Phase B+) |

Feature flags enable safe rollout. Data backfill required before enabling on existing deployments.

## Certification Readiness

### Self-Certification Checklist

- [x] National ID collection with encryption at rest
- [x] Health ID assignment infrastructure
- [x] Visit tracking schema and integration
- [x] Enhanced audit log with SNDHS correlation
- [x] Feature flag controlled rollout
- [x] Backfill scripts for existing data
- [x] Rollback procedures documented
- [ ] Data retention policy documented
- [ ] Breach notification procedure documented
- [ ] Consent management workflow complete
- [ ] Third-party audit scheduled

### Recommended Certification Path

1. **Internal audit** — Self-certification against SNDHS Phase 1 requirements
2. **External audit** — Third-party security and compliance audit
3. **Government submission** — Submit compliance documentation to Ministry of Health
4. **Periodic review** — Annual recertification cycle

## Documents Required for Government Submission

| Document | Status | Location |
|----------|--------|----------|
| Data protection policy | ✅ Complete | `SECURITY.md` |
| Security architecture | ✅ Complete | `docs/adr/` |
| Encryption methodology | ✅ Complete | `docs/security/` |
| Audit trail specification | ✅ Complete | `docs/security/` |
| Data retention policy | ❌ Missing | TBD |
| Breach notification procedure | ❌ Missing | TBD |
| Consent management workflow | ❌ Missing | TBD |
| DPIA (Data Protection Impact Assessment) | ❌ Missing | TBD |
| Business continuity plan | ❌ Missing | TBD |
| Incident response plan | ❌ Missing | TBD |

## Recommendations

### Immediate (30 days)
1. Document data retention policy
2. Document breach notification procedure
3. Schedule internal audit against SNDHS Phase 1 requirements

### Short-term (60 days)
4. Implement consent management workflow
5. Complete Data Protection Impact Assessment
6. Develop business continuity plan

### Medium-term (90 days)
7. Schedule third-party security audit
8. Implement staff training program
9. Establish annual recertification cycle

## References

- `docs/sndhs/` — SNDHS-lite integration documentation (22 files)
- `docs/sndhs/phase1/RUNBOOK.md` — Phase 1 production deployment guide
- `SECURITY.md` — Security policy
- `docs/engineering/RISK-REGISTER.md` — Risk register
- `CLAUDE.md` — Engineering Constitution (SNDHS flags section)
- `scripts/sndhs_phase1_backfill.py` — Data backfill script
- `scripts/sndhs_phase1_rollback.sql` — Rollback script
