# PROGRAM-DEPLOYMENT-001: Deployment Audit Report

**Date:** 2026-08-04
**Status:** Phase 3 Complete
**Readiness on re-audit:** ~82/100 (all 10 critical issues fixed; Phase 2 smoke test PASSED; Phase 3 frontend verified + offline-first restored)

---

## Overall Deployment Readiness: 30/100

---

## Top 10 Critical Issues

| # | Severity | Issue | Impact | Status |
|---|---|---|---|---|
| 1 | BLOCKER | Backend port mismatch: Dockerfile binds 10000, compose expects 8000 | Health checks fail, API gateway 502 | ✅ FIXED — backend/Dockerfile + docker/Dockerfile now bind/EXPOSE 8000 |
| 2 | BLOCKER | No CI build-and-push for backend Docker image | GHCR deployments fail | ✅ FIXED — added `.github/workflows/build-images.yml` (GHCR push, sha+latest tags) |
| 3 | BLOCKER | deploy.yml rollback doesn't change image tag | Cannot actually roll back | ✅ FIXED — rollback restores previous GULA_IMAGE_TAG, pulls, re-verifies health |
| 4 | HIGH | frontend serves legacy dir, not frontend-v3 React build | Outdated UI | ✅ FIXED — compose mounts `./frontend-v3/dist` |
| 5 | HIGH | docker/Dockerfile orphaned | Dead code | ✅ FIXED — rewired docker/docker-compose.yml to backend context; fixed Node/Python mismatch |
| 6 | HIGH | Keycloak start-dev + Vault dev mode in full compose | Insecure | ✅ FIXED — Keycloak `start` prod mode; Vault persistent `server` mode w/ file storage |
| 7 | MEDIUM | No container log rotation | Disk exhaustion | ✅ FIXED — json-file 50m×5 on postgres, redis, backend, frontend, gateway |
| 8 | MEDIUM | backups/ dir missing, no automated backups | Zero backup coverage | ✅ FIXED — `backups/` created; script configurable/local-first; `gula-backup` cron service added |
| 9 | MEDIUM | deploy.yml hardcodes REPO_DIR | Non-portable | ✅ FIXED — configurable via `vars.REPO_DIR` |
| 10 | MEDIUM | Docs reference non-existent files | Drift | ✅ FIXED — 6 runbook links corrected; 0 broken refs |

---

## Phase 2 Smoke Test Results (2026-08-04)

End-to-end container verification with PostgreSQL 16 + Redis (real services, not mocks):

| Check | Result |
|---|---|
| `backend/Dockerfile` image build | ✅ PASS |
| gunicorn binds `0.0.0.0:8000` | ✅ PASS |
| `/health` | ✅ `{"status":"ok","system_ready":true,"database":"ok"}` |
| `/health/ready` | ✅ `status: ok` |
| `/health/live` | ✅ `status: alive` |
| `/docs` | ✅ HTTP 200 |
| `/openapi.json` | ✅ HTTP 200 (~13s spec generation) |
| Startup guard | ✅ `[STARTUP GUARD] === System READY (15775ms) — accepting traffic ===` |

**Additional blocker found & fixed during smoke test:** migration
`20260804_0001_communication_experience.py` used invalid `op.Column`/`op.String`/`op.false()`
(Alembic has no such ops — should be `sa.*`). Would have failed `alembic upgrade head`
in production. Fixed to `sa.Column`/`sa.String`/`sa.false()` + `import sqlalchemy as sa`.
Migrations now apply cleanly to head `20260804_0001`.

## Phase 3 Frontend Verification (2026-08-04)

| Check | Result |
|---|---|
| `frontend-v3` build (`npm run build`) | ✅ PASS (2.9s, tsc 0 errors) |
| `tsc --noEmit` | ✅ PASS (0 errors) |
| ESLint | ✅ PASS (0 warnings) |
| Vitest | ✅ 122/122 tests pass |
| `dist/sw.js` present | ✅ PASS (was missing — offline-first gap) |
| `manifest.webmanifest` + `offline.html` in dist | ✅ PASS |

**Offline-first restored:** `vite-plugin-pwa` generates the manifest/offline.html but its
workbox SW generation does not fire under Vite 8 (Rolldown) — no `sw.js` was emitted and no
registration injected. Replaced with a self-contained `public/sw.js` (app-shell precache,
network-first for API/navigations, cache-first for assets, offline.html fallback) registered
manually in `main.tsx`; plugin set to `injectRegister: false`.

**Frontend nginx config aligned to frontend-v3:** `manifest.webmanifest` (was `manifest.json`),
added `offline.html` and PWA-icon caching rules, removed legacy `/login.html` and `/r/` pages.

**Gateway routing verified:** api-gateway `/api/*`, `/api/v1/*`, `/auth/*`, `/health/*` → `gula-backend:8000`
(matches fixed Dockerfile bind). Security headers (CSP, X-Frame-Options, HSTS 1y, Referrer-Policy,
Permissions-Policy, COOP/COEP) confirmed present.

---

## Area Readiness

| Area | Score | Key Finding |
|---|---|---|
| Docker Compose | 25/100 | Correct architecture, port mismatch |
| Dockerfiles | 75/100 | Clean multi-stage, 1 orphaned |
| Nginx | 80/100 | Production two-layer, missing ssl.conf |
| SSL/DNS | 70/100 | Cloudflare edge + certbot scripts |
| Environment/Secrets | 65/100 | Well-documented, placeholder tokens |
| Database | 70/100 | Tuned PostgreSQL, HA available |
| CI/CD | 20/100 | No image build, broken rollback |
| K8s | 40/100 | Base manifests exist, strategies incomplete |
| Monitoring | 70/100 | Prometheus/Grafana/Alertmanager |
| Backups | 10/100 | Scripts exist but not automated |
| Documentation | 55/100 | Comprehensive but references missing files |
| Security | 60/100 | Non-root, UFW, weak HAProxy defaults |

---

**Proceeding to Phase 3 — frontend readiness (nginx config, SPA fallback) and Phase 4 services.**
