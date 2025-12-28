FROM python:3.12-slim

WORKDIR /app

# Install build dependencies if needed
RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*

# Copy core library
COPY lithium_core /app/lithium_core

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install core in editable mode or just add to path
ENV PYTHONPATH=/app

# Copy application
COPY apps/bot /app/apps/bot

# Install curl for healthcheck
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

CMD ["python", "apps/bot/main.py"]
