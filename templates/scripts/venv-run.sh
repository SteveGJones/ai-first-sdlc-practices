#!/bin/bash
# Virtual Environment Runner for AI-First SDLC Python Projects
# Auto-activates virtual environment and runs commands in that context
# Perfect for AI agents like Claude to run Python commands safely

set -e

# Configuration
VENV_DIR="${VENV_DIR:-venv}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output (disabled if not terminal)
if [ -t 1 ]; then
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    BLUE='\033[0;34m'
    NC='\033[0m' # No Color
else
    RED=''
    GREEN=''
    YELLOW=''
    BLUE=''
    NC=''
fi

# Helper functions
error() {
    echo -e "${RED}❌ Error: $1${NC}" >&2
    exit 1
}

info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Check Python availability
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

PYTHON_CMD=$(find_python) || error "Python 3.7+ not found. Please install Python."

# Check if venv exists, create if needed
if [ ! -d "$VENV_DIR" ]; then
    warning "Virtual environment not found at '$VENV_DIR'"
    info "Creating virtual environment..."

    $PYTHON_CMD -m venv "$VENV_DIR" || error "Failed to create virtual environment"

    # Activate for initial setup
    source "$VENV_DIR/bin/activate"

    # Upgrade pip
    info "Upgrading pip..."
    pip install --upgrade pip --quiet

    # Install requirements if exists
    if [ -f "requirements.txt" ]; then
        info "Installing requirements.txt..."
        pip install -r requirements.txt
        success "Requirements installed"
    fi

    # Install dev requirements if exists
    if [ -f "requirements-dev.txt" ]; then
        info "Installing requirements-dev.txt..."
        pip install -r requirements-dev.txt
        success "Dev requirements installed"
    fi

    success "Virtual environment created and configured"
else
    # Just activate existing venv
    source "$VENV_DIR/bin/activate"
fi

# Show environment info if verbose or no args
if [ "$1" = "--info" ] || [ "$VENV_VERBOSE" = "1" ]; then
    info "Python: $(which python)"
    info "Version: $(python --version)"
    info "Venv: $VIRTUAL_ENV"
fi

# Execute command or start shell
if [ $# -eq 0 ]; then
    warning "No command provided. Starting interactive shell with venv activated..."
    info "Python: $(which python)"
    info "Exit shell to deactivate virtual environment"
    exec $SHELL
else
    # Remove --info flag if present
    if [ "$1" = "--info" ]; then
        shift
    fi

    # Execute the command
    exec "$@"
fi
