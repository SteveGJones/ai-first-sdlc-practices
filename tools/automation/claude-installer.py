#!/usr/bin/env python3
"""
Claude AI Agent Installer - DevOps Grade
Single unified installer for AI agents and framework components
"""

import argparse
import base64
import json
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional
import requests
from dataclasses import dataclass
import hashlib


@dataclass
class AgentSpec:
    """Agent specification with metadata."""

    name: str
    version: str
    category: str
    dependencies: List[str]
    source_path: str
    content: bytes
    checksum: str


class GitHubAPI:
    """Efficient GitHub API client for selective downloads."""

    def __init__(self, repo: str, branch: str = "main"):
        self.repo = repo
        self.branch = branch
        self.base_url = f"https://api.github.com/repos/{repo}"
        self.rate_limit_remaining = 60  # GitHub API limit for unauthenticated

    def get_file(self, path: str) -> bytes:
        """Download single file via GitHub API."""
        url = f"{self.base_url}/contents/{path}?ref={self.branch}"

        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()

            data = json.loads(response.json())
            if data.get("type") != "file":
                raise ValueError(f"Path {path} is not a file")

            content = base64.b64decode(data["content"]).decode("utf-8")
            return content

        except requests.RequestException as e:
            raise ConnectionError(f"Failed to download {path}: {e}")

    def get_directory_listing(self, path: str) -> List[Dict]:
        """Get directory contents via GitHub API."""
        url = f"{self.base_url}/contents/{path}?ref={self.branch}"

        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            return response.json()

        except requests.RequestException as e:
            raise ConnectionError(f"Failed to list directory {path}: {e}")


class ClaudeInstaller:
    """DevOps-grade installer with progressive enhancement."""

    MODES = {
        "agents-only": "Install only AI agents (fastest)",
        "with-framework": "Agents + essential framework tools",
        "full-setup": "Complete AI-First SDLC framework",
    }

    # Core agents that should be installed in all modes
    CORE_AGENTS = [
        "sdlc-enforcer",
        "solution-architect",
        "critical-goal-reviewer"]

    def __init__(self, project_root: Path, mode: str = "agents-only"):
        self.project_root = project_root
        self.mode = mode
        self.target_dir = project_root / ".claude"
        self.github_api = GitHubAPI("SteveGJones/ai-first-sdlc-practices")
        self.installed_manifest = {}

    def validate_environment(self) -> bool:
        """Validate installation environment."""
        if not self.project_root.exists():
            print(
                f"Error: Project directory does not exist: {self.project_root}")
            return False

        if not self.project_root.is_dir():
            print(
                f"Error: Project path is not a directory: {self.project_root}")
            return False

        # Check if we can write to the target directory
        try:
            self.target_dir.mkdir(parents=True, exist_ok=True)
            test_file = self.target_dir / ".write_test"
            test_file.write_text("test")
            test_file.unlink()
            return True
        except PermissionError:
            print(f"Error: No write permission to {self.target_dir}")
            return False
        except Exception as e:
            print(f"Error: Cannot write to target directory: {e}")
            return False

    def load_agent_manifest(self) -> Dict:
        """Load agent manifest from GitHub."""
        try:
            content = self.github_api.get_file("release/agent-manifest.json")
            return json.loads(content.decode("utf-8"))
        except Exception as e:
            print(f"Warning: Could not load agent manifest: {e}")
            return {"categories": {}}

    def get_available_agents(self) -> Dict[str, List[str]]:
        """Get list of available agents by category."""
        manifest = self.load_agent_manifest()
        return manifest.get("categories", {})

    def select_agents_for_mode(self) -> List[str]:
        """Select agents based on installation mode."""
        available = self.get_available_agents()

        if self.mode == "agents-only":
            # Just core agents
            return self.CORE_AGENTS

        elif self.mode == "with-framework":
            # Core + some specialized agents
            agents = self.CORE_AGENTS.copy()

            # Add framework helpers
            if "sdlc" in available:
                agents.extend(["framework-validator"])

            # Add GitHub integration
            if "core" in available:
                agents.extend(["github-integration-specialist"])

            return agents

        else:  # full-setup
            # All core agents + selection from each category
            agents = []

            # All core agents
            if "core" in available:
                agents.extend(available["core"])

            # Essential from other categories
            if "sdlc" in available:
                agents.extend(["framework-validator", "ai-first-kick-starter"])

            if "testing" in available:
                agents.extend(["ai-test-engineer"])

            return agents

    def download_agent(
            self,
            agent_name: str,
            category: str) -> Optional[AgentSpec]:
        """Download a single agent."""
        try:
            source_path = f"agents/{category}/{agent_name}.md"
            content = self.github_api.get_file(source_path)

            # Calculate checksum
            checksum = hashlib.sha256(content).hexdigest()

            return AgentSpec(
                name=agent_name,
                version="1.0.0",  # Default version for initial release
                category=category,
                dependencies=[],  # No dependencies for base agents
                source_path=source_path,
                content=content,
                checksum=checksum,
            )

        except Exception as e:
            print(f"Warning: Could not download agent {agent_name}: {e}")
            return None

    def find_agent_category(
        self, agent_name: str, available: Dict[str, List[str]]
    ) -> Optional[str]:
        """Find which category an agent belongs to."""
        for category, agents in available.items():
            if agent_name in agents:
                return category
        return None

    def install_agents_only(self) -> bool:
        """Install only AI agents (fastest mode)."""
        print("🚀 Installing AI agents only...")
        print("   This will create .claude/agents/ with core AI agents")
        print()

        # Create target structure
        agents_dir = self.target_dir / "agents"
        agents_dir.mkdir(parents=True, exist_ok=True)

        # Get available agents
        available = self.get_available_agents()
        selected_agents = self.select_agents_for_mode()

        installed_count = 0
        failed_agents = []

        for agent_name in selected_agents:
            category = self.find_agent_category(agent_name, available)
            if not category:
                print(f"   ⚠️  Agent {agent_name} not found in manifest")
                failed_agents.append(agent_name)
                continue

            print(f"   📥 Downloading {agent_name}...")
            agent_spec = self.download_agent(agent_name, category)

            if agent_spec:
                # Write agent file
                agent_file = agents_dir / f"{agent_name}.md"
                agent_file.write_bytes(agent_spec.content)

                # Record in manifest
                self.installed_manifest[agent_name] = {
                    "version": agent_spec.version,
                    "category": agent_spec.category,
                    "checksum": agent_spec.checksum,
                    "installed_date": time.strftime("%Y-%m-%d %H:%M:%S"),
                }

                installed_count += 1
                print(f"   ✅ Installed {agent_name}")
            else:
                failed_agents.append(agent_name)

        # Save installation manifest
        manifest_file = self.target_dir / "agent-manifest.json"
        with open(manifest_file, "w") as f:
            json.dump(self.installed_manifest, f, indent=2)

        # Create minimal config
        config = {
            "installation_mode": self.mode,
            "version": "1.6.0",
            "installed_date": time.strftime("%Y-%m-%d %H:%M:%S"),
            "agents_count": installed_count,
        }

        config_file = self.target_dir / "config.json"
        with open(config_file, "w") as f:
            json.dump(config, f, indent=2)

        print()
        print("✅ Installation complete!")
        print(f"   📦 Installed {installed_count} agents to .claude/agents/")

        if failed_agents:
            print(f"   ⚠️  Failed to install: {', '.join(failed_agents)}")

        print()
        print("🔄 Next Steps:")
        print("   1. Restart your AI assistant to load the agents")
        print("   2. Agents are now available in your project")
        print("   3. Use 'claude-installer list' to see installed agents")

        return installed_count > 0

    def install_with_framework(self) -> bool:
        """Install agents + essential framework tools."""
        print("🚀 Installing agents with essential framework...")

        # First install agents
        if not self.install_agents_only():
            return False

        # Then add framework essentials
        print("\n📋 Adding framework essentials...")

        essentials = [
            "CLAUDE-CORE.md",
            "tools/validation/validate-pipeline.py",
            "templates/feature-proposal.md",
        ]

        tools_dir = self.target_dir / "tools"
        templates_dir = self.target_dir / "templates"

        tools_dir.mkdir(exist_ok=True)
        templates_dir.mkdir(exist_ok=True)

        for essential in essentials:
            try:
                print(f"   📥 Downloading {essential}...")
                content = self.github_api.get_file(essential)

                if essential.startswith("tools/"):
                    target = tools_dir / Path(essential).name
                elif essential.startswith("templates/"):
                    target = templates_dir / Path(essential).name
                else:
                    target = self.target_dir / Path(essential).name

                target.write_bytes(content)
                print(f"   ✅ Added {essential}")

            except Exception as e:
                print(f"   ⚠️  Could not add {essential}: {e}")

        print("\n✅ Framework essentials installed!")
        return True

    def install_full_setup(self) -> bool:
        """Install complete AI-First SDLC framework."""
        print("🚀 Installing complete AI-First SDLC framework...")
        print("   This is equivalent to running setup-smart.py")

        # For now, delegate to existing setup-smart.py
        # In the future, we'll implement this directly
        setup_script = self.project_root / "setup-smart.py"

        if not setup_script.exists():
            print("   📥 Downloading setup-smart.py...")
            try:
                content = self.github_api.get_file("setup-smart.py")
                setup_script.write_bytes(content)
                setup_script.chmod(0o755)
            except Exception as e:
                print(f"   ❌ Could not download setup-smart.py: {e}")
                return False

        print("   🔄 Running full framework setup...")
        import subprocess

        try:
            result = subprocess.run(
                [
                    sys.executable,
                    str(setup_script),
                    "AI-assisted development with agents",
                    "--non-interactive",
                ],
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                print("   ✅ Full framework setup complete!")
                return True
            else:
                print(f"   ❌ Setup failed: {result.stderr}")
                return False

        except Exception as e:
            print(f"   ❌ Could not run setup: {e}")
            return False

    def list_installed_agents(self):
        """List currently installed agents."""
        manifest_file = self.target_dir / "agent-manifest.json"

        if not manifest_file.exists():
            print("No agents installed.")
            return

        with open(manifest_file) as f:
            manifest = json.load(f)

        if not manifest:
            print("No agents installed.")
            return

        print("Installed Agents:")
        print("=" * 50)

        for agent_name, info in manifest.items():
            category = info.get("category", "unknown")
            version = info.get("version", "1.0.0")
            date = info.get("installed_date", "unknown")
            print(f"  {agent_name:<25} {category:<15} v{version} ({date})")

    def install(self) -> bool:
        """Main installation method."""
        if not self.validate_environment():
            return False

        print("Claude AI Agent Installer")
        print(f"Mode: {self.mode} - {self.MODES[self.mode]}")
        print(f"Target: {self.target_dir}")
        print()

        if self.mode == "agents-only":
            return self.install_agents_only()
        elif self.mode == "with-framework":
            return self.install_with_framework()
        else:
            return self.install_full_setup()


def main():
    parser = argparse.ArgumentParser(
        description="Claude AI Agent Installer - DevOps Grade"
    )

    parser.add_argument(
        "--mode",
        choices=["agents-only", "with-framework", "full-setup"],
        default="agents-only",
        help="Installation mode",
    )

    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path.cwd(),
        help="Project root directory")

    parser.add_argument(
        "--list",
        action="store_true",
        help="List installed agents")

    args = parser.parse_args()

    installer = ClaudeInstaller(args.project_root, args.mode)

    if args.list:
        installer.list_installed_agents()
        return

    success = installer.install()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
