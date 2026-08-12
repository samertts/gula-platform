# GULA Platform — DigitalOcean Deployment

Two supported flavours on DigitalOcean:

| Mode             | When to use                                          | Files                                        |
| ---------------- | ---------------------------------------------------- | -------------------------------------------- |
| **App Platform** | Managed PaaS, autoscaling, zero ops. Recommended.    | `digitalocean/app.yaml`                      |
| **Droplet**      | Full Docker-Compose stack, more control, lower cost. | `scripts/server-setup.sh`, `docker-compose.yml` |

Both modes use **Supabase** as the Postgres provider unless you self-host Postgres
inside the droplet.

---

## A. App Platform (managed, recommended)

### 1. Install `doctl`
```bash
brew install doctl                    # macOS
# or:  snap install doctl              # Linux
doctl auth init                       # paste an API token from cloud.digitalocean.com
```

### 2. Create the app
```bash
doctl apps create --spec digitalocean/app.yaml
APP_ID=$(doctl apps list --format ID,Spec.Name --no-header | grep gula-platform | awk '{print $1}')
echo "APP_ID=$APP_ID"
```

### 3. Set the encrypted secrets
The spec ships with `REPLACE_VIA_DASHBOARD` placeholders. Replace them via
the dashboard (App → Settings → App-Level Environment Variables) **or**
patch the spec:

```bash
# Generate keys locally
ENCRYPTION_KEY=$(python3 -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())')
NID_HMAC_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(32))')
DEVICE_HMAC_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(32))')
SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_urlsafe(64))')
REFRESH_TOKEN_SECRET=$(python3 -c 'import secrets; print(secrets.token_urlsafe(64))')
METRICS_BEARER_TOKEN=$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')
GULA_ADMIN_PASSWORD=$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')

# Apply via the dashboard or edit app.yaml then:
doctl apps update "$APP_ID" --spec digitalocean/app.yaml
```

`DATABASE_URL` must be a **Supabase pooled** connection string (port `6543`,
`?sslmode=require`). See `supabase/README.md`.

### 4. Trigger the first deploy
```bash
doctl apps create-deployment "$APP_ID" --force-rebuild
doctl apps logs "$APP_ID" --type build --follow
```

The `pre_deploy` step runs `alembic upgrade head` automatically.

### 5. Attach a custom domain
```bash
doctl apps update "$APP_ID" --spec digitalocean/app.yaml \
  --update-domain gula-platform.org
```
(or via the dashboard) — DO will issue + renew Let's Encrypt for you.

### 6. Verify
```bash
APP_URL=$(doctl apps get "$APP_ID" --format DefaultIngress --no-header)
curl -fsSL "$APP_URL/health" | jq
curl -fsSL "$APP_URL/health/deep" | jq
```

---

## B. Droplet (Docker-Compose, full stack)

For when you want to run **everything** inside one VM (Postgres, Redis, nginx,
Prometheus, Grafana). Cheapest production-capable size is the **2 GB / 2 vCPU**
basic droplet at $18/mo — but bump to **4 GB / 2 vCPU ($24/mo)** for headroom.

### 1. Spin a droplet
```bash
doctl compute droplet create gula-prod \
  --image ubuntu-22-04-x64 \
  --size s-2vcpu-4gb \
  --region fra1 \
  --ssh-keys $(doctl compute ssh-key list --format ID --no-header | head -1) \
  --enable-monitoring --enable-backups
```

### 2. Run the bootstrap (installs Docker, nginx, certbot, clones repo)
```bash
DROPLET_IP=$(doctl compute droplet list --format Name,PublicIPv4 --no-header | grep gula-prod | awk '{print $2}')
ssh root@$DROPLET_IP 'curl -fsSL https://raw.githubusercontent.com/samertts/gula-platform/main/scripts/server-setup.sh | sudo bash'
```

### 3. Configure secrets and start the stack
```bash
ssh samertts@$DROPLET_IP
cd ~/gula-platform
cp .env.example .env
nano .env                              # fill DATABASE_URL, ENCRYPTION_KEY, ...
docker compose up -d
docker compose logs -f gula-backend
```

### 4. Day-2 operations
All routine commands are wrapped in `scripts/digitalocean-manage.sh`:
```bash
./scripts/digitalocean-manage.sh status
./scripts/digitalocean-manage.sh logs gula-backend
./scripts/digitalocean-manage.sh deploy main
./scripts/digitalocean-manage.sh backup
./scripts/digitalocean-manage.sh scale 3
./scripts/digitalocean-manage.sh kill-switch on
```

---

## Cost cheat-sheet (April 2026)

| Setup                                    | Monthly |
| ---------------------------------------- | ------- |
| App Platform basic-xs + DO Redis dev     | ~$19    |
| App Platform basic-s + DO Redis primary  | ~$32    |
| Droplet 4 GB + Supabase Free             | ~$24    |
| Droplet 4 GB + Supabase Pro              | ~$49    |
