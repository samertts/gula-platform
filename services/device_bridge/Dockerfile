FROM python:3.14-slim

RUN addgroup --system app && adduser --system --ingroup app app

WORKDIR /app

COPY pyproject.toml .
RUN pip install --no-cache-dir "fastapi>=0.115.0" "uvicorn>=0.30.0" "pydantic>=2.8.0" "httpx>=0.27.0"

COPY --chown=app:app app/ ./app/

USER app

EXPOSE 8200

HEALTHCHECK --interval=30s --timeout=5s --retries=3 --start-period=10s \
  CMD python -c "import socket; s=socket.create_connection(('127.0.0.1', 8200), 2); s.close()"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8200"]
