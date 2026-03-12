# =============================================================================
# GULA Platform - Operations Makefile
# =============================================================================

.PHONY: help up down restart ps logs pull-ai status health test audit k8s-dev k8s-prod

help:
	@echo "GULA Platform Commands:"
	@echo ""
	@echo "  Operations:"
	@echo "    make up          - Start all services"
	@echo "    make down        - Stop all services"
	@echo "    make restart     - Restart all services (rebuild)"
	@echo "    make ps          - Show service status"
	@echo "    make logs        - Follow all logs"
	@echo "    make status      - Full platform status"
	@echo ""
	@echo "  AI:"
	@echo "    make pull-ai     - Pull llama3 model to Ollama"
	@echo ""
	@echo "  Testing:"
	@echo "    make health      - Quick health check all services"
	@echo "    make audit       - Run full integration test suite"
	@echo "    make check-queues - Verify RabbitMQ queues"
	@echo ""
	@echo "  Maintenance:"
	@echo "    make backup      - Manual database backup"
	@echo "    make vault-init  - Initialize Vault secrets"
	@echo ""
	@echo "  Kubernetes (Order 21):"
	@echo "    make k8s-dev     - Apply K8s dev overlay"
	@echo "    make k8s-prod    - Apply K8s prod overlay"

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

# Initialize Vault with GULA secrets
vault-init:
	@echo "Initializing Vault with GULA secrets..."
	docker exec gula-vault vault login $(VAULT_TOKEN)
	docker exec gula-vault vault kv put secret/gula/database url="postgresql://postgres:gula_secure_2024@pgbouncer:5432/labdb"
	docker exec gula-vault vault kv put secret/gula/rabbitmq url="amqp://gula:gula_rabbit_2024@rabbitmq:5672/gula"
	docker exec gula-vault vault kv put secret/gula/minio access_key="gula_minio" secret_key="gula_minio_2024"
	@echo "Vault secrets initialized."
