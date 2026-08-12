# Runbook: Backend Down

**Severity:** SEV1
**Response Time:** <15 minutes
**Last Updated:** 2026-07-15

---

## Symptoms

- `/health` returns 503 or timeout
- Users see 502/503 errors
- Backend container in `Exit` or `CrashLoopBackOff` status
- `docker compose ps` shows gula-backend as `exited` or `restarting`
- Monitoring alert: `BackendDown`

## Quick Checks

```bash
# 1. Check backend status
docker compose ps gula-backend

# 2. Check recent logs
docker compose logs --tail=100 gula-backend

# 3. Check resource usage
docker stats --no-stream gula-backend

# 4. Check health endpoints
curl -sf http://localhost:8000/health || echo "Backend not responding"
curl -sf http://localhost:8000/health/ready || echo "Backend not ready"
```

## Possible Causes & Fixes

### Cause 1: Out of Memory (OOM)

**Symptoms:** Container exits with code 137, OOM message in logs, high memory usage before crash

**Check:**
```bash
docker inspect gula-backend --format '{{.State.ExitCode}}'
# Code 137 = SIGKILL (OOM)
docker logs gula-backend --tail 20 | grep -i "memory\|oom\|killed"
```

**Fix:**
```yaml
# Increase memory limit in docker-compose.yml
services:
  gula-backend:
    deploy:
      resources:
        limits:
          memory: 4G  # Increase from current
```

**Then:**
```bash
docker compose up -d --no-deps gula-backend
```

### Cause 2: Configuration Error

**Symptoms:** Backend exits immediately with ImportError or validation error in logs

**Check:**
```bash
docker compose logs --tail=50 gula-backend | grep -i "error\|traceback\|invalid\|missing"
```

**Fix:**
```bash
# Check .env file for missing or invalid values
cat .env | grep -v "^#\|^$"

# Verify each required variable is set
# See .env.example for reference
cp .env.example .env  # Restore from template
# Re-apply production values

# Restart
docker compose up -d --no-deps gula-backend
```

### Cause 3: Database Unreachable

**Symptoms:** Backend logs show `could not connect to server` or `connection refused`

**Check:**
```bash
# Check DB container status
docker compose ps postgres

# Test DB connectivity
docker compose exec postgres pg_isready -U gula

# Check DB logs
docker compose logs --tail=50 postgres | grep -i "error\|fatal\|refused"
```

**Fix:**
```bash
# Restart database
docker compose restart postgres

# Verify DB is accepting connections
sleep 5
docker compose exec postgres pg_isready -U gula

# Restart backend
docker compose up -d --no-deps gula-backend
```

### Cause 4: Code Crash / Unhandled Exception

**Symptoms:** Backend starts, serves some requests, then crashes. Traceback in logs.

**Check:**
```bash
docker compose logs --tail=200 gula-backend | grep -A 20 "Traceback"
```

**Fix:**
```bash
# Rollback to previous working version
docker compose up -d --no-deps gula-backend=previous-tag

# If no previous tag, rebuild without recent changes
git stash
docker compose build gula-backend
docker compose up -d --no-deps gula-backend
```

### Cause 5: Port Conflict

**Symptoms:** Backend fails to bind to port 8000

**Check:**
```bash
# Check if port is in use
sudo lsof -i :8000
netstat -tlnp | grep 8000
```

**Fix:**
```bash
# Kill process using the port
sudo fuser -k 8000/tcp

# Or reconfigure port in .env
# Change PORT=8001
# Update api-gateway config accordingly

# Restart
docker compose up -d --no-deps gula-backend
```

## Resolution Verification

```bash
# 1. Check container is running
docker compose ps gula-backend
# Status should be "Up"

# 2. Check health endpoint
curl -sf http://localhost:8000/health

# 3. Check readiness
curl -sf http://localhost:8000/health/ready

# 4. Check deep health
curl -s http://localhost:8000/health/deep | jq .

# 5. Test API
curl -sf http://localhost:8000/api/test

# 6. Check logs for errors
docker compose logs --since=1m gula-backend | grep -i "error\|exception\|critical"
```

## Escalation

| Time | Action |
|------|--------|
| 0 min | Begin diagnosis |
| 5 min | If not resolved, escalate to secondary on-call |
| 10 min | If SEV1, page Engineering Lead |
| 15 min | If still down, declare SEV1 incident |

### Escalation Contacts

| Role | Contact |
|------|---------|
| Primary on-call | PagerDuty |
| Secondary on-call | PagerDuty |
| Engineering Lead | [Phone] |
| CTO | [Phone] |

## Post-Incident Actions

- [ ] Root cause identified and documented
- [ ] Fix applied to prevent recurrence
- [ ] Runbook updated if new cause discovered
- [ ] Incident report filed
- [ ] Monitoring alert improved (if needed)
