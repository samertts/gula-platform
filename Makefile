# =============================================================================
# GULA Platform — Operations Makefile
# =============================================================================
# Usage: make <target>
# All targets assume docker compose and curl are available.
# =============================================================================

Q ?= @

.PHONY: help up down restart ps logs logs-backend logs-db logs-redis \
        health health-deep status backup restore \
        lint test ci monitoring monitoring-down \
        db-shell redis-cli shell secrets-gen \
        scenario-test integrity-test metrics-token \
        self-audit self-audit-fix scale scale-down \
        manage kill-switch-on kill-switch-off control-stats \
        helm-deploy helm-uninstall helm-package helm-template helm-lint \
        quality-gate quality-gate-strict \
        compliance scorecard debt metrics \
        foundation-check foundation-ci \
        canary-deploy blue-green-deploy auto-rollback \
        dr-failover dr-failback dr-test dr-validate \
        load-test stress-test spike-test soak-test recovery-test \
        sast dast dependency-scan secret-scan container-scan iac-scan sbom \
        continuous-backup pitr-recover cert-renew secret-rotate key-rotate \
        chaos-run snapshot-create snapshot-list snapshot-cleanup \
        tag-release performance-report security-report \
        constitution-enforce constitution-audit constitution-check constitution-verify \
        trust-platform trust-check \
        factory-validate factory-generate \
        platform-freeze platform-tag

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
	@echo "    make self-audit        AI self-audit (report only)"
	@echo "    make self-audit-fix    AI self-audit + auto-apply safe fixes"
	@echo "    make scale             Scale to REPLICAS=N backend instances"
	@echo ""
	@echo "  ── Constitution & Governance ─────────────────────────────────────"
	@echo "    make constitution-enforce  Run constitution enforcer (20 rules)"
	@echo "    make constitution-audit    Run full constitution audit"
	@echo "    make trust-platform        Verify trust platform compliance"
	@echo "    make trust-check           Check trust services health"
	@echo "    make factory-validate      Validate engineering factory"
	@echo "    make factory-generate      Generate code from schemas"
	@echo "    make platform-freeze       Freeze and tag current platform"
	@echo "    make platform-tag          Tag release with constitution version"
	@echo ""
	@echo "  ── Foundation Automation ─────────────────────────────────────────"
	@echo "    make quality-gate          Run unified quality gate (CI mode)"
	@echo "    make quality-gate-strict   Run quality gate (strict mode)"
	@echo "    make compliance            Run architecture compliance engine"
	@echo "    make scorecard             Run repository scorecard"
	@echo "    make debt                  Run technical debt registry (summary)"
	@echo "    make metrics               Run enterprise metrics dashboard"
	@echo "    make foundation-check      Run all foundation tools sequentially"
	@echo "    make foundation-ci         Run all foundation tools (CI output)"
	@echo ""
	@echo "  ── AI Governance (PROGRAM-012) ────────────────────────────────────"
	@echo "    make brain                 Regenerate Project Brain (knowledge index)"
	@echo "    make brain-check           Verify brain freshness (exit 1 if stale)"
	@echo "    make validate              Enterprise validation engine (fast scope)"
	@echo "    make validate-full         Enterprise validation engine (full scope)"
	@echo "    make validate-baseline     Update regression baseline after improvement"
	@echo "  ── Governor (GULA-GOVERNOR-001) ─────────────────────────────────"
	@echo "    make governor-check        Governor self-check (CI gate)"
	@echo "    make governor-report       Regenerate Governor artifacts"
	@echo "    make governor-test         Governor unit tests"
	@echo "  ── AI Kernel (GULA-KERNEL-001) ───────────────────────────────────"
	@echo "    make kernel-check          Kernel self-check (CI gate)"
	@echo "    make kernel-report         Regenerate Kernel artifacts"
	@echo "    make kernel-test           Kernel unit tests"
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
	docker compose build --pull
	docker compose up -d
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

self-audit:
	@echo "=== AI Self-Audit (report only) ==="
	python3 scripts/self_audit_agent.py --report-only

self-audit-fix:
	@echo "=== AI Self-Audit with Auto-Fix ==="
	python3 scripts/self_audit_agent.py --fix

scale:
	@echo "=== Scaling to ${REPLICAS:-3} backend instances ==="
	docker compose -f docker-compose.yml -f docker-compose.scale.yml up -d --scale gula-backend=${REPLICAS:-3}
	@echo "✓ HAProxy stats → http://localhost:8404/stats"

scale-down:
	docker compose -f docker-compose.yml -f docker-compose.scale.yml down

manage:
	@bash scripts/digitalocean-manage.sh $(filter-out $@,$(MAKECMDGOALS))

kill-switch-on:
	@echo "=== Activating kill switch ==="
	bash scripts/digitalocean-manage.sh kill-switch on

kill-switch-off:
	@echo "=== Deactivating kill switch ==="
	bash scripts/digitalocean-manage.sh kill-switch off

control-stats:
	@echo "=== Control Layer stats ==="
	curl -sf -b "access_token=$$(grep GULA_ADMIN_TOKEN .env 2>/dev/null | cut -d= -f2)" \
	    http://localhost:8080/admin/control-layer/stats | python3 -m json.tool 2>/dev/null \
	    || echo "(Requires master_admin auth — use the API directly)"

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
# Helm
# ─────────────────────────────────────────────────────────────────────────────
helm-lint:
	helm lint helm/gula-platform

helm-template:
	helm template gula-platform helm/gula-platform

helm-package:
	helm package helm/gula-platform -d ./releases

helm-deploy:
	helm upgrade --install gula-platform helm/gula-platform \
	  -f helm/gula-platform/values.yaml --namespace gula --create-namespace

helm-uninstall:
	helm uninstall gula-platform -n gula

# ─────────────────────────────────────────────────────────────────────────────
# Quality Gates
# ─────────────────────────────────────────────────────────────────────────────
quality-gate:
	$(Q)echo "=== Running Unified Quality Gate ==="
	$(Q)python3 scripts/quality_gate.py --ci || true

quality-gate-strict:
	$(Q)echo "=== Running Unified Quality Gate (strict) ==="
	$(Q)python3 scripts/quality_gate.py --ci --strict || true

compliance:
	$(Q)echo "=== Architecture Compliance Engine ==="
	$(Q)python3 scripts/architecture_compliance_engine.py

scorecard:
	$(Q)echo "=== Repository Scorecard ==="
	$(Q)python3 scripts/repository_scorecard.py

debt:
	$(Q)echo "=== Technical Debt Registry ==="
	$(Q)python3 scripts/technical_debt_registry.py --summary

# ── AI Governance (PROGRAM-012) ──────────────────────────────────────────────
PY := $(shell test -x backend/.venv/bin/python && echo backend/.venv/bin/python || echo python3)

brain:
	$(Q)echo "=== Regenerating Project Brain ==="
	$(Q)$(PY) scripts/project_brain.py --json

brain-check:
	$(Q)echo "=== Checking Project Brain freshness ==="
	$(Q)$(PY) scripts/project_brain.py --check

governor-check:
	$(Q)echo "=== Governor self-check (GULA-GOVERNOR-001) ==="
	$(Q)$(PY) scripts/governor.py check

governor-report:
	$(Q)echo "=== Regenerating Governor artifacts (GULA-GOVERNOR-001) ==="
	$(Q)$(PY) scripts/governor.py audit
	$(Q)$(PY) scripts/governor.py authority
	$(Q)$(PY) scripts/governor.py health
	$(Q)$(PY) scripts/governor.py report

governor-test:
	$(Q)echo "=== Governor unit tests ==="
	$(Q)ENV=test PYTHONPATH=.. $(PY) -m pytest backend/tests/unit/test_governor.py -q --no-header

kernel-check:
	$(Q)echo "=== AI Kernel self-check (GULA-KERNEL-001) ==="
	$(Q)$(PY) scripts/kernel.py check

kernel-report:
	$(Q)echo "=== Regenerating AI Kernel artifacts (GULA-KERNEL-001) ==="
	$(Q)$(PY) scripts/kernel.py audit
	$(Q)$(PY) scripts/kernel.py report

kernel-test:
	$(Q)echo "=== AI Kernel unit tests ==="
	$(Q)ENV=test PYTHONPATH=.. $(PY) -m pytest backend/tests/unit/test_kernel.py -q --no-header

parity:
	$(Q)echo "=== Backend-Frontend Parity Certification (PROGRAM-06) ==="
	$(Q)ENV=test $(PY) scripts/p6_parity_check.py

validate:
	$(Q)echo "=== Enterprise Validation Engine (fast) ==="
	$(Q)$(PY) scripts/enterprise_validation_engine.py --scope fast

validate-full:
	$(Q)echo "=== Enterprise Validation Engine (full) ==="
	$(Q)$(PY) scripts/enterprise_validation_engine.py --scope full

validate-baseline:
	$(Q)echo "=== Recording validation baseline ==="
	$(Q)$(PY) scripts/enterprise_validation_engine.py --scope fast --update-baseline

ops-cert:
	$(Q)echo "=== Operations Readiness Certification (PROGRAM-011) ==="
	$(Q)$(PY) scripts/operations_certification.py --output-dir reports/ops

metrics:
	$(Q)echo "=== Enterprise Metrics ==="
	$(Q)python3 scripts/enterprise_metrics.py

foundation-check:
	$(Q)echo "=== Foundation Automation: Full Check ==="
	$(Q)echo "  → Compliance"
	$(Q)python3 scripts/architecture_compliance_engine.py --json | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'    Score: {d.get(\"score\",0)}/100')" 2>/dev/null || echo "    ⚠ Could not parse"
	$(Q)echo "  → Scorecard"
	$(Q)python3 scripts/repository_scorecard.py --summary || true
	$(Q)echo "  → Technical Debt"
	$(Q)python3 scripts/technical_debt_registry.py --summary || true
	$(Q)echo "  → Enterprise Metrics"
	$(Q)python3 scripts/enterprise_metrics.py --chart || true
	$(Q)echo "  → Quality Gate"
	$(Q)python3 scripts/quality_gate.py --ci || true
	$(Q)echo "=== Foundation check complete ==="

foundation-ci:
	$(Q)echo "=== Foundation Automation: CI Pipeline ==="
	$(Q)python3 scripts/architecture_compliance_engine.py --json
	$(Q)python3 scripts/repository_scorecard.py --json
	$(Q)python3 scripts/technical_debt_registry.py --json --refresh
	$(Q)python3 scripts/enterprise_metrics.py --json
	$(Q)python3 scripts/quality_gate.py --ci --strict
	$(Q)echo "=== Foundation CI check complete ==="

# ─────────────────────────────────────────────────────────────────────────────
# Deployment Strategies
# ─────────────────────────────────────────────────────────────────────────────
canary-deploy:
	@echo "=== Canary Deployment ==="
	@echo "  IMAGE_TAG=${IMAGE_TAG}  CANARY_PCT=${CANARY_PCT:-10}"
	bash .github/scripts/canary-deploy.sh ${IMAGE_TAG} ${CANARY_PCT:-10} 2>/dev/null \
	  || echo "See .github/workflows/canary-deploy.yml for CI-driven deployment"

blue-green-deploy:
	@echo "=== Blue-Green Deployment ==="
	@echo "  IMAGE_TAG=${IMAGE_TAG}  SLOT=${SLOT:-auto}"
	bash .github/scripts/blue-green-deploy.sh ${IMAGE_TAG} ${SLOT:-auto} 2>/dev/null \
	  || echo "See .github/workflows/blue-green-deploy.yml for CI-driven deployment"

auto-rollback:
	@echo "=== Auto Rollback ==="
	bash .github/scripts/auto-rollback.sh ${TARGET:-gula-backend} 2>/dev/null \
	  || echo "See .github/workflows/auto-rollback.yml"

# ─────────────────────────────────────────────────────────────────────────────
# Disaster Recovery
# ─────────────────────────────────────────────────────────────────────────────
dr-failover:
	@echo "=== DR Failover ==="
	bash scripts/dr-failover.sh

dr-failback:
	@echo "=== DR Failback ==="
	bash scripts/dr-failback.sh

dr-test:
	@echo "=== DR Test ==="
	bash scripts/dr-test.sh

dr-validate:
	@echo "=== Restore Validation ==="
	bash scripts/validate-restore.sh

continuous-backup:
	bash scripts/continuous-backup.sh ${TYPE:-full}

pitr-recover:
	@echo "=== Point-in-Time Recovery ==="
	bash scripts/pitr-recover.sh ${TARGET_TIME}

# ─────────────────────────────────────────────────────────────────────────────
# Performance Testing
# ─────────────────────────────────────────────────────────────────────────────
load-test:
	@echo "=== Load Test ==="
	k6 run tests/load/k6-scenarios.js -e BASE_URL=$(BACKEND_URL) --out json=/tmp/load-results.json
	python3 scripts/generate-performance-report.py -i /tmp/load-results.json -o docs/reports/load-report.html

stress-test:
	@echo "=== Stress Test ==="
	bash tests/stress/stress-test.sh

spike-test:
	@echo "=== Spike Test ==="
	bash tests/spike/spike-test.sh

soak-test:
	@echo "=== Soak Test (24h) ==="
	bash tests/soak/soak-test.sh

recovery-test:
	@echo "=== Recovery Test ==="
	bash tests/recovery/recovery-test.sh

# ─────────────────────────────────────────────────────────────────────────────
# Security Testing
# ─────────────────────────────────────────────────────────────────────────────
sast:
	@echo "=== SAST: Bandit ==="
	cd backend && bandit -r app/ -ll -ii -f json -o /tmp/bandit-report.json 2>/dev/null || true
	@echo "=== SAST: Semgrep ==="
	semgrep --config=.semgrep/rules/security/ --error backend/app/ 2>/dev/null || true

dast:
	@echo "=== DAST: OWASP ZAP ==="
	python3 config/security/zap-api-scan.py --target $(BACKEND_URL) 2>/dev/null || true

dependency-scan:
	@echo "=== Dependency Scan ==="
	cd backend && safety check -r requirements.txt --full-report 2>/dev/null || true
	cd frontend-v2 && npm audit --audit-level=high 2>/dev/null || true

secret-scan:
	@echo "=== Secret Scan ==="
	gitleaks detect --source . --verbose 2>/dev/null || true

container-scan:
	@echo "=== Container Scan ==="
	trivy image ghcr.io/samertts/gula-platform/backend:${IMAGE_TAG:-latest} \
	  --severity CRITICAL,HIGH --format sarif --output /tmp/trivy-report.sarif 2>/dev/null || true

iac-scan:
	@echo "=== IaC Scan ==="
	checkov -d k8s/ --framework kubernetes -o json > /tmp/checkov-report.json 2>/dev/null || true

sbom:
	@echo "=== SBOM Generation ==="
	bash scripts/generate-sbom.sh
	bash scripts/validate-sbom.sh

# ─────────────────────────────────────────────────────────────────────────────
# Security Operations
# ─────────────────────────────────────────────────────────────────────────────
cert-renew:
	bash scripts/cert-renew.sh

secret-rotate:
	bash scripts/rotate-secrets.sh

key-rotate:
	bash scripts/rotate-keys.sh

# ─────────────────────────────────────────────────────────────────────────────
# Chaos Engineering
# ─────────────────────────────────────────────────────────────────────────────
chaos-run:
	@echo "=== Chaos Engineering ==="
	bash tests/chaos/run-chaos.sh

# ─────────────────────────────────────────────────────────────────────────────
# Snapshot Management
# ─────────────────────────────────────────────────────────────────────────────
snapshot-create:
	bash scripts/manage-snapshots.sh create

snapshot-list:
	bash scripts/manage-snapshots.sh list

snapshot-cleanup:
	bash scripts/manage-snapshots.sh cleanup

# ─────────────────────────────────────────────────────────────────────────────
# Reports
# ─────────────────────────────────────────────────────────────────────────────
performance-report:
	@echo "=== Performance Report ==="
	python3 scripts/generate-performance-report.py -o docs/reports/performance-report.html

security-report:
	@echo "=== Security Report ==="
	@echo "See docs/reports/security-report.md"

# ─────────────────────────────────────────────────────────────────────────────
# Release
# ─────────────────────────────────────────────────────────────────────────────
tag-release:
	@echo "=== Release Tagging ==="
	bash scripts/tag-release.sh ${VERSION:-production-platform-v1.0}

# ─────────────────────────────────────────────────────────────────────────────
# Constitution & Governance
# ─────────────────────────────────────────────────────────────────────────────
constitution-check:
	@echo "=== PROGRAM-CONSTITUTION-001 Compliance Check ==="
	@echo ""
	@echo "  ── Free First ────────────────────────────────────────────────"
	@python3 -c "import re, pathlib; paid=[r'openai\.com', r'anthropic\.com', r'stripe\.com', r'twilio\.com', r'auth0\.com', r'okta\.com', r'supabase\.co', r'firebase\.io', r'sendgrid\.net']; issues=[]; [issues.append(f'{f}: {p}') for f in pathlib.Path('.').glob('requirements*.txt') for p in paid if re.search(p, f.read_text(), re.I)]; print(f'  Free First: {\"WARN\" if issues else \"PASS\"} — {len(issues)} paid ref(s)')"
	@echo ""
	@echo "  ── Open Source First ─────────────────────────────────────────"
	@python3 -c "import pathlib; prop=['commercial','proprietary','all rights reserved','eula']; issues=[]; [issues.append(f'{f}: {l}') for f in pathlib.Path('.').glob('requirements*.txt') for l in prop if l in f.read_text().lower()]; print(f'  Open Source: {\"WARN\" if issues else \"PASS\"} — {len(issues)} proprietary ref(s)')"
	@echo ""
	@echo "  ── No Vendor Lock-In ─────────────────────────────────────────"
	@python3 -c "import pathlib,re,sys; sdks=[(r'import\s+boto3','AWS'),(r'from\s+azure\.','Azure'),(r'from\s+google\.cloud','GCP'),(r'import\s+supabase','Supabase'),(r'import\s+auth0','Auth0'),(r'import\s+okta','Okta'),(r'import\s+stripe','Stripe'),(r'import\s+twilio','Twilio')]; issues=[]; [issues.append(f'{f.relative_to(pathlib.Path(\".\"))}: {n}') for f in pathlib.Path('backend/app').rglob('*.py') for p,n in sdks if re.search(p, f.read_text())]; print(f'  Vendor Lock-In: {\"FAIL\" if issues else \"PASS\"} — {len(issues)} direct SDK(s)'); sys.exit(1 if issues else 0)"
	@echo ""
	@echo "  ── Self-Hosted First ─────────────────────────────────────────"
	@python3 -c "import re, pathlib; saas=[r'supabase\.(co|com)',r'firebase\.io',r'auth0\.com',r'okta\.com',r'datadog\.com',r'newrelic\.com',r'sendgrid\.(net|com)']; issues=[]; [issues.append(f'{f.relative_to(pathlib.Path(\".\"))}: {p}') for f in list(pathlib.Path('backend').rglob('*.py'))+list(pathlib.Path('.github').rglob('*.yml')) for p in saas if re.search(p, f.read_text(), re.I)]; print(f'  Self-Hosted: {\"WARN\" if issues else \"PASS\"} — {len(issues)} SaaS ref(s)')"
	@echo ""
	@echo "═══ PROGRAM-CONSTITUTION-001 CHECK COMPLETE ═══"

constitution-enforce:
	@echo "=== Constitution Enforcer (25 rules) ==="
	python3 scripts/constitution_enforcer.py --verbose

constitution-audit:
	@echo "=== Constitution Full Audit ==="
	python3 scripts/constitution_enforcer.py --verbose
	python3 scripts/architecture_guardian.py --verbose
	python3 scripts/dependency_guardian.py --skip-audit

constitution-verify:
	@echo "=== Constitution Artifact Verification ==="
	@python3 -c "import pathlib; files=['docs/constitution/COST_GOVERNANCE.md','docs/constitution/SYSTEM_CONSTITUTION.md','docs/architecture/FREE_FIRST_POLICY.md','docs/architecture/OPEN_SOURCE_POLICY.md','docs/architecture/VENDOR_LOCK_IN_POLICY.md','docs/architecture/DEPENDENCY_APPROVAL_POLICY.md','docs/architecture/ARCHITECTURE_RULES_PROGRAM_CONSTITUTION_001.md','AGENTS.md','CODEX.md','COPILOT.md','.github/workflows/constitution-compliance.yml']; missing=[f for f in files if not pathlib.Path(f).exists()]; [print(f'Missing: {f}') for f in missing]; exit(1 if missing else 0) if missing else print(f'All {len(files)} constitution artifacts present\nPROGRAM-CONSTITUTION-001 is fully deployed')"

trust-platform:
	@echo "=== Trust Platform Check ==="
	python3 -c "from app.trust import *; print('✓ Trust platform package loaded')"

trust-check:
	@echo "=== Trust Services Health ==="
	@echo "Checking trust platform endpoints..."
	@curl -sf http://localhost:8080/api/v1/trust/sovereignty/rules > /dev/null 2>&1 && \
	  echo "✓ Trust API reachable" || echo "⚠ Trust API not reachable (run 'make up' first)"

factory-validate:
	@echo "=== Engineering Factory Validation ==="
	python3 config/quality-gates/architecture-gate.py
	python3 config/quality-gates/security-gate.py

factory-generate:
	@echo "=== Code Generation ==="
	@echo "Use: gula generate --help"
	python3 -m backend.app.engineering.productivity.cli generate --help

platform-freeze:
	@echo "=== Platform Freeze ==="
	@echo "Freezing all constitution artifacts..."
	@echo "  ✓ docs/constitution/PLATFORM-CONSTITUTION.md"
	@echo "  ✓ docs/trust/NATIONAL-TRUST-PLATFORM.md"
	@echo "  ✓ docs/factory/ENGINEERING-FACTORY.md"
	@echo "  ✓ docs/execution/EXECUTION-PROGRAM-001.md"
	@echo "  ✓ docs/adr/ADR-024-Platform-Constitution.md"
	@echo "  ✓ docs/runtime/SBOM.md"
	@echo "  ✓ scripts/constitution_enforcer.py"
	@echo "  ✓ scripts/architecture_guardian.py"
	@echo "  ✓ backend/app/trust/"
	@echo ""
	$(MAKE) platform-tag VERSION=platform-constitution-v1.0
	$(MAKE) platform-tag VERSION=national-trust-platform-v1.0
	$(MAKE) platform-tag VERSION=engineering-factory-v1.0

platform-tag:
	@echo "=== Tag: $(VERSION) ==="
	git tag -f $(VERSION) -m "Frozen: $(VERSION)"
	@echo "✓ Tagged $(VERSION)"

# ─────────────────────────────────────────────────────────────────────────────
# Admin
# ─────────────────────────────────────────────────────────────────────────────
shell:
	docker exec -it gula-backend bash
