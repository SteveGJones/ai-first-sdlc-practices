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
        "tools/automation/setup-branch-protection.py": "tools/setup-branch-protection.py",
        "tools/automation/setup-branch-protection-gh.py": "tools/setup-branch-protection-gh.py",
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
        """Generate project-specific CLAUDE.md content using full template"""
        try:
            # Download the full template
            template_url = f"{self.GITHUB_RAW_BASE}/templates/CLAUDE.md"
            response = urllib.request.urlopen(template_url)
            template_content = response.read().decode('utf-8')
            
            # Customize the template with project-specific information
            customized_content = template_content.replace(
                "**Project**: [Your Project Name]", 
                f"**Project**: {self.project_name}"
            ).replace(
                "**Purpose**: [Brief description of what this project does]",
                f"**Purpose**: {self.project_purpose}"
            ).replace(
                "[CUSTOMIZE: Brief overview of your project and its main purpose]",
                f"This project focuses on {self.project_purpose.lower()}."
            )
            
            return customized_content
            
        except Exception as e:
            print(f"⚠️  Could not download template, using fallback: {e}")
            # Fallback to simplified version if template download fails
            return f"""# CLAUDE.md

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
    
    def setup_project(self, skip_ci: bool = False, github_token: str = None) -> bool:
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
        
        # Setup branch protection for GitHub repos
        detected_platform = self.detect_ci_platform() or "github"
        if detected_platform == "github":
            if self.check_gh_cli():
                print("\n🔒 Setting up branch protection using GitHub CLI...")
                self.setup_branch_protection()
            elif github_token:
                print("\n🔒 Setting up branch protection using token...")
                self.setup_branch_protection(github_token)
            else:
                print("\n💡 Tip: Install 'gh' CLI or provide GITHUB_TOKEN for automatic branch protection")
        
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
    
    def check_gh_cli(self) -> bool:
        """Check if gh CLI is available and authenticated"""
        try:
            # Check if gh is installed
            subprocess.run(
                ["gh", "--version"],
                capture_output=True,
                check=True
            )
            
            # Check if authenticated
            result = subprocess.run(
                ["gh", "auth", "status"],
                capture_output=True,
                check=True
            )
            
            return True
        except FileNotFoundError:
            return False
        except subprocess.CalledProcessError:
            # gh is installed but not authenticated
            print("\n🔐 GitHub CLI is installed but not authenticated")
            response = input("Would you like to authenticate now? [Y/n]: ").strip().lower()
            
            if response == '' or response == 'y':
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
                gh_script_url = f"{self.GITHUB_RAW_BASE}/tools/automation/setup-branch-protection-gh.py"
                gh_script_path = self.project_dir / "tools" / "setup-branch-protection-gh.py"
                
                if self.download_file("tools/automation/setup-branch-protection-gh.py", gh_script_path):
                    result = subprocess.run(
                        ["python", str(gh_script_path), "--branch", "main"],
                        cwd=self.project_dir,
                        capture_output=True,
                        text=True
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
                text=True
            )
            
            if result.returncode != 0:
                print("❌ Could not determine repository URL")
                return False
                
            remote_url = result.stdout.strip()
            
            # Extract owner/repo from URL
            # Handle both HTTPS and SSH URLs
            import re
            if "github.com" in remote_url:
                if remote_url.startswith("git@"):
                    # SSH: git@github.com:owner/repo.git
                    match = re.search(r'github\.com:(.+?)(?:\.git)?$', remote_url)
                else:
                    # HTTPS: https://github.com/owner/repo.git
                    match = re.search(r'github\.com/(.+?)(?:\.git)?$', remote_url)
                
                if match:
                    repo_path = match.group(1)
                    owner, repo = repo_path.split('/')
                    
                    # Download and run the branch protection script
                    protection_script = self.project_dir / "tools" / "setup-branch-protection.py"
                    if protection_script.exists():
                        result = subprocess.run(
                            [
                                "python", str(protection_script),
                                "--platform", "github",
                                "--repo", repo_path,
                                "--token", github_token
                            ],
                            cwd=self.project_dir,
                            capture_output=True,
                            text=True
                        )
                        
                        if result.returncode == 0:
                            print("✅ Branch protection enabled for main branch")
                            print("   - Require pull request reviews")
                            print("   - Require status checks to pass")
                            print("   - No direct pushes allowed")
                            return True
                        else:
                            print(f"❌ Failed to set up branch protection: {result.stderr}")
                            return False
                    else:
                        print("⚠️  Branch protection tool not found")
                        return False
                else:
                    print("❌ Could not parse repository information")
                    return False
            else:
                print("ℹ️  Branch protection is only supported for GitHub repositories")
                return False
                
        except Exception as e:
            self.errors.append(f"Could not set up branch protection: {e}")
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
    parser.add_argument(
        "--github-token",
        default=os.environ.get('GITHUB_TOKEN'),
        help="GitHub token for branch protection (or set GITHUB_TOKEN env var)"
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
    success = setup.setup_project(args.skip_ci, args.github_token)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()