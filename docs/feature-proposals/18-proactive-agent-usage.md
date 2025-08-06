# Feature Proposal: Proactive Agent Usage and Python Project Essentials

**Feature ID**: 18
**Title**: Make Framework Proactively Use Agents and Create Python Essentials
**Author**: AI Assistant
**Date**: 2025-08-05
**Status**: Proposed
**Target Branch**: `feature/proactive-agent-usage`

## Executive Summary

The framework currently doesn't proactively create essential files (requirements.txt, updated README) for Python projects, nor does it actively encourage using team agents. This proposal makes the framework more assertive about agent collaboration and ensures Python projects start with proper structure.

## Motivation

### Current Problems

1. **Missing Python Essentials**:
   - No `requirements.txt` created by default
   - README.md not updated with project-specific information
   - No `.gitignore` entries for Python
   - Missing `setup.py` or `pyproject.toml`

2. **Missing MANDATORY Architecture Directory**:
   - Framework FORBIDS code without architecture docs
   - But doesn't create `docs/architecture/` directory
   - Validation fails immediately on new projects
   - Users blocked from starting work

3. **Passive Agent Usage**:
   - Framework mentions agents but doesn't actively push their use
   - AI assistants don't naturally reach for team agents
   - No "agent-first" mindset in instructions

4. **Lack of Initial Structure**:
   - First commit often missing essential files
   - No guidance on Python best practices
   - No automated dependency tracking

### Impact
- Python projects start incomplete
- Developers miss the value of agent collaboration
- Technical debt accumulates from day one

## Proposed Solution

### 1. Create MANDATORY Directories First

```python
# In setup-smart.py - MUST create these directories
def create_mandatory_structure(self):
    """Create ALL mandatory directories to prevent validation failures"""

    mandatory_dirs = [
        "docs/architecture",          # REQUIRED for validation
        "docs/architecture/decisions", # For ADRs
        "docs/feature-proposals",     # Already created
        "retrospectives",             # Already created
        "plan",                       # Already created
        "tests",                      # For Python projects
        "src",                        # For Python projects
    ]

    for dir_path in mandatory_dirs:
        (self.project_dir / dir_path).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created {dir_path}/")

    # Create placeholder architecture docs for each level
    if self.sdlc_level == 'prototype':
        # Create minimal docs
        (self.project_dir / "docs" / "feature-intent.md").touch()
        (self.project_dir / "docs" / "basic-design.md").touch()
    else:  # production/enterprise
        # Create all 6 architecture doc templates
        arch_docs = [
            "requirements-traceability-matrix.md",
            "what-if-analysis.md",
            "architecture-decision-record.md",
            "system-invariants.md",
            "integration-design.md",
            "failure-mode-analysis.md"
        ]
        for doc in arch_docs:
            doc_path = self.project_dir / "docs" / "architecture" / doc
            doc_path.write_text(f"# {doc.replace('-', ' ').title()}\n\n<!-- TODO: Complete this document -->\n")
```

### 2. Python Project Detection and Setup

```python
# In setup-smart.py
def setup_python_project(self):
    """Create essential Python project files"""

    # Create requirements.txt with common dependencies
    requirements = """# Core dependencies
pytest>=7.0.0
pytest-cov>=4.0.0
black>=23.0.0
flake8>=6.0.0
mypy>=1.0.0
pre-commit>=3.0.0

# Add your project dependencies below:
"""

    # Create pyproject.toml
    pyproject = f"""[tool.black]
line-length = 88
target-version = ['py39']

[tool.mypy]
python_version = "3.9"
warn_return_any = true
warn_unused_configs = true

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
addopts = "-v --cov=src --cov-report=html"

[build-system]
requires = ["setuptools>=45", "wheel"]
build-backend = "setuptools.build_meta"
"""

    # Update README with Python-specific sections
    readme_update = f"""
## Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd {self.project_name}

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .
```

## Development

```bash
# Run tests
pytest

# Format code
black .

# Lint
flake8

# Type check
mypy .
```

## Project Structure

```
{self.project_name}/
├── src/
│   └── {self.project_name.replace('-', '_')}/
│       └── __init__.py
├── tests/
│   └── test_{self.project_name.replace('-', '_')}.py
├── docs/
├── requirements.txt
├── setup.py
├── pyproject.toml
└── README.md
```
"""
```

### 2. Aggressive Agent Promotion in CLAUDE.md

Update CLAUDE-CORE-PROGRESSIVE.md with:

```markdown
## 🚨 MANDATORY: Use Team Agents IMMEDIATELY

**YOU MUST PROACTIVELY USE AGENTS FOR EVERY TASK**

### Starting ANY Work:
```
STOP! Before writing ANY code or making ANY decision:
1. IMMEDIATELY invoke sdlc-enforcer to check compliance
2. ALWAYS consult solution-architect for design decisions
3. MUST use test-manager for test planning
4. REQUIRED to use critical-goal-reviewer after implementation
```

### Agent Usage is NOT Optional:
- See a bug? → IMMEDIATELY invoke critical-goal-reviewer
- Writing code? → FIRST consult solution-architect
- Need tests? → MUST use test-manager
- Deployment? → REQUIRED sre-specialist approval

### Example Workflow:
User: "Add user authentication"
You: "I'll immediately engage our team of specialist agents to ensure we build this correctly."
*Invokes solution-architect for design*
*Invokes security-architect for auth patterns*
*Invokes test-manager for test strategy*

DO NOT proceed without agent consultation!
```

### 3. Auto-invoke Agents for Python Projects

Add to agent-decision-tree.py:

```python
PYTHON_PROJECT_AGENTS = {
    'initial_setup': [
        'sdlc-enforcer',  # Ensure SDLC compliance
        'python-expert',  # Python best practices
        'test-manager',   # Testing strategy
        'devops-specialist'  # CI/CD setup
    ],
    'new_feature': [
        'solution-architect',
        'python-expert',
        'test-manager',
        'critical-goal-reviewer'
    ]
}
```

### 4. First Commit Automation

```python
def create_first_commit(self):
    """Create a proper first commit with all essentials"""

    # Stage all essential files
    files_to_commit = [
        'README.md',
        'requirements.txt',
        'setup.py',
        'pyproject.toml',
        '.gitignore',
        'src/__init__.py',
        'tests/test_basic.py',
        'CLAUDE.md',
        '.pre-commit-config.yaml'
    ]

    # Create comprehensive first commit
    commit_message = f"""Initial commit: {self.project_name} with AI-First SDLC

- Complete Python project structure
- AI-First SDLC framework integrated
- Testing and linting configured
- Agent team ready for collaboration
- Requirements and dependencies tracked

This project uses AI agents for all development decisions.
Run 'python tools/agent-help.py' to see available agents.

🤖 Generated with AI-First SDLC Framework
"""
```

## Implementation Plan

### Phase 1: Python Essentials (Immediate)
1. Update setup-smart.py to detect Python projects
2. Create all essential Python files
3. Update README.md with Python-specific content
4. Add Python-specific .gitignore entries

### Phase 2: Agent Assertion (Week 1)
1. Update CLAUDE instructions to mandate agent usage
2. Add "agent-first" examples throughout docs
3. Create agent auto-invocation patterns
4. Add agent usage tracking

### Phase 3: Behavioral Changes (Week 2)
1. Add prompts that remind about agents
2. Create agent suggestion system
3. Build agent usage metrics
4. Add "agent score" to validation

## Success Metrics

1. **File Creation**: 100% of Python projects have requirements.txt
2. **Agent Usage**: 5+ agent invocations per feature
3. **First Commit**: Contains all essential files
4. **README Quality**: Project-specific, not generic

## Example Usage

```bash
# Setup creates everything
python setup-smart.py "Python API for user management" --level production

# First commit includes:
- README.md (updated with project info)
- requirements.txt (with dependencies)
- setup.py (properly configured)
- Full project structure
- Agent recommendations

# AI Assistant behavior:
User: "Add database models"
Assistant: "I'll engage our team to design this properly:
- First, consulting solution-architect for design
- Then python-expert for SQLAlchemy patterns
- And test-manager for testing strategy"
*Actually invokes all agents*
```

## Risks and Mitigation

1. **Over-aggressive**: Mitigate by making it helpful, not annoying
2. **Generic files**: Use project analysis to customize
3. **Agent fatigue**: Show value, not just process

## Alternatives Considered

1. **Gentle suggestions**: Rejected - doesn't change behavior
2. **Optional templates**: Rejected - won't be used
3. **Post-setup reminders**: Rejected - too late

## Conclusion

This proposal transforms the framework from passive to proactive, ensuring Python projects start correctly and AI assistants actively collaborate with specialist agents. The key is making agent usage feel natural and valuable, not forced.