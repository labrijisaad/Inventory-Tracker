#!/bin/bash
# Deployment script for production VM
# Usage: ./scripts/deploy.sh

set -e  # Exit on error

echo "🚀 Deploying Midad Books..."

# Pull latest code
echo "📥 Pulling from GitHub..."
git pull origin main

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