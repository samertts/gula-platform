FROM python:3.14-slim

RUN addgroup --system app && adduser --system --ingroup app app

WORKDIR /app

COPY pyproject.toml .
# pyserial is needed by app/connectors/base.py to open a serial analyzer.
# Its import there is function-local, so its absence broke the first serial
# connection rather than startup, and nothing caught it. IA-044.
RUN pip install --no-cache-dir "fastapi>=0.115.0" "uvicorn>=0.30.0" \
    "pydantic>=2.8.0" "httpx>=0.27.0" "pyserial>=3.5"

COPY --chown=app:app app/ ./app/

USER app

EXPOSE 8200

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8200"]
