#!/usr/bin/env python3
"""
AI-First SDLC Framework Setup Tool
One-command setup for AI-First SDLC compliance
"""

import os
import sys
import shutil
import subprocess
import argparse
from pathlib import Path
from typing import Optional, List, Tuple
import json


class AIFirstSDLCSetup:
    """Setup tool for AI-First SDLC Framework"""

    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path.cwd()
        self.framework_root = Path(__file__).parent.parent
        self.templates_dir = self.framework_root / "templates"
        self.tools_dir = self.framework_root / "tools"

    def setup_project(
            self,
            components: List[str] = None,
            force: bool = False) -> bool:
        """Setup AI-First SDLC in project"""

        print("🚀 AI-First SDLC Framework Setup")
        print("=" * 50)

        # Default to all components
        if not components:
            components = ["ai-docs", "templates", "hooks", "tools"]

        success = True
        if "ai-docs" in components:
            success &= self.setup_ai_documentation(force)

        if "templates" in components:
            success &= self.setup_templates(force)

        if "hooks" in components:
            success &= self.setup_pre_commit_hooks(force)

        if "tools" in components:
            success &= self.setup_tools(force)

        if success:
            print("\n✅ Setup completed successfully!")
            self.print_next_steps()
        else:
            print("\n⚠️  Setup completed with some issues")
            print("Run with --force to overwrite existing files")

        return success

    def setup_ai_documentation(self, force: bool = False) -> bool:
        """Setup AI instruction files"""
        print("\n📝 Setting up AI documentation...")

        ai_files = ["CLAUDE.md", "GEMINI.md", "GPT.md"]
        existing = []

        # Check for existing files
        for ai_file in ai_files:
            if (self.project_root / ai_file).exists():
                existing.append(ai_file)

        if existing and not force:
            print(f"   ℹ️  Found existing: {', '.join(existing)}")
            print("   Use --force to overwrite")
            return True

        # Copy CLAUDE.md template
        claude_template = self.templates_dir / "CLAUDE.md"
        claude_target = self.project_root / "CLAUDE.md"

        try:
            # Read template
            with open(claude_template, "r") as f:
                content = f.read()

            # Replace placeholders
            project_name = self.project_root.name
            content = content.replace("[Your Project Name]", project_name)
            content = content.replace(
                "[Brief description]",
                f"AI-First development of {project_name}")

            # Write to project
            with open(claude_target, "w") as f:
                f.write(content)

            print("   ✅ Created CLAUDE.md")

            # Create symlinks for other AI files
            for ai_file in ["GEMINI.md", "GPT.md"]:
                target = self.project_root / ai_file
                if not target.exists() or force:
                    target.symlink_to("CLAUDE.md")
                    print(f"   ✅ Created {ai_file} → CLAUDE.md")

            return True

        except Exception as e:
            print(f"   ❌ Error creating AI documentation: {e}")
            return False

    def setup_templates(self, force: bool = False) -> bool:
        """Setup project templates"""
        print("\n📋 Setting up templates...")

        # Create directories
        dirs_to_create = ["docs/feature-proposals", "plan", "retrospectives"]

        for dir_path in dirs_to_create:
            target_dir = self.project_root / dir_path
            target_dir.mkdir(parents=True, exist_ok=True)
            print(f"   ✅ Created {dir_path}/")

        # Copy templates
        templates_to_copy = [
            (
                "feature-proposal.md",
                "docs/feature-proposals/template-feature-proposal.md",
            ),
            ("implementation-plan.md", "plan/template-implementation-plan.md"),
            ("retrospective.md", "retrospectives/template-retrospective.md"),
        ]

        for template_file, target_path in templates_to_copy:
            source = self.templates_dir / template_file
            target = self.project_root / target_path

            if target.exists() and not force:
                print(f"   ⏭️  Skipped {target_path} (exists)")
                continue

            try:
                shutil.copy2(source, target)
                print(f"   ✅ Created {target_path}")
            except Exception as e:
                print(f"   ❌ Error copying {template_file}: {e}")
                return False

        return True

    def setup_pre_commit_hooks(self, force: bool = False) -> bool:
        """Setup pre-commit hooks"""
        print("\n🔧 Setting up pre-commit hooks...")

        # Check if pre-commit is installed
        try:
            subprocess.run(["pre-commit", "--version"],
                           capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("   ⚠️  pre-commit not installed")
            print("   Install with: pip install pre-commit")
            return False

        # Copy pre-commit config
        source = self.templates_dir / ".pre-commit-config.yaml"
        target = self.project_root / ".pre-commit-config.yaml"

        if target.exists() and not force:
            print("   ⏭️  .pre-commit-config.yaml already exists")
        else:
            try:
                shutil.copy2(source, target)
                print("   ✅ Created .pre-commit-config.yaml")
            except Exception as e:
                print(f"   ❌ Error copying pre-commit config: {e}")
                return False

        # Install pre-commit hooks
        try:
            subprocess.run(["pre-commit", "install"],
                           cwd=self.project_root, check=True)
            print("   ✅ Installed pre-commit hooks")
        except subprocess.CalledProcessError as e:
            print(f"   ❌ Error installing hooks: {e}")
            return False

        return True

    def setup_tools(self, force: bool = False) -> bool:
        """Setup AI-First SDLC tools"""
        print("\n🛠️  Setting up tools...")

        # Create tools directory
        tools_target = self.project_root / "tools"
        tools_target.mkdir(exist_ok=True)

        # Copy essential tools
        tools_to_copy = [
            ("automation/context-manager.py", "context-manager.py"),
            ("automation/progress-tracker.py", "progress-tracker.py"),
            ("validation/check-feature-proposal.py", "check-feature-proposal.py"),
            ("validation/validate-pipeline.py", "validate-pipeline.py"),
        ]

        for source_path, target_name in tools_to_copy:
            source = self.tools_dir / source_path
            target = tools_target / target_name

            if target.exists() and not force:
                print(f"   ⏭️  Skipped {target_name} (exists)")
                continue

            try:
                shutil.copy2(source, target)
                # Make executable (owner only)
                os.chmod(target, 0o700)  # Owner read/write/execute only
                print(f"   ✅ Installed {target_name}")
            except Exception as e:
                print(f"   ❌ Error copying {target_name}: {e}")
                return False

        return True

    def verify_git_setup(self) -> Tuple[bool, str]:
        """Verify git is properly configured"""
        try:
            # Check if git repo
            subprocess.run(["git", "status"], capture_output=True, check=True)

            # Get current branch
            result = subprocess.run(
                ["git", "symbolic-ref", "--short", "HEAD"],
                capture_output=True,
                text=True,
                check=True,
            )
            branch = result.stdout.strip()
            return True, branch

        except subprocess.CalledProcessError:
            return False, ""

    def initialize_git(self) -> bool:
        """Initialize git repository"""
        try:
            subprocess.run(["git", "init"], check=True)
            print("   ✅ Initialized git repository")

            # Create initial commit
            subprocess.run(["git", "add", "."], check=True)
            subprocess.run(
                ["git", "commit", "-m", "feat: initialize AI-First SDLC framework"],
                check=True,
            )
            print("   ✅ Created initial commit")

            return True

        except subprocess.CalledProcessError as e:
            print(f"   ❌ Error initializing git: {e}")
            return False

    def print_next_steps(self):
        """Print next steps for user"""
        print("\n📚 Next Steps:")
        print("=" * 50)

        print("\n1. Create a feature branch:")
        print("   git checkout -b feature/your-feature-name")

        print("\n2. Create a feature proposal:")
        print("   cp docs/feature-proposals/template-feature-proposal.md \\")
        print("      docs/feature-proposals/01-your-feature.md")

        print("\n3. Run validation:")
        print("   python tools/validate-pipeline.py")

        print("\n4. Track your progress:")
        print('   python tools/progress-tracker.py add "Implement feature X"')

        print("\n5. Save context between sessions:")
        print('   python tools/context-manager.py handoff --current "Working on X"')

        print("\n📖 Full documentation:")
        print("   https://github.com/your-org/ai-first-sdlc-framework")

    def create_config_file(self):
        """Create AI-First SDLC config file"""
        config = {
            "version": "1.0",
            "framework": "ai-first-sdlc",
            "settings": {
                "enforce_branch_protection": True,
                "require_feature_proposals": True,
                "require_implementation_plans": True,
                "ai_agents": ["claude", "gemini", "gpt"],
                "validation_on_commit": True,
            },
            "tools": {
                "context_preservation": True,
                "progress_tracking": True,
                "automated_validation": True,
            },
        }

        config_file = self.project_root / ".ai-sdlc.json"
        with open(config_file, "w") as f:
            json.dump(config, f, indent=2)

        print("   ✅ Created .ai-sdlc.json configuration")


def main():
    parser = argparse.ArgumentParser(
        description="Setup AI-First SDLC Framework in your project"
    )
    parser.add_argument(
        "--components",
        nargs="+",
        choices=["ai-docs", "templates", "hooks", "tools"],
        help="Components to setup (default: all)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing files")
    parser.add_argument(
        "--init-git",
        action="store_true",
        help="Initialize git repository if needed")
    parser.add_argument(
        "--skip-config",
        action="store_true",
        help="Skip creating .ai-sdlc.json config")
    parser.add_argument(
        "--project-dir",
        type=Path,
        help="Project directory (default: current directory)",
    )

    args = parser.parse_args()

    # Create setup instance
    setup = AIFirstSDLCSetup(args.project_dir)

    print("🤖 Welcome to AI-First SDLC Framework Setup")
    print("=" * 50)

    # Check git setup
    has_git, branch = setup.verify_git_setup()

    if not has_git:
        if args.init_git:
            print("\n📂 Initializing git repository...")
            if not setup.initialize_git():
                sys.exit(1)
        else:
            print("\n⚠️  No git repository found")
            print("Run with --init-git to initialize")
            response = input("\nContinue anyway? [y/N]: ")
            if response.lower() != "y":
                sys.exit(0)
    else:
        print(f"\n✅ Git repository found (branch: {branch})")
        if branch in ["main", "master"]:
            print("⚠️  Warning: On main branch - create feature branch recommended")

    # Run setup
    success = setup.setup_project(args.components, args.force)
    # Create config file
    if success and not args.skip_config:
        setup.create_config_file()

    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
