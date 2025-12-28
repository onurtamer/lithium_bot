#!/bin/bash
set -e

echo "Running migrations..."
(cd lithium_core && alembic upgrade head)

echo "Running seed script..."
python scripts/seed.py

echo "Starting Lithium API..."
exec uvicorn apps.backend.main:app --host 0.0.0.0 --port 8000
