FROM python:3.14-slim

RUN addgroup --system app && adduser --system --ingroup app app

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=app:app . .

USER app

EXPOSE 8000

ENV PYTHONPATH=/app
ENV ENVIRONMENT=production

HEALTHCHECK --interval=30s --timeout=5s --retries=3 --start-period=10s \
  CMD python -c "import socket; s=socket.create_connection(('127.0.0.1', 8000), 2); s.close()"

CMD ["python3", "-m", "platform.entry", "--workers", "2"]
