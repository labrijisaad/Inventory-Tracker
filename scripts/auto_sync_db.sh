#!/bin/bash

# 🔄 Smart Auto-Sync - Only commit if DATABASE changed
# Runs EVERY SECOND via cron (but only commits when data changes!)
# Ultra-fast backup with zero spam

set -e

# Configuration
DB_PATH="/opt/midad/data/midad.db"
BRANCH="test/saad_labri"
LOG_FILE="/opt/midad/logs/auto-sync.log"

# Change to repo directory
cd /opt/midad 2>/dev/null || exit 0

# Check if database exists
[ ! -f "$DB_PATH" ] && exit 0

# 🎯 SMART CHECK: Only proceed if database actually changed
git diff --quiet HEAD -- data/midad.db && exit 0

# Database changed! Log and sync
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
DB_SIZE=$(du -h "$DB_PATH" | cut -f1)

# Ensure log directory exists
mkdir -p /opt/midad/logs

# Log to file (not stdout to avoid cron email spam)
{
    echo "[$TIMESTAMP] 📊 Database changed, syncing... (Size: $DB_SIZE)"

    # Stage ONLY the database
    git add data/midad.db

    # Commit
    if git commit -m "db: auto-sync $TIMESTAMP" 2>&1; then
        echo "[$TIMESTAMP] ✅ Committed"
    else
        echo "[$TIMESTAMP] ⚠️  Commit failed"
        exit 0
    fi

    # Pull latest (rebase)
    if git pull origin $BRANCH --rebase 2>&1; then
        echo "[$TIMESTAMP] 📥 Pulled latest"
    else
        echo "[$TIMESTAMP] ⚠️  Pull failed, trying push anyway"
    fi

    # Push to GitHub
    if git push origin $BRANCH 2>&1; then
        echo "[$TIMESTAMP] ✅ Synced to GitHub successfully"
        echo "[$TIMESTAMP] 🎉 Auto-sync complete"
    else
        echo "[$TIMESTAMP] ❌ Push failed"
        exit 1
    fi
} >> "$LOG_FILE" 2>&1
