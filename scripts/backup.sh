#!/bin/bash
# Database backup script
# Will be run by cron daily

set -e

# Configuration
DB_PATH="/opt/midad-data/midad.db"
BACKUP_DIR="/opt/backups"
GCS_BUCKET="gs://midad-backups-$(whoami)"  # Change this to your bucket name
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="midad_backup_${TIMESTAMP}.db"

# Create backup directory if not exists
mkdir -p "$BACKUP_DIR"

# Check if database exists
if [ ! -f "$DB_PATH" ]; then
    echo "❌ Database not found at $DB_PATH"
    exit 1
fi

# Create local backup
echo "📦 Creating backup: $BACKUP_FILE"
cp "$DB_PATH" "$BACKUP_DIR/$BACKUP_FILE"

# Upload to Google Cloud Storage (if gsutil available)
if command -v gsutil &> /dev/null; then
    echo "☁️ Uploading to GCS..."
    gsutil mb -l us-central1 "$GCS_BUCKET" 2>/dev/null || true
    gsutil cp "$BACKUP_DIR/$BACKUP_FILE" "$GCS_BUCKET/"
    echo "✅ Uploaded to $GCS_BUCKET/$BACKUP_FILE"
fi

# Delete local backups older than 30 days
echo "🗑️ Cleaning old local backups..."
find "$BACKUP_DIR" -name "midad_backup_*.db" -mtime +30 -delete

# Delete GCS backups older than 30 days (if gsutil available)
if command -v gsutil &> /dev/null; then
    echo "🗑️ Cleaning old GCS backups..."
    gsutil ls "$GCS_BUCKET/midad_backup_*.db" | while read file; do
        # Extract date from filename
        file_date=$(basename "$file" | grep -oP '\d{8}')
        if [ -n "$file_date" ]; then
            file_epoch=$(date -d "$file_date" +%s 2>/dev/null || echo 0)
            current_epoch=$(date +%s)
            age_days=$(( ($current_epoch - $file_epoch) / 86400 ))
            
            if [ $age_days -gt 30 ]; then
                echo "  Deleting old backup: $file"
                gsutil rm "$file"
            fi
        fi
    done
fi

echo "✅ Backup complete!"
echo "📁 Local: $BACKUP_DIR/$BACKUP_FILE"
echo "☁️ Cloud: $GCS_BUCKET/$BACKUP_FILE"