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
from typing import Optional
import urllib.request
import urllib.error


class SmartFrameworkSetup:
    """Smart installer for AI-First SDLC Framework"""
    
    GITHUB_RAW_BASE = "https://raw.githubusercontent.com/SteveGJones/ai-first-sdlc-practices/main"
    
    # Files to download for basic setup
    ESSENTIAL_FILES = {
        # New hierarchical instruction system
        "CLAUDE-CORE.md": "CLAUDE-CORE.md",
        "CLAUDE-SETUP.md": "CLAUDE-SETUP.md",
        "CLAUDE-CONTEXT-architecture.md": "CLAUDE-CONTEXT-architecture.md",
        "CLAUDE-CONTEXT-validation.md": "CLAUDE-CONTEXT-validation.md",
        "CLAUDE-CONTEXT-update.md": "CLAUDE-CONTEXT-update.md",
        "CLAUDE-CONTEXT-language-validators.md": "CLAUDE-CONTEXT-language-validators.md",
        "CLAUDE-CONTEXT-logging.md": "CLAUDE-CONTEXT-logging.md",
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
        # Zero Technical Debt additions
        "ZERO-TECHNICAL-DEBT.md": "ZERO-TECHNICAL-DEBT.md",
        "LANGUAGE-SPECIFIC-VALIDATORS.md": "LANGUAGE-SPECIFIC-VALIDATORS.md",
        "tools/validation/validate-architecture.py": "tools/validation/validate-architecture.py",
        "tools/validation/check-technical-debt.py": "tools/validation/check-technical-debt.py",
        "tools/validation/check-instruction-size.py": "tools/validation/check-instruction-size.py",
        "tools/validation/check-logging-compliance.py": "tools/validation/check-logging-compliance.py",
        "templates/quality-gates.yaml": "templates/quality-gates.yaml",
        # Architecture templates
        "templates/architecture/requirements-traceability-matrix.md": "templates/architecture/requirements-traceability-matrix.md",
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
        "templates/tests/framework_test.rs": None
    }
    
    # CI/CD configurations by platform
    CI_CONFIGS = {
        "github": "examples/ci-cd/.github/workflows/ai-sdlc.yml",
        "gitlab": "examples/ci-cd/gitlab/.gitlab-ci.yml",
        "jenkins": "examples/ci-cd/jenkins/Jenkinsfile",
        "azure": "examples/ci-cd/azure-devops/azure-pipelines.yml",
        "circleci": "examples/ci-cd/circleci/.circleci/config.yml"
    }
    
    # Agent installation files
    AGENT_FILES = {
        "tools/automation/agent-installer.py": "tools/agent-installer.py",
        "tools/automation/project-analyzer.py": "tools/project-analyzer.py",
        "tools/automation/agent-recommender.py": "tools/agent-recommender.py",
        "tools/automation/agent-help.py": "tools/agent-help.py",
        "release/agent-manifest.json": None,  # Downloaded for metadata
        "release/agents/README.md": None  # Downloaded for reference
    }
    
    def __init__(self, project_dir: Optional[Path] = None, project_purpose: str = None, 
                 non_interactive: bool = False, ci_platform: str = None, quickstart: bool = False):
        self.project_dir = project_dir or Path.cwd()
        self.project_purpose = project_purpose or "AI-assisted software development"
        self.project_name = self.project_dir.name
        self.errors = []
        self.non_interactive = non_interactive or not sys.stdin.isatty()
        self.ci_platform = ci_platform
        self.detected_language = None
        self.quickstart = quickstart
        
    def download_file(self, remote_path: str, local_path: Optional[Path]) -> bool:
        """Download a file from the framework repository"""
        url = f"{self.GITHUB_RAW_BASE}/{remote_path}"
        
        try:
            # Download file
            with urllib.request.urlopen(url) as response:
                content = response.read()
            
            # If local_path is None, save to temp directory for templates
            if local_path is None:
                temp_dir = self.project_dir / '.ai-sdlc-temp'
                temp_dir.mkdir(parents=True, exist_ok=True)
                local_path = temp_dir / Path(remote_path).name
            
            # Create parent directory if needed
            local_path.parent.mkdir(parents=True, exist_ok=True)
                
            # Write to local file
            with open(local_path, 'wb') as f:
                f.write(content)
                
            # Make executable if it's a Python script (owner only)
            if local_path.suffix == '.py':
                os.chmod(local_path, 0o700)  # Owner read/write/execute only
                
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
    
    def detect_project_language(self) -> str:
        """Detect the primary language of the project"""
        import glob
        
        # Language indicators with priority (check in order)
        indicators = [
            ('python', ['*.py', 'requirements.txt', 'setup.py', 'pyproject.toml', 'Pipfile']),
            ('node', ['*.js', '*.ts', '*.jsx', '*.tsx', 'package.json', 'yarn.lock', 'package-lock.json']),
            ('go', ['*.go', 'go.mod', 'go.sum']),
            ('rust', ['*.rs', 'Cargo.toml', 'Cargo.lock']),
            ('java', ['*.java', 'pom.xml', 'build.gradle', 'build.gradle.kts']),
            ('ruby', ['*.rb', 'Gemfile', 'Gemfile.lock', 'Rakefile']),
            ('csharp', ['*.cs', '*.csproj', '*.sln']),
            ('php', ['*.php', 'composer.json', 'composer.lock']),
        ]
        
        # Check if any language files exist
        language_detected = False
        for lang, patterns in indicators:
            for pattern in patterns:
                # Check both root and subdirectories
                if glob.glob(str(self.project_dir / pattern)) or \
                   glob.glob(str(self.project_dir / '**' / pattern), recursive=True):
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
                            "7": "general"
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
        self.detected_language = 'general'
        return 'general'
    
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
    
    def create_gitignore(self) -> bool:
        """Create comprehensive .gitignore file"""
        gitignore_path = self.project_dir / ".gitignore"
        
        # Check if .gitignore already exists
        existing_content = ""
        if gitignore_path.exists():
            # Create backup
            import shutil
            from datetime import datetime
            backup_name = f".gitignore.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            backup_path = self.project_dir / backup_name
            shutil.copy2(gitignore_path, backup_path)
            print(f"📁 Created backup: {backup_name}")
            
            with open(gitignore_path, 'r') as f:
                existing_content = f.read()
            print("📝 Updating existing .gitignore...")
        else:
            print("📝 Creating new .gitignore...")
        
        # Detect language if not already done
        if not self.detected_language:
            self.detect_project_language()
        
        # Load gitignore templates
        templates_to_combine = [
            'base.gitignore',
            'ai-tools.gitignore',
            f'{self.detected_language}.gitignore' if self.detected_language != 'general' else 'general.gitignore'
        ]
        
        combined_content = []
        for template_name in templates_to_combine:
            try:
                # Read from downloaded templates
                template_path = self.project_dir / '.ai-sdlc-temp' / template_name
                if template_path.exists():
                    with open(template_path, 'r') as f:
                        content = f.read()
                        if content.strip():  # Only add non-empty templates
                            combined_content.append(f"# === {template_name.replace('.gitignore', '').title()} Patterns ===")
                            combined_content.append(content.strip())
                            combined_content.append("")  # Empty line between sections
            except Exception as e:
                self.errors.append(f"Could not read template {template_name}: {e}")
        
        # Combine with existing content if any
        if existing_content:
            # Parse existing patterns to avoid duplicates
            existing_patterns = set()
            for line in existing_content.strip().split('\n'):
                line = line.strip()
                if line and not line.startswith('#'):
                    existing_patterns.add(line)
            
            # Filter out duplicate patterns from new content
            filtered_content = []
            for section in combined_content:
                if section.startswith('# ==='):
                    filtered_content.append(section)
                else:
                    # Filter individual patterns
                    filtered_lines = []
                    for line in section.split('\n'):
                        line_stripped = line.strip()
                        if not line_stripped or line_stripped.startswith('#') or line_stripped not in existing_patterns:
                            filtered_lines.append(line)
                    if filtered_lines:
                        filtered_content.append('\n'.join(filtered_lines))
            
            # Combine existing and new content
            combined_content = [existing_content.strip(), 
                              "\n# === AI-First SDLC Framework Patterns (Added) ===\n"] + filtered_content
        
        # Write the combined content
        final_content = "\n".join(combined_content)
        with open(gitignore_path, 'w') as f:
            f.write(final_content)
        
        print(f"✅ Created comprehensive .gitignore (detected language: {self.detected_language})")
        return True
    
    def create_initial_test(self) -> bool:
        """Create initial framework verification test based on detected language"""
        if not self.detected_language:
            self.detect_project_language()
        
        # Map language to test file
        test_mappings = {
            'python': ('test_framework_setup.py', 'test_framework_setup.py'),
            'node': ('framework.test.js', 'test/framework.test.js'),
            'go': ('test-framework.sh', 'test-framework.sh'),
            'java': ('FrameworkTest.java', 'src/test/java/FrameworkTest.java'),
            'ruby': ('framework_test.rb', 'test/framework_test.rb'),
            'rust': ('framework_test.rs', 'tests/framework_test.rs'),
            'general': ('test-framework.sh', 'test-framework.sh')
        }
        
        # Get test file info
        template_name, target_path = test_mappings.get(self.detected_language, test_mappings['general'])
        
        # Create test directory if needed
        test_file_path = self.project_dir / target_path
        test_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Copy test from downloaded templates
        template_path = self.project_dir / '.ai-sdlc-temp' / template_name
        if template_path.exists():
            with open(template_path, 'r') as f:
                content = f.read()
            with open(test_file_path, 'w') as f:
                f.write(content)
            
            # Make shell script executable by owner only
            if template_name.endswith('.sh'):
                os.chmod(test_file_path, 0o700)  # Owner: rwx, Group: ---, Others: ---
            
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

This project uses the AI-First SDLC framework for development. AI agents and developers should refer to [CLAUDE.md](CLAUDE.md) for development guidelines.

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
        
        with open(readme_path, 'w') as f:
            f.write(content)
        
        print("✅ Created README.md")
        return True
    
    def setup_project(self, skip_ci: bool = False, github_token: str = None, quickstart: bool = False) -> bool:
        """Run the complete setup process"""
        print("🚀 AI-First SDLC Smart Setup")
        print("=" * 50)
        print(f"Project: {self.project_name}")
        print(f"Purpose: {self.project_purpose}")
        print()
        
        # Quickstart mode - minimal setup
        if quickstart:
            print("\n⚡ Running in quickstart mode...")
            
            # Download only necessary templates for quickstart
            print("📥 Downloading templates...")
            quickstart_files = [
                "templates/gitignore/base.gitignore",
                "templates/gitignore/ai-tools.gitignore",
                "templates/gitignore/general.gitignore",
                "templates/tests/test-framework.sh",
                "tools/validation/validate-pipeline.py"
            ]
            
            # Always detect language first
            print("🔍 Detecting project language...")
            language = self.detect_project_language()
            print(f"✅ Detected language: {language}")
            
            # Add language-specific templates
            if language != 'general':
                quickstart_files.append(f"templates/gitignore/{language}.gitignore")
                # Add language-specific test template
                test_map = {
                    'python': 'templates/tests/test_framework_setup.py',
                    'node': 'templates/tests/framework.test.js',
                    'java': 'templates/tests/FrameworkTest.java',
                    'ruby': 'templates/tests/framework_test.rb',
                    'rust': 'templates/tests/framework_test.rs',
                    'go': 'templates/tests/test-framework.sh'
                }
                if language in test_map:
                    quickstart_files.append(test_map[language])
            
            # Download quickstart files
            for file in quickstart_files:
                self.download_file(file, None)
            
            # Create minimal directory structure
            print("📁 Creating minimal directory structure...")
            minimal_dirs = ["docs", "docs/architecture", "tools"]
            for dir_path in minimal_dirs:
                (self.project_dir / dir_path).mkdir(parents=True, exist_ok=True)
            
            # Create README if doesn't exist
            if not (self.project_dir / "README.md").exists():
                print("📄 Creating README.md...")
                self.create_readme()
            
            # Create .gitignore
            print("📝 Setting up .gitignore...")
            self.create_gitignore()
            
            # Create initial test
            print("🧪 Creating initial test...")
            self.create_initial_test()
            
            # Create VERSION file
            print("📌 Creating VERSION file...")
            version_file = self.project_dir / "VERSION"
            version_file.write_text("1.6.0")
            
            # Run validation
            print("🔍 Running validation...")
            self.run_validation()
            
            # Clean up temp directory
            temp_dir = self.project_dir / '.ai-sdlc-temp'
            if temp_dir.exists():
                import shutil
                shutil.rmtree(temp_dir)
            
            print("\n✅ Quickstart setup completed in < 10 seconds!")
            print("\n📚 Next steps:")
            print("  1. Review the generated files")
            print(f"  2. Run the full setup with: python setup-smart.py \"{self.project_purpose}\"")
            print("  3. Commit your changes: git add . && git commit -m 'Initial AI-First SDLC setup'")
            
            return True
        
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
            if local is not None:
                local_path = self.project_dir / local
            else:
                local_path = None  # Will be saved to temp directory
            
            if self.download_file(remote, local_path):
                if local is not None:
                    print(f"✅ Downloaded {local}")
            else:
                print(f"❌ Failed to download {remote}")
        
        # Create directory structure
        print("\n📁 Creating directory structure...")
        dirs = [
            "docs/feature-proposals", 
            "docs/architecture/decisions",  # New for Zero Technical Debt
            "plan", 
            "retrospectives", 
            ".claude",
            "templates/architecture"  # New for architecture templates
        ]
        for dir_path in dirs:
            (self.project_dir / dir_path).mkdir(parents=True, exist_ok=True)
            print(f"✅ Created {dir_path}/")
        
        # Detect project language
        print("\n🔍 Detecting project language...")
        language = self.detect_project_language()
        print(f"✅ Detected language: {language}")
        
        # Always use hierarchical system for new installations
        if (self.project_dir / "CLAUDE-CORE.md").exists():
            print("\n✅ Using hierarchical instruction system (CLAUDE-CORE.md)")
            # Create deprecation notice only
            deprecation_content = """# CLAUDE.md

⚠️ **DEPRECATED**: This file exists only for backward compatibility and will be removed in v2.0.0.

Please use the new hierarchical instruction system:
- Start with: CLAUDE-CORE.md
- For setup: CLAUDE-SETUP.md
- For other tasks: See context loading table in CLAUDE-CORE.md

To migrate existing customizations: python tools/migrate-to-hierarchical.py
"""
            with open(self.project_dir / "CLAUDE.md", 'w') as f:
                f.write(deprecation_content)
            print("✅ Created CLAUDE.md (deprecation notice only)")
        else:
            # Should not happen with new setup, but keep minimal fallback
            print("\n⚠️  WARNING: Hierarchical system not found. Please update framework.")
            fallback_content = """# CLAUDE.md

ERROR: The hierarchical instruction system was not properly installed.

Please re-run setup or manually download:
- CLAUDE-CORE.md
- CLAUDE-SETUP.md
- CLAUDE-CONTEXT-*.md files

From: https://github.com/SteveGJones/ai-first-sdlc-practices
"""
            with open(self.project_dir / "CLAUDE.md", 'w') as f:
                f.write(fallback_content)
            print("❌ ERROR: Created error notice in CLAUDE.md")
        
        # Create symlinks for other AI files
        for ai_file in ["GEMINI.md", "GPT.md"]:
            target = self.project_dir / ai_file
            if not target.exists():
                target.symlink_to("CLAUDE.md")
                print(f"✅ Created {ai_file} → CLAUDE.md")
        
        # Create comprehensive .gitignore
        print("\n📝 Setting up .gitignore...")
        self.create_gitignore()
        
        # Create initial test
        print("\n🧪 Creating initial test...")
        self.create_initial_test()
        
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
        
        # Create VERSION file
        print("\n📌 Creating VERSION file...")
        version_file = self.project_dir / "VERSION"
        version_file.write_text("1.6.0")
        print("✅ Created VERSION file (1.6.0)")
        
        # Install AI agents
        print("\n🤖 Installing AI agents...")
        self.install_agents()
        
        # Create Claude project configuration
        print("\n🔧 Creating Claude project configuration...")
        self.create_claude_config()
        
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
        
        # Clean up temp directory
        temp_dir = self.project_dir / '.ai-sdlc-temp'
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
            subprocess.run(
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
            
            if self.non_interactive:
                print("   ℹ️  Non-interactive mode: skipping gh auth login prompt")
                print("   💡 To authenticate: gh auth login")
                return False
                
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
            # Use proper URL parsing to avoid security issues
            if remote_url.startswith("git@github.com:"):
                # SSH: git@github.com:owner/repo.git
                match = re.search(r'^git@github\.com:(.+?)(?:\.git)?$', remote_url)
            elif remote_url.startswith("https://github.com/"):
                # HTTPS: https://github.com/owner/repo.git
                match = re.search(r'^https://github\.com/(.+?)(?:\.git)?$', remote_url)
            else:
                print("❌ Repository URL is not from github.com")
                return False
                
            if match:
                repo_path = match.group(1)
                
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
                "tools/automation/agent-help.py"
            ]
            
            for tool in agent_tools:
                local_path = self.project_dir / "tools" / Path(tool).name
                self.download_file(tool, local_path)
            
            # Create claude/agents directory
            claude_agents_dir = self.project_dir / "claude" / "agents"
            claude_agents_dir.mkdir(parents=True, exist_ok=True)
            
            # In non-interactive mode, do smart installation
            if self.non_interactive:
                print("   🔍 Analyzing project for smart agent recommendations...")
                
                # Build command for smart installation
                cmd = [
                    sys.executable, 
                    str(self.project_dir / "tools" / "agent-installer.py"),
                    "--project-root", str(self.project_dir)
                ]
                
                # If we have project purpose, pass it as objectives
                if self.project_purpose and self.project_purpose != "AI-assisted software development":
                    # Create a temp file with analysis including objectives
                    analysis_data = {
                        'languages': {self.detected_language: {'files': 10, 'percentage': 100}} if self.detected_language else {},
                        'primary_language': self.detected_language,
                        'project_types': [],
                        'frameworks': set(),
                        'objectives': self.project_purpose
                    }
                    
                    # Use the recommender directly
                    print(f"   📋 Project purpose: {self.project_purpose}")
                    
                # Just install core + detected language for now
                cmd.extend(["--core-only"])
                if self.detected_language and self.detected_language != 'general':
                    cmd.extend(["--languages", self.detected_language])
                
                print(f"   🚀 Installing essential agents...")
                
                # Try to run the installer
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode != 0:
                    # Fallback to downloading core agents directly
                    return self._install_core_agents_fallback()
                    
                print("   ✅ Installed smart agent selection")
                print("   💡 Run 'python tools/agent-installer.py' for more agents")
                print("   💡 Use 'python tools/agent-help.py <challenge>' to find agents")
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
            ("agents/core/sdlc-enforcer.md", "claude/agents/core/sdlc-enforcer.md"),
            ("agents/core/solution-architect.md", "claude/agents/core/solution-architect.md"),
            ("agents/core/critical-goal-reviewer.md", "claude/agents/core/critical-goal-reviewer.md"),
            ("agents/sdlc/framework-validator.md", "claude/agents/sdlc/framework-validator.md"),
            ("agents/core/github-integration-specialist.md", "claude/agents/core/github-integration-specialist.md")
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
                "github-integration-specialist": "1.0.0"
            }
            manifest_path = self.project_dir / ".agent-manifest.json"
            with open(manifest_path, 'w') as f:
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
                    text=True
                )
                if result.returncode == 0 and result.stdout.strip():
                    github_url = result.stdout.strip()
            except:
                pass
            
            # Create project configuration
            config = {
                "project_name": self.project_name,
                "project_purpose": self.purpose,
                "github_repository": github_url,
                "agent_preferences": {
                    "required_agents": [
                        "sdlc-enforcer",
                        "solution-architect",
                        "critical-goal-reviewer"
                    ],
                    "auto_suggest": True,
                    "context_aware_selection": True
                },
                "sdlc_settings": {
                    "enforce_feature_proposals": True,
                    "require_architecture_docs": True,
                    "zero_technical_debt": True,
                    "require_retrospectives": True
                },
                "detected_stack": {
                    "languages": [self.detected_language] if self.detected_language else [],
                    "frameworks": [],
                    "project_type": self.project_type
                }
            }
            
            config_path = claude_dir / "project-config.json"
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
            
            print("   ✅ Created Claude project configuration")
            if github_url:
                print(f"   📍 GitHub repository linked: {github_url}")
            return True
            
        except Exception as e:
            print(f"   ⚠️  Could not create Claude config: {e}")
            return False
    
    def print_next_steps(self):
        """Print next steps for the user"""
        print("\n📋 Next Steps:")
        print("=" * 50)
        print("\n🚨 NEW: Zero Technical Debt Policy Enforced!")
        print("   - Complete ALL 6 architecture documents before coding")
        print("   - Run: python tools/validation/validate-architecture.py")
        print("   - Zero tolerance for TODOs, any types, or commented code")
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
        print("\n4. Install recommended AI agents:")
        
        # Check if this is an MCP project
        is_mcp_project = "mcp" in self.project_purpose.lower() or "model context protocol" in self.project_purpose.lower()
        
        if is_mcp_project:
            print("   🎯 MCP Project Detected! Essential Agents:")
            print("     • sdlc-enforcer - Primary compliance guardian")
            print("     • critical-goal-reviewer - Quality assurance")
            print("     • solution-architect - System design expert")
            print("     • mcp-server-architect - MCP design specialist ⭐")
            print("     • mcp-test-agent - MCP testing from AI perspective ⭐")
            print("     • mcp-quality-assurance - MCP quality & security ⭐")
            print("   ")
            print("   📚 Additional recommended agents:")
        else:
            print("   🤖 Core Agents (CRITICAL - Install These First):")
            print("     • sdlc-enforcer - Primary compliance guardian")
            print("     • critical-goal-reviewer - Quality assurance")
            print("     • solution-architect - System design expert")
            print("   ")
            print("   📚 Based on your project type, also consider:")
        
        if "python" in self.project_purpose.lower() or "api" in self.project_purpose.lower():
            print("     • python-expert - Python best practices")
            print("     • ai-test-engineer - AI system testing")
        if "langchain" in self.project_purpose.lower() or "llm" in self.project_purpose.lower():
            print("     • langchain-architect - LangChain expertise")
            print("     • prompt-engineer - Prompt optimization")
        print("   ")
        print("   ⚠️  IMPORTANT: Installing agents requires a reboot of your AI assistant!")
        print("   ")
        print("   To install agents, use:")
        print("   python tools/agent-installer.py --install <agent-name>")
        print("   Example: python tools/agent-installer.py --install mcp-server-architect")
        print("   ")
        print("   To discover more agents for your needs:")
        print("   - Ask: 'What agents should I install for [your specific need]?'")
        print("   - The ai-first-kick-starter agent can recommend agents anytime")
        print("   - List all available agents: python tools/agent-installer.py --list")
        print("\n5. Customize CLAUDE.md with project-specific details:")
        print("   edit CLAUDE.md")
        print("\n6. Complete the setup tasks:")
        print("   python tools/progress-tracker.py list")
        print("\n7. When ready, push the branch:")
        print("   git add .")
        print("   git commit -m \"feat: implement AI-First SDLC framework with Zero Technical Debt\"")
        print("   git push -u origin ai-first-kick-start")
        print("\n8. Create retrospective (REQUIRED before PR):")
        print("   Create file: retrospectives/00-ai-first-setup.md")
        print("   Document what went well, what could improve, and lessons learned")
        print("\n9. Create a pull request to merge into main")
        print("   Note: PR will be rejected without retrospective AND architecture docs!")
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
    parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Run without prompts (use defaults)"
    )
    parser.add_argument(
        "--ci-platform",
        choices=["github", "gitlab", "jenkins", "azure", "circleci", "none"],
        help="CI/CD platform to configure (for non-interactive mode)"
    )
    parser.add_argument(
        "--quickstart",
        action="store_true",
        help="Quick start mode: creates README, .gitignore, and initial test"
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
    setup = SmartFrameworkSetup(args.project_dir, args.purpose, 
                                args.non_interactive, args.ci_platform, args.quickstart)
    
    # Update version if specified
    if args.version != "main":
        setup.GITHUB_RAW_BASE = setup.GITHUB_RAW_BASE.replace("/main", f"/{args.version}")
    
    # Run setup
    success = setup.setup_project(args.skip_ci, args.github_token, args.quickstart)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()