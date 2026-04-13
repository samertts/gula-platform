# GULA Platform — Supabase Setup

Supabase is the **managed PostgreSQL** layer for production GULA deployments.
The application connects to it via SQLAlchemy + Alembic exactly the same way
it connects to a self-hosted Postgres — only the URL changes.

## 1. Create the project

1. Go to <https://supabase.com> → **New project**
2. Recommended settings:
   | Setting       | Value                                      |
   | ------------- | ------------------------------------------ |
   | Region        | Closest to your users (Frankfurt for GCC)  |
   | Postgres      | 16 (default)                               |
   | Plan          | Free for staging, Pro ($25/mo) for prod    |
3. Wait ~2 min for provisioning, then open the project.

## 2. Grab the connection string (use **pooled** mode)

Open **Project Settings → Database → Connection string** and pick the
**Transaction pooler** tab (port `6543`). The URI looks like:

```
postgresql://postgres.<project-ref>:<pwd>@aws-0-<region>.pooler.supabase.com:6543/postgres?sslmode=require
```

> **Why pooled?** GULA runs 2 gunicorn workers × 15 connections = 30 sockets.
> Direct connections (port 5432) are capped at 60 on the free tier; pgBouncer
> on 6543 lifts that to 200 and survives serverless cold starts.

Copy the URI — it becomes `DATABASE_URL` on Render / DigitalOcean App Platform.

## 3. Apply the bootstrap SQL (one-time)

Two equivalent paths:

### Option A — Alembic (preferred)
The backend ships every schema change as a migration. Once `DATABASE_URL`
is configured, Render/DO run `alembic upgrade head` automatically before each
deploy. Locally you can prime a fresh project with:

```bash
cd backend
DATABASE_URL='postgresql://postgres.xxx:pwd@aws-0-eu-central-1.pooler.supabase.com:6543/postgres?sslmode=require' \
  alembic upgrade head
```

### Option B — `supabase/setup.sql`
Run once in the Supabase SQL editor before the first deploy. It:
- enables required extensions (`pgcrypto`, `pg_trgm`, `pg_stat_statements`)
- tightens default privileges so anon/authenticated roles cannot reach
  the application schema (we do not use Supabase Auth — RLS bypasses
  via FastAPI service role)
- creates a dedicated `gula_app` role with rotated password
- sets sane runtime defaults (`statement_timeout`, `idle_in_transaction`)

```sql
-- In the Supabase SQL editor:
\i supabase/setup.sql
```

## 4. Set storage limits & alerts

Project Settings → Usage:

- Database size warning at **80 %**
- Egress warning at **80 %**
- Pause at **100 %** (free tier only — disable for Pro)

## 5. Daily backups

- Free tier: enable **daily logical backups** (download the .sql.gz nightly).
- Pro tier: **PITR** is on by default (7 days). Turn on **daily snapshots**
  for an extra layer.

## 6. Restore drill (do this at least once)

```bash
# Pull backup
supabase db dump --file backup.sql

# Restore into a scratch project to verify
psql 'postgresql://postgres.scratch:pwd@.../postgres?sslmode=require' < backup.sql
```

## 7. Connection-string env vars summary

| Platform           | Variable                  | Source                                                   |
| ------------------ | ------------------------- | -------------------------------------------------------- |
| Render             | `DATABASE_URL` (secret)   | Supabase pooled URI (port 6543, sslmode=require)         |
| DO App Platform    | `DATABASE_URL` (secret)   | Same                                                     |
| DO Droplet (.env)  | `DATABASE_URL`            | Same                                                     |
| Local dev          | `.env` → `DATABASE_URL`   | Optional — the docker-compose Postgres works fine too    |

## 8. Why not Supabase Auth / Storage / Realtime?

GULA enforces its own RBAC (9 roles × 13 permissions) and JWTs. Mixing
Supabase Auth would create two sources of truth. We use Supabase **only**
as a managed Postgres + automated backups + good observability. Storage
and realtime stay disabled.
