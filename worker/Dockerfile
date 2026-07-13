FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Overridden per docker-compose service: `worker` runs the Celery consumer,
# `ingestion-webhook` runs the FastAPI producer (uvicorn webhook:app).
CMD ["celery", "-A", "celery_app", "worker", "--loglevel=info"]
