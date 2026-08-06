---
id: SKILL-000002
type: skill
title: "WSL2 Docker Compose Resolution"
version: "1.0"
created: "2026-08-04"
status: verified
confidence: 100%
tags: [docker, docker-compose, wsl, linux]
related_skills: [SKILL-000001]
related_playbooks: [PLAYBOOK-000001]
---

# SKILL-000002: WSL2 Docker Compose Resolution

## Problem
In WSL2, `docker-compose` resolves to the Windows Docker Desktop binary
via PATH interop, which fails with "command not found" in the Linux distro.

## Symptoms
```
$ docker-compose --version
The command 'docker-compose' could not be found in this WSL 2 distro.
```

## Environment
- OS: Ubuntu 22.04.5 LTS (WSL2)
- Docker: 29.1.3

## Root Cause
WSL2 interop adds Windows PATH entries. `docker-compose.exe` exists in
Windows Docker Desktop resources but is not executable from WSL2 Linux.

## Solution
Use Docker Compose v2 plugin instead of standalone `docker-compose`:
```bash
docker compose version   # v2 plugin, works natively
```

If standalone is needed:
```bash
# Install via pip (Python)
pip install docker-compose

# Or download Linux binary
curl -SL https://github.com/docker/compose/releases/latest/download/docker-compose-linux-x86_64 -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
```

## Verification
```bash
docker compose version   # Should show v2.x.x
```

## Rollback
No rollback needed — no changes made.

## Lessons Learned
- WSL2 interop PATH entries cause tool resolution conflicts
- Prefer `docker compose` (v2 plugin) over `docker-compose` (standalone)
- Docker CLI v23+ includes compose as a plugin

## Changelog
| Version | Date | Author | Change |
|---|---|---|---|
| 1.0 | 2026-08-04 | GAIOS | Initial creation |
