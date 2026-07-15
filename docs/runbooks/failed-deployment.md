# Runbook: Failed Deployment

**Severity:** SEV2 (partial failure) / SEV1 (full rollback required)
**Response Time:** <15 minutes
**Last Updated:** 2026-07-15

---

## Symptoms

- Health check fails after deployment
- Error rate spikes (monitoring alert: `ErrorRateSpike`)
- Migration errors in deployment logs
- Container in `CrashLoopBackOff` or `Error` state
- Automated rollback triggered
- Users report errors or missing functionality
- Performance regression (latency increase)

## Quick Checks

```bash
# 1. Check deployment status (K8s)
kubectl rollout status deployment/gula-backend -n gula-platform
kubectl get pods -n gula-platform | grep gula-backend

# 2. Check deployment status (Docker)
docker compose ps
docker compose logs --tail=50 gula-backend

# 3. Check migration status
docker compose run --rm gula-backend alembic current

# 4. Check health
curl -sf http://localhost:8000/health/ready

# 5. Check error rate in Grafana
# Look for 5xx spike in last 15 minutes
```

## Possible Causes & Fixes

### Cause 1: Code Error (Runtime)

**Symptoms:** Backend starts but fails on specific requests, traceback in logs

**Check:**
```bash
docker compose logs --tail=200 gula-backend | grep -A 20 "Traceback\|ERROR\|Exception"
```

**Fix — Rollback:**
```bash
# Docker Compose: Rollback to previous tag
docker compose up -d --no-deps gula-backend=<previous-tag>

# K8s Helm: Rollback to previous revision
helm rollback gula-platform 1 --namespace gula-platform

# K8s kubectl: Rollback deployment
kubectl rollout undo deployment/gula-backend -n gula-platform

# Verify rollback
curl -sf http://localhost:8000/health/ready
```

**Fix — Hotfix (if quick):**
```bash
# 1. Identify the problematic commit
git log --oneline -10

# 2. Create hotfix branch
git checkout -b hotfix/deploy-issue-$(date +%Y%m%d)
git revert <problematic-commit>
git push origin hotfix/deploy-issue-$(date +%Y%m%d)

# 3. Rebuild and deploy
docker compose build --no-cache gula-backend
docker compose up -d --no-deps gula-backend

# 4. Verify
curl -sf http://localhost:8000/health/ready
```

### Cause 2: Database Migration Failure

**Symptoms:** Alembic migration fails, tables missing or schema mismatch

**Check:**
```bash
# Check migration logs
docker compose logs --tail=100 gula-backend | grep -i "migration\|alembic\|revision"

# Check current migration state
docker compose run --rm gula-backend alembic current

# Check migration history
docker compose run --rm gula-backend alembic history
```

**Fix — Rollback migration:**
```bash
# 1. Rollback the migration
docker compose run --rm gula-backend alembic downgrade -1

# 2. Verify rollback
docker compose run --rm gula-backend alembic current

# 3. Rollback application code
docker compose up -d --no-deps gula-backend=<previous-tag>

# 4. Fix migration and re-deploy
```

**Fix — Fix forward (preferred for data changes):**
```bash
# 1. Create new migration that fixes the issue
docker compose run --rm gula-backend alembic revision --autogenerate -m "fix_migration_issue"

# 2. Edit migration file to resolve conflict
# Apply the fix

# 3. Run the new migration
docker compose run --rm gula-backend alembic upgrade head

# 4. Re-deploy
docker compose up -d --no-deps gula-backend
```

### Cause 3: Configuration Error

**Symptoms:** Backend fails to start, env var errors in logs

**Check:**
```bash
docker compose logs --tail=50 gula-backend | grep -i "config\|env\|missing\|invalid"
```

**Fix:**
```bash
# 1. Check .env differences
diff .env .env.backup

# 2. Revert to previous config
cp .env.backup .env

# 3. Restart
docker compose up -d --no-deps gula-backend
```

### Cause 4: Resource Limit

**Symptoms:** Container OOM killed, resource limits hit

**Check:**
```bash
docker compose logs --tail=50 gula-backend | grep -i "memory\|oom\|killed\|exit code 137"
```

**Fix:**
```bash
# Increase resource limits in docker-compose.yml
# Then restart
docker compose up -d --no-deps gula-backend
```

### Cause 5: Image Build Failure

**Symptoms:** Container registry doesn't have new image, build pipeline failed

**Check:**
```bash
# Check Docker build in CI
# Check that image was pushed
docker pull ghcr.io/gula-platform/backend:latest

# Verify image exists with correct tag
docker images ghcr.io/gula-platform/backend
```

**Fix:**
```bash
# Option A: Rebuild locally
docker compose build --no-cache gula-backend
docker compose up -d --no-deps gula-backend

# Option B: Fall back to previous known-good image
docker compose up -d --no-deps gula-backend=<known-good-tag>
```

## Rollback Procedure

### Automated Rollback (K8s)

```bash
# Helm rollback
helm rollback gula-platform [REVISION] --namespace gula-platform

# kubectl rollout undo
kubectl rollout undo deployment/gula-backend -n gula-platform

# Wait for rollback to complete
kubectl rollout status deployment/gula-backend -n gula-platform
```

### Automated Rollback (Docker Compose)

```bash
# If using docker-compose with tagged images
docker compose up -d --no-deps gula-backend=<previous-tag>

# If using :latest, rebuild and restart from git history
git checkout <previous-tag>
docker compose build --no-cache gula-backend
docker compose up -d --no-deps gula-backend
```

### Manual Database Rollback

```bash
# Only if migration is the issue and fix-forward is not possible
docker compose run --rm gula-backend alembic downgrade -1

# If multiple migrations need rollback
docker compose run --rm gula-backend alembic downgrade <target-revision>
```

### Full System Rollback

```bash
# 1. Stop all services
docker compose down

# 2. Revert environment
cp .env.backup .env

# 3. Revert docker-compose
git checkout <previous-tag> -- docker-compose.yml

# 4. Run old migration state
docker compose run --rm gula-backend alembic downgrade <target-revision>

# 5. Start services
GULA_IMAGE_TAG=<previous-tag> docker compose up -d

# 6. Verify
make health
make health-deep
```

## Resolution Verification

```bash
# 1. Health check
curl -sf http://localhost:8000/health
curl -sf http://localhost:8000/health/ready

# 2. Deep health
curl -s http://localhost:8000/health/deep | jq .
# Grade should be GREEN

# 3. Error rate check
# Grafana: Check 5xx rate — should be <0.1%

# 4. Migration state
docker compose run --rm gula-backend alembic current

# 5. Smoke test
./scripts/smoke-test.sh

# 6. Performance check
curl -w "p95: %{time_total}s\n" -o /dev/null -s http://localhost:8000/health
```

## Escalation

| Time | Action |
|------|--------|
| 0 min | Begin diagnosis, attempt fix |
| 5 min | If rollback needed, execute immediately |
| 10 min | If rollback fails, escalate to secondary on-call |
| 15 min | If full system rollback needed, declare SEV1 |

## Post-Mortem

- [ ] Root cause identified
- [ ] Fix applied and tested
- [ ] CI/CD pipeline improved (if applicable)
- [ ] Migration policy reviewed (if migration caused issue)
- [ ] Monitoring/alerting improved (if missed by existing checks)
- [ ] Runbook updated with new findings
- [ ] Team notified of changes

## Prevention Checklist

- [ ] Pre-deployment smoke tests pass
- [ ] Migration tested on staging first
- [ ] Feature flags for risky changes
- [ ] Canary deployment for major changes
- [ ] Performance regression tests in CI
- [ ] Rollback plan documented and tested
- [ ] Database migration is backward-compatible
- [ ] Monitoring dashboards reviewed during deployment
