#!/bin/bash
# ============================================
# Lithium Bot - Service Start Script
# Run after initial deployment or after updates
# ============================================

set -e

cd /opt/lithium

echo "🚀 Starting Lithium Bot services..."

# Build and start containers
docker compose -f docker-compose.prod.yml up -d --build

# Wait for services to be healthy
echo "⏳ Waiting for services to start..."
sleep 10

# Run database migrations
echo "📦 Running database migrations..."
docker compose exec -T api alembic upgrade head

# Show status
echo ""
echo "✅ Services started successfully!"
echo ""
docker compose ps

# Health check
echo ""
echo "🔍 Health check:"
curl -s https://lithiumbot.xyz/health || echo "⚠️ API not responding yet, wait a few seconds"
