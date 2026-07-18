# GULA Platform — Executive Summary

**Date:** 2026-07-18
**Classification:** CONFIDENTIAL — Board/C-Suite
**Prepared by:** PROGRAM-02 Enterprise Discovery

---

## Current State Overview

GULA is an **Arabic-first medical laboratory SaaS platform** that has evolved into a **national healthcare platform** for Iraq. The core LIMS is **production-ready** with strong security (7.8/10), advanced self-healing infrastructure, comprehensive CI/CD, and Iraqi-specific integration (SNDHS-lite, MoI National ID, IQD claims). The monorepo spans ~3,700 files, ~120K lines of Python, 250+ database tables, and 53+ route modules.

**Version:** 2.1.0 (config.py) — divergence exists across repo  
**Deployment:** Docker Compose on DigitalOcean (MVP: 6 containers)  
**Team:** Single founder-led with ~120K LOC monolith  
**Revenue:** Pre-revenue  
**Certification Level:** BRONZE (Quality Index: 673/1000 — Grade D)

---

## Key Strengths

| Strength | Detail |
|----------|--------|
| **Production LIMS** | Orders, results, samples, QC, patient cards, PDF reports, multi-tenancy — fully operational |
| **Security Foundation** | JWT, RBAC (9 roles), ABAC, MFA (TOTP + WebAuthn/FIDO2), OAuth2/OIDC, SAML 2.0, Fernet encryption, hash-chain audit, rate limiting, circuit breakers |
| **Self-Healing** | 3-layer: circuit breaker → auto-repair → adaptive concurrency; startup guard blocks until ready |
| **Infrastructure** | Docker Compose (MVP + Full + HA), K8s (Kustomize + Helm), Terraform, 6 CI/CD workflows with canary/blue-green/auto-rollback |
| **Healthcare Standards** | FHIR R4/R5 (6 resources), LOINC/SNOMED/ICD-10/11 models, Westgard QC rules |
| **Clinical Intelligence** | 30+ lab test interpretations (Arabic/English), 15 multi-test patterns |
| **Device Integration** | ASTM/HL7 bridge for Sysmex, Roche, Mindray |
| **Iraqi-Specific** | MoI National ID, SNDHS-lite, IQD claims — unmatched in-market |

---

## Critical Gaps

| # | Gap | Risk Score | Impact |
|---|-----|-----------|--------|
| 1 | **Firebase security bypass** — frontend-v2 writes directly to Firestore, bypassing entire backend security stack | **25/25** | Catastrophic data exposure |
| 2 | **No LICENSE file** — Legal blocker for open source and commercial licensing | **25/25** | Cannot accept contributions or enforce IP |
| 3 | **No legal entity** — Cannot sign contracts or accept payments | **25/25** | Blocks all commercial activity |
| 4 | **No backup restore testing** — DR scripts exist but never verified | **20/25** | Backup corruption could mean total data loss |
| 5 | **AI regulatory violations** — Gemini/Groq in production violate Executive Orders 3&4 (Ollama-only mandate) | **20/25** | Regulatory exposure for Iraqi health data |
| 6 | **Single PostgreSQL** — No HA in production; any failure = complete outage | **15/25** | Availability risk |
| 7 | **Schema/ORM drift** — 70% of tables (200+) have no ORM model | **16/25** | Silent schema divergence |
| 8 | **Test coverage 54%** — Routes 35%, Services 30%, Edge 0% | **12/25** | Production regression risk |

---

## Certification Status

| Certificate | Status | Next Step |
|-------------|--------|-----------|
| **Enterprise Certification** | **BRONZE** (673/1000, Grade D) | Resolve P0 debt → Phase A target 700 |
| Architecture Compliance | **7/100 (F)** — 26 layer violations, 7 circular deps, 365 cross-domain leakages | Reduce violations by 50% |
| Security Posture | **85/100 (B)** | JWT → RS256, secrets rotation, CSRF |
| CI/CD Maturity | **88/100 (B)** | Add staging, SBOM, E2E tests |
| Healthcare Compliance | **72/100 (C)** | ISO 15189 gap analysis, LOINC population |
| Quality Index Path to 800+ | Requires ~720h of remediation across 4 phases | Target: B-Grade by Month 6 |

---

## Top 5 Recommendations

| # | Recommendation | Effort | Impact | Timeline |
|---|---------------|--------|--------|----------|
| 1 | **Fix Firebase security bypass** — Lockdown Firestore to admin-only; proxy all data through backend | 2 weeks (lockdown) / 3 months (full migration) | Eliminates catastrophic data exposure | Month 1 |
| 2 | **Establish legal foundation** — Add AGPL v3 LICENSE, incorporate entity, resolve license contradictions | 1-4 weeks | Unblocks contracts, contributions, revenue | Month 1 |
| 3 | **Deploy PostgreSQL HA** — Patroni + PgBouncer + read replicas; add automated restore testing | 2-3 weeks | Eliminates SPOF, ensures DR works | Month 1-2 |
| 4 | **Resolve AI compliance** — Remove external AI providers or update Executive Orders with guardrails | 1 week | Regulatory compliance; data sovereignty | Month 1 |
| 5 | **Close test coverage gap** — Prioritize route/service coverage from 35/30% to 60%; fix 268 fixture errors | 4-6 weeks | Quality assurance foundation | Month 1-3 |

---

## Investment Ask

| Round | Amount | Purpose | Timeline |
|-------|--------|---------|----------|
| **Seed** | $2M | Product completion (6-8 engineers, 18 months), initial sales, compliance certification | Month 1-3 |
| **Series A** | $10M | Regional expansion (UAE, KSA, Jordan), enterprise sales team, AI/ML R&D, HIPAA/GDPR compliance | Month 12-18 |

### Year 1-3 Revenue Projection (Conservative)

| Metric | Year 1 | Year 2 | Year 3 |
|--------|--------|--------|--------|
| SaaS customers | 50 | 200 | 500 |
| On-prem deployments | 10 | 40 | 100 |
| Government contracts | 1 | 3 | 5 |
| Revenue | $250K | $1.5M | $5M |
| Team size | 8 | 20 | 40 |

### Grant Opportunities
- World Bank Digital Health: $500K-5M
- EU Horizon Europe: €1-10M
- Gates Foundation: $100K-3M
- USAID Digital Health: $500K-5M

---

## The 90-Day Plan

| Week | Action | Owner |
|------|--------|-------|
| 1 | Add LICENSE, fix metadata, unify version | Legal / DevOps |
| 1 | Remove external AI providers | AI Lead |
| 1-2 | Start legal entity incorporation | Founder |
| 1-2 | Implement backup restore testing | DevOps |
| 2-3 | Lockdown Firestore (interim) | Security Lead |
| 3-4 | Deploy PostgreSQL HA | DevOps |
| 4-8 | Close test coverage gaps; fix fixture errors | QA / Backend |
| 4-8 | Start Enterprise presales | Founder / Sales |
| 8-12 | Create staging environment | DevOps |

---

## Conclusion

GULA has a **world-class technical foundation** — the core LIMS is production-capable, the security architecture is strong, and the Iraqi healthcare integration is unmatched. However, **critical legal, operational, and security gaps** must be resolved before the platform can accept revenue, go open source, or scale to enterprise/government deployments.

**The next 90 days determine trajectory.** The platform needs:
1. **$2M seed funding** for 6-8 engineers and compliance
2. **Legal entity + license** to unlock commercial activity
3. **Firebase architecture fix** to close the biggest security hole
4. **Infrastructure hardening** (PG HA, staging, DR testing) for enterprise readiness

With these foundations in place, GULA is positioned to capture the **$23.4B MENA digital health market** and become the **leading sovereign healthcare platform for the Middle East and North Africa**.
