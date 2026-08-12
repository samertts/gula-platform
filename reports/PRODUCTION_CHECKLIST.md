# GULA Platform — Production Readiness Checklist

**Date:** 2026-07-15
**Version:** 2.1.0
**Release Tag:** `production-platform-v1.0`

---

## 1. Environment Configuration

- [ ] `.env` file created from `.env.example`
- [ ] `SECRET_KEY` set to strong random value
- [ ] `ENCRYPTION_KEY` set to valid Fernet key
- [ ] `POSTGRES_PASSWORD` set to strong random value
- [ ] `REDIS_PASSWORD` set to strong random value
- [ ] `NID_HMAC_KEY` set to strong random value
- [ ] `REFRESH_TOKEN_SECRET` set to strong random value
- [ ] `CORS_ORIGINS` configured for production domains
- [ ] `IS_PRODUCTION=true` set
- [ ] `RUNTIME_MODE=api` set for API server
- [ ] `FEATURE_BACKGROUND_TASKS=true` set (if worker process)
- [ ] `MAX_CONCURRENT_REQUESTS` configured (default: 200)
- [ ] `ALERT_WEBHOOK_URL` configured (if alerts needed)
- [ ] `SENTRY_DSN` configured (optional)

## 2. Secrets Management

- [ ] All secrets generated via `make secrets-gen`
- [ ] No weak/default secrets present (checked by `config.py` startup guard)
- [ ] Secrets not hardcoded in any source file
- [ ] `.env` file excluded from version control (gitignored)
- [ ] Encryption keys rotated from defaults

## 3. Database

- [ ] PostgreSQL 16 running
- [ ] All migrations applied: `alembic upgrade head`
- [ ] Base schema migration executed (`20250322_0000_create_base_schema.py`)
- [ ] SNDHS Phase 1 migrations applied (if flags enabled)
- [ ] Financial Engine migrations applied (if flags enabled)
- [ ] Database backups configured (`make backup` or cron)
- [ ] Connection pool settings verified:
  - `DB_POOL_SIZE` (default: 6)
  - `DB_MAX_OVERFLOW` (default: 12)
  - `WEB_CONCURRENCY` (default: 3)
  - Total: 3 × (6 + 12) = 54 < PostgreSQL max_connections (100)
- [ ] Read replica configured (if high availability needed)

## 4. Redis

- [ ] Redis 7 running
- [ ] `REDIS_PASSWORD` configured
- [ ] Redis persistence configured (RDB/AOF)
- [ ] Redis maxmemory policy configured
- [ ] Redis backup configured

## 5. TLS / HTTPS

- [ ] TLS certificates installed on host nginx
- [ ] Certificate auto-renewal configured (certbot/cert-renew.sh)
- [ ] HTTP→HTTPS redirect configured
- [ ] HSTS header enabled (`Strict-Transport-Security: max-age=31536000`)
- [ ] TLS 1.2+ only (no TLS 1.0/1.1)

## 6. Monitoring

- [ ] Prometheus scrape config configured
- [ ] Grafana dashboards provisioned
- [ ] `METRICS_BEARER_TOKEN` generated and set
- [ ] Health alert watchdog configured with `ALERT_WEBHOOK_URL`
- [ ] `/health/deep` accessible and returning GREEN grade
- [ ] Health check interval configured (default: 60s)
- [ ] RED state alerting configured (10s retry, 5min reminder)

## 7. Backups

- [ ] Database backup schedule configured (`make backup` or cron)
- [ ] Backup destination verified (local `./backups/` or S3)
- [ ] Backup retention policy configured
- [ ] Backup encryption configured
- [ ] Restore test completed successfully (`scripts/restore-test.sh`)
- [ ] PITR (Point-In-Time Recovery) configured (`scripts/pitr-recover.sh`)

## 8. Security Hardening

- [ ] All `requirements.txt` dependencies scanned (safety, bandit)
- [ ] No high/medium severity vulnerabilities
- [ ] Gitleaks scan passed (no secrets in repo)
- [ ] CSP headers configured and tested
- [ ] Rate limiting configured (per-IP + per-user)
- [ ] Max body size limit configured (10 MB default)
- [ ] CORS origins restricted to known domains
- [ ] API docs protected (admin JWT required in production)
- [ ] Circuit breaker thresholds configured
- [ ] Intrusion detection enabled

## 9. Disaster Recovery

- [ ] Disaster recovery plan documented (`scripts/dr-recovery.sh`)
- [ ] Failover procedure tested (`scripts/dr-failover.sh`)
- [ ] Failback procedure verified (`scripts/dr-failback.sh`)
- [ ] DR test completed (`scripts/dr-test.sh`)
- [ ] Emergency repair script available (`scripts/emergency-fix.sh`)
- [ ] Droplet repair script available (`scripts/repair-droplet.sh`)
- [ ] Kill switch mechanism available (`make kill-switch-on` / `make kill-switch-off`)

## 10. Network & Firewall

- [ ] API gateway on 127.0.0.1:8080 (not exposed directly)
- [ ] Host nginx owns ports 80/443
- [ ] PostgreSQL port (5432) not exposed to internet
- [ ] Redis port (6379) not exposed to internet
- [ ] Firewall rules restrict access to essential ports only
- [ ] SSH access restricted (key-based only)
- [ ] Fail2ban or similar configured

## 11. Deployment

- [ ] Docker Compose stack running (`make up`)
- [ ] All containers healthy (`make ps`)
- [ ] Health check passing (`make health-deep`)
- [ ] Smoke test passed (`scripts/smoke-bootstrap.sh`)
- [ ] API endpoints responding correctly
- [ ] Database connections working
- [ ] Redis cache working
- [ ] Static assets served correctly

## 12. Validation

- [ ] Syntax gate passed (`py_compile` on all Python files)
- [ ] Lint gate passed (`flake8 --select=E9,F821`)
- [ ] All tests passing (`make test`)
- [ ] CI pipeline green
- [ ] Kernel boot completed (12-phase initialization)
- [ ] All 52 capabilities registered and active
- [ ] Feature flags configured per-tenant
- [ ] Release tagged (`production-platform-v1.0`)

---

### Sign-off

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Platform Lead | | | |
| Security Officer | | | |
| DevOps Engineer | | | |
| QA Lead | | | |

---

*Checklist generated by GULA Production Freeze Agent on 2026-07-15 12:45 UTC*
