#!/usr/bin/env python3
"""
GitHub Actions Permissions Checker
==================================

Validates that GitHub Actions workflows have appropriate permissions
for their operations, specifically checking for PR comment permissions.

This prevents the "Resource not accessible by integration" error.
"""

import sys
import yaml
from pathlib import Path
from typing import Dict, List, Optional


def load_workflow(workflow_path: Path) -> Optional[Dict]:
    """Load and parse a GitHub Actions workflow file."""
    try:
        with open(workflow_path, "r") as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"❌ Error loading {workflow_path}: {e}")
        return None


def check_pr_comment_permissions(
        workflow: Dict,
        workflow_name: str) -> List[str]:
    """Check if workflow has proper permissions for PR commenting."""
    issues = []

    # Check if workflow uses github-script for PR operations
    uses_pr_comments = False

    for job_name, job in workflow.get("jobs", {}).items():
        for step in job.get("steps", []):
            if step.get("uses", "").startswith("actions/github-script"):
                # Check if the script references PR/issue operations
                script = step.get("with", {}).get("script", "")
                if any(
                    term in script
                    for term in [
                        "issues.createComment",
                        "issues.updateComment",
                        "pull_request",
                    ]
                ):
                    uses_pr_comments = True

    # If workflow uses PR comments, check permissions
    if uses_pr_comments:
        permissions = workflow.get("permissions", {})

        if not permissions:
            issues.append(
                f"❌ {workflow_name}: Uses PR comments but has no permissions block"
            )
        else:
            required_perms = {"issues": "write", "pull-requests": "write"}

            for perm, level in required_perms.items():
                if permissions.get(perm) != level:
                    issues.append(
                        f"❌ {workflow_name}: Missing '{perm}: {level}' permission for PR comments"
                    )

    return issues


def check_workflow_security(workflow: Dict, workflow_name: str) -> List[str]:
    """Check workflow for security best practices."""
    issues = []

    permissions = workflow.get("permissions", {})

    # Check for overly broad permissions
    dangerous_perms = {
        "contents": "write",  # Generally should be 'read' unless pushing
        "packages": "write",  # Only for release workflows
        "actions": "write",  # Rarely needed
    }

    for perm, level in dangerous_perms.items():
        if permissions.get(perm) == level:
            # Only warn if it's not an obvious release workflow
            if "release" not in workflow_name.lower() and perm != "contents":
                issues.append(
                    f"⚠️  {workflow_name}: Consider if '{perm}: {level}' permission is necessary"
                )

    return issues


def main():
    """Main validation function."""
    print("🔍 GitHub Actions Permissions Checker")
    print("=====================================")

    workflows_dir = Path(".github/workflows")
    if not workflows_dir.exists():
        print("❌ No .github/workflows directory found")
        return 1

    all_issues = []
    checked_workflows = 0

    for workflow_file in workflows_dir.glob("*.yml"):
        workflow = load_workflow(workflow_file)
        if not workflow:
            continue

        workflow_name = workflow_file.stem
        checked_workflows += 1

        print(f"\n📋 Checking {workflow_name}...")

        # Check PR comment permissions
        pr_issues = check_pr_comment_permissions(workflow, workflow_name)
        all_issues.extend(pr_issues)

        # Check security practices
        security_issues = check_workflow_security(workflow, workflow_name)
        all_issues.extend(security_issues)

        if not pr_issues and not security_issues:
            print(f"✅ {workflow_name}: Permissions look good")

    print(f"\n📊 Summary: Checked {checked_workflows} workflows")

    if all_issues:
        print(f"\n🚨 Found {len(all_issues)} permission issues:")
        for issue in all_issues:
            print(f"  {issue}")

        print("\n💡 Fix: Add explicit permissions block to workflows:")
        print(
            """
permissions:
  contents: read        # Required to checkout code
  issues: write         # Required to comment on PRs
  pull-requests: write  # Required for PR operations
  actions: read         # Required to read workflow status
  checks: write         # Required to write check results
"""
        )
        return 1
    else:
        print("✅ All workflows have appropriate permissions!")
        return 0


if __name__ == "__main__":
    sys.exit(main())
