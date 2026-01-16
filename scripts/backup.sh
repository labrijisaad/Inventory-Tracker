#!/bin/bash
# Database backup script
# Will be run by cron daily

set -e

# Configuration
DB_PATH="/opt/midad/data/midad.db"
BACKUP_DIR="/opt/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="midad_backup_${TIMESTAMP}.db"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Check if database exists
if [ ! -f "$DB_PATH" ]; then
    echo "❌ Database not found at $DB_PATH"
    exit 1
fi

# Create local backup
echo "📦 Creating backup: $BACKUP_FILE"
cp "$DB_PATH" "$BACKUP_DIR/$BACKUP_FILE"

# Delete local backups older than 30 days
echo "🗑️ Cleaning old backups..."
find "$BACKUP_DIR" -name "midad_backup_*.db" -mtime +30 -delete

echo "✅ Backup complete!"
echo "📁 Local: $BACKUP_DIR/$BACKUP_FILE"