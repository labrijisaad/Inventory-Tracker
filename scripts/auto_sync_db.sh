#!/bin/bash
# Auto-commit and push database to GitHub
# Run by cron every 6 hours on VM

set -e

REPO_DIR="/opt/midad"

cd "$REPO_DIR"

echo "🔄 Auto-sync starting at $(date)"

# Check if database exists
if [ ! -f "data/midad.db" ]; then
    echo "❌ Database not found: data/midad.db"
    exit 1
fi

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

# Commit and push
if git commit -m "db: auto-backup $TIMESTAMP"; then
    if git push origin test/saad_labri; then
        echo "✅ Database synced to GitHub: $TIMESTAMP"
    else
        echo "⚠️ Push failed - will retry next sync"
        git reset HEAD~1
        exit 1
    fi
else
    echo "⚠️ Nothing to commit"
fi