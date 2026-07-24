FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml .
RUN pip install --no-cache-dir "fastapi>=0.115.0" "uvicorn>=0.30.0" "pydantic>=2.8.0" "httpx>=0.27.0"

COPY app/ ./app/

EXPOSE 8200

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8200"]
