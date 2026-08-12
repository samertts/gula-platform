# =============================================================================
# GULA Platform — Backend Production Dockerfile (Root Context)
# =============================================================================

FROM python:3.12-slim AS builder

WORKDIR /deps

COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --compile --prefix=/install -r requirements.txt


FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    fonts-dejavu-core \
    fonts-noto-core \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /install /usr/local

COPY backend ./backend
COPY backend/app ./app
COPY shared ./shared
COPY backend/migrations ./migrations
COPY backend/alembic.ini .
COPY backend/start_railway.sh /usr/local/bin/start_railway.sh

RUN chmod +x /usr/local/bin/start_railway.sh && python -m compileall app/ shared/ backend/

RUN adduser --disabled-password --gecos "" appuser && chown -R appuser /app
USER appuser

EXPOSE 10000

HEALTHCHECK --interval=15s --timeout=5s --start-period=60s --retries=5 \
    CMD-SHELL python3 -c "import os, urllib.request; urllib.request.urlopen('http://localhost:%s/health' % os.getenv('PORT', '10000'), timeout=3)"

ENTRYPOINT ["/usr/local/bin/start_railway.sh"]
