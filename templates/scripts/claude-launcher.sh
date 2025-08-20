#!/bin/bash
# AI-First SDLC Claude Launcher
# One command to set up everything and start Claude Code
# Usage: ./bin/claude

set -e

# Determine project root (parent of bin directory)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PROJECT_NAME="$(basename "$PROJECT_ROOT")"

# Configuration
VENV_DIR="${VENV_DIR:-$PROJECT_ROOT/venv}"

# Colors for output (disabled if not terminal)
if [ -t 1 ]; then
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    BLUE='\033[0;34m'
    CYAN='\033[0;36m'
    BOLD='\033[1m'
    NC='\033[0m' # No Color
else
    RED=''
    GREEN=''
    YELLOW=''
    BLUE=''
    CYAN=''
    BOLD=''
    NC=''
fi

# Banner
echo ""
echo -e "${BLUE}${BOLD}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}${BOLD}║          🤖 AI-First SDLC Claude Launcher            ║${NC}"
echo -e "${BLUE}${BOLD}╚══════════════════════════════════════════════════════╝${NC}"
echo ""

# Change to project directory
cd "$PROJECT_ROOT"
echo -e "${CYAN}📁 Project:${NC} ${BOLD}$PROJECT_NAME${NC}"
echo -e "${CYAN}📍 Location:${NC} $PROJECT_ROOT"

# Python detection
find_python() {
    for cmd in python3 python; do
        if command -v $cmd &> /dev/null; then
            if $cmd -c "import sys; sys.exit(0 if sys.version_info >= (3, 7) else 1)" 2>/dev/null; then
                echo $cmd
                return 0
            fi
        fi
    done
    return 1
}

# Only set up Python venv if this is a Python project
if [ -f "requirements.txt" ] || [ -f "setup.py" ] || [ -f "pyproject.toml" ] || [ -f "Pipfile" ]; then
    echo -e "${CYAN}🐍 Python project detected${NC}"

    PYTHON_CMD=$(find_python) || {
        echo -e "${RED}❌ Python 3.7+ not found${NC}"
        echo "Please install Python from https://python.org"
        exit 1
    }

    # Check/create virtual environment
    if [ ! -d "$VENV_DIR" ]; then
        echo -e "${YELLOW}📦 Creating virtual environment...${NC}"
        $PYTHON_CMD -m venv "$VENV_DIR"
        source "$VENV_DIR/bin/activate"

        echo -e "${YELLOW}⬆️  Upgrading pip...${NC}"
        pip install --upgrade pip --quiet

        if [ -f "requirements.txt" ]; then
            echo -e "${YELLOW}📚 Installing requirements...${NC}"
            pip install -r requirements.txt
        fi

        if [ -f "requirements-dev.txt" ]; then
            echo -e "${YELLOW}🔧 Installing dev requirements...${NC}"
            pip install -r requirements-dev.txt
        fi

        echo -e "${GREEN}✅ Virtual environment ready${NC}"
    else
        source "$VENV_DIR/bin/activate"
        echo -e "${GREEN}✅ Virtual environment activated${NC}"
    fi

    echo -e "${CYAN}🔧 Python:${NC} $(which python) ($(python --version 2>&1))"
else
    echo -e "${CYAN}📂 Non-Python project${NC}"
fi

# Check for Claude CLI
if ! command -v claude &> /dev/null; then
    echo ""
    echo -e "${RED}❌ Claude CLI not found${NC}"
    echo ""
    echo -e "${YELLOW}Please install Claude Code:${NC}"
    echo ""
    echo "  🍎 macOS:"
    echo "     brew install claude"
    echo ""
    echo "  🐧 Linux:"
    echo "     Visit https://claude.ai/download"
    echo ""
    echo "  🪟 Windows:"
    echo "     Visit https://claude.ai/download"
    echo ""
    exit 1
fi

# Display helpful context
echo ""
echo -e "${GREEN}${BOLD}Ready to start Claude Code!${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${YELLOW}💡 Quick tips:${NC}"
echo "  • Claude will start in: $PROJECT_ROOT"
if [ -f "requirements.txt" ]; then
    echo "  • Python environment is activated"
    echo "  • All dependencies from requirements.txt are installed"
fi
echo "  • Type 'exit' in Claude to return here"
echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Launch Claude Code
echo -e "${BLUE}${BOLD}🚀 Launching Claude Code...${NC}"
echo ""

# Start Claude in the project directory
# The exec replaces this script's process with Claude
exec claude "$PROJECT_ROOT"
