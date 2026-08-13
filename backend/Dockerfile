# =============================================================================
# GULA Platform — Backend (multi-stage)
# Repository-root build context: this file lives in backend/Dockerfile.
# =============================================================================

# ── Stage 1: dependency builder ───────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /deps

COPY backend/requirements.txt ./requirements.txt

# Install into an isolated prefix so the runtime image contains only packages.
RUN pip install --no-cache-dir --compile --prefix=/install -r requirements.txt


# ── Stage 2: runtime image ────────────────────────────────────────────────────
FROM python:3.12-slim

WORKDIR /app

# System dependencies for bilingual Arabic/English PDF reports.
RUN apt-get update && apt-get install -y --no-install-recommends \
    fonts-dejavu-core \
    fonts-noto-core \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder.
COPY --from=builder /install /usr/local

# The application source is under backend/ while shared/ is a first-class
# runtime package used by logging, auth, and other backend modules.
COPY backend/app ./app
COPY backend/migrations ./migrations
COPY backend/alembic.ini .
COPY shared ./shared

# Shared modules refer to backend.app._compat for the UTC compatibility shim.
# Copy only that small compatibility module under the namespace expected by
# shared/; the running application itself continues to import app.*.
RUN mkdir -p /app/backend/app
COPY backend/app/_compat.py ./backend/app/_compat.py

# Fail the image build on syntax errors in application or shared code.
RUN python -m compileall app/ shared/ backend/app/_compat.py

# SECURITY: Drop root — run as unprivileged user.
RUN adduser --disabled-password --gecos "" appuser && chown -R appuser /app
USER appuser

EXPOSE 10000

HEALTHCHECK --interval=15s --timeout=5s --start-period=60s --retries=5 \
    CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:10000/health', timeout=3)"

# Railway will use its saved custom command when present. This fallback is also
# production-safe when the custom command is cleared: one worker, port 10000.
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "app.main:app", \
     "--workers", "1", \
     "--timeout", "30", \
     "--bind", "0.0.0.0:10000", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
