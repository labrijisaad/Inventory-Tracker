#!/bin/bash

# 🕐 Update cron to run auto-sync every second
# Run this ONCE after deploying new auto_sync_db.sh

echo "🕐 Updating cron to 1-second auto-sync..."

# Backup current crontab
crontab -l > /tmp/crontab_backup_$(date +%Y%m%d_%H%M%S).txt 2>/dev/null || true

# Create new crontab (remove old auto-sync, add new one)
(
    # Keep other cron jobs (backup, etc.)
    crontab -l 2>/dev/null | grep -v "auto_sync_db.sh" | grep -v "^#.*auto-sync" || true

    # Add 1-second auto-sync (runs every second!)
    echo "# Smart auto-sync: Only commit when database changes (every 1 second)"
    echo "* * * * * cd /opt/midad && /opt/midad/scripts/auto_sync_db.sh"
    echo "* * * * * sleep 1 && cd /opt/midad && /opt/midad/scripts/auto_sync_db.sh"
    echo "* * * * * sleep 2 && cd /opt/midad && /opt/midad/scripts/auto_sync_db.sh"
    echo "* * * * * sleep 3 && cd /opt/midad && /opt/midad/scripts/auto_sync_db.sh"
    echo "* * * * * sleep 4 && cd /opt/midad && /opt/midad/scripts/auto_sync_db.sh"
    echo "* * * * * sleep 5 && cd /opt/midad && /opt/midad/scripts/auto_sync_db.sh"
    echo "* * * * * sleep 6 && cd /opt/midad && /opt/midad/scripts/auto_sync_db.sh"
    echo "* * * * * sleep 7 && cd /opt/midad && /opt/midad/scripts/auto_sync_db.sh"
    echo "* * * * * sleep 8 && cd /opt/midad && /opt/midad/scripts/auto_sync_db.sh"
    echo "* * * * * sleep 9 && cd /opt/midad && /opt/midad/scripts/auto_sync_db.sh"
    echo "* * * * * sleep 10 && cd /opt/midad && /opt/midad/scripts/auto_sync_db.sh"
    echo "* * * * * sleep 11 && cd /opt/midad && /opt/midad/scripts/auto_sync_db.sh"
    echo "* * * * * sleep 12 && cd /opt/midad && /opt/midad/scripts/auto_sync_db.sh"
    echo "* * * * * sleep 13 && cd /opt/midad && /opt/midad/scripts/auto_sync_db.sh"
    echo "* * * * * sleep 14 && cd /opt/midad && /opt/midad/scripts/auto_sync_db.sh"
    echo "* * * * * sleep 15 && cd /opt/midad && /opt/midad/scripts/auto_sync_db.sh"
    echo "* * * * * sleep 16 && cd /opt/midad && /opt/midad/scripts/auto_sync_db.sh"
    echo "* * * * * sleep 17 && cd /opt/midad && /opt/midad/scripts/auto_sync_db.sh"
    echo "* * * * * sleep 18 && cd /opt/midad && /opt/midad/scripts/auto_sync_db.sh"
    echo "* * * * * sleep 19 && cd /opt/midad && /opt/midad/scripts/auto_sync_db.sh"
    echo "* * * * * sleep 20 && cd /opt/midad && /opt/midad/scripts/auto_sync_db.sh"
    echo "* * * * * sleep 21 && cd /opt/midad && /opt/midad/scripts/auto_sync_db.sh"
    echo "* * * * * sleep 22 && cd /opt/midad && /opt/midad/scripts/auto_sync_db.sh"
    echo "* * * * * sleep 23 && cd /opt/midad && /opt/midad/scripts/auto_sync_db.sh"
    echo "* * * * * sleep 24 && cd /opt/midad && /opt/midad/scripts/auto_sync_db.sh"
    echo "* * * * * sleep 25 && cd /opt/midad && /opt/midad/scripts/auto_sync_db.sh"
    echo "* * * * * sleep 26 && cd /opt/midad && /opt/midad/scripts/auto_sync_db.sh"
    echo "* * * * * sleep 27 && cd /opt/midad && /opt/midad/scripts/auto_sync_db.sh"
    echo "* * * * * sleep 28 && cd /opt/midad && /opt/midad/scripts/auto_sync_db.sh"
    echo "* * * * * sleep 29 && cd /opt/midad && /opt/midad/scripts/auto_sync_db.sh"
    echo "* * * * * sleep 30 && cd /opt/midad && /opt/midad/scripts/auto_sync_db.sh"
    echo "* * * * * sleep 31 && cd /opt/midad && /opt/midad/scripts/auto_sync_db.sh"
    echo "* * * * * sleep 32 && cd /opt/midad && /opt/midad/scripts/auto_sync_db.sh"
    echo "* * * * * sleep 33 && cd /opt/midad && /opt/midad/scripts/auto_sync_db.sh"
    echo "* * * * * sleep 34 && cd /opt/midad && /opt/midad/scripts/auto_sync_db.sh"
    echo "* * * * * sleep 35 && cd /opt/midad && /opt/midad/scripts/auto_sync_db.sh"
    echo "* * * * * sleep 36 && cd /opt/midad && /opt/midad/scripts/auto_sync_db.sh"
    echo "* * * * * sleep 37 && cd /opt/midad && /opt/midad/scripts/auto_sync_db.sh"
    echo "* * * * * sleep 38 && cd /opt/midad && /opt/midad/scripts/auto_sync_db.sh"
    echo "* * * * * sleep 39 && cd /opt/midad && /opt/midad/scripts/auto_sync_db.sh"
    echo "* * * * * sleep 40 && cd /opt/midad && /opt/midad/scripts/auto_sync_db.sh"
    echo "* * * * * sleep 41 && cd /opt/midad && /opt/midad/scripts/auto_sync_db.sh"
    echo "* * * * * sleep 42 && cd /opt/midad && /opt/midad/scripts/auto_sync_db.sh"
    echo "* * * * * sleep 43 && cd /opt/midad && /opt/midad/scripts/auto_sync_db.sh"
    echo "* * * * * sleep 44 && cd /opt/midad && /opt/midad/scripts/auto_sync_db.sh"
    echo "* * * * * sleep 45 && cd /opt/midad && /opt/midad/scripts/auto_sync_db.sh"
    echo "* * * * * sleep 46 && cd /opt/midad && /opt/midad/scripts/auto_sync_db.sh"
    echo "* * * * * sleep 47 && cd /opt/midad && /opt/midad/scripts/auto_sync_db.sh"
    echo "* * * * * sleep 48 && cd /opt/midad && /opt/midad/scripts/auto_sync_db.sh"
    echo "* * * * * sleep 49 && cd /opt/midad && /opt/midad/scripts/auto_sync_db.sh"
    echo "* * * * * sleep 50 && cd /opt/midad && /opt/midad/scripts/auto_sync_db.sh"
    echo "* * * * * sleep 51 && cd /opt/midad && /opt/midad/scripts/auto_sync_db.sh"
    echo "* * * * * sleep 52 && cd /opt/midad && /opt/midad/scripts/auto_sync_db.sh"
    echo "* * * * * sleep 53 && cd /opt/midad && /opt/midad/scripts/auto_sync_db.sh"
    echo "* * * * * sleep 54 && cd /opt/midad && /opt/midad/scripts/auto_sync_db.sh"
    echo "* * * * * sleep 55 && cd /opt/midad && /opt/midad/scripts/auto_sync_db.sh"
    echo "* * * * * sleep 56 && cd /opt/midad && /opt/midad/scripts/auto_sync_db.sh"
    echo "* * * * * sleep 57 && cd /opt/midad && /opt/midad/scripts/auto_sync_db.sh"
    echo "* * * * * sleep 58 && cd /opt/midad && /opt/midad/scripts/auto_sync_db.sh"
    echo "* * * * * sleep 59 && cd /opt/midad && /opt/midad/scripts/auto_sync_db.sh"
    echo ""
    echo "# Daily backup at 3 AM"
    echo "0 3 * * * cd /opt/midad && /opt/midad/scripts/backup.sh >> /opt/midad/logs/backup.log 2>&1"
) | crontab -

echo "✅ Cron updated!"
echo "📋 View cron jobs: crontab -l"
echo "📊 Monitor syncs: tail -f /opt/midad/logs/auto-sync.log"
echo ""
echo "⚡ Script now runs EVERY SECOND (60 times per minute)"
echo "🎯 But only commits when database actually changes!"
