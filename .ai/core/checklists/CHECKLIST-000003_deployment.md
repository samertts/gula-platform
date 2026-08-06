---
id: CHECKLIST-000003
type: checklist
title: "Deployment Checklist"
version: "1.0"
created: "2026-08-04"
status: verified
confidence: 95%
tags: [deployment, checklist, production, release]
---

# Deployment Checklist

Run before every production deployment.

## Pre-Deployment
- [ ] All tests pass locally
- [ ] CI/CD pipeline green
- [ ] Code reviewed and approved
- [ ] Database migration tested
- [ ] Rollback plan documented
- [ ] Stakeholders notified

## Backend
- [ ] `ruff check .` — 0 violations
- [ ] `pytest tests/` — all pass
- [ ] `docker build` — succeeds
- [ ] No new environment variables without docs
- [ ] Database migration is backward compatible
- [ ] Shared modules mounted correctly

## Frontend
- [ ] `npx tsc --noEmit` — 0 errors
- [ ] `npx eslint src/` — 0 errors
- [ ] `npx vitest run` — all pass
- [ ] `npx vite build` — succeeds
- [ ] No new API calls without error handling

## Infrastructure
- [ ] Docker images built and tagged
- [ ] Environment variables configured
- [ ] SSL certificates valid
- [ ] DNS records correct
- [ ] Monitoring alerts configured
- [ ] Backup completed

## Security
- [ ] No secrets in code
- [ ] CORS configured correctly
- [ ] Rate limiting enabled
- [ ] Input validation present
- [ ] Authentication/authorization tested

## Post-Deployment
- [ ] Health endpoint returns 200
- [ ] Smoke tests pass
- [ ] Error rates within normal range
- [ ] Response times within SLA
- [ ] Logs clean (no errors)
- [ ] Monitoring confirms stability

## Rollback Procedure
```bash
# If issues detected within 30 minutes:
docker compose down
git checkout HEAD~1
docker compose up -d
# Verify health
curl -sf http://localhost:8000/health
```
