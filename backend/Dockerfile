FROM python:3.11-slim

WORKDIR /app

# Install system dependencies:
# - fonts-dejavu-core: Unicode font with Arabic glyph support for PDF reports
# - fonts-noto-core:   Noto Sans fonts including Arabic coverage
# Both are needed for bilingual Arabic/English PDF lab result reports
RUN apt-get update && apt-get install -y --no-install-recommends \
    fonts-dejavu-core \
    fonts-noto-core \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

# Exclude pycache from image
RUN find /app -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

# SECURITY: Run as non-root user
RUN adduser --disabled-password --gecos "" appuser && chown -R appuser /app
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --start-period=30s --retries=5 \
    CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health', timeout=3)"

# 2 workers for concurrency; nginx handles access logging
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2", "--no-access-log"]
