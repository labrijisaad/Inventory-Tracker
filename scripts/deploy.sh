#!/bin/bash
# Deployment script for production VM
# Usage: ./scripts/deploy.sh

set -e

echo "🚀 Deploying Midad Books..."

# Pull latest code + database
echo "📥 Pulling from GitHub..."
git pull origin test/saad_labri

# Make scripts executable
echo "🔧 Updating permissions..."
chmod +x scripts/*.sh

# Restart service
echo "🔄 Restarting application..."
sudo systemctl restart midad

# Wait a moment
sleep 3

# Check status
echo "✅ Checking service status..."
sudo systemctl status midad --no-pager -l

echo ""
echo "🎉 Deployment complete!"
echo "📊 View logs: sudo journalctl -u midad -f"
echo "📈 Sync logs: tail -f /opt/midad/logs/auto-sync.log"
