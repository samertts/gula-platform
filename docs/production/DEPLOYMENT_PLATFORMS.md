# GULA Platform — Deployment on Render, Supabase, and DigitalOcean

> منصة غولا الصحية — جاهزة للعمل على ثلاث منصات سحابية: Render و Supabase و DigitalOcean.

This document is the single, authoritative deployment guide. All three
platforms are designed to **inter-operate**:

```
                        ┌──────────────────────────┐
                        │   Browser  /  Mobile     │
                        └────────────┬─────────────┘
                                     │ HTTPS
              ┌──────────────────────┴───────────────────────┐
              │                                              │
   ┌──────────▼──────────┐                       ┌───────────▼──────────┐
   │   Render (web)      │                       │  DigitalOcean        │
   │  • static frontend  │                       │  • App Platform OR   │
   │  • FastAPI backend  │                       │    Droplet           │
   │  • managed Redis    │                       │  • managed Redis     │
   └──────────┬──────────┘                       └───────────┬──────────┘
              │                                              │
              └──────────────────┬───────────────────────────┘
                                 │ DATABASE_URL
                                 ▼
                       ┌──────────────────────┐
                       │   Supabase Postgres  │
                       │   • daily backups    │
                       │   • PITR (Pro plan)  │
                       └──────────────────────┘
```

You can run **just one** target (e.g. Render + Supabase) or use **DigitalOcean
as a hot-standby** by pointing both apps at the same Supabase project.

---

## 0. One-shot bootstrapper

```bash
# Generate / preserve secrets, write .env.deploy, print platform-specific steps
./scripts/setup-deployment.sh --platform all

# After Supabase project is created and DATABASE_URL is in .env.deploy:
./scripts/setup-deployment.sh --platform supabase --supabase-bootstrap
```

What it produces:

| File                    | Use                                                 |
| ----------------------- | --------------------------------------------------- |
| `.env.deploy`           | Local docker-compose, droplet `.env`, scripts.      |
| `.deploy/secrets.txt`   | Copy/paste blob for Render & DO dashboards.         |

Both files are gitignored. Treat them like a password vault.

> The script reuses existing `ENCRYPTION_KEY` and `NID_HMAC_KEY` if they
> already exist in `.env.deploy` — these must **never** change once patient
> data has been written. Add `--rotate` to force-rotate JWT/HMAC keys
> (operators get logged out; data stays safe).

---

## 1. Render (managed PaaS) — recommended primary

Files in repo:

| File                                  | Purpose                                       |
| ------------------------------------- | --------------------------------------------- |
| `render.yaml`                         | Blueprint for backend + frontend + Key Value. |
| `backend/Dockerfile`                  | Multi-stage Docker build.                     |

Steps:

```bash
git push origin claude/setup-deployment-platforms-jQYUw
# Render dashboard → New → Blueprint → pick this repo → render.yaml
# When prompted for `sync: false` secrets, paste from .deploy/secrets.txt:
#   DATABASE_URL, ENCRYPTION_KEY, NID_HMAC_KEY, GULA_ADMIN_PASSWORD,
#   (optional) GEMINI_API_KEY, GROQ_API_KEY, SENTRY_DSN, ALERT_WEBHOOK_URL
```

What you get out of the box:

- `gula-backend` web service on port 10000, autoscaling-ready
- `gula-frontend` static site with SPA routing + security headers
- `gula-redis` Key Value (Redis-compatible) attached automatically
- `preDeployCommand: alembic upgrade head` runs before traffic switches
- Health check on `/health` (Render kills + restarts on failure)

Verify:

```bash
curl https://gula-backend.onrender.com/health         # → {"status":"ok"}
curl https://gula-backend.onrender.com/health/ready   # → 200
curl https://gula-backend.onrender.com/health/deep    # → grade GREEN/AMBER
```

---

## 2. Supabase (managed Postgres) — required for cloud deploys

Files in repo:

| File                                  | Purpose                                          |
| ------------------------------------- | ------------------------------------------------ |
| `supabase/setup.sql`                  | Idempotent extensions + privileges + defaults.   |
| `supabase/README.md`                  | Step-by-step project creation + restore drill.   |
| `scripts/supabase_bootstrap.sh`       | One-shot apply of setup.sql + alembic upgrade.   |

Steps:

1. Create the project at <https://supabase.com> (Frankfurt for GCC users).
2. Project Settings → Database → **Connection pooler** → URI (port 6543).
3. Paste into `.env.deploy` as `DATABASE_URL`.
4. Run:

```bash
./scripts/setup-deployment.sh --platform supabase --supabase-bootstrap
```

The bootstrap will:
- enable `pgcrypto`, `pg_trgm`, `pg_stat_statements`, `btree_gin`
- revoke default privileges from `anon` / `authenticated`
- apply runtime `statement_timeout`, `idle_in_transaction_session_timeout`
- run all Alembic migrations on the empty DB
- assert that the 8 critical tables (`labs`, `lab_users`, `patients`,
  `lab_orders`, `lab_results`, `outbox_events`, `audit_logs`,
  `alembic_version`) exist after migration

After that the same `DATABASE_URL` is reusable on Render, DO App Platform,
or any droplet — Supabase is the single source of truth.

---

## 3. DigitalOcean — App Platform OR Droplet

### 3a. App Platform (managed)

Files in repo:

| File                                  | Purpose                                      |
| ------------------------------------- | -------------------------------------------- |
| `digitalocean/app.yaml`               | App Platform spec (backend + frontend).      |
| `digitalocean/README.md`              | doctl + dashboard walkthrough.               |

Steps:

```bash
brew install doctl        # or: snap install doctl
doctl auth init
doctl apps create --spec digitalocean/app.yaml
APP_ID=$(doctl apps list --format ID,Spec.Name --no-header | awk '/gula-platform/ {print $1}')

# Replace REPLACE_VIA_DASHBOARD secrets (from .deploy/secrets.txt)
# either via the dashboard or by editing app.yaml + doctl apps update.
doctl apps create-deployment "$APP_ID" --force-rebuild
doctl apps logs "$APP_ID" --type build --follow
```

Health check, autoscaling (1–3 instances), pre_deploy migrations, and
managed Redis (Valkey) all wired in.

### 3b. Droplet (Docker-Compose, full stack)

Files in repo:

| File                                  | Purpose                                       |
| ------------------------------------- | --------------------------------------------- |
| `scripts/server-setup.sh`             | One-shot droplet bootstrap (Docker, nginx).   |
| `scripts/digitalocean-manage.sh`      | Day-2 ops console (status/logs/scale/...).    |
| `docker-compose.yml`                  | Full stack — backend, postgres, redis, nginx. |
| `docker-compose.scale.yml`            | HAProxy multi-instance overlay.               |

Steps:

```bash
doctl compute droplet create gula-prod \
  --image ubuntu-22-04-x64 --size s-2vcpu-4gb \
  --region fra1 --enable-backups --enable-monitoring
DROPLET_IP=$(doctl compute droplet list --format Name,PublicIPv4 --no-header \
  | awk '/gula-prod/ {print $2}')
ssh root@$DROPLET_IP \
  'curl -fsSL https://raw.githubusercontent.com/samertts/gula-platform/main/scripts/server-setup.sh | sudo bash'
scp .env.deploy samertts@$DROPLET_IP:~/gula-platform/.env
ssh samertts@$DROPLET_IP 'cd ~/gula-platform && docker compose up -d'
```

Day-2 commands (run on the droplet):

```bash
./scripts/digitalocean-manage.sh status
./scripts/digitalocean-manage.sh logs gula-backend
./scripts/digitalocean-manage.sh scale 3
./scripts/digitalocean-manage.sh backup
./scripts/digitalocean-manage.sh kill-switch on   # halt all autonomous AI/repair
```

---

## 4. Verification matrix (run after every deploy)

```bash
BASE=https://YOUR_DEPLOYED_URL

# 1. Liveness — should be instant
curl -fsS $BASE/health | jq

# 2. Readiness — DB reachable, migrations applied, system_ready=true
curl -fsS $BASE/health/ready | jq

# 3. Deep — all subsystems graded GREEN/AMBER (RED = block traffic)
curl -fsS $BASE/health/deep | jq '.grade,.checks'

# 4. Public seed data — proves DB is wired correctly
curl -fsS $BASE/test-types | jq 'length'

# 5. Auth round-trip
curl -fsS -X POST "$BASE/auth/login" \
  -H 'content-type: application/json' \
  -d '{"email":"admin@gula-platform.org","password":"YOUR_BOOTSTRAP_PASSWORD"}'
```

A deployment is "green" when **all 5** succeed and `/health/deep.grade ≠ RED`.

---

## 5. Failure-mode quick reference

| Symptom                                            | Fix                                                            |
| -------------------------------------------------- | -------------------------------------------------------------- |
| `[GULA FATAL] DATABASE_URL must be set`            | Secret missing in dashboard. Paste from `.deploy/secrets.txt`. |
| `[GULA FATAL] SECRET_KEY contains a weak pattern`  | Re-run `setup-deployment.sh --rotate`.                          |
| `Migration 20250322_0000 already exists`           | DB partially bootstrapped. Run `alembic stamp head`.            |
| Render build OK, `/health` returns 502             | Check Render logs — usually `ENCRYPTION_KEY` missing.           |
| `/health/deep` grade = RED                          | Inspect `.checks.<subsystem>.detail` and `docker logs ...`.     |
| Supabase "too many connections"                     | Switch URL to pooled (port 6543) — see `supabase/README.md`.    |
| DO App Platform stuck on pre_deploy                 | View build logs; usually a migration is non-idempotent.        |
| Backend can't reach Redis                           | Leave `REDIS_URL` blank — backend falls back to in-memory.      |

---

## 6. Cost snapshot (April 2026 prices)

| Topology                                                | Approx /month |
| ------------------------------------------------------- | ------------- |
| Render Starter + Supabase Free                          | $7            |
| Render Starter + Supabase Pro + Sentry Team             | $58           |
| DO App basic-xs + DO Redis dev + Supabase Free          | $19           |
| DO App basic-s + DO Redis primary + Supabase Pro        | $57           |
| DO Droplet 4 GB + Supabase Free + Backups               | $26           |
| DO Droplet 4 GB + Supabase Pro + Backups + Spaces       | $54           |

> Budget tip: start on **Render Starter + Supabase Free** ($7/mo). Switch to
> **DigitalOcean Droplet** once you cross 50 active labs — break-even is
> roughly 5,000 daily requests.

---

## 7. Where things live

| Concern                | File / dir                                                 |
| ---------------------- | ---------------------------------------------------------- |
| Runtime config schema  | `backend/app/config.py` + `.env.example`                    |
| Render manifest        | `render.yaml`                                              |
| Supabase bootstrap     | `supabase/setup.sql`, `scripts/supabase_bootstrap.sh`       |
| DO App Platform spec   | `digitalocean/app.yaml`                                    |
| DO Droplet bootstrap   | `scripts/server-setup.sh`                                  |
| Day-2 ops              | `scripts/digitalocean-manage.sh`                           |
| Unified setup          | `scripts/setup-deployment.sh`                              |
| CI gates               | `.github/workflows/ci.yml`                                 |
| Migration policy       | `CLAUDE.md` → "Migration Policy"                           |

---

Made for the GULA team. Questions? Open an issue with the `deployment` label.
