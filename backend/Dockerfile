FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
# Wheels are pre-downloaded to /tmp/wheels on the host and copied here
# so the build works in environments without outbound internet access.
COPY wheels/ /tmp/wheels/
RUN pip install --no-cache-dir --no-index --find-links=/tmp/wheels -r requirements.txt \
 && rm -rf /tmp/wheels

COPY app ./app
COPY migrations ./migrations
COPY alembic.ini .

# Exclude pycache from image
RUN find /app -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

RUN adduser --disabled-password --gecos "" appuser && chown -R appuser /app
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --start-period=30s --retries=5 \
    CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health', timeout=3)"

# 1. Create base tables (idempotent — skipped if already exist)
# 2. Run incremental migrations
# 3. Start server
CMD ["sh", "-c", "python3 -c 'from app.database import engine; from app.models import Base; Base.metadata.create_all(engine)' && alembic upgrade head && exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2 --no-access-log"]
