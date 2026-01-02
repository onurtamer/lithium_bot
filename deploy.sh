#!/bin/bash

# Lithium Bot Deployment Script
# This script handles the cleanup of old containers to prevent "ContainerConfig" errors
# common with older docker-compose versions.

echo "🚀 Starting Lithium Bot deployment..."

# 1. Stop existing containers
echo "🛑 Stopping services..."
sudo docker-compose -f docker-compose.prod.yml down --remove-orphans || true

# 2. Aggressive cleanup of 'lithium' containers
# This is critical for fixing the KeyError: 'ContainerConfig'
echo "🧹 Cleaning up old containers to prevent conflicts..."
sudo docker ps -a --filter "name=lithium" -q | xargs -r sudo docker rm -f || true

# 3. Pull latest changes
echo "⬇️ Ensuring code is up to date..."
git pull

# 4. Build and Start
echo "🏗️ Building and starting services..."
sudo docker-compose -f docker-compose.prod.yml up -d --build --force-recreate

# 5. Show Status
echo "✅ Deployment complete! Services status:"
sudo docker-compose -f docker-compose.prod.yml ps

echo "📝 To follow logs, run: sudo docker-compose -f docker-compose.prod.yml logs -f bot"
