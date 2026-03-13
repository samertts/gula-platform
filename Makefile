# =============================================================================
# GULA Platform - Operations Makefile
# =============================================================================

.PHONY: help up down restart ps logs pull-ai status health test audit k8s-dev k8s-prod chaos load-test dr-verify dr-drill pg-test linkerd-install vault-status redis-status

help:
	@echo "GULA Platform - Enterprise Medical Laboratory System"
	@echo ""
	@echo "  Operations:"
	@echo "    make up            - Start all services"
	@echo "    make down          - Stop all services"
	@echo "    make restart       - Full rebuild and restart"
	@echo "    make ps            - Service status table"
	@echo "    make logs          - Follow all logs"
	@echo "    make status        - Full platform status"
	@echo ""
	@echo "  AI:"
	@echo "    make pull-ai       - Pull llama3 model to Ollama (run once)"
	@echo ""
	@echo "  Testing:"
	@echo "    make health        - Quick health check all services"
	@echo "    make audit         - Full integration test suite (10 checks)"
	@echo "    make chaos         - Chaos engineering tests"
	@echo "    make load-test     - k6 load test (10k req/min)"
	@echo "    make check-queues  - Verify RabbitMQ queues"
	@echo ""
	@echo "  Reliability:"
	@echo "    make pg-test       - PostgreSQL failover test"
	@echo "    make redis-status  - Redis Sentinel status"
	@echo "    make vault-status  - Vault seal/unseal status"
	@echo "    make dr-verify     - Verify latest backup is restorable"
	@echo "    make dr-drill      - Monthly disaster recovery drill"
	@echo ""
	@echo "  Maintenance:"
	@echo "    make backup        - Manual database backup"
	@echo "    make vault-init    - Initialize Vault secrets"
	@echo ""
	@echo "  Kubernetes (Order 21):"
	@echo "    make k8s-dev       - Apply K8s dev overlay"
	@echo "    make k8s-prod      - Apply K8s prod overlay (5-8 replicas)"
	@echo "    make linkerd-install - Install Linkerd service mesh"

# Executive Order 1: System restart and verification
up:
	docker compose up -d

down:
	docker compose down

restart:
	docker compose down
	docker compose up -d --build
	@echo "Waiting for services to start..."
	@sleep 10
	@make ps

ps:
	docker compose ps

logs:
	docker compose logs -f

# Executive Order 3: Pull local AI model
pull-ai:
	@echo "Pulling llama3 model to Ollama..."
	docker exec gula-ollama ollama pull llama3
	@echo "Verifying model..."
	curl -s http://localhost:11434/api/tags | python3 -m json.tool

# Executive Order 2: Verify RabbitMQ queues
check-queues:
	@echo "Checking RabbitMQ queues..."
	curl -s -u gula:gula_rabbit_2024 http://localhost:15672/api/queues/gula | python3 -c "import sys,json; queues=[q['name'] for q in json.load(sys.stdin)]; print('Queues:', queues); required={'orders.events','samples.events','results.events','alerts.events'}; missing=required-set(queues); print('Missing:',missing) if missing else print('All required queues present!')"

# Health check all services
health:
	@echo "=== GULA Platform Health Check ==="
	@echo "API Gateway:" && curl -sf http://localhost/health || echo "DOWN"
	@echo "Lab Service:" && curl -sf http://localhost:8001/health || echo "DOWN"
	@echo "Patient Service:" && curl -sf http://localhost:8002/health || echo "DOWN"
	@echo "Order Service:" && curl -sf http://localhost:8003/health || echo "DOWN"
	@echo "Result Service:" && curl -sf http://localhost:8004/health || echo "DOWN"
	@echo "Sample Service:" && curl -sf http://localhost:8005/health || echo "DOWN"
	@echo "AI Service:" && curl -sf http://localhost:9000/health || echo "DOWN"
	@echo "Ollama:" && curl -sf http://localhost:11434/api/tags || echo "DOWN"
	@echo "Autonomous Manager:" && curl -sf http://localhost:8010/status || echo "DOWN"

# Executive Order 20: Manual backup
backup:
	@echo "Creating database backup..."
	docker exec gula-postgres-primary pg_dump -U postgres labdb | gzip > backup_$(shell date +%Y%m%d_%H%M%S).sql.gz
	@echo "Backup complete."

status:
	@echo "=== GULA Platform Status ==="
	@docker compose ps
	@echo ""
	@echo "=== Autonomous Manager Status ==="
	@curl -sf http://localhost:8010/status | python3 -m json.tool || echo "Manager unavailable"

# Hardening Phase: Run full integration test suite
audit:
	@echo "=== GULA Platform Integration Tests ==="
	bash scripts/integration_test.sh

test: audit

# Kubernetes deployment (Executive Order 21)
k8s-dev:
	kubectl apply -k k8s/overlays/dev

k8s-prod:
	kubectl apply -k k8s/overlays/prod

# Chaos engineering tests
chaos:
	@echo "=== Chaos Engineering Tests ==="
	bash tests/chaos/chaos_test.sh

# Load testing with k6 (requires k6 installed: https://k6.io/docs/getting-started/installation/)
load-test:
	@echo "=== Load Test: 10k requests/min ==="
	k6 run tests/load/gula-load-test.js

# PostgreSQL failover test
pg-test:
	bash scripts/pg_failover.sh test

# PostgreSQL replication monitoring
pg-monitor:
	bash scripts/pg_failover.sh monitor

# Redis Sentinel status
redis-status:
	@echo "=== Redis HA Status ==="
	@echo "Primary:" && redis-cli -p 6379 ping || echo "DOWN"
	@echo "Replica:" && redis-cli -p 6380 ping || echo "DOWN"
	@echo "Sentinel:" && redis-cli -p 26379 ping || echo "DOWN"
	@echo ""
	@redis-cli -p 26379 sentinel masters 2>/dev/null || echo "Sentinel not reachable"

# Vault status
vault-status:
	@echo "=== Vault Status ==="
	@curl -sf http://localhost:8200/v1/sys/health | python3 -m json.tool || echo "Vault not reachable"

# Disaster Recovery
dr-verify:
	bash scripts/dr_recovery.sh verify

dr-drill:
	bash scripts/dr_recovery.sh drill

# Linkerd Service Mesh install (requires kubectl and linkerd CLI)
linkerd-install:
	@echo "Installing Linkerd service mesh..."
	curl -sL run.linkerd.io/install | sh
	linkerd install --crds | kubectl apply -f -
	linkerd install | kubectl apply -f -
	linkerd check
	kubectl apply -f k8s/base/mesh/linkerd.yaml
	@echo "Linkerd installed. Run: linkerd viz install | kubectl apply -f -"

# Initialize Vault with GULA secrets
vault-init:
	@echo "Initializing Vault with GULA secrets..."
	docker exec gula-vault vault login $(VAULT_TOKEN)
	docker exec gula-vault vault kv put secret/gula/database url="postgresql://postgres:gula_secure_2024@pgbouncer:5432/labdb"
	docker exec gula-vault vault kv put secret/gula/rabbitmq url="amqp://gula:gula_rabbit_2024@rabbitmq:5672/gula"
	docker exec gula-vault vault kv put secret/gula/minio access_key="gula_minio" secret_key="gula_minio_2024"
	@echo "Vault secrets initialized."
