# GULA Platform — Production Deployment

Step-by-step runbook for deploying the GULA medical-laboratory SaaS on a fresh
Linux VPS. Aligned with the actual stack (FastAPI + PostgreSQL 16 + Redis 7),
the existing `Makefile`, `setup-production.sh`, the CI/CD pipeline in
`.github/workflows/`, and the nginx reverse-proxy config in
`config/nginx/system/`.

> **Stack note** — The platform uses **PostgreSQL 16 exclusively**. MySQL is
> not supported. Ignore any older docs that mention `mysql` / `mysqldump` —
> they predate the migration.

---

## Topology

```
Internet
   │
   ▼
Host nginx (TLS, port 80/443)        ◄── system service, /etc/nginx
   │
   ▼
api-gateway  (Docker, 127.0.0.1:8080) ◄── reverse proxy + rate limit
   │
   ▼
gula-backend (FastAPI, expose 8000)   ◄── gunicorn + uvicorn workers
   │
   ├─► postgres (postgres:16-alpine, expose 5432)
   └─► redis    (redis:7-alpine,    expose 6379)
```

The backend never binds a public port. All traffic enters through host nginx
→ Docker api-gateway → backend. See `docker-compose.yml`.

---

## Quick path — fresh VPS to verified-live in ~10 minutes

If you have a clean Ubuntu 22.04 VPS and SSH access, this is the shortest
path to a system you can trust. Each step has a verification gate; do not
proceed until the previous gate prints `[✓]`.

```bash
# 0. SSH in as the deploy user, clone, configure
git clone https://github.com/samertts/gula-platform.git
cd gula-platform
cp .env.example .env
nano .env                        # set BASE_URL, CORS_ORIGINS, GULA_ADMIN_*

# 1. Bring up the stack with auto-secret-generation + health gate
sudo bash setup-production.sh    # ~5 min — exits non-zero on any failure
                                 # gate: prints "GULA Platform is running!"

# 2. Smoke + perf gate against the live system
bash scripts/smoke-bootstrap.sh
                                 # gate: prints "Smoke gate PASSED"
                                 # checks /health, /health/ready, /health/deep,
                                 # POST /login, authed GET, p50/p95/p99 latency,
                                 # error rate over 100 calls

# 3. TLS (only after DNS A-record points at this VPS)
sudo bash scripts/setup-https.sh api.gula.iq
                                 # gate: curl -I https://api.gula.iq/health → 200

# 4. Re-run the smoke gate against the public URL
bash scripts/smoke-bootstrap.sh https://api.gula.iq
                                 # gate: same as step 2, but over the internet

# 5. Backups
make backup
bash scripts/backup-verification.sh ./backups/gula_*.sql.gz | tail -1
                                 # gate: prints "Backup is restorable"
```

If any gate fails, do not proceed. Run `make logs-backend` to see the
single-line reason; the startup guard / health endpoints are explicit about
what failed and why. The detailed phase-by-phase guide below covers
everything Quick Path skips (CI/CD, monitoring, scaling, on-prem mode,
mobile clients).

---

## Phase 1 — Provision the VPS

Minimum viable host:

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| OS       | Ubuntu 22.04 LTS | Ubuntu 22.04 LTS |
| vCPU     | 2 | 4 |
| RAM      | 4 GB | 8 GB |
| Disk     | 40 GB SSD | 80 GB SSD |
| Network  | Public IPv4 + DNS A record | + IPv6 |

```bash
# As root, on the VPS
apt update && apt upgrade -y
apt install -y docker.io docker-compose-plugin git nginx certbot \
                python3-certbot-nginx ufw fail2ban
systemctl enable --now docker

# Firewall
ufw allow OpenSSH
ufw allow 'Nginx Full'
ufw --force enable

# Create deploy user (do NOT deploy as root)
adduser --disabled-password --gecos "" samertts
usermod -aG docker,sudo samertts
mkdir -p /home/samertts/.ssh
# Paste the deploy key into authorized_keys, chown samertts:samertts, chmod 600
```

---

## Phase 2 — Clone & configure

```bash
sudo -iu samertts
git clone https://github.com/samertts/gula-platform.git
cd gula-platform

# Generate strong secrets in one shot
make secrets-gen >> .env          # appends SECRET_KEY, ENCRYPTION_KEY, etc.
# OR use the dedicated script that writes a complete .env:
bash scripts/generate-launch-secrets.sh
```

Then open `.env` and set:

```env
ENV=production
DEBUG=false
LOG_LEVEL=warning

BASE_URL=https://api.gula.iq            # your domain
CORS_ORIGINS=https://gula.iq,https://www.gula.iq
ENABLE_API_DOCS=false                   # /docs is admin-gated in prod anyway

POSTGRES_PASSWORD=<from secrets-gen>
DATABASE_URL=postgresql://postgres:<same-password>@postgres:5432/labdb
REDIS_PASSWORD=<from secrets-gen>
REDIS_URL=redis://:<same-password>@redis:6379

SECRET_KEY=<from secrets-gen>           # JWT signing
REFRESH_TOKEN_SECRET=<DIFFERENT value>  # MUST differ from SECRET_KEY
ENCRYPTION_KEY=<Fernet key>             # never change after first data write
NID_HMAC_KEY=<from secrets-gen>         # never change after first patient
DEVICE_HMAC_KEY=<from secrets-gen>

GULA_ADMIN_EMAIL=admin@gula.iq
GULA_ADMIN_PASSWORD=<strong, ≥20 chars>

TZ=Asia/Baghdad
```

`config.py` hard-fails on startup if any of these are missing or match a
known weak pattern — that's a feature, not a bug.

`.env.example` is the source-of-truth template; if you add a new variable,
update it in the same PR.

---

## Phase 3 — Bring up the stack

```bash
make ci          # syntax-gate + lint + docker build (locally — fast feedback)
make up          # docker compose up -d + waits for /health/ready
make health-deep # full diagnostic: GREEN / YELLOW / RED grade
```

Expected on success:

```
gula-postgres    healthy
gula-redis       healthy
gula-backend     healthy
api-gateway      healthy
Grade: GREEN
```

If `make health-deep` returns RED, check `make logs-backend` first — the
startup guard prints a single line explaining exactly which check failed
(missing secret, DB unreachable, migration drift, etc.).

---

## Phase 4 — TLS termination (host nginx)

`config/nginx/system/gula-platform-http.conf` is the bootstrap HTTP-only
config. The deploy script copies it into `/etc/nginx/sites-available/` on
every push. To enable HTTPS:

```bash
# Point your DNS A record at the VPS first, then:
sudo bash scripts/setup-https.sh api.gula.iq
```

This script:

1. Confirms the domain resolves to this host
2. Runs `certbot --nginx -d api.gula.iq --redirect`
3. Swaps the active nginx config to the SSL-enabled variant
4. Sets up the renewal timer (`systemctl status certbot.timer`)

Verify:

```bash
curl -I https://api.gula.iq/health
# HTTP/2 200
# strict-transport-security: max-age=31536000
```

---

## Phase 5 — CI/CD

`.github/workflows/ci.yml` runs on every push (syntax-gate, migrations,
smoke test, pytest, security scan, image build to GHCR).

`.github/workflows/deploy.yml` runs on pushes to `main`:

1. Resolves the GHCR image tag (short SHA)
2. SSHs to `${SERVER_HOST}` as `${SERVER_USER}` using `${SERVER_SSH_KEY}`
3. `git fetch origin main && git reset --hard origin/main` (preserving `.env`)
4. Auto-fills any missing secrets in `.env`
5. Pulls the new image, `docker compose up -d --remove-orphans`
6. Waits up to 3 minutes for `http://127.0.0.1:8080/health` to respond
7. **Rolls back to the previous commit** if the health check fails

Required GitHub Secrets:

| Secret | Value |
|--------|-------|
| `SERVER_HOST` | `1.2.3.4` (VPS IPv4) |
| `SERVER_USER` | `samertts` (deploy user) |
| `SERVER_SSH_KEY` | full Ed25519 private key |

Manual deploys: `gh workflow run deploy.yml -f image_tag=<sha>`.

---

## Phase 6 — Backups

```bash
# Manual snapshot (gzipped pg_dump → ./backups/gula_<ts>.sql.gz)
make backup

# Verify a backup is restorable on a scratch DB
bash scripts/backup-verification.sh ./backups/gula_<ts>.sql.gz
```

For automated nightly backups, set in `.env`:

```env
BACKUP_ENABLED=true
BACKUP_SCHEDULE=0 2 * * *      # 02:00 Asia/Baghdad
BACKUP_RETENTION_DAYS=30
```

The `gula-backup` sidecar in `docker-compose.full.yml` runs
`scripts/backup.sh` on the schedule; old archives past
`BACKUP_RETENTION_DAYS` are pruned automatically.

Off-host copy (recommended): rsync `./backups/` to a separate object store
nightly via cron.

---

## Phase 7 — Monitoring (optional)

```bash
make metrics-token       # writes config/prometheus/metrics_token
make monitoring          # starts prometheus + grafana on the monitoring profile
```

Both bind to `127.0.0.1` only — reach them via SSH tunnel:

```bash
ssh -L 9090:127.0.0.1:9090 -L 3001:127.0.0.1:3000 samertts@api.gula.iq
# then http://localhost:9090 (Prometheus) and http://localhost:3001 (Grafana)
```

Grafana is provisioned from `config/grafana/`; dashboards reload on container
start. Default login is `admin` + `${GRAFANA_PASSWORD}` from `.env`.

For external alerting set `ALERT_WEBHOOK_URL` in `.env` (Telegram / Discord
/ Slack). The `_health_alert_loop` watchdog in `backend/app/main.py` fires
on GREEN→YELLOW→RED transitions and re-fires every 5 min while RED.

---

## Phase 8 — Horizontal scaling

```bash
make scale REPLICAS=5    # HAProxy + 5 backend replicas
open http://localhost:8404/stats   # via SSH tunnel
```

Pool budget: `WEB_CONCURRENCY × (DB_POOL_SIZE + DB_MAX_OVERFLOW) <
postgres.max_connections`. With defaults (`2 × (3 + 7) = 20` per replica)
five replicas use 100 connections — bump `max_connections` in
`config/postgres/postgresql.conf` if you exceed that.

---

## Phase 9 — Local / on-prem mode

For laboratories without reliable internet, the same stack runs on a
mini-PC inside the lab. The only differences from cloud mode:

| Setting | Cloud | Local |
|---------|-------|-------|
| `BASE_URL` | `https://api.gula.iq` | `http://192.168.1.10:8000` |
| `CORS_ORIGINS` | public domain | `http://192.168.1.10` |
| TLS | Let's Encrypt | self-signed (or none on LAN) |
| `DEBUG` | `false` | `false` (still) |

The mobile and web clients pick the base URL at runtime (see Phase 10) — no
code changes are required to switch modes.

For lab-instrument integration (ASTM/HL7), enable the device-bridge profile:

```bash
docker compose --profile device-bridge up -d device-bridge
```

See `services/device_bridge/README.md`.

---

## Phase 10 — Mobile & web clients

The Flutter mobile app and `frontend-v2/` React app talk to the **same
public API** — never directly to the database.

Flutter base-URL pattern:

```dart
const baseUrl = String.fromEnvironment(
  'API_URL',
  defaultValue: 'https://api.gula.iq',
);
final dio = Dio(BaseOptions(
  baseUrl: baseUrl,
  headers: {'Authorization': 'Bearer $jwt'},
));
```

Build for production:

```bash
flutter build appbundle --release --dart-define=API_URL=https://api.gula.iq
flutter build ios       --release --dart-define=API_URL=https://api.gula.iq
```

Build for an offline-capable lab install:

```bash
flutter build apk --release --dart-define=API_URL=http://192.168.1.10:8000
```

App-store requirements (both stores reject without these):

- HTTPS in production (no plaintext `http://` in the public build)
- Privacy policy URL (citizen-data implications — required for healthcare apps)
- Justified Android permissions (camera = barcode scan, location = lab pickup,
  notifications = result-ready alerts)
- Apple: 2 FA on the developer account, an iOS-13-or-newer minimum target

---

## Production readiness checklist

Run through this before announcing the deployment:

- [ ] `make ci` passes locally
- [ ] `.env` has zero `CHANGE_ME` markers (`grep CHANGE_ME .env` returns nothing)
- [ ] `make health-deep` reports `Grade: GREEN`
- [ ] `curl -I https://<domain>/health` returns 200 + HSTS header
- [ ] `/docs` is gated (returns 401 without admin JWT)
- [ ] `make backup` succeeds and `scripts/backup-verification.sh` confirms restore
- [ ] `gh secret list` shows `SERVER_HOST`, `SERVER_USER`, `SERVER_SSH_KEY`
- [ ] Push a no-op commit to `main` and watch `deploy.yml` go green end-to-end
- [ ] DNS has a low-TTL A record (300 s) to enable fast failover
- [ ] Admin password rotated from the bootstrap value
- [ ] `ALERT_WEBHOOK_URL` set and a test alert reaches the on-call channel

---

## Troubleshooting

**`make up` hangs at "waiting for /health/ready"**
Run `make logs-backend`. The startup guard prints exactly one line per
failed check. Most common causes: missing secret in `.env`, Postgres
volume from a previous version that's incompatible with the current
schema (run `make backup && docker volume rm gula-platform_pgdata` only as
a last resort, after confirming the backup), or `migrations/` divergence
(`docker compose run --rm gula-backend alembic upgrade head`).

**Deploy succeeds but `/health` returns 503**
The readiness middleware blocks every non-whitelisted path until the
startup guard confirms DB reachability. Hit `/health/status` instead — it
bypasses the readiness gate and explains why startup hasn't completed.

**High DB connection count**
Check `WEB_CONCURRENCY × (DB_POOL_SIZE + DB_MAX_OVERFLOW) <
postgres.max_connections` (default 100). Lower `DB_MAX_OVERFLOW` or raise
`max_connections` in `config/postgres/postgresql.conf`.

**Container OOM-killed**
`docker stats` to confirm. Bump `BACKEND_MEM_LIMIT` / `PG_MEM_LIMIT` in
`.env`, then `make restart`.

**Deploy rolled back automatically**
`deploy.yml` rolls back on health-check failure. SSH in, `git log -3` to
see which commit you're on, then `make logs-backend` on the rolled-back
build to find the regression. Fix on a branch, re-merge.

---

## Reference

| Path | Purpose |
|------|---------|
| `Makefile` | Every operational command — `make help` lists them |
| `setup-production.sh` | One-shot bootstrap for a fresh VPS |
| `deploy.sh` | Manual deploy from the VPS itself |
| `scripts/generate-launch-secrets.sh` | Writes a complete `.env` |
| `scripts/setup-https.sh` | Certbot + nginx SSL switch-over |
| `scripts/backup.sh` / `backup-verification.sh` | DB snapshot + restore test |
| `scripts/dr_recovery.sh` | Disaster-recovery playbook |
| `scripts/preflight.sh` | Pre-deploy sanity check |
| `config/nginx/system/` | Host-level nginx (HTTP-only and SSL variants) |
| `config/postgres/postgresql.conf` | DB tuning |
| `config/haproxy/haproxy.cfg` | Load balancer (used by `make scale`) |
| `config/prometheus/` | Scrape config + alert rules |
| `config/grafana/` | Provisioned dashboards |
| `.github/workflows/ci.yml` | CI: syntax + migrations + tests + security + build |
| `.github/workflows/deploy.yml` | CD: pull + restart + health gate + auto-rollback |
| `.github/workflows/blue-green-deploy.yml` | Zero-downtime release variant |
