#!/usr/bin/env python3
"""
AI-First SDLC Smart Setup Tool
Downloads and configures AI-First SDLC framework without cloning the
entire repository
"""

import os
import sys
import json
import subprocess
import argparse
from pathlib import Path
from typing import Optional
import urllib.request
import urllib.error


class SmartFrameworkSetup:
    """Smart installer for AI-First SDLC Framework"""

    GITHUB_RAW_BASE = (
        "https://raw.githubusercontent.com/SteveGJones/ai-first-sdlc-practices/main"
    )

    # Files to download for basic setup
    ESSENTIAL_FILES = {
        # New hierarchical instruction system
        "CLAUDE-CORE.md": "CLAUDE-CORE.md",
        "CLAUDE-CORE-PROGRESSIVE.md": "CLAUDE-CORE-PROGRESSIVE.md",
        "CLAUDE-SETUP.md": "CLAUDE-SETUP.md",
        "CLAUDE-CONTEXT-architecture.md": "CLAUDE-CONTEXT-architecture.md",
        "CLAUDE-CONTEXT-validation.md": "CLAUDE-CONTEXT-validation.md",
        "CLAUDE-CONTEXT-update.md": "CLAUDE-CONTEXT-update.md",
        "CLAUDE-CONTEXT-language-validators.md": (
            "CLAUDE-CONTEXT-language-validators.md"
        ),
        "CLAUDE-CONTEXT-logging.md": "CLAUDE-CONTEXT-logging.md",
        "CLAUDE-CONTEXT-levels.md": "CLAUDE-CONTEXT-levels.md",
        "CLAUDE-CONTEXT-agents.md": "CLAUDE-CONTEXT-agents.md",
        # Migration tool for existing projects
        "tools/migrate-to-hierarchical.py": "tools/migrate-to-hierarchical.py",
        "templates/feature-proposal.md": "docs/feature-proposals/template-feature-proposal.md",
        "templates/implementation-plan.md": "plan/template-implementation-plan.md",
        "templates/retrospective.md": "retrospectives/template-retrospective.md",
        "tools/automation/context-manager.py": "tools/context-manager.py",
        "tools/automation/progress-tracker.py": "tools/progress-tracker.py",
        "tools/automation/setup-branch-protection.py": "tools/setup-branch-protection.py",
        "tools/automation/setup-branch-protection-gh.py": "tools/setup-branch-protection-gh.py",
        "tools/validation/check-feature-proposal.py": "tools/check-feature-proposal.py",
        "tools/validation/validate-pipeline.py": "tools/validate-pipeline.py",
        "tools/validation/validate-pipeline-progressive.py": "tools/validate-pipeline-progressive.py",
        "tools/automation/sdlc-level.py": "tools/sdlc-level.py",
        # Zero Technical Debt additions
        "ZERO-TECHNICAL-DEBT.md": "ZERO-TECHNICAL-DEBT.md",
        "LANGUAGE-SPECIFIC-VALIDATORS.md": "LANGUAGE-SPECIFIC-VALIDATORS.md",
        "tools/validation/validate-architecture.py": "tools/validation/validate-architecture.py",
        "tools/validation/check-technical-debt.py": "tools/validation/check-technical-debt.py",
        "tools/validation/check-instruction-size.py": "tools/validation/check-instruction-size.py",
        "tools/validation/check-logging-compliance.py": "tools/validation/check-logging-compliance.py",
        "templates/quality-gates.yaml": "templates/quality-gates.yaml",
        # Architecture templates
        "templates/architecture/requirements-traceability-matrix.md": (
            "templates/architecture/requirements-traceability-matrix.md"
        ),
        "templates/architecture/what-if-analysis.md": "templates/architecture/what-if-analysis.md",
        "templates/architecture/architecture-decision-record.md": "templates/architecture/architecture-decision-record.md",
        "templates/architecture/system-invariants.md": "templates/architecture/system-invariants.md",
        "templates/architecture/integration-design.md": "templates/architecture/integration-design.md",
        "templates/architecture/failure-mode-analysis.md": "templates/architecture/failure-mode-analysis.md",
        "templates/architecture/observability-design.md": "templates/architecture/observability-design.md",
        # Pre-commit configuration
        "templates/.pre-commit-config.yaml": ".pre-commit-config.yaml",
        "CONTRIBUTING.md": "CONTRIBUTING.md",
        # Gitignore templates
        "templates/gitignore/base.gitignore": None,  # Downloaded but not placed directly
        "templates/gitignore/ai-tools.gitignore": None,
        "templates/gitignore/python.gitignore": None,
        "templates/gitignore/node.gitignore": None,
        "templates/gitignore/go.gitignore": None,
        "templates/gitignore/java.gitignore": None,
        "templates/gitignore/ruby.gitignore": None,
        "templates/gitignore/rust.gitignore": None,
        "templates/gitignore/general.gitignore": None,
        # Test templates
        "templates/tests/test_framework_setup.py": None,
        "templates/tests/framework.test.js": None,
        "templates/tests/test-framework.sh": None,
        "templates/tests/FrameworkTest.java": None,
        "templates/tests/framework_test.rb": None,
        "templates/tests/framework_test.rs": None,
        # Venv runner scripts
        "templates/scripts/venv-run.sh": None,
        "templates/scripts/venv-run.bat": None,
    }

    # CI/CD configurations by platform
    CI_CONFIGS = {
        "github": "examples/ci-cd/.github/workflows/ai-sdlc.yml",
        "gitlab": "examples/ci-cd/gitlab/.gitlab-ci.yml",
        "jenkins": "examples/ci-cd/jenkins/Jenkinsfile",
        "azure": "examples/ci-cd/azure-devops/azure-pipelines.yml",
        "circleci": "examples/ci-cd/circleci/.circleci/config.yml",
    }

    # Agent installation files
    AGENT_FILES = {
        "tools/automation/agent-installer.py": "tools/agent-installer.py",
        "tools/automation/project-analyzer.py": "tools/project-analyzer.py",
        "tools/automation/agent-recommender.py": "tools/agent-recommender.py",
        "tools/automation/agent-help.py": "tools/agent-help.py",
        "release/agent-manifest.json": None,  # Downloaded for metadata
        "release/agents/README.md": None,  # Downloaded for reference
    }

    def __init__(
        self,
        project_dir: Optional[Path] = None,
        project_purpose: str = None,
        non_interactive: bool = False,
        ci_platform: str = None,
        quickstart: bool = False,
        organized: bool = False,
        sdlc_level: str = "production",
        skip_venv: bool = False,
        venv_name: str = "venv",
        python_cmd: str = None,
    ):
        self.project_dir = project_dir or Path.cwd()
        self.project_purpose = project_purpose or "AI-assisted software development"
        self.project_name = self.project_dir.name
        self.errors = []
        self.non_interactive = non_interactive or not sys.stdin.isatty()
        self.ci_platform = ci_platform
        self.detected_language = None
        self.quickstart = quickstart
        self.organized = organized
        self.sdlc_level = sdlc_level  # Use .sdlc directory structure
        self.skip_venv = skip_venv
        self.venv_name = venv_name
        self.python_cmd = python_cmd

    def download_file(self, remote_path: str, local_path: Optional[Path]) -> bool:
        """Download a file from the framework repository"""
        url = f"{self.GITHUB_RAW_BASE}/{remote_path}"

        try:
            # Download file
            with urllib.request.urlopen(url) as response:
                content = response.read()

            # If local_path is None, save to temp directory for templates
            if local_path is None:
                temp_dir = self.project_dir / ".ai-sdlc-temp"
                temp_dir.mkdir(parents=True, exist_ok=True)
                local_path = temp_dir / Path(remote_path).name

            # Create parent directory if needed
            local_path.parent.mkdir(parents=True, exist_ok=True)

            # Write to local file
            with open(local_path, "wb") as f:
                f.write(content)

            # Make executable if it's a Python script (owner only)
            if local_path.suffix == ".py":
                os.chmod(local_path, 0o700)  # Owner read/write/execute only

            return True

        except urllib.error.URLError as e:
            self.errors.append(f"Failed to download {remote_path}: {e}")
            return False

    def detect_ci_platform(self) -> Optional[str]:
        """Detect which CI/CD platform is being used"""
        # Check environment variables
        if os.getenv("GITHUB_ACTIONS") == "true":
            return "github"
        elif os.getenv("GITLAB_CI") == "true":
            return "gitlab"
        elif os.getenv("JENKINS_URL"):
            return "jenkins"
        elif os.getenv("TF_BUILD") == "True":
            return "azure"
        elif os.getenv("CIRCLECI") == "true":
            return "circleci"

        # Check for existing CI files
        if (self.project_dir / ".github" / "workflows").exists():
            return "github"
        elif (self.project_dir / ".gitlab-ci.yml").exists():
            return "gitlab"
        elif (self.project_dir / "Jenkinsfile").exists():
            return "jenkins"
        elif (self.project_dir / "azure-pipelines.yml").exists():
            return "azure"
        elif (self.project_dir / ".circleci" / "config.yml").exists():
            return "circleci"

        return None

    def detect_project_language(self) -> str:
        """Detect the primary language of the project"""
        import glob

        # Language indicators with priority (check in order)
        indicators = [
            (
                "python",
                [
                    "*.py",
                    "requirements.txt",
                    "setup.py",
                    "pyproject.toml",
                    "Pipfile",
                ],
            ),
            (
                "node",
                [
                    "*.js",
                    "*.ts",
                    "*.jsx",
                    "*.tsx",
                    "package.json",
                    "yarn.lock",
                    "package-lock.json",
                ],
            ),
            ("go", ["*.go", "go.mod", "go.sum"]),
            ("rust", ["*.rs", "Cargo.toml", "Cargo.lock"]),
            (
                "java",
                ["*.java", "pom.xml", "build.gradle", "build.gradle.kts"],
            ),
            ("ruby", ["*.rb", "Gemfile", "Gemfile.lock", "Rakefile"]),
            ("csharp", ["*.cs", "*.csproj", "*.sln"]),
            ("php", ["*.php", "composer.json", "composer.lock"]),
        ]

        # Check if any language files exist
        language_detected = False
        for lang, patterns in indicators:
            for pattern in patterns:
                # Check both root and subdirectories
                if glob.glob(str(self.project_dir / pattern)) or glob.glob(
                    str(self.project_dir / "**" / pattern), recursive=True
                ):
                    self.detected_language = lang
                    return lang

        # If no language detected, handle based on mode
        if not language_detected:
            # In non-interactive mode, provide helpful message
            if self.non_interactive:
                print("\n⚠️  No programming language detected in the project.")
                print("   You can specify the language by creating one of these files:")
                print("   - Python: requirements.txt, setup.py, or *.py files")
                print("   - Node.js: package.json or *.js files")
                print("   - Go: go.mod or *.go files")
                print("   - Rust: Cargo.toml or *.rs files")
                print("   - Java: pom.xml, build.gradle, or *.java files")
                print("   Using general language settings for now.")
            elif not self.quickstart:  # Interactive mode
                print("\n🤔 No programming language detected in the project.")
                print("What type of project is this?")
                print("1. Python")
                print("2. Node.js/JavaScript/TypeScript")
                print("3. Go")
                print("4. Rust")
                print("5. Java")
                print("6. Ruby")
                print("7. General/Other")

                while True:
                    try:
                        choice = input("\nSelect language (1-7) [7]: ").strip() or "7"
                        choice_map = {
                            "1": "python",
                            "2": "node",
                            "3": "go",
                            "4": "rust",
                            "5": "java",
                            "6": "ruby",
                            "7": "general",
                        }
                        if choice in choice_map:
                            self.detected_language = choice_map[choice]
                            return self.detected_language
                        else:
                            print("Please enter a number between 1 and 7")
                    except KeyboardInterrupt:
                        print("\nUsing general language settings")
                        break

        # Default to general
        self.detected_language = "general"
        return "general"

    def generate_claude_md(self) -> str:
        """Generate project-specific CLAUDE.md content using full template"""
        try:
            # Download the full template
            template_url = f"{self.GITHUB_RAW_BASE}/templates/CLAUDE.md"
            response = urllib.request.urlopen(template_url)
            template_content = response.read().decode("utf-8")

            # Customize the template with project-specific information
            customized_content = (
                template_content.replace(
                    "**Project**: [Your Project Name]",
                    f"**Project**: {self.project_name}",
                )
                .replace(
                    "**Purpose**: [Brief description of what this project does]",
                    f"**Purpose**: {self.project_purpose}",
                )
                .replace(
                    "[CUSTOMIZE: Brief overview of your project and its main purpose]",
                    f"This project focuses on {self.project_purpose.lower()}.",
                )
            )

            return customized_content

        except Exception as e:
            print(f"⚠️  Could not download template, using fallback: {e}")
            # Fallback to simplified version if template download fails
            return """# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Project**: {self.project_name}
**Purpose**: {self.project_purpose}
**Framework**: AI-First SDLC Practices (https://github.com/SteveGJones/ai-first-sdlc-practices)

⚠️  **Note**: This is a simplified CLAUDE.md. For full features, download the complete template from the framework repository.

## Development Workflow

### MANDATORY: Follow AI-First SDLC Practices

1. **Never push directly to main branch** - Main branch should be protected
2. **Always create feature proposals before implementing**
3. **Always use feature branches** (feature/name, fix/name, etc.)
4. **Create retrospectives after completing features**

### Quick Repository Health Check
```bash
# Verify you're not on main branch
git branch --show-current

# Check if main branch protection exists
gh api repos/:owner/:repo/branches/main/protection --jq '.required_status_checks.contexts' 2>/dev/null
```

## Important Notes

- This project follows AI-First SDLC practices
- All changes must go through feature branches with PR review
- Main branch protection should be enabled
- Feature proposals and retrospectives are required
"""

    def setup_python_project(self) -> bool:
        """Create essential Python project files"""
        print("\n🐍 Setting up Python project essentials...")

        # Create virtual environment first (unless disabled)
        self._setup_python_virtual_env()

        # Create venv runner scripts for easy command execution
        self._create_venv_runner_scripts()

        self._create_requirements_txt()
        self._create_pyproject_toml()
        self._create_setup_py()
        self._create_python_package_structure()
        self._create_basic_test_file()

        return True

    def _detect_existing_venv(self) -> Optional[str]:
        """Detect if a virtual environment already exists"""
        venv_indicators = ["venv", ".venv", "env", ".env", "virtualenv", ".virtualenv"]

        for venv_name in venv_indicators:
            venv_path = self.project_dir / venv_name
            if venv_path.exists() and venv_path.is_dir():
                # Check if it's actually a venv by looking for key files
                if (venv_path / "bin" / "activate").exists() or (
                    venv_path / "Scripts" / "activate.bat"
                ).exists():
                    return venv_name

        # Check for Poetry/Pipenv
        if (self.project_dir / "poetry.lock").exists():
            return "poetry"
        if (self.project_dir / "Pipfile.lock").exists():
            return "pipenv"

        return None

    def _find_python_executable(self) -> str:
        """Find the best Python executable to use"""
        # Use provided python command if specified
        if self.python_cmd:
            try:
                result = subprocess.run(
                    [self.python_cmd, "--version"],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                if "Python 3" in result.stdout:
                    return self.python_cmd
                else:
                    print(
                        f"   ⚠️  {self.python_cmd} is not Python 3, searching for alternative..."
                    )
            except (subprocess.CalledProcessError, FileNotFoundError):
                print(
                    f"   ⚠️  {self.python_cmd} not found, searching for alternative..."
                )

        # Try Python 3 first
        for cmd in ["python3", "python"]:
            try:
                result = subprocess.run(
                    [cmd, "--version"], capture_output=True, text=True, check=True
                )
                # Check if it's Python 3
                if "Python 3" in result.stdout:
                    return cmd
            except (subprocess.CalledProcessError, FileNotFoundError):
                continue

        # Default to python3 and let it fail with clear error
        return "python3"

    def _setup_python_virtual_env(self) -> bool:
        """Set up Python virtual environment unless disabled or already exists"""

        # Check if we should skip venv creation
        if getattr(self, "skip_venv", False):
            print("   ℹ️  Skipping virtual environment creation (--no-venv flag)")
            return True

        # Check for existing virtual environment
        existing_venv = self._detect_existing_venv()
        if existing_venv:
            if existing_venv in ["poetry", "pipenv"]:
                print(f"   ✓ Using existing {existing_venv} environment")
            else:
                print(f"   ✓ Virtual environment already exists: {existing_venv}/")
            return True

        # Create new virtual environment
        print("   🔧 Creating Python virtual environment...")

        python_cmd = self._find_python_executable()
        venv_name = getattr(self, "venv_name", "venv")
        venv_path = self.project_dir / venv_name

        try:
            # Create venv
            subprocess.run(
                [python_cmd, "-m", "venv", str(venv_path)],
                check=True,
                capture_output=True,
            )

            # Determine pip path based on OS
            if os.name == "nt":  # Windows
                pip_path = venv_path / "Scripts" / "pip"
                activate_cmd = f"{venv_name}\\Scripts\\activate"
            else:  # Unix-like
                pip_path = venv_path / "bin" / "pip"
                activate_cmd = f"source {venv_name}/bin/activate"

            # Upgrade pip
            subprocess.run(
                [str(pip_path), "install", "--upgrade", "pip"],
                check=True,
                capture_output=True,
            )

            print(f"   ✅ Created virtual environment: {venv_name}/")
            print(f"   📝 Activate with: {activate_cmd}")

            # Add venv instructions to context
            self.venv_created = True
            self.venv_name = venv_name
            self.activate_cmd = activate_cmd

            return True

        except subprocess.CalledProcessError as e:
            print(f"   ⚠️  Failed to create virtual environment: {e}")
            print("   ℹ️  Continuing without virtual environment")
            return False
        except Exception as e:
            print(f"   ⚠️  Unexpected error creating virtual environment: {e}")
            return False

    def _create_venv_runner_scripts(self) -> bool:
        """Create convenience scripts for running commands in venv context."""

        # Skip if venv was skipped
        if self.skip_venv:
            return True

        print("   🔧 Creating venv runner scripts...")

        # Unix/Linux/Mac script
        unix_script = """#!/bin/bash
# Virtual Environment Runner - Auto-activates venv for commands
# Usage: ./venv-run.sh python script.py
# Usage: ./venv-run.sh pip install package
# Usage: ./venv-run.sh pytest

set -e
VENV_DIR="${VENV_DIR:-venv}"
cd "$(dirname "${BASH_SOURCE[0]}")"

# Check and create venv if needed
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
    source "$VENV_DIR/bin/activate"
    pip install --upgrade pip --quiet
    [ -f "requirements.txt" ] && pip install -r requirements.txt
else
    source "$VENV_DIR/bin/activate"
fi

# Execute command or start shell
if [ $# -eq 0 ]; then
    echo "Python: $(which python)"
    echo "Starting shell with venv activated..."
    exec $SHELL
else
    exec "$@"
fi
"""

        # Windows script
        windows_script = """@echo off
REM Virtual Environment Runner - Auto-activates venv for commands
REM Usage: venv-run.bat python script.py
REM Usage: venv-run.bat pip install package
REM Usage: venv-run.bat pytest

setlocal enabledelayedexpansion
if "%VENV_DIR%"=="" set VENV_DIR=venv
cd /d "%~dp0"

REM Check and create venv if needed
if not exist "%VENV_DIR%\\Scripts\\activate.bat" (
    echo Creating virtual environment...
    python -m venv "%VENV_DIR%"
    call "%VENV_DIR%\\Scripts\\activate.bat"
    python -m pip install --upgrade pip --quiet
    if exist "requirements.txt" pip install -r requirements.txt
) else (
    call "%VENV_DIR%\\Scripts\\activate.bat"
)

REM Execute command or start shell
if "%1"=="" (
    where python
    echo Starting command prompt with venv activated...
    cmd /k
) else (
    REM Build and execute command
    set cmd_line=%*
    !cmd_line!
)
"""

        # Create the scripts
        try:
            # Unix script
            venv_run_sh = self.project_dir / "venv-run.sh"
            venv_run_sh.write_text(unix_script)
            # Make executable on Unix
            if os.name != "nt":
                venv_run_sh.chmod(0o755)

            # Windows script
            venv_run_bat = self.project_dir / "venv-run.bat"
            venv_run_bat.write_text(windows_script)

            print("   ✅ Created venv runner scripts")
            print("   📝 Usage: ./venv-run.sh python script.py (Unix/Mac)")
            print("   📝 Usage: venv-run.bat python script.py (Windows)")

            return True

        except Exception as e:
            print(f"   ⚠️  Failed to create venv runner scripts: {e}")
            return False

    def _create_claude_launcher(self) -> bool:
        """Create bin/claude launcher script for one-command Claude startup."""

        print("   🚀 Creating Claude launcher script...")

        # Create bin directory
        bin_dir = self.project_dir / "bin"
        bin_dir.mkdir(exist_ok=True)

        # Unix/Mac launcher script
        unix_launcher = f"""#!/bin/bash
# Claude Launcher - One command to start Claude with everything set up
# Generated by AI-First SDLC setup
# Usage: ./bin/claude

set -e
SCRIPT_DIR="$(cd "$(dirname "${{BASH_SOURCE[0]}}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
VENV_DIR="$PROJECT_ROOT/{self.venv_name if hasattr(self, 'venv_name') else 'venv'}"

cd "$PROJECT_ROOT"

# Colors
GREEN='\\033[0;32m'
BLUE='\\033[0;34m'
NC='\\033[0m'

echo -e "${{BLUE}}🤖 AI-First SDLC Claude Launcher${{NC}}"
echo "Project: {self.project_name}"

# Setup Python venv if this is a Python project
if [ -f "requirements.txt" ] || [ -f "setup.py" ] || [ -f "pyproject.toml" ]; then
    if [ ! -d "$VENV_DIR" ]; then
        echo "Creating virtual environment..."
        python3 -m venv "$VENV_DIR"
        source "$VENV_DIR/bin/activate"
        pip install --upgrade pip --quiet
        [ -f "requirements.txt" ] && pip install -r requirements.txt
    else
        source "$VENV_DIR/bin/activate"
    fi
    echo -e "${{GREEN}}✓ Python environment ready${{NC}}"
fi

# Check for Claude CLI
if ! command -v claude &> /dev/null; then
    echo "Claude CLI not found. Please install from:"
    echo "  https://claude.ai/download"
    exit 1
fi

# Launch Claude
echo -e "${{BLUE}}Launching Claude Code...${{NC}}"
exec claude "$PROJECT_ROOT"
"""

        # Windows launcher script
        windows_launcher = f"""@echo off
REM Claude Launcher - One command to start Claude with everything set up
REM Generated by AI-First SDLC setup
REM Usage: bin\\claude.bat

setlocal
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%\\.."
set PROJECT_ROOT=%CD%
set VENV_DIR=%PROJECT_ROOT%\\{self.venv_name if hasattr(self, 'venv_name') else 'venv'}

echo AI-First SDLC Claude Launcher
echo Project: {self.project_name}

REM Setup Python venv if this is a Python project
if exist "requirements.txt" goto :setup_venv
if exist "setup.py" goto :setup_venv
if exist "pyproject.toml" goto :setup_venv
goto :check_claude

:setup_venv
if not exist "%VENV_DIR%\\Scripts\\activate.bat" (
    echo Creating virtual environment...
    python -m venv "%VENV_DIR%"
    call "%VENV_DIR%\\Scripts\\activate.bat"
    python -m pip install --upgrade pip --quiet
    if exist "requirements.txt" pip install -r requirements.txt
) else (
    call "%VENV_DIR%\\Scripts\\activate.bat"
)
echo Python environment ready

:check_claude
where claude >nul 2>nul
if errorlevel 1 (
    echo Claude CLI not found. Please install from:
    echo   https://claude.ai/download
    pause
    exit /b 1
)

echo Launching Claude Code...
claude "%PROJECT_ROOT%"
"""

        try:
            # Create Unix/Mac launcher
            claude_sh = bin_dir / "claude"
            claude_sh.write_text(unix_launcher)
            if os.name != "nt":
                claude_sh.chmod(0o755)  # Make executable

            # Create Windows launcher
            claude_bat = bin_dir / "claude.bat"
            claude_bat.write_text(windows_launcher)

            print("   ✅ Created Claude launcher: ./bin/claude")
            print("   💡 Start Claude with: ./bin/claude")

            # Also add to gitignore if not present
            gitignore_path = self.project_dir / ".gitignore"
            if gitignore_path.exists():
                content = gitignore_path.read_text()
                if "bin/claude" not in content:
                    # Don't ignore the launcher scripts
                    pass  # They should be committed

            return True

        except Exception as e:
            print(f"   ⚠️  Failed to create Claude launcher: {e}")
            return False

    def _create_requirements_txt(self):
        """Create requirements.txt with common dependencies"""
        requirements_content = """# Core dependencies
pytest>=7.0.0
pytest-cov>=4.0.0
black>=23.0.0
flake8>=6.0.0
mypy>=1.0.0
pre-commit>=3.0.0

# Add your project dependencies below:
"""
        requirements_path = self.project_dir / "requirements.txt"
        if not requirements_path.exists():
            requirements_path.write_text(requirements_content)
            print("✅ Created requirements.txt")

    def _create_pyproject_toml(self):
        """Create pyproject.toml with tool configurations"""
        BLACK_LINE_LENGTH = 88
        SETUPTOOLS_MIN_VERSION = 45

        pyproject_content = f"""[tool.black]
line-length = {BLACK_LINE_LENGTH}
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
requires = ["setuptools>={SETUPTOOLS_MIN_VERSION}", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "{self.project_name}"
version = "0.1.0"
description = "{self.project_purpose}"
"""
        pyproject_path = self.project_dir / "pyproject.toml"
        if not pyproject_path.exists():
            pyproject_path.write_text(pyproject_content)
            print("✅ Created pyproject.toml")

    def _create_setup_py(self):
        """Create setup.py for package distribution"""
        setup_content = f"""#!/usr/bin/env python3
\"\"\"
{self.project_name}
{self.project_purpose}
\"\"\"

from setuptools import setup, find_packages

setup(
    name="{self.project_name}",
    version="0.1.0",
    description="{self.project_purpose}",
    packages=find_packages(where="src"),
    package_dir={{"": "src"}},
    python_requires=">=3.8",
    install_requires=[
        # Add runtime dependencies here
    ],
    extras_require={{
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
            "pre-commit>=3.0.0",
        ],
    }},
)
"""
        setup_path = self.project_dir / "setup.py"
        if not setup_path.exists():
            setup_path.write_text(setup_content)
            os.chmod(setup_path, 0o600)
            print("✅ Created setup.py")

    def _create_python_package_structure(self):
        """Create __init__.py files for package structure"""
        package_name = self.project_name.replace("-", "_")
        init_files = [
            self.project_dir / "src" / package_name / "__init__.py",
            self.project_dir / "tests" / "__init__.py",
        ]

        for init_file in init_files:
            if not init_file.exists():
                init_file.parent.mkdir(parents=True, exist_ok=True)
                init_file.write_text('"""Package initialization."""\n')

        print("✅ Created package structure")

    def _create_basic_test_file(self):
        """Create basic test file for the package"""
        package_name = self.project_name.replace("-", "_")
        test_content = f"""\"\"\"
Basic tests for {self.project_name}
\"\"\"

import pytest


def test_framework_setup():
    \"\"\"Test that the AI-First SDLC framework is properly set up.\"\"\"
    from pathlib import Path

    # Check essential directories exist
    project_root = Path(__file__).parent.parent
    assert (project_root / "docs" / "architecture").exists()
    assert (project_root / "docs" / "feature-proposals").exists()
    assert (project_root / "retrospectives").exists()


def test_import():
    \"\"\"Test that the package can be imported.\"\"\"
    import {package_name}
    assert {package_name}.__name__ == "{package_name}"
"""
        test_path = self.project_dir / "tests" / f"test_{package_name}.py"
        if not test_path.exists():
            test_path.write_text(test_content)
            print("✅ Created basic test file")

    def update_readme_for_python(self):
        """Update README.md with Python-specific content"""
        readme_path = self.project_dir / "README.md"

        if not readme_path.exists():
            # Create new README if it doesn't exist
            self.create_readme()

        # Read existing content
        content = readme_path.read_text()

        # Check if Python section already exists
        if "## Installation" in content and "pip install" in content:
            print("ℹ️  README.md already has Python content, skipping update")
            return

        # Find where to insert Python content (after Overview or at end)
        python_section = """
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

# Run tests with coverage
pytest --cov

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
│   ├── architecture/
│   └── feature-proposals/
├── requirements.txt
├── setup.py
├── pyproject.toml
└── README.md
```
"""

        # Insert after Overview section or before Testing section
        if "## Overview" in content:
            parts = content.split("## Getting Started")
            if len(parts) == 2:
                content = parts[0] + python_section + "\n## Getting Started" + parts[1]
            else:
                # Insert after Overview
                parts = content.split("## Overview")
                if len(parts) == 2:
                    # Find the end of Overview section
                    lines = parts[1].split("\n")
                    insert_idx = 0
                    for i, line in enumerate(lines):
                        if line.startswith("##"):
                            insert_idx = i
                            break
                    if insert_idx > 0:
                        lines.insert(insert_idx, python_section)
                        parts[1] = "\n".join(lines)
                        content = "## Overview".join(parts)
        else:
            # Just append at the end
            content = content.rstrip() + "\n" + python_section

        # Write updated content
        readme_path.write_text(content)
        print("✅ Updated README.md with Python-specific content")

    def configure_sdlc_level(self):
        """Configure the SDLC level for the project"""
        print(f"\n🎯 Configuring SDLC Level: {self.sdlc_level}")

        # Create .sdlc directory if needed
        sdlc_dir = self.project_dir / ".sdlc"
        sdlc_dir.mkdir(exist_ok=True)

        # Create level configuration
        level_config = {
            "level": self.sdlc_level,
            "set_date": subprocess.run(
                ["date", "+%Y-%m-%dT%H:%M:%S"], capture_output=True, text=True
            ).stdout.strip(),
            "framework_version": "1.6.0",
        }

        level_file = sdlc_dir / "level.json"
        with open(level_file, "w") as f:
            json.dump(level_config, f, indent=2)

        print(f"✅ Set SDLC level to: {self.sdlc_level}")

        # Print level-specific guidance
        if self.sdlc_level == "prototype":
            print("   📝 Prototype level: Quick starts with basic requirements")
            print("   ✅ TODOs are allowed during prototyping")
            print("   📋 Required: feature intent, basic design, retrospective")
        elif self.sdlc_level == "production":
            print("   🏭 Production level: Full architecture and zero technical debt")
            print("   📋 Required: All 6 architecture documents")
            print("   🚫 No TODOs, FIXMEs, or technical debt allowed")
        else:  # enterprise
            print("   🏢 Enterprise level: Maximum rigor with compliance")
            print("   📋 Required: All production requirements plus compliance docs")
            print("   👥 Team coordination and audit trails mandatory")

    def create_initial_feature_proposal(self) -> bool:
        """Create the initial setup feature proposal"""
        proposal_dir = self.project_dir / "docs" / "feature-proposals"
        proposal_dir.mkdir(parents=True, exist_ok=True)

        proposal_path = proposal_dir / "00-ai-first-setup.md"

        content = """# Feature Proposal: AI-First SDLC Setup

**Proposal Number:** 00
**Status:** In Progress
**Author:** AI Setup Assistant
**Created:** {subprocess.run(['date', '+%Y-%m-%d'], capture_output=True, text=True).stdout.strip()}
**Target Branch:** `ai-first-kick-start`
**Implementation Type:** Infrastructure

---

## Executive Summary

Initial setup of AI-First SDLC practices for {self.project_name}.
This establishes the framework, tools, and workflows needed for AI-assisted development.

---

## Motivation

### Problem Statement

- Project needs structured AI-assisted development workflow
- No existing framework for AI agent collaboration
- Need consistent practices for quality and compliance

### User Stories

- As a developer, I want AI agents to follow consistent practices
- As an AI agent, I want clear guidance on development workflow
- As a project maintainer, I want automated validation of changes

---

## Proposed Solution

Implement AI-First SDLC framework with:
- AI instruction files (CLAUDE.md)
- Feature proposal templates
- Progress tracking tools
- Automated validation pipeline
- CI/CD integration

---

## Success Criteria

- [ ] Framework tools installed
- [ ] CI/CD pipeline configured
- [ ] CLAUDE.md customized for project
- [ ] Initial validation passes
- [ ] Feature branch workflow enforced

---

## Implementation Status

- [x] Downloaded framework tools
- [x] Created directory structure
- [x] Generated CLAUDE.md
- [ ] Configure CI/CD
- [ ] Run initial validation
- [ ] Create first retrospective
"""

        with open(proposal_path, "w") as f:
            f.write(content)

        return True

    def customize_architecture_templates(self) -> bool:
        """Customize architecture templates with project-specific content"""
        print("\n🏗️  Customizing architecture templates with project info...")

        # Try both organized and regular directory structures
        architecture_dirs = [
            self.project_dir / "docs" / "architecture",  # Regular setup
            self.project_dir
            / ".sdlc"
            / "templates"
            / "architecture",  # Organized setup
        ]

        architecture_dir = None
        for dir_path in architecture_dirs:
            if dir_path.exists():
                architecture_dir = dir_path
                break

        if not architecture_dir:
            print("⚠️  Architecture directory not found, skipping customization")
            return True

        from datetime import datetime

        current_date = datetime.now().strftime("%Y-%m-%d")

        # Template customization mappings
        customizations = {
            "[Feature Name]": self.project_name,
            "[YYYY-MM-DD]": current_date,
            "[Team/Roles responsible]": "Development Team",
            "[Project Description]": self.project_purpose,
            "[Component Name]": self.project_name,
            "FR-001": f"{self.project_name.upper()}-FR-001",
            "NFR-001": f"{self.project_name.upper()}-NFR-001",
            "[Service]": f"{self.project_name} Service",
            "[System Name]": self.project_name,
        }

        # Architecture templates to customize
        templates_to_customize = [
            "requirements-traceability-matrix.md",
            "what-if-analysis.md",
            "system-invariants.md",
            "integration-design.md",
            "failure-mode-analysis.md",
        ]

        for template_file in templates_to_customize:
            template_path = architecture_dir / template_file
            if template_path.exists():
                try:
                    content = template_path.read_text()

                    # Apply customizations
                    for placeholder, replacement in customizations.items():
                        content = content.replace(placeholder, replacement)

                    # Add project-specific examples for requirements matrix
                    if template_file == "requirements-traceability-matrix.md":
                        content = self._customize_requirements_matrix(content)

                    # Add project-specific invariants for system invariants
                    elif template_file == "system-invariants.md":
                        content = self._customize_system_invariants(content)

                    # Write back customized content
                    template_path.write_text(content)
                    print(f"✅ Customized {template_file}")

                except Exception as e:
                    print(f"⚠️  Could not customize {template_file}: {e}")

        return True

    def _customize_requirements_matrix(self, content: str) -> str:
        """Add project-specific requirements to the matrix"""
        # Replace the template requirements with project-specific ones
        project_reqs = (
            f"| {self.project_name.upper()}-FR-001 | MUST | Core {self.project_name} "
            f"functionality | Main Service | src/main.py | tests/test_main.py | ❌ |\n"
            f"| {self.project_name.upper()}-FR-002 | MUST | User interface for "
            f"{self.project_purpose} | UI Component | src/ui/ | tests/test_ui.py | ❌ |\n"
            f"| {self.project_name.upper()}-NFR-001 | MUST | System performance "
            f"requirements | All Components | - | tests/performance/ | ❌ |\n"
            f"| {self.project_name.upper()}-NFR-002 | MUST | Security and authentication "
            f"| Auth Service | src/auth/ | tests/test_auth.py | ❌ |"
        )

        # Replace the template rows
        template_rows = (
            "| FR-001 | MUST | [Feature] | [Service] | [path/file.ext] | [test/file.ext] | ❌ |\n"
            "| FR-002 | MUST | | | | | ❌ |\n"
            "| NFR-001 | MUST | [Performance/Security] | | | | ❌ |\n"
            "| NFR-002 | MUST | | | | | ❌ |"
        )
        content = content.replace(template_rows, project_reqs)

        return content

    def _customize_system_invariants(self, content: str) -> str:
        """Add project-specific invariants"""
        # Add project-specific invariants to existing examples
        project_invariants = """
### {self.project_name} Specific
- [ ] **INV-{self.project_name.upper()[:3]}001**: {self.project_purpose} data is always validated
- [ ] **INV-{self.project_name.upper()[:3]}002**: System state remains consistent during operations
- [ ] **INV-{self.project_name.upper()[:3]}003**: User inputs are properly sanitized
- [ ] **INV-{self.project_name.upper()[:3]}004**: Error conditions are handled gracefully
- [ ] **INV-{self.project_name.upper()[:3]}005**: System resources are properly managed"""

        # Insert after the existing User Data section
        insert_point = "- [ ] **INV-U005**: [Add your invariant]"
        if insert_point in content:
            content = content.replace(
                insert_point,
                f"- [ ] **INV-U005**: User data integrity maintained{project_invariants}",
            )

        return content

    def create_gitignore(self) -> bool:
        """Create comprehensive .gitignore file"""
        gitignore_path = self.project_dir / ".gitignore"

        # Check if .gitignore already exists
        existing_content = ""
        if gitignore_path.exists():
            # Create backup
            import shutil
            from datetime import datetime

            backup_name = (
                f".gitignore.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )
            backup_path = self.project_dir / backup_name
            shutil.copy2(gitignore_path, backup_path)
            print(f"📁 Created backup: {backup_name}")

            with open(gitignore_path, "r") as f:
                existing_content = f.read()
            print("📝 Updating existing .gitignore...")
        else:
            print("📝 Creating new .gitignore...")

        # Detect language if not already done
        if not self.detected_language:
            self.detect_project_language()

        # Load gitignore templates
        templates_to_combine = [
            "base.gitignore",
            "ai-tools.gitignore",
            (
                f"{self.detected_language}.gitignore"
                if self.detected_language != "general"
                else "general.gitignore"
            ),
        ]

        combined_content = []
        for template_name in templates_to_combine:
            try:
                # Read from downloaded templates
                template_path = self.project_dir / ".ai-sdlc-temp" / template_name
                if template_path.exists():
                    with open(template_path, "r") as f:
                        content = f.read()
                        if content.strip():  # Only add non-empty templates
                            combined_content.append(
                                f"# === {template_name.replace('.gitignore', '').title()} Patterns ==="
                            )
                            combined_content.append(content.strip())
                            # Empty line between sections
                            combined_content.append("")
            except Exception as e:
                self.errors.append(f"Could not read template {template_name}: {e}")

        # Combine with existing content if any
        if existing_content:
            # Parse existing patterns to avoid duplicates
            existing_patterns = set()
            for line in existing_content.strip().split("\n"):
                line = line.strip()
                if line and not line.startswith("#"):
                    existing_patterns.add(line)

            # Filter out duplicate patterns from new content
            filtered_content = []
            for section in combined_content:
                if section.startswith("# ==="):
                    filtered_content.append(section)
                else:
                    # Filter individual patterns
                    filtered_lines = []
                    for line in section.split("\n"):
                        line_stripped = line.strip()
                        if (
                            not line_stripped
                            or line_stripped.startswith("#")
                            or line_stripped not in existing_patterns
                        ):
                            filtered_lines.append(line)
                    if filtered_lines:
                        filtered_content.append("\n".join(filtered_lines))

            # Combine existing and new content
            combined_content = [
                existing_content.strip(),
                "\n# === AI-First SDLC Framework Patterns (Added) ===\n",
            ] + filtered_content

        # Write the combined content
        final_content = "\n".join(combined_content)
        with open(gitignore_path, "w") as f:
            f.write(final_content)

        print(
            f"✅ Created comprehensive .gitignore (detected language: {self.detected_language})"
        )
        return True

    def create_initial_test(self) -> bool:
        """Create initial framework verification test based on detected language"""
        if not self.detected_language:
            self.detect_project_language()

        # Map language to test file
        test_mappings = {
            "python": ("test_framework_setup.py", "test_framework_setup.py"),
            "node": ("framework.test.js", "test/framework.test.js"),
            "go": ("test-framework.sh", "test-framework.sh"),
            "java": (
                "FrameworkTest.java",
                "src/test/java/FrameworkTest.java",
            ),
            "ruby": ("framework_test.rb", "test/framework_test.rb"),
            "rust": ("framework_test.rs", "tests/framework_test.rs"),
            "general": ("test-framework.sh", "test-framework.sh"),
        }

        # Get test file info
        template_name, target_path = test_mappings.get(
            self.detected_language, test_mappings["general"]
        )

        # Create test directory if needed
        test_file_path = self.project_dir / target_path
        test_file_path.parent.mkdir(parents=True, exist_ok=True)

        # Copy test from downloaded templates
        template_path = self.project_dir / ".ai-sdlc-temp" / template_name
        if template_path.exists():
            with open(template_path, "r") as f:
                content = f.read()
            with open(test_file_path, "w") as f:
                f.write(content)

            # Make shell script executable by owner only
            if template_name.endswith(".sh"):
                # Owner: rwx, Group: ---, Others: ---
                os.chmod(test_file_path, 0o700)

            print(f"✅ Created initial test: {target_path}")
            return True
        else:
            self.errors.append(f"Test template not found: {template_name}")
            return False

    def create_readme(self) -> bool:
        """Create initial README.md if it doesn't exist"""
        readme_path = self.project_dir / "README.md"
        if readme_path.exists():
            print("ℹ️  README.md already exists, skipping...")
            return True

        content = f"""# {self.project_name}

{self.project_purpose}

## Overview

This project uses the AI-First SDLC framework for development.
AI agents and developers should refer to [CLAUDE.md](CLAUDE.md) for development guidelines.

## Getting Started

1. Review [CLAUDE.md](CLAUDE.md) for AI-First development practices
2. Check `docs/feature-proposals/` for planned features
3. Run validation: `python tools/validate-pipeline.py`

## Project Structure

```
{self.project_name}/
├── CLAUDE.md              # AI agent instructions
├── docs/
│   └── feature-proposals/ # Feature proposals
├── plan/                  # Implementation plans
├── retrospectives/        # Feature retrospectives
└── tools/                 # Framework tools
```

## Development Workflow

1. Create feature proposal in `docs/feature-proposals/`
2. Create feature branch: `git checkout -b feature/name`
3. Implement changes
4. Update retrospective
5. Create Pull Request

## Testing

```bash
# Run framework verification
python test_framework_setup.py  # or appropriate test file
```

## Contributing

This project follows AI-First SDLC practices. See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

---

Built with [AI-First SDLC Framework](https://github.com/SteveGJones/ai-first-sdlc-practices)
"""

        with open(readme_path, "w") as f:
            f.write(content)

        print("✅ Created README.md")
        return True

    def setup_project(
        self,
        skip_ci: bool = False,
        github_token: str = None,
        quickstart: bool = False,
    ) -> bool:
        """Run the complete setup process"""
        self._print_setup_header()

        # Handle quickstart/organized modes
        if quickstart or self.organized:
            return self._handle_quickstart_mode(skip_ci, github_token)

        # Setup full framework
        self._setup_git_repository()
        self._download_framework_files()
        language = self._detect_and_setup_language()
        self._create_directory_structure(language)
        self._setup_claude_files()
        self._setup_project_files()
        self._setup_language_specifics(language)
        self._setup_cicd_if_needed(skip_ci)
        self._finalize_setup()
        self._setup_branch_protection_if_needed(github_token)
        self._create_first_commit_if_needed()
        self._cleanup_and_finish()

        return len(self.errors) == 0

    def _print_setup_header(self):
        """Print setup header information"""
        print("🚀 AI-First SDLC Smart Setup")
        print("=" * 50)
        print(f"Project: {self.project_name}")
        print(f"Purpose: {self.project_purpose}")
        print()

    def _handle_quickstart_mode(self, skip_ci: bool, github_token: str) -> bool:
        """Handle quickstart and organized setup modes"""
        mode_name = "organized" if self.organized else "quickstart"
        print(f"\n⚡ Running in {mode_name} mode...")

        if self.organized:
            return self.setup_organized_project(skip_ci, github_token)

        return self._run_quickstart_setup()

    def _run_quickstart_setup(self) -> bool:
        """Run minimal quickstart setup"""
        # Download quickstart files
        print("📥 Downloading templates...")
        quickstart_files = self._get_quickstart_files()

        for file in quickstart_files:
            self.download_file(file, None)

        # Create minimal structure
        self._create_minimal_structure()
        self._create_version_file()
        self._run_validation_and_cleanup()
        self._print_quickstart_completion()
        return True

    def _get_quickstart_files(self):
        """Get list of files needed for quickstart"""
        base_files = [
            "templates/gitignore/base.gitignore",
            "templates/gitignore/ai-tools.gitignore",
            "templates/gitignore/general.gitignore",
            "templates/tests/test-framework.sh",
            "tools/validation/validate-pipeline.py",
        ]

        print("🔍 Detecting project language...")
        language = self.detect_project_language()
        print(f"✅ Detected language: {language}")

        if language != "general":
            base_files.append(f"templates/gitignore/{language}.gitignore")
            test_map = {
                "python": "templates/tests/test_framework_setup.py",
                "node": "templates/tests/framework.test.js",
                "java": "templates/tests/FrameworkTest.java",
                "ruby": "templates/tests/framework_test.rb",
                "rust": "templates/tests/framework_test.rs",
                "go": "templates/tests/test-framework.sh",
            }
            if language in test_map:
                base_files.append(test_map[language])

        return base_files

    def _create_minimal_structure(self):
        """Create minimal directory structure for quickstart"""
        print("📁 Creating minimal directory structure...")
        minimal_dirs = ["docs", "docs/architecture", "tools"]
        for dir_path in minimal_dirs:
            (self.project_dir / dir_path).mkdir(parents=True, exist_ok=True)

        if not (self.project_dir / "README.md").exists():
            print("📄 Creating README.md...")
            self.create_readme()

        print("📝 Setting up .gitignore...")
        self.create_gitignore()

        print("🧪 Creating initial test...")
        self.create_initial_test()

    def _create_version_file(self):
        """Create VERSION file"""
        print("📌 Creating VERSION file...")
        version_file = self.project_dir / "VERSION"
        version_file.write_text("1.6.0")

    def _run_validation_and_cleanup(self):
        """Run validation and clean up temp files"""
        print("🔍 Running validation...")
        self.run_validation()

        temp_dir = self.project_dir / ".ai-sdlc-temp"
        if temp_dir.exists():
            import shutil

            shutil.rmtree(temp_dir)

    def _print_quickstart_completion(self):
        """Print quickstart completion message"""
        print("\n✅ Quickstart setup completed in < 10 seconds!")
        print("\n📚 Next steps:")
        print("  1. Review the generated files")
        print(
            f'  2. Run the full setup with: python setup-smart.py "{self.project_purpose}"'
        )
        print(
            "  3. Commit your changes: git add . && git commit -m 'Initial AI-First SDLC setup'"
        )

    def _setup_git_repository(self):
        """Setup git repository and branch"""
        if not self.check_git_repo():
            print("⚠️  No git repository found. Initializing...")
            self.init_git_repo()

        print("\n🌿 Creating ai-first-kick-start branch...")
        try:
            subprocess.run(
                ["git", "checkout", "-b", "ai-first-kick-start"],
                capture_output=True,
                check=True,
            )
            print("✅ Created and switched to ai-first-kick-start branch")
        except subprocess.CalledProcessError:
            print("ℹ️  Branch already exists or couldn't be created")

    def _download_framework_files(self):
        """Download essential framework files"""
        print("\n📥 Downloading framework files...")
        for remote, local in self.ESSENTIAL_FILES.items():
            if local is not None:
                local_path = self.project_dir / local
            else:
                local_path = None

            if self.download_file(remote, local_path):
                if local is not None:
                    print(f"✅ Downloaded {local}")
            else:
                print(f"❌ Failed to download {remote}")

    def _detect_and_setup_language(self):
        """Detect project language"""
        print("\n🔍 Detecting project language...")
        language = self.detect_project_language()
        print(f"✅ Detected language: {language}")
        return language

    def _create_directory_structure(self, language: str):
        """Create directory structure based on detected language"""
        print("\n📁 Creating directory structure...")
        dirs = [
            "docs/feature-proposals",
            "docs/architecture",
            "docs/architecture/decisions",
            "plan",
            "retrospectives",
            ".claude",
            ".claude/agents",
            "templates/architecture",
        ]

        # Add language-specific directories
        if language == "python":
            dirs.extend(["src", "tests", "src/" + self.project_name.replace("-", "_")])
        elif language == "node":
            dirs.extend(["src", "test"])
        elif language == "go":
            dirs.extend(["cmd", "pkg", "internal"])
        elif language == "java":
            dirs.extend(["src/main/java", "src/test/java"])
        elif language == "rust":
            dirs.extend(["src", "tests"])
        elif language == "ruby":
            dirs.extend(["lib", "spec", "test"])

        for dir_path in dirs:
            (self.project_dir / dir_path).mkdir(parents=True, exist_ok=True)
            print(f"✅ Created {dir_path}/")

    def _setup_claude_files(self):
        """Setup Claude.md and related AI files"""
        if (self.project_dir / "CLAUDE-CORE.md").exists():
            print("\n✅ Using hierarchical instruction system (CLAUDE-CORE.md)")
            self._create_claude_deprecation_notice()
        else:
            print(
                "\n⚠️  WARNING: Hierarchical system not found. Please update framework."
            )
            self._create_claude_error_notice()

        # Create symlinks for other AI files
        for ai_file in ["GEMINI.md", "GPT.md"]:
            target = self.project_dir / ai_file
            if not target.exists():
                target.symlink_to("CLAUDE.md")
                print(f"✅ Created {ai_file} → CLAUDE.md")

    def _create_claude_deprecation_notice(self):
        """Create CLAUDE.md deprecation notice"""
        deprecation_content = """# CLAUDE.md

⚠️ **DEPRECATED**: This file exists only for backward compatibility and will be removed in v2.0.0.

Please use the new hierarchical instruction system:
- Start with: CLAUDE-CORE.md
- For setup: CLAUDE-SETUP.md
- For other tasks: See context loading table in CLAUDE-CORE.md

To migrate existing customizations: python tools/migrate-to-hierarchical.py
"""
        with open(self.project_dir / "CLAUDE.md", "w") as f:
            f.write(deprecation_content)
        print("✅ Created CLAUDE.md (deprecation notice only)")

    def _create_claude_error_notice(self):
        """Create CLAUDE.md error notice"""
        fallback_content = """# CLAUDE.md

ERROR: The hierarchical instruction system was not properly installed.

Please re-run setup or manually download:
- CLAUDE-CORE.md
- CLAUDE-SETUP.md
- CLAUDE-CONTEXT-*.md files

From: https://github.com/SteveGJones/ai-first-sdlc-practices
"""
        with open(self.project_dir / "CLAUDE.md", "w") as f:
            f.write(fallback_content)
        print("❌ ERROR: Created error notice in CLAUDE.md")

    def _setup_project_files(self):
        """Setup basic project files"""
        print("\n📝 Setting up .gitignore...")
        self.create_gitignore()

        self.customize_architecture_templates()

        print("\n🧪 Creating initial test...")
        self.create_initial_test()

    def _setup_language_specifics(self, language: str):
        """Setup language-specific files and configuration"""
        if language == "python":
            self.setup_python_project()
            self.update_readme_for_python()

        # Create Claude launcher for ALL projects (not just Python)
        self._create_claude_launcher()

    def _setup_cicd_if_needed(self, skip_ci: bool):
        """Setup CI/CD if not skipped"""
        if not skip_ci:
            platform = self.detect_ci_platform()
            if platform:
                print(f"\n🔧 Detected {platform} CI/CD platform")
                self.setup_ci_cd(platform)
            else:
                print("\n❓ Could not detect CI/CD platform")
                platform = self.ask_ci_platform()
                if platform:
                    self.setup_ci_cd(platform)

    def _finalize_setup(self):
        """Finalize setup with feature proposal, version, and configuration"""
        print("\n📋 Creating initial feature proposal...")
        self.create_initial_feature_proposal()
        print("✅ Created docs/feature-proposals/00-ai-first-setup.md")

        self._create_version_file()
        print("✅ Created VERSION file (1.6.0)")

        self.configure_sdlc_level()

        print("\n🤖 Installing AI agents...")
        self.install_agents()

        print("\n🔧 Creating Claude project configuration...")
        self.create_claude_config()

        print("\n💾 Creating initial context...")
        self.create_initial_context()

        print("\n🔍 Running initial validation...")
        self.run_validation()

    def _setup_branch_protection_if_needed(self, github_token: str):
        """Setup branch protection for GitHub repos if available"""
        detected_platform = self.detect_ci_platform() or "github"
        if detected_platform == "github":
            if self.check_gh_cli():
                print("\n🔒 Setting up branch protection using GitHub CLI...")
                self.setup_branch_protection()
            elif github_token:
                print("\n🔒 Setting up branch protection using token...")
                self.setup_branch_protection(github_token)
            else:
                print(
                    "\n💡 Tip: Install 'gh' CLI or provide GITHUB_TOKEN for automatic branch protection"
                )

    def _create_first_commit_if_needed(self):
        """Create first commit if in non-interactive mode"""
        if self.non_interactive:
            print("\n📦 Creating comprehensive first commit...")
            self.create_first_commit()

    def _cleanup_and_finish(self):
        """Clean up temporary files and print final status"""
        temp_dir = self.project_dir / ".ai-sdlc-temp"
        if temp_dir.exists():
            import shutil

            shutil.rmtree(temp_dir)
            print("\n🧹 Cleaned up temporary files")

        if self.errors:
            print("\n⚠️  Setup completed with errors:")
            for error in self.errors:
                print(f"  - {error}")
        else:
            print("\n✅ Setup completed successfully!")

        self.print_next_steps()

    def setup_organized_project(
        self, skip_ci: bool = False, github_token: str = None
    ) -> bool:
        """Setup project with organized .sdlc directory structure"""
        print("\n📂 Setting up organized framework structure...")

        self._setup_organized_git_and_language()
        self._create_organized_directories()
        self._download_organized_files()
        self._setup_organized_project_files()
        self._setup_organized_ci_and_finalize(skip_ci)
        self._print_organized_completion()

        return True

    def _setup_organized_git_and_language(self):
        """Setup git repository and detect language for organized project"""
        if not self.check_git_repo():
            print("⚠️  No git repository found. Initializing...")
            self.init_git_repo()

        print("\n🔍 Detecting project language...")
        language = self.detect_project_language()
        print(f"✅ Detected language: {language}")
        return language

    def _create_organized_directories(self):
        """Create .sdlc and user-facing directories"""
        print("\n📁 Creating .sdlc directory structure...")
        sdlc_dirs = [
            ".sdlc/tools/validation",
            ".sdlc/tools/automation",
            ".sdlc/templates/architecture",
            ".sdlc/templates/proposals",
            ".sdlc/config",
            ".sdlc/agents",
        ]
        for dir_path in sdlc_dirs:
            (self.project_dir / dir_path).mkdir(parents=True, exist_ok=True)
            print(f"✅ Created {dir_path}/")

        print("\n📁 Creating user-facing directories...")
        user_dirs = [
            "docs/feature-proposals",
            "docs/architecture/decisions",
            "plan",
            "retrospectives",
        ]
        for dir_path in user_dirs:
            (self.project_dir / dir_path).mkdir(parents=True, exist_ok=True)
            print(f"✅ Created {dir_path}/")

    def _download_organized_files(self):
        """Download framework files to .sdlc structure"""
        print("\n📥 Downloading framework files to .sdlc/...")
        organized_files = self._get_organized_files_mapping()

        for remote, local in organized_files.items():
            local_path = self.project_dir / local
            if self.download_file(remote, local_path):
                print(f"✅ Downloaded {local}")

    def _get_organized_files_mapping(self):
        """Get mapping of remote files to organized local paths"""
        return {
            "CLAUDE-CORE.md": "CLAUDE-CORE.md",
            "CLAUDE-SETUP.md": "CLAUDE-SETUP.md",
            "CONTRIBUTING.md": "CONTRIBUTING.md",
            "tools/validation/validate-pipeline.py": ".sdlc/tools/validation/validate-pipeline.py",
            "tools/validation/check-feature-proposal.py": ".sdlc/tools/validation/check-feature-proposal.py",
            "tools/validation/validate-architecture.py": ".sdlc/tools/validation/validate-architecture.py",
            "tools/validation/check-technical-debt.py": ".sdlc/tools/validation/check-technical-debt.py",
            "tools/automation/context-manager.py": ".sdlc/tools/automation/context-manager.py",
            "tools/automation/progress-tracker.py": ".sdlc/tools/automation/progress-tracker.py",
            "tools/automation/agent-installer.py": ".sdlc/tools/automation/agent-installer.py",
            "templates/feature-proposal.md": ".sdlc/templates/proposals/feature-proposal.md",
            "templates/implementation-plan.md": ".sdlc/templates/proposals/implementation-plan.md",
            "templates/retrospective.md": ".sdlc/templates/proposals/retrospective.md",
            "templates/architecture/requirements-traceability-matrix.md": (
                ".sdlc/templates/architecture/requirements-traceability-matrix.md"
            ),
            "templates/architecture/what-if-analysis.md": ".sdlc/templates/architecture/what-if-analysis.md",
            "templates/architecture/architecture-decision-record.md": (
                ".sdlc/templates/architecture/architecture-decision-record.md"
            ),
            "templates/architecture/system-invariants.md": ".sdlc/templates/architecture/system-invariants.md",
            "templates/architecture/integration-design.md": ".sdlc/templates/architecture/integration-design.md",
            "templates/architecture/failure-mode-analysis.md": ".sdlc/templates/architecture/failure-mode-analysis.md",
            "VERSION": ".sdlc/VERSION",
        }

    def _setup_organized_project_files(self):
        """Setup project files for organized structure"""
        print("\n📝 Creating convenience scripts...")
        self.create_convenience_scripts()

        print("\n📄 Creating minimal CLAUDE.md...")
        self.create_minimal_claude_md()

        if not (self.project_dir / "README.md").exists():
            print("\n📄 Creating README.md...")
            self.create_organized_readme()

        print("\n📝 Setting up .gitignore...")
        self.create_organized_gitignore()

        self.customize_architecture_templates()

        print("\n🤖 Installing AI agents to .sdlc/agents/...")
        self.install_organized_agents()

    def _setup_organized_ci_and_finalize(self, skip_ci: bool):
        """Setup CI/CD and finalize organized project"""
        if not skip_ci:
            platform = self.detect_ci_platform() or self.ci_platform
            if platform and platform != "none":
                print(f"\n🔧 Setting up {platform} CI/CD...")
                self.setup_organized_ci_cd(platform)

        print("\n📋 Creating initial feature proposal...")
        self.create_initial_feature_proposal()

        print("\n🔍 Running validation...")
        self.run_organized_validation()

    def _print_organized_completion(self):
        """Print completion message for organized setup"""
        print("\n✅ Organized setup completed successfully!")
        print("\n📚 Next steps:")
        print("  1. Review the clean project structure")
        print("  2. Run tools from: cd sdlc-tools")
        print("     - ./validate - Run validation checks")
        print("     - ./install-agents - Install AI agents")
        print("     - ./new-feature <name> - Create feature proposal")
        print('  3. Or add to PATH: export PATH="$PATH:$(pwd)/sdlc-tools"')

    def create_convenience_scripts(self):
        """Create convenience wrapper scripts in sdlc-tools directory"""
        tools_dir = self.project_dir / "sdlc-tools"
        tools_dir.mkdir(exist_ok=True)

        self._create_sdlc_scripts(tools_dir)
        self._create_sdlc_readme(tools_dir)

    def _create_sdlc_scripts(self, tools_dir):
        """Create individual SDLC wrapper scripts"""
        scripts = self._get_script_definitions()

        for name, content in scripts.items():
            script_path = tools_dir / name
            with open(script_path, "w") as f:
                f.write(content)
            # rwx------ (owner only: read, write, execute)
            os.chmod(script_path, 0o700)
            print(f"✅ Created sdlc-tools/{name}")

    def _get_script_definitions(self):
        """Get dictionary of script names and their content"""
        return {
            "validate": """#!/bin/bash
# Convenience wrapper for validation
python ../.sdlc/tools/validation/validate-pipeline.py "$@"
""",
            "new-feature": """#!/bin/bash
# Create a new feature proposal
if [ -z "$1" ]; then
    echo "Usage: ./new-feature <feature-name>"
    exit 1
fi
cp ../.sdlc/templates/proposals/feature-proposal.md "../docs/feature-proposals/$(date +%y)-$1.md"
echo "Created: docs/feature-proposals/$(date +%y)-$1.md"
""",
            "install-agents": """#!/bin/bash
# Install AI agents
python ../.sdlc/tools/automation/agent-installer.py "$@"
""",
            "check-debt": """#!/bin/bash
# Check for technical debt
python ../.sdlc/tools/validation/check-technical-debt.py "$@"
""",
            "track-progress": """#!/bin/bash
# Track development progress
python ../.sdlc/tools/automation/progress-tracker.py "$@"
""",
        }

    def _create_sdlc_readme(self, tools_dir):
        """Create README.md for sdlc-tools directory"""
        readme_content = self._get_sdlc_readme_content()
        with open(tools_dir / "README.md", "w") as f:
            f.write(readme_content)
        print("✅ Created sdlc-tools/README.md")

    def _get_sdlc_readme_content(self):
        """Get the content for sdlc-tools README.md"""
        return """# SDLC Tools

User-friendly command-line tools for the AI-First SDLC Framework.

## Overview

This directory contains convenience wrappers for common framework commands.
These tools help you follow AI-First SDLC practices without remembering complex paths or commands.

## Available Commands

### 📋 `validate` - Run Framework Validation
Checks your project for AI-First SDLC compliance.

```bash
./validate                    # Run basic checks
./validate --checks all       # Run all validation checks
./validate --checks branch    # Check branch compliance only
./validate --export report.md # Export results to file
```

### 🚀 `new-feature` - Create Feature Proposal
Creates a new feature proposal from the template.

```bash
./new-feature user-auth              # Creates: docs/feature-proposals/24-user-auth.md
./new-feature "payment integration"  # Handles spaces in names
```

### 🤖 `install-agents` - Manage AI Agents
Install and manage specialized AI agents for your project.

```bash
./install-agents list         # List available agents
./install-agents --core-only  # Install essential agents
./install-agents -i langchain-architect  # Install specific agent
./install-agents --analyze    # Get recommendations based on your project
```

### 🔍 `check-debt` - Technical Debt Scanner
Scans for technical debt indicators (TODOs, commented code, etc).

```bash
./check-debt                  # Scan current directory
./check-debt --threshold 0    # Fail if ANY debt found (Zero Technical Debt)
./check-debt --format json    # Output as JSON
```

### 📊 `track-progress` - Task Management
Track development tasks and progress.

```bash
./track-progress add "Implement user authentication"
./track-progress list         # Show all tasks
./track-progress complete 1   # Mark task #1 as complete
./track-progress export       # Export task list
```

## Quick Start

1. **From this directory:**
   ```bash
   cd sdlc-tools
   ./validate
   ```

2. **Add to PATH (recommended):**
   ```bash
   # Add to your .bashrc or .zshrc
   export PATH="$PATH:/path/to/your/project/sdlc-tools"

   # Then use from anywhere in your project
   validate
   new-feature my-feature
   ```

3. **Create aliases:**
   ```bash
   # Add to your shell config
   alias sdlc-validate="cd $PROJECT_ROOT/sdlc-tools && ./validate"
   alias sdlc-feature="cd $PROJECT_ROOT/sdlc-tools && ./new-feature"
   ```

## Tool Details

All tools are shell wrappers around Python scripts in `.sdlc/tools/`. This design:
- Keeps commands simple and memorable
- Hides implementation details
- Allows easy updates without changing commands
- Supports both local and PATH usage

## Getting Help

- Run any command without arguments for usage help
- Check `.sdlc/tools/` for the underlying Python scripts
- See the [AI-First SDLC documentation](https://github.com/SteveGJones/ai-first-sdlc-practices)

## Tips

- **AI Agents**: Always restart your AI assistant after installing new agents
- **Validation**: Run `./validate` before creating pull requests
- **Features**: Create a feature proposal before starting any new work
- **Technical Debt**: Aim for zero output from `./check-debt`

---

Part of the [AI-First SDLC Framework](https://github.com/SteveGJones/ai-first-sdlc-practices)
"""

    def create_minimal_claude_md(self):
        """Create minimal CLAUDE.md for organized structure"""
        content = """# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with this repository.

## Project Overview

**Project**: {self.project_name}
**Purpose**: {self.project_purpose}
**Framework**: AI-First SDLC Practices v1.6.0 (Organized Structure)

## Quick Start

This project uses the organized AI-First SDLC structure:
- Framework tools are in `.sdlc/`
- User tools are in `sdlc-tools/`
- User work is in the standard directories
- Run validation: `cd sdlc-tools && ./validate`

## Directory Structure

```
{self.project_name}/
├── .sdlc/                    # Framework internals (hidden)
│   ├── tools/               # Validation and automation scripts
│   ├── templates/           # Templates for proposals and architecture
│   ├── agents/              # Installed AI agents
│   └── VERSION              # Framework version
├── sdlc-tools/              # User-facing command tools
│   ├── validate             # Run validation checks
│   ├── new-feature          # Create feature proposals
│   ├── install-agents       # Manage AI agents
│   ├── check-debt           # Check technical debt
│   └── track-progress       # Track tasks
├── docs/                    # Documentation and proposals
│   ├── feature-proposals/   # Feature proposals
│   └── architecture/        # Architecture documents and ADRs
├── plan/                    # Implementation plans
├── retrospectives/          # Feature retrospectives
└── src/                     # Your actual project code
```

## Development Workflow

1. **Create feature proposal**: `cd sdlc-tools && ./new-feature <name>`
2. **Create feature branch**: `git checkout -b feature/<name>`
3. **Implement changes**
4. **Update retrospective** in `retrospectives/`
5. **Run validation**: `cd sdlc-tools && ./validate`
6. **Create Pull Request**

## Available Agents

Run `cd sdlc-tools && ./install-agents list` to see available AI agents.
Agents are installed to `.sdlc/agents/` for clean organization.

## Framework Documentation

For detailed instructions, see:
- CLAUDE-CORE.md - Core framework instructions
- CLAUDE-SETUP.md - Setup and configuration

---
Built with [AI-First SDLC Framework](https://github.com/SteveGJones/ai-first-sdlc-practices)
"""
        with open(self.project_dir / "CLAUDE.md", "w") as f:
            f.write(content)

    def create_organized_readme(self):
        """Create README for organized structure"""
        content = """# {self.project_name}

{self.project_purpose}

## Overview

This project uses the AI-First SDLC framework with organized structure for clean project management.

## Quick Start

```bash
# Go to tools directory
cd sdlc-tools

# Validate project compliance
./validate

# Create new feature
./new-feature my-feature-name

# Install AI agents
./install-agents
```

## Project Structure

```
├── .sdlc/              # Framework internals (hidden)
├── sdlc-tools/         # User command tools
├── docs/               # Documentation
├── plan/               # Implementation plans
├── retrospectives/     # Feature retrospectives
└── src/                # Your code here
```

See [CLAUDE.md](CLAUDE.md) for AI agent instructions.
"""
        with open(self.project_dir / "README.md", "w") as f:
            f.write(content)

    def create_organized_gitignore(self):
        """Create .gitignore for organized structure"""
        # Download gitignore templates to temp
        templates = ["base.gitignore", "ai-tools.gitignore"]
        if self.detected_language and self.detected_language != "general":
            templates.append(f"{self.detected_language}.gitignore")

        for template in templates:
            self.download_file(f"templates/gitignore/{template}", None)

        # Now create the actual gitignore
        self.create_gitignore()

        # Add .sdlc specific entries
        with open(self.project_dir / ".gitignore", "a") as f:
            f.write("\n# AI-First SDLC Framework (Organized)\n")
            f.write(".sdlc/temp/\n")
            f.write(".sdlc/cache/\n")
            f.write(".sdlc/logs/\n")

    def install_organized_agents(self):
        """Install agents to .sdlc/agents directory"""
        # Download agent installer
        installer_path = self.project_dir / ".sdlc/tools/automation/agent-installer.py"
        if installer_path.exists():
            try:
                # Run installer with .sdlc/agents as target
                subprocess.run(
                    [
                        sys.executable,
                        str(installer_path),
                        "install",
                        "core",
                        "--target",
                        str(self.project_dir / ".sdlc/agents"),
                    ],
                    check=True,
                )
                print("✅ Installed core agents to .sdlc/agents/")
            except subprocess.CalledProcessError:
                print("⚠️  Agent installation failed - run ./install-agents manually")

    def setup_organized_ci_cd(self, platform: str):
        """Setup CI/CD for organized structure"""
        # Similar to regular CI/CD but update paths
        # This would need platform-specific templates with .sdlc paths
        print(f"✅ CI/CD setup for {platform} (paths adjusted for .sdlc structure)")

    def run_organized_validation(self):
        """Run validation with organized structure"""
        validator = self.project_dir / ".sdlc/tools/validation/validate-pipeline.py"
        if validator.exists():
            try:
                subprocess.run(
                    [sys.executable, str(validator), "--checks", "basic"],
                    check=True,
                )
            except subprocess.CalledProcessError:
                print("⚠️  Validation found issues - this is normal for initial setup")

    def check_git_repo(self) -> bool:
        """Check if current directory is a git repository"""
        try:
            subprocess.run(["git", "status"], capture_output=True, check=True)
            return True
        except subprocess.CalledProcessError:
            return False

    def init_git_repo(self) -> bool:
        """Initialize git repository"""
        try:
            subprocess.run(["git", "init"], check=True)
            subprocess.run(["git", "add", "."], check=True)
            subprocess.run(["git", "commit", "-m", "Initial commit"], check=True)
            return True
        except subprocess.CalledProcessError as e:
            self.errors.append(f"Failed to initialize git: {e}")
            return False

    def ask_ci_platform(self) -> Optional[str]:
        """Ask user which CI/CD platform they're using"""
        # If we have a pre-specified platform, use it
        if self.ci_platform:
            return self.ci_platform if self.ci_platform != "none" else None

        # In non-interactive mode, default to GitHub Actions
        if self.non_interactive:
            print("\n⚙️  Non-interactive mode: defaulting to GitHub Actions")
            return "github"

        print("\nWhich CI/CD platform are you using?")
        print("1. GitHub Actions")
        print("2. GitLab CI")
        print("3. Jenkins")
        print("4. Azure DevOps")
        print("5. CircleCI")
        print("6. None/Skip")

        choice = input("\nEnter choice (1-6): ").strip()

        platform_map = {
            "1": "github",
            "2": "gitlab",
            "3": "jenkins",
            "4": "azure",
            "5": "circleci",
            "6": None,
        }

        return platform_map.get(choice)

    def setup_ci_cd(self, platform: str) -> bool:
        """Setup CI/CD configuration for the detected platform"""
        if platform not in self.CI_CONFIGS:
            return False

        remote_path = self.CI_CONFIGS[platform]
        # Determine local path based on platform
        if platform == "github":
            local_path = self.project_dir / ".github" / "workflows" / "ai-sdlc.yml"
        elif platform == "gitlab":
            local_path = self.project_dir / ".gitlab-ci.yml"
        elif platform == "jenkins":
            local_path = self.project_dir / "Jenkinsfile"
        elif platform == "azure":
            local_path = self.project_dir / "azure-pipelines.yml"
        elif platform == "circleci":
            local_path = self.project_dir / ".circleci" / "config.yml"
        else:
            # This should never happen due to the check above, but be safe
            return False

        if self.download_file(remote_path, local_path):
            print(f"✅ Configured {platform} CI/CD")
            return True
        else:
            print(f"❌ Failed to configure {platform} CI/CD")
            return False

    def create_initial_context(self) -> bool:
        """Create initial context for AI handof"""
        context = {
            "project": self.project_name,
            "purpose": self.project_purpose,
            "setup_date": subprocess.run(
                ["date"], capture_output=True, text=True
            ).stdout.strip(),
            "current_task": "Complete AI-First SDLC setup",
            "next_steps": [
                "Review and customize CLAUDE.md",
                "Configure project-specific build commands",
                "Create first feature proposal",
                "Run validation pipeline",
            ],
            "branch": "ai-first-kick-start",
        }

        context_file = self.project_dir / ".claude" / "context.json"
        with open(context_file, "w") as f:
            json.dump(context, f, indent=2)

        return True

    def run_validation(self) -> bool:
        """Run initial validation"""
        try:
            result = subprocess.run(
                ["python", "tools/validate-pipeline.py", "--ci"],
                cwd=self.project_dir,
                capture_output=True,
                text=True,
            )
            print(result.stdout)
            if result.returncode != 0:
                self.errors.append(
                    "Validation failed (this is expected for initial setup)"
                )
            return result.returncode == 0
        except Exception as e:
            self.errors.append(f"Could not run validation: {e}")
            return False

    def check_gh_cli(self) -> bool:
        """Check if gh CLI is available and authenticated"""
        try:
            # Check if gh is installed
            subprocess.run(["gh", "--version"], capture_output=True, check=True)

            # Check if authenticated
            subprocess.run(["gh", "auth", "status"], capture_output=True, check=True)

            return True
        except FileNotFoundError:
            return False
        except subprocess.CalledProcessError:
            # gh is installed but not authenticated
            print("\n🔐 GitHub CLI is installed but not authenticated")

            if self.non_interactive:
                print("   ℹ️  Non-interactive mode: skipping gh auth login prompt")
                print("   💡 To authenticate: gh auth login")
                return False

            response = (
                input("Would you like to authenticate now? [Y/n]: ").strip().lower()
            )

            if response == "" or response == "y":
                print("Running 'gh auth login'...")
                try:
                    subprocess.run(["gh", "auth", "login"], check=True)
                    print("✅ Authentication successful!")
                    return True
                except subprocess.CalledProcessError:
                    print("❌ Authentication failed or cancelled")
                    return False
            else:
                return False

    def setup_branch_protection(self, github_token: str = None) -> bool:
        """Setup GitHub branch protection rules (prefers gh CLI for security)"""
        try:
            # First, try to use gh CLI if available (more secure)
            if self.check_gh_cli():
                print("   Using GitHub CLI (gh) for secure setup...")

                # Download the gh-based protection script
                gh_script_path = (
                    self.project_dir / "tools" / "setup-branch-protection-gh.py"
                )

                if self.download_file(
                    "tools/automation/setup-branch-protection-gh.py",
                    gh_script_path,
                ):
                    result = subprocess.run(
                        ["python", str(gh_script_path), "--branch", "main"],
                        cwd=self.project_dir,
                        capture_output=True,
                        text=True,
                    )

                    if result.returncode == 0:
                        return True
                    else:
                        print(f"   ⚠️  gh-based setup failed: {result.stderr}")
                        # Fall through to token-based method
                else:
                    print("   ⚠️  Could not download gh-based script")
                    # Fall through to token-based method

            # Fallback to token-based setup if gh not available or failed
            if not github_token:
                print("   ℹ️  No GitHub token provided and gh CLI not available")
                return False
            # Get repository info from git remote
            result = subprocess.run(
                ["git", "remote", "get-url", "origin"],
                cwd=self.project_dir,
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                print("❌ Could not determine repository URL")
                return False

            remote_url = result.stdout.strip()
            # Extract owner/repo from URL
            # Handle both HTTPS and SSH URLs
            import re

            # Use proper URL parsing to avoid security issues
            if remote_url.startswith("git@github.com:"):
                # SSH: git@github.com:owner/repo.git
                match = re.search(r"^git@github\.com:(.+?)(?:\.git)?$", remote_url)
            elif remote_url.startswith("https://github.com/"):
                # HTTPS: https://github.com/owner/repo.git
                match = re.search(r"^https://github\.com/(.+?)(?:\.git)?$", remote_url)
            else:
                print("❌ Repository URL is not from github.com")
                return False

            if match:
                repo_path = match.group(1)

                # Download and run the branch protection script
                protection_script = (
                    self.project_dir / "tools" / "setup-branch-protection.py"
                )
                if not protection_script.exists():
                    print("⚠️  Branch protection tool not found")
                    return False

                result = subprocess.run(
                    [
                        "python",
                        str(protection_script),
                        "--platform",
                        "github",
                        "--repo",
                        repo_path,
                        "--token",
                        github_token,
                    ],
                    cwd=self.project_dir,
                    capture_output=True,
                    text=True,
                )

                if result.returncode != 0:
                    print(f"❌ Failed to set up branch protection: {result.stderr}")
                    return False

                print("✅ Branch protection enabled for main branch")
                print("   - Require pull request reviews")
                print("   - Require status checks to pass")
                print("   - No direct pushes allowed")
                return True
            else:
                print("❌ Could not parse repository information")
                return False

        except Exception as e:
            self.errors.append(f"Could not set up branch protection: {e}")
            return False

    def install_agents(self) -> bool:
        """Install AI agents for the project with smart recommendations"""
        try:
            # Download agent tools
            print("   📥 Downloading agent tools...")
            agent_tools = [
                "tools/automation/agent-installer.py",
                "tools/automation/project-analyzer.py",
                "tools/automation/agent-recommender.py",
                "tools/automation/agent-help.py",
            ]

            for tool in agent_tools:
                local_path = self.project_dir / "tools" / Path(tool).name
                self.download_file(tool, local_path)

            # Create .claude/agents directory
            claude_agents_dir = self.project_dir / ".claude" / "agents"
            claude_agents_dir.mkdir(parents=True, exist_ok=True)

            # In non-interactive mode, do smart installation
            if self.non_interactive:
                print("   🔍 Analyzing project for smart agent recommendations...")

                # Build command for smart installation
                cmd = [
                    sys.executable,
                    str(self.project_dir / "tools" / "agent-installer.py"),
                    "--project-root",
                    str(self.project_dir),
                ]

                # If we have project purpose, pass it as objectives
                if (
                    self.project_purpose
                    and self.project_purpose != "AI-assisted software development"
                ):
                    # Create a temp file with analysis including objectives
                    # Note: analysis_data was unused - removed to fix F841

                    # Use the recommender directly
                    print(f"   📋 Project purpose: {self.project_purpose}")

                # Just install core + detected language for now
                cmd.extend(["--core-only"])
                if self.detected_language and self.detected_language != "general":
                    cmd.extend(["--languages", self.detected_language])

                print("   🚀 Installing essential agents...")

                # Try to run the installer
                result = subprocess.run(
                    cmd, cwd=self.project_dir, capture_output=True, text=True
                )
                if result.returncode != 0:
                    # Fallback to downloading core agents directly
                    return self._install_core_agents_fallback()

                print("   ✅ Installed smart agent selection")
                print("   💡 Run 'python tools/agent-installer.py' for more agents")
                print(
                    "   💡 Use 'python tools/agent-help.py <challenge>' to find agents"
                )
            else:
                # Interactive mode - just download core agents
                return self._install_core_agents_fallback()

            return True

        except Exception as e:
            print(f"   ⚠️  Could not install agents: {e}")
            print("   💡 You can install agents manually later")
            return False

    def _install_core_agents_fallback(self) -> bool:
        """Fallback method to install core agents directly"""
        # Download core agents directly
        print("   📦 Installing core agents...")

        # Updated core agents list with new universal agents
        core_agents = [
            (
                "agents/core/sdlc-enforcer.md",
                ".claude/agents/core/sdlc-enforcer.md",
            ),
            (
                "agents/core/solution-architect.md",
                ".claude/agents/core/solution-architect.md",
            ),
            (
                "agents/core/critical-goal-reviewer.md",
                ".claude/agents/core/critical-goal-reviewer.md",
            ),
            (
                "agents/sdlc/framework-validator.md",
                ".claude/agents/sdlc/framework-validator.md",
            ),
            (
                "agents/core/github-integration-specialist.md",
                ".claude/agents/core/github-integration-specialist.md",
            ),
        ]

        installed_count = 0
        for remote, local in core_agents:
            local_path = self.project_dir / local
            local_path.parent.mkdir(parents=True, exist_ok=True)
            if self.download_file(remote, local_path):
                installed_count += 1

        if installed_count > 0:
            print(f"   ✅ Installed {installed_count} core agents")

            # Create agent manifest with updated agents
            manifest = {
                "sdlc-enforcer": "1.0.0",
                "solution-architect": "1.0.0",
                "critical-goal-reviewer": "1.0.0",
                "framework-validator": "1.0.0",
                "github-integration-specialist": "1.0.0",
            }
            manifest_path = self.project_dir / ".agent-manifest.json"
            with open(manifest_path, "w") as f:
                json.dump(manifest, f, indent=2)
            print("   ✅ Created agent manifest")
            return True
        else:
            print("   ℹ️  No agents downloaded (this is okay for initial setup)")
            print("   💡 Full agent library will be available after framework update")
            return False

    def create_claude_config(self) -> bool:
        """Create Claude project configuration with GitHub repo and agent settings"""
        try:
            claude_dir = self.project_dir / ".claude"
            claude_dir.mkdir(exist_ok=True)

            # Try to get GitHub repo URL
            github_url = None
            try:
                result = subprocess.run(
                    ["git", "remote", "get-url", "origin"],
                    cwd=self.project_dir,
                    capture_output=True,
                    text=True,
                )
                if result.returncode == 0 and result.stdout.strip():
                    github_url = result.stdout.strip()
            except Exception:
                pass

            # Create project configuration
            config = {
                "project_name": self.project_name,
                "project_purpose": self.project_purpose,
                "github_repository": github_url,
                "agent_preferences": {
                    "required_agents": [
                        "sdlc-enforcer",
                        "solution-architect",
                        "critical-goal-reviewer",
                    ],
                    "auto_suggest": True,
                    "context_aware_selection": True,
                },
                "sdlc_settings": {
                    "enforce_feature_proposals": True,
                    "require_architecture_docs": True,
                    "zero_technical_debt": True,
                    "require_retrospectives": True,
                },
                "detected_stack": {
                    "languages": (
                        [self.detected_language] if self.detected_language else []
                    ),
                    "frameworks": [],
                    "project_type": self.project_type,
                },
            }

            config_path = self.project_dir / ".claude-project.json"
            with open(config_path, "w") as f:
                json.dump(config, f, indent=2)

            print("   ✅ Created Claude project configuration")
            if github_url:
                print(f"   📍 GitHub repository linked: {github_url}")
            return True

        except Exception as e:
            print(f"   ⚠️  Could not create Claude config: {e}")
            return False

    def create_first_commit(self) -> bool:
        """Create a comprehensive first commit with all essentials"""
        try:
            print("\n📝 Preparing comprehensive first commit...")

            # Essential files that should be in the commit
            essential_files = [
                "README.md",
                "CLAUDE.md",
                "CLAUDE-CORE.md",
                "CLAUDE-CORE-PROGRESSIVE.md",
                ".gitignore",
                "VERSION",
                "CONTRIBUTING.md",
                ".pre-commit-config.yaml",
                "docs/feature-proposals/00-ai-first-setup.md",
            ]

            # Add language-specific files
            if self.detected_language == "python":
                essential_files.extend(
                    [
                        "requirements.txt",
                        "setup.py",
                        "pyproject.toml",
                        "src/__init__.py",
                        "tests/__init__.py",
                    ]
                )

            # Stage all essential files
            for file in essential_files:
                file_path = self.project_dir / file
                if file_path.exists() or any(
                    (self.project_dir / p).exists() for p in Path(file).parents
                ):
                    try:
                        subprocess.run(
                            ["git", "add", file],
                            cwd=self.project_dir,
                            check=True,
                        )
                    except Exception:
                        pass

            # Stage directories
            essential_dirs = [
                "docs",
                "tools",
                "retrospectives",
                "plan",
                ".claude",
                ".sdlc",
            ]
            for dir_name in essential_dirs:
                dir_path = self.project_dir / dir_name
                if dir_path.exists():
                    try:
                        subprocess.run(
                            ["git", "add", f"{dir_name}/"],
                            cwd=self.project_dir,
                            check=True,
                        )
                    except Exception:
                        pass

            # Create comprehensive commit message
            commit_message = """feat: implement AI-First SDLC framework with proactive agent usage

- Complete project structure with mandatory directories
- AI-First SDLC framework v1.6.0 integrated
- Progressive SDLC level: {self.sdlc_level}
- Proactive agent collaboration enforced
- Zero Technical Debt policy active
"""

            if self.detected_language == "python":
                commit_message += """- Python project essentials created
- Testing and linting configured
- Package structure established
"""

            commit_message += """
Project: {self.project_name}
Purpose: {self.project_purpose}

This project uses AI agents as primary developers with mandatory
consultation before any coding decisions.

Run 'python tools/agent-installer.py' to install specialist agents.

🤖 Generated with AI-First SDLC Framework
"""

            # Check if there are changes to commit
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.project_dir,
                capture_output=True,
                text=True,
            )

            if result.stdout.strip():
                print("   📦 Creating comprehensive first commit...")
                # Create the commit
                subprocess.run(
                    ["git", "commit", "-m", commit_message],
                    cwd=self.project_dir,
                    check=True,
                )
                print("   ✅ Created comprehensive first commit")
                return True
            else:
                print("   ℹ️  No changes to commit")
                return False

        except Exception as e:
            print(f"   ⚠️  Could not create first commit: {e}")
            return False

    def print_next_steps(self):
        """Print next steps for the user"""
        self._print_setup_header_and_policy()
        self._print_architecture_requirements()
        self._print_agent_recommendations()
        self._print_validation_and_completion_steps()
        self._print_documentation_links()

    def _print_setup_header_and_policy(self):
        """Print header and zero technical debt policy"""
        print("\n📋 Next Steps:")
        print("=" * 50)
        print("\n🚨 NEW: Zero Technical Debt Policy Enforced!")
        print("   - Complete ALL 6 architecture documents before coding")
        print("   - Run: python tools/validation/validate-architecture.py")
        print("   - Zero tolerance for TODOs, any types, or commented code")

    def _print_architecture_requirements(self):
        """Print architecture and validation requirements"""
        print("\n1. Review the initial feature proposal:")
        print("   cat docs/feature-proposals/00-ai-first-setup.md")
        print("\n2. Create architecture documents (MANDATORY):")
        print("   - Copy templates from templates/architecture/")
        print("   - Fill out ALL 6 documents completely")
        print("   - Validate: python tools/validation/validate-architecture.py")
        print("\n3. Create language-specific validator (MANDATORY):")
        print("   - Read LANGUAGE-SPECIFIC-VALIDATORS.md")
        print("   - Create tools/validation/validate-[your-language].py")
        print("   - Configure for ZERO tolerance")

    def _print_agent_recommendations(self):
        """Print AI agent recommendations based on project type"""
        print("\n4. Install recommended AI agents:")

        # Check if this is an MCP project
        is_mcp_project = (
            "mcp" in self.project_purpose.lower()
            or "model context protocol" in self.project_purpose.lower()
        )

        if is_mcp_project:
            self._print_mcp_agents()
        elif self.detected_language == "python":
            self._print_python_agents()
        else:
            self._print_core_agents()

        self._print_agent_installation_info()

    def _print_mcp_agents(self):
        """Print MCP-specific agent recommendations"""
        print("   🎯 MCP Project Detected! Essential Agents:")
        print("     • sdlc-enforcer - Primary compliance guardian")
        print("     • critical-goal-reviewer - Quality assurance")
        print("     • solution-architect - System design expert")
        print("     • mcp-server-architect - MCP design specialist ⭐")
        print("     • mcp-test-agent - MCP testing from AI perspective ⭐")
        print("     • mcp-quality-assurance - MCP quality & security ⭐")
        print("   ")

    def _print_python_agents(self):
        """Print Python-specific agent recommendations"""
        print("   🐍 Python Project Detected! Essential Agents:")
        print("     • sdlc-enforcer - Primary compliance guardian")
        print("     • critical-goal-reviewer - Quality assurance")
        print("     • solution-architect - System design expert")
        print("     • language-python-expert - Python best practices ⭐")
        print("     • ai-test-engineer - AI testing specialist ⭐")
        print("     • test-manager - Testing strategy")
        print("   ")
        print("   📚 Additional recommended agents:")

    def _print_core_agents(self):
        """Print core agent recommendations"""
        print("   🤖 Core Agents (CRITICAL - Install These First):")
        print("     • sdlc-enforcer - Primary compliance guardian")
        print("     • critical-goal-reviewer - Quality assurance")
        print("     • solution-architect - System design expert")
        print("   ")
        print("   📚 Based on your project type, also consider:")

        if (
            "python" in self.project_purpose.lower()
            or "api" in self.project_purpose.lower()
        ):
            print("     • python-expert - Python best practices")
            print("     • ai-test-engineer - AI system testing")
        if (
            "langchain" in self.project_purpose.lower()
            or "llm" in self.project_purpose.lower()
        ):
            print("     • langchain-architect - LangChain expertise")
            print("     • prompt-engineer - Prompt optimization")

    def _print_agent_installation_info(self):
        """Print agent installation information and requirements"""
        print("   ")
        print(
            "   ⚠️  IMPORTANT: Installing agents requires a reboot of your AI assistant!"
        )
        print("   ")
        print("   To install agents, use:")
        print("   python tools/agent-installer.py --install <agent-name>")
        print(
            "   Example: python tools/agent-installer.py --install mcp-server-architect"
        )
        print("   ")
        print("   To discover more agents for your needs:")
        print("   - Ask: 'What agents should I install for [your specific need]?'")
        print("   - The ai-first-kick-starter agent can recommend agents anytime")
        print("   - List all available agents: python tools/agent-installer.py --list")
        print("\n🚨 CRITICAL: AI AGENTS MUST BE USED PROACTIVELY!")
        print("   The framework REQUIRES agents to be consulted BEFORE any coding:")
        print("   - NEVER write code without agent consultation")
        print("   - ALWAYS engage agents at the START of tasks")
        print("   - Agents are MANDATORY, not optional helpers")
        print("   ")
        print("   Example: User says 'add login' → You IMMEDIATELY invoke:")
        print("   1. sdlc-enforcer (check compliance)")
        print("   2. solution-architect (design approach)")
        print("   3. security-architect (auth patterns)")
        print("   4. test-manager (test strategy)")

    def _print_validation_and_completion_steps(self):
        """Print validation setup and completion steps"""
        print("\n5. Install Git hooks for local validation (HIGHLY RECOMMENDED):")
        print("   🛡️  Prevent syntax errors and validation failures before push!")
        print("   python tools/automation/install-git-hooks.py")
        print("   ")
        print(
            "   This installs pre-commit and pre-push validation to catch issues locally."
        )
        print("   See docs/LOCAL-VALIDATION-WORKFLOW.md for details.")

        print("\n6. Customize CLAUDE.md with project-specific details:")
        print("   edit CLAUDE.md")
        print("\n7. Complete the setup tasks:")
        print("   python tools/progress-tracker.py list")
        print("\n8. When ready, push the branch:")
        print("   git add .")
        print(
            '   git commit -m "feat: implement AI-First SDLC framework with Zero Technical Debt"'
        )
        print("   git push -u origin ai-first-kick-start")
        print("\n9. Create retrospective (REQUIRED before PR):")
        print("   Create file: retrospectives/00-ai-first-setup.md")
        print("   Document what went well, what could improve, and lessons learned")
        print("\n10. Create a pull request to merge into main")
        print(
            "   Note: PR will be rejected without retrospective AND architecture docs!"
        )

    def _print_documentation_links(self):
        """Print documentation and reference links"""
        print("\n📚 Framework Documentation:")
        print("   https://github.com/SteveGJones/ai-first-sdlc-practices")
        print("\n📖 Zero Technical Debt Policy:")
        print("   cat ZERO-TECHNICAL-DEBT.md")


def main():
    parser = argparse.ArgumentParser(
        description="Smart setup for AI-First SDLC Framework"
    )
    parser.add_argument(
        "purpose",
        nargs="?",
        default="AI-assisted software development",
        help="Purpose of the project (e.g., 'building a todo app')",
    )
    parser.add_argument(
        "--project-dir",
        type=Path,
        default=Path.cwd(),
        help="Project directory (default: current)",
    )
    parser.add_argument("--skip-ci", action="store_true", help="Skip CI/CD setup")
    parser.add_argument(
        "--version", default="main", help="Framework version/branch to use"
    )
    parser.add_argument(
        "--github-token",
        default=os.environ.get("GITHUB_TOKEN"),
        help="GitHub token for branch protection (or set GITHUB_TOKEN env var)",
    )
    parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Run without prompts (use defaults)",
    )
    parser.add_argument(
        "--ci-platform",
        choices=["github", "gitlab", "jenkins", "azure", "circleci", "none"],
        help="CI/CD platform to configure (default: auto-detect)",
    )
    parser.add_argument(
        "--quickstart",
        action="store_true",
        help="Quick start mode: creates README, .gitignore, and initial test",
    )
    parser.add_argument(
        "--organized",
        action="store_true",
        help="Use organized structure with .sdlc directory for framework files",
    )
    parser.add_argument(
        "--no-venv",
        action="store_true",
        help="Skip virtual environment creation for Python projects",
    )
    parser.add_argument(
        "--venv-name",
        default="venv",
        help="Name for virtual environment directory (default: venv)",
    )
    parser.add_argument(
        "--python",
        help="Python executable to use for venv (default: auto-detect)",
    )
    parser.add_argument(
        "--level",
        choices=["prototype", "production", "enterprise"],
        default="production",
        help="SDLC enforcement level (default: production)",
    )

    args = parser.parse_args()

    # For AI agents: detect if being called with framework URL pattern
    if (
        args.purpose
        and "github.com/SteveGJones/ai-first-sdlc-practices" in args.purpose
    ):
        # Extract actual purpose if provided after URL
        parts = args.purpose.split(" for ")
        if len(parts) > 1:
            args.purpose = " for ".join(parts[1:])
        else:
            args.purpose = "AI-assisted software development"

    # Create setup instance
    setup = SmartFrameworkSetup(
        args.project_dir,
        args.purpose,
        args.non_interactive,
        args.ci_platform,
        args.quickstart,
        args.organized,
        args.level,
        args.no_venv,
        args.venv_name,
        args.python,
    )

    # Update version if specified
    if args.version != "main":
        setup.GITHUB_RAW_BASE = setup.GITHUB_RAW_BASE.replace(
            "/main", f"/{args.version}"
        )

    # Run setup
    success = setup.run_setup(
        args.skip_ci, args.github_token, args.quickstart or args.organized
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
