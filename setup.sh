#!/usr/bin/env bash
#
# AI-First SDLC Framework Setup Script
# One-liner installer for the framework
#
# Usage:
#   curl -L https://raw.githubusercontent.com/SteveGJones/ai-first-sdlc-practices/main/setup.sh | bash
#   curl -L https://raw.githubusercontent.com/SteveGJones/ai-first-sdlc-practices/main/setup.sh | bash -s -- "building a todo app"

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
GITHUB_REPO="SteveGJones/ai-first-sdlc-practices"
GITHUB_BRANCH="${AI_SDLC_VERSION:-main}"
SETUP_SCRIPT_URL="https://raw.githubusercontent.com/${GITHUB_REPO}/${GITHUB_BRANCH}/setup-smart.py"

# Parse arguments (purpose of the project)
PROJECT_PURPOSE="${1:-AI-assisted software development}"

echo -e "${GREEN}🚀 AI-First SDLC Framework Setup${NC}"
echo "=================================================="
echo "Repository: https://github.com/${GITHUB_REPO}"
echo "Version: ${GITHUB_BRANCH}"
echo "Purpose: ${PROJECT_PURPOSE}"
echo ""

# Check for Python 3
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Error: Python 3 is required but not found${NC}"
    echo "Please install Python 3.7 or higher and try again"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo -e "${GREEN}✅ Found Python ${PYTHON_VERSION}${NC}"

# Check for git
if ! command -v git &> /dev/null; then
    echo -e "${YELLOW}⚠️  Warning: Git is not installed${NC}"
    echo "Git is recommended for version control"
    read -p "Continue anyway? [y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Create temporary directory for setup script
TEMP_DIR=$(mktemp -d)
trap "rm -rf ${TEMP_DIR}" EXIT

echo ""
echo "📥 Downloading setup script..."

# Download the setup script
if command -v curl &> /dev/null; then
    curl -sL "${SETUP_SCRIPT_URL}" -o "${TEMP_DIR}/setup-smart.py"
elif command -v wget &> /dev/null; then
    wget -q "${SETUP_SCRIPT_URL}" -O "${TEMP_DIR}/setup-smart.py"
else
    echo -e "${RED}❌ Error: Neither curl nor wget found${NC}"
    echo "Please install curl or wget and try again"
    exit 1
fi

# Check if download was successful
if [ ! -f "${TEMP_DIR}/setup-smart.py" ]; then
    echo -e "${RED}❌ Error: Failed to download setup script${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Downloaded setup script${NC}"
echo ""

# Make it executable
chmod +x "${TEMP_DIR}/setup-smart.py"

# Check if we're in a git repository and on main branch
if command -v git &> /dev/null && git rev-parse --git-dir > /dev/null 2>&1; then
    CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
    if [[ "$CURRENT_BRANCH" == "main" || "$CURRENT_BRANCH" == "master" ]]; then
        echo -e "${YELLOW}⚠️  Warning: You're on the ${CURRENT_BRANCH} branch${NC}"
        echo "The setup will create an 'ai-first-kick-start' branch"
        echo ""
    fi
fi

# Run the setup script
echo "🔧 Running setup..."
echo "=================================================="
echo ""

python3 "${TEMP_DIR}/setup-smart.py" "${PROJECT_PURPOSE}"

SETUP_EXIT_CODE=$?

if [ $SETUP_EXIT_CODE -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✅ Setup completed successfully!${NC}"
    echo ""
    echo "🎯 Quick Start Commands:"
    echo "  python tools/progress-tracker.py list    # View tasks"
    echo "  python tools/validate-pipeline.py        # Run validation"
    echo "  git status                               # Check changes"
    echo ""
else
    echo ""
    echo -e "${RED}❌ Setup failed with exit code ${SETUP_EXIT_CODE}${NC}"
    echo "Please check the errors above and try again"
    exit $SETUP_EXIT_CODE
fi

# Special message for AI agents
if [[ "${PROJECT_PURPOSE}" == *"start new project using"* ]] || [[ "${AI_AGENT}" == "true" ]]; then
    echo "🤖 AI Agent Instructions:"
    echo "1. You are now on the 'ai-first-kick-start' branch"
    echo "2. Review docs/feature-proposals/00-ai-first-setup.md"
    echo "3. Customize CLAUDE.md with project-specific details"
    echo "4. Complete setup tasks listed in progress tracker"
    echo "5. Commit and push when ready"
fi