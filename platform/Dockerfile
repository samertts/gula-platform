FROM python:3.14-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

ENV PYTHONPATH=/app
ENV ENVIRONMENT=production

CMD ["python3", "-m", "platform.entry", "--workers", "2"]
