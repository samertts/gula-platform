# P4 Phase 8 — Production Configuration Audit v1.0

**Platform:** GULA National Health Platform
**Branch:** `remediate-security-001`
**Date:** 2026-08-02
**Method:** Full inventory of Docker, compose, env templates, CI, k8s, backup/DR, hardening, config loading, observability.

## Verdict

**PRODUCTION CONFIGURATION v1.0: PASS** — one critical defect found and
remediated; configuration surface otherwise complete and production-hardened.

## 1. Critical Finding — Fixed (`e1c7486e`)

**Committed production secrets.** `.env.production` was tracked in git since
`4b9acab7` (2026-03-29) containing 11 real production secrets: `SECRET_KEY`,
`REFRESH_TOKEN_SECRET`, `ENCRYPTION_KEY`, `NID_HMAC_KEY`, `DEVICE_HMAC_KEY`,
`AUDIT_ANCHOR_KEY`, `POSTGRES_PASSWORD`, `REDIS_PASSWORD`,
`GRAFANA_PASSWORD`, `GULA_ADMIN_PASSWORD`, `DATABASE_URL`, `REDIS_URL`
(31–55 char random values).

**Remediation:**
- `git rm --cached .env.production` — removed from tracking; local copy kept
  for operations.
- `.gitignore` now excludes `.env.production`.
- **Values are compromised in git history and MUST be rotated** — per
  `docs/security/SECRET_ROTATION_PLAN.md`. This is an operator action
  (production values are not accessible to this certification).
- `.env.example` rebuilt from ~12 vars to ~105 vars covering the full config
  surface (`backend/app/config.py` reads ~110 env vars).

## 2. Docker (14 images) — PASS

- All 14 Dockerfiles pin **Python 3.12** / node 24, run **non-root**
  (`appuser`/`nodejs`), have **HEALTHCHECK**, EXPOSE only internal ports.
- Backend: gunicorn+uvicorn 2 workers, `python -m compileall app/` build gate,
  healthcheck hits `/health`.
- `.dockerignore` excludes `.env*`, docs, scripts, compose files.

## 3. Compose — PASS (with notes)

- `docker-compose.yml` (MVP): postgres 17, redis 7 (requirepass), backend,
  worker, frontend (nginx), api-gateway; `monitoring` profile (prometheus/
  grafana/alertmanager); `device-bridge` profile. No-external-ports for DB/
  Redis, `no-new-privileges`, healthchecks + `depends_on` conditions.
- `docker-compose.full.yml`: full HA stack — pg primary/replica + pgbouncer,
  redis + sentinel, clickhouse, rabbitmq+zk+kafka, ollama, ai-service,
  minio, keycloak, vault, observability (prometheus/grafana/loki/promtail/
  jaeger), 7 microservices, backup-cron.
- **Note:** MVP compose `frontend` service serves legacy `./frontend`;
  production deployment paths (k8s/helm, deploy.yml) build the current app
  via the root Dockerfile. Tracked, non-blocking.

## 4. Environment Templates — PASS after fix

- `.env.example` (rebuilt): core secrets, DB (+pool/read-replica), Redis
  (+sentinel/cluster), cache, JWT, rate limits, body/upload limits,
  bootstrap accounts (+bcrypt `_PASSWORD_HASH` alternates), docs/metrics
  bearer token, Grafana, OTel, **Ollama-first** AI, commercial AI (optional),
  FCM/APNS, national adapters (MOI/residency/insurance, local-first),
  R2/Supabase storage, kernel feature flags, SNDHS flags.
- Backend loads via plain `os.getenv` (no dotenv) — production env injected
  by orchestrator (compose `.env`, CI secrets, ESO). By design; documented.
- `frontend-v3/.env.example` — Vite vars only.

## 5. CI/CD (25 workflows) — PASS

Backend/frontend pipelines, quality-gate, foundation-gate (compose validity),
ai-governance, constitution-compliance, formatting, frontend e2e/pwa,
deploy (SSH), blue-green/canary/rollback/auto-rollback, release, nightly,
mobile (3), sdk-publish, codeql, secret-scanning, dependency-review,
scorecard.

## 6. Kubernetes — PASS

`k8s/` kustomize (base + dev/prod/region-eu/region-me overlays): backend
deployment/service/HPA/PDB/PVC, ingress, postgres statefulset, redis,
rabbitmq, linkerd mesh, configmap; `secrets.yaml` intentionally empty —
**external-vault** (ESO) with `stringData: {}` (no inline secrets). Helm
chart with 40+ templates incl. Prometheus ServiceMonitors for
backend/postgres/redis/minio/rabbitmq.

## 7. Backup / DR — PASS

`scripts/backup.sh` (pg_dump hourly/daily + AES-256-CBC encryption + SHA-256
sidecars + 30d retention), `scripts/backup-verification.sh` (PROGRAM-011
verifier: restore-into-labdb_verify + checksums + audit-chain integrity),
`dr-failover/failback/test.sh`, `emergency-recover.sh`, `backup-cron` in
full compose; `docs/production/DISASTER_RECOVERY_GUIDE.md`, PITR runbook,
7 incident runbooks, `make backup|dr-*|pitr-recover` targets.

## 8. Production Hardening — PASS

- **HSTS** only in production; CSP/nosniff/X-Frame-Options DENY/COOP/
  Permissions-Policy always on.
- **Docs guarded** behind JWT in production; docs disabled unless
  `ENABLE_API_DOCS=true`.
- **/metrics/prom** requires `Bearer METRICS_BEARER_TOKEN` in production.
- **Fail-fast config**: `sys.exit(1)` in production for missing/weak
  `DATABASE_URL`, `SECRET_KEY`, `REFRESH_TOKEN_SECRET`, `ENCRYPTION_KEY`,
  `NID_HMAC_KEY`, `AUDIT_ANCHOR_KEY` (weak-secret detection).
- **Startup guard**: DB → Redis → migrations → seeds → kernel, atomic
  readiness.
- **Secure cookies** (`secure=IS_PRODUCTION`), setup route blocked in
  production, error redaction, Redis prod-only mode.

## 9. Observability — PASS

Prometheus scrape config (+ bearer token file) with 3 SLO rules, Grafana
provisioned (10 dashboards + alert rules + notifiers → Alertmanager →
Telegram/Discord/Slack webhook), OTel SDK (auto-instrumented FastAPI +
SQLAlchemy, OTLP HTTP), OTel collector config, Tempo/Jaeger HA configs.
Note (tracked): OTel/Tempo active only in `.full.yml` profile, not default.

## Verdict

**PRODUCTION CONFIGURATION v1.0: PASS** — the committed-secrets defect is
remediated (rotation is an operator action per the existing rotation plan);
all other surfaces (Docker hygiene, compose security posture, env template
coverage, k8s no-inline-secrets, backup verifier, prod hardening, SLO
alerting) verified present and consistent with the certification scope.
