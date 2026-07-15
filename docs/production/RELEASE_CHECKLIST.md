# GULA Platform — Release Checklist

**Release:** production-platform-v1.0
**Date:** 2026-07-15
**Release Manager:** [Name]

---

## Pre-Release

### Code Quality

- [ ] All code changes reviewed and approved
- [ ] No unresolved PR comments
- [ ] All CI checks passing
  - [ ] syntax-gate
  - [ ] migration-check
  - [ ] smoke-test
  - [ ] backend-test
  - [ ] security-scan
  - [ ] build-and-push

### Quality Gates (9 Gates)

#### Architecture Gate

- [ ] No violations of Clean Architecture principles
- [ ] No circular dependencies introduced
- [ ] All new modules follow established patterns
- [ ] ADR created for any architectural changes
- [ ] Backward compatibility maintained

#### Performance Gate

- [ ] Load test passed (200 req/s, p95 < 500ms)
- [ ] No performance regression >10% from baseline
- [ ] No N+1 queries introduced
- [ ] All database queries have proper indexes
- [ ] Cache utilization reviewed

#### Security Gate

- [ ] SAST scan: 0 HIGH findings
- [ ] DAST scan: 0 HIGH findings
- [ ] Dependency scan: 0 CRITICAL findings
- [ ] Secret scan: 0 findings
- [ ] Container scan: 0 CRITICAL, 0 HIGH
- [ ] IaC scan: 0 errors
- [ ] No hardcoded secrets introduced
- [ ] All new endpoints have proper auth checks
- [ ] Tenant isolation verified for new features

#### Accessibility Gate

- [ ] Arabic language support verified
- [ ] RTL layout tested
- [ ] Keyboard navigation works
- [ ] Screen reader compatibility verified
- [ ] Color contrast meets WCAG AA standards
- [ ] Error messages are in Arabic

#### Offline Gate

- [ ] Offline mode works (frontend)
- [ ] Queue-based sync works for offline operations
- [ ] Conflict resolution tested
- [ ] Reconnection logic tested

#### FHIR Gate

- [ ] New endpoints are FHIR-compatible
- [ ] FHIR resource mappings are correct
- [ ] FHIR validation passes
- [ ] FHIR search parameters work

#### Database Gate

- [ ] All migrations are idempotent
- [ ] Migration tested on clean database
- [ ] Migration reversible (downgrade works)
- [ ] No data loss on migration
- [ ] Migration performance tested (>1M rows)
- [ ] New columns are nullable or have defaults
- [ ] No existing migrations modified
- [ ] Foreign keys and constraints verified

#### API Gate

- [ ] API response shape documented
- [ ] OpenAPI spec updated
- [ ] API versioning strategy followed
- [ ] Rate limiting configured for new endpoints
- [ ] Input validation comprehensive
- [ ] Error responses consistent format
- [ ] All endpoints return JSON

#### Scalability Gate

- [ ] Horizontal scaling verified
- [ ] Auto-scaling HPA configured
- [ ] Connection pool limits reviewed
- [ ] Resource limits configured for all containers
- [ ] Database index strategy reviewed

### Security Scans

- [ ] SAST (Bandit + Semgrep) — 0 HIGH
- [ ] DAST (OWASP ZAP) — 0 HIGH
- [ ] Dependency scan (Safety) — 0 CRITICAL
- [ ] Secret scan (Gitleaks) — 0 findings
- [ ] Container scan (Trivy) — 0 CRITICAL, 0 HIGH
- [ ] IaC scan (Checkov) — 0 errors
- [ ] License scan (FOSSA) — PASS
- [ ] SBOM generated

### Performance Tests

- [ ] Load test (200 req/s, p95 < 500ms, p99 < 1000ms)
- [ ] Stress test (breaking point documented)
- [ ] Spike test (sudden 10x load, recovery < 1 min)
- [ ] Soak test (24h at 200 req/s, no degradation)
- [ ] Database migration performance test
- [ ] End-to-end flow test (create patient → order → result)

### Documentation

- [ ] Production Guide reviewed and updated
- [ ] Deployment Guide reviewed and updated
- [ ] Operations Guide reviewed and updated
- [ ] Disaster Recovery Guide reviewed and updated
- [ ] Security Operations Guide reviewed and updated
- [ ] All runbooks reviewed and updated
- [ ] API documentation updated (OpenAPI)
- [ ] Architecture Decision Records updated
- [ ] Release notes prepared
- [ ] CHANGELOG.md updated
- [ ] README.md updated (if applicable)

### Infrastructure

- [ ] Production environment verified
- [ ] Staging environment matches production
- [ ] DNS records verified
- [ ] TLS certificates valid (>30 days to expiry)
- [ ] Backup system operational
- [ ] DR procedures tested
- [ ] Monitoring dashboards updated
- [ ] Alerts configured and tested
- [ ] Log retention configured
- [ ] Metric thresholds tuned

### Team Preparedness

- [ ] On-call team notified of release
- [ ] Rollback plan documented and tested
- [ ] Post-deployment smoke tests prepared
- [ ] Communication plan ready
- [ ] Stakeholder notification drafted
- [ ] Engineering Lead approval obtained
- [ ] CTO sign-off obtained

---

## Release Day

### Pre-Deployment

- [ ] Final code review of all changes
- [ ] CI pipeline green on target commit
- [ ] Docker images built and pushed to registry
- [ ] Image tag verified (SHA256 match)
- [ ] `.env` configuration verified
- [ ] Database migration scripts ready
- [ ] Feature flags confirmed (disabled if risky)
- [ ] Backup taken (pre-deployment snapshot)
- [ ] Monitoring dashboards open and visible
- [ ] Release manager confirmed on-call
- [ ] Stakeholders notified of maintenance window

### Deployment Steps

- [ ] Database migration executed
  - Command: `docker compose run --rm gula-backend alembic upgrade head`
  - Verification: `docker compose run --rm gula-backend alembic check`
- [ ] Backend deployed (blue-green or rolling)
  - Blue-green: Deploy green, smoke test, switch traffic
  - Rolling: One replica at a time, verify after each
- [ ] Frontend deployed
  - `cd frontend-v2 && npm run build && npm run deploy`
- [ ] Worker processes deployed
  - `docker compose up -d --no-deps gula-worker`

### Post-Deployment Verification

- [ ] `/health` returns 200
- [ ] `/health/ready` returns 200
- [ ] `/health/deep` returns grade GREEN
- [ ] All containers running (`docker compose ps`)
- [ ] Database migrations at correct revision
- [ ] Auth endpoints functional
- [ ] Patient CRUD operations work
- [ ] Order creation and result entry work
- [ ] Search endpoints return results
- [ ] TLS certificate valid
- [ ] No ERROR/CRITICAL logs in last 5 minutes
- [ ] Error rate < 0.1% in Grafana
- [ ] Latency p95 < 200ms
- [ ] Redis cache warming (hit rate increasing)
- [ ] Queue consumers processing messages
- [ ] Alerts firing correctly
- [ ] Smoke tests pass
- [ ] Integration tests pass

### Post-Deployment

- [ ] Monitoring period (30 minutes min)
- [ ] Release tagged in git
  - Command: `git tag -a production-platform-v1.0 -m "Production Platform v1.0"`
  - Command: `git push origin production-platform-v1.0`
- [ ] Release notes published
- [ ] CHANGELOG.md updated
- [ ] Stakeholders notified
- [ ] Incident channel archived (if no issues)
- [ ] Post-release review scheduled (48h after)

---

## Rollback Plan

### Automatic Rollback Triggers

The deployment will automatically roll back if any of these conditions are met within 15 minutes:

- [ ] Health check fails for >30 seconds
- [ ] Error rate increases by >2%
- [ ] p99 latency increases by >50%
- [ ] Database circuit breaker opens

### Manual Rollback Procedure

```bash
# Step 1: Revert backend
docker compose up -d --no-deps gula-backend=<previous-tag>

# Step 2: Revert frontend
cd frontend-v2 && git checkout <previous-tag> && npm run build && npm run deploy

# Step 3: Revert database migration (if migration was applied)
docker compose run --rm gula-backend alembic downgrade -1

# Step 4: Verify rollback
make health && make health-deep

# Step 5: Notify stakeholders
```

---

## Sign-off

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Release Manager | | | |
| Engineering Lead | | | |
| QA Lead | | | |
| Security Lead | | | |
| CTO | | | |

---

*This checklist must be completed for every production release. Partial completion will block the release.*
