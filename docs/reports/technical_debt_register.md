# GULA Technical Debt Register

**Version:** 1.0  
**Date:** 2026-07-18  
**Classification:** INTERNAL  

---

## Classification

| Severity | Definition | Response Time |
|----------|-----------|---------------|
| CRITICAL | Blocks development, production risk, security vulnerability | Immediate |
| HIGH | Significant maintenance burden, performance impact, safety concern | Within 30 days |
| MEDIUM | Moderate impact, should be addressed in normal work | Within 90 days |
| LOW | Minor improvement, no immediate impact | Within 180 days |

---

## Critical Items

| ID | Item | Location | Impact | Cost Est. | Owner |
|----|------|----------|--------|-----------|-------|
| TD-C01 | main.py at 1,948 lines | `backend/app/main.py` | Single-file bottleneck; hard to test, reason about, or modify | 2 weeks | Architecture |
| TD-C02 | 70 top-level packages | `backend/app/*/` | Inconsistent module naming, no clear taxonomy, hard onboarding | 4 weeks | Architecture |
| TD-C03 | 268 fixture collection errors | `backend/tests/` | Undermines CI confidence, hides real failures | 1 week | QA |
| TD-C04 | Two circuit breaker implementations | `core/self_healing.py` + `kernel/gateway/circuit_breaker.py` | Maintenance divergence, inconsistent behavior under load | 2 weeks | Architecture |
| TD-C05 | Two feature flag systems | `core/feature_flags.py` + `kernel/features/` | Dual origin of truth, inconsistent flag evaluation | 2 weeks | Architecture |
| TD-C06 | Two DI systems | Legacy import-time + Kernel DI container | Dual paradigms, Kernel modules can't use legacy services | 3 weeks | Architecture |
| TD-C07 | Route layer bypasses services (direct model imports) | `routes/*.py` importing `models/*.py` directly | Architecture violation, bypasses business logic | 3 weeks | Engineering |

## High Items

| ID | Item | Location | Impact | Cost Est. | Owner |
|----|------|----------|--------|-----------|-------|
| TD-H01 | Routes test coverage at 35% | `routes/*.py` | Production risk in 50+ route modules | 4 weeks | QA |
| TD-H02 | Services test coverage at 30% | `services/*.py` | Business logic not validated | 4 weeks | QA |
| TD-H03 | No FHIR API server | `backend/app/` | Cannot serve FHIR resources despite having mappers | 4 weeks | Interop |
| TD-H04 | Vector store in-memory only | `ai_fabric/rag.py` | RAG state lost on restart, not production-ready | 2 weeks | AI |
| TD-H05 | Domain logic scattered across 15+ directories | `domain/` only has order_state.py; other domains in their own directories | Fragmented domain knowledge, no single source of truth | 3 weeks | Architecture |
| TD-H06 | Agent implementations are stub-level | `ai_fabric/agents/*.py` | 5 agents registered but no real LLM integration | 3 weeks | AI |
| TD-H07 | Kernel runtime cannot reference `app/runtime` | `app/kernel/ai_runtime` referenced but doesn't exist | Dead code path, broken initialization | 1 week | Architecture |
| TD-H08 | `except: pass` patterns | Multiple locations | Silent error swallowing, hard to debug production issues | 1 week | Engineering |
| TD-H09 | Hospital module is stub | `backend/app/hospital/` | Major domain gap | 4 weeks | Healthcare |
| TD-H10 | No frontend automated tests | `frontend-v2/` | UI regression risk, no validation of clinical workflows | 4 weeks | Frontend |
| TD-H11 | CD deployment not in CI workflows | `.github/workflows/` | Deploy scripts exist but not automated in CI/CD | 3 weeks | DevOps |
| TD-H12 | RBAC data in external shared library | `shared.rbac` | Hard dependency, cannot modify roles without shared library update | 2 weeks | Security |

## Medium Items

| ID | Item | Location | Impact | Cost Est. | Owner |
|----|------|----------|--------|-----------|-------|
| TD-M01 | Domain imports from FastAPI | `domain/order_state.py: from fastapi import HTTPException` | Domain layer depends on framework | 1 week | Architecture |
| TD-M02 | Module-level globals prevent test isolation | `database.py`, `self_healing.py`, `main.py` | Hard to mock, test pollution | 2 weeks | Engineering |
| TD-M03 | Inconsistent route naming | `routes/*.py` | Some describe domain, some describe mechanism, some describe feature flag | 1 week | Architecture |
| TD-M04 | Empty `__init__.py` files | Most `__init__.py` are empty | No explicit public API boundaries | 1 week | Architecture |
| TD-M05 | No remote debugging configuration | `docker-compose.yml` | Hard to debug issues in deployed containers | 1 week | DevOps |
| TD-M06 | Load tests not in CI | `tests/load/`, `k6/` | Performance regression not caught automatically | 2 weeks | QA |
| TD-M07 | Placeholder values in Alertmanager | `config/alertmanager/alertmanager.yml` | Production alerting not fully operational | 1 day | DevOps |
| TD-M08 | No SLA/SLO dashboard | `config/grafana/dashboards/` | SLO rules exist but no visualization | 1 week | Observability |
| TD-M09 | SQLite for tests (not PG) | `backend/tests/conftest.py` | PG-specific features (JSONB, array) not tested | 1 week | QA |
| TD-M10 | No automated E2E tests | `backend/tests/` | Full-stack workflows never validated automatically | 3 weeks | QA |
| TD-M11 | Lazy imports in exception handlers | `database.py` lines 422, 441, 463 | Runtime cost during error recovery | 1 week | Engineering |
| TD-M12 | Per-worker concurrency limit | `main.py` ConcurrencyLimitMiddleware | Total capacity = workers × _MAX_CONCURRENT, not shared | 2 weeks | Architecture |
| TD-M13 | No hot-reload configuration | `backend/app/config.py` | Env var changes require process restart | 2 weeks | Engineering |
| TD-M14 | CD scripts not in GitHub Actions | `scripts/deploy.sh`, `scripts/blue-green-deploy.sh`, etc. | Script-based, not workflow-based deployment | 2 weeks | DevOps |

## Low Items

| ID | Item | Location | Impact | Cost Est. | Owner |
|----|------|----------|--------|-----------|-------|
| TD-L01 | No multi-language support | `frontend-v2/` documentation | Arabic-first design good; no formal i18n infrastructure | 3 weeks | Frontend |
| TD-L02 | No multi-currency support | N/A | Not yet needed; not blocking | - | Future |
| TD-L03 | No external synthetic monitoring | N/A | Smoke tests only at deploy time | 1 week | DevOps |
| TD-L04 | No performance regression CI gate | `.github/workflows/ci.yml` | Performance not benchmarked in CI | 2 weeks | QA |
| TD-L05 | No SBOM attestation in CI | `.github/workflows/ci.yml` | SBOM generation exists but not CI-gated | 1 week | DevOps |
| TD-L06 | No IHE profile support | N/A | Future requirement | - | Future |
| TD-L07 | No SMART on FHIR | N/A | Future requirement | - | Future |
| TD-L08 | No formal threat modeling | N/A | Process exists but not documented | 2 weeks | Security |
| TD-L09 | No pen test performed | N/A | DAST configured; external pen test planned | 4 weeks | Security |
| TD-L10 | Multi-region only in K8s/Terraform, not Docker Compose | N/A | MVP has no DR path | 3 weeks | DevOps |

## Technical Debt Summary

| Severity | Count | Est. Total Effort |
|----------|-------|-------------------|
| CRITICAL | 7 | 17 weeks |
| HIGH | 12 | 33 weeks |
| MEDIUM | 14 | 20 weeks |
| LOW | 10 | 13 weeks |
| **Total** | **43** | **83 weeks** |

## Top 10 Priority Items (by Risk/Cost Ratio)

| Rank | ID | Item | Severity | Effort | Risk Reduction |
|------|----|------|----------|--------|----------------|
| 1 | TD-C03 | Fix 268 fixture errors | CRITICAL | 1 week | CI reliability, test confidence |
| 2 | TD-C01 | Extract main.py | CRITICAL | 2 weeks | Maintainability, onboarding |
| 3 | TD-H01 | Increase routes coverage to 60% | HIGH | 4 weeks | Production risk reduction |
| 4 | TD-H03 | Implement FHIR API server | HIGH | 4 weeks | Interoperability gap |
| 5 | TD-C07 | Fix route/service direct model imports | CRITICAL | 3 weeks | Architecture compliance |
| 6 | TD-H04 | Connect pgvector | HIGH | 2 weeks | AI production readiness |
| 7 | TD-C02 | Consolidate to 15-25 top-level modules | CRITICAL | 4 weeks | Architecture clarity |
| 8 | TD-C04/TD-C05 | Unify circuit breaker and feature flags | CRITICAL | 4 weeks | Eliminate dual systems |
| 9 | TD-H05 | Consolidate domain logic | HIGH | 3 weeks | Domain integrity |
| 10 | TD-H10 | Add frontend E2E tests | HIGH | 4 weeks | UI regression prevention |

---

*This register is a living document. Items should be reviewed and reprioritized quarterly.*
