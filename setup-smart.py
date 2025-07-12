#!/usr/bin/env python3
"""
AI-First SDLC Smart Setup Tool
Downloads and configures AI-First SDLC framework without cloning the entire repository
"""

import os
import sys
import json
import subprocess
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import urllib.request
import urllib.error
import tempfile
import shutil


class SmartFrameworkSetup:
    """Smart installer for AI-First SDLC Framework"""
    
    GITHUB_RAW_BASE = "https://raw.githubusercontent.com/SteveGJones/ai-first-sdlc-practices/main"
    
    # Files to download for basic setup
    ESSENTIAL_FILES = {
        "templates/CLAUDE.md": "templates/CLAUDE.md",
        "templates/feature-proposal.md": "docs/feature-proposals/template-feature-proposal.md",
        "templates/implementation-plan.md": "plan/template-implementation-plan.md", 
        "templates/retrospective.md": "retrospectives/template-retrospective.md",
        "tools/automation/context-manager.py": "tools/context-manager.py",
        "tools/automation/progress-tracker.py": "tools/progress-tracker.py",
        "tools/validation/check-feature-proposal.py": "tools/check-feature-proposal.py",
        "tools/validation/validate-pipeline.py": "tools/validate-pipeline.py"
    }
    
    # CI/CD configurations by platform
    CI_CONFIGS = {
        "github": "examples/ci-cd/.github/workflows/ai-sdlc.yml",
        "gitlab": "examples/ci-cd/gitlab/.gitlab-ci.yml",
        "jenkins": "examples/ci-cd/jenkins/Jenkinsfile",
        "azure": "examples/ci-cd/azure-devops/azure-pipelines.yml",
        "circleci": "examples/ci-cd/circleci/.circleci/config.yml"
    }
    
    def __init__(self, project_dir: Optional[Path] = None, project_purpose: str = None):
        self.project_dir = project_dir or Path.cwd()
        self.project_purpose = project_purpose or "AI-assisted software development"
        self.project_name = self.project_dir.name
        self.errors = []
        
    def download_file(self, remote_path: str, local_path: Path) -> bool:
        """Download a file from the framework repository"""
        url = f"{self.GITHUB_RAW_BASE}/{remote_path}"
        
        try:
            # Create parent directory if needed
            local_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Download file
            with urllib.request.urlopen(url) as response:
                content = response.read()
                
            # Write to local file
            with open(local_path, 'wb') as f:
                f.write(content)
                
            # Make executable if it's a Python script
            if local_path.suffix == '.py':
                os.chmod(local_path, 0o755)
                
            return True
            
        except urllib.error.URLError as e:
            self.errors.append(f"Failed to download {remote_path}: {e}")
            return False
    
    def detect_ci_platform(self) -> Optional[str]:
        """Detect which CI/CD platform is being used"""
        # Check environment variables
        if os.getenv('GITHUB_ACTIONS') == 'true':
            return 'github'
        elif os.getenv('GITLAB_CI') == 'true':
            return 'gitlab'
        elif os.getenv('JENKINS_URL'):
            return 'jenkins'
        elif os.getenv('TF_BUILD') == 'True':
            return 'azure'
        elif os.getenv('CIRCLECI') == 'true':
            return 'circleci'
        
        # Check for existing CI files
        if (self.project_dir / '.github' / 'workflows').exists():
            return 'github'
        elif (self.project_dir / '.gitlab-ci.yml').exists():
            return 'gitlab'
        elif (self.project_dir / 'Jenkinsfile').exists():
            return 'jenkins'
        elif (self.project_dir / 'azure-pipelines.yml').exists():
            return 'azure'
        elif (self.project_dir / '.circleci' / 'config.yml').exists():
            return 'circleci'
            
        return None
    
    def generate_claude_md(self) -> str:
        """Generate project-specific CLAUDE.md content"""
        return f"""# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Project**: {self.project_name}
**Purpose**: {self.project_purpose}
**Framework**: AI-First SDLC Practices (https://github.com/SteveGJones/ai-first-sdlc-practices)

## Development Workflow

### MANDATORY: Follow AI-First SDLC Practices

1. **Never push directly to main branch**
2. **Always create feature proposals before implementing**
3. **Track progress with the progress tracker**
4. **Create retrospectives after completing features**

### Quick Commands

```bash
# Create feature branch
git checkout -b feature/feature-name

# Track progress
python tools/progress-tracker.py add "Task description"
python tools/progress-tracker.py list
python tools/progress-tracker.py complete <task_id>

# Validate work
python tools/validate-pipeline.py --ci

# Save context
python tools/context-manager.py handoff --current "Working on X" --next "Continue with Y"
```

## Project-Specific Configuration

[TODO: Add project-specific build commands, dependencies, and architecture notes here]

## Git Workflow

1. Create feature proposal: `docs/feature-proposals/XX-feature-name.md`
2. Create feature branch: `git checkout -b feature/feature-name`
3. Implement changes
4. Run validation: `python tools/validate-pipeline.py`
5. Create retrospective: `retrospectives/XX-feature-name.md`
6. Push and create PR: `git push -u origin feature/feature-name`

## Important Notes

- This project follows AI-First SDLC practices
- All changes must go through feature branches
- Feature proposals are required before implementation
- Retrospectives document lessons learned
"""
    
    def create_initial_feature_proposal(self) -> bool:
        """Create the initial setup feature proposal"""
        proposal_dir = self.project_dir / "docs" / "feature-proposals"
        proposal_dir.mkdir(parents=True, exist_ok=True)
        
        proposal_path = proposal_dir / "00-ai-first-setup.md"
        
        content = f"""# Feature Proposal: AI-First SDLC Setup

**Proposal Number:** 00  
**Status:** In Progress  
**Author:** AI Setup Assistant  
**Created:** {subprocess.run(['date', '+%Y-%m-%d'], capture_output=True, text=True).stdout.strip()}  
**Target Branch:** `ai-first-kick-start`  
**Implementation Type:** Infrastructure

---

## Executive Summary

Initial setup of AI-First SDLC practices for {self.project_name}. This establishes the framework, tools, and workflows needed for AI-assisted development.

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
        
        with open(proposal_path, 'w') as f:
            f.write(content)
            
        return True
    
    def setup_project(self, skip_ci: bool = False) -> bool:
        """Run the complete setup process"""
        print("🚀 AI-First SDLC Smart Setup")
        print("=" * 50)
        print(f"Project: {self.project_name}")
        print(f"Purpose: {self.project_purpose}")
        print()
        
        # Check git repository
        if not self.check_git_repo():
            print("⚠️  No git repository found. Initializing...")
            self.init_git_repo()
        
        # Create ai-first-kick-start branch
        print("\n🌿 Creating ai-first-kick-start branch...")
        try:
            subprocess.run(["git", "checkout", "-b", "ai-first-kick-start"], 
                         capture_output=True, check=True)
            print("✅ Created and switched to ai-first-kick-start branch")
        except subprocess.CalledProcessError:
            print("ℹ️  Branch already exists or couldn't be created")
        
        # Download essential files
        print("\n📥 Downloading framework files...")
        for remote, local in self.ESSENTIAL_FILES.items():
            local_path = self.project_dir / local
            if self.download_file(remote, local_path):
                print(f"✅ Downloaded {local}")
            else:
                print(f"❌ Failed to download {local}")
        
        # Create directory structure
        print("\n📁 Creating directory structure...")
        dirs = ["docs/feature-proposals", "plan", "retrospectives", ".claude"]
        for dir_path in dirs:
            (self.project_dir / dir_path).mkdir(parents=True, exist_ok=True)
            print(f"✅ Created {dir_path}/")
        
        # Generate CLAUDE.md
        print("\n📝 Generating project-specific CLAUDE.md...")
        claude_content = self.generate_claude_md()
        with open(self.project_dir / "CLAUDE.md", 'w') as f:
            f.write(claude_content)
        print("✅ Created CLAUDE.md")
        
        # Create symlinks for other AI files
        for ai_file in ["GEMINI.md", "GPT.md"]:
            target = self.project_dir / ai_file
            if not target.exists():
                target.symlink_to("CLAUDE.md")
                print(f"✅ Created {ai_file} → CLAUDE.md")
        
        # Setup CI/CD if not skipped
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
        
        # Create initial feature proposal
        print("\n📋 Creating initial feature proposal...")
        self.create_initial_feature_proposal()
        print("✅ Created docs/feature-proposals/00-ai-first-setup.md")
        
        # Create initial context
        print("\n💾 Creating initial context...")
        self.create_initial_context()
        
        # Run initial validation
        print("\n🔍 Running initial validation...")
        self.run_validation()
        
        if self.errors:
            print("\n⚠️  Setup completed with errors:")
            for error in self.errors:
                print(f"  - {error}")
        else:
            print("\n✅ Setup completed successfully!")
        
        self.print_next_steps()
        return len(self.errors) == 0
    
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
            "6": None
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
        
        if self.download_file(remote_path, local_path):
            print(f"✅ Configured {platform} CI/CD")
            return True
        else:
            print(f"❌ Failed to configure {platform} CI/CD")
            return False
    
    def create_initial_context(self) -> bool:
        """Create initial context for AI handoff"""
        context = {
            "project": self.project_name,
            "purpose": self.project_purpose,
            "setup_date": subprocess.run(['date'], capture_output=True, text=True).stdout.strip(),
            "current_task": "Complete AI-First SDLC setup",
            "next_steps": [
                "Review and customize CLAUDE.md",
                "Configure project-specific build commands",
                "Create first feature proposal",
                "Run validation pipeline"
            ],
            "branch": "ai-first-kick-start"
        }
        
        context_file = self.project_dir / ".claude" / "context.json"
        with open(context_file, 'w') as f:
            json.dump(context, f, indent=2)
            
        return True
    
    def run_validation(self) -> bool:
        """Run initial validation"""
        try:
            result = subprocess.run(
                ["python", "tools/validate-pipeline.py", "--ci"],
                cwd=self.project_dir,
                capture_output=True,
                text=True
            )
            print(result.stdout)
            if result.returncode != 0:
                self.errors.append("Validation failed (this is expected for initial setup)")
            return result.returncode == 0
        except Exception as e:
            self.errors.append(f"Could not run validation: {e}")
            return False
    
    def print_next_steps(self):
        """Print next steps for the user"""
        print("\n📋 Next Steps:")
        print("=" * 50)
        print("\n1. Review the initial feature proposal:")
        print("   cat docs/feature-proposals/00-ai-first-setup.md")
        print("\n2. Customize CLAUDE.md with project-specific details:")
        print("   edit CLAUDE.md")
        print("\n3. Complete the setup tasks:")
        print("   python tools/progress-tracker.py list")
        print("\n4. When ready, push the branch:")
        print("   git add .")
        print("   git commit -m \"feat: implement AI-First SDLC framework\"")
        print("   git push -u origin ai-first-kick-start")
        print("\n5. Create a pull request to merge into main")
        print("\n📚 Framework Documentation:")
        print("   https://github.com/SteveGJones/ai-first-sdlc-practices")


def main():
    parser = argparse.ArgumentParser(
        description="Smart setup for AI-First SDLC Framework"
    )
    parser.add_argument(
        "purpose",
        nargs="?",
        default="AI-assisted software development",
        help="Purpose of the project (e.g., 'building a todo app')"
    )
    parser.add_argument(
        "--project-dir",
        type=Path,
        default=Path.cwd(),
        help="Project directory (default: current)"
    )
    parser.add_argument(
        "--skip-ci",
        action="store_true",
        help="Skip CI/CD setup"
    )
    parser.add_argument(
        "--version",
        default="main",
        help="Framework version/branch to use"
    )
    
    args = parser.parse_args()
    
    # For AI agents: detect if being called with framework URL pattern
    if args.purpose and "github.com/SteveGJones/ai-first-sdlc-practices" in args.purpose:
        # Extract actual purpose if provided after URL
        parts = args.purpose.split(" for ")
        if len(parts) > 1:
            args.purpose = " for ".join(parts[1:])
        else:
            args.purpose = "AI-assisted software development"
    
    # Create setup instance
    setup = SmartFrameworkSetup(args.project_dir, args.purpose)
    
    # Update version if specified
    if args.version != "main":
        setup.GITHUB_RAW_BASE = setup.GITHUB_RAW_BASE.replace("/main", f"/{args.version}")
    
    # Run setup
    success = setup.setup_project(args.skip_ci)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()