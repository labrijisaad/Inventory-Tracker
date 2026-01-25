#!/bin/bash

# 🔄 Smart Auto-Sync - Sync ENTIRE PROJECT (code + database + all files)
# Runs EVERY SECOND via cron (but only commits when ANYTHING changes!)
# Ultra-fast backup with zero spam

set -e

# Configuration
BRANCH="test/saad_labri"
LOG_FILE="/opt/midad/logs/auto-sync.log"

# Change to repo directory
cd /opt/midad 2>/dev/null || exit 0

# 🎯 SMART CHECK: Only proceed if ANYTHING changed in project
git diff --quiet HEAD && git diff --cached --quiet && exit 0

# Something changed! Log and sync
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# Ensure log directory exists
mkdir -p /opt/midad/logs

# Log to file (not stdout to avoid cron email spam)
{
    echo "[$TIMESTAMP] 📦 Project changed, syncing..."
    
    # Stage ALL changes (code + database + configs + everything!)
    git add -A
    
    # Show what's being committed
    echo "[$TIMESTAMP] 📋 Changes:"
    git status --short | head -10
    
    # Commit
    if git commit -m "auto-sync: full project backup $TIMESTAMP" 2>&1; then
        echo "[$TIMESTAMP] ✅ Committed"
    else
        echo "[$TIMESTAMP] ⚠️  Commit failed"
        exit 0
    fi
    
    # Skip pull (one-way sync VM → GitHub only)
    # Pull is not needed for auto-sync (we pull manually when deploying)
    echo "[$TIMESTAMP] ⏭️  Skipping pull (one-way sync)"
    
    # Push to GitHub
    if git push origin $BRANCH 2>&1; then
        echo "[$TIMESTAMP] ✅ Synced to GitHub successfully"
        echo "[$TIMESTAMP] 🎉 Auto-sync complete"
    else
        echo "[$TIMESTAMP] ❌ Push failed"
        exit 1
    fi
} >> "$LOG_FILE" 2>&1
