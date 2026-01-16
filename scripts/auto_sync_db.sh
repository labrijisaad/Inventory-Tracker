#!/bin/bash
# Auto-commit and push database to GitHub
# Run by cron every 6 hours on VM

set -e

REPO_DIR="/opt/midad"
DB_PATH="/opt/midad-data/midad.db"

cd "$REPO_DIR"

echo "🔄 Auto-sync starting at $(date)"

# Check if database exists
if [ ! -f "$DB_PATH" ]; then
    echo "❌ Database not found: $DB_PATH"
    exit 1
fi

# Copy production database to repo data folder
mkdir -p data
cp "$DB_PATH" data/midad.db

echo "📊 Database size: $(du -h data/midad.db | cut -f1)"

# Check if there are changes
if git diff --quiet data/midad.db; then
    echo "✅ No changes in database - skipping commit"
    exit 0
fi

# Configure git (if not already done)
git config user.email "auto-sync@midad-books.local" || true
git config user.name "Auto Sync" || true

# Commit with timestamp
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
git add data/midad.db

# Check if we can commit (no conflicts)
if git commit -m "db: auto-backup $TIMESTAMP"; then
    # Push to GitHub
    if git push origin main; then
        echo "✅ Database synced to GitHub: $TIMESTAMP"
    else
        echo "⚠️ Push failed - will retry next sync"
        # Rollback commit to try again next time
        git reset HEAD~1
        exit 1
    fi
else
    echo "⚠️ Nothing to commit"
fi