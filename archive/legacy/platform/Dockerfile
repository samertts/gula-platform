FROM python:3.12-slim

RUN addgroup --system --gid 1001 appuser && \
    adduser --system --uid 1001 --gid 1001 appuser

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chown -R appuser:appuser /app

ENV PYTHONPATH=/app
ENV ENVIRONMENT=production

USER appuser

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python3 -c "import http.client; http.client.HTTPConnection('localhost', 8000).request('GET', '/health'); assert http.client.HTTPConnection('localhost', 8000).getresponse().status == 200" || exit 1

EXPOSE 8000

CMD ["python3", "-m", "platform.entry", "--workers", "2"]
