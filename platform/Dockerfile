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

CMD ["python3", "-m", "platform.entry", "--workers", "2"]
