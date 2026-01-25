#!/bin/bash
cd /opt/midad 2>/dev/null || exit 0
git fetch origin test/saad_labri --quiet 2>/dev/null || exit 0
LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse origin/test/saad_labri)
[ "$LOCAL" = "$REMOTE" ] && exit 0
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
mkdir -p /opt/midad/logs
{
    echo "[$TIMESTAMP] 🔄 New commits detected, pulling..."
    git pull origin test/saad_labri 2>&1
    echo "[$TIMESTAMP] 🔄 Restarting app..."
    sudo systemctl restart midad 2>&1
    echo "[$TIMESTAMP] ✅ App restarted"
} >> /opt/midad/logs/auto-pull.log 2>&1
