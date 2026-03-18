FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

# Exclude pycache from image
RUN find /app -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

RUN adduser --disabled-password --gecos "" appuser && chown -R appuser /app
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --start-period=30s --retries=5 \
    CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health', timeout=3)"

# 2 workers for better concurrency; access log off (nginx handles logging)
CMD ["uvicorn","app.main:app","--host","0.0.0.0","--port","8000","--workers","2","--access-log","--no-access-log"]
