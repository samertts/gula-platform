# GULA Platform — Technical Debt Register
**Date:** 2026-07-17

---

## 1. Architecture Debt

| ID | Debt | Location | Impact | Effort | Priority |
|----|------|----------|--------|--------|----------|
| AD01 | **Monster route files** | ehr.py (73KB), compliance.py (47KB), clinical.py (41KB) | Maintainability, testability | 2 weeks | High |
| AD02 | **Dual AI engine** | services/ai (Ollama-only) vs routes/ai.py (multi-provider) | Fragmentation, confusion | 1 week | Medium |
| AD03 | **Dual frontend architecture** | frontend-v2 (Firebase) vs client (tRPC) | Security, alignment | 3 months | Critical |
| AD04 | **6 microservice stubs** | lab, order, patient, result, sample, notification | Dead code, maintenance overhead | 2 weeks | Medium |
| AD05 | **Deprecated services/shared** | Bridge to canonical shared/ | Confusion | 1 day | Low |
| AD06 | **AWS Terraform for DO** | IaC targets wrong platform | Mismatched infrastructure | 2 weeks | Medium |
| AD07 | **National platform schema-only** | 200+ tables with no code | Dead schema, migration overhead | Unknown | Medium |

---

## 2. Code Quality Debt

| ID | Debt | Location | Impact | Effort | Priority |
|----|------|----------|--------|--------|----------|
| CQ01 | **Low route test coverage (35%)** | routes/ | Quality risk | 4 weeks | High |
| CQ02 | **Low service test coverage (30%)** | services/ | Quality risk | 3 weeks | High |
| CQ03 | **Zero edge/interop tests** | edge/ | Quality risk | 2 weeks | High |
| CQ04 | **No frontend tests** | frontend-v2/ | Quality risk | 4 weeks | High |
| CQ05 | **No E2E tests** | Entire platform | Integration risk | 3 weeks | High |
| CQ06 | **Duplicate clinical engine logic** | interpretation.py, clinical_intelligence.py, clinical_engine.py | Maintenance overhead | 1 week | Low |

---

## 3. Security Debt

| ID | Debt | Location | Impact | Effort | Priority |
|----|------|----------|--------|--------|----------|
| SD01 | **HS256 JWT (symmetric key)** | security/auth.py | No key distribution | 1 week | High |
| SD02 | **No JWT kid header** | security/auth.py | No key rotation | 1 day | Medium |
| SD03 | **No automated secrets rotation** | CI/CD | Credential aging | 2 weeks | High |
| SD04 | **Firestore security bypass** | frontend-v2/ | No audit trail | 1 month | Critical |
| SD05 | **Emergency break-glass audit-only** | security/consent_dep.py | No second factor | 1 week | Medium |
| SD06 | **OIDC uses HMAC for id_tokens** | security/oauth2_provider.py | Compliance gap | 1 week | Medium |

---

## 4. Database Debt

| ID | Debt | Location | Impact | Effort | Priority |
|----|------|----------|--------|--------|----------|
| DB01 | **Version divergence (2.1.0 vs 2.3.2)** | config.py vs CHANGELOG.md | Tracking confusion | 1 day | Low |
| DB02 | **Massive same-day migrations** | 17 files on 2026-07-16 | Review burden | 1 week | High |
| DB03 | **No VACUUM/ANALYZE automation** | PostgreSQL | Performance decline | 1 day | Medium |
| DB04 | **Single PG in production** | docker-compose.yml | No HA | 2 weeks | Critical |
| DB05 | **No partition management for audit_logs** | PostgreSQL at scale | Performance risk | 1 week | Medium |

---

## 5. Documentation Debt

| ID | Debt | Location | Impact | Effort | Priority |
|----|------|----------|--------|--------|----------|
| DD01 | **Route count mismatch (36 vs 53+)** | CLAUDE.md | Misleading documentation | 2 days | Medium |
| DD02 | **Model count mismatch (17 vs 60+)** | CLAUDE.md | Misleading documentation | 2 days | Medium |
| DD03 | **MySQL reference instead of PG** | INFRASTRUCTURE_GUIDE.md | Confusion | 1 hour | Low |
| DD04 | **Missing consumer API changelog** | docs/ | Breaking changes risk | 2 days | Medium |
| DD05 | **Missing Arabic user manual** | docs/ | User friction | 2 weeks | Medium |
| DD06 | **Missing on-premise deployment guide** | docs/ | Deployment friction | 3 days | Medium |

---

## 6. Infrastructure Debt

| ID | Debt | Location | Impact | Effort | Priority |
|----|------|----------|--------|--------|----------|
| ID01 | **No staging environment** | k8s/overlays/ | Pre-production risk | 2 weeks | Critical |
| ID02 | **No backup restore testing** | scripts/ | DR risk | 1 week | Critical |
| ID03 | **No automated secrets rotation** | CI/CD | Security risk | 2 weeks | High |
| ID04 | **No synthetic monitoring** | monitoring | Blind to issues | 1 week | Medium |
| ID05 | **K8s overlays but not primary deployment** | k8s/ | Maintenance overhead | 1 month | Medium |
| ID06 | **No APM integration** | monitoring | Performance blind | 2 weeks | Medium |

---

## 7. Debt Summary

| Category | Count | Critical | High | Medium | Low | Estimated Effort |
|----------|-------|----------|------|--------|-----|-----------------|
| Architecture | 7 | 1 | 1 | 4 | 1 | 4 months |
| Code Quality | 6 | 0 | 4 | 0 | 1 | 4 months |
| Security | 6 | 1 | 2 | 3 | 0 | 2 months |
| Database | 5 | 1 | 1 | 2 | 1 | 1 month |
| Documentation | 6 | 0 | 0 | 4 | 2 | 1 month |
| Infrastructure | 6 | 2 | 1 | 3 | 0 | 2 months |
| **Total** | **36** | **5** | **9** | **16** | **5** | **~14 months** |

---

## 8. Top 5 Debt Items by Urgency

| Rank | ID | Debt | Category | Action |
|------|----|------|----------|--------|
| 1 | SD04 | Firestore security bypass | Security | Migrate frontend-v2 to backend API |
| 2 | DB04 | Single PG instance | Database | Deploy HA PostgreSQL |
| 3 | ID02 | No backup restore testing | Infrastructure | Automate restore testing |
| 4 | ID01 | No staging environment | Infrastructure | Create staging environment |
| 5 | CQ01 | Low route test coverage | Code Quality | Add integration tests |
