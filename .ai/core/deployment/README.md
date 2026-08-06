---
id: DEPLOY-000001
type: deployment
title: "Deployment Knowledge Bridge"
version: "1.0"
created: "2026-08-04"
status: verified
confidence: 85%
tags: [deployment, ci-cd, docker, production, bridge]
---

# Deployment Knowledge — Bridge Reference

## CI/CD Workflows
| Workflow | File | Purpose |
|---|---|---|
| Main CI | `.github/workflows/ci.yml` | Ruff, tests, Docker build |
| Deploy | `.github/workflows/deploy.yml` | Production deployment |
| Blue-Green | `.github/workflows/blue-green-deploy.yml` | Zero-downtime deploy |
| Canary | `.github/workflows/canary-deploy.yml` | Gradual rollout |
| Rollback | `.github/workflows/rollback.yml` | Manual rollback |
| Auto-Rollback | `.github/workflows/auto-rollback.yml` | Auto-revert on failure |
| Release | `.github/workflows/release.yml` | Version release |
| Nightly | `.github/workflows/nightly.yml` | Nightly build + tests |

## Deployment Architecture
- Backend: Docker container (Python 3.12, non-root)
- Frontend: Docker container (Node 24, nginx)
- Reverse Proxy: Nginx with Let's Encrypt SSL
- Database: PostgreSQL 16 (Docker)
- Cache: Redis 7.x (Docker)
- Object Storage: MinIO (Docker)
- AI: Ollama (host system)

## Environment Variables
| Variable | Purpose | Required |
|---|---|---|
| `DATABASE_URL` | PostgreSQL connection | Yes |
| `REDIS_URL` | Redis connection (with password) | Yes |
| `SECRET_KEY` | Application secret | Yes |
| `ENCRYPTION_KEY` | Fernet encryption key | Yes |
| `MINIO_ENDPOINT` | MinIO storage endpoint | Yes |
| `OLLAMA_BASE_URL` | Ollama AI endpoint | Yes |

## Docker Commands
```bash
# Build
docker build -t gula-backend ./backend
docker build -t gula-frontend ./frontend-v3

# Run
docker run -d \
  -v $(pwd)/shared:/app/shared:ro \
  -e REDIS_URL="redis://:password@redis:6379/0" \
  -e DATABASE_URL="postgresql://..." \
  -p 5000:5000 \
  gula-backend

# Compose
docker compose up -d
docker compose ps
docker compose logs -f gula-backend
```

## Deployment Scripts
- `.github/scripts/auto-rollback.sh` — Auto-rollback
- `.github/scripts/blue-green-deploy.sh` — Blue-green deploy
- `.github/scripts/canary-deploy.sh` — Canary deploy

## Related
- `.ai/core/devops/README.md` — DevOps procedures
- `.ai/core/infrastructure/README.md` — Infrastructure
- `.ai/core/checklists/CHECKLIST-000003_deployment.md` — Deploy checklist
- `docs/DEPLOYMENT.md` — Full deployment guide
- `docs/production/` — 10 production documents
