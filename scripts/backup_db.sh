#!/bin/bash
# ============================================
# Lithium Bot - Database Backup Script
# Schedule with cron: 0 3 * * * /opt/lithium/scripts/backup_db.sh
# ============================================

set -e

BACKUP_DIR="/opt/lithium/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/lithium_db_$DATE.sql.gz"

# Create backup directory
mkdir -p $BACKUP_DIR

# Get database credentials from .env
source /opt/lithium/.env

echo "📦 Creating database backup..."

# Backup using docker exec
docker compose -f /opt/lithium/docker-compose.prod.yml exec -T postgres \
    pg_dump -U $POSTGRES_USER $POSTGRES_DB | gzip > $BACKUP_FILE

echo "✅ Backup created: $BACKUP_FILE"

# Keep only last 7 days of backups
find $BACKUP_DIR -name "lithium_db_*.sql.gz" -mtime +7 -delete

echo "🧹 Old backups cleaned up"

# Show backup info
ls -lh $BACKUP_FILE
