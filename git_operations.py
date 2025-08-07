#!/usr/bin/env python3
"""
Git operations for version management feature
"""

import subprocess
import os

# sys import removed - not used
from typing import Tuple

# Version number for current branch and files (zero-padded)
VERSION_NUMBER = "07"  # This is a version string, not a magic number


def run_git_command(cmd: str, cwd: str) -> Tuple[str, str, int]:
    """Run a git command and return output"""
    try:
        result = subprocess.run(
            cmd, shell=True, cwd=cwd, capture_output=True, text=True
        )
        return result.stdout, result.stderr, result.returncode
    except Exception as e:
        return "", str(e), 1


def main() -> None:
    # Change to project directory
    project_dir = "/Users/stevejones/Documents/Development/ai-first-sdlc-practices"
    os.chdir(project_dir)

    print(f"Working in: {os.getcwd()}")

    # Check git status
    print("\n=== Git Status ===")
    stdout, stderr, rc = run_git_command("git status", project_dir)
    print(stdout)
    if stderr:
        print(f"Error: {stderr}")

    # Add files
    print("\n=== Adding files ===")
    files_to_add = [
        "VERSION",
        "CHANGELOG.md",
        "docs/updates/UPDATE-PROMPT.md",
        "docs/releases/v1.3.0-to-v1.4.0.md",
        "docs/releases/v1.4.0-to-v1.5.0.md",
        "templates/migration-guide.md",
        f"retrospectives/{VERSION_NUMBER}-version-management-updates.md",
        f"docs/feature-proposals/{VERSION_NUMBER}-version-management-updates.md",
        f"plan/{VERSION_NUMBER}-version-management-plan.md",
        "setup-smart.py",
        "CLAUDE.md",
        "README.md",
        "templates/CLAUDE.md",
        "QUICKSTART.md",
        "docs/updates/whats-new.md",
    ]

    for file in files_to_add:
        stdout, stderr, rc = run_git_command(f"git add {file}", project_dir)
        if rc == 0:
            print(f"Added: {file}")
        else:
            print(f"Failed to add {file}: {stderr}")

    # Show what's staged
    print("\n=== Staged files ===")
    stdout, stderr, rc = run_git_command("git status --short", project_dir)
    print(stdout)

    # Create commit
    print("\n=== Creating commit ===")
    commit_message = """feat: implement version management system

- Add VERSION file and CHANGELOG.md
- Create UPDATE-PROMPT.md for guided updates
- Add migration guide template and examples
- Update setup-smart.py to track versions
- Update CLAUDE.md with version management
- Add comprehensive documentation

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"""

    # Write commit message to temp file to avoid shell escaping issues
    with open("/tmp/commit_msg.txt", "w") as f:
        f.write(commit_message)

    stdout, stderr, rc = run_git_command(
        "git commit -F /tmp/commit_msg.txt", project_dir
    )
    print(stdout)
    if stderr:
        print(f"Error: {stderr}")

    # Push branch
    print("\n=== Pushing branch ===")
    stdout, stderr, rc = run_git_command(
        "git push -u origin feature/version-management-updates", project_dir
    )
    print(stdout)
    if stderr:
        print(f"Error: {stderr}")

    print("\n=== Done! ===")


if __name__ == "__main__":
    main()
