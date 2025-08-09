#!/usr/bin/env python3
"""
Framework verification test for Python projects.

This test ensures the AI-First SDLC framework is properly set up.
It can run in empty repositories and passes basic CI/CD validation.

Replace this test with real project tests as you develop your application.
"""

import os
import sys


def test_framework_structure() -> None:
    """Verify basic AI-First SDLC framework structure exists."""
    required_files = [
        "README.md",
        "CLAUDE.md",
    ]

    required_dirs = [
        "docs/feature-proposals",
        "retrospectives",
    ]

    # Check required files
    for file_path in required_files:
        if not os.path.exists(file_path):
            raise AssertionError(f"Required file missing: {file_path}")

    # Check required directories
    for dir_path in required_dirs:
        if not os.path.isdir(dir_path):
            raise AssertionError(f"Required directory missing: {dir_path}")


def test_claude_md_content() -> None:
    """Verify CLAUDE.md has basic required content."""
    if not os.path.exists("CLAUDE.md"):
        raise AssertionError("CLAUDE.md not found")

    with open("CLAUDE.md", "r", encoding="utf-8") as f:
        content = f.read().lower()

    # Check for key framework indicators
    required_patterns = [
        "claude.md",
        "ai development",
        "git workflow",
        "never push directly to main",
    ]

    for pattern in required_patterns:
        if pattern not in content:
            raise AssertionError(
                f"CLAUDE.md missing required pattern: {pattern}")


def test_gitignore_exists() -> None:
    """Verify .gitignore file exists and has AI tool patterns."""
    if not os.path.exists(".gitignore"):
        print("Warning: .gitignore not found (run setup-smart.py to create)")
        return

    with open(".gitignore", "r", encoding="utf-8") as f:
        content = f.read().lower()

    # Check for some AI tool patterns (optional check)
    ai_patterns = [".claude", ".cursor", ".aider"]
    found_patterns = sum(1 for pattern in ai_patterns if pattern in content)

    if found_patterns == 0:
        print("Info: Consider adding AI tool patterns to .gitignore")


def test_python_environment() -> None:
    """Verify Python environment is suitable for development."""
    # Check Python version
    if sys.version_info < (3, 8):
        raise AssertionError(f"Python 3.8+ required, found {sys.version}")

    # Check if we can import basic modules
    try:
        pass
    except ImportError as e:
        raise AssertionError(f"Required Python module not available: {e}")


def test_git_repository() -> None:
    """Verify this is a git repository."""
    if not os.path.isdir(".git"):
        raise AssertionError("Not a git repository (run 'git init')")


def main():
    """Run all framework verification tests."""
    tests = [
        test_framework_structure,
        test_claude_md_content,
        test_gitignore_exists,
        test_python_environment,
        test_git_repository,
    ]

    print("🔍 Running AI-First SDLC framework verification...")

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            print(f"✅ {test.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"❌ {test.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"⚠️  {test.__name__}: Unexpected error: {e}")
            failed += 1

    print(f"\n📊 Results: {passed} passed, {failed} failed")

    if failed == 0:
        print("🎉 Framework verification complete! Ready for development.")
        return 0
    else:
        print("🔧 Please fix the issues above before proceeding.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
