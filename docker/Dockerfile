FROM python:3.12-slim AS builder

WORKDIR /deps

COPY backend/requirements.txt .

RUN pip install --no-cache-dir --compile --prefix=/install -r requirements.txt

FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    fonts-dejavu-core \
    fonts-noto-core \
    && rm -rf /var/lib/apt/lists/*

RUN pip install dumb-init

COPY --from=builder /install /usr/local

COPY backend/app ./app
COPY backend/migrations ./migrations
COPY backend/alembic.ini .

RUN adduser --disabled-password --gecos "" appuser && chown -R appuser /app
USER appuser

EXPOSE 10000

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:10000/health', timeout=3)"

ENTRYPOINT ["dumb-init", "--"]

CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "app.main:app", \
     "--workers", "2", \
     "--timeout", "30", \
     "--bind", "0.0.0.0:10000", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
