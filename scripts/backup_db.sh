#!/bin/bash
# Lithium Bot - Database Backup Script

# Load environment variables if needed
# source .env

BACKUP_DIR="./backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
FILENAME="lithium_db_$TIMESTAMP.sql"
RETENTION_DAYS=14

mkdir -p $BACKUP_DIR

echo "Starting database backup: $FILENAME"

# Using docker exec to dump from the postgres container
docker compose exec -t postgres pg_dumpall -U postgres > "$BACKUP_DIR/$FILENAME"

if [ $? -eq 0 ]; then
    echo "Backup successful: $BACKUP_DIR/$FILENAME"
    # Compress the backup
    gzip "$BACKUP_DIR/$FILENAME"
    
    # Remove old backups
    find $BACKUP_DIR -type f -name "*.gz" -mtime +$RETENTION_DAYS -delete
    echo "Old backups cleaned up (Retention: $RETENTION_DAYS days)."
else
    echo "Backup FAILED!"
    exit 1
fi
