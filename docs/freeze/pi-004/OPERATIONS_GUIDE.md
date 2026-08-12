# PI-004: National Deployment, Operations & Resilience Platform

## Operations Guide

**Version:** 1.0.0
**App Version:** 2.1.0
**Date:** 2026-07-16

---

### 1. Monitoring Stack

#### 1.1 Stack Overview

The GULA Platform uses the Grafana LGTM stack (Loki, Grafana, Tempo, Mimir) with Prometheus for production observability:

| Component | Role | Config Path |
|-----------|------|-------------|
| Prometheus | Metrics collection & alerting | `config/prometheus/prometheus.yml` |
| Grafana | Visualization & dashboards | `config/grafana/provisioning/` |
| Alertmanager | Alert routing & notification | `config/alertmanager/alertmanager.yml` |
| Loki | Log aggregation | `config/loki/loki-config.yml` |
| Tempo | Distributed tracing | `config/tempo/tempo-config.yml` |
| Promtail | Log shipping | `config/promtail/promtail-config.yml` |
| OpenTelemetry Collector | Trace collection | `config/opentelemetry/otel-collector-config.yml` |

#### 1.2 Prometheus Configuration (`config/prometheus/prometheus.yml`)

Scrape configuration:

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  scrape_timeout: 10s
  external_labels:
    cluster: 'gula-platform'
    environment: 'production'
```

Scrape targets: prometheus self, gula-backend (`/metrics/prom` with Bearer token auth), node-exporter (host metrics), postgres-exporter, redis-exporter, nginx-exporter.

Bearer token authentication for metrics endpoint (configured in `docker-compose.yml:151`):

```bash
make metrics-token  # Generates token at config/prometheus/metrics_token
```

#### 1.3 Grafana Dashboards

Provisioned dashboards at `config/grafana/dashboards/`:

| Dashboard | File | Focus |
|-----------|------|-------|
| Platform Overview | `gula-platform.json` | System-wide health |
| Platform Full | `gula-platform-full.json` | Comprehensive metrics |
| Laboratory | `gula-laboratory.json` | Per-lab operations |
| Hospital | `gula-hospital.json` | Hospital-level view |
| Clinical | `gula-clinical.json` | Clinical workflow |
| Business | `gula-business.json` | Business KPIs |
| Security | `gula-security.json` | Security posture |
| Capacity | `gula-capacity.json` | Resource utilization |
| National Status | `gula-national-status.json` | National deployment |
| Incident | `gula-incident.json` | Incident management |

Automated provisioning via `config/grafana/provisioning/dashboards/dashboards.yml` and `config/grafana/provisioning/datasources/datasources.yml`.

#### 1.4 Monitoring Activation

```bash
# Start monitoring stack (optional profile in docker-compose.yml:306)
ENABLE_MONITORING=true docker compose --profile monitoring up -d prometheus grafana

# Full stack monitoring
docker compose -f docker-compose.full.yml up -d prometheus grafana loki

# Access via SSH tunnel
ssh -L 9090:localhost:9090 -L 3000:localhost:3000 user@server
```

---

### 2. Alerting

#### 2.1 Alertmanager (`config/alertmanager/alertmanager.yml`)

Multi-channel alerting with severity-based routing:

| Severity | Channels | Repeat Interval | Config |
|----------|----------|-----------------|--------|
| CRITICAL | PagerDuty + Slack #gula-critical + Email oncall | 1h | `alertmanager.yml:25-41` |
| WARNING | Slack #gula-alerts + Email ops | 4h | `alertmanager.yml:44-53` |
| INFO | Slack #gula-info | 24h | `alertmanager.yml:56-59` |
| Database | Slack #gula-db-alerts | 1h | `alertmanager.yml:62-65` |
| Kill Switch | PagerDuty immediate | 5m | `alertmanager.yml:68-73` |

Inhibition rules suppress lower-severity alerts when critical is firing for the same service.

Notification templates at `config/alertmanager/templates/slack.tmpl` and `config/pagerduty.tmpl`.

#### 2.2 Prometheus Alert Rules (`config/prometheus/rules/`)

| Rule File | Rule Groups | Count |
|-----------|-------------|-------|
| `gula.yml` | SLO recording, Availability, Performance, Capacity, Infrastructure, Database, Control Layer | ~30 rules |
| `gula-full.yml` | Extended rules for full-stack deployment | Additional rules |
| `slo.yml` | Service Level Objective rules | SLO-specific |

Key alert rules in `config/prometheus/rules/gula.yml`:

- **BackendDown** (critical): `gula_up == 0` for >1m
- **DatabaseDown** (critical): `gula_db_up == 0` for >1m
- **DatabaseSlow** (warning): DB latency >200ms for 3m
- **DatabaseVerySlow** (critical): DB latency >500ms for 2m
- **ConcurrencyLimitReached** (critical): `gula_active_requests > 190`
- **HighMemory** (warning): Backend RSS >600MB for 5m
- **DiskSpaceCritical** (critical): Disk >92%
- **DatabaseAuthFailed** (critical): Immediate — permanent misconfiguration
- **DatabaseErrorRatioCritical** (critical): >75% DB health check failure rate
- **KillSwitchActive** (critical): Autonomous actions halted
- **DegradationL2ReadOnly** (warning): DB circuit open, writes blocked
- **DegradationL3CriticalOnly** (critical): DB storm, only essential paths reachable
- **OrderBacklog** (warning): 100+ pending orders for 5m
- **PolicyBlockSpike** (warning): Autonomous actions blocked spike

#### 2.3 Self-Healing Health Alerts (`docker-compose.yml:148-149`)

```yaml
ALERT_WEBHOOK_URL: ${ALERT_WEBHOOK_URL:-}  # Telegram/Discord/Slack
HEALTH_ALERT_INTERVAL_SECONDS: ${HEALTH_ALERT_INTERVAL_SECONDS:-60}
```

The `_health_alert_loop` watchdog (defined in `backend/app/main.py`) scores the system GREEN/YELLOW/RED every 60s and fires alerts on transitions.

---

### 3. Central Logging

#### 3.1 Loki (`config/loki/loki-config.yml`)

```yaml
limits_config:
  ingestion_rate_mb: 16
  ingestion_burst_size_mb: 32
  max_streams_per_user: 10000
```

#### 3.2 Promtail (`config/promtail/promtail-config.yml`)

Collects from:
- Docker container logs (`/var/lib/docker/containers/*/*.log`)
- Host system logs (`/var/log/*`)
- Application logs

#### 3.3 Structured Logging

Nginx JSON log format (`config/nginx/nginx.conf:36-51`):

```nginx
log_format json_combined escape=json
  '{ "time":"$time_iso8601", "remote_addr":"$remote_addr", ...}';
```

FastAPI structured JSON logging via `backend/app/core/logging_config.py`.

---

### 4. Distributed Tracing

#### 4.1 Grafana Tempo (`config/tempo/tempo-config.yml`)

- **Receiver protocols:** OTLP (gRPC + HTTP), Jaeger (gRPC, Thrift, Binary, Compact), Zipkin
- **Storage backend:** S3 (MinIO) — bucket `tempo-traces`
- **Block retention:** 48h
- **Metrics generator:** Span metrics + service graphs → remote write to Prometheus
- **Search:** Enabled with SLO (5s duration, 1GB/s throughput)

#### 4.2 OpenTelemetry (`config/opentelemetry/`)

- Collector config: `otel-collector-config.yml`
- Docker Compose: `docker-compose.otel.yml`
- Python instrumentation: `python-instrumentation.md`

#### 4.3 Jaeger (Legacy, `docker-compose.full.yml:506-518`)

Available in full stack for compatibility:
```yaml
jaeger:
  image: jaegertracing/all-in-one:1.51
  environment:
    COLLECTOR_OTLP_ENABLED: "true"
```

#### 4.4 Request Correlation

Every request receives a unique `X-Request-ID` header (set by `RequestIDMiddleware` in `backend/app/main.py` and nginx `haproxy.cfg:42`):

```haproxy
http-request set-header X-Request-ID %[uuid()] if !{ req.hdr(X-Request-Id) -m found }
```

---

### 5. Health Endpoints

| Path | Purpose | Status Code | Config |
|------|---------|-------------|--------|
| `/health` | Liveness (process alive) | 200 | `docker-compose.yml:178` |
| `/health/live` | Same as above | 200 | nginx healthcheck target |
| `/health/ready` | Readiness (startup guard complete) | 200/503 | `docker-compose.yml:179` |
| `/health/status` | Startup diagnostic info | 200 | Always visible |
| `/health/deep` | Full diagnostic (grade, latency, memory) | 200 | Used by `make health-deep` |

All five are in `_ALWAYS_ALLOWED_PATHS` — they bypass readiness, degraded-mode, and concurrency middlewares.

#### 5.1 Monitoring Commands

```bash
make health           # Quick liveness (containers + HTTP 200)
make health-deep      # Full diagnostic: grade (GREEN/YELLOW/RED), latency, memory
make status           # ps + health-deep combined
```

---

### 6. Self-Healing Operations

#### 6.1 Three-Layer Self-Healing

1. **Circuit Breaker** (`backend/app/core/self_healing.py`): Isolates failing DB/Redis; flips to degraded mode. Three levels: L1_NORMAL, L2_READ_ONLY, L3_CRITICAL_ONLY.

2. **Auto-Repair Engine** (`backend/app/core/auto_repair.py`): GC, pool recycle, reconnects.

3. **Adaptive Concurrency** (`backend/app/main.py::_adaptive_concurrency_loop`): Halves `_MAX_CONCURRENT` on 2 slow DB readings (>300ms); restores after 3 fast (<150ms).

#### 6.2 Auto-Repair Scripts

```bash
./scripts/auto_heal.sh            # Automated healing
./scripts/self_heal.py            # Python self-healing agent
./scripts/gula_autofix.py         # Automated fix application
```

---

### 7. Incident Detection & Response

#### 7.1 Incident Categories

| Category | Severity | Response |
|----------|----------|----------|
| Backend Down | Critical | PagerDuty + Slack + Email |
| Database Down | Critical | PagerDuty + Slack + Email |
| Disk Full | Critical | PagerDuty + Slack + Email |
| Performance Degradation | Warning | Slack + Email |
| Kill Switch Active | Critical | PagerDuty immediate (5m repeat) |
| DB Storm (L3) | Critical | Emergency degrade |

#### 7.2 Runbooks

- **DB Failover:** `scripts/pg_failover.sh` or `config/postgres-ha/failover.sh`
- **Emergency Fix:** `scripts/emergency-fix.sh`
- **Droplet Repair:** `scripts/repair-droplet.sh` (requires approval)
- **Diagnostics:** `scripts/diagnose-droplet.sh` (read-only, always safe)
- **Fix Server:** `scripts/fix-server.sh`

#### 7.3 Control Layer

```bash
make kill-switch-on     # Enable kill switch (blocks all autonomous actions)
make kill-switch-off    # Disable kill switch
make control-stats      # View control layer statistics
```

#### 7.4 Monitoring Dashboard Access

```bash
# SSH tunnel for secure access
ssh -L 9090:localhost:9090 -L 3000:localhost:3000 -L 9093:localhost:9093 user@host

# Grafana metrics dashboard
make metrics-token  # Generate bearer token for Prometheus
```

---

### 8. Operational Commands Reference

| Command | Purpose |
|---------|---------|
| `make up` | Start stack + wait for readiness |
| `make down` | Stop and remove containers |
| `make restart` | Rebuild + restart + deep health check |
| `make ps` | Container status |
| `make logs-backend` | Tail backend logs |
| `make logs-db` | Tail PostgreSQL logs |
| `make logs-redis` | Tail Redis logs |
| `make monitoring` | Start Prometheus + Grafana |
| `make shell` | Bash into backend container |
| `make db-shell` | psql into PostgreSQL |
| `make redis-cli` | redis-cli shell |
| `make backup` | pg_dump to ./backups/ |
| `make health-deep` | Full health diagnostic |
| `make chaos-run` | Execute chaos experiments |

---

**References:** `config/prometheus/`, `config/alertmanager/`, `config/loki/`, `config/tempo/`, `config/grafana/`, `config/promtail/`, `config/opentelemetry/`, `scripts/self_heal.py`, `scripts/monitor.sh`, `scripts/diagnose.sh`, `scripts/check_platform.sh`, `scripts/auto_heal.sh`, `backend/app/core/self_healing.py`, `backend/app/core/auto_repair.py`
