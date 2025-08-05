#!/usr/bin/env python3
"""
Feature Proposal Checker
Ensures feature proposals exist for feature branches
"""

import os
import subprocess
import sys
from pathlib import Path
import re
import argparse


def get_current_branch():
    """Get the current git branch name"""
    try:
        # Try to get symbolic ref (normal case)
        result = subprocess.run(
            ["git", "symbolic-ref", "--short", "HEAD"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        # In CI or detached HEAD, try to get branch from environment or git describe
        # GitHub Actions
        branch = os.environ.get('GITHUB_HEAD_REF') or os.environ.get('GITHUB_REF_NAME')
        if branch:
            return branch
            
        # GitLab CI
        branch = os.environ.get('CI_MERGE_REQUEST_SOURCE_BRANCH_NAME') or os.environ.get('CI_COMMIT_BRANCH')
        if branch:
            return branch
            
        # Try git describe as last resort
        try:
            result = subprocess.run(
                ["git", "describe", "--all", "--exact-match"],
                capture_output=True,
                text=True,
                check=True
            )
            branch = result.stdout.strip()
            if branch.startswith('heads/'):
                return branch[6:]
        except subprocess.CalledProcessError:
            pass
            
        return None


def extract_feature_name(branch_name):
    """Extract feature name from branch name"""
    # Pattern: feature/feature-name or fix/bug-name
    match = re.match(r"^(feature|fix|enhancement)/(.+)$", branch_name)
    if match:
        return match.group(2)
    return None


def find_feature_proposal(feature_name):
    """Look for feature proposal file"""
    proposal_dirs = [
        "docs/feature-proposals",
        "feature-proposals",
        "proposals",
        "docs/proposals"
    ]
    
    for proposal_dir in proposal_dirs:
        if not os.path.exists(proposal_dir):
            continue
            
        # Look for files containing the feature name
        for file in Path(proposal_dir).glob("*.md"):
            if feature_name.lower() in file.name.lower():
                return file
            
            # Check file content for branch name
            try:
                with open(file, 'r') as f:
                    content = f.read()
                    if f"feature/{feature_name}" in content or feature_name in content:
                        return file
            except:
                continue
    
    return None


def check_proposal_content(proposal_file, branch_name):
    """Verify proposal has required fields"""
    required_fields = [
        "Target Branch:",
        "## Motivation",
        "## Proposed Solution",
        "## Success Criteria"
    ]
    
    try:
        with open(proposal_file, 'r') as f:
            content = f.read()
            
        missing_fields = []
        for field in required_fields:
            if field not in content:
                missing_fields.append(field)
        
        # Check if branch name matches
        if f"`{branch_name}`" not in content:
            print(f"⚠️  Branch name '{branch_name}' not found in proposal")
            print(f"   Please ensure 'Target Branch: `{branch_name}`' is in the proposal")
        
        if missing_fields:
            print(f"⚠️  Proposal is missing required sections:")
            for field in missing_fields:
                print(f"   - {field}")
            return False
            
        return True
    except Exception as e:
        print(f"❌ Error reading proposal: {e}")
        return False


def main():
    """Main validation logic"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Check for feature proposal")
    parser.add_argument("--branch", help="Branch name to check (default: current branch)")
    args = parser.parse_args()
    
    # Get branch name
    if args.branch:
        branch = args.branch
    else:
        branch = get_current_branch()
        if not branch:
            print("❌ Could not determine current branch")
            print("   In CI environments, use --branch parameter")
            sys.exit(1)
    
    # Skip check for main/master branches
    if branch in ["main", "master", "develop"]:
        sys.exit(0)
    
    # Skip check for non-feature branches unless it's a feature/fix/enhancement
    if not branch.startswith(("feature/", "fix/", "enhancement/")):
        print(f"ℹ️  Skipping proposal check for branch: {branch}")
        sys.exit(0)
    
    # Extract feature name
    feature_name = extract_feature_name(branch)
    if not feature_name:
        print(f"⚠️  Could not extract feature name from branch: {branch}")
        sys.exit(0)
    
    # Look for feature proposal
    proposal_file = find_feature_proposal(feature_name)
    
    if not proposal_file:
        print(f"❌ No feature proposal found for branch: {branch}")
        print(f"\n📝 Please create a feature proposal:")
        print(f"   1. Copy templates/feature-proposal.md to docs/feature-proposals/")
        print(f"   2. Name it descriptively (e.g., 01-{feature_name}.md)")
        print(f"   3. Fill out all required sections")
        print(f"   4. Set 'Target Branch: `{branch}`'")
        print(f"\n❓ Why is this required?")
        print(f"   Feature proposals ensure clear planning and prevent wasted effort.")
        print(f"   They are mandatory in the AI-First SDLC framework.")
        sys.exit(1)
    
    print(f"✅ Found feature proposal: {proposal_file}")
    
    # Verify proposal content
    if not check_proposal_content(proposal_file, branch):
        print(f"\n❌ Feature proposal needs updates")
        sys.exit(1)
    
    print(f"✅ Feature proposal is properly formatted")
    sys.exit(0)


if __name__ == "__main__":
    main()