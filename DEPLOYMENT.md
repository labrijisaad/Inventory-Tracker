# 🚀 MIDAD BOOKS - COMPLETE DEPLOYMENT GUIDE

**Comprehensive guide for deploying the Midad Books Inventory Tracker from local development to Google Cloud Platform production.**

---

## 📋 Table of Contents

1. [System Overview](#system-overview)
2. [Architecture & Design Decisions](#architecture--design-decisions)
3. [Prerequisites](#prerequisites)
4. [Local Development Setup](#local-development-setup)
5. [Testing Locally](#testing-locally)
6. [Preparing for Production](#preparing-for-production)
7. [GCP VM Setup](#gcp-vm-setup)
8. [Production Deployment](#production-deployment)
9. [Daily Operations](#daily-operations)
10. [Monitoring & Maintenance](#monitoring--maintenance)
11. [Backup & Recovery](#backup--recovery)
12. [Troubleshooting](#troubleshooting)
13. [Common Issues & Solutions](#common-issues--solutions)

---

## System Overview

### What This Application Does

**Midad Books Inventory Tracker** is a complete inventory and sales management system for a small bookshop selling Arabic literature. It handles:

- **Inventory Management**: Track books with Arabic titles, pricing (buy price + target price), stock levels
- **Sales Recording**: Record individual or bundle sales, automatically update stock
- **Customer Management**: Track customer purchase history (linked via Vinted username)
- **Analytics**: Revenue, profit, margin analysis with visual charts
- **Quick Messages**: Pre-saved customer communication templates in French

### Technology Stack

```
Frontend/UI:        Streamlit 1.32+ (Python web framework)
Database ORM:       SQLModel 0.0.14 (Pydantic + SQLAlchemy)
Database:           SQLite 3 (embedded, file-based)
Package Manager:    UV (fast Python package installer)
Deployment:         GCP e2-micro VM (free tier)
Version Control:    Git + GitHub
Backup Strategy:    Git commits + local backups + GCS
```

### Key Features

1. **Book IDs**: String-based `BOOK-001`, `BOOK-002` format (human-readable, cross-system compatible)
2. **Sale IDs**: Display format `SE001` (database stores integers)
3. **Bundle Sales**: Multiple books sold together share a `bundle_id` (UUID)
4. **Stock Management**: Sales automatically decrement stock in transactional updates
5. **Environment Detection**: Automatically switches between dev (local) and production (VM) modes
6. **Database Sync**: Database is version-controlled in Git for disaster recovery

---

## Architecture & Design Decisions

### Why SQLite (Not PostgreSQL/MySQL)?

**Decision**: Use SQLite for both development and production.

**Reasoning**:
- ✅ Single user application (no concurrent writes)
- ✅ Small data volume (<100 MB for years of data)
- ✅ Zero maintenance (no separate database server)
- ✅ Simple backup (just copy the .db file)
- ✅ Fast for read-heavy workloads
- ✅ Can be version-controlled in Git

**Trade-offs**:
- ❌ Cannot scale horizontally (but not needed for single user)
- ❌ No replication (but Git provides backup)
- ❌ File-based (but stored on persistent disk on VM)

### Why String-Based Book IDs?

**Decision**: Use `BOOK-001` format instead of auto-increment integers.

**Reasoning**:
- ✅ Human-readable (easy to reference in conversations)
- ✅ Cross-system compatible (Vinted bot uses same IDs)
- ✅ Predictable sorting (BOOK-001, BOOK-002, BOOK-010 sorts correctly)
- ✅ No ID collision risk when syncing across systems

**Implementation**:
```python
# Auto-generate next ID
def generate_book_id() -> str:
    max_num = max(int(b.id.replace("BOOK-", "")) for b in books)
    return f"BOOK-{max_num + 1:03d}"  # Zero-padded to 3 digits
```

### Why Database in Git?

**Decision**: Commit database to Git repository (in `main` branch).

**Reasoning**:
- ✅ Single user (no merge conflicts)
- ✅ Simple disaster recovery (just `git pull`)
- ✅ Version history of data changes
- ✅ Can test locally with production data (`git pull`)
- ✅ Auto-sync to GitHub every 6 hours (cron job)
- ✅ Free unlimited backup (GitHub storage)

**Trade-offs**:
- ❌ Git repo size grows (but .db file is small, <10 MB)
- ❌ Unconventional approach (but works perfectly for use case)

**How It Works**:
```
Local PC:
  Edit code → Commit → Push to GitHub
  
VM (Production):
  Pull from GitHub (gets code + database)
  Auto-commit database changes every 6 hours
  Auto-push to GitHub (backup)
  
Disaster Recovery:
  Create new VM → Git clone → Database restored ✅
```

### Environment Detection Strategy

**Decision**: Use `PRODUCTION` environment variable to switch database paths.

**Code**:
```python
# src/data/database.py
if os.getenv('PRODUCTION') == 'true':
    DB_PATH = Path('/opt/midad-data/midad.db')  # VM
else:
    DB_PATH = Path('./data/midad.db')  # Local
```

**Why**:
- ✅ Explicit control (clear when in production)
- ✅ Testable locally (`PRODUCTION=true python app.py`)
- ✅ Industry standard (like `NODE_ENV`, `RAILS_ENV`)
- ✅ No path detection magic (less confusing)

**Alternative Rejected**:
```python
# ❌ Path-based detection (implicit, can break)
if Path('/opt/midad').exists():
    DB_PATH = Path('/opt/midad-data/midad.db')
```

### Database Path Strategy

**Decision**: Separate data directory outside app code.

**Structure on VM**:
```
/opt/midad/               ← Application code (git-controlled)
  ├── app.py
  ├── src/
  └── data/               ← Tracked in git (for sync)
      └── midad.db        ← Staging copy

/opt/midad-data/          ← Production database (persistent)
  └── midad.db            ← Live database (not in git directly)
```

**Why Separate**:
- ✅ Can delete/reinstall app without losing data
- ✅ Clear separation of code vs. data
- ✅ Easier backup (just backup /opt/midad-data/)
- ✅ Git operations don't risk database corruption

**Sync Flow**:
```
1. User records sale → /opt/midad-data/midad.db updated
2. Cron job runs → Copies to /opt/midad/data/midad.db
3. Cron commits → Git push to GitHub
4. VM can pull → Gets latest database from GitHub
```

---

## Prerequisites

### Required Software

**On Your Local PC (Windows/Mac/Linux)**:
- Python 3.11+ ([python.org](https://python.org))
- Git ([git-scm.com](https://git-scm.com))
- UV package manager (installed below)
- Text editor (VS Code recommended)

**On Google Cloud**:
- GCP account ([console.cloud.google.com](https://console.cloud.google.com))
- Payment method added (won't charge with free tier)
- gcloud CLI (optional but helpful)

### Required Accounts

- ✅ GitHub account (to host code)
- ✅ Google Cloud account (for VM hosting)

### Cost Expectations

**Free Tier (First 90 Days)**:
```
VM (e2-micro):           $0/month (free tier)
Boot disk (10GB):        $0/month (included)
Data disk (10GB):        $0.40/month
Backups:                 $0.30/month
─────────────────────────────────────
TOTAL:                   $0.70/month
```

**After Free Tier**:
```
VM (e2-micro):           $6.11/month
Boot disk (10GB):        $0.40/month
Data disk (10GB):        $0.40/month
Backups:                 $0.30/month
─────────────────────────────────────
TOTAL:                   $7.21/month ($86.52/year)
```

---

## Local Development Setup

### Step 1: Install UV Package Manager

**Windows (PowerShell)**:
```powershell
irm https://astral.sh/uv/install.ps1 | iex
```

**macOS/Linux**:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.cargo/env
```

**Verify Installation**:
```bash
uv --version
# Should show: uv 0.x.x
```

### Step 2: Clone Repository

```bash
# Clone your repository
git clone https://github.com/YOUR_USERNAME/Inventory-Tracker.git
cd Inventory-Tracker

# Verify files exist
ls -la
# Should see: app.py, src/, pages/, data/, etc.
```

### Step 3: Install Dependencies

```bash
# UV will create virtual environment and install packages
uv sync

# This installs:
# - streamlit (UI framework)
# - sqlmodel (database ORM)
# - pandas (data manipulation)
# - plotly (charts)
```

**What `uv sync` does**:
1. Reads `pyproject.toml` (dependencies list)
2. Creates `.venv/` folder (virtual environment)
3. Installs all packages specified
4. Creates `uv.lock` (lock file for reproducibility)

### Step 4: Verify inventory.json Exists

```bash
# Check inventory.json is in project root
ls inventory.json

# If missing, create one with your books
# Example format:
cat > inventory.json << 'EOF'
{
  "books": [
    {
      "id": "BOOK-001",
      "name": "فن اللامبالاة",
      "isbn": "6144720197",
      "category": "Non-fiction",
      "genre": "Non-fiction",
      "price": 14.99,
      "buy_price": 2.50,
      "stock": 1
    }
  ]
}
EOF
```

### Step 5: Initialize Database

```bash
# Create fresh database with your books
uv run python reset_db.py

# You'll see:
# 💻 Running in DEVELOPMENT mode
# 📂 Database path: /path/to/Inventory-Tracker/data/midad.db
# 
# Delete existing database and recreate? (yes/no): yes
# 
# ✅ Loaded 45 books from inventory.json
#    📖 Fiction: 5
#    📚 Non-fiction: 38
#    📦 Other: 2
```

**What This Creates**:
- `data/midad.db` (SQLite database file)
- Tables: `book`, `customer`, `sale`, `quickmessage`
- Sample data: Books from inventory.json, default quick messages
- Test customer (only in dev mode)

### Step 6: Run Application

```bash
# Start Streamlit server
uv run streamlit run app.py

# You'll see:
# You can now view your Streamlit app in your browser.
# 
# Local URL: http://localhost:8501
# Network URL: http://192.168.x.x:8501
```

**Browser Opens Automatically**:
- Home page with dashboard metrics
- Sidebar with navigation (Inventory, Sales, Analytics, etc.)
- No errors in terminal

---

## Testing Locally

### Test 1: Environment Detection

**Verify Development Mode (Default)**:
```bash
# Check console output
uv run streamlit run app.py

# Should show at startup:
# 💻 Running in DEVELOPMENT mode
# 📂 Database path: /path/to/Inventory-Tracker/data/midad.db
```

**Test Production Mode Locally**:
```bash
# Simulate production environment
PRODUCTION=true uv run streamlit run app.py

# Should show:
# 🚀 Running in PRODUCTION mode
# 📂 Database path: /opt/midad-data/midad.db
# 
# Then error:
# FileNotFoundError: /opt/midad-data (doesn't exist locally)
```

**Expected**: ✅ Error is GOOD! Confirms environment detection works.

Press `Ctrl+C` to stop.

### Test 2: Inventory Management

**In Browser** (`http://localhost:8501`):

1. **Click "📦 Inventory" in sidebar**
2. **Active Inventory Tab**:
   - See your books loaded from inventory.json ✅
   - Try editing a book title (inline)
   - Click "💾 Save Changes"
   - Verify changes persist (reload page)

3. **Add New Book**:
   - Click `+` button at bottom of table
   - Fill: ID (BOOK-999), Title, Genre, Prices, Stock
   - Save
   - Verify new book appears

4. **Filter Test**:
   - Check "Active Inventory" shows only stock > 0
   - Check "Sold Out" shows only stock = 0

### Test 3: Sales Recording

**Record a Sale**:

1. **Click "💰 Sales" in sidebar**
2. **"Record Sale" Tab**:
   - Select a book from dropdown
   - Enter:
     - Date: Today
     - Platform: Vinted
     - Quantity: 1
     - Total Paid: 15.00
     - Packaging: 1.00 (default)
   - Enter customer:
     - Name: "Test Customer"
     - Username: "test_user"
   
3. **Check Live Calculation**:
   - Should show profit calculation in green box
   - Example: "💚 PROFITABLE SALE | €12.50 profit (45.2% margin)"

4. **Click "✅ Record Sale"**:
   - Success toast appears: "🎉 Profit: €12.50"
   - Balloons animation
   - Sale appears in history below

5. **Verify Stock Updated**:
   - Go back to Inventory
   - Check book stock decreased by 1

### Test 4: Bundle Sales

**Record Bundle**:

1. **Sales → "Bundle Sale" Tab**
2. **Select Multiple Books**:
   - Select 2-3 books from multi-select dropdown
3. **Enter Quantities**:
   - For each book, set quantity (e.g., 2, 1, 1)
4. **Set Total Price**:
   - System suggests total based on target prices
   - Override if needed (e.g., €40 for bundle)
5. **Check Preview**:
   - Shows: Total books, average price, profit, margin
6. **Record Bundle**:
   - Enter customer info
   - Click "Record Bundle"
   - Success message

7. **Verify in History**:
   - Sales History shows `B-xxxxx` (bundle ID)
   - Expand to see books in bundle
   - Each book stock decreased

### Test 5: Analytics

**Check Dashboard**:

1. **Click "📊 Analytics"**
2. **Verify Metrics Display**:
   - Top cards: Revenue, Profit, Books Sold, Avg Order
   - All should have values (if sales recorded)

3. **Check Charts**:
   - Sales by Platform (bar chart)
   - Sales Timeline (line chart with markers)
   - Profit Margin Distribution (histogram)

4. **Check Best Sellers**:
   - Top 5 books by quantity sold
   - Medal icons: 🥇🥈🥉

### Test 6: Quick Messages

**Manage Templates**:

1. **Click "💬 Quick Messages"**
2. **View Messages**:
   - See default messages (Welcome, Shipping, etc.)
   - Copy button to clipboard

3. **Add New Message**:
   - Switch to "Add Message" tab
   - Fill: Title, Category, Message
   - Save
   - Verify appears in list

4. **Edit Message**:
   - Click edit button on a message
   - Update text
   - Save
   - Verify changes

### Test 7: Health Check

**Access Monitoring Endpoint**:

```bash
# In browser, go to:
http://localhost:8501/99_health

# Should show JSON:
{
  "status": "healthy",
  "timestamp": "2026-01-16T12:00:00",
  "database": {
    "path": "/path/to/data/midad.db",
    "exists": true,
    "size_mb": 0.05,
    "books_count": 45
  }
}
```

**This page is hidden from sidebar** (for monitoring tools only).

### Test 8: Database Reset

**Test Reset Script**:

```bash
# Stop Streamlit (Ctrl+C)

# Run reset
uv run python reset_db.py

# Prompts: Delete existing database and recreate? (yes/no)
# Answer: yes

# Should see:
# ✅ DATABASE RESET COMPLETE!
# 📂 Location: /path/to/data/midad.db
# 📊 Books: 45
# 💰 Default buy price: €2.50
```

**Verify**:
- Start app: `uv run streamlit run app.py`
- Check inventory: Should show fresh books
- Check sales: Should be empty (no history)

---

## Preparing for Production

### Verify Git Status

**Before pushing to GitHub, check**:

```bash
# What will be committed?
git status

# Should show:
# On branch main
# Your branch is up to date with 'origin/main'.
# 
# nothing to commit, working tree clean
```

**If you have uncommitted changes**:

```bash
# See what changed
git diff

# Stage changes
git add .

# Commit
git commit -m "description of changes"

# Push to GitHub
git push origin main
```

### Verify .gitignore

**Check database is NOT ignored**:

```bash
# View .gitignore content
cat .gitignore | grep -A5 "data"

# Should see:
# ✅ ALLOW main database (we WANT this in git)
# Database temporary files only
# data/*.db-journal
# data/*.db-shm
# data/*.db-wal
```

**Should NOT see**: `data/*.db` (this would block database from git)

### Commit Database

**Add database to git**:

```bash
# Check if database is tracked
git ls-files | grep midad.db

# If nothing shows, add it:
git add data/midad.db

# Commit with timestamp
git commit -m "db: production ready $(date '+%Y-%m-%d %H:%M:%S')"

# Push to GitHub
git push origin main
```

### Verify on GitHub

**Go to your repository**:
```
https://github.com/YOUR_USERNAME/Inventory-Tracker
```

**Check These Exist**:
- ✅ `data/midad.db` file (click to view)
- ✅ `scripts/` folder with 4 .sh files:
  - `auto_sync_db.sh`
  - `backup.sh`
  - `deploy.sh`
  - `pull_and_sync.sh`
- ✅ `.streamlit/config.toml` (updated)
- ✅ `reset_db.py` (updated)
- ✅ `pages/99_health.py` (health check)

**If Missing Any**:
```bash
# Add missing files
git add <missing-file>
git commit -m "add missing file"
git push origin main
```

### Pre-Deployment Checklist

**Copy this and verify**:

```
Local Testing:
✅ App runs without errors (uv run streamlit run app.py)
✅ Console shows "💻 Running in DEVELOPMENT mode"
✅ Can view inventory (all books visible)
✅ Can record sale (stock updates correctly)
✅ Can record bundle (multiple books)
✅ Analytics page loads (charts visible)
✅ Health check works (http://localhost:8501/99_health)

Environment Detection:
✅ Development mode uses ./data/midad.db
✅ Production mode (PRODUCTION=true) looks for /opt/midad-data/midad.db
✅ Console output shows correct mode

Git Repository:
✅ All code changes committed
✅ Database file (data/midad.db) committed
✅ Scripts exist (scripts/*.sh)
✅ .gitignore allows database (not blocking data/*.db)
✅ GitHub repository has latest code
✅ GitHub repository has database file

Scripts Verified:
✅ scripts/auto_sync_db.sh exists (1255 bytes)
✅ scripts/backup.sh exists (1875 bytes)
✅ scripts/deploy.sh exists (517 bytes)
✅ scripts/pull_and_sync.sh exists (1825 bytes)

Configuration:
✅ .streamlit/config.toml has production settings
✅ src/data/database.py has environment detection
✅ reset_db.py has production safeguards
```

**If all checked** → ✅ **READY FOR PRODUCTION DEPLOYMENT!**

---

## GCP VM Setup

### Step 1: Create GCP Project

1. **Go to**: [console.cloud.google.com](https://console.cloud.google.com)
2. **Click**: "Select a project" (top bar)
3. **Click**: "New Project"
4. **Enter**:
   - Project name: `midad-bookshop`
   - Organization: (leave default or select if applicable)
5. **Click**: "Create"
6. **Wait**: 30 seconds for project creation
7. **Switch**: To new project (use project selector dropdown)

### Step 2: Enable Billing (Required for Free Tier)

1. **Click**: "☰" menu → "Billing"
2. **Link**: A billing account (credit/debit card required)
   - ⚠️ **Note**: Won't charge with free tier, but card required for verification
3. **Verify**: "Billing enabled" badge appears

### Step 3: Enable Compute Engine API

1. **Search**: "Compute Engine" in top search bar
2. **Click**: "Compute Engine" result
3. **Click**: "Enable" button (if prompted)
4. **Wait**: 1-2 minutes for API to activate
5. **Verify**: VM Instances page loads

### Step 4: Create VM Instance

**Option A: Via Web Console** (Recommended for First Time)

1. **Navigate**: Compute Engine → VM Instances
2. **Click**: "Create Instance"
3. **Configure**:

**Name**:
```
midad-app
```

**Region** (MUST be free tier region):
```
us-central1 (Iowa)
```

**Zone**:
```
us-central1-a
```

**Machine Configuration**:
```
Series: E2
Machine type: e2-micro (0.25-2 vCPU, 1 GB memory)
```
⚠️ **Important**: This is the FREE TIER machine type!

**Boot Disk**:
```
Click "CHANGE"
  Operating system: Ubuntu
  Version: Ubuntu 22.04 LTS
  Boot disk type: Standard persistent disk
  Size: 10 GB
Click "SELECT"
```

**Firewall**:
```
✅ Allow HTTP traffic
✅ Allow HTTPS traffic
```

**Advanced Options** → **Management**:
```
Tags: midad-app
```

4. **Click**: "Create" (bottom of page)
5. **Wait**: 30-60 seconds for VM to start
6. **Verify**: VM status shows green checkmark "✓ Running"

**Option B: Via gcloud CLI** (Faster if you have gcloud installed)

```bash
# Login to GCP
gcloud auth login

# Set project
gcloud config set project midad-bookshop

# Create VM
gcloud compute instances create midad-app \
    --zone=us-central1-a \
    --machine-type=e2-micro \
    --image-family=ubuntu-2204-lts \
    --image-project=ubuntu-os-cloud \
    --boot-disk-size=10GB \
    --boot-disk-type=pd-standard \
    --tags=midad-app

# Verify
gcloud compute instances list
```

### Step 5: Create Firewall Rule (Open Streamlit Port)

**Why**: By default, VM blocks all incoming traffic. We need to open port 8501 (Streamlit).

**Via Web Console**:

1. **Navigate**: VPC Network → Firewall → "Create Firewall Rule"
2. **Configure**:

```
Name: allow-streamlit
Description: Allow Streamlit app access
Direction of traffic: Ingress
Action on match: Allow
Targets: Specified target tags
Target tags: midad-app
Source IP ranges: 0.0.0.0/0
Protocols and ports:
  ✅ Specified protocols and ports
  tcp: 8501
```

3. **Click**: "Create"

**Via gcloud CLI**:

```bash
gcloud compute firewall-rules create allow-streamlit \
    --allow=tcp:8501 \
    --source-ranges=0.0.0.0/0 \
    --target-tags=midad-app \
    --description="Allow Streamlit app access"
```

### Step 6: Get VM IP Address

**Via Web Console**:
- Go to: Compute Engine → VM Instances
- Look at "External IP" column
- Copy IP (e.g., `35.123.45.67`)

**Via gcloud CLI**:
```bash
gcloud compute instances list --filter="name=midad-app"
```

**Save This IP**: You'll use it to access your app later!

### Step 7: SSH into VM

**Via Web Console** (Easiest):
1. Go to: Compute Engine → VM Instances
2. Find "midad-app" row
3. Click "SSH" button (opens browser terminal)
4. **Wait**: SSH session opens (might take 10-20 seconds first time)

**Via gcloud CLI**:
```bash
gcloud compute ssh midad-app --zone=us-central1-a
```

**Via Standard SSH** (if you have SSH key):
```bash
ssh YOUR_USERNAME@35.123.45.67
```

**You Should See**:
```
Welcome to Ubuntu 22.04.3 LTS (GNU/Linux ...)
yourname@midad-app:~$
```

---

## Production Deployment

**⚠️ Run these commands in the VM SSH terminal!**

### Step 1: Update System

```bash
# Update package lists
sudo apt update

# Upgrade existing packages
sudo apt upgrade -y

# Install essential tools
sudo apt install -y git curl wget
```

**Wait**: 2-3 minutes for updates.

### Step 2: Install UV Package Manager

```bash
# Download and install UV
curl -LsSf https://astral.sh/uv/install.sh | sh

# Add UV to current shell
source $HOME/.cargo/env

# Verify installation
uv --version
# Should show: uv 0.x.x
```

### Step 3: Clone Repository

```bash
# Create app directory
cd /opt
sudo mkdir midad
sudo chown $USER:$USER midad
cd midad

# Clone from GitHub (replace with YOUR username!)
git clone https://github.com/YOUR_USERNAME/Inventory-Tracker.git .

# Verify files exist
ls -la
# Should show: app.py, src/, pages/, data/, scripts/, etc.
```

**If Git Asks for Credentials**:
- Use GitHub username
- For password, use Personal Access Token (not actual password)
- Generate token: GitHub → Settings → Developer Settings → Personal Access Tokens

### Step 4: Create Production Data Directory

```bash
# Create persistent data directory
sudo mkdir -p /opt/midad-data
sudo chown $USER:$USER /opt/midad-data

# Verify ownership
ls -ld /opt/midad-data
# Should show: drwxr-xr-x ... yourname yourname ... /opt/midad-data
```

**Why Separate Directory**:
- App code in `/opt/midad` (can be deleted/reinstalled)
- Database in `/opt/midad-data` (persistent, survives app reinstalls)

### Step 5: Install Dependencies

```bash
cd /opt/midad

# Install all Python packages
uv sync

# Wait: 2-4 minutes (downloads streamlit, sqlmodel, etc.)
# You'll see:
# ✅ Resolved X packages in Y seconds
# ✅ Installed X packages in Y seconds
```

**What Gets Installed**:
```
.venv/            ← Virtual environment created
.venv/bin/        ← Python executable and scripts
.venv/lib/        ← Installed packages (streamlit, sqlmodel, etc.)
```

### Step 6: Pull Database from GitHub

```bash
cd /opt/midad

# Pull latest (gets database from git)
git pull origin main

# Copy database to production location
cp data/midad.db /opt/midad-data/

# Verify database exists
ls -lh /opt/midad-data/midad.db
# Should show: -rw-r--r-- ... midad.db
```

**Alternatively, Initialize Fresh**:
```bash
# If you want fresh database instead of pulling from GitHub:
cd /opt/midad
PRODUCTION=true uv run python reset_db.py

# Prompts: Type 'YES DELETE PRODUCTION' to confirm
# (only if database already exists)
```

### Step 7: Test Run (Manual)

```bash
cd /opt/midad

# Start app manually (test)
PRODUCTION=true uv run streamlit run app.py --server.address 0.0.0.0

# You should see:
# 🚀 Running in PRODUCTION mode
# 📂 Database path: /opt/midad-data/midad.db
# 
# You can now view your Streamlit app in your browser.
# External URL: http://35.xxx.xxx.xxx:8501
```

**Test Access**:
- Open browser on your PC
- Go to: `http://YOUR_VM_IP:8501`
- App should load!

**Press Ctrl+C to stop** (we'll set up auto-start next).

### Step 8: Create Systemd Service (Auto-Start)

**Why**: Systemd will auto-start app on boot and restart on crashes.

**Create service file**:

```bash
sudo nano /etc/systemd/system/midad.service
```

**Paste this** (replace `YOUR_USERNAME` with your actual username):

```ini
[Unit]
Description=Midad Books Inventory Tracker
After=network.target
Documentation=https://github.com/YOUR_USERNAME/Inventory-Tracker

[Service]
Type=simple
User=YOUR_USERNAME
WorkingDirectory=/opt/midad
Environment="PATH=/home/YOUR_USERNAME/.cargo/bin:/usr/local/bin:/usr/bin:/bin"
Environment="PRODUCTION=true"
ExecStart=/home/YOUR_USERNAME/.cargo/bin/uv run streamlit run app.py --server.port 8501 --server.address 0.0.0.0 --server.headless true
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

**Get Your Username**:
```bash
whoami
# Output: yourname
```

Replace `YOUR_USERNAME` with this output!

**Save File**:
- Press `Ctrl+X`
- Press `Y` (yes)
- Press `Enter`

**Enable and Start Service**:

```bash
# Reload systemd (recognize new service)
sudo systemctl daemon-reload

# Enable auto-start on boot
sudo systemctl enable midad

# Start service now
sudo systemctl start midad

# Check status
sudo systemctl status midad
```

**Expected Output**:
```
● midad.service - Midad Books Inventory Tracker
     Loaded: loaded (/etc/systemd/system/midad.service; enabled)
     Active: active (running) since ...
```

**If Status Shows "failed"** → Skip to Troubleshooting section!

### Step 9: Verify App is Running

**Check Logs**:
```bash
sudo journalctl -u midad -f

# Should see:
# 🚀 Running in PRODUCTION mode
# 📂 Database path: /opt/midad-data/midad.db
# 
# You can now view your Streamlit app in your browser.
```

**Press Ctrl+C to exit logs.**

**Access in Browser**:
```
http://YOUR_VM_IP:8501
```

**You Should See**:
- Home page with metrics
- Sidebar navigation
- Your books in inventory
- No errors!

🎉 **IF IT WORKS → PRODUCTION DEPLOYMENT COMPLETE!** 🎉

### Step 10: Setup Cron Jobs (Auto-Sync & Backup)

**Why**: Automatically sync database to GitHub and create backups.

**Edit crontab**:
```bash
crontab -e

# If prompted, choose editor: nano (easiest)
```

**Add these lines at the end**:

```bash
# Auto-sync database to GitHub every 6 hours
0 */6 * * * cd /opt/midad && /opt/midad/scripts/auto_sync_db.sh >> /opt/midad/logs/auto-sync.log 2>&1

# Local + GCS backup daily at 3 AM
0 3 * * * cd /opt/midad && /opt/midad/scripts/backup.sh >> /opt/midad/logs/backup.log 2>&1
```

**Save**:
- Press `Ctrl+X`
- Press `Y`
- Press `Enter`

**Create Logs Directory**:
```bash
mkdir -p /opt/midad/logs
```

**Test Scripts Manually**:

```bash
# Test auto-sync (commits database to GitHub)
cd /opt/midad
./scripts/auto_sync_db.sh

# Should see:
# 🔄 Auto-sync starting at ...
# ✅ Database synced to GitHub: 2026-01-16 15:00:00

# Check GitHub - new commit should appear!

# Test backup (creates local + GCS backup)
./scripts/backup.sh

# Should see:
# 📦 Creating backup: midad_backup_20260116_150000.db
# ✅ Backup complete!
```

**Verify Cron Jobs**:
```bash
# List cron jobs
crontab -l

# Should show the two lines you added
```

---

## Daily Operations

### Regular Workflow (Code Changes)

**On Your Local PC**:

1. **Make Changes**:
```bash
# Edit code
code src/services/sales_service.py

# Test locally
uv run streamlit run app.py

# Commit changes
git add src/services/sales_service.py
git commit -m "fix: sales calculation bug"

# Push to GitHub
git push origin main
```

2. **Deploy to VM**:

**Option A: SSH and Run Deploy Script**:
```bash
# SSH into VM
gcloud compute ssh midad-app --zone=us-central1-a

# Or: ssh yourname@YOUR_VM_IP

# Run deploy script
cd /opt/midad
./scripts/deploy.sh

# Should see:
# 🚀 Deploying Midad Books...
# 📥 Pulling from GitHub...
# 🔄 Restarting application...
# ✅ Service restarted successfully
# 🎉 Deployment complete!
```

**Option B: Manual Deployment**:
```bash
# SSH into VM
gcloud compute ssh midad-app --zone=us-central1-a

# Pull latest code
cd /opt/midad
git pull origin main

# Restart service
sudo systemctl restart midad

# Check logs
sudo journalctl -u midad -n 20

# Exit SSH
exit
```

**Option C: Automatic (Wait 6 Hours)**:
- Cron job auto-pulls every 6 hours
- No manual action needed
- Use for non-urgent changes

### Testing with Production Database Locally

**Sometimes you want to test locally with real production data**:

```bash
# On your local PC

# Pull latest (includes production database)
git pull origin main

# Your local database now matches production!

# Test
uv run streamlit run app.py

# When done, keep production database or restore dev database
# (Keep backup: cp data/midad.db data/midad_prod_backup.db before pulling)
```

### Checking Application Status

**From Anywhere**:

```bash
# SSH into VM
gcloud compute ssh midad-app --zone=us-central1-a

# Check service status
sudo systemctl status midad

# View recent logs
sudo journalctl -u midad -n 50

# View live logs (tail)
sudo journalctl -u midad -f

# Exit
exit
```

**Or Access Health Check**:
```
http://YOUR_VM_IP:8501/99_health
```

Should show JSON with status.

---

## Monitoring & Maintenance

### Daily Checks

**Quick Health Check** (30 seconds):

```bash
# SSH into VM
gcloud compute ssh midad-app --zone=us-central1-a

# One-liner status check
sudo systemctl status midad --no-pager && \
  echo "Database:" && ls -lh /opt/midad-data/midad.db && \
  echo "Recent backups:" && ls -lt /opt/backups/ | head -n 3

# Should show:
# ● midad.service - Midad Books Inventory Tracker
#      Active: active (running) ...
# Database:
#   -rw-r--r-- ... 0.XX MB ... midad.db
# Recent backups:
#   midad_backup_20260116_030000.db
#   midad_backup_20260115_030000.db
```

### Weekly Checks

**Review Logs for Errors**:

```bash
# SSH into VM
gcloud compute ssh midad-app --zone=us-central1-a

# Check for errors in last 7 days
sudo journalctl -u midad --since "7 days ago" | grep -i error

# If nothing shows → All good! ✅
```

**Verify Backups Exist**:

```bash
# Check local backups
ls -lh /opt/backups/

# Should show backups from last 30 days

# Check GCS backups (if setup)
gsutil ls gs://midad-backups-YOURNAME/

# Should show backups in cloud
```

### Monthly Maintenance

**Update System Packages**:

```bash
# SSH into VM
gcloud compute ssh midad-app --zone=us-central1-a

# Update packages
sudo apt update
sudo apt upgrade -y

# Reboot if kernel updated
sudo reboot
# (VM will auto-restart app)
```

**Clean Old Backups**:

```bash
# Cron already deletes >30 days, but verify:
cd /opt/backups
ls -lt | wc -l
# Should show around 30 files (one per day)

# Manual cleanup if needed:
find /opt/backups -name "midad_backup_*.db" -mtime +30 -delete
```

**Check Disk Usage**:

```bash
# Check free space
df -h /

# Should show >2GB free (10GB disk, ~1GB used)

# If low, clean old logs:
sudo journalctl --vacuum-time=30d
```

---

## Backup & Recovery

### Backup Strategy

**3 Layers of Protection**:

1. **GitHub (Every 6 Hours)**:
   - Cron commits database to git
   - Automatic, no action needed
   - Free unlimited history

2. **Local VM Backups (Daily)**:
   - Stored in `/opt/backups/`
   - Keeps last 30 days
   - Fast recovery (same VM)

3. **Google Cloud Storage (Daily)**:
   - Off-site backup
   - Survives VM deletion
   - 30-day retention

### Manual Backup

**Create Backup Now**:

```bash
# SSH into VM
gcloud compute ssh midad-app --zone=us-central1-a

# Run backup script
cd /opt/midad
./scripts/backup.sh

# Verify backup created
ls -lh /opt/backups/ | tail -n 1
```

**Download Backup to Your PC**:

```bash
# From your PC (not SSH)

# Using gcloud
gcloud compute scp midad-app:/opt/backups/midad_backup_20260116_030000.db ./local-backup.db --zone=us-central1-a

# Using SCP
scp yourname@YOUR_VM_IP:/opt/backups/midad_backup_20260116_030000.db ./local-backup.db
```

### Disaster Recovery Scenarios

### Scenario 1: Accidental Data Deletion

**You deleted sales records by mistake.**

**Solution: Restore from GitHub** (Last 6-hour checkpoint):

```bash
# SSH into VM
gcloud compute ssh midad-app --zone=us-central1-a

cd /opt/midad

# See recent commits
git log --oneline -n 10

# Find commit before deletion (e.g., 2 commits ago)
git log --pretty=format:"%h %cd %s" --date=format:"%Y-%m-%d %H:%M" -n 10

# Restore database from that commit
git checkout abc123 -- data/midad.db

# Copy to production
cp data/midad.db /opt/midad-data/

# Restart app
sudo systemctl restart midad

# Verify data restored in browser
```

**Max Data Loss**: Up to 6 hours (last sync).

---

### Scenario 2: Database Corrupted

**App won't start, database file corrupted.**

**Solution: Restore from Local Backup** (Last night):

```bash
# SSH into VM
gcloud compute ssh midad-app --zone=us-central1-a

# Stop app
sudo systemctl stop midad

# Check available backups
ls -lh /opt/backups/

# Copy latest backup
cp /opt/backups/midad_backup_20260116_030000.db /opt/midad-data/midad.db

# Restart app
sudo systemctl start midad

# Check logs
sudo journalctl -u midad -n 20

# Verify in browser
```

**Max Data Loss**: 24 hours (since last daily backup at 3 AM).

---

### Scenario 3: VM Deleted/Lost

**Entire VM gone, need to recreate everything.**

**Solution: Rebuild from GitHub**:

1. **Create New VM** (follow GCP VM Setup steps 1-7)

2. **Deploy App**:

```bash
# SSH into new VM
gcloud compute ssh midad-app-NEW --zone=us-central1-a

# Update system
sudo apt update && sudo apt upgrade -y
sudo apt install -y git curl

# Install UV
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.cargo/env

# Clone repository
cd /opt
sudo mkdir midad
sudo chown $USER:$USER midad
cd midad
git clone https://github.com/YOUR_USERNAME/Inventory-Tracker.git .

# Create data directory
sudo mkdir -p /opt/midad-data
sudo chown $USER:$USER /opt/midad-data

# Install dependencies
uv sync

# Copy database from GitHub
cp data/midad.db /opt/midad-data/

# Setup systemd service (copy from Deployment section)
# ... (create service file, enable, start)

# Setup cron jobs
crontab -e
# ... (add auto-sync and backup lines)
```

3. **Done!** Database restored from GitHub.

**Max Data Loss**: Up to 6 hours (last GitHub sync).

---

### Scenario 4: Complete Disaster (GitHub + VM Lost)

**GitHub account hacked, VM deleted, all gone.**

**Solution: Restore from Google Cloud Storage** (if setup):

1. **Create New VM + Deploy App** (as above)

2. **Restore from GCS**:

```bash
# SSH into new VM
gcloud compute ssh midad-app-NEW --zone=us-central1-a

# List GCS backups
gsutil ls gs://midad-backups-YOURNAME/

# Download latest
gsutil cp gs://midad-backups-YOURNAME/midad_backup_20260116_030000.db /opt/midad-data/midad.db

# Restart app
sudo systemctl restart midad
```

**Max Data Loss**: 24 hours (last daily GCS backup).

---

## Troubleshooting

### Common Issues & Solutions

#### Issue 1: Service Won't Start

**Symptom**:
```bash
sudo systemctl status midad
# Shows: failed (code=exited, status=1)
```

**Diagnosis**:
```bash
# View detailed logs
sudo journalctl -u midad -n 100

# Common errors:
# - ModuleNotFoundError: No module named 'streamlit'
# - FileNotFoundError: [Errno 2] No such file or directory: '/opt/midad-data/midad.db'
# - Permission denied
```

**Solutions**:

**A) Missing Dependencies**:
```bash
cd /opt/midad
uv sync
sudo systemctl restart midad
```

**B) Database Missing**:
```bash
# Initialize database
cd /opt/midad
PRODUCTION=true uv run python reset_db.py
sudo systemctl restart midad
```

**C) Wrong Username in Service File**:
```bash
# Check username
whoami

# Edit service file
sudo nano /etc/systemd/system/midad.service

# Replace YOUR_USERNAME with actual username
# Save (Ctrl+X, Y, Enter)

# Reload and restart
sudo systemctl daemon-reload
sudo systemctl restart midad
```

**D) Wrong Python Path**:
```bash
# Find UV path
which uv
# Shows: /home/yourname/.cargo/bin/uv

# Update service file ExecStart to use this path
sudo nano /etc/systemd/system/midad.service
```

---

#### Issue 2: Can't Access App from Browser

**Symptom**: `http://YOUR_VM_IP:8501` times out.

**Diagnosis**:

**A) Check if Service Running**:
```bash
sudo systemctl status midad
# Should show: active (running)
```

**B) Check if Port Open**:
```bash
sudo netstat -tlnp | grep 8501
# Should show:
# tcp 0.0.0.0:8501 ... LISTEN ... streamlit
```

**C) Check Firewall Rule**:
```bash
gcloud compute firewall-rules list | grep streamlit
# Should show: allow-streamlit ... tcp:8501
```

**Solutions**:

**A) Service Not Running**:
```bash
sudo systemctl start midad
sudo systemctl status midad
```

**B) Firewall Rule Missing**:
```bash
gcloud compute firewall-rules create allow-streamlit \
    --allow=tcp:8501 \
    --source-ranges=0.0.0.0/0 \
    --target-tags=midad-app
```

**C) Wrong VM Tags**:
```bash
# Check VM tags
gcloud compute instances describe midad-app --zone=us-central1-a | grep tags -A5

# Add tag if missing
gcloud compute instances add-tags midad-app --tags=midad-app --zone=us-central1-a
```

---

#### Issue 3: Cron Jobs Not Running

**Symptom**: No new commits in GitHub, no backups created.

**Diagnosis**:
```bash
# Check cron jobs exist
crontab -l

# Should show:
# 0 */6 * * * cd /opt/midad && /opt/midad/scripts/auto_sync_db.sh ...
# 0 3 * * * cd /opt/midad && /opt/midad/scripts/backup.sh ...
```

**Check Logs**:
```bash
# Auto-sync log
cat /opt/midad/logs/auto-sync.log

# Backup log
cat /opt/midad/logs/backup.log

# If logs empty or missing → cron never ran
```

**Solutions**:

**A) Scripts Not Executable**:
```bash
chmod +x /opt/midad/scripts/*.sh
```

**B) Wrong Paths in Cron**:
```bash
# Edit crontab
crontab -e

# Verify paths are absolute:
# ✅ cd /opt/midad && /opt/midad/scripts/auto_sync_db.sh
# ❌ cd midad && ./scripts/auto_sync_db.sh (relative paths don't work in cron)
```

**C) Test Scripts Manually**:
```bash
cd /opt/midad
./scripts/auto_sync_db.sh
# Check output for errors

./scripts/backup.sh
# Check if backup created
```

---

#### Issue 4: Git Push Fails (Auto-Sync)

**Symptom**:
```bash
cat /opt/midad/logs/auto-sync.log
# Shows: error: failed to push some refs
```

**Cause**: Git authentication not configured.

**Solution**:

**A) Setup Git Credentials**:
```bash
# Configure git user
git config --global user.email "your-email@example.com"
git config --global user.name "Your Name"

# For HTTPS (Personal Access Token required)
git config --global credential.helper store

# Push manually once (will prompt for credentials)
cd /opt/midad
git push origin main
# Enter:
#   Username: YOUR_GITHUB_USERNAME
#   Password: YOUR_PERSONAL_ACCESS_TOKEN (not actual password!)

# Credentials saved for future pushes
```

**Generate Personal Access Token**:
1. Go to: https://github.com/settings/tokens
2. Click: "Generate new token (classic)"
3. Scopes: ✅ repo (full control)
4. Generate
5. Copy token (save it - shown only once!)

---

#### Issue 5: Database Not Syncing

**Symptom**: Changes made on VM don't appear in GitHub.

**Diagnosis**:
```bash
# Check last sync
cat /opt/midad/logs/auto-sync.log | tail -n 10

# Check git status
cd /opt/midad
git status
# Should show: nothing to commit, working tree clean
# (after successful sync)
```

**Solutions**:

**A) Manual Sync**:
```bash
cd /opt/midad
./scripts/auto_sync_db.sh

# Check GitHub for new commit
```

**B) Check Database Path**:
```bash
# Verify production database exists
ls -lh /opt/midad-data/midad.db

# Verify script copies it correctly
cat scripts/auto_sync_db.sh | grep "cp"
# Should show: cp "$DB_PATH" data/midad.db
```

---

### Logs & Debugging

**View Application Logs**:
```bash
# Last 50 lines
sudo journalctl -u midad -n 50

# Live tail
sudo journalctl -u midad -f

# Since specific time
sudo journalctl -u midad --since "2 hours ago"

# Filter by priority (errors only)
sudo journalctl -u midad -p err

# Save to file
sudo journalctl -u midad -n 1000 > ~/midad-logs.txt
```

**View Cron Logs**:
```bash
# System cron log
sudo grep CRON /var/log/syslog | tail -n 20

# Your user's cron
grep CRON /var/log/syslog | grep $(whoami)
```

**Check Script Outputs**:
```bash
# Auto-sync log
cat /opt/midad/logs/auto-sync.log

# Backup log
cat /opt/midad/logs/backup.log

# Live tail
tail -f /opt/midad/logs/auto-sync.log
```

**Database Integrity Check**:
```bash
# Check database file
cd /opt/midad-data
file midad.db
# Should show: SQLite 3.x database

# Check database schema
sqlite3 midad.db ".tables"
# Should show: book  customer  quickmessage  sale

# Check record counts
sqlite3 midad.db "SELECT COUNT(*) FROM book;"
sqlite3 midad.db "SELECT COUNT(*) FROM sale;"
```

---

## Common Issues & Solutions

### Performance Issues

**App Slow to Load**:

**Possible Causes**:
1. Large database (>100 MB)
2. Too many records in single table
3. VM out of memory

**Solutions**:

**A) Check Database Size**:
```bash
du -h /opt/midad-data/midad.db
# If >100 MB → consider archiving old sales
```

**B) Check Memory Usage**:
```bash
free -h
# Available should be >100 MB
```

**C) Restart Service**:
```bash
sudo systemctl restart midad
```

---

### Security Concerns

**App Accessible to Anyone**:

**Current State**: Anyone with `http://YOUR_VM_IP:8501` can access.

**Solutions**:

**A) IP Whitelist (Restrict to Your IP)**:
```bash
# Get your home IP
curl https://ifconfig.me

# Update firewall rule
gcloud compute firewall-rules update allow-streamlit \
    --source-ranges=YOUR_HOME_IP/32

# Now only your IP can access
```

**B) Setup Cloudflare Tunnel** (Recommended):
- Free HTTPS
- Password protection
- Professional domain name
- (This requires separate setup - beyond scope)

**C) Add Basic Auth to Streamlit**:
- Requires code changes
- Add login page
- Store credentials securely

---

### Data Loss Prevention

**Best Practices**:

1. **Never delete database manually**:
```bash
# ❌ DON'T DO THIS:
rm /opt/midad-data/midad.db

# ✅ Use reset_db.py with confirmation:
PRODUCTION=true uv run python reset_db.py
```

2. **Always backup before major changes**:
```bash
# Before updating code
cd /opt/midad
./scripts/backup.sh

# Then deploy
./scripts/deploy.sh
```

3. **Test locally first**:
```bash
# On your PC, not VM
git pull
uv run streamlit run app.py
# Test changes
# If broken, fix before deploying to VM
```

4. **Monitor logs after deployment**:
```bash
# After deploy
sudo journalctl -u midad -f
# Watch for errors for 2-3 minutes
```

---

## Additional Resources

### Useful Commands Cheat Sheet

```bash
# === Service Management ===
sudo systemctl start midad         # Start service
sudo systemctl stop midad          # Stop service
sudo systemctl restart midad       # Restart service
sudo systemctl status midad        # Check status
sudo systemctl enable midad        # Enable auto-start
sudo systemctl disable midad       # Disable auto-start

# === Logs ===
sudo journalctl -u midad -f        # Live tail
sudo journalctl -u midad -n 50     # Last 50 lines
sudo journalctl -u midad --since "1 hour ago"

# === Git ===
git status                         # Check changes
git pull origin main               # Pull latest
git log --oneline -n 10            # Recent commits
git diff                           # Show changes

# === Database ===
ls -lh /opt/midad-data/midad.db   # Check database
sqlite3 /opt/midad-data/midad.db ".tables"  # List tables
du -h /opt/midad-data/midad.db    # Database size

# === Backups ===
ls -lh /opt/backups/              # List local backups
./scripts/backup.sh               # Create backup now
./scripts/auto_sync_db.sh         # Sync to GitHub now

# === System ===
df -h                             # Disk usage
free -h                           # Memory usage
top                               # CPU/RAM monitor
sudo reboot                       # Restart VM
```

### File Locations Reference

```
=== Application ===
/opt/midad/                       # App code
/opt/midad/app.py                 # Main entry point
/opt/midad/src/                   # Source code
/opt/midad/scripts/               # Deployment scripts
/opt/midad/.venv/                 # Virtual environment

=== Data ===
/opt/midad-data/midad.db          # Production database
/opt/midad/data/midad.db          # Staging (for git sync)

=== Backups ===
/opt/backups/                     # Local backups (30 days)
gs://midad-backups-YOURNAME/      # GCS backups (30 days)

=== Logs ===
/opt/midad/logs/auto-sync.log     # Auto-sync cron log
/opt/midad/logs/backup.log        # Backup cron log
sudo journalctl -u midad          # Systemd service logs

=== Configuration ===
/etc/systemd/system/midad.service # Systemd service file
crontab -e                        # Cron jobs
/opt/midad/.streamlit/config.toml # Streamlit config
```

---

## Conclusion

**You now have**:
- ✅ Complete local development environment
- ✅ Production deployment on GCP VM
- ✅ Automatic backups (3 layers)
- ✅ Auto-sync to GitHub (every 6 hours)
- ✅ Health monitoring
- ✅ Disaster recovery procedures

**Next Steps**:
1. Use the app daily (record sales)
2. Monitor GitHub for auto-commits (verify backups working)
3. Test disaster recovery once (to confirm it works)
4. Consider adding domain + HTTPS (optional)
5. Consider adding authentication (optional)

**Support**:
- Check logs: `sudo journalctl -u midad -f`
- Check GitHub: New commits should appear every 6 hours
- Check backups: `/opt/backups/` should grow daily
- Health check: `http://YOUR_VM_IP:8501/99_health`

**Congratulations! Your production system is live!** 🎉