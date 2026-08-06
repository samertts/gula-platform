---
id: DEVOPS-000001
type: devops
title: "DevOps Knowledge Bridge"
version: "1.0"
created: "2026-08-04"
status: verified
confidence: 100%
tags: [devops, bridge, index]
---

# DevOps Knowledge — Bridge Reference

## CI/CD Workflows
| Workflow | Purpose |
|---|---|
| `ci.yml` | Main CI: ruff, tests, Docker build |
| `ai-governance.yml` | Brain freshness + validation |
| `constitution-compliance.yml` | Constitution compliance |
| `quality-gate.yml` | Quality gate checks |
| `deploy.yml` | Production deployment |
| `blue-green-deploy.yml` | Blue-green deployment |
| `canary-deploy.yml` | Canary deployment |
| `auto-rollback.yml` | Auto-rollback on failure |
| `nightly.yml` | Nightly build + tests |

## Docker
- Backend: `backend/Dockerfile` (Python 3.12, non-root)
- Frontend: `frontend-v3/Dockerfile` (Node 24, nginx)
- Volume mount required: `-v /path/to/shared:/app/shared:ro`
- Redis URL with password required

## Deployment
- `docs/DEPLOYMENT.md` — Deployment guide
- `docs/production/` — 10 production documents
- `docs/runbooks/` — 7 operational runbooks

## Infrastructure
- Docker containers (backend, frontend, PostgreSQL, Redis, MinIO)
- Nginx reverse proxy
- Let's Encrypt SSL
- WSL2 development environment

## Self-Healing
- `scripts/self_heal.py` — Automated recovery
- `scripts/auto_repair.py` — Auto-repair actions
- Circuit breaker pattern implemented

## Related
- `.ai/core/playbooks/` — Operational playbooks
- `.ai/core/runbooks/` — Step-by-step guides
