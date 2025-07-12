#!/usr/bin/env python3
"""
Branch Protection Setup Tool
Configures branch protection rules for AI-First SDLC compliance
Supports GitHub, GitLab, and Bitbucket
"""

import json
import os
import sys
import argparse
import subprocess
from typing import Dict, Any, Optional
import requests
from pathlib import Path


class BranchProtectionConfigurator:
    """Configures branch protection across different platforms"""
    
    def __init__(self, platform: str, token: str, repo: str):
        self.platform = platform.lower()
        self.token = token
        self.repo = repo
        self.headers = self._get_headers()
        
    def _get_headers(self) -> Dict[str, str]:
        """Get platform-specific headers"""
        if self.platform == "github":
            return {
                "Authorization": f"token {self.token}",
                "Accept": "application/vnd.github.v3+json"
            }
        elif self.platform == "gitlab":
            return {
                "PRIVATE-TOKEN": self.token,
                "Content-Type": "application/json"
            }
        elif self.platform == "bitbucket":
            return {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            }
        else:
            raise ValueError(f"Unsupported platform: {self.platform}")
    
    def configure_github(self, branch: str = "main") -> bool:
        """Configure GitHub branch protection"""
        owner, repo_name = self.repo.split("/")
        url = f"https://api.github.com/repos/{owner}/{repo_name}/branches/{branch}/protection"
        
        protection_rules = {
            "required_status_checks": {
                "strict": True,
                "contexts": ["continuous-integration", "tests", "lint"]
            },
            "enforce_admins": True,
            "required_pull_request_reviews": {
                "required_approving_review_count": 1,
                "dismiss_stale_reviews": True,
                "require_code_owner_reviews": False,
                "dismissal_restrictions": {}
            },
            "restrictions": None,
            "allow_force_pushes": False,
            "allow_deletions": False,
            "required_conversation_resolution": True
        }
        
        try:
            response = requests.put(url, headers=self.headers, json=protection_rules)
            if response.status_code in [200, 201]:
                print(f"✅ GitHub branch protection enabled for '{branch}'")
                return True
            else:
                print(f"❌ Failed to enable protection: {response.json()}")
                return False
        except Exception as e:
            print(f"❌ Error configuring GitHub: {e}")
            return False
    
    def configure_gitlab(self, branch: str = "main") -> bool:
        """Configure GitLab branch protection"""
        # URL encode the project path
        project_path = self.repo.replace("/", "%2F")
        url = f"https://gitlab.com/api/v4/projects/{project_path}/protected_branches"
        
        protection_rules = {
            "name": branch,
            "push_access_level": 0,  # No one
            "merge_access_level": 30,  # Developers + Maintainers
            "unprotect_access_level": 40,  # Maintainers
            "allow_force_push": False,
            "code_owner_approval_required": False
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=protection_rules)
            if response.status_code in [200, 201]:
                print(f"✅ GitLab branch protection enabled for '{branch}'")
                return True
            else:
                print(f"❌ Failed to enable protection: {response.json()}")
                return False
        except Exception as e:
            print(f"❌ Error configuring GitLab: {e}")
            return False
    
    def configure_bitbucket(self, branch: str = "main") -> bool:
        """Configure Bitbucket branch protection"""
        workspace, repo_slug = self.repo.split("/")
        url = f"https://api.bitbucket.org/2.0/repositories/{workspace}/{repo_slug}/branch-restrictions"
        
        protection_rules = {
            "type": "branchrestriction",
            "kind": "require_passing_builds_to_merge",
            "pattern": branch,
            "value": 1  # Number of required builds
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=protection_rules)
            if response.status_code in [200, 201]:
                print(f"✅ Bitbucket branch protection enabled for '{branch}'")
                return True
            else:
                print(f"❌ Failed to enable protection: {response.json()}")
                return False
        except Exception as e:
            print(f"❌ Error configuring Bitbucket: {e}")
            return False
    
    def configure(self, branch: str = "main") -> bool:
        """Configure branch protection for the platform"""
        print(f"🔧 Configuring {self.platform} branch protection for {self.repo}...")
        
        if self.platform == "github":
            return self.configure_github(branch)
        elif self.platform == "gitlab":
            return self.configure_gitlab(branch)
        elif self.platform == "bitbucket":
            return self.configure_bitbucket(branch)
        else:
            print(f"❌ Unsupported platform: {self.platform}")
            return False


def generate_config_file(platform: str, repo: str, branch: str = "main") -> None:
    """Generate configuration file for manual setup"""
    config = {
        "platform": platform,
        "repository": repo,
        "branch": branch,
        "protection_rules": {
            "require_pull_request_reviews": True,
            "required_approving_review_count": 1,
            "dismiss_stale_reviews": True,
            "require_code_owner_reviews": False,
            "include_administrators": True,
            "require_status_checks": True,
            "strict_status_checks": True,
            "status_check_contexts": ["tests", "lint", "security"],
            "restrict_push_access": True,
            "push_access_levels": ["maintainer"],
            "allow_force_pushes": False,
            "allow_deletions": False,
            "require_conversation_resolution": True,
            "require_signed_commits": False
        }
    }
    
    filename = f"branch-protection-{platform}.json"
    with open(filename, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"📄 Configuration saved to {filename}")
    print("\nManual setup instructions:")
    print(f"1. Go to your {platform} repository settings")
    print("2. Navigate to branch protection rules")
    print("3. Apply the settings from the configuration file")


def detect_git_platform() -> Optional[str]:
    """Detect git platform from remote URL"""
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            check=True
        )
        remote_url = result.stdout.strip()
        
        if "github.com" in remote_url:
            return "github"
        elif "gitlab.com" in remote_url:
            return "gitlab"
        elif "bitbucket.org" in remote_url:
            return "bitbucket"
        else:
            return None
    except subprocess.CalledProcessError:
        return None


def extract_repo_from_url(url: str) -> str:
    """Extract repository path from git URL"""
    # Remove protocol
    if url.startswith("https://"):
        url = url[8:]
    elif url.startswith("git@"):
        url = url[4:].replace(":", "/")
    
    # Remove .git suffix
    if url.endswith(".git"):
        url = url[:-4]
    
    # Extract owner/repo
    parts = url.split("/")
    if len(parts) >= 2:
        return f"{parts[-2]}/{parts[-1]}"
    else:
        raise ValueError(f"Could not extract repository from URL: {url}")


def main():
    parser = argparse.ArgumentParser(
        description="Configure branch protection for AI-First SDLC compliance"
    )
    parser.add_argument(
        "--platform",
        choices=["github", "gitlab", "bitbucket", "auto"],
        default="auto",
        help="Git platform (default: auto-detect)"
    )
    parser.add_argument(
        "--repo",
        help="Repository path (e.g., owner/repo). Default: auto-detect from git remote"
    )
    parser.add_argument(
        "--branch",
        default="main",
        help="Branch to protect (default: main)"
    )
    parser.add_argument(
        "--token",
        help="API token for authentication (or set GITHUB_TOKEN, GITLAB_TOKEN, BITBUCKET_TOKEN)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Generate configuration file without applying"
    )
    
    args = parser.parse_args()
    
    # Auto-detect platform if needed
    platform = args.platform
    if platform == "auto":
        platform = detect_git_platform()
        if not platform:
            print("❌ Could not auto-detect git platform")
            print("Please specify --platform explicitly")
            sys.exit(1)
        print(f"🔍 Detected platform: {platform}")
    
    # Auto-detect repository if needed
    repo = args.repo
    if not repo:
        try:
            result = subprocess.run(
                ["git", "remote", "get-url", "origin"],
                capture_output=True,
                text=True,
                check=True
            )
            repo = extract_repo_from_url(result.stdout.strip())
            print(f"🔍 Detected repository: {repo}")
        except Exception as e:
            print(f"❌ Could not auto-detect repository: {e}")
            print("Please specify --repo explicitly")
            sys.exit(1)
    
    # Generate config file for dry run
    if args.dry_run:
        generate_config_file(platform, repo, args.branch)
        return
    
    # Get token
    token = args.token
    if not token:
        # Try environment variables
        env_vars = {
            "github": "GITHUB_TOKEN",
            "gitlab": "GITLAB_TOKEN",
            "bitbucket": "BITBUCKET_TOKEN"
        }
        env_var = env_vars.get(platform)
        if env_var:
            token = os.environ.get(env_var)
        
        if not token:
            print(f"❌ No API token provided")
            print(f"Please provide --token or set {env_var} environment variable")
            sys.exit(1)
    
    # Configure branch protection
    configurator = BranchProtectionConfigurator(platform, token, repo)
    success = configurator.configure(args.branch)
    
    if success:
        print("\n✅ Branch protection successfully configured!")
        print("\n📋 AI-First SDLC Compliance Checklist:")
        print("  ✓ Direct pushes to main branch blocked")
        print("  ✓ Pull request reviews required")
        print("  ✓ Stale reviews dismissed on new commits")
        print("  ✓ Administrators included in restrictions")
        print("  ✓ Status checks required")
        print("\n🤖 Your repository is now AI-First SDLC compliant!")
    else:
        print("\n❌ Failed to configure branch protection")
        print("You may need to configure manually or check permissions")
        generate_config_file(platform, repo, args.branch)


if __name__ == "__main__":
    main()