# GULA Platform — Enterprise Discovery Report

**Program:** PROGRAM-02 Enterprise Discovery
**Date:** 2026-07-18
**Classification:** CONFIDENTIAL
**Source:** 17 discovery reports consolidated into canonical inventory

---

## 1. Platform Identity

| Attribute | Value |
|-----------|-------|
| Product | GULA Platform (منصة غولا الصحية) — Medical LIS/LIMS + National Health Platform |
| Version | 2.1.0 (config.py) / 2.3.2 (CHANGELOG.md) — **divergence detected** |
| Deployment | SaaS Multi-Tenant + On-Premise Edge |
| Market | Iraq (Ministry of Health, private labs); MENA digital health ~$23.4B (2025) |
| Language | Arabic-first, English bilingual |
| Codebase | 3,709+ files, 1,421+ directories, ~120K LOC Python |
| Git | 467+ commits across monorepo consolidation |
| Architecture | FastAPI monolith (production) + 8 microservices (6 stubs) |

---

## 2. What Was Found

### Verified Strengths (9 categories)

| Category | Evidence |
|----------|----------|
| **Core LIMS Production-Ready** | Orders, results, samples, QC, patient cards, PDF reports, audit, multi-tenancy |
| **Security Foundation** | JWT auth, RBAC (9 roles × 16 permissions), ABAC, MFA (TOTP + WebAuthn/FIDO2), OAuth2/OIDC provider, SAML 2.0, Fernet encryption, hash-chain audit, rate limiting, circuit breakers, tenant isolation |
| **Self-Healing Infrastructure** | 3-layer: circuit breaker (DB/Redis) → auto-repair engine → adaptive concurrency. Startup guard, 4-level degraded mode |
| **Infrastructure Maturity** | Docker Compose (MVP + Full + Scale), Kubernetes (Kustomize + Helm), Terraform (AWS), 6 CI/CD workflows with canary/blue-green/auto-rollback |
| **Arabic-First Design** | Full Arabic UI, clinical interpretations, PDF reports, RTL support |
| **Iraqi Healthcare Integration** | MoI National ID, SNDHS-lite Phase 1, IQD claims |
| **Healthcare Standards** | FHIR R4/R5 (6 resources), LOINC/SNOMED CT/ICD-10/11 models, Westgard QC rules |
| **Clinical Intelligence** | 30+ lab test interpretations (Arabic/English), 15 multi-test syndrome patterns |
| **Device Integration** | ASTM/HL7 device bridge for Sysmex, Roche, Mindray, generic analyzers |

### Critical Issues (Risk Score 15-25)

| # | Issue | Score | Category |
|---|-------|-------|----------|
| 1 | **Firebase security bypass** — frontend-v2 writes directly to Firestore, bypassing RBAC/ABAC/audit/encryption | **25/25** | Security |
| 2 | **No LICENSE file** — Legal blocker for open source | **25/25** | Legal |
| 3 | **Contradictory license metadata** — MIT vs Proprietary | **25/25** | Legal |
| 4 | **No legal entity** — Cannot sign contracts or accept payments | **25/25** | Organizational |
| 5 | **Patient data exposure via Firebase** — PHI flows through Firestore invisible to backend security | **20/25** | Security |
| 6 | **No backup restore testing** — DR scripts exist but never tested | **20/25** | Infrastructure |
| 7 | **AI provider regulatory violations** — Executive Orders 3&4 mandate Ollama-only; Gemini + Groq in production | **20/25** | Compliance |
| 8 | **No revenue** — Pre-commercial phase | **20/25** | Business |
| 9 | **Single PostgreSQL instance** — No HA in production | **15/25** | Infrastructure |
| 10 | **Schema/ORM drift** — 70% of tables have no ORM model | **16/25** | Technical |

### Major Gaps

| Gap | Severity | Detail |
|-----|----------|--------|
| Test coverage 54% | HIGH | Routes 35%, Services 30%, Edge 0% |
| No staging environment | HIGH | No pre-production validation |
| JWT uses HS256 | HIGH | Symmetric key distribution risk |
| No automated secrets rotation | HIGH | Credentials never rotated |
| 6 microservice stubs | MEDIUM | 6 of 9 services have 0 tests |
| National platform domains schema-only | MEDIUM | 200+ tables with no corresponding code |
| Documentation behind code | MEDIUM | 36 documented vs 53+ actual routes |
| Version tracking divergence | LOW | 2.1.0 vs 2.2.0 vs 2.3.2 |

### Contradictions Found (14 documented)

| ID | Contradiction | Severity |
|----|--------------|----------|
| C1 | Coverage target: ≥95% (Constitution) vs 70% (Digital Constitution) vs 54% actual | CRITICAL |
| C2 | UUID PK mandate vs Integer PK reality | CRITICAL |
| C3 | Architecture layer naming: 3-layer (CLAUDE.md) vs 4-layer (Constitution) | MAJOR |
| C4 | Version: config.py=2.1.0, pyproject.toml=2.2.0, CHANGELOG.md=2.3.2 | MINOR |
| C5 | FHIR strategy: separate route vs content-type on every endpoint | MAJOR |
| C6 | mTLS mandate vs HTTP communications | CRITICAL |
| C7 | SBOM mandate vs no SBOM in CI | MAJOR |
| C8 | Duplicate governance files | MINOR |
| C9 | Superseded document not deprecated | MAJOR |
| C10 | No README per module (Constitution violation) | MAJOR |
| C11 | No circular dependency check in CI | MAJOR |
| C12 | Failed tests contradiction (268 errors vs Q12=0) | MAJOR |
| C13 | Retention policy enforcement missing | MAJOR |
| C14 | AI provider policy violation (EO3/EO4) | CRITICAL |

---

## 3. Technical Debt Summary

| Category | Count | Critical | High | Medium | Low | Est. Effort |
|----------|-------|----------|------|--------|-----|-------------|
| Architecture | 7 | 1 | 1 | 4 | 1 | 4 months |
| Code Quality | 6 | 0 | 4 | 0 | 1 | 4 months |
| Security | 6 | 1 | 2 | 3 | 0 | 2 months |
| Database | 5 | 1 | 1 | 2 | 1 | 1 month |
| Documentation | 6 | 0 | 0 | 4 | 2 | 1 month |
| Infrastructure | 6 | 2 | 1 | 3 | 0 | 2 months |
| **Total (36 items)** | **36** | **5** | **9** | **16** | **5** | **~14 months** |

---

## 4. Healthcare Standards Readiness

| Standard | Status |
|----------|--------|
| Core LIMS | ✅ PRODUCTION |
| FHIR R4/R5 | ⚠️ PARTIAL (6/100+ resources) |
| HL7 v2.x | ⚠️ ASTM only (no ADT/ORM/ORU) |
| DICOM | ❌ NOT IMPLEMENTED |
| LOINC/SNOMED/ICD | ⚠️ Model only (not populated) |
| Clinical CDS | ❌ Schema only |
| Pharmacy/Radiology/Nursing | ❌ Schema only (200+ tables, no routes) |

---

## 5. Business Maturity

| Dimension | Status |
|-----------|--------|
| Prototype | ✅ PASSED |
| MVP | ✅ PASSED |
| Production Ready | ✅ ACHIEVED (Core LIMS) |
| Enterprise Ready | ⚠️ PARTIAL |
| Government Ready | ⚠️ PARTIAL (SNDHS Phase 1 done) |
| Healthcare Ready | ⚠️ PARTIAL |
| International Ready | ❌ NOT YET (Arabic-only, Iraq-focused) |

---

## 6. Top 5 Strategic Recommendations

| # | Recommendation | Effort | Impact |
|---|---------------|--------|--------|
| 1 | **Fix Firebase security bypass** — Lockdown Firestore to admin-only; proxy through backend | 2 weeks (lockdown) / 3 months (full migration) | Eliminates catastrophic data exposure |
| 2 | **Add backup restore testing** — Automated weekly restore with integrity verification | 1 week | Ensures disaster recovery works |
| 3 | **Deploy PostgreSQL HA** — Patroni + PgBouncer + read replicas | 2-3 weeks | Eliminates single point of failure |
| 4 | **Resolve AI provider compliance** — Remove external providers or update Executive Orders | 1 week | Regulatory compliance |
| 5 | **Add legal entity + LICENSE** — Incorporate + AGPL v3 | 1-4 weeks | Unblocks contracts, contributions, revenue |
