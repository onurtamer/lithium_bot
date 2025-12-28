FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

COPY lithium_core /app/lithium_core
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

ENV PYTHONPATH=/app

COPY apps/api /app/apps/api
COPY alembic.ini /app/alembic.ini
COPY lithium_core /app/lithium_core

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["sh", "-c", "alembic upgrade head && python lithium_core/scripts/seed.py && uvicorn apps.api.main:app --host 0.0.0.0 --port 8000"]
