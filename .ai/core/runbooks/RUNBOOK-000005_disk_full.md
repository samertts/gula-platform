---
id: RUNBOOK-000005
type: runbook
title: "Disk Full Recovery"
version: "1.0"
created: "2026-08-04"
status: verified
confidence: 90%
tags: [incident, disk, storage, recovery]
source: docs/runbooks/disk-full.md
---

# RUNBOOK-000005: Disk Full Recovery

**Severity:** SEV2
**Response Time:** <30 minutes
**Source:** `docs/runbooks/disk-full.md`

## Quick Diagnosis
```bash
# 1. Check disk usage
df -h

# 2. Find large files
du -sh /* 2>/dev/null | sort -rh | head -10

# 3. Docker disk usage
docker system df
```

## Resolution Steps

### Step 1: Docker cleanup (safe)
```bash
# Remove stopped containers
docker container prune -f

# Remove dangling images
docker image prune -f

# Remove unused volumes
docker volume prune -f

# Full cleanup (aggressive)
docker system prune -af
```

### Step 2: Log cleanup
```bash
# Truncate large log files
truncate -s 0 /var/log/*.log

# Docker logs
truncate -s 0 $(docker inspect --format='{{.LogPath}}' gula-backend)
```

### Step 3: If still full
```bash
# Find largest directories
du -sh /var/lib/docker/* | sort -rh | head -5

# Move Docker data disk if needed
```

## Validation
- [ ] Disk usage below 80%
- [ ] All containers running
- [ ] Application accessible
- [ ] No data loss

## Full Reference
See `docs/runbooks/disk-full.md` for complete runbook.
