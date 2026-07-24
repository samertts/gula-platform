FROM python:3.12-slim

RUN addgroup --system --gid 1001 appuser && \
    adduser --system --uid 1001 --gid 1001 appuser

WORKDIR /app

COPY pyproject.toml .
RUN pip install --no-cache-dir "fastapi>=0.115.0" "uvicorn>=0.30.0" "pydantic>=2.8.0" "httpx>=0.27.0"

COPY app/ ./app/

RUN chown -R appuser:appuser /app

USER appuser

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python3 -c "import http.client; http.client.HTTPConnection('localhost', 8200).request('GET', '/health'); assert http.client.HTTPConnection('localhost', 8200).getresponse().status == 200" || exit 1

EXPOSE 8200

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8200"]
