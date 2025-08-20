#!/usr/bin/env python3
"""
SDLC Git Hooks Setup

Installs git hooks for AI-First SDLC compliance, ensuring validation
runs automatically before commits and pushes.
"""

import os
import sys
import stat
import click
from pathlib import Path
from typing import List, Tuple


class GitHooksInstaller:
    """Manages installation of SDLC-compliant git hooks"""

    def __init__(self, project_dir: Path = None):
        """
        Initialize the installer

        Args:
            project_dir: Project directory (defaults to current directory)
        """
        self.project_dir = project_dir or Path.cwd()
        self.git_dir = self.project_dir / '.git'
        self.hooks_dir = self.git_dir / 'hooks'

    def is_git_repo(self) -> bool:
        """Check if the current directory is a git repository"""
        return self.git_dir.exists() and self.git_dir.is_dir()

    def create_pre_commit_hook(self) -> str:
        """Generate pre-commit hook content"""
        return '''#!/bin/bash
# AI-First SDLC Pre-commit Hook
# Runs syntax validation before allowing commits

echo "🔍 AI-First SDLC: Running pre-commit validation..."

# Check if validation tool exists in .sdlc directory
if [ -f ".sdlc/tools/validation/local-validation.py" ]; then
    python .sdlc/tools/validation/local-validation.py --syntax
    if [ $? -ne 0 ]; then
        echo "❌ Syntax validation failed!"
        echo "Fix the errors above before committing."
        exit 1
    fi
    echo "✅ Syntax validation passed"
else
    # If no validation tool, check basic Python syntax
    if command -v python3 &> /dev/null; then
        find . -name "*.py" -type f -not -path "./.sdlc/*" -exec python3 -m py_compile {} + 2>&1
        if [ $? -ne 0 ]; then
            echo "❌ Python syntax errors found!"
            exit 1
        fi
    fi
fi

# Check for forbidden patterns
echo "🔍 Checking for technical debt markers..."

# Check for TODOs, FIXMEs, HACKs in code files
TODO_COUNT=$(grep -r "TODO\\|FIXME\\|HACK" --include="*.py" --include="*.js" --include="*.ts" . 2>/dev/null | wc -l)
if [ $TODO_COUNT -gt 0 ]; then
    echo "⚠️  Warning: Found $TODO_COUNT TODO/FIXME/HACK comments"
    echo "Consider addressing technical debt before committing"
    # This is a warning, not a blocker for now
fi

echo "✅ Pre-commit checks complete"
exit 0
'''

    def create_pre_push_hook(self) -> str:
        """Generate pre-push hook content"""
        return '''#!/bin/bash
# AI-First SDLC Pre-push Hook
# Runs comprehensive validation before allowing pushes

echo "🚀 AI-First SDLC: Running pre-push validation..."

# Get the branch being pushed
current_branch=$(git symbolic-ref HEAD 2>/dev/null | cut -d"/" -f 3)

# Check if pushing to main/master
if [ "$current_branch" = "main" ] || [ "$current_branch" = "master" ]; then
    echo "⛔ Direct push to $current_branch branch is not allowed!"
    echo "Please create a feature branch and submit a pull request."
    exit 1
fi

# Run quick validation if tool exists in .sdlc directory
if [ -f ".sdlc/tools/validation/local-validation.py" ]; then
    echo "Running quick validation suite..."
    python .sdlc/tools/validation/local-validation.py --quick
    if [ $? -ne 0 ]; then
        echo "❌ Validation failed!"
        echo "Run 'python .sdlc/tools/validation/local-validation.py --pre-push' for full validation"
        exit 1
    fi
    echo "✅ Quick validation passed"
fi

# Check for feature proposal
if [[ "$current_branch" == feature/* ]]; then
    proposal_name=${current_branch#feature/}
    if ! ls docs/feature-proposals/*${proposal_name}* 2>/dev/null | grep -q .; then
        echo "⚠️  Warning: No feature proposal found for branch $current_branch"
        echo "Consider creating a proposal in docs/feature-proposals/"
    fi
fi

# Check for retrospective (warning only)
if ! ls retrospectives/*${proposal_name}* 2>/dev/null | grep -q .; then
    echo "⚠️  Reminder: Create a retrospective before submitting PR"
fi

echo "✅ Pre-push validation complete"
echo "📝 Remember to create a retrospective before opening a Pull Request!"
exit 0
'''

    def create_commit_msg_hook(self) -> str:
        """Generate commit-msg hook content"""
        return '''#!/bin/bash
# AI-First SDLC Commit Message Hook
# Enforces conventional commit format

commit_regex='^(feat|fix|docs|style|refactor|test|chore|perf|ci|build|revert)(\(.+\))?: .{1,100}$'
commit_msg=$(cat $1)

if ! echo "$commit_msg" | grep -qE "$commit_regex"; then
    echo "❌ Invalid commit message format!"
    echo ""
    echo "Commit message must follow conventional format:"
    echo "  <type>(<scope>): <subject>"
    echo ""
    echo "Types: feat, fix, docs, style, refactor, test, chore, perf, ci, build, revert"
    echo "Example: feat(auth): add user login functionality"
    echo ""
    echo "Your message: $commit_msg"
    exit 1
fi

echo "✅ Commit message format is valid"
exit 0
'''

    def install_hook(self, hook_name: str, content: str) -> bool:
        """
        Install a git hook

        Args:
            hook_name: Name of the hook (e.g., 'pre-commit')
            content: Hook script content

        Returns:
            True if successful
        """
        if not self.is_git_repo():
            return False

        hook_path = self.hooks_dir / hook_name

        # Back up existing hook if present
        if hook_path.exists():
            backup_path = hook_path.with_suffix('.backup')
            hook_path.rename(backup_path)
            print(f"  Backed up existing {hook_name} to {hook_name}.backup")

        # Write new hook
        hook_path.write_text(content)

        # Make executable
        st = os.stat(hook_path)
        os.chmod(hook_path, st.st_mode | stat.S_IEXEC)

        return True

    def install_all_hooks(self) -> List[Tuple[str, bool]]:
        """
        Install all SDLC git hooks

        Returns:
            List of (hook_name, success) tuples
        """
        hooks = [
            ('pre-commit', self.create_pre_commit_hook()),
            ('pre-push', self.create_pre_push_hook()),
            ('commit-msg', self.create_commit_msg_hook()),
        ]

        results = []
        for hook_name, content in hooks:
            success = self.install_hook(hook_name, content)
            results.append((hook_name, success))

        return results

    def verify_hooks(self) -> List[Tuple[str, bool]]:
        """
        Verify that hooks are installed and executable

        Returns:
            List of (hook_name, is_valid) tuples
        """
        hooks_to_check = ['pre-commit', 'pre-push', 'commit-msg']
        results = []

        for hook_name in hooks_to_check:
            hook_path = self.hooks_dir / hook_name
            is_valid = hook_path.exists() and os.access(hook_path, os.X_OK)
            results.append((hook_name, is_valid))

        return results


@click.command()
@click.option('--verify', is_flag=True, help='Verify hooks are installed')
@click.option('--force', is_flag=True, help='Overwrite existing hooks without backup')
def main(verify: bool, force: bool):
    """
    Install AI-First SDLC git hooks for automated validation

    This tool installs git hooks that enforce SDLC compliance:
    - pre-commit: Syntax validation and technical debt checking
    - pre-push: Comprehensive validation and branch protection
    - commit-msg: Conventional commit format enforcement

    Examples:
        python setup-sdlc-git-hooks.py
        python setup-sdlc-git-hooks.py --verify
        python setup-sdlc-git-hooks.py --force
    """
    installer = GitHooksInstaller()

    # Check if we're in a git repository
    if not installer.is_git_repo():
        print("❌ Not a git repository!")
        print("Initialize with 'git init' first")
        sys.exit(1)

    if verify:
        # Verify mode
        print("🔍 Verifying git hooks...")
        results = installer.verify_hooks()

        all_valid = True
        for hook_name, is_valid in results:
            status = "✅ Installed" if is_valid else "❌ Missing"
            print(f"  {hook_name}: {status}")
            if not is_valid:
                all_valid = False

        if all_valid:
            print("\n✅ All hooks are properly installed!")
        else:
            print("\n⚠️  Some hooks are missing. Run without --verify to install.")

        sys.exit(0 if all_valid else 1)

    # Installation mode
    print("🔧 Installing AI-First SDLC git hooks...")
    print(f"📁 Git directory: {installer.git_dir}")

    results = installer.install_all_hooks()

    success_count = 0
    for hook_name, success in results:
        if success:
            print(f"  ✅ Installed {hook_name}")
            success_count += 1
        else:
            print(f"  ❌ Failed to install {hook_name}")

    if success_count == len(results):
        print(f"\n✅ Successfully installed {success_count} git hooks!")
        print("\nHooks will run automatically:")
        print("  • pre-commit: Syntax validation")
        print("  • pre-push: Comprehensive validation")
        print("  • commit-msg: Commit format check")
        print("\nTo test: make a commit or run 'git hooks run pre-commit'")
    else:
        print(f"\n⚠️  Installed {success_count}/{len(results)} hooks")
        print("Some hooks failed to install. Check permissions and try again.")
        sys.exit(1)


if __name__ == '__main__':
    main()