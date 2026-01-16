#!/bin/bash

# 🔄 Auto-Sync Database AND Code to GitHub
# Runs automatically via cron every 6 hours
# Also commits any code changes on VM

set -e  # Exit on error

# Timestamp
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

echo "🔄 Auto-sync starting at $TIMESTAMP"
echo "📋 Current directory: $(pwd)"

# Change to repo directory
cd /opt/midad

# Check current branch
BRANCH=$(git rev-parse --abbrev-ref HEAD)
echo "📍 Branch: $BRANCH"

# Copy production database to git staging area
DB_PATH="/opt/midad/data/midad.db"
if [ -f "$DB_PATH" ]; then
    echo "📦 Database found, syncing..."
    # Database already in git location, no copy needed
else
    echo "⚠️  Warning: Database not found at $DB_PATH"
fi

# Stage ALL changes (database + any code changes)
git add -A

# Check if there are changes to commit
if git diff-index --quiet HEAD --; then
    echo "✅ No changes to sync"
    exit 0
fi

# Show what's being committed
echo "📋 Changes to commit:"
git status --short

# Commit changes
git commit -m "auto-sync: database + code backup $TIMESTAMP" || {
    echo "⚠️  Nothing to commit or commit failed"
    exit 0
}

# Pull latest (rebase to avoid merge commits)
echo "📥 Pulling latest from GitHub..."
git pull origin $BRANCH --rebase || {
    echo "⚠️  Warning: Pull failed, will try push anyway"
}

# Push to GitHub
echo "📤 Pushing to GitHub..."
if git push origin $BRANCH; then
    echo "✅ Database + code synced to GitHub: $TIMESTAMP"
else
    echo "❌ Push failed at $TIMESTAMP"
    exit 1
fi
