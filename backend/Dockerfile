# =============================================================================
# GULA Platform — Backend (multi-stage)
# Stage 1: install & compile deps  →  smaller, faster final image
# Stage 2: runtime only
# =============================================================================

# ── Stage 1: dependency builder ───────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /deps

COPY requirements.txt .

# Install into an isolated prefix so we can copy just the packages
# --compile: pre-generate .pyc so the runtime image has no .py → .pyc overhead
RUN pip install --no-cache-dir --compile --prefix=/install -r requirements.txt


# ── Stage 2: runtime image ────────────────────────────────────────────────────
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies for bilingual Arabic/English PDF reports
RUN apt-get update && apt-get install -y --no-install-recommends \
    fonts-dejavu-core \
    fonts-noto-core \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder (no build tools, no pip cache in final layer)
COPY --from=builder /install /usr/local

# Copy application source
COPY app ./app
COPY migrations ./migrations
COPY alembic.ini .

# Pre-compile application code to .pyc — FAIL BUILD on syntax error.
# This is the last line of defence: if a SyntaxError slips past CI,
# the Docker build itself will refuse to produce a runnable image.
RUN python -m compileall app/

# SECURITY: Drop root — run as unprivileged user
RUN adduser --disabled-password --gecos "" appuser && chown -R appuser /app
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --start-period=60s --retries=5 \
    CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health', timeout=3)"

# Startup: gunicorn with UvicornWorker.
#   Migrations (alembic upgrade head) run as a Render preDeployCommand — NOT here.
#   Total DB connections = 2 workers × (pool_size + max_overflow) = 2 × 15 = 30.
#   Keep well under Supabase free-tier limit (60 connections).
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "app.main:app", \
     "--workers", "2", \
     "--timeout", "30", \
     "--bind", "0.0.0.0:8000", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
