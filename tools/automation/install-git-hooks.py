#!/usr/bin/env python3
"""
Install Git Hooks for AI-First SDLC

This script installs Git hooks that enforce validation before commits and pushes.
Critical for preventing the push-fail-fix cycle.

Usage:
    python tools/automation/install-git-hooks.py
"""

import os
import stat
from pathlib import Path
import shutil


def create_pre_push_hook() -> str:
    """Create pre-push hook content"""
    return """#!/bin/bash
# Pre-push hook for AI-First SDLC
# Prevents pushing broken code to remote repository

echo "🔍 Running pre-push validation..."

# Run local validation script
python tools/validation/local-validation.py --pre-push

validation_result=$?

if [ $validation_result -ne 0 ]; then
    echo ""
    echo "❌ PRE-PUSH VALIDATION FAILED!"
    echo "🛑 Push blocked to prevent CI/CD failures."
    echo ""
    echo "💡 To fix issues quickly:"
    echo "   python tools/validation/local-validation.py --syntax"
    echo ""
    echo "💡 To run full validation:"
    echo "   python tools/validation/local-validation.py"
    echo ""
    echo "⚠️  To bypass (NOT RECOMMENDED):"
    echo "   git push --no-verify"
    echo ""
    exit $validation_result
fi

echo "✅ Pre-push validation passed! Pushing to remote..."
"""


def create_commit_msg_hook() -> str:
    """Create commit-msg hook for enforcing commit standards"""
    return """#!/bin/bash
# Commit message hook for AI-First SDLC
# Enforces commit message standards

commit_regex='^(feat|fix|docs|style|refactor|test|chore)(\\(.+\\))?: .{1,50}'

error_msg="❌ Invalid commit message format!

Expected format: type(scope): description

Types:
  feat:     New feature
  fix:      Bug fix
  docs:     Documentation changes
  style:    Code style changes (formatting, etc.)
  refactor: Code refactoring
  test:     Adding/updating tests
  chore:    Maintenance tasks

Examples:
  feat: add user authentication system
  fix: resolve syntax error in migration script
  docs: update API documentation
  fix(validation): prevent false positive TODO detection

Keep the description under 50 characters.
"

if ! grep -qE "$commit_regex" "$1"; then
    echo "$error_msg" >&2
    exit 1
fi
"""


def create_pre_commit_hook() -> str:
    """Create pre-commit hook for immediate syntax validation"""
    return """#!/bin/bash
# Pre-commit hook for AI-First SDLC
# Fast syntax validation before commit

echo "🚀 Running pre-commit syntax validation..."

# Run syntax check only (fast)
python tools/validation/local-validation.py --syntax

syntax_result=$?

if [ $syntax_result -ne 0 ]; then
    echo ""
    echo "❌ SYNTAX VALIDATION FAILED!"
    echo "🛑 Commit blocked due to syntax errors."
    echo ""
    echo "💡 Fix syntax errors and try again."
    echo "⚠️  To bypass (NOT RECOMMENDED): git commit --no-verify"
    echo ""
    exit $syntax_result
fi

echo "✅ Syntax validation passed!"
"""


def install_hooks():
    """Install Git hooks"""

    # Find git directory
    git_dir = Path(".git")
    if not git_dir.exists():
        print("❌ Not in a Git repository!")
        return False

    hooks_dir = git_dir / "hooks"
    hooks_dir.mkdir(exist_ok=True)

    hooks_to_install = [
        ("pre-push", create_pre_push_hook()),
        ("commit-msg", create_commit_msg_hook()),
        ("pre-commit", create_pre_commit_hook()),
    ]

    print("🪝 Installing Git hooks for AI-First SDLC...")

    installed_hooks = []
    for hook_name, hook_content in hooks_to_install:
        hook_path = hooks_dir / hook_name

        # Backup existing hook
        if hook_path.exists():
            backup_path = hooks_dir / f"{hook_name}.backup"
            shutil.copy2(hook_path, backup_path)
            print(f"💾 Backed up existing {hook_name} hook to {backup_path}")

        # Write new hook
        with open(hook_path, "w") as f:
            f.write(hook_content)

        # Make executable
        hook_path.chmod(hook_path.stat().st_mode | stat.S_IEXEC)

        print(f"✅ Installed {hook_name} hook")
        installed_hooks.append(hook_name)

    print(f"\\n🎉 Successfully installed {len(installed_hooks)} Git hooks:")
    for hook in installed_hooks:
        print(f"   • {hook}")

    print(
        """
🛡️ Protection Active:
   • pre-commit: Fast syntax validation
   • commit-msg: Commit message standards
   • pre-push: Full validation before push

💡 Benefits:
   • Prevents syntax errors reaching repository
   • Blocks broken code from CI/CD pipeline
   • Enforces consistent commit messages
   • Reduces push-fail-fix cycles

⚠️ To bypass hooks (NOT RECOMMENDED):
   git commit --no-verify
   git push --no-verify
"""
    )

    return True


def main():
    """Main function"""
    try:
        # Change to repository root
        repo_root = Path(__file__).parent.parent.parent
        os.chdir(repo_root)

        success = install_hooks()

        if success:
            print("\\n🚀 Git hooks installed successfully!")
            print("   Run 'git commit' or 'git push' to test the hooks.")
        else:
            print("\\n❌ Failed to install Git hooks.")

    except Exception as e:
        print(f"❌ Error installing Git hooks: {str(e)}")
        return False


if __name__ == "__main__":
    main()
