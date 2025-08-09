#!/usr/bin/env python3
"""Agent Installer for AI-First SDLC Framework

This tool installs specialized agents into user projects, managing:
- Automatic project analysis and agent recommendations
- Agent discovery and selection
- Version compatibility checking
- Dependency resolution
- Installation to appropriate directories
"""

import json
import shutil
import sys
import tempfile
import urllib.request
import zipfile
import time
from pathlib import Path
from typing import Dict, List, Optional
import click
import yaml
from rich.console import Console
from rich.prompt import Confirm, Prompt
from rich.table import Table
from rich.tree import Tree

# Import project analyzer and recommender
try:
    from project_analyzer import ProjectAnalyzer
    from agent_recommender import AgentRecommender

    ANALYSIS_AVAILABLE = True
except ImportError:
    ANALYSIS_AVAILABLE = False

console = Console()

# GitHub repository details
GITHUB_REPO = "SteveGJones/ai-first-sdlc-practices"
GITHUB_BRANCH = "main"
AGENTS_URL = (
    f"https://github.com/{GITHUB_REPO}/archive/refs/heads/"
    f"{GITHUB_BRANCH}.zip")

# Define agent tiers for deployment
AGENT_TIERS = {
    "universal": [
        "sdlc-enforcer",
        "solution-architect",
        "critical-goal-reviewer",
        "framework-validator",
        "github-integration-specialist",
    ],
    "language_specific": {
        "python": ["language-python-expert", "ai-test-engineer"],
        # Other language experts will be created as needed
    },
    "context_specific": {
        "api": ["integration-orchestrator", "devops-specialist"],
        "web": ["example-security-architect"],
        "ml": ["ai-solution-architect", "ai-test-engineer"],
        "microservices": ["integration-orchestrator", "devops-specialist"],
        "production": ["sre-specialist", "performance-engineer"],
        "compliance": ["compliance-auditor", "example-security-architect"],
    },
    "on_demand": [
        "agile-coach",
        "delivery-manager",
        "documentation-architect",
        "technical-writer",
        "prompt-engineer",
        "mcp-server-architect",
    ],
}


class AgentInstaller:
    """Manages installation of AI agents to user projects with tiered
    deployment."""

    def __init__(
        self,
        project_root: Path,
        agent_source: Optional[Path] = None,
        target_dir: Optional[Path] = None,
    ):
        self.project_root = project_root
        self.agent_source = agent_source

        # Always use .claude/agents as the standard location (with dot)
        if target_dir:
            self.claude_agents_dir = target_dir
        else:
            # Standard location for Claude agents
            self.claude_agents_dir = project_root / ".claude" / "agents"

        self.installed_agents_file = (
            self.claude_agents_dir.parent / "agent-manifest.json"
        )
        self.installed_agents = self._load_installed_agents()
        self._temp_dir = None

    def _download_agents(self) -> Path:
        """Download agents from GitHub repository."""
        console.print("[yellow]Downloading agents from GitHub...[/yellow]")

        # Create temporary directory
        self._temp_dir = tempfile.mkdtemp(prefix="ai-first-agents-")
        zip_path = Path(self._temp_dir) / "agents.zip"

        try:
            # Download the repository
            urllib.request.urlretrieve(AGENTS_URL, zip_path)

            # Extract the zip file
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(self._temp_dir)

            # Find the agents directory
            extracted_dir = (Path(self._temp_dir) /
                             f"ai-first-sdlc-practices-{GITHUB_BRANCH}")
            agents_dir = extracted_dir / "agents"

            if not agents_dir.exists():
                raise FileNotFoundError(
                    "Agents directory not found in downloaded repository"
                )

            console.print("[green]✓ Agents downloaded successfully[/green]")
            return agents_dir

        except Exception as e:
            console.print(f"[red]Error downloading agents: {e}[/red]")
            if self._temp_dir and Path(self._temp_dir).exists():
                shutil.rmtree(self._temp_dir)
            raise

    def _cleanup_temp(self):
        """Clean up temporary directory."""
        if self._temp_dir and Path(self._temp_dir).exists():
            shutil.rmtree(self._temp_dir)

    def _load_installed_agents(self) -> Dict[str, str]:
        """Load record of installed agents."""
        if self.installed_agents_file.exists():
            with open(self.installed_agents_file) as f:
                return json.load(f)
        return {}

    def _save_installed_agents(self):
        """Save record of installed agents."""
        with open(self.installed_agents_file, "w") as f:
            json.dump(self.installed_agents, f, indent=2)

    def _parse_agent_metadata(self, agent_path: Path) -> Dict:
        """Parse agent YAML frontmatter."""
        try:
            with open(agent_path, "r", encoding="utf-8") as f:
                content = f.read()

            if not content.startswith("---"):
                console.print(
                    (
                        f"[yellow]Warning: {agent_path.name} missing "
                        f"YAML frontmatter[/yellow]"
                    )
                )
                return None

            # Extract YAML frontmatter
            parts = content.split("---", 2)
            if len(parts) < 3:
                console.print(
                    (
                        f"[yellow]Warning: Invalid agent format in "
                        f"{agent_path.name}[/yellow]"
                    )
                )
                return None

            # Parse YAML with robust error handling
            try:
                metadata = yaml.safe_load(parts[1])
            except yaml.YAMLError:
                # Use the same robust fallback as discover_agents
                metadata = self._parse_basic_metadata(parts[1])

            if metadata:
                metadata["content"] = parts[2].strip()
                return metadata
            else:
                return None
        except Exception as e:
            console.print(f"[red]Error parsing {agent_path.name}: {e}[/red]")
            return None

    def _parse_basic_metadata(self, yaml_content: str) -> Dict:
        """Fallback parser for basic agent metadata when YAML parsing fails."""
        metadata = {}

        # Split into lines and parse basic fields
        lines = yaml_content.strip().split("\n")

        for line in lines:
            # Skip empty lines and comments
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            # Parse key: value pairs (only first colon)
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip()
                value = value.strip()

                # Only extract essential fields
                if key == "name":
                    metadata["name"] = value
                elif key == "description":
                    # Take only the first sentence for descriptions
                    metadata["description"] = value.split(
                        ".")[0] + "." if value else ""
                elif key == "version":
                    metadata["version"] = value
                elif key == "category":
                    metadata["category"] = value
                elif key == "priority":
                    metadata["priority"] = value

        # Ensure we have at least a name
        if "name" not in metadata and lines:
            # Use filename as fallback name
            metadata["name"] = "unknown-agent"

        return metadata if metadata else None

    def discover_agents(self) -> Dict[str, List[Path]]:
        """Discover all available agents organized by category."""
        # Download agents if no local source provided
        if self.agent_source is None:
            self.agent_source = self._download_agents()

        agents = {}

        for category_dir in self.agent_source.iterdir():
            if not category_dir.is_dir() or category_dir.name.startswith("."):
                continue

            category_agents = []
            for agent_file in category_dir.rglob("*.md"):
                # Read and parse the agent file
                try:
                    content = agent_file.read_text(encoding="utf-8")
                    if not content.startswith("---"):
                        continue

                    # Extract YAML frontmatter with robust error handling
                    parts = content.split("---", 2)
                    if len(parts) >= 3:
                        try:
                            metadata = yaml.safe_load(parts[1])
                        except yaml.YAMLError:
                            # Fallback: parse basic fields manually
                            metadata = self._parse_basic_metadata(parts[1])

                        if metadata:
                            category_agents.append(
                                {"path": agent_file, "metadata": metadata}
                            )
                except Exception:
                    continue

            if category_agents:
                agents[category_dir.name] = category_agents
        return agents

    def check_dependencies(self, agent_metadata: Dict) -> List[str]:
        """Check if agent dependencies are satisfied."""
        missing = []

        if "dependencies" in agent_metadata:
            for dep in agent_metadata["dependencies"]:
                if dep not in self.installed_agents:
                    missing.append(dep)

        return missing

    def install_agent(
        self, agent_path: Path, metadata: Dict, force: bool = False
    ) -> bool:
        """Install a single agent."""
        agent_name = metadata.get("name", agent_path.stem)

        # Check if already installed
        if agent_name in self.installed_agents and not force:
            console.print(
                (
                    f"[yellow]Agent '{agent_name}' already installed "
                    f"(v{self.installed_agents[agent_name]})[/yellow]"
                )
            )
            return False

        # Check dependencies
        missing_deps = self.check_dependencies(metadata)
        if missing_deps:
            console.print(
                (
                    f"[red]Missing dependencies for {agent_name}: "
                    f"{', '.join(missing_deps)}[/red]"
                )
            )
            return False

        # Install flat into .claude/agents without category folders
        self.claude_agents_dir.mkdir(parents=True, exist_ok=True)

        # Copy agent file directly to .claude/agents
        target_path = self.claude_agents_dir / agent_path.name

        # Debug: Check source file exists
        if not agent_path.exists():
            console.print(
                f"[red]Error: Source file does not exist: {agent_path}[/red]")
            return False

        # Actually copy the file
        try:
            shutil.copy2(agent_path, target_path)
            # Verify the copy succeeded
            if not target_path.exists():
                console.print(
                    (
                        f"[red]Error: Failed to copy {agent_path.name} "
                        f"to {target_path}[/red]"
                    )
                )
                return False
        except Exception as e:
            console.print(f"[red]Error copying {agent_path.name}: {e}[/red]")
            return False

        # Record installation
        self.installed_agents[agent_name] = metadata.get("version", "1.0.0")
        self._save_installed_agents()

        console.print(
            (
                f"[green]✓ Installed {agent_name} "
                f"v{metadata.get('version', '1.0.0')}[/green]"
            )
        )
        return True

    def install_core_agents(self):
        """Install all core agents required for every project."""
        console.print("\n[bold]Installing Core Agents[/bold]")

        # Ensure we have agents downloaded
        if self.agent_source is None:
            self.agent_source = self._download_agents()

        core_dir = self.agent_source / "core"
        if not core_dir.exists():
            console.print(
                f"[red]Core agents directory not found at: {core_dir}[/red]")
            return

        console.print(f"[dim]Looking for agents in: {core_dir}[/dim]")

        installed_count = 0
        found_count = 0
        for agent_file in core_dir.rglob("*.md"):
            found_count += 1
            console.print(f"[dim]Processing: {agent_file.name}[/dim]")
            metadata = self._parse_agent_metadata(agent_file)
            if metadata and self.install_agent(agent_file, metadata):
                installed_count += 1

        console.print(
            (
                f"\n[green]Found {found_count} agents, installed "
                f"{installed_count} core agents[/green]"
            )
        )

    def install_language_agents(self, languages: List[str]):
        """Install language-specific agents."""
        console.print(
            f"\n[bold]Installing agents for: {', '.join(languages)}[/bold]")

        languages_dir = self.agent_source / "languages"
        installed_count = 0

        for lang in languages:
            lang_dir = languages_dir / lang.lower()
            if not lang_dir.exists():
                console.print(f"[yellow]No agents found for {lang}[/yellow]")
                continue

            for agent_file in lang_dir.glob("*.md"):
                try:
                    metadata = self._parse_agent_metadata(agent_file)
                    if metadata and self.install_agent(agent_file, metadata):
                        installed_count += 1
                except Exception as e:
                    console.print(
                        f"[red]Failed to install {agent_file.name}: {e}[/red]"
                    )

        console.print(
            (
                f"\n[green]Installed {installed_count} "
                f"language-specific agents[/green]"
            )
        )

    def install_tiered_agents(
        self, project_context: Dict = None
    ) -> Dict[str, List[str]]:
        """Install agents based on tiered deployment strategy."""
        installed = {"universal": [], "context_aware": [], "on_demand": []}

        # Tier 1: Always install universal agents
        console.print(
            "\n[bold]Installing Tier 1: Universal Core Agents[/bold]")
        for agent_name in AGENT_TIERS["universal"]:
            if self._install_by_name(agent_name):
                installed["universal"].append(agent_name)
                console.print(f"  ✓ {agent_name}")

        # Tier 2: Install context-aware agents based on project analysis
        if project_context:
            console.print(
                "\n[bold]Installing Tier 2: Context-Aware Agents[/bold]")

            # Language-specific agents
            detected_languages = project_context.get("languages", [])
            for lang in detected_languages:
                if lang.lower() in AGENT_TIERS["language_specific"]:
                    for agent_name in AGENT_TIERS["language_specific"][lang.lower(
                    )]:
                        if self._install_by_name(agent_name):
                            installed["context_aware"].append(agent_name)
                            console.print(f"  ✓ {agent_name} (for {lang})")

            # Context-specific agents
            if project_context.get("has_api"):
                for agent_name in AGENT_TIERS["context_specific"]["api"]:
                    if self._install_by_name(agent_name):
                        installed["context_aware"].append(agent_name)
                        console.print(f"  ✓ {agent_name} (API support)")

            if project_context.get("is_web"):
                for agent_name in AGENT_TIERS["context_specific"]["web"]:
                    if self._install_by_name(agent_name):
                        installed["context_aware"].append(agent_name)
                        console.print(f"  ✓ {agent_name} (Web support)")

            if project_context.get("has_ml"):
                for agent_name in AGENT_TIERS["context_specific"]["ml"]:
                    if self._install_by_name(agent_name):
                        installed["context_aware"].append(agent_name)
                        console.print(f"  ✓ {agent_name} (ML support)")

            if project_context.get("is_production"):
                for agent_name in AGENT_TIERS["context_specific"]["production"]:
                    if self._install_by_name(agent_name):
                        installed["context_aware"].append(agent_name)
                        console.print(f"  ✓ {agent_name} (Production)")

            if project_context.get("requires_compliance"):
                for agent_name in AGENT_TIERS["context_specific"]["compliance"]:
                    if self._install_by_name(agent_name):
                        installed["context_aware"].append(agent_name)
                        console.print(f"  ✓ {agent_name} (Compliance)")

        # Tier 3: Show available on-demand agents
        console.print("\n[bold]Tier 3: On-Demand Agents Available[/bold]")
        console.print("These agents can be installed when needed:")
        for agent_name in AGENT_TIERS["on_demand"]:
            console.print(f"  • {agent_name}")

        return installed

    def smart_install(self) -> Dict[str, List[str]]:
        """Smart installation with project analysis and tiered deployment."""
        # Analyze project if available
        project_context = {}
        if ANALYSIS_AVAILABLE:
            try:
                analyzer = ProjectAnalyzer(self.project_root)
                analysis = analyzer.analyze()

                project_context = {
                    "languages": analysis.get("languages", []),
                    "has_api": any(
                        f in str(analysis) for f in ["api", "REST", "GraphQL"]
                    ),
                    "is_web": any(
                        f in str(analysis) for f in ["web", "frontend", "html"]
                    ),
                    "has_ml": any(f in str(analysis) for f in ["ml", "ai", "model"]),
                    "is_production": self.project_root.name
                    not in ["test", "demo", "example"],
                    "requires_compliance": any(
                        f in str(analysis) for f in ["compliance", "audit", "security"]
                    ),
                }
            except Exception as e:
                console.print(
                    f"[yellow]Could not analyze project: {e}[/yellow]")

        # Install based on tiers
        return self.install_tiered_agents(project_context)

    def show_available_agents(self):
        """Display all available agents in a tree structure."""
        agents = self.discover_agents()

        tree = Tree("[bold]Available Agents[/bold]")

        for category, category_agents in sorted(agents.items()):
            category_branch = tree.add(f"[blue]{category}[/blue]")

            for agent_info in category_agents:
                metadata = agent_info.get("metadata", {})
                name = metadata.get("name", agent_info["path"].stem)
                version = metadata.get("version", "1.0.0")
                installed = " [green]✓[/green]" if name in self.installed_agents else ""

                agent_branch = category_branch.add(
                    f"{name} v{version}{installed}")

                if "description" in metadata:
                    desc = metadata["description"]
                    # Handle multiline descriptions - take first line only
                    if isinstance(desc, str):
                        desc = desc.split("\\n")[0].strip()
                        # Limit length for display
                        if len(desc) > 80:
                            desc = desc[:77] + "..."
                    agent_branch.add(f"[dim]{desc}[/dim]")

        console.print(tree)

    def analyze_and_recommend(self) -> Optional[Dict]:
        """Analyze project and get agent recommendations."""
        if not ANALYSIS_AVAILABLE:
            return None

        console.print("\n[bold]Analyzing your project...[/bold]")

        # Run project analysis
        analyzer = ProjectAnalyzer(self.project_root)
        analysis = analyzer.analyze()

        # Get project objectives
        console.print("\n[bold]Project Analysis Complete![/bold]")
        console.print(analyzer.get_summary())

        objectives = Prompt.ask(
            "\n[bold]What are your main project objectives?[/bold]",
            default="Build a high-quality, maintainable application",
        )

        # Get recommendations
        recommender = AgentRecommender()
        recommendations = recommender.recommend(analysis, objectives)

        return {
            "analysis": analysis,
            "objectives": objectives,
            "recommendations": recommendations,
        }

    def install_recommended_agents(
            self, recommendations: Dict[str, List[Dict]]):
        """Install agents based on recommendations."""
        # Install essential agents automatically
        console.print("\n[bold red]Installing Essential Agents[/bold red]")
        for agent in recommendations.get("essential", []):
            console.print(f"  Installing {agent['name']}: {agent['reason']}")
            # Find and install the agent
            self._install_by_name(agent["name"])

        # Ask about strongly recommended
        if recommendations.get("strongly_recommended"):
            console.print(
                "\n[bold yellow]Strongly Recommended Agents[/bold yellow]")
            table = Table(show_header=True)
            table.add_column("Agent", style="yellow")
            table.add_column("Reason")

            for agent in recommendations["strongly_recommended"]:
                table.add_row(agent["name"], agent["reason"])

            console.print(table)

            if Confirm.ask(
                "\nInstall all strongly recommended agents?",
                    default=True):
                for agent in recommendations["strongly_recommended"]:
                    self._install_by_name(agent["name"])

        # Show recommended agents
        if recommendations.get("recommended"):
            console.print("\n[bold green]Recommended Agents[/bold green]")

            for agent in recommendations["recommended"]:
                if Confirm.ask(
                    f"Install {agent['name']}? ({agent['reason']})",
                    default=False,
                ):
                    self._install_by_name(agent["name"])

    def _install_by_name(self, agent_name: str) -> bool:
        """Install a specific agent by name."""
        agents = self.discover_agents()

        for category, category_agents in agents.items():
            for agent_info in category_agents:
                if agent_info["metadata"]["name"] == agent_name:
                    return self.install_agent(
                        agent_info["path"], agent_info["metadata"]
                    )

        console.print(
            f"[yellow]Agent '{agent_name}' not found in repository[/yellow]")
        return False

    def interactive_install(self):
        """Interactive agent installation wizard with smart recommendations."""
        # Try to analyze and recommend first
        recommendation_data = None  # This would be set by analysis function

        if recommendation_data:
            # Show recommendations and install
            console.print("\n[bold]Agent Recommendations[/bold]")
            console.print(
                (
                    "Based on your project analysis, here are the "
                    "recommended agents:\n"
                )
            )

            self.install_recommended_agents(
                recommendation_data["recommendations"])

            # Ask if they want to see all available agents
            if Confirm.ask(
                "\nWould you like to see all available agents?", default=False
            ):
                self.show_available_agents()
                self._install_optional_agents()
        else:
            # Fallback to original behavior
            self.show_available_agents()

            # Install core agents
            if Confirm.ask("\nInstall all core agents?", default=True):
                self.install_core_agents()

            # Language selection
            console.print("\n[bold]Select Programming Languages[/bold]")
            console.print("Available: Python, JavaScript, Go, Java, Rust")

            languages = Prompt.ask(
                "Enter languages (comma-separated)", default="Python"
            ).split(",")

            languages = [lang.strip() for lang in languages if lang.strip()]
            if languages:
                self.install_language_agents(languages)

            # Optional agents
            if Confirm.ask(
                "\nWould you like to install additional specialized agents?"
            ):
                self._install_optional_agents()

    def _install_optional_agents(self):
        """Install optional agents based on user selection."""
        agents = self.discover_agents()

        # Categories to offer (excluding core and languages)
        optional_categories = [
            cat for cat in agents.keys() if cat not in ["core", "languages"]
        ]

        for category in optional_categories:
            console.print(
                f"\n[bold]{category.replace('_', ' ').title()} Agents[/bold]")

            table = Table(show_header=True)
            table.add_column("Agent", style="cyan")
            table.add_column("Description")
            table.add_column("Status", style="green")

            for agent_info in agents[category]:
                metadata = agent_info.get("metadata", {})
                status = (
                    "Installed"
                    if metadata["name"] in self.installed_agents
                    else "Available"
                )
                table.add_row(
                    metadata["name"],
                    metadata.get("description", "No description"),
                    status,
                )

            console.print(table)

            if Confirm.ask(f"Install agents from {category}?"):
                agent_names = Prompt.ask("Enter agent names (comma-separated)")
                for name in agent_names.split(","):
                    name = name.strip()
                    # Find and install the agent
                    for agent_info in agents[category]:
                        if agent_info["metadata"]["name"] == name:
                            self.install_agent(
                                agent_info["path"], agent_info["metadata"]
                            )
                            break


@click.command()
@click.option(
    "--project-root",
    type=click.Path(exists=True),
    default=".",
    help="Project root directory",
)
@click.option(
    "--agent-source",
    type=click.Path(exists=True),
    default=None,
    help="Agent source directory",
)
@click.option(
    "--target",
    type=click.Path(),
    default=None,
    help="Target directory for agents (default: .claude/agents)",
)
@click.option("--core-only", is_flag=True, help="Install only core agents")
@click.option(
    "--languages", "-l", multiple=True, help="Languages to install agents for"
)
@click.option("--list", "list_agents", is_flag=True,
              help="List available agents")
@click.option("--install", "-i", multiple=True,
              help="Specific agents to install")
@click.option(
    "--analyze", is_flag=True, help="Analyze project and show recommendations"
)
@click.option("--objectives", help="Project objectives for recommendations")
@click.option(
    "--recommend-only",
    is_flag=True,
    help="Show recommendations without installing",
)
@click.option("--tiered", is_flag=True, help="Use tiered deployment strategy")
def main(
    project_root,
    agent_source,
    target,
    core_only,
    languages,
    list_agents,
    install,
    analyze,
    objectives,
    recommend_only,
    tiered,
):
    """Install AI agents for the AI-First SDLC framework."""

    project_path = Path(project_root).resolve()

    # Handle agent source
    agent_source_path = None
    if agent_source:
        agent_source_path = Path(agent_source).resolve()
        if not agent_source_path.exists():
            console.print(
                (
                    f"[red]Agent source directory not found at: "
                    f"{agent_source_path}[/red]"
                )
            )
            console.print(
                "[yellow]Will download agents from GitHub instead...[/yellow]"
            )
            agent_source_path = None

    # Handle target directory
    target_path = Path(target) if target else None

    installer = AgentInstaller(project_path, agent_source_path, target_path)

    # Handle analysis and recommendations
    if analyze or recommend_only:
        if not ANALYSIS_AVAILABLE:
            console.print(
                ("[red]Project analysis not available. "
                 "Missing dependencies.[/red]"))
            sys.exit(1)

        recommendation_data = None  # This would be set by analysis function
        if recommendation_data:
            # Display recommendations
            from agent_recommender import display_recommendations

            display_recommendations(
                recommendation_data["recommendations"],
                recommendation_data["analysis"],
            )

            if not recommend_only:
                if Confirm.ask(
                    "\nProceed with recommended installation?", default=True
                ):
                    installer.install_recommended_agents(
                        recommendation_data["recommendations"]
                    )
        return

    if list_agents:
        installer.show_available_agents()
        return
    elif tiered:
        # Use tiered deployment strategy
        installer.smart_install()
    elif core_only:
        installer.install_core_agents()
    elif languages:
        installer.install_language_agents(list(languages))
    elif install:
        # Install specific agents
        agents = installer.discover_agents()
        for agent_name in install:
            found = False
            for category, category_agents in agents.items():
                for agent_info in category_agents:
                    if agent_info["metadata"]["name"] == agent_name:
                        installer.install_agent(
                            agent_info["path"], agent_info["metadata"]
                        )
                        found = True
                        break
                if found:
                    break
            if not found:
                console.print(f"[red]Agent '{agent_name}' not found![/red]")
    else:
        # Interactive mode
        installer.interactive_install()

    console.print("\n[bold green]Agent installation complete![/bold green]")
    console.print(f"Agents installed to: {installer.claude_agents_dir}")

    # List what was actually installed
    if installer.claude_agents_dir.exists():
        installed_files = list(installer.claude_agents_dir.glob("*.md"))
        if installed_files:
            console.print(
                (
                    f"\n[green]Successfully installed "
                    f"{len(installed_files)} agent(s):[/green]"
                )
            )
            for f in installed_files[:5]:  # Show first 5
                console.print(f"  - {f.name}")
            if len(installed_files) > 5:
                console.print(f"  ... and {len(installed_files) - 5} more")
        else:
            console.print(
                (
                    "\n[red]WARNING: No agent files found in "
                    "installation directory![/red]"
                )
            )
    else:
        console.print(
            "\n[red]WARNING: Installation directory does not exist![/red]")

    # Important notes
    console.print("\n[bold yellow]⚠️  Important Notes[/bold yellow]")

    # Determine which directory structure we're using
    if ".sdlc" in str(installer.claude_agents_dir):
        console.print(
            (f"\n1. Agents have been installed to: "
             f"{installer.claude_agents_dir}"))
        console.print("   (Using organized .sdlc structure)")
    else:
        console.print(
            (f"\n1. Agents have been installed to: "
             f"{installer.claude_agents_dir}"))

    console.print(
        ("2. [bold red]RESTART YOUR AI ASSISTANT[/bold red] "
         "to activate the agents!"))
    console.print("\nFor system-wide availability, you can also copy to:")
    console.print(
        (f"   [cyan]cp -r {installer.claude_agents_dir}/* "
         f"~/.claude/agents/[/cyan]"))
    console.print(
        "\nNote: Project-specific agents are not automatically available")

    # Clean up temporary directory after all operations are complete
    installer._cleanup_temp()


if __name__ == "__main__":
    try:
        main()
    finally:
        # Clean up any temporary directories
        for path in Path(tempfile.gettempdir()).glob("ai-first-agents-*"):
            if (
                path.is_dir() and path.stat().st_mtime < time.time() - 3600
            ):  # Older than 1 hour
                try:
                    shutil.rmtree(path)
                except Exception:
                    pass
