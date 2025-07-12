#!/usr/bin/env python3
"""
Branch Protection Setup Tool using GitHub CLI
More secure version that uses gh instead of direct token handling
"""

import subprocess
import sys
import argparse
import json
from typing import Dict, Any, Optional


def check_gh_installed() -> bool:
    """Check if gh CLI is installed and authenticated"""
    try:
        # Check if gh is installed
        result = subprocess.run(
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
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def get_repo_info() -> Optional[tuple]:
    """Get repository owner and name using gh"""
    try:
        result = subprocess.run(
            ["gh", "repo", "view", "--json", "owner,name"],
            capture_output=True,
            text=True,
            check=True
        )
        
        data = json.loads(result.stdout)
        return data['owner']['login'], data['name']
    except subprocess.CalledProcessError:
        return None


def setup_branch_protection(branch: str = "main", required_checks: list = None) -> bool:
    """Setup branch protection using gh CLI"""
    
    # Default required checks for AI-First SDLC
    if required_checks is None:
        required_checks = ["validate", "test-framework-tools (3.8)"]
    
    try:
        # Build the protection rules
        protection_cmd = [
            "gh", "api",
            f"repos/:owner/:repo/branches/{branch}/protection",
            "--method", "PUT",
            "-f", "required_status_checks[strict]=true",
            "-f", "enforce_admins=true",
            "-f", "required_pull_request_reviews[required_approving_review_count]=1",
            "-f", "required_pull_request_reviews[dismiss_stale_reviews]=true",
            "-f", "required_pull_request_reviews[require_code_owner_reviews]=false",
            "-f", "restrictions=null",
            "-f", "allow_force_pushes=false",
            "-f", "allow_deletions=false",
            "-f", "required_conversation_resolution=true",
            "-f", "lock_branch=false",
            "-f", "allow_fork_syncing=true"
        ]
        
        # Add required status checks
        for check in required_checks:
            protection_cmd.extend(["-f", f"required_status_checks[contexts][]={check}"])
        
        # Execute the command
        result = subprocess.run(
            protection_cmd,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print(f"✅ Branch protection enabled for '{branch}'")
            print("   - No direct pushes allowed")
            print("   - Pull request reviews required (1 approval)")
            print("   - Status checks must pass")
            print("   - Stale reviews dismissed on new commits")
            print("   - Conversations must be resolved")
            return True
        else:
            print(f"❌ Failed to enable branch protection")
            if "Not Found" in result.stderr:
                print("   Branch might not exist yet. Push the branch first.")
            elif "401" in result.stderr or "403" in result.stderr:
                print("   Permission denied. You need admin access to the repository.")
            else:
                print(f"   Error: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error setting up branch protection: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Setup branch protection using GitHub CLI (more secure)"
    )
    parser.add_argument(
        "--branch",
        default="main",
        help="Branch to protect (default: main)"
    )
    parser.add_argument(
        "--checks",
        nargs="+",
        help="Required status checks (default: validate, test-framework-tools)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes"
    )
    
    args = parser.parse_args()
    
    print("🔒 AI-First SDLC Branch Protection Setup (Secure)")
    print("=" * 50)
    
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
    
    owner, repo = repo_info
    print(f"📦 Repository: {owner}/{repo}")
    print(f"🌿 Branch: {args.branch}")
    
    if args.dry_run:
        print("\n🔍 DRY RUN - No changes will be made")
        print("\nWould configure:")
        print("  - No direct pushes")
        print("  - Require 1 PR approval")
        print("  - Dismiss stale reviews")
        print("  - Require status checks:", args.checks or ["validate", "test-framework-tools (3.8)"])
        print("  - Require conversation resolution")
        sys.exit(0)
    
    # Setup protection
    if setup_branch_protection(args.branch, args.checks):
        print("\n🎉 Branch protection successfully configured!")
        print("\nNext steps:")
        print("1. Push your branch if it doesn't exist yet")
        print("2. All future changes must go through pull requests")
        print("3. Configure additional status checks as needed")
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()