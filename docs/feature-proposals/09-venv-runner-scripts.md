# Feature Proposal: Virtual Environment Runner Scripts

## Summary
Create convenience scripts (`venv-run.sh` and `venv-run.bat`) that automatically activate the virtual environment and execute commands, making it seamless for AI agents and developers to run Python commands in the correct environment.

## Problem Statement
Currently, AI agents (like Claude) and developers must remember to:
1. Manually activate the virtual environment before each Python command
2. Handle different activation commands for different platforms
3. Deal with activation state persistence issues in non-interactive shells
4. Remember the correct activation syntax for their platform

This leads to:
- **Common mistakes**: Running Python/pip commands outside venv
- **AI agent errors**: Claude forgetting to activate venv in new shell sessions
- **Platform confusion**: Windows vs Unix activation commands
- **Workflow friction**: Extra steps for every Python operation

## Proposed Solution

### 1. Create Platform-Specific Runner Scripts

#### Unix/Linux/Mac: `venv-run.sh`
```bash
#!/bin/bash
# Automatically runs commands in virtual environment context

VENV_DIR="venv"
if [ ! -d "$VENV_DIR" ]; then
    echo "Error: Virtual environment not found at $VENV_DIR"
    echo "Run: python -m venv $VENV_DIR"
    exit 1
fi

# Activate venv and run command
source "$VENV_DIR/bin/activate"
exec "$@"
```

#### Windows: `venv-run.bat`
```batch
@echo off
REM Automatically runs commands in virtual environment context

SET VENV_DIR=venv
IF NOT EXIST "%VENV_DIR%\Scripts\activate.bat" (
    echo Error: Virtual environment not found at %VENV_DIR%
    echo Run: python -m venv %VENV_DIR%
    exit /b 1
)

REM Activate venv and run command
call "%VENV_DIR%\Scripts\activate.bat"
%*
```

### 2. Enhanced Version with Features

#### Advanced `venv-run.sh`
```bash
#!/bin/bash
set -e

# Configuration
VENV_DIR="${VENV_DIR:-venv}"
PYTHON_MIN_VERSION="3.8"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if venv exists
if [ ! -d "$VENV_DIR" ]; then
    echo -e "${YELLOW}Virtual environment not found. Creating...${NC}"
    python3 -m venv "$VENV_DIR"
    source "$VENV_DIR/bin/activate"
    pip install --upgrade pip
    if [ -f "requirements.txt" ]; then
        echo -e "${GREEN}Installing requirements...${NC}"
        pip install -r requirements.txt
    fi
else
    source "$VENV_DIR/bin/activate"
fi

# Show active environment
echo -e "${GREEN}Using: $(which python) ($(python --version))${NC}"

# Execute command or start interactive shell
if [ $# -eq 0 ]; then
    echo -e "${YELLOW}No command provided. Starting interactive shell...${NC}"
    exec $SHELL
else
    exec "$@"
fi
```

### 3. Usage Examples

```bash
# Run Python script
./venv-run.sh python script.py

# Install package
./venv-run.sh pip install requests

# Run tests
./venv-run.sh pytest

# Start interactive Python
./venv-run.sh python

# Run any command in venv context
./venv-run.sh mypy src/

# For AI agents like Claude
./venv-run.sh python -c "import sys; print(sys.prefix)"
```

### 4. Integration with setup-smart.py

```python
def create_venv_runner_scripts(self) -> bool:
    """Create convenience scripts for running commands in venv."""

    # Unix/Linux/Mac script
    unix_script = '''#!/bin/bash
# Auto-generated script for running commands in virtual environment
set -e

VENV_DIR="${VENV_DIR:-venv}"

if [ ! -d "$VENV_DIR" ]; then
    echo "Error: Virtual environment not found at $VENV_DIR"
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
    source "$VENV_DIR/bin/activate"
    pip install --upgrade pip
    [ -f "requirements.txt" ] && pip install -r requirements.txt
else
    source "$VENV_DIR/bin/activate"
fi

if [ $# -eq 0 ]; then
    echo "Active Python: $(which python)"
    exec $SHELL
else
    exec "$@"
fi
'''

    # Windows script
    windows_script = '''@echo off
REM Auto-generated script for running commands in virtual environment

SET VENV_DIR=venv
IF NOT EXIST "%VENV_DIR%\\Scripts\\activate.bat" (
    echo Error: Virtual environment not found at %VENV_DIR%
    echo Creating virtual environment...
    python -m venv %VENV_DIR%
    call "%VENV_DIR%\\Scripts\\activate.bat"
    pip install --upgrade pip
    if exist requirements.txt pip install -r requirements.txt
) ELSE (
    call "%VENV_DIR%\\Scripts\\activate.bat"
)

if "%~1"=="" (
    echo Active Python:
    where python
    cmd /k
) else (
    %*
)
'''

    # Create scripts
    venv_run_sh = self.project_dir / "venv-run.sh"
    venv_run_bat = self.project_dir / "venv-run.bat"

    venv_run_sh.write_text(unix_script)
    venv_run_sh.chmod(0o755)  # Make executable

    venv_run_bat.write_text(windows_script)

    print("   ✅ Created venv runner scripts: venv-run.sh and venv-run.bat")
    print("   📝 Usage: ./venv-run.sh python script.py")

    return True
```

## Implementation Plan

### Phase 1: Create Script Templates
1. Design Unix/Linux/Mac shell script
2. Design Windows batch script
3. Add error handling and venv detection
4. Include auto-creation option

### Phase 2: Integrate with Setup
1. Update setup-smart.py to create scripts
2. Make scripts executable on Unix
3. Add to .gitignore if needed
4. Document in setup output

### Phase 3: AI Agent Instructions
1. Update CLAUDE-CORE.md with script usage
2. Teach agents to use `./venv-run.sh` prefix
3. Add examples to documentation
4. Update Python expert agent

## Success Criteria
- [ ] Scripts created automatically during Python project setup
- [ ] Scripts work on both Windows and Unix platforms
- [ ] AI agents use scripts instead of manual activation
- [ ] Scripts handle missing venv gracefully
- [ ] Clear error messages guide users

## Risk Mitigation
- **Script permissions**: Ensure executable on Unix
- **Path issues**: Use relative paths consistently
- **Shell compatibility**: Test on bash, zsh, sh
- **Windows variations**: Test on cmd and PowerShell

## Technical Debt Considerations
- No TODOs in implementation
- Complete error handling
- Clear documentation
- Automated testing where possible

## Acceptance Criteria
- [ ] venv-run.sh works on Mac/Linux
- [ ] venv-run.bat works on Windows
- [ ] Scripts auto-create venv if missing
- [ ] Scripts install requirements.txt if present
- [ ] AI agents successfully use scripts
- [ ] Documentation clearly explains usage

## Timeline
- Day 1: Create and test script templates
- Day 2: Integrate with setup-smart.py
- Day 3: Update documentation and agents
- Day 4: Testing and refinement

## Related Issues
- AI agents forgetting to activate venv
- Cross-platform activation differences
- Non-interactive shell activation issues
- Workflow friction in Python development
