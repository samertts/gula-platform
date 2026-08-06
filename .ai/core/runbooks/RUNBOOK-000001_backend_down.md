---
id: RUNBOOK-000001
type: runbook
title: "Backend Down Recovery"
version: "1.0"
created: "2026-08-04"
status: verified
confidence: 95%
tags: [incident, backend, docker, recovery, sev1]
related_skills: [SKILL-000002]
related_playbooks: [PLAYBOOK-000002]
source: docs/runbooks/backend-down.md
---

# RUNBOOK-000001: Backend Down Recovery

**Severity:** SEV1
**Response Time:** <15 minutes
**Source:** `docs/runbooks/backend-down.md`

## Prerequisites
- [ ] Docker access (`docker ps`)
- [ ] Server SSH access
- [ ] Monitoring dashboard access

## Quick Diagnosis
```bash
# 1. Check backend status
docker compose ps gula-backend

# 2. Check recent logs
docker compose logs --tail=100 gula-backend

# 3. Check resource usage
docker stats --no-stream gula-backend

# 4. Health check
curl -sf http://localhost:8000/health || echo "Backend not responding"
```

## Resolution Steps

### Step 1: Check container status
```bash
docker compose ps gula-backend
# Expected: running
# If exited: proceed to Step 2
```

### Step 2: Check logs for root cause
```bash
docker compose logs --tail=200 gula-backend 2>&1 | grep -i "error\|fatal\|exception"
```

### Step 3: Common fixes
```bash
# OOM killed — increase memory limit
# Database connection — check postgres status
# Redis connection — check redis status
# Port conflict — check port 5000

# Restart backend
docker compose restart gula-backend
```

### Step 4: If restart fails
```bash
# Rebuild and restart
docker compose down gula-backend
docker compose up -d gula-backend
```

### Step 5: Verify recovery
```bash
curl -sf http://localhost:8000/health
# Should return 200 with status "healthy"
```

## Validation
- [ ] Backend container running
- [ ] Health endpoint returns 200
- [ ] Users can access application
- [ ] No error logs in last 5 minutes

## Rollback
```bash
# If new deployment caused issue
docker compose down
git checkout HEAD~1
docker compose up -d
```

## Full Reference
See `docs/runbooks/backend-down.md` for complete 206-line runbook.
