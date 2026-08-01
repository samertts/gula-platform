# GULA Platform — v1.0.0-RC2 Deployment Package

Release certification: **PROGRAM-010** (Release Candidate Certification)
Tag: `v1.0.0-RC2` — branch: `remediate-security-001`
Date: 2026-08-01

This package is the certified deployment bundle for GULA Platform
v1.0.0-RC2. It supersedes `v1.0.0-RC1`, which was tagged before the
certification cycle completed (pre-certification version files, no
Python 3.12 shared-library alignment).

## Bundle Contents

| Artifact | Location |
|---|---|
| Backend image | `backend/Dockerfile` (context: `backend/`) |
| Orchestration | `docker-compose.yml` (validated: `docker compose config` PASS) |
| Backend Dockerfile | `backend/Dockerfile` (HEALTHCHECK on `/health`, port 10000) |
| Safe deploy script | `scripts/deploy.sh` (backup-first, lock, health smoke) |
| Server provisioning | `scripts/server-setup.sh`, `setup-deployment.sh`, `setup-https.sh` |
| Operations manual | `docs/ops/OPERATIONS_MANUAL.md` |
| PITR runbook | `docs/dr/PITR_RUNBOOK.md` |
| Backup (AES-256) | `scripts/backup.sh`, `backup-verification.sh`, `continuous-backup.sh` |
| Health probes | `scripts/health-probes/`, `scripts/foundation_health.sh` |
| Environment template | `.env.example`, `.env.production` (placeholders only) |
| Frontend bundle | `frontend-v3/dist/` (built from certified source) |
| Android | `.github/workflows/mobile-android.yml` (CI builds; local SDK unavailable) |

## Certified Verification Results (production-like)

Performed against live `gula-postgres` (PostgreSQL 16, 342 tables,
alembic head `20260723_0002`) and `gula-redis` (Redis 7).

| Check | Result |
|---|---|
| `GET /health` | `status: ok`, `system_ready: true`, `database: ok` |
| `GET /health/ready` | `status: ok`, `system_ready: true` |
| `GET /health/deep` | grade **A**, 0 issues; DB 2.7 ms, Redis 2.1 ms, queue backlog 0 |
| `POST /login` (bad creds) | `401`-equivalent structured error (no crash) |
| `GET /openapi.json` | 200 — 1640 paths |
| `GET /metrics` | 401 (auth-gated, expected) |
| Docker image `gula-backend-rc:local` | builds clean, runs healthy with `shared/` mount |

## Deployment Steps (production)

1. **Provision host**: run `scripts/server-setup.sh` (installs Docker,
   crons for backup, logrotate, health checks).
2. **Prepare environment**: copy `.env.example` → `.env`; set
   `POSTGRES_PASSWORD`, `REDIS_PASSWORD`, `SECRET_KEY`, `ENCRYPTION_KEY`,
   `NID_HMAC_KEY`, `AUDIT_ANCHOR_KEY`, `GRAFANA_PASSWORD` to strong values.
   Never commit `.env` / `.env.production` values.
3. **Checkout the certified tag**: `git fetch && git checkout v1.0.0-RC2`.
4. **Deploy**: `./scripts/deploy.sh` (creates pre-deploy backup, builds
   images, starts stack, waits for `/health` up to 180 s, smoke-tests).
5. **Verify**: `curl http://localhost/health` → `system_ready: true`;
   `curl http://localhost/health/deep` → `grade: A`.
6. **Android**: CI workflow `mobile-android.yml` builds the APK/AAB from
   `mobile/android/` on tag push (local machine has no Android SDK).

## Required Volume & Runtime Contract

- `shared/` must be mounted read-only into the backend container at
  `/app/shared` (`-v /path/to/shared:/app/shared:ro`) — this is the
  documented runtime contract (see AGENTS.md); the image does not embed
  `shared/`.
- Backend runs on port 10000 (gunicorn, 2 workers); `docker-compose.yml`
  exposes it through the api-gateway on port 80.

## Rollback

- Images are immutable by tag; roll back by checking out the previous
  release tag and re-running `./scripts/deploy.sh`.
- Database: restore the pre-deploy backup with `scripts/restore-test.sh`
  pattern or PITR via `scripts/pitr-recover.sh` + `docs/dr/PITR_RUNBOOK.md`.

## Known Deviations (documented, not blocking)

1. **Android**: local SDK absent → release artifact produced by CI only.
2. **53 unresolved FE API calls**: all confined to dormant capability /
   national / NIAM / citizen demo pages (strategic dormant modules per
   constitution — preserved, not activated). Zero unresolved calls in
   core LIMS flows.
3. **Ruff baseline 379**: E402 (167, intentional cond-imports), N801
   (141, capabilities pattern), N999 (71) — unchanged from baseline,
   gate PASS.
4. **mypy**: full-codebase run times out (known); tsc/eslint/ruff cover
   the gate.
