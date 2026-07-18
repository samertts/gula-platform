# GULA Platform — Contradiction Detection
**Date:** 2026-07-17

---

## 1. Version Contradiction

| Source | Value |
|--------|-------|
| `backend/app/config.py` | `APP_VERSION = "2.1.0"` |
| `CHANGELOG.md` | Latest entry: v2.3.2 |
| `helm/gula-platform/Chart.yaml` | `appVersion: "2.1.0"` |

**Conclusion**: Version tracking is inconsistent. CHANGELOG tracks 2.3.2, code says 2.1.0.

---

## 2. Route Count Contradiction

| Source | Claimed Count | Actual Count |
|--------|---------------|--------------|
| CLAUDE.md | "36 route modules" | **53+** route modules |
| `backend/app/routes/` | Documented: auth, labs, orders, results, samples | Actual: clinical, EHR, FHIR, compliance, national, edge, AI, hospital, etc. |

**Conclusion**: Documentation is significantly behind implementation.

---

## 3. Architecture Contradiction

| Document | Claim | Evidence | Contradiction |
|----------|-------|----------|---------------|
| CLAUDE.md | "Monolith is source of truth" | 9 microservices in services/ with Dockerfiles | Microservices exist but are stubs |
| CLAUDE.md | "backend/app/ is production" | services/ai/ is functional | Duplicate AI engine |
| MASTER_SYSTEM_ATLAS | Full system atlas | 17 migrations from 2026-07-16 (1 day) | Schema churn contradicts "stable" claim |
| ARCHITECTURE.md | Clean architecture | ehr.py (73KB), compliance.py (47KB) | Architectural violation (monster files) |

---

## 4. AI Contradiction

| Rule | Claim | Evidence | Violation |
|------|-------|----------|-----------|
| Executive Order 3 | "Only local Ollama AI" | `routes/ai.py` uses Gemini + Groq | **VIOLATED** |
| Executive Order 4 | "No external AI providers" | `gateways/google_ai.py` exists | **VIOLATED** |
| Executive Order 19 | "Three AI tiers" | Implemented in `services/ai/main.py` | Compliant |

---

## 5. Database Contradiction

| Document | Claim | Evidence |
|----------|-------|----------|
| CLAUDE.md | "17 SQLAlchemy ORM models" | **60+ model files** with ~250 tables |
| CLAUDE.md | "PostgreSQL 16" | full.yml uses postgres:14.11-alpine |
| INFRASTRUCTURE_GUIDE.md | Mentions MySQL | Codebase uses PostgreSQL exclusively |
| 2026-07-16 migrations | 17 migrations same day | Massive schema churn in 24 hours |

---

## 6. Security Contradiction

| Document | Claim | Evidence |
|----------|-------|----------|
| CLAUDE.md | "9 roles × 13 permissions" | Code has **10 roles × 16 permissions** (enums + strings) |
| SECURITY.md | "Only backend auth" | frontend-v2 uses Firebase Auth (bypasses backend) |
| CLAUDE.md "security invariants" | "All patient-data queries filter by lab_id" | Firebase Firestore bypasses this completely |

---

## 7. Infrastructure Contradiction

| Document | Claim | Evidence |
|----------|-------|----------|
| DEPLOYMENT_PLATFORMS.md | "Render, Supabase, DigitalOcean" | MVP deployment happens via `docker-compose.yml` |
| Terraform targets | AWS (RDS, EKS, ElastiCache) | Actual deployment is Docker Compose on DigitalOcean |
| docker-compose.full.yml | Full HA with PG14 | MVP docker-compose.yml uses PG16 |
| CLAUDE.md | "app version: 2.1.0" (config.py) | Helm Chart agrees (2.1.0) but CHANGELOG says 2.3.2 |

---

## 8. Quality Contradiction

| Document | Claim | Evidence |
|----------|-------|----------|
| CLAUDE.md | "28 test modules" | **77+ test files** in backend/tests/ |
| TESTING.md | "54% coverage" | Routes 35%, Services 30% — below 70% target |
| CLAUDE.md | "Production ready" | 6 microservice stubs with 0 tests |

---

## 9. Business Contradiction

| Document | Claim | Evidence |
|----------|-------|----------|
| BUSINESS_PLAN.md | "$100–$10,000+/mo pricing" | No evidence of payment processing implementation |
| BUSINESS_PLAN.md | "50 customers Y1" | No evidence of any customers |
| MARKETING_STRATEGY.md | "4 segments" | Only LIMS functionality delivered |

---

## 10. Documentation vs Implementation Contradictions (Summary)

| Area | Documented | Actual | Impact |
|------|-----------|--------|--------|
| Routes | 36 | 53+ | High |
| Models | 17 | 60+ | High |
| Version | 2.1.0 | 2.3.2 | Low |
| DB Engine | PG16 | PG14 (full.yml) | Medium |
| AI Provider | Ollama-only | Ollama + Gemini + Groq | High |
| Microservices | Ready | 6/9 are stubs | High |
| Roles × Perms | 9 × 13 | 10 × 16 | Medium |
| Tests | 28 modules | 77+ files | Low (understated) |
| RBAC location | backend/app/security/ | Delegates to shared/ | Low |
