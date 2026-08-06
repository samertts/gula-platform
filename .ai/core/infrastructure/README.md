---
id: INFRA-000001
type: infrastructure
title: "Infrastructure Knowledge Bridge"
version: "1.0"
created: "2026-08-04"
status: verified
confidence: 75%
tags: [infrastructure, deployment, docker, bridge]
---

# Infrastructure Knowledge — Bridge Reference

## Deployment Stack
- Docker containers (backend, frontend, PostgreSQL, Redis, MinIO)
- Nginx reverse proxy
- Let's Encrypt SSL certificates
- WSL2 development environment

## Container Architecture
```
nginx:443 → backend:5000 (FastAPI)
         → frontend:80 (static)
backend:5000 → PostgreSQL:5432
             → Redis:6379
             → MinIO:9000
             → Ollama:11434 (local AI)
```

## Required Environment Variables
- `DATABASE_URL` — PostgreSQL connection string
- `REDIS_URL` — Redis connection (with password)
- `MINIO_ENDPOINT` — MinIO endpoint
- `OLLAMA_BASE_URL` — Ollama API endpoint
- `SECRET_KEY` — Application secret
- `ENCRYPTION_KEY` — Fernet encryption key

## Volume Mounts
- `shared/` — Read-only shared modules (`-v $(pwd)/shared:/app/shared:ro`)

## Health Checks
- Backend: `GET /health`
- Database: `SELECT 1`
- Redis: `PING`
- Ollama: `GET /api/tags`

## Related
- `.ai/core/devops/README.md` — DevOps procedures
- `ARCHITECTURE.md` — Deployment topology
- `docs/DEPLOYMENT.md` — Full deployment guide
