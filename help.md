# 🚀 Essential Commands

## Deploy (One Line)
```bash
cd /opt/midad && git pull origin test/saad_labri && sudo systemctl restart midad && sudo systemctl status midad
```

## Quick Commands
```bash
# Deploy (using script)
cd /opt/midad && ./scripts/deploy.sh

# View logs
sudo journalctl -u midad -n 50

# Live logs
sudo journalctl -u midad -f

# Restart service
sudo systemctl restart midad

# Check status
sudo systemctl status midad

# Exit SSH
exit
```

## Local PC
```bash
# Pull latest
git pull origin test/saad_labri

# Run locally
uv run streamlit run app.py

# Push changes
git add . && git commit -m "message" && git push origin test/saad_labri
```