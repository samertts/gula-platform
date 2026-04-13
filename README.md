🚀 GULA Platform — Production Specification (Ultimate)

---

🎯 Objective

Deploy a production-grade backend system with:

- ≥ 99% availability
- Deterministic startup (no race conditions)
- Zero manual post-deploy steps
- Stateless architecture
- Strict failure isolation
- Controlled resource & concurrency usage

---

🧠 Architecture

Client / Frontend
↓
Render (FastAPI API — stateless)
↓
Supabase (PostgreSQL — single source of truth)

---

🧰 Technology Stack

- FastAPI (async API layer)
- PostgreSQL (Supabase)
- SQLAlchemy (pooled connections)
- Gunicorn + Uvicorn workers
- Docker (immutable runtime)
- Render (deployment)

---

⚙️ Environment Variables

Required (hard fail if missing)

DATABASE_URL=postgresql://user:pass@host:5432/postgres?sslmode=require
ENCRYPTION_KEY=44-character Fernet key
SECRET_KEY=32+ char random
REFRESH_TOKEN_SECRET=32+ char random
NID_HMAC_KEY=32+ char random

---

Optional (with enforced defaults)

AI_BUDGET_SECONDS=6
MAX_CONCURRENT_REQUESTS=50
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10
WEB_CONCURRENCY=2

---

🚀 Deployment

Platform: Render
Runtime: Docker
Port: 10000

---

🔥 Deterministic Startup (Strict)

alembic upgrade head && \
gunicorn -k uvicorn.workers.UvicornWorker app.main:app \
--workers ${WEB_CONCURRENCY:-2} \
--bind 0.0.0.0:10000 \
--timeout 45 \
--graceful-timeout 30 \
--max-requests 1000 \
--max-requests-jitter 100

---

🧪 Health & Readiness

GET /health
→ process alive only

GET /health/ready
→ DB connected + pool ready

---

🗄️ Database (Strict)

- Supabase only
- SSL required
- No localhost

---

Connection Pool (MANDATORY)

- pool_size ≤ 5
- max_overflow ≤ 10
- pool_timeout ≤ 30s
- pool_recycle ≤ 1800s
- pool_pre_ping=True

---

Startup Retry (Required)

- max retries: 5
- exponential backoff
- failure → NOT READY (no crash loop)

---

⚙️ Concurrency Control (CRITICAL)

System MUST enforce:

semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)

All DB / AI calls go through it

---

⏱️ Timeout Enforcement

All external calls MUST use:

asyncio.wait_for(..., timeout=AI_BUDGET_SECONDS)

---

🚦 Backpressure Strategy

If concurrency exceeded:

- reject request (429)
- do NOT queue infinitely

---

🧠 Request Lifecycle Control

Middleware MUST include:

- request_id generation
- latency tracking
- structured logging

---

📊 Logging (MANDATORY)

JSON logs including:

- request_id
- path
- method
- status
- latency_ms
- error_type

---

🔒 Security

- ENV only secrets
- no hardcoded credentials
- Fernet encryption
- SSL DB required

---

🔄 Failure Handling

DB failure

- retry on startup
- fail readiness

AI failure

- max retry = 1
- timeout enforced

overload

- reject requests
- prevent DB exhaustion

---

🧯 Graceful Shutdown

System MUST:

- handle SIGTERM
- complete in-flight requests
- close DB connections

---

📉 Memory Safety

Gunicorn MUST use:

- max-requests
- jitter

to prevent leaks

---

🚫 Non-Negotiable Rules

- ❌ No SQLite
- ❌ No localhost
- ❌ No Redis (MVP)
- ❌ No blocking I/O
- ❌ No background tasks in API
- ❌ No manual deploy steps

---

📊 Operational Guarantees

Valid ONLY if:

- no crash ≥ 60 min
- API latency < 2s
- AI latency < 6s
- no pool exhaustion
- no unhandled exceptions

---

❗ Critical Failures (Must NOT happen)

- DB exhaustion
- infinite retries
- hanging requests
- silent migration failure
- partial startup

---

🔄 Future Extensions

- Redis (rate limit + cache)
- background workers
- queue system
- horizontal scaling

---

📌 Status

Production-Ready (Hardened — Safe for real traffic)

---

🧠 Final Directive

System must behave as:

- Stateless
- Backpressure-aware
- Timeout-controlled
- Failure-isolated
- Horizontally scalable

---
