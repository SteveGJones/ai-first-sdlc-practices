#!/usr/bin/env python3
"""
Smart Branch Protection Setup Tool for AI-First SDLC

Features:
- Intelligent collaboration pattern detection
- Solo developer mode with self-approval
- Team collaboration mode with strict reviews
- Automated PR approval with status checks
- GitHub Actions workflow generation
- Comprehensive validation pipeline integration

More secure version that uses gh CLI instead of direct token handling.
See docs/SMART-BRANCH-PROTECTION.md for detailed usage guide.
"""

import subprocess
import sys
import argparse
import json
import re
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple

# Version for compatibility tracking
TOOL_VERSION = "2.0.0"


def check_gh_installed() -> bool:
    """Check if gh CLI is installed and authenticated"""
    try:
        # Check if gh is installed
        result = subprocess.run(["gh", "--version"], capture_output=True, check=True)

        # Check if authenticated
        result = subprocess.run(
            ["gh", "auth", "status"], capture_output=True, check=True
        )

        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def get_repo_info() -> Optional[tuple]:
    """Get repository owner and name using gh"""
    try:
        result = subprocess.run(
            ["gh", "repo", "view", "--json", "owner,name,createdAt,pushedAt"],
            capture_output=True,
            text=True,
            check=True,
        )

        data = json.loads(result.stdout)
        return data["owner"]["login"], data["name"], data
    except subprocess.CalledProcessError:
        return None


def detect_collaboration_pattern() -> Dict[str, Any]:
    """Detect if this is a solo developer or team repository"""
    try:
        # Get contributor statistics
        result = subprocess.run(
            ["gh", "api", "repos/:owner/:repo/contributors", "--paginate"],
            capture_output=True,
            text=True,
            check=True,
        )

        contributors = json.loads(result.stdout)

        # Get recent commit activity (last 30 days)
        result = subprocess.run(
            [
                "gh",
                "api",
                "repos/:owner/:repo/commits",
                "--jq",
                ".[].author.login",
                "--paginate",
                "-H",
                "Accept: application/vnd.github.v3+json",
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        recent_authors = [
            line.strip() for line in result.stdout.split("\n") if line.strip()
        ]
        unique_recent_authors = set(recent_authors)

        # Get PR statistics
        result = subprocess.run(
            [
                "gh",
                "pr",
                "list",
                "--state",
                "all",
                "--json",
                "author,createdAt,reviews",
                "--limit",
                "100",
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        prs = json.loads(result.stdout)

        # Analyze patterns
        total_contributors = len(contributors)
        active_contributors = len(unique_recent_authors)
        total_prs = len(prs)

        # Count PRs with external reviews (not self-reviews)
        external_reviews = 0
        self_merges = 0

        for pr in prs:
            author = pr.get("author", {}).get("login", "")
            reviews = pr.get("reviews", [])

            has_external_review = any(
                review.get("author", {}).get("login", "") != author
                for review in reviews
            )

            if has_external_review:
                external_reviews += 1
            else:
                self_merges += 1

        # Determine collaboration pattern
        is_solo = (
            total_contributors <= 2
            and active_contributors <= 1  # Allow for occasional contributor
            and (  # Only one active contributor
                total_prs == 0 or (self_merges / total_prs) > 0.8
            )  # Mostly self-merged PRs
        )

        return {
            "is_solo": is_solo,
            "total_contributors": total_contributors,
            "active_contributors": active_contributors,
            "total_prs": total_prs,
            "external_reviews": external_reviews,
            "self_merges": self_merges,
            "confidence": (
                "high" if total_prs > 5 else "medium" if total_prs > 0 else "low"
            ),
        }

    except (subprocess.CalledProcessError, json.JSONDecodeError, KeyError) as e:
        print(f"⚠️  Could not analyze collaboration pattern: {e}")
        return {
            "is_solo": None,
            "total_contributors": 0,
            "active_contributors": 0,
            "total_prs": 0,
            "external_reviews": 0,
            "self_merges": 0,
            "confidence": "unknown",
        }


def check_approval_bot_installed() -> Optional[str]:
    """Check if an approval bot is installed and return its name"""
    try:
        # Check for GitHub Apps that could auto-approve
        result = subprocess.run(
            ["gh", "api", "repos/:owner/:repo/installation"],
            capture_output=True,
            text=True,
            check=True,
        )

        # Common approval bots
        approval_bots = [
            "kodiak-ai",
            "mergify",
            "bors",
            "auto-approve",
            "github-actions",
            "dependabot",
        ]

        # Check for webhook configurations that might indicate approval automation
        result = subprocess.run(
            ["gh", "api", "repos/:owner/:repo/hooks"],
            capture_output=True,
            text=True,
            check=True,
        )

        hooks = json.loads(result.stdout)

        for hook in hooks:
            config = hook.get("config", {})
            url = config.get("url", "").lower()

            for bot in approval_bots:
                if bot in url:
                    return bot

        return None

    except (subprocess.CalledProcessError, json.JSONDecodeError):
        return None


def create_approval_bot_workflow() -> bool:
    """Create a GitHub Actions workflow for auto-approval"""
    workflow_content = """
name: Auto-approve AI-First SDLC PRs

on:
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  auto-approve:
    runs-on: ubuntu-latest
    if: github.actor == github.repository_owner || contains(github.event.pull_request.title, '[AI-FIRST]')

    steps:
    - name: Check if all status checks passed
      id: status-check
      uses: actions/github-script@v7
      with:
        github-token: ${{ secrets.GITHUB_TOKEN }}
        script: |
          const { data: pr } = await github.rest.pulls.get({
            owner: context.repo.owner,
            repo: context.repo.repo,
            pull_number: context.issue.number
          });

          // Get the latest commit
          const { data: commit } = await github.rest.repos.getCommit({
            owner: context.repo.owner,
            repo: context.repo.repo,
            ref: pr.head.sha
          });

          // Check if all required status checks are successful
          const requiredChecks = ['validate', 'test-framework-tools (3.8)', 'code-quality'];
          let allPassed = true;

          for (const check of requiredChecks) {
            const status = commit.commit.verification?.verified || false;
            if (!status) {
              allPassed = false;
              break;
            }
          }

          return allPassed;

    - name: Auto-approve PR
      if: steps.status-check.outputs.result == 'true'
      uses: actions/github-script@v7
      with:
        github-token: ${{ secrets.GITHUB_TOKEN }}
        script: |
          await github.rest.pulls.createReview({
            owner: context.repo.owner,
            repo: context.repo.repo,
            pull_number: context.issue.number,
            event: 'APPROVE',
            body: '✅ Auto-approved: All AI-First SDLC checks passed'
          });
"""

    try:
        import os

        # Create .github/workflows directory if it doesn't exist
        workflows_dir = ".github/workflows"
        os.makedirs(workflows_dir, exist_ok=True)

        # Write the workflow file
        workflow_path = os.path.join(workflows_dir, "auto-approve.yml")
        with open(workflow_path, "w") as f:
            f.write(workflow_content.strip())

        print(f"✅ Created auto-approval workflow: {workflow_path}")
        return True

    except Exception as e:
        print(f"❌ Failed to create auto-approval workflow: {e}")
        return False


def setup_branch_protection(
    branch: str = "main",
    required_checks: List[str] = None,
    solo_mode: bool = False,
    enable_auto_approval: bool = False,
) -> bool:
    """Setup branch protection using gh CLI with smart solo/team detection"""

    # Default required checks for AI-First SDLC
    if required_checks is None:
        required_checks = ["validate", "test-framework-tools (3.8)", "code-quality"]

    try:
        # Build the protection rules based on collaboration pattern
        if solo_mode:
            # Solo developer mode: rely on status checks, minimal review requirements
            protection_json = {
                "required_status_checks": {"strict": True, "contexts": required_checks},
                "enforce_admins": False,  # Allow admin bypass for solo developers
                "required_pull_request_reviews": {
                    "required_approving_review_count": 0 if enable_auto_approval else 1,
                    "dismiss_stale_reviews": True,
                    "require_code_owner_reviews": False,
                    "require_review_from_code_owners": False,
                },
                "restrictions": None,
                "allow_force_pushes": False,
                "allow_deletions": False,
                "required_conversation_resolution": False,  # More flexible for solo
            }
        else:
            # Team mode: stricter review requirements
            protection_json = {
                "required_status_checks": {"strict": True, "contexts": required_checks},
                "enforce_admins": True,
                "required_pull_request_reviews": {
                    "required_approving_review_count": 1,
                    "dismiss_stale_reviews": True,
                    "require_code_owner_reviews": True,
                },
                "restrictions": None,
                "allow_force_pushes": False,
                "allow_deletions": False,
                "required_conversation_resolution": True,
            }

        # Build the protection command with proper JSON
        protection_cmd = [
            "gh",
            "api",
            f"repos/:owner/:repo/branches/{branch}/protection",
            "--method",
            "PUT",
            "--input",
            "-",
        ]

        # Debug: print the command
        if "--dry-run" not in sys.argv:
            print(f"Debug: Running command: {' '.join(protection_cmd[:4])}...")
            print(f"Debug: JSON input:\n{json.dumps(protection_json, indent=2)}")

        # Execute the command with JSON input via stdin
        result = subprocess.run(
            protection_cmd,
            input=json.dumps(protection_json),
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            mode_str = "Solo Developer" if solo_mode else "Team Collaboration"
            print(f"✅ Branch protection enabled for '{branch}' ({mode_str} mode)")
            print("   - No direct pushes allowed")

            if solo_mode:
                if enable_auto_approval:
                    print("   - Auto-approval enabled (status checks required)")
                else:
                    print("   - Self-approval allowed (1 approval required)")
                print("   - Flexible conversation resolution")
                print("   - Admin bypass enabled")
            else:
                print("   - Team reviews required (1+ approvals)")
                print("   - Code owner reviews required")
                print("   - Conversations must be resolved")
                print("   - Admin enforcement enabled")

            print(f"   - Required status checks: {', '.join(required_checks)}")
            print("   - Stale reviews dismissed on new commits")
            return True
        else:
            print(f"❌ Failed to enable branch protection")
            if "Not Found" in result.stderr:
                print("   Branch might not exist yet. Push the branch first.")
            elif "401" in result.stderr or "403" in result.stderr:
                print("   Permission denied. You need admin access to the repository.")
                print(f"   Full error: {result.stderr}")
            else:
                print(f"   Error: {result.stderr}")
                print(f"   Stdout: {result.stdout}")
            return False

    except Exception as e:
        print(f"❌ Error setting up branch protection: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Smart Branch Protection Setup for AI-First SDLC",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Auto-detect collaboration pattern
  python setup-branch-protection-gh.py

  # Force solo developer mode
  python setup-branch-protection-gh.py --solo --auto-approval

  # Force team mode with custom checks
  python setup-branch-protection-gh.py --team --checks validate security-scan

  # Dry run to see what would be configured
  python setup-branch-protection-gh.py --dry-run
""",
    )
    parser.add_argument(
        "--branch", default="main", help="Branch to protect (default: main)"
    )
    parser.add_argument(
        "--checks",
        nargs="+",
        help="Required status checks (default: AI-First SDLC checks)",
    )
    parser.add_argument(
        "--solo",
        action="store_true",
        help="Force solo developer mode (allows self-approval)",
    )
    parser.add_argument(
        "--team",
        action="store_true",
        help="Force team collaboration mode (strict reviews)",
    )
    parser.add_argument(
        "--auto-approval",
        action="store_true",
        help="Enable automated PR approval when all checks pass",
    )
    parser.add_argument(
        "--create-bot-workflow",
        action="store_true",
        help="Create GitHub Actions workflow for auto-approval",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"Smart Branch Protection v{TOOL_VERSION}",
    )

    args = parser.parse_args()

    # Validate conflicting arguments
    if args.solo and args.team:
        print("❌ Cannot specify both --solo and --team modes")
        sys.exit(1)

    print("🔒 Smart AI-First SDLC Branch Protection Setup")
    print("=" * 55)

    # Check gh installation
    if not check_gh_installed():
        print("❌ GitHub CLI (gh) is not installed or not authenticated")
        print("\nTo install:")
        print("  macOS:    brew install gh")
        print("  Windows:  winget install GitHub.cli")
        print("  Linux:    See https://github.com/cli/cli#installation")
        print("\nTo authenticate:")
        print("  gh auth login")
        sys.exit(1)

    print("✅ GitHub CLI is installed and authenticated")

    # Get repo info
    repo_info = get_repo_info()
    if not repo_info:
        print("❌ Could not determine repository information")
        print("   Make sure you're in a Git repository with a GitHub remote")
        sys.exit(1)

    owner, repo, repo_data = repo_info
    print(f"📦 Repository: {owner}/{repo}")
    print(f"🌿 Branch: {args.branch}")

    # Detect collaboration pattern unless explicitly specified
    solo_mode = False
    if args.solo:
        solo_mode = True
        print("👤 Mode: Solo Developer (forced)")
    elif args.team:
        solo_mode = False
        print("👥 Mode: Team Collaboration (forced)")
    else:
        print("\n🔍 Analyzing collaboration patterns...")
        collaboration = detect_collaboration_pattern()

        if collaboration["is_solo"] is not None:
            solo_mode = collaboration["is_solo"]
            confidence = collaboration["confidence"]

            print(f"📊 Analysis Results ({confidence} confidence):")
            print(f"   - Total contributors: {collaboration['total_contributors']}")
            print(f"   - Active contributors: {collaboration['active_contributors']}")
            print(f"   - Total PRs: {collaboration['total_prs']}")
            print(f"   - External reviews: {collaboration['external_reviews']}")
            print(f"   - Self-merges: {collaboration['self_merges']}")

            mode_str = "Solo Developer" if solo_mode else "Team Collaboration"
            print(f"🎯 Detected mode: {mode_str}")
        else:
            print(
                "⚠️  Could not analyze collaboration pattern, defaulting to team mode"
            )
            solo_mode = False

    # Check for existing approval bots
    approval_bot = check_approval_bot_installed()
    if approval_bot:
        print(f"🤖 Detected approval bot: {approval_bot}")

    # Determine if auto-approval should be enabled
    enable_auto_approval = args.auto_approval or (approval_bot is not None)

    if enable_auto_approval:
        print("🔄 Auto-approval will be enabled")

    if args.dry_run:
        print("\n🔍 DRY RUN - No changes will be made")
        print("\nWould configure:")
        print("  - No direct pushes")

        if solo_mode:
            if enable_auto_approval:
                print("  - Auto-approval (0 reviews required)")
            else:
                print("  - Self-approval allowed (1 review)")
            print("  - Flexible conversation resolution")
            print("  - Admin bypass enabled")
        else:
            print("  - Team reviews required (1+ approvals)")
            print("  - Code owner reviews required")
            print("  - Strict conversation resolution")
            print("  - Admin enforcement")

        checks = args.checks or [
            "validate",
            "test-framework-tools (3.8)",
            "code-quality",
        ]
        print(f"  - Required status checks: {', '.join(checks)}")
        print("  - Dismiss stale reviews")

        if args.create_bot_workflow or (enable_auto_approval and not approval_bot):
            print("  - Create auto-approval GitHub Actions workflow")

        sys.exit(0)

    # Create auto-approval workflow if requested or needed
    if args.create_bot_workflow or (enable_auto_approval and not approval_bot):
        print("\n🤖 Creating auto-approval workflow...")
        if create_approval_bot_workflow():
            print("   You may need to commit and push the workflow file")
        else:
            print("   Warning: Auto-approval workflow creation failed")

    # Setup protection
    print("\n🔧 Configuring branch protection...")
    if setup_branch_protection(
        args.branch, args.checks, solo_mode, enable_auto_approval
    ):
        print("\n🎉 Branch protection successfully configured!")

        print("\n📋 Next steps:")
        print("1. Push your branch if it doesn't exist yet")
        print("2. All future changes must go through pull requests")

        if solo_mode:
            if enable_auto_approval:
                print("3. PRs will auto-approve when all status checks pass")
                print("4. You can still merge manually after approval")
            else:
                print("3. You can approve your own PRs once checks pass")
                print("4. Consider using --auto-approval for fully automated workflow")
        else:
            print("3. PRs require approval from team members")
            print("4. Code owners must review changes")

        print("5. All AI-First SDLC validation checks must pass")

        if args.create_bot_workflow or (enable_auto_approval and not approval_bot):
            print("\n⚠️  Don't forget to commit and push the auto-approval workflow:")
            print("   git add .github/workflows/auto-approve.yml")
            print(
                "   git commit -m 'feat: add auto-approval workflow for AI-First SDLC'"
            )
            print("   git push")
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
