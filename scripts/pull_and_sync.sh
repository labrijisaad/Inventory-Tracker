#!/bin/bash
# Pull latest code + database from GitHub
# Then sync database to production location
# Usage: ./scripts/pull_and_sync.sh

set -e

REPO_DIR="/opt/midad"
DB_PATH="/opt/midad-data/midad.db"

cd "$REPO_DIR"

echo "📥 Pulling from GitHub..."

# Stash any local changes (shouldn't be any, but just in case)
git stash --quiet || true

# Pull latest (code + database)
if git pull origin main; then
    echo "✅ Code pulled successfully"
else
    echo "❌ Git pull failed!"
    exit 1
fi

# Copy database from repo to production location
if [ -f "data/midad.db" ]; then
    # Backup current production database (just in case)
    if [ -f "$DB_PATH" ]; then
        BACKUP_NAME="midad_before_sync_$(date +%Y%m%d_%H%M%S).db"
        cp "$DB_PATH" "/opt/midad-data/$BACKUP_NAME"
        echo "💾 Current database backed up to: $BACKUP_NAME"
        
        # Keep only last 5 pre-sync backups
        cd /opt/midad-data
        ls -t midad_before_sync_*.db 2>/dev/null | tail -n +6 | xargs -r rm
        cd "$REPO_DIR"
    fi
    
    # Copy new database
    cp data/midad.db "$DB_PATH"
    echo "✅ Database synced to: $DB_PATH"
    echo "📊 Database size: $(du -h $DB_PATH | cut -f1)"
else
    echo "⚠️ Warning: data/midad.db not found in repository"
fi

# Restart service if running
if systemctl is-active --quiet midad 2>/dev/null; then
    echo "🔄 Restarting application..."
    sudo systemctl restart midad
    
    # Wait and check status
    sleep 2
    if systemctl is-active --quiet midad; then
        echo "✅ Service restarted successfully"
    else
        echo "❌ Service failed to start! Check logs:"
        echo "   sudo journalctl -u midad -n 50"
        exit 1
    fi
else
    echo "ℹ️  Service not running (this is OK during initial setup)"
fi

echo "✅ Pull and sync complete!"