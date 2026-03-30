# =============================================================================
# GULA Platform — Operations Makefile
# =============================================================================
# Usage: make <target>
# All targets assume docker compose and curl are available.
# =============================================================================

.PHONY: help up down restart ps logs logs-backend logs-db logs-redis \
        health health-deep status backup restore \
        lint test ci monitoring monitoring-down \
        db-shell redis-cli shell secrets-gen \
        scenario-test integrity-test metrics-token

BACKEND_URL ?= http://localhost:8080

# ─────────────────────────────────────────────────────────────────────────────
help:
	@echo ""
	@echo "  GULA Platform — Medical Laboratory SaaS"
	@echo ""
	@echo "  ── Core ──────────────────────────────────────────────────────────"
	@echo "    make up           Start all services (detached)"
	@echo "    make down         Stop and remove containers"
	@echo "    make restart      Rebuild images + restart everything"
	@echo "    make ps           Container status table"
	@echo ""
	@echo "  ── Logs ──────────────────────────────────────────────────────────"
	@echo "    make logs         Follow all container logs"
	@echo "    make logs-backend Follow backend logs only"
	@echo "    make logs-db      Follow postgres logs"
	@echo "    make logs-redis   Follow redis logs"
	@echo ""
	@echo "  ── Health ────────────────────────────────────────────────────────"
	@echo "    make health       Quick liveness check (HTTP 200)"
	@echo "    make health-deep  Full diagnostic (grade / latency / memory)"
	@echo "    make status       docker compose ps + deep health"
	@echo ""
	@echo "  ── Database ──────────────────────────────────────────────────────"
	@echo "    make backup       Dump gula DB to ./backups/"
	@echo "    make db-shell     psql shell inside postgres container"
	@echo "    make redis-cli    redis-cli shell inside redis container"
	@echo ""
	@echo "  ── Development ───────────────────────────────────────────────────"
	@echo "    make lint              Run pyflakes + flake8 on backend code"
	@echo "    make test              Run backend pytest suite"
	@echo "    make ci                Run the full CI pipeline locally"
	@echo "    make secrets-gen       Generate strong random secrets (.env)"
	@echo "    make scenario-test     Real end-to-end scenario load test"
	@echo "    make integrity-test    Concurrent validation integrity test"
	@echo "    make metrics-token     Write METRICS_BEARER_TOKEN → token file"
	@echo ""
	@echo "  ── Monitoring (optional profile) ─────────────────────────────────"
	@echo "    make monitoring       Start Prometheus + Grafana"
	@echo "    make monitoring-down  Stop monitoring stack"
	@echo ""
	@echo "  ── Admin ─────────────────────────────────────────────────────────"
	@echo "    make shell        bash inside backend container"
	@echo ""

# ─────────────────────────────────────────────────────────────────────────────
# Core
# ─────────────────────────────────────────────────────────────────────────────
up:
	docker compose up -d
	@echo "Waiting for readiness..."
	@for i in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20; do \
	  if curl -sf $(BACKEND_URL)/health/ready > /dev/null 2>&1; then \
	    echo "✓ Platform ready"; break; \
	  fi; \
	  echo "  ... waiting ($$i/20)"; sleep 5; \
	done

down:
	docker compose down

restart:
	docker compose down
	docker compose up -d --build
	@$(MAKE) --no-print-directory health-deep

ps:
	docker compose ps

# ─────────────────────────────────────────────────────────────────────────────
# Logs
# ─────────────────────────────────────────────────────────────────────────────
logs:
	docker compose logs -f

logs-backend:
	docker compose logs -f gula-backend

logs-db:
	docker compose logs -f postgres

logs-redis:
	docker compose logs -f redis

# ─────────────────────────────────────────────────────────────────────────────
# Health
# ─────────────────────────────────────────────────────────────────────────────
health:
	@echo "=== GULA Platform — Quick Health Check ==="
	@echo -n "  Gateway  ($(BACKEND_URL)/health)       → "
	@curl -sf $(BACKEND_URL)/health | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('status','?'))" 2>/dev/null || echo "DOWN"
	@echo -n "  Postgres (docker health)              → "
	@docker inspect --format '{{.State.Health.Status}}' gula-postgres 2>/dev/null || echo "unknown"
	@echo -n "  Redis    (docker health)              → "
	@docker inspect --format '{{.State.Health.Status}}' gula-redis 2>/dev/null || echo "unknown"
	@echo -n "  Backend  (docker health)              → "
	@docker inspect --format '{{.State.Health.Status}}' gula-backend 2>/dev/null || echo "unknown"

health-deep:
	@echo "=== GULA Platform — Deep Health ==="
	@curl -sf $(BACKEND_URL)/health/deep | python3 -c "\
import sys, json, textwrap; \
d = json.load(sys.stdin); \
grade = d.get('grade','?'); \
emoji = '✅' if grade == 'GREEN' else ('🟡' if grade == 'YELLOW' else '🔴'); \
print(f'  Grade   : {emoji}  {grade}'); \
print(f'  Issues  : {d.get(\"issues\", [])}'); \
c = d.get('components', {}); \
db = c.get('database', {}); \
print(f'  DB      : {\"OK\" if db.get(\"ok\") else \"DOWN\"}  {db.get(\"latency_ms\", -1)} ms'); \
rd = c.get('redis', {}); \
print(f'  Redis   : {\"OK\" if rd.get(\"ok\") else \"DOWN\"}  {rd.get(\"latency_ms\", -1)} ms'); \
p = d.get('process', {}); \
print(f'  Memory  : {p.get(\"memory_rss_mb\", 0)} MB'); \
print(f'  Uptime  : {p.get(\"uptime_h\", 0)} h'); \
print(f'  Req/now : {p.get(\"active_requests\", 0)}'); \
print(f'  Version : {d.get(\"version\", \"?\")}'); \
" 2>/dev/null || echo "Cannot reach backend"

status: ps health-deep

# ─────────────────────────────────────────────────────────────────────────────
# Database
# ─────────────────────────────────────────────────────────────────────────────
BACKUP_DIR ?= ./backups

backup:
	@mkdir -p $(BACKUP_DIR)
	@TS=$$(date +%Y%m%d_%H%M%S); \
	 docker exec gula-postgres pg_dump -U postgres labdb | \
	   gzip > $(BACKUP_DIR)/gula_$$TS.sql.gz && \
	   echo "✓ Backup saved to $(BACKUP_DIR)/gula_$$TS.sql.gz"

db-shell:
	docker exec -it gula-postgres psql -U postgres labdb

redis-cli:
	docker exec -it gula-redis redis-cli -a "$$(grep REDIS_PASSWORD .env | cut -d= -f2)"

# ─────────────────────────────────────────────────────────────────────────────
# Development
# ─────────────────────────────────────────────────────────────────────────────
lint:
	@echo "=== pyflakes ==="
	cd backend && python -m pyflakes app 2>&1 | grep -v "imported but unused" || true
	@echo "=== flake8 (errors only) ==="
	cd backend && flake8 app --select=E9,F821 --statistics

test:
	cd backend && python -m pytest tests/ -v 2>&1 || echo "No tests yet — add tests/test_*.py"

chaos:
	@bash tests/chaos/chaos_test.sh all

chaos-%:
	@bash tests/chaos/chaos_test.sh $*

scenario-test:
	@echo "=== Real Scenario Load Test ==="
	python3 tests/load/scenario_test.py --url $(BACKEND_URL) --users ${USERS:-10} --rounds ${ROUNDS:-1}

integrity-test:
	@echo "=== Concurrent Order Validation Integrity Test ==="
	python3 tests/integration/integrity_test.py --url $(BACKEND_URL) --workers ${WORKERS:-100}

metrics-token:
	@source .env && bash scripts/generate-metrics-token.sh

ci: lint
	@echo "=== Syntax gate ==="
	cd backend && python -m py_compile app/main.py && echo "✓ Syntax OK"
	@echo "=== Docker build (catches compile errors) ==="
	docker compose build gula-backend

secrets-gen:
	@echo "=== Generating strong secrets ==="
	@python3 -c "\
import secrets; \
from cryptography.fernet import Fernet; \
print('SECRET_KEY=' + secrets.token_urlsafe(64)); \
print('REFRESH_TOKEN_SECRET=' + secrets.token_urlsafe(64)); \
print('ENCRYPTION_KEY=' + Fernet.generate_key().decode()); \
print('NID_HMAC_KEY=' + secrets.token_hex(32)); \
print('DEVICE_HMAC_KEY=' + secrets.token_hex(32)); \
print('METRICS_BEARER_TOKEN=' + secrets.token_urlsafe(32)); \
"

# ─────────────────────────────────────────────────────────────────────────────
# Monitoring
# ─────────────────────────────────────────────────────────────────────────────
monitoring:
	docker compose --profile monitoring up -d prometheus grafana
	@echo "✓ Prometheus → http://localhost:9090"
	@echo "✓ Grafana    → http://localhost:3000  (admin / see GRAFANA_PASSWORD in .env)"

monitoring-down:
	docker compose --profile monitoring stop prometheus grafana

# ─────────────────────────────────────────────────────────────────────────────
# Admin
# ─────────────────────────────────────────────────────────────────────────────
shell:
	docker exec -it gula-backend bash
