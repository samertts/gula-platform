# =============================================================================
# GULA Platform — Backend (multi-stage)
# Stage 1: install & compile deps  →  smaller, faster final image
# Stage 2: runtime only
# =============================================================================

# ── Stage 1: dependency builder ───────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /deps

COPY requirements.txt .

# Install into an isolated prefix so we can copy just the packages
# --compile: pre-generate .pyc so the runtime image has no .py → .pyc overhead
RUN pip install --no-cache-dir --compile --prefix=/install -r requirements.txt


# ── Stage 2: runtime image ────────────────────────────────────────────────────
FROM python:3.11-slim

WORKDIR /app

# Copy installed packages from builder (no build tools, no pip cache in final layer)
COPY --from=builder /install /usr/local

# Copy application source
COPY app ./app
COPY migrations ./migrations
COPY alembic.ini .

# Pre-compile application code to .pyc (faster cold start; skip errors silently)
RUN python -m compileall -q app/ 2>/dev/null || true

# Drop root: run as unprivileged user
RUN adduser --disabled-password --gecos "" appuser && chown -R appuser /app
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --start-period=30s --retries=5 \
    CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health', timeout=3)"

# Startup sequence:
#   1. create_all  — idempotent table creation (safe on fresh DB)
#   2. alembic     — incremental schema migrations
#   3. uvicorn     — application server (startup_guard validates config/DB/seeds)
#
# WEB_CONCURRENCY: number of uvicorn workers (default 4).
#   Total DB connections = WEB_CONCURRENCY × (DB_POOL_SIZE + DB_MAX_OVERFLOW)
#   Keep WEB_CONCURRENCY × 10 ≤ 100 (PG max_connections) → max 10 workers.
CMD ["sh", "-c", \
    "python3 -c 'from app.database import engine; from app.models import Base; Base.metadata.create_all(engine)' && \
     alembic upgrade head && \
     exec uvicorn app.main:app \
       --host 0.0.0.0 \
       --port 8000 \
       --workers ${WEB_CONCURRENCY:-4} \
       --no-access-log \
       --loop uvloop \
       --http httptools \
       --timeout-keep-alive 65 \
       --backlog 2048"]
