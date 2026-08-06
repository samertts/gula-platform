---
id: PLAYBOOK-000002
type: playbook
title: "Fix Docker Build Failure"
version: "1.0"
created: "2026-08-04"
status: verified
confidence: 90%
tags: [docker, build, container, devops]
related_skills: [SKILL-000002]
related_runbooks: []
estimated_duration: "15 minutes"
---

# PLAYBOOK-000002: Fix Docker Build Failure

## Objective
Diagnose and fix Docker build failures for the GULA Platform containers.

## Prerequisites
- [ ] Docker daemon running (`docker info`)
- [ ] Access to repository source code
- [ ] Network connectivity for base image pulls

## Scope
- **In scope:** Dockerfile errors, build context issues, dependency failures
- **Out of scope:** Docker daemon installation, WSL2 Docker Desktop setup

## Risk Assessment
| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Breaking existing image | Low | High | Tag backups before rebuild |
| Network timeout pulling base | Medium | Low | Retry, use mirror |
| Disk space exhaustion | Low | Medium | Prune before build |

## Procedure

### Phase 1: Diagnose (3 min)
1. Check Docker daemon:
   ```bash
   docker info
   ```
2. Check available disk space:
   ```bash
   df -h /var/lib/docker
   ```
3. Try verbose build:
   ```bash
   docker build --progress=plain -t gula-backend ./backend 2>&1 | tail -50
   ```

### Phase 2: Common Fixes (10 min)

**Fix 1: Missing volume mount**
```bash
# Backend requires shared/ mount
docker run -v $(pwd)/shared:/app/shared:ro ...
```

**Fix 2: Redis URL required**
```bash
docker run -e REDIS_URL="redis://:password@redis:6379/0" ...
```

**Fix 3: Base image pull failure**
```bash
docker pull python:3.12-slim  # Test base image
```

**Fix 4: pip/uv install failure**
```bash
# Check requirements.txt exists
ls backend/requirements.txt
# Check network
curl -s https://pypi.org/simple/ | head -5
```

**Fix 5: Shared module not found**
```bash
# Ensure shared/ is in build context or mounted
ls shared/
```

### Phase 3: Rebuild (2 min)
```bash
docker build --no-cache -t gula-backend ./backend
```

## Verification
```bash
docker run --rm gula-backend python --version  # Should show 3.12
docker run --rm gula-backend python -c "import app; print('OK')"
```

## Rollback
```bash
docker tag gula-backend:latest gula-backend:backup-$(date +%Y%m%d)
```

## Related Skills
- SKILL-000002: WSL2 Docker Compose Resolution

## Changelog
| Version | Date | Author | Change |
|---|---|---|---|
| 1.0 | 2026-08-04 | GAIOS | Initial creation |
