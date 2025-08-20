# Feature Proposal: Python Virtual Environment as Default

## Summary
Establish virtual environment creation as the default behavior for Python projects in the AI-First SDLC framework, with options to override when needed.

## Problem Statement
Currently, the framework doesn't enforce or encourage virtual environment usage for Python projects, leading to:
1. **Dependency conflicts** between projects
2. **Polluted global Python environments**
3. **Reproducibility issues** across team members
4. **Security risks** from uncontrolled package installations
5. **Inconsistent development environments**

Virtual environments are a Python best practice but are often overlooked, especially by AI agents who may install packages globally.

## Proposed Solution

### 1. Automatic Virtual Environment Setup
When detecting a Python project, the framework will:
```python
# Default behavior
if is_python_project and not has_virtual_env:
    create_virtual_environment()
    activate_in_instructions()
```

### 2. Detection Logic
```python
def detect_python_project():
    """Detect if this is a Python project."""
    indicators = [
        'requirements.txt',
        'setup.py',
        'pyproject.toml',
        'Pipfile',
        '*.py files',
        'conda.yml',
        'environment.yml'
    ]
    return any(exists(indicator) for indicator in indicators)

def has_virtual_env():
    """Check if virtual environment already exists."""
    venv_indicators = [
        'venv/',
        '.venv/',
        'env/',
        '.env/',
        'virtualenv/',
        '.virtualenv/',
        os.environ.get('VIRTUAL_ENV'),
        'Pipfile.lock',  # Pipenv
        'poetry.lock'    # Poetry
    ]
    return any(exists(indicator) for indicator in venv_indicators)
```

### 3. Configuration Options
Add to framework settings:
```yaml
python:
  virtual_environment:
    enabled: true  # Default
    name: "venv"   # Default directory name
    python_version: "auto"  # Or specific like "3.9"
    upgrade_pip: true
    install_requirements: true
    
  # Override options
  skip_venv_creation: false  # Set true to disable
  use_system_packages: false  # --system-site-packages flag
```

### 4. AI Agent Instructions
Update CLAUDE.md and agent instructions:
```markdown
## Python Project Setup

When working with Python projects, ALWAYS:
1. Check for existing virtual environment
2. If none exists, create one: `python -m venv venv`
3. Activate before any Python operations:
   - Linux/Mac: `source venv/bin/activate`
   - Windows: `venv\Scripts\activate`
4. Install dependencies within venv: `pip install -r requirements.txt`
5. Add venv/ to .gitignore if not present

NEVER:
- Install packages globally without explicit user permission
- Delete existing virtual environments without asking
- Assume venv is activated (always check)
```

### 5. Setup Script Enhancement
```python
# In setup-smart.py
def setup_python_virtual_env(project_path, skip_venv=False):
    """Set up Python virtual environment unless explicitly disabled."""
    
    if skip_venv:
        print("ℹ️ Skipping virtual environment creation (--no-venv flag)")
        return
    
    if not is_python_project(project_path):
        return
    
    if has_virtual_env(project_path):
        print("✓ Virtual environment already exists")
        return
    
    print("🐍 Setting up Python virtual environment...")
    
    # Determine Python executable
    python_cmd = find_python_executable()
    
    # Create venv
    venv_path = os.path.join(project_path, 'venv')
    subprocess.run([python_cmd, '-m', 'venv', venv_path], check=True)
    
    # Upgrade pip
    pip_path = os.path.join(venv_path, 'bin', 'pip') if os.name != 'nt' else os.path.join(venv_path, 'Scripts', 'pip')
    subprocess.run([pip_path, 'install', '--upgrade', 'pip'], check=True)
    
    # Install requirements if exists
    req_file = os.path.join(project_path, 'requirements.txt')
    if os.path.exists(req_file):
        subprocess.run([pip_path, 'install', '-r', req_file], check=True)
    
    # Update .gitignore
    update_gitignore(project_path, ['venv/', '.venv/', '*.pyc', '__pycache__/'])
    
    print("✓ Virtual environment created at 'venv/'")
    print("  Activate with: source venv/bin/activate")
```

### 6. CLI Arguments
```python
# Add to setup-smart.py arguments
parser.add_argument('--no-venv', action='store_true',
                    help='Skip virtual environment creation for Python projects')
parser.add_argument('--venv-name', default='venv',
                    help='Name for virtual environment directory (default: venv)')
parser.add_argument('--python', default='python3',
                    help='Python executable to use (default: python3)')
```

## Implementation Plan

### Phase 1: Core Implementation
1. Update setup-smart.py with venv creation logic
2. Add detection functions for Python projects
3. Implement venv creation with proper error handling
4. Update .gitignore management

### Phase 2: Agent Integration
1. Update Python-related agents to check for venv
2. Add venv activation to agent instructions
3. Create warnings when venv not detected

### Phase 3: Documentation
1. Update CLAUDE.md with venv instructions
2. Add Python best practices guide
3. Create troubleshooting section

## Success Criteria
- [ ] Python projects automatically get virtual environments
- [ ] AI agents activate venv before Python operations
- [ ] Clear opt-out mechanism with --no-venv flag
- [ ] No disruption to non-Python projects
- [ ] Existing venvs are respected and not overwritten

## Risk Mitigation
- **Existing environments**: Never delete without explicit permission
- **Different tools**: Detect Poetry, Pipenv, Conda environments
- **Corporate environments**: Provide --no-venv flag for restricted systems
- **Windows compatibility**: Test on Windows, Mac, and Linux

## Technical Debt Considerations
- No TODOs in implementation
- Complete error handling for venv creation failures
- Clear logging of venv operations
- Rollback capability if venv creation fails

## Acceptance Criteria
- [ ] setup-smart.py creates venv for Python projects by default
- [ ] --no-venv flag successfully skips creation
- [ ] Existing virtual environments are detected and preserved
- [ ] .gitignore is updated appropriately
- [ ] AI agents receive clear instructions about venv usage
- [ ] Works on Windows, Mac, and Linux

## Timeline
- Day 1: Implement core venv creation logic
- Day 2: Add detection and configuration options
- Day 3: Update agents and documentation
- Day 4: Testing across platforms
- Day 5: Release and documentation

## Related Issues
- Dependency conflicts in Python projects
- Global package pollution
- Inconsistent development environments
- AI agents installing packages globally