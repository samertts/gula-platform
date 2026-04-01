# GULA Platform — Claude Autonomous Operation Guide

This file instructs Claude Code (and the self-audit agent) how to operate autonomously on the GULA Platform.

## Core Principles

1. **Stability first** — never break working code to add features
2. **Data integrity above all** — no change may risk patient data loss
3. **Fix before feature** — bugs and security issues take priority over improvements
4. **Test then commit** — always run `python -m py_compile app/main.py` before committing

## Architecture Overview

- **Backend**: FastAPI (Python 3.11), SQLAlchemy ORM, Alembic migrations
- **Database**: PostgreSQL 16 (primary data store)
- **Cache**: Redis 7 (rate limiting, sessions, outbox idempotency)
- **Gateway**: nginx (rate limiting, TLS, static files)
- **Load balancer**: HAProxy (multi-instance mode)
- **Monitoring**: Prometheus + Grafana
- **CI**: GitHub Actions (syntax-gate → security-scan → build)

## Development Branch

All development goes to: `claude/merge-prepare-production-ih1XG`

## Autonomous Tasks Claude May Perform

### ALWAYS safe to do:
- Fix pyflakes/flake8 errors
- Add missing indexes to models
- Fix typos in log messages
- Add test cases for untested business logic
- Update `.env.example` with new variables

### Requires human approval:
- Changes to JWT/auth logic
- Changes to billing/subscription tier logic
- Database schema changes (new columns, removed columns)
- Changing API response shapes (breaks mobile clients)
- Modifying the CI pipeline

### NEVER do autonomously:
- Delete or truncate database tables
- Change `SECRET_KEY`, `ENCRYPTION_KEY`, or `NID_HMAC_KEY` defaults
- Push to `main` branch
- Remove audit log entries or reduce audit coverage
- Disable rate limiting or security headers

## Self-Audit Workflow

```bash
# Run one audit cycle
ANTHROPIC_API_KEY=... python3 scripts/self_audit_agent.py

# Run with auto-fix enabled
ANTHROPIC_API_KEY=... python3 scripts/self_audit_agent.py --fix

# Watch mode (audit every hour)
ANTHROPIC_API_KEY=... python3 scripts/self_audit_agent.py --watch 3600
```

## Self-Healing System

The platform heals itself via three layers:
1. **Circuit Breaker** (`app/core/self_healing.py`) — isolates failing dependencies
2. **Auto-Repair Engine** (`app/core/auto_repair.py`) — GC, pool recycle, reconnects
3. **Adaptive Concurrency** (`app/main.py`) — tightens request cap when DB is slow

## Horizontal Scaling

```bash
# Scale to 5 backend instances with HAProxy
docker compose -f docker-compose.yml -f docker-compose.scale.yml up -d --scale gula-backend=5

# Monitor load distribution
open http://localhost:8404/stats
```

## Testing

```bash
make lint            # pyflakes + flake8
make test            # all unit tests
make scenario-test   # real end-to-end scenario test
make integrity-test  # concurrent validation integrity test
make chaos           # chaos engineering tests
```

## Key Files

| File | Purpose |
|------|---------|
| `backend/app/main.py` | FastAPI app, middleware stack, startup |
| `backend/app/core/self_healing.py` | Circuit breaker, degraded mode |
| `backend/app/core/auto_repair.py` | Auto-repair engine |
| `backend/app/core/startup_guard.py` | Production startup validation |
| `backend/app/security/rbac.py` | 9 roles × 13 permissions |
| `backend/app/domain/order_state.py` | Lab order state machine |
| `backend/app/services/outbox_service.py` | Guaranteed event delivery |
| `scripts/self_audit_agent.py` | Claude-powered self-audit |
| `config/haproxy/haproxy.cfg` | Load balancer config |
| `config/prometheus/` | Metrics collection |
| `config/grafana/` | Dashboards |

## Security Invariants (never violate)

1. All patient data queries MUST filter by `lab_id = current_user.lab_id`
2. All mutations MUST be in the audit log
3. Phone lookups MUST use exact match (never LIKE with user input)
4. `/metrics/prom` MUST require Bearer token in production
5. `system_ready` MUST stay False until DB is confirmed reachable
6. Optimistic lock (`version` column) MUST be checked on all result mutations

## Migration Policy (MANDATORY — never violate)

Violating these rules causes `NoSuchTableError` on fresh deploys and silent
data drift between environments.

| Rule | Why |
|------|-----|
| **Never modify an existing migration** | Existing DBs have already run it; changing it creates divergence |
| **All schema changes = new revision only** | `alembic revision --autogenerate -m "describe_change"` |
| **`20250322_0000` is immutable** | It is the bootstrap snapshot; treat it like a DB backup |
| **Every migration must be idempotent** | Use `_has_column()`, `_table_exists()`, `_index_exists()` guards |
| **New columns must be nullable or have a server_default** | Non-nullable columns without defaults break existing rows |
| **Test every migration on a clean DB before PR** | Run `docker compose run --rm gula-backend alembic upgrade head` |

### Quick reference

```bash
# Create a new migration
cd backend && alembic revision --autogenerate -m "add_foo_column"

# Test it on a clean database (same as CI migration-gate)
docker compose down -v && docker compose up -d gula-postgres
docker compose run --rm gula-backend alembic upgrade head

# Downgrade one step (must not error)
docker compose run --rm gula-backend alembic downgrade -1
```
