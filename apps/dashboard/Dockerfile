FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy Core Library
COPY lithium_core /app/lithium_core

# Install Dependencies
COPY apps/dashboard/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy Project
COPY apps/dashboard /app/apps/dashboard

# Set Python Path
ENV PYTHONPATH=/app

# Install curl for healthcheck
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# Run gunicorn
CMD ["gunicorn", "apps.dashboard.core.wsgi:application", "--bind", "0.0.0.0:8001"]
