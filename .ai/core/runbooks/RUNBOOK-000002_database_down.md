---
id: RUNBOOK-000002
type: runbook
title: "Database Down Recovery"
version: "1.0"
created: "2026-08-04"
status: verified
confidence: 95%
tags: [incident, database, postgresql, recovery, sev1]
related_skills: []
related_playbooks: []
source: docs/runbooks/database-down.md
---

# RUNBOOK-000002: Database Down Recovery

**Severity:** SEV1
**Response Time:** <15 minutes
**Source:** `docs/runbooks/database-down.md`

## Prerequisites
- [ ] Docker access
- [ ] PostgreSQL admin access
- [ ] Backup verification

## Quick Diagnosis
```bash
# 1. Check database container
docker compose ps postgres

# 2. Check PostgreSQL readiness
docker compose exec postgres pg_isready -U gula

# 3. Check backend logs for DB errors
docker compose logs --tail=50 gula-backend | grep -i "database\|postgres"
```

## Resolution Steps

### Step 1: Check container status
```bash
docker compose ps postgres
# If exited: check OOM, disk, permissions
```

### Step 2: Check disk space
```bash
df -h /var/lib/docker
# If full: clean docker system
docker system prune -f
```

### Step 3: Restart PostgreSQL
```bash
docker compose restart postgres
sleep 5
docker compose exec postgres pg_isready -U gula
```

### Step 4: If restart fails
```bash
docker compose down postgres
docker compose up -d postgres
# Wait for initialization
sleep 10
docker compose exec postgres pg_isready -U gula
```

### Step 5: Verify recovery
```bash
# Test connection
docker compose exec postgres psql -U gula -d gula -c "SELECT 1;"

# Check backend can connect
curl -sf http://localhost:8000/health
```

## Validation
- [ ] PostgreSQL accepting connections
- [ ] Backend health endpoint returns 200
- [ ] No connection errors in logs
- [ ] Data integrity check passes

## Rollback
If data corruption suspected:
```bash
# Stop writes
docker compose stop gula-backend

# Restore from backup
# See docs/runbooks/database-down.md for PITR procedure
```

## Full Reference
See `docs/runbooks/database-down.md` for complete 290-line runbook.
