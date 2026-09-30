#!/bin/bash

# LLMSync Automated Backup Script
# Run this via cron: 0 2 * * * /path/to/backup.sh

set -e

BACKUP_DIR="${BACKUP_DIR:-/backups/llmsync}"
DATE=$(date +%Y%m%d_%H%M%S)
KEEP_DAYS=${KEEP_DAYS:-30}

# Create backup directory
mkdir -p "$BACKUP_DIR"

echo "=== LLMSync Backup Started: $DATE ==="

# Backup Postgres
echo "Backing up Postgres..."
docker exec llmsync-postgres pg_dump -U llmsync llmsync | gzip > \
  "$BACKUP_DIR/postgres_$DATE.sql.gz"

echo "✓ Postgres backup complete: postgres_$DATE.sql.gz"

# Backup MinIO (sync to backup location)
echo "Backing up MinIO..."
docker exec llmsync-minio sh -c "tar czf - /data" > \
  "$BACKUP_DIR/minio_$DATE.tar.gz"

echo "✓ MinIO backup complete: minio_$DATE.tar.gz"

# Backup Redis (optional - Redis is cache, not critical)
echo "Backing up Redis..."
docker exec llmsync-redis redis-cli SAVE
docker cp llmsync-redis:/data/dump.rdb "$BACKUP_DIR/redis_$DATE.rdb"

echo "✓ Redis backup complete: redis_$DATE.rdb"

# Backup environment and config
echo "Backing up configuration..."
cp .env "$BACKUP_DIR/env_$DATE.bak"
cp docker-compose.yml "$BACKUP_DIR/docker-compose_$DATE.yml"

echo "✓ Configuration backup complete"

# Clean up old backups
echo "Cleaning up backups older than $KEEP_DAYS days..."
find "$BACKUP_DIR" -name "postgres_*.sql.gz" -mtime +$KEEP_DAYS -delete
find "$BACKUP_DIR" -name "minio_*.tar.gz" -mtime +$KEEP_DAYS -delete
find "$BACKUP_DIR" -name "redis_*.rdb" -mtime +$KEEP_DAYS -delete
find "$BACKUP_DIR" -name "env_*.bak" -mtime +$KEEP_DAYS -delete
find "$BACKUP_DIR" -name "docker-compose_*.yml" -mtime +$KEEP_DAYS -delete

# Calculate sizes
TOTAL_SIZE=$(du -sh "$BACKUP_DIR" | cut -f1)

echo "=== LLMSync Backup Complete ==="
echo "Location: $BACKUP_DIR"
echo "Total size: $TOTAL_SIZE"
echo "Retention: $KEEP_DAYS days"

# Optional: Upload to S3/cloud storage
if [ -n "$AWS_S3_BUCKET" ]; then
    echo "Uploading to S3..."
    aws s3 sync "$BACKUP_DIR" "s3://$AWS_S3_BUCKET/llmsync-backups/" \
        --exclude "*" \
        --include "*_$DATE.*"
    echo "✓ Uploaded to S3"
fi
