#!/bin/bash

# 🔄 Git Push All - Commit and push everything (code + database)
# Usage: ./scripts/git_push_all.sh "optional commit message"

set -e  # Exit on error

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔄 Git Push All - Starting...${NC}"
echo ""

# Change to repo directory
cd /opt/midad

# Check if we're in a git repo
if [ ! -d .git ]; then
    echo -e "${RED}❌ Error: Not a git repository${NC}"
    exit 1
fi

# Get current branch
BRANCH=$(git rev-parse --abbrev-ref HEAD)
echo -e "${BLUE}📍 Branch: ${BRANCH}${NC}"

# Check if there are any changes
if git diff-index --quiet HEAD --; then
    echo -e "${GREEN}✅ No changes to commit${NC}"
    echo -e "${YELLOW}📤 Pulling latest from GitHub...${NC}"
    git pull origin $BRANCH
    echo -e "${GREEN}✅ Up to date!${NC}"
    exit 0
fi

# Show what changed
echo -e "${YELLOW}📋 Changed files:${NC}"
git status --short
echo ""

# Get commit message (use parameter or default)
if [ -z "$1" ]; then
    COMMIT_MSG="sync: auto-commit from VM $(date '+%Y-%m-%d %H:%M:%S')"
else
    COMMIT_MSG="$1"
fi

# Stage all changes (code + database)
echo -e "${BLUE}📦 Staging all changes...${NC}"
git add -A

# Commit
echo -e "${BLUE}📝 Committing...${NC}"
git commit -m "$COMMIT_MSG"

# Pull latest (in case of remote changes)
echo -e "${BLUE}📥 Pulling latest from GitHub...${NC}"
git pull origin $BRANCH --rebase

# Push
echo -e "${BLUE}📤 Pushing to GitHub...${NC}"
git push origin $BRANCH

echo ""
echo -e "${GREEN}✅ Everything pushed to GitHub!${NC}"
echo -e "${GREEN}🎉 Local PC can now: git pull origin $BRANCH${NC}"
