#!/bin/bash

# Lithium Bot Production Deployment Script
# Usage: ./deploy.sh

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}>>> Lithium Bot Deployment Started${NC}"

# Check for Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker is not installed. Please install Docker first.${NC}"
    exit 1
fi

# Check for .env file
if [ ! -f .env ]; then
    echo -e "${YELLOW}.env file not found. Creating from example...${NC}"
    if [ -f .env.example ]; then
        cp .env.example .env
        echo -e "${YELLOW}Please edit .env file with your production credentials and run this script again.${NC}"
        exit 1
    else
        echo -e "${RED}.env.example not found. Please create .env manually.${NC}"
        exit 1
    fi
fi

# 1. Force Sync with Git
# This ensures local files are EXACTLY the same as remote
if [ -d .git ]; then
    echo -e "${GREEN}>>> Fetching latest changes...${NC}"
    git fetch origin main
    
    echo -e "${GREEN}>>> Resetting to origin/main (Force Update)...${NC}"
    git reset --hard origin/main
    
    # Optional: Clean untracked files (Use with caution)
    # git clean -fd
else
    echo -e "${RED}Not a git repository. Skipping git pull.${NC}"
fi

# 2. Stop Existing Services
echo -e "${GREEN}>>> Stopping existing services...${NC}"
docker compose -f docker-compose.prod.yml down --remove-orphans

# 3. Prune Old Images (Optional but recommended to clear cache)
# echo -e "${GREEN}>>> Cleaning up old images...${NC}"
# docker image prune -f

# 4. Build and Start Services
# --build: Yeniden build almayı zorunlu kılar
# --force-recreate: Konteynerleri sıfırdan oluşturur
echo -e "${GREEN}>>> Building and starting services (Forced)...${NC}"
docker compose -f docker-compose.prod.yml up -d --build --force-recreate

# 5. Wait for Database
echo -e "${GREEN}>>> Waiting for database to initialize...${NC}"
sleep 10

# 6. Run Migrations
echo -e "${GREEN}>>> Running Database Migrations...${NC}"
# Using bot container to run migrations as it has alembic installed
docker compose -f docker-compose.prod.yml exec -T bot alembic upgrade head

# 7. Check status
echo -e "${GREEN}>>> Checking Service Status...${NC}"
docker compose -f docker-compose.prod.yml ps

echo -e "${GREEN}>>> Deployment Complete!${NC}"
# Extract domain from env if possible
DOMAIN=$(grep DOMAIN_NAME .env | cut -d '=' -f2)
echo -e "Web: https://${DOMAIN:-lithiumbot.xyz}"
echo -e "API: https://${DOMAIN:-lithiumbot.xyz}/api"
