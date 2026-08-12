# GULA Platform — Configuration Reference

**Version:** 1.0 | **Last Updated:** 2026-07-23

## Table of Contents

1. [Configuration Philosophy](#1-configuration-philosophy)
2. [Environment Variable Categories](#2-environment-variable-categories)
   - 2.1 [App Configuration](#21-app-configuration)
   - 2.2 [Runtime Isolation](#22-runtime-isolation)
   - 2.3 [Database](#23-database)
   - 2.4 [JWT & Secrets](#24-jwt--secrets)
   - 2.5 [Redis](#25-redis)
   - 2.6 [Caching](#26-caching)
   - 2.7 [Read Replica](#27-read-replica)
   - 2.8 [Rate Limiting](#28-rate-limiting)
   - 2.9 [Upload Limits](#29-upload-limits)
   - 2.10 [Startup Guard](#210-startup-guard)
   - 2.11 [AI Providers](#211-ai-providers)
   - 2.12 [Notifications](#212-notifications)
   - 2.13 [Feature Flags: SNDHS](#213-feature-flags-sndhs)
   - 2.14 [Feature Flags: Financial Engine](#214-feature-flags-financial-engine)
   - 2.15 [Feature Flags: AI Dataset](#215-feature-flags-ai-dataset)
   - 2.16 [External Adapters (Government Integration)](#216-external-adapters-government-integration)
   - 2.17 [Cloudflare](#217-cloudflare)
   - 2.18 [Supabase](#218-supabase)
   - 2.19 [Kernel Runtime](#219-kernel-runtime)
   - 2.20 [Edge Platform](#220-edge-platform)
   - 2.21 [Monitoring & Alerting](#221-monitoring--alerting)
   - 2.22 [Self-Audit](#222-self-audit)
   - 2.23 [Auto-Repair](#223-auto-repair)
   - 2.24 [Control Layer & Kill Switch](#224-control-layer--kill-switch)
   - 2.25 [Metrics & Observability](#225-metrics--observability)
   - 2.26 [Admin Bootstrap](#226-admin-bootstrap)
   - 2.27 [Device Bridge (LabLink-Core)](#227-device-bridge-lablink-core)
   - 2.28 [Docker & Container Resources](#228-docker--container-resources)
   - 2.29 [Platform Info](#229-platform-info)
   - 2.30 [National Integration Connectors](#230-national-integration-connectors)
   - 2.31 [Digital Twin Platform](#231-digital-twin-platform)
   - 2.32 [Command Intelligence](#232-command-intelligence)
3. [Weak Secret Detection](#3-weak-secret-detection)
4. [Hard Fail Behaviours](#4-hard-fail-behaviours)
5. [Adapter Mode Resolution](#5-adapter-mode-resolution)
6. [Database Connection Pool Formula](#6-database-connection-pool-formula)

---

## 1. Configuration Philosophy

The application uses environment variables for all configuration. Secrets have NO hardcoded fallbacks in production — absence causes hard fail on startup (`sys.exit(1)`). In development, safe random defaults are generated for secrets (with warnings logged).

Configuration is loaded eagerly at module level in `backend/app/config.py`. Feature flags are deployed as environment variables so that toggling a feature never requires a code change — just a container restart.

**Key principles:**
- Every secret must be set in `.env` for production deployments
- Weak/guessable secret patterns cause hard fail in production
- New columns in migrations must always be nullable or have `server_default`
- Feature flags default to `false` so new behaviour is opt-in

---

## 2. Environment Variable Categories

### 2.1 App Configuration

| Variable | Default | Required | Secret | Description |
|----------|---------|----------|--------|-------------|
| `ENV` | `production` | No | No | Runtime environment (`production`, `development`, `test`). Controls production guards. |
| `APP_NAME` | `GULA Platform` | No | No | Application name used in responses and metadata. |
| `APP_VERSION` | `2.5.0` | No | No | Application version, updated with each release. |
| `BASE_URL` | `http://localhost:8000` | No | No | Base URL for link generation (result links, password resets, etc.). |
| `PLATFORM_NAME_AR` | `منصة غولا الصحية` | No | No | Arabic platform name. |
| `ENABLE_API_DOCS` | `false` | No | No | Enable Swagger `/docs` and ReDoc `/redoc` in production (for government testers). |
| `CORS_ORIGINS` | `""` | No | No | Comma-separated list of allowed CORS origins. |
| `PYTHONPATH` | `/app` | No | No | Python path for the `shared` library. Set to monorepo root. |

### 2.2 Runtime Isolation

| Variable | Default | Required | Secret | Description |
|----------|---------|----------|--------|-------------|
| `RUNTIME_MODE` | `api` | No | No | Controls process behaviour. Valid values: `api` (FastAPI HTTP server, no maintenance loops), `worker` (background tasks, outbox, recovery), `test` (pytest, never spawns threads), `cli` (one-shot scripts), `migration`, `openapi`. |
| `FEATURE_BACKGROUND_TASKS` | `false` (api) / `true` (worker) | No | No | Master kill-switch for background coroutines. Background tasks run only when this is `true` AND `RUNTIME_MODE=worker`. Hard-forced to `false` in test runtime. |

### 2.3 Database

| Variable | Default | Required | Secret | Description |
|----------|---------|----------|--------|-------------|
| `DATABASE_URL` | `""` (dev: `postgresql://postgres@localhost:5432/gula`) | Yes (prod) | Yes | PostgreSQL connection string. In production, absence causes `sys.exit(1)`. |
| `DB_POOL_SIZE` | `6` | No | No | SQLAlchemy connection pool size per worker. |
| `DB_MAX_OVERFLOW` | `12` | No | No | Maximum overflow connections beyond pool size. |
| `DB_POOL_TIMEOUT` | `10` | No | No | Timeout (seconds) for waiting on a pooled connection. |
| `DB_POOL_RECYCLE` | `1800` | No | No | Connection recycle time (seconds). |

### 2.4 JWT & Secrets

| Variable | Default | Required | Secret | Description |
|----------|---------|----------|--------|-------------|
| `SECRET_KEY` | Random 64-char URL-safe token (dev only) | Yes (prod) | Yes | Primary JWT signing key. Weak patterns cause hard fail in production. |
| `JWT_ALGORITHM` | `HS256` | No | No | JWT signing algorithm. |
| `JWT_EXPIRE_MINUTES` | `30` | No | No | Access token time-to-live in minutes. Takes priority over legacy `JWT_EXPIRE_HOURS`. |
| `JWT_EXPIRE_HOURS` | derived from `JWT_EXPIRE_MINUTES` | No | No | Legacy compat: used only when `JWT_EXPIRE_MINUTES` is not set. |
| `REFRESH_TOKEN_SECRET` | Random 64-char URL-safe token (dev only) | Yes (prod) | Yes | Refresh token signing key. Independent of `SECRET_KEY` for key separation. |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `30` | No | No | Refresh token time-to-live in days. |
| `ENCRYPTION_KEY` | `""` (dev warns) | Yes (prod) | Yes | Fernet symmetric key for AES-256-GCM encryption at rest. Must NOT change after first data is stored. Weak patterns cause hard fail in production. |
| `NID_HMAC_KEY` | Falls back to `ENCRYPTION_KEY` then `SECRET_KEY` (dev) | Yes (prod) | Yes | HMAC key for national ID hashing. Must NOT change after first registration or existing lookups will break. |
| `AUDIT_ANCHOR_KEY` | Falls back to `NID_HMAC_KEY` (dev) | Yes (prod) | Yes | Separate HMAC key for audit hash chain anchor integrity. Key separation best practice. |
| `DEVICE_HMAC_KEY` | `""` | No | Yes | HMAC key for lab device message signing and pharmacy dispensing verification. |
| `ALLOWED_DEVICE_IDS` | `""` | No | No | Comma-separated whitelist of analyzer device IDs. Empty = allow all. |

### 2.5 Redis

| Variable | Default | Required | Secret | Description |
|----------|---------|----------|--------|-------------|
| `REDIS_URL` | `""` (in-memory fallback) | No | Yes | Redis connection string. When absent, an in-memory store is used (not shared across workers). |
| `REDIS_SENTINEL_HOSTS` | `""` | No | No | Comma-separated list of Redis Sentinel hosts for HA (overrides `REDIS_URL`). |
| `REDIS_SENTINEL_MASTER` | `gula-redis-primary` | No | No | Redis Sentinel master service name. |
| `REDIS_CLUSTER_NODES` | `""` | No | No | Comma-separated Redis Cluster node addresses (overrides `REDIS_URL`). |

### 2.6 Caching

| Variable | Default | Required | Secret | Description |
|----------|---------|----------|--------|-------------|
| `CACHE_ENABLED` | `true` | No | No | Master switch for L1 (in-memory) + L2 (Redis) cache coordinator. |
| `CACHE_L1_TTL` | `60` | No | No | Default L1 in-memory cache TTL in seconds. |
| `CACHE_L2_TTL` | `300` | No | No | Default L2 Redis cache TTL in seconds. |
| `CACHE_L1_MAX_SIZE` | `10000` | No | No | Maximum number of entries in L1 cache. |
| `CACHE_METRICS_ENABLED` | `true` | No | No | Enable cache hit/miss/eviction metrics collection. |

### 2.7 Read Replica

| Variable | Default | Required | Secret | Description |
|----------|---------|----------|--------|-------------|
| `READ_REPLICA_URL` | `""` | No | Yes | Read replica PostgreSQL connection string. When set, read queries route here. |
| `READ_REPLICA_ENABLED` | `false` | No | No | Enable read replica query routing. Auto-detected if `READ_REPLICA_URL` is set. |
| `REPLICA_POOL_SIZE` | `10` | No | No | Read replica connection pool size. |
| `REPLICA_MAX_OVERFLOW` | `20` | No | No | Read replica max overflow connections. |

### 2.8 Rate Limiting

| Variable | Default | Required | Secret | Description |
|----------|---------|----------|--------|-------------|
| `RATE_LIMIT_AUTH` | `10` | No | No | Rate limit for authentication endpoints (requests per minute per IP). |
| `RATE_LIMIT_PUBLIC` | `30` | No | No | Rate limit for public endpoints (requests per minute per IP). |
| `RATE_LIMIT_BLOCK_DURATION_SECONDS` | `3600` | No | No | Duration (seconds) to hard-block an IP after 5x rate limit breach. |

### 2.9 Upload Limits

| Variable | Default | Required | Secret | Description |
|----------|---------|----------|--------|-------------|
| `MAX_UPLOAD_SIZE_MB` | `2` | No | No | Maximum individual file upload size in megabytes. |
| `MAX_REQUEST_BODY_MB` | `10` | No | No | Maximum total request body size in megabytes (enforced by middleware returning 413). |

### 2.10 Startup Guard

| Variable | Default | Required | Secret | Description |
|----------|---------|----------|--------|-------------|
| `STARTUP_TIMEOUT_SECONDS` | `120` | No | No | Maximum seconds the startup guard waits for all validation steps (DB, Redis, migrations, kernel) before switching to partial-readiness mode. |

### 2.11 AI Providers

All AI providers are optional — the platform functions without any AI key using rules-based fallback.

| Variable | Default | Required | Secret | Description |
|----------|---------|----------|--------|-------------|
| `GEMINI_API_KEY` | `""` | No | Yes | Google AI Studio (Gemini) API key. Free tier: 15 req/min, 1,500 req/day. |
| `GEMINI_CLINICAL_MODEL` | `gemini-2.0-flash` | No | No | Gemini model for clinical interpretation (e.g. `gemini-2.5-flash` for better accuracy). |
| `GEMINI_CHAT_MODEL` | `gemini-2.0-flash` | No | No | Gemini model for assistant chat endpoint. |
| `GROQ_API_KEY` | `""` | No | Yes | Groq API key for ultra-fast Llama inference. Free tier: 30 req/min. |
| `OLLAMA_BASE_URL` | `""` | No | No | Ollama server URL (e.g. `http://host.docker.internal:11434`). When set, Ollama is preferred over cloud providers. |
| `OLLAMA_MODEL` | `llama3.2:1b` | No | No | Ollama model for system optimization / metrics analysis (small & fast). |
| `OLLAMA_CLINICAL_MODEL` | `""` | No | No | Ollama model for clinical interpretation (e.g. `aya:8b` for Arabic, `llama3.2:3b`). |
| `OLLAMA_TIMEOUT` | `15` (config.py) / `20` (.env.example) | No | No | Ollama request timeout in seconds. |
| `OLLAMA_RATE_LIMIT_SECONDS` | `60` | No | No | Minimum interval between Ollama API calls. |
| `AI_PROVIDER` | `""` | No | No | Override auto-detection: `ollama`, `gemini`, `groq`, or `none`. Empty = auto-detect. |
| `EMBEDDING_MODEL` | `text-embedding-004` | No | No | Embedding model name for vector search. |
| `EMBEDDING_DIMENSIONS` | `768` | No | No | Embedding vector dimensionality. |
| `AI_BUDGET_SECONDS` | `6` | No | No | Timeout in seconds for AI embedding calls. |
| `METRICS_CACHE_SECONDS` | `30` | No | No | Metrics analysis cache TTL in seconds. |
| `ANALYSIS_CACHE_SECONDS` | `60` | No | No | AI system analysis cache TTL in seconds. |
| `ENABLE_PGVECTOR` | `false` | No | No | Enable pgvector extension for vector similarity search. |

### 2.12 Notifications

| Variable | Default | Required | Secret | Description |
|----------|---------|----------|--------|-------------|
| `FCM_SERVER_KEY` | `""` | No | Yes | Firebase Cloud Messaging server key for push notifications (only remaining Firebase dependency). |
| `APNS_KEY` | `""` | No | Yes | Apple Push Notification Service key for iOS notifications. |

### 2.13 Feature Flags: SNDHS

SNDHS-lite Phase 1 deployment-wide flags. All default to `false` so a fresh deploy behaves identically to the previous release.

| Variable | Default | Required | Secret | Description |
|----------|---------|----------|--------|-------------|
| `SNDHS_ENABLE_VISITS` | `false` | No | No | Enable visit tracking (`visits` table + `lab_orders.visit_id`). Requires data backfill before enabling. |
| `SNDHS_ENABLE_NATIONAL_ID` | `false` | No | No | Enable national ID / health ID fields on patients. Existing rows pre-backfill will have null values |

. |

### 2.14 Feature Flags: Financial Engine

| Variable | Default | Required | Secret | Description |
|----------|---------|----------|--------|-------------|
| `ENABLE_FINANCIAL_ENGINE` | `false` | No | No | Master switch for the Financial Engine (`/financial/*` routes, pricing, ranking, transactions, governance, incentives). Must stay OFF until Phase B+ is validated. |
| `ENABLE_ADS` | `false` | No | No | Sub-flag for sponsored listings / ad bidding surface. Has effect ONLY when `ENABLE_FINANCIAL_ENGINE` is also true. |

### 2.15 Feature Flags: AI Dataset

| Variable | Default | Required | Secret | Description |
|----------|---------|----------|--------|-------------|
| `ENABLE_AI_DATASET` | `false` | No | No | Enable AI interaction dataset pipeline (tables: `ai_interactions`, `ai_feedback`, `ai_retrieval_refs`, etc.). No code path reads or writes them until enabled. |
| `ENABLE_AI_FEEDBACK` | `false` | No | No | Sub-flag for explicit AI feedback collection. Has effect only when `ENABLE_AI_DATASET` is true. |

### 2.16 External Adapters (Government Integration)

Adapter modes control whether external API calls use real endpoints (`live`), return fake data (`stub`), or both (`shadow` — call live but return stub).

| Variable | Default | Required | Secret | Description |
|----------|---------|----------|--------|-------------|
| `GULA_ADAPTER_MODE` | `stub` | No | No | Global default adapter mode: `stub`, `live`, or `shadow`. |
| `GULA_ADAPTER_MODE_NID` | inherits `GULA_ADAPTER_MODE` | No | No | Override for the MoI National ID adapter. |
| `GULA_ADAPTER_MODE_INSURANCE` | inherits `GULA_ADAPTER_MODE` | No | No | Override for the NHI insurance adapter. |
| `GULA_ADAPTER_MODE_RESIDENCY` | inherits `GULA_ADAPTER_MODE` | No | No | Override for the MoI residency adapter. |
| `GULA_ADAPTER_MODE_CLOUDFLARE` | inherits `GULA_ADAPTER_MODE` | No | No | Override for the Cloudflare control plane adapter. |
| `MOI_NID_API_URL` | `""` | No | No | Ministry of Interior National ID API endpoint (live mode only). |
| `MOI_NID_API_KEY` | `""` | No | Yes | MoI National ID API authentication key. |
| `INSURANCE_API_URL` | `""` | No | No | National Health Insurance API endpoint. |
| `INSURANCE_API_KEY` | `""` | No | Yes | Insurance API authentication key. |
| `RESIDENCY_API_URL` | `""` | No | No | Ministry of Interior Residency API endpoint. |
| `RESIDENCY_API_KEY` | `""` | No | Yes | Residency API authentication key. |

### 2.17 Cloudflare

| Variable | Default | Required | Secret | Description |
|----------|---------|----------|--------|-------------|
| `CF_API_TOKEN` | `""` | No | Yes | Cloudflare API token for control plane operations. |
| `CF_ACCOUNT_ID` | `""` | No | No | Cloudflare account ID. |
| `CF_ZONE_ID` | `""` | No | No | Cloudflare zone ID for DNS/SSL management. |
| `CF_R2_BUCKET` | `gula-reports` | No | No | Cloudflare R2 bucket name for report storage. |

### 2.18 Supabase

Supabase integration is optional and informational only — the primary `DATABASE_URL` is still authoritative for runtime connections.

| Variable | Default | Required | Secret | Description |
|----------|---------|----------|--------|-------------|
| `SUPABASE_URL` | `""` | No | No | Supabase project URL for health/diagnostic scripts. |
| `SUPABASE_ANON_KEY` | `""` | No | Yes | Supabase anonymous/public key. |
| `SUPABASE_SERVICE_KEY` | `""` | No | Yes | Supabase service role key (full access). |

### 2.19 Kernel Runtime

All Kernel flags default to `true` so the Kernel is fully active out of the box.

| Variable | Default | Required | Secret | Description |
|----------|---------|----------|--------|-------------|
| `KERNEL_KILL_SWITCH` | `false` | No | No | Emergency stop: blocks all autonomous kernel actions. |
| `KERNEL_DEGRADED` | `false` | No | No | Puts kernel into degraded mode — no plugin or module loading. |
| `KERNEL_ENABLE_PLUGINS` | `true` | No | No | Enable the plugin system. |
| `KERNEL_ENABLE_EVENT_BUS` | `true` | No | No | Enable the internal event bus. |
| `KERNEL_ENABLE_BACKGROUND` | `true` | No | No | Enable background task processing in the kernel. |
| `KERNEL_ENABLE_FEATURES` | `true` | No | No | Enable feature flag management subsystem. |
| `KERNEL_ENABLE_CONFIG` | `true` | No | No | Enable configuration engine subsystem. |
| `KERNEL_ENABLE_TENANT` | `true` | No | No | Enable multi-tenant engine subsystem. |
| `KERNEL_ENABLE_GATEWAY` | `true` | No | No | Enable internal API gateway subsystem. |
| `KERNEL_NAME` | `gula-kernel` | No | No | Kernel instance name for identification. |
| `KERNEL_DEBUG` | `false` | No | No | Enable kernel debug mode (verbose logging). |
| `KERNEL_BOOT_TIMEOUT` | `30` | No | No | Kernel boot timeout in seconds. |
| `KERNEL_SHUTDOWN_TIMEOUT` | `30` | No | No | Kernel shutdown timeout in seconds. |
| `KERNEL_DATA_DIR` | `/var/lib/gula/kernel` | No | No | Kernel runtime data directory. |
| `KERNEL_PLUGIN_DIR` | `/var/lib/gula/plugins` | No | No | Kernel plugin installation directory. |
| `KERNEL_MODULE_DIR` | `/var/lib/gula/modules` | No | No | Kernel module installation directory. |

### 2.20 Edge Platform

| Variable | Default | Required | Secret | Description |
|----------|---------|----------|--------|-------------|
| `EDGE_ENABLED` | `true` | No | No | Master enable for the edge AI platform. When false, `/edge/*` endpoints respond 503. |
| `EDGE_KILL_SWITCH` | `false` | No | No | Global emergency kill switch for edge fleet. Overrides per-tenant policies. |
| `EDGE_HEARTBEAT_TIMEOUT_S` | `180` | No | No | Maximum seconds between agent heartbeats before marking device offline. |
| `EDGE_TELEMETRY_RETENTION_DAYS` | `14` | No | No | Edge telemetry data retention period in days. |
| `EDGE_DISPATCH_GRACE_S` | `30` | No | No | Grace period (seconds) added to task timeout before reaper requeues/fails stuck tasks. |
| `EDGE_TRUST_INITIAL` | `50.0` | No | No | Initial trust score for new edge agents. |
| `EDGE_TRUST_QUARANTINE_BELOW` | `20.0` | No | No | Trust score below which an agent is quarantined. |
| `EDGE_TASK_SIGNING_KEY` | `""` (falls back to `SECRET_KEY`) | No | Yes | HMAC key for signing tasks dispatched to edge agents. |
| `EDGE_TASK_SIGNING_KEY_PREV` | `""` | No | Yes | Previous signing key for key rotation. |

### 2.21 Monitoring & Alerting

| Variable | Default | Required | Secret | Description |
|----------|---------|----------|--------|-------------|
| `ALERT_WEBHOOK_URL` | `""` | No | Yes | Webhook URL for health alert notifications (Telegram, Discord, Slack). POST on grade transitions. |
| `HEALTH_ALERT_INTERVAL_SECONDS` | `60` | No | No | Interval (seconds) between health check evaluations. |
| `SENTRY_DSN` | `""` | No | Yes | Sentry error tracking DSN. Leave empty to disable. |
| `SENTRY_TRACES_RATE` | `0.05` | No | No | Sentry performance trace sample rate (0.05 = 5% of requests). |
| `ENVIRONMENT` | `production` | No | No | Environment tag for Sentry. |
| `GRAFANA_PASSWORD` | `changeme_grafana` | No | Yes | Grafana admin password (monitoring profile). |

### 2.22 Self-Audit

| Variable | Default | Required | Secret | Description |
|----------|---------|----------|--------|-------------|
| `GULA_AUTO_FIX` | `false` | No | No | Allow the self-audit agent to auto-apply safe fixes (only respected when `ENV=development`). |
| `ANTHROPIC_API_KEY` | `""` | No | Yes | Claude API key for the self-audit agent. |
| `GULA_AUDIT_MODEL` | `claude-sonnet-4-6` | No | No | Claude model name used by the self-audit agent. |

### 2.23 Auto-Repair

| Variable | Default | Required | Secret | Description |
|----------|---------|----------|--------|-------------|
| `REPAIR_MEMORY_WARN_MB` | `600` | No | No | Memory usage threshold (MB) triggering warning-level auto-repair. |
| `REPAIR_MEMORY_CRITICAL_MB` | `900` | No | No | Memory usage threshold (MB) triggering critical auto-repair (GC, pool recycle). |
| `REPAIR_DB_LATENCY_WARN` | `300` | No | No | DB query latency threshold (ms) for warning. |
| `REPAIR_REDIS_LATENCY_WARN` | `50` | No | No | Redis command latency threshold (ms) for warning. |
| `REPAIR_QUEUE_WARN` | `50` | No | No | Background queue depth warning threshold. |
| `REPAIR_QUEUE_CRITICAL` | `200` | No | No | Background queue depth critical threshold. |
| `REPAIR_POLL_SECS` | `30` | No | No | Auto-repair engine poll interval in seconds. |

### 2.24 Control Layer & Kill Switch

| Variable | Default | Required | Secret | Description |
|----------|---------|----------|--------|-------------|
| `CONTROL_LAYER_ENABLED` | `true` | No | No | Enable the policy engine + decision guard + kill switch. |
| `KILL_SWITCH` | `false` | No | No | Kill switch to immediately halt all autonomous AI/repair actions. Can also be activated at runtime via `POST /admin/kill-switch/activate` or Redis `SET gula:kill_switch 1`. |

### 2.25 Metrics & Observability

| Variable | Default | Required | Secret | Description |
|----------|---------|----------|--------|-------------|
| `METRICS_BEARER_TOKEN` | `""` | No | Yes | Bearer token required for `GET /metrics/prom` in production. Leave empty to disable. |
| `MAX_CONCURRENT_REQUESTS` | `50` (config) / `200` (middleware default) | No | No | Per-worker in-flight request cap. Clinical writes (results, orders, samples, critical alerts) are exempt. |

### 2.26 Admin Bootstrap

| Variable | Default | Required | Secret | Description |
|----------|---------|----------|--------|-------------|
| `GULA_ADMIN_EMAIL` | `admin@gula-platform.org` | No | No | Email address for the initial admin account created during startup seeding. |
| `GULA_ADMIN_NAME` | `GULA Platform Admin` | No | No | Display name for the initial admin account. |
| `GULA_ADMIN_PASSWORD` | `""` | Yes (for bootstrap) | Yes | Plaintext password for the initial admin account. |
| `GULA_ADMIN_PASSWORD_HASH` | `""` | No | Yes | Pre-hashed password (takes priority over plaintext). |
| `MASTER_ADMIN_NID` | `""` | No | No | National ID for the master admin account during seeding. |

### 2.27 Device Bridge (LabLink-Core)

| Variable | Default | Required | Secret | Description |
|----------|---------|----------|--------|-------------|
| `LABLINK_API_KEY` | `""` | No | Yes | API key for the device bridge to authenticate incoming device data. |
| `LABLINK_MODE` | `hybrid` | No | No | Device bridge deployment mode: `local_only`, `hybrid`, or `cloud_only`. |
| `GULA_BACKEND_URL` | `""` | No | No | Backend URL used by the device bridge to forward results (set in docker-compose). |

### 2.28 Docker & Container Resources

| Variable | Default | Required | Secret | Description |
|----------|---------|----------|--------|-------------|
| `POSTGRES_PASSWORD` | `""` | Yes | Yes | PostgreSQL superuser password. |
| `REDIS_PASSWORD` | `""` | Yes | Yes | Redis password (used in `REDIS_URL` and `redis-cli` health checks). |
| `PG_SHARED_BUFFERS` | `512MB` | No | No | PostgreSQL shared_buffers configuration. |
| `PG_MEM_LIMIT` | `896m` | No | No | Docker memory limit for PostgreSQL container. |
| `PG_CPUS` | `1.0` | No | No | Docker CPU limit for PostgreSQL container. |
| `BACKEND_MEM_LIMIT` | `1536m` | No | No | Docker memory limit for backend container. |
| `BACKEND_CPUS` | `1.5` | No | No | Docker CPU limit for backend container. |
| `WORKER_MEM_LIMIT` | `512m` | No | No | Docker memory limit for worker container. |
| `WORKER_CPUS` | `0.5` | No | No | Docker CPU limit for worker container. |
| `WORKER_DB_POOL_SIZE` | `3` | No | No | Worker-specific DB connection pool size. |
| `WORKER_DB_MAX_OVERFLOW` | `5` | No | No | Worker-specific DB max overflow connections. |
| `WEB_CONCURRENCY` | `3` | No | No | Number of uvicorn worker processes. |
| `GULA_IMAGE_PREFIX` | `local` | No | No | Docker image repository prefix for CI/CD deployments. |
| `GULA_IMAGE_TAG` | `local` | No | No | Docker image tag for CI/CD deployments. |

### 2.29 Platform Info

| Variable | Default | Required | Secret | Description |
|----------|---------|----------|--------|-------------|
| `RENDER_SERVICE_ID` | `""` | No | No | Render.com service identifier (informational, set by platform). |
| `DIGITALOCEAN_APP_ID` | `""` | No | No | DigitalOcean App Platform identifier (informational, set by platform). |

### 2.30 National Integration Connectors

Phase 11 integration connectors. All optional — platform functions without them.

| Variable | Default | Required | Secret | Description |
|----------|---------|----------|--------|-------------|
| `PACS_SERVER_URL` | `""` | No | No | PACS (DICOM) server URL for medical imaging. |
| `PACS_AETITLE` | `GULA` | No | No | PACS Application Entity title. |
| `PACS_PEER_AETITLE` | `PACS_SERVER` | No | No | PACS peer AE title. |
| `LIS_ENDPOINT` | `""` | No | No | Laboratory Information System endpoint. |
| `LIS_API_KEY` | `""` | No | Yes | LIS API authentication key. |
| `RIS_ENDPOINT` | `""` | No | No | Radiology Information System endpoint. |
| `RIS_API_KEY` | `""` | No | Yes | RIS API authentication key. |
| `ERP_ENDPOINT` | `""` | No | No | Enterprise Resource Planning endpoint. |
| `ERP_API_KEY` | `""` | No | Yes | ERP API authentication key. |
| `PAYMENT_PROVIDER` | `zaincash` | No | No | Payment gateway provider name. |
| `PAYMENT_API_KEY` | `""` | No | Yes | Payment gateway API key. |
| `PAYMENT_MERCHANT_ID` | `""` | No | Yes | Payment gateway merchant ID. |
| `SMS_PROVIDER` | `""` | No | No | SMS service provider name. |
| `SMS_API_KEY` | `""` | No | Yes | SMS service API key. |
| `SMS_SENDER_ID` | `GULA` | No | No | SMS sender ID / originator. |
| `SIGNATURE_CERT_PATH` | `""` | No | No | Path to digital signature certificate. |
| `SIGNATURE_KEY_PATH` | `""` | No | No | Path to digital signature private key. |
| `SIGNATURE_CA_PATH` | `""` | No | No | Path to digital signature CA certificate. |
| `GIS_API_KEY` | `""` | No | Yes | Geographic Information System API key. |
| `GIS_BASE_URL` | `""` | No | No | GIS base URL. |
| `GOVERNMENT_GATEWAY_URL` | `""` | No | No | Government API gateway URL. |
| `GOVERNMENT_CLIENT_ID` | `""` | No | Yes | Government gateway OAuth client ID. |
| `GOVERNMENT_CLIENT_SECRET` | `""` | No | Yes | Government gateway OAuth client secret. |

### 2.31 Digital Twin Platform

| Variable | Default | Required | Secret | Description |
|----------|---------|----------|--------|-------------|
| `TWIN_SIMULATION_ENABLED` | `true` | No | No | Enable digital twin simulation engine. |
| `TWIN_MAX_HISTORY_DAYS` | `365` | No | No | Maximum days of historical data for twin simulation. |
| `TWIN_PREDICTION_HORIZON_DAYS` | `30` | No | No | Forecast horizon in days for twin predictions. |

### 2.32 Command Intelligence

| Variable | Default | Required | Secret | Description |
|----------|---------|----------|--------|-------------|
| `SITUATION_ROOM_REFRESH_SECONDS` | `60` | No | No | Situation room dashboard refresh interval in seconds. |
| `KPI_RETENTION_DAYS` | `365` | No | No | KPI data retention period in days. |
| `INCIDENT_AUTO_RESOLVE_HOURS` | `72` | No | No | Hours after which incidents auto-resolve if no activity. |

---

## 3. Weak Secret Detection

The platform checks for weak patterns in `SECRET_KEY`, `ENCRYPTION_KEY`, and `NID_HMAC_KEY` in production. If any of these patterns are detected, the process exits immediately with status code 1.

**Weak patterns (case-insensitive substring match):**

| Pattern | Pattern | Pattern | Pattern |
|---------|---------|---------|---------|
| `default` | `change` | `secret` | `example` |
| `test` | `demo` | `gula_default` | `changeme` |
| `password` | `12345` | `abcdef` | `admin` |
| `qwerty` | `letmein` | `welcome` | `pass` |
| `00000` | `11111` | | |

Detection is implemented in `config.py::_is_weak_secret()` and only runs when `ENV=production`.

---

## 4. Hard Fail Behaviours

In production (`ENV=production`), the following conditions cause `sys.exit(1)` with a clear error message:

| Condition | Variable(s) |
|-----------|-------------|
| Missing `DATABASE_URL` | `DATABASE_URL` |
| Missing `SECRET_KEY` | `SECRET_KEY` |
| Weak `SECRET_KEY` | `SECRET_KEY` |
| Missing `REFRESH_TOKEN_SECRET` | `REFRESH_TOKEN_SECRET` |
| Missing `ENCRYPTION_KEY` | `ENCRYPTION_KEY` |
| Weak `ENCRYPTION_KEY` | `ENCRYPTION_KEY` |
| Missing `NID_HMAC_KEY` | `NID_HMAC_KEY` |
| Missing `AUDIT_ANCHOR_KEY` | `AUDIT_ANCHOR_KEY` |
| Invalid `RUNTIME_MODE` | `RUNTIME_MODE` |

In development, missing secrets generate random fallback values (with warnings logged via `logger.warning()`).

---

## 5. Adapter Mode Resolution

External adapter modes resolve in priority order:

1. Per-adapter override (e.g. `GULA_ADAPTER_MODE_NID`)
2. Global default (`GULA_ADAPTER_MODE`, default: `stub`)
3. Fallback: `stub`

**Mode meanings:**
- `stub` — return fake/simulated data, never call external API
- `live` — call the real external API endpoint
- `shadow` — call the real API but return stub data (dual-write for testing)

---

## 6. Database Connection Pool Formula

Total DB connections must stay under PostgreSQL's `max_connections` (default 100):

```
WEB_CONCURRENCY × (DB_POOL_SIZE + DB_MAX_OVERFLOW) < max_connections
```

Defaults: `3 × (6 + 12) = 54` — fits inside the default 100.

Worker uses a separate smaller pool: `WORKER_DB_POOL_SIZE + WORKER_DB_MAX_OVERFLOW = 3 + 5 = 8`.

If you change any of these knobs, recalculate the budget.
