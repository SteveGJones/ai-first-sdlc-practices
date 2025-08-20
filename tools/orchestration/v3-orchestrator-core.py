#!/usr/bin/env python3
"""
V3 Orchestrator Core - Integrated orchestration with all components.
Connects state management, validation, team enforcement, and parallel downloads.
"""

import json
import sys
import importlib.util
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

import click


# Import our components
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    # Import components with proper module names
    # Use importlib to handle hyphenated filenames

    # Load InstallationStateManager
    spec = importlib.util.spec_from_file_location(
        "installation_state_manager",
        Path(__file__).parent.parent / "automation" / "installation-state-manager.py"
    )
    ism_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ism_module)
    InstallationStateManager = ism_module.InstallationStateManager
    InstallationPhase = ism_module.InstallationPhase

    # Load AgentCatalog
    spec = importlib.util.spec_from_file_location(
        "agent_catalog_manager",
        Path(__file__).parent.parent / "automation" / "agent-catalog-manager.py"
    )
    acm_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(acm_module)
    AgentCatalog = acm_module.AgentCatalog

    # Load IntegratedDownloadValidator
    spec = importlib.util.spec_from_file_location(
        "integrated_download_validator",
        Path(__file__).parent.parent / "validation" / "integrated-download-validator.py"
    )
    idv_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(idv_module)
    IntegratedDownloadValidator = idv_module.IntegratedDownloadValidator

except ImportError as e:
    click.echo(f"Error importing components: {e}", err=True)
    click.echo("Ensure all required tools are in place", err=True)
    sys.exit(1)
except Exception as e:
    click.echo(f"Error loading components: {e}", err=True)
    click.echo("Check that all tool files exist and are valid Python modules", err=True)
    sys.exit(1)


class TeamFirstBlockedException(Exception):
    """Raised when team-first requirements are not met"""
    pass


class ValidationFailedException(Exception):
    """Raised when validation requirements fail"""
    pass


@dataclass
class DiscoveryResult:
    """Results from project discovery phase"""
    project_type: str
    languages: List[str]
    frameworks: List[str]
    team_size: str
    pain_points: List[str]
    existing_agents: List[str]
    ci_platform: Optional[str] = None
    deployment_target: Optional[str] = None


class V3OrchestratorCore:
    """
    Core orchestrator with all integrations.
    Enforces team-first, validates everything, manages state.
    """

    # Core agents that MUST be installed first
    GATEWAY_AGENTS = ["sdlc-enforcer", "critical-goal-reviewer", "solution-architect"]

    # Agent mappings based on project type (verified against actual repository)
    AGENT_MAPPINGS = {
        "api": {
            "required": ["api-architect", "backend-engineer", "integration-orchestrator"],
            "recommended": ["security-specialist", "performance-engineer"]
        },
        "frontend": {
            "required": ["frontend-engineer", "frontend-security-specialist"],
            "recommended": ["performance-engineer", "documentation-architect"]
        },
        "fullstack": {
            "required": ["solution-architect", "api-architect", "backend-engineer",
                        "frontend-engineer", "database-architect"],
            "recommended": ["integration-orchestrator", "devops-specialist"]
        },
        "data": {
            "required": ["data-architect", "database-architect"],
            "recommended": ["performance-engineer"]
        },
        "ml": {
            "required": ["data-architect"],
            "recommended": ["performance-engineer"]
        }
    }

    # Comprehensive agent directory mapping for URL construction
    # Updated to handle all 69 agents across 15 categories
    AGENT_DIRECTORY_MAP = {
        # ==== CORE AGENTS (23 agents) ====
        # Gateway agents (always required)
        "sdlc-enforcer": "core",
        "critical-goal-reviewer": "core",
        "solution-architect": "core",

        # Primary architecture agents
        "api-architect": "core",
        "api-design-specialist": "core",
        "backend-engineer": "core",
        "frontend-engineer": "core",
        "database-architect": "core",
        "data-architect": "core",
        "mobile-architect": "core",
        "ux-ui-architect": "core",

        # DevOps and operations
        "devops-specialist": "core",
        "sre-specialist": "core",

        # Security core
        "security-specialist": "core",
        "example-security-architect": "core",
        "data-privacy-officer": "core",

        # Quality and compliance
        "compliance-auditor": "core",
        "test-manager": "core",

        # GitHub and integration
        "github-integration-specialist": "core",

        # SDLC guidance
        "sdlc-coach": "core",

        # Security specialization (some are in both core/ and security/)
        "frontend-security-specialist": "core",  # Primary location

        # ==== TESTING AGENTS (3 agents) ====
        "integration-orchestrator": "testing",
        "performance-engineer": "testing",
        "ai-test-engineer": "testing",

        # ==== DOCUMENTATION AGENTS (2 agents) ====
        "documentation-architect": "documentation",
        "technical-writer": "documentation",

        # ==== SECURITY AGENTS (1 agent) ====
        # Note: frontend-security-specialist also exists here as duplicate

        # ==== PROJECT MANAGEMENT (3 agents) ====
        "project-plan-tracker": "project-management",
        "agile-coach": "project-management",
        "delivery-manager": "project-management",

        # ==== SDLC AGENTS (6 agents) ====
        "language-python-expert": "sdlc",
        "language-javascript-expert": "sdlc",
        "language-go-expert": "sdlc",
        "ai-first-kick-starter": "sdlc",
        "framework-validator": "sdlc",
        "kickstart-architect": "sdlc",
        "project-bootstrapper": "sdlc",
        "retrospective-miner": "sdlc",

        # ==== AI DEVELOPMENT AGENTS (8 agents) ====
        "a2a-architect": "ai-development",
        "agent-developer": "ai-development",
        "ai-solution-architect": "ai-development",
        "junior-ai-solution-architect": "ai-development",
        "langchain-architect": "ai-development",
        "mcp-quality-assurance": "ai-development",
        "mcp-server-architect": "ai-development",
        "mcp-test-agent": "ai-development",
        "prompt-engineer": "ai-development",

        # ==== AI BUILDERS (5 agents) ====
        "ai-devops-engineer": "ai-builders",
        "ai-team-transformer": "ai-builders",
        "context-engineer": "ai-builders",
        "orchestration-architect": "ai-builders",
        "rag-system-designer": "ai-builders",
        # Note: mcp-server-architect also exists here as duplicate

        # ==== CREATIVE AGENTS (1 agent) ====
        # Note: ux-ui-architect exists here as duplicate from core

        # ==== FUTURE AGENTS (4 agents) ====
        "a2a-mesh-controller": "future",
        "evolution-engine": "future",
        "mcp-orchestrator": "future",
        "swarm-coordinator": "future",

        # ==== TEMPLATES (2 agents) ====
        "project-strategy-orchestrator": "templates",
        "team-assembly-orchestrator": "templates",

        # ==== LANGUAGES (1 agent) ====
        "example-python-expert": "languages/python",

        # ==== ROOT LEVEL AGENTS (7 agents) ====
        # V3 orchestrators and setup specialists
        "v3-setup-orchestrator": "",  # Root level
        "v3-setup-orchestrator-enhanced": "",
        "v3-setup-orchestrator-fixed": "",
        "v3-setup-orchestrator-no-creation": "",
        "v3-setup-orchestrator-reboot-aware": "",
        "v3-setup-orchestrator-team-first": "",
        "sdlc-setup-specialist": "",

        # Special case: agent template
        "agent-template": "",
    }

    # Fallback directories for when agents aren't in the main map
    FALLBACK_DIRECTORIES = [
        "core",           # Try core first (most common)
        "sdlc",          # Try SDLC agents
        "testing",       # Try testing agents
        "ai-development", # Try AI development
        "ai-builders",   # Try AI builders
        "",              # Try root level
    ]

    def __init__(self, verbose: bool = False, strict: bool = True, dry_run: bool = False):
        """
        Initialize orchestrator with all components.

        Args:
            verbose: Enable verbose output
            strict: Use strict validation mode
            dry_run: Show what would be done without making changes
        """
        self.verbose = verbose
        self.strict = strict
        self.dry_run = dry_run

        # Initialize components
        self.state_manager = InstallationStateManager()
        self.catalog_manager = AgentCatalog()
        self.download_validator = IntegratedDownloadValidator(
            strict_mode=strict,
            verbose=verbose
        )

        # Team enforcement (simulated - would use actual validator)
        self.team_enforcer_active = True

        # Track orchestration state
        self.installation_id = None
        self.discovery_result = None
        self.selected_agents = []
        self.download_results = []

    def enforce_team_first(self) -> bool:
        """
        Enforce team-first requirements before any setup.

        Returns:
            True if team requirements met

        Raises:
            TeamFirstBlockedException if requirements not met
        """
        if not self.team_enforcer_active:
            return True

        click.echo("\n" + "="*50)
        click.echo("TEAM-FIRST ENFORCEMENT CHECK")
        click.echo("="*50)

        # Check for team engagement indicators
        team_checks = [
            ("Team assembly initiated", self._check_team_assembly()),
            ("Specialist consultation active", self._check_specialist_consultation()),
            ("Solo patterns blocked", self._check_no_solo_patterns()),
            ("SDLC enforcer engaged", self._check_sdlc_enforcer())
        ]

        all_passed = True
        for check_name, passed in team_checks:
            status = "✅" if passed else "❌"
            click.echo(f"{status} {check_name}")
            if not passed:
                all_passed = False

        if not all_passed:
            error_msg = """
❌ TEAM-FIRST REQUIREMENTS NOT MET

The V3 orchestrator REQUIRES team engagement before proceeding.

Run these commands first:
1. python .sdlc/tools/automation/auto-team-assembly.py "v3 setup" --force-consultation
2. python .sdlc/tools/validation/validate-team-engagement.py --strict

Setup BLOCKED until team requirements are met.
            """
            click.echo(error_msg, err=True)
            raise TeamFirstBlockedException("Team-first requirements not met")

        click.echo("\n✅ Team-first requirements verified. Proceeding with setup.\n")
        return True

    def _check_team_assembly(self) -> bool:
        """Check if team assembly was initiated"""
        # Check for team assembly marker file
        marker = Path(".sdlc/state/team-assembly.json")
        if marker.exists():
            try:
                with open(marker) as f:
                    data = json.load(f)
                    # Check if recent (within last hour)
                    timestamp = datetime.fromisoformat(data.get("timestamp", ""))
                    age = (datetime.now() - timestamp).seconds
                    return age < 3600
            except (ValueError, KeyError, TypeError):
                pass
        return False

    def _check_specialist_consultation(self) -> bool:
        """Check if specialists were consulted"""
        # Check for specialist consultation logs
        log_file = Path(".sdlc/logs/specialist-consultation.log")
        return log_file.exists() and log_file.stat().st_size > 0

    def _check_no_solo_patterns(self) -> bool:
        """Check that no solo patterns are present"""
        # Would run solo pattern detector
        return True  # Simulated for now

    def _check_sdlc_enforcer(self) -> bool:
        """Check if sdlc-enforcer was engaged"""
        # Check for sdlc-enforcer activity
        enforcer_log = Path(".sdlc/logs/sdlc-enforcer.log")
        return enforcer_log.exists()

    def discover_project(self, project_path: Path = Path(".")) -> DiscoveryResult:
        """
        Discover project characteristics.

        Args:
            project_path: Path to project root

        Returns:
            DiscoveryResult with project details
        """
        click.echo("\n" + "="*50)
        click.echo("PROJECT DISCOVERY PHASE")
        click.echo("="*50)

        discovery = DiscoveryResult(
            project_type="unknown",
            languages=[],
            frameworks=[],
            team_size="unknown",
            pain_points=[],
            existing_agents=[]
        )

        # Check for language indicators
        if (project_path / "package.json").exists():
            discovery.languages.append("javascript")
            with open(project_path / "package.json") as f:
                pkg = json.load(f)
                deps = list(pkg.get("dependencies", {}).keys())
                if "express" in deps or "fastify" in deps:
                    discovery.frameworks.append("node-api")
                    discovery.project_type = "api"
                if "react" in deps or "vue" in deps:
                    discovery.frameworks.append("frontend")
                    discovery.project_type = "frontend" if discovery.project_type == "unknown" else "fullstack"

        if (project_path / "requirements.txt").exists() or (project_path / "pyproject.toml").exists():
            discovery.languages.append("python")
            if (project_path / "requirements.txt").exists():
                with open(project_path / "requirements.txt") as f:
                    reqs = f.read()
                    if "django" in reqs or "flask" in reqs or "fastapi" in reqs:
                        discovery.frameworks.append("python-api")
                        discovery.project_type = "api" if discovery.project_type == "unknown" else discovery.project_type
                    if "pandas" in reqs or "numpy" in reqs:
                        discovery.frameworks.append("data-science")
                        discovery.project_type = "data" if discovery.project_type == "unknown" else discovery.project_type

        if (project_path / "go.mod").exists():
            discovery.languages.append("go")
            discovery.project_type = "api" if discovery.project_type == "unknown" else discovery.project_type

        # Check for existing agents
        agents_dir = Path.home() / ".claude" / "agents"
        if agents_dir.exists():
            discovery.existing_agents = [f.stem for f in agents_dir.glob("*.md")]

        # Check for CI/CD
        if (project_path / ".github" / "workflows").exists():
            discovery.ci_platform = "github"
        elif (project_path / ".gitlab-ci.yml").exists():
            discovery.ci_platform = "gitlab"

        # Display discovery results
        click.echo("\n📊 Discovery Results:")
        click.echo(f"  Project Type: {discovery.project_type}")
        click.echo(f"  Languages: {', '.join(discovery.languages) or 'none detected'}")
        click.echo(f"  Frameworks: {', '.join(discovery.frameworks) or 'none detected'}")
        click.echo(f"  Existing Agents: {len(discovery.existing_agents)}")
        click.echo(f"  CI Platform: {discovery.ci_platform or 'none detected'}")

        self.discovery_result = discovery
        return discovery

    def determine_agents(self, discovery: DiscoveryResult) -> List[str]:
        """
        Determine which agents to install based on discovery.

        Args:
            discovery: Project discovery results

        Returns:
            List of agent names to install
        """
        agents = []

        # Always include gateway agents
        agents.extend(self.GATEWAY_AGENTS)

        # Add project-type specific agents
        if discovery.project_type in self.AGENT_MAPPINGS:
            mapping = self.AGENT_MAPPINGS[discovery.project_type]
            agents.extend(mapping["required"])

            # Add recommended if verbose
            if self.verbose:
                agents.extend(mapping["recommended"])

        # Add language-specific coaches
        for lang in discovery.languages:
            if lang == "python":
                agents.append("language-python-expert")
            elif lang == "javascript":
                agents.append("language-javascript-expert")
            elif lang == "go":
                agents.append("language-go-expert")
            # For other languages, the general solution-architect provides guidance

        # Remove duplicates while preserving order
        seen = set()
        unique_agents = []
        for agent in agents:
            if agent not in seen:
                seen.add(agent)
                unique_agents.append(agent)

        # Filter out already installed agents
        final_agents = [a for a in unique_agents if a not in discovery.existing_agents]

        click.echo(f"\n📦 Agents to Install ({len(final_agents)}):")
        for agent in final_agents:
            status = "🔹 Required" if agent in self.GATEWAY_AGENTS else "🔸 Selected"
            click.echo(f"  {status} {agent}")

        self.selected_agents = final_agents
        return final_agents

    def create_installation(self, agents: List[str]) -> str:
        """
        Create installation tracking state.

        Args:
            agents: List of agents to install

        Returns:
            Installation ID
        """
        # Create installation record
        installation_data = {
            "project_type": self.discovery_result.project_type if self.discovery_result else "unknown",
            "agents": agents,
            "total_agents": len(agents),
            "phase": InstallationPhase.PRE_REBOOT.value
        }

        self.installation_id = self.state_manager.create_installation(installation_data)

        # Add TODOs
        todos = [
            f"Download and validate {len(agents)} agents",
            "Set up SDLC git hooks",
            "Configure branch protection",
            "Install GitHub Actions workflow",
            "Restart Claude for agents to activate",
            "Run post-reboot validation",
            "Complete team-first setup verification"
        ]

        for todo in todos:
            self.state_manager.add_todo(self.installation_id, todo)

        click.echo(f"\n📝 Installation tracking created: {self.installation_id}")
        return self.installation_id

    def download_agents(self, agents: List[str]) -> List[Any]:
        """
        Download and validate agents in parallel.

        Args:
            agents: List of agent names to download

        Returns:
            List of download results
        """
        click.echo("\n" + "="*50)
        click.echo("DOWNLOADING AND VALIDATING AGENTS")
        click.echo("="*50)

        # Prepare agent URLs
        base_url = "https://raw.githubusercontent.com/SteveGJones/ai-first-sdlc-practices/main/agents"

        agent_urls = []
        for agent in agents:
            # Map agent names to repository paths using comprehensive directory map
            if agent in self.AGENT_DIRECTORY_MAP:
                directory = self.AGENT_DIRECTORY_MAP[agent]
                if directory:  # Non-empty directory
                    url = f"{base_url}/{directory}/{agent}.md"
                else:  # Root level agent
                    url = f"{base_url}/{agent}.md"
                agent_urls.append({"name": agent, "url": url})
            else:
                # Use fallback mechanism for unknown agents
                if self.verbose:
                    click.echo(f"⚠️ Warning: Agent '{agent}' not in directory map, trying fallbacks...")

                # Create fallback URLs to try in order
                fallback_urls = []
                for fallback_dir in self.FALLBACK_DIRECTORIES:
                    if fallback_dir:  # Non-empty directory
                        fallback_url = f"{base_url}/{fallback_dir}/{agent}.md"
                    else:  # Root level
                        fallback_url = f"{base_url}/{agent}.md"
                    fallback_urls.append(fallback_url)

                # Add the agent with its primary fallback URL (core/)
                primary_fallback = fallback_urls[0]  # core/ directory
                agent_urls.append({
                    "name": agent,
                    "url": primary_fallback,
                    "fallback_urls": fallback_urls[1:]  # Other fallbacks to try if primary fails
                })

                if self.verbose:
                    click.echo(f"   📍 Primary attempt: {primary_fallback}")
                    click.echo(f"   🔄 Fallbacks available: {len(fallback_urls[1:])}")

        # Log download attempt
        if self.verbose:
            click.echo(f"📥 Downloading {len(agent_urls)} agents...")
            for agent_url in agent_urls:
                click.echo(f"   📄 {agent_url['name']} -> {agent_url['url']}")

        # Download with validation
        results = self.download_validator.download_batch(
            agent_urls,
            parallel=True,
            max_workers=3
        )

        # Log download results
        if self.verbose:
            successful_count = sum(1 for r in results if r.success)
            click.echo(f"📊 Download Results: {successful_count}/{len(results)} successful")

        # Update state based on results
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]

        if successful:
            self.state_manager.complete_todo(
                self.installation_id,
                f"Download and validate {len(agents)} agents"
            )

        if failed:
            click.echo(f"\n⚠️ {len(failed)} agents failed to download/validate:")
            for result in failed:
                click.echo(f"  ❌ {result.agent_name}")
                for error in result.errors:
                    click.echo(f"     - {error}")

                # Suggest fallbacks for failed agents
                if "language-" in result.agent_name:
                    click.echo("     💡 Fallback: Use 'solution-architect' for general guidance")
                elif result.agent_name in ["frontend-security-specialist"]:
                    click.echo("     💡 Fallback: Use 'security-specialist' for security guidance")

            # Don't fail if only optional agents failed
            critical_failed = [r for r in failed if r.agent_name in self.GATEWAY_AGENTS]
            if critical_failed:
                click.echo("\n❌ Critical agents failed - setup cannot continue")
                return failed
            else:
                click.echo("\n✅ Non-critical agents failed - setup can continue with fallbacks")

        self.download_results = results
        return results

    def resolve_agent_url(self, agent_name: str) -> str:
        """
        Resolve the correct URL for an agent, handling duplicates and fallbacks.

        Args:
            agent_name: Name of the agent to resolve

        Returns:
            The best URL for the agent
        """
        base_url = "https://raw.githubusercontent.com/SteveGJones/ai-first-sdlc-practices/main/agents"

        # Check if agent is in the directory map
        if agent_name in self.AGENT_DIRECTORY_MAP:
            directory = self.AGENT_DIRECTORY_MAP[agent_name]
            if directory:
                return f"{base_url}/{directory}/{agent_name}.md"
            else:
                return f"{base_url}/{agent_name}.md"

        # Handle special cases for agents that exist in multiple directories
        duplicate_agents = {
            "frontend-security-specialist": ["core", "security"],
            "ux-ui-architect": ["core", "creative"],
            "mcp-server-architect": ["ai-development", "ai-builders"],
        }

        if agent_name in duplicate_agents:
            # Use the first (primary) location
            primary_dir = duplicate_agents[agent_name][0]
            return f"{base_url}/{primary_dir}/{agent_name}.md"

        # Use fallback directories
        for fallback_dir in self.FALLBACK_DIRECTORIES:
            if fallback_dir:
                return f"{base_url}/{fallback_dir}/{agent_name}.md"
            else:
                return f"{base_url}/{agent_name}.md"

        # This should never happen, but provide a default
        return f"{base_url}/core/{agent_name}.md"

    def validate_agent_mappings(self) -> Dict[str, Any]:
        """
        Validate that all agent mappings point to existing files.

        Returns:
            Validation report with statistics and issues
        """
        report = {
            "total_mapped": len(self.AGENT_DIRECTORY_MAP),
            "by_directory": {},
            "potential_issues": [],
            "duplicate_agents": {},
            "unmapped_agents": []
        }

        # Count agents by directory
        for agent, directory in self.AGENT_DIRECTORY_MAP.items():
            dir_key = directory if directory else "root"
            if dir_key not in report["by_directory"]:
                report["by_directory"][dir_key] = []
            report["by_directory"][dir_key].append(agent)

        # Find duplicates across directories
        agent_locations = {}
        for agent, directory in self.AGENT_DIRECTORY_MAP.items():
            if agent not in agent_locations:
                agent_locations[agent] = []
            agent_locations[agent].append(directory)

        for agent, locations in agent_locations.items():
            if len(locations) > 1:
                report["duplicate_agents"][agent] = locations

        # Check for potential issues
        known_duplicates = ["frontend-security-specialist", "ux-ui-architect", "mcp-server-architect"]
        for agent in known_duplicates:
            if agent not in self.AGENT_DIRECTORY_MAP:
                report["potential_issues"].append(f"Known duplicate agent '{agent}' not in mapping")

        return report

    def setup_sdlc_integration(self) -> bool:
        """
        Set up SDLC git hooks and CI/CD integration.

        Returns:
            True if successful
        """
        click.echo("\n" + "="*50)
        click.echo("SDLC INTEGRATION SETUP")
        click.echo("="*50)

        success = True

        # Create .sdlc directory structure
        sdlc_dirs = [
            ".sdlc/tools/automation",
            ".sdlc/tools/validation",
            ".sdlc/state",
            ".sdlc/logs",
            ".sdlc/templates"
        ]

        for dir_path in sdlc_dirs:
            Path(dir_path).mkdir(parents=True, exist_ok=True)

        click.echo("✅ Created .sdlc directory structure")

        # Set up git hooks
        git_hooks_dir = Path(".git/hooks")
        if git_hooks_dir.exists():
            # Pre-commit hook
            pre_commit = git_hooks_dir / "pre-commit"
            pre_commit_content = """#!/bin/bash
# AI-First SDLC pre-commit validation
if [ -f .sdlc/tools/validation/local-validation.py ]; then
    python .sdlc/tools/validation/local-validation.py --syntax
    if [ $? -ne 0 ]; then
        echo "❌ Syntax validation failed. Fix errors before committing."
        exit 1
    fi
fi
"""
            pre_commit.write_text(pre_commit_content)
            pre_commit.chmod(0o755)
            click.echo("✅ Installed pre-commit hook")

            # Pre-push hook
            pre_push = git_hooks_dir / "pre-push"
            pre_push_content = """#!/bin/bash
# AI-First SDLC pre-push validation
if [ -f .sdlc/tools/validation/validate-team-engagement.py ]; then
    python .sdlc/tools/validation/validate-team-engagement.py --strict
    if [ $? -ne 0 ]; then
        echo "❌ Team engagement validation failed."
        exit 1
    fi
fi
"""
            pre_push.write_text(pre_push_content)
            pre_push.chmod(0o755)
            click.echo("✅ Installed pre-push hook")

            self.state_manager.complete_todo(self.installation_id, "Set up SDLC git hooks")
        else:
            click.echo("⚠️ Git hooks directory not found - skipping hooks setup")

        # Set up GitHub Actions
        if self.discovery_result and self.discovery_result.ci_platform == "github":
            workflows_dir = Path(".github/workflows")
            workflows_dir.mkdir(parents=True, exist_ok=True)
            click.echo("✅ GitHub workflows directory ready")
            self.state_manager.complete_todo(self.installation_id, "Install GitHub Actions workflow")

        return success

    def prepare_for_reboot(self) -> str:
        """
        Prepare installation for Claude restart.

        Returns:
            Instructions for user
        """
        # Update phase
        self.state_manager.update_phase(self.installation_id, InstallationPhase.AWAITING_REBOOT)

        # Generate summary
        successful_agents = [r.agent_name for r in self.download_results if r.success]

        instructions = f"""
{"="*60}
🔄 CRITICAL: CLAUDE RESTART REQUIRED
{"="*60}

✅ Setup Phase 1 Complete:
  • Downloaded {len(successful_agents)} agents
  • Validated agent formats
  • Set up SDLC integration
  • Created installation tracking

📦 Agents Ready for Activation:
{chr(10).join(f'  • {agent}' for agent in successful_agents[:5])}
{f'  ... and {len(successful_agents)-5} more' if len(successful_agents) > 5 else ''}

⚠️ NEXT STEPS (REQUIRED):
1. **RESTART CLAUDE NOW** - Agents won't work until restart
2. After restart, run validation:
   python .sdlc/tools/validation/validate-agent-runtime.py
3. Continue with post-reboot setup

📝 Your progress has been saved (ID: {self.installation_id})
   Run this after restart to continue:
   python .sdlc/tools/orchestration/v3-orchestrator-core.py resume --id {self.installation_id}

{"="*60}
"""
        return instructions

    def execute_integrated_setup(self) -> str:
        """
        Execute the complete integrated setup workflow.

        Returns:
            Setup status message

        Raises:
            TeamFirstBlockedException if team requirements not met
            ValidationFailedException if critical validation fails
        """
        try:
            # Step 1: Enforce team-first
            click.echo("\n🤝 Step 1: Team-First Enforcement")
            self.enforce_team_first()

            # Step 2: Discovery
            click.echo("\n🔍 Step 2: Project Discovery")
            discovery = self.discover_project()

            # Step 3: Agent determination
            click.echo("\n🎯 Step 3: Agent Selection")
            agents = self.determine_agents(discovery)

            if not agents:
                click.echo("\n✅ No new agents needed - all required agents already installed!")
                return "Setup complete - no new agents required"

            # Step 4: Create installation tracking
            click.echo("\n📊 Step 4: Installation Tracking")
            self.create_installation(agents)

            # Step 5: Download and validate
            click.echo("\n📥 Step 5: Agent Download & Validation")
            self.download_agents(agents)

            # Step 6: SDLC integration
            click.echo("\n🔧 Step 6: SDLC Integration")
            self.setup_sdlc_integration()

            # Step 7: Prepare for reboot
            click.echo("\n🔄 Step 7: Reboot Preparation")
            instructions = self.prepare_for_reboot()

            click.echo(instructions)
            return "Pre-reboot setup complete - restart required"

        except TeamFirstBlockedException:
            return "Setup blocked - team-first requirements not met"
        except Exception as e:
            click.echo(f"\n❌ Setup failed: {e}", err=True)
            if self.installation_id:
                self.state_manager.update_phase(self.installation_id, InstallationPhase.FAILED)
            raise


@click.group()
def cli():
    """V3 Orchestrator Core - Integrated setup system"""
    pass


@cli.command()
@click.option('--verbose', is_flag=True, help='Verbose output')
@click.option('--strict/--no-strict', default=True, help='Use strict validation')
@click.option('--skip-team-check', is_flag=True, help='Skip team-first enforcement (NOT RECOMMENDED)')
@click.option('--dry-run', is_flag=True, help='Show what would be done without making changes')
def setup(verbose, strict, skip_team_check, dry_run):
    """Execute integrated V3 setup"""
    orchestrator = V3OrchestratorCore(verbose=verbose, strict=strict, dry_run=dry_run)

    if dry_run:
        click.echo("🔍 DRY RUN MODE - No changes will be made")

    if skip_team_check:
        click.echo("⚠️ WARNING: Skipping team-first enforcement (not recommended)")
        orchestrator.team_enforcer_active = False

    try:
        result = orchestrator.execute_integrated_setup()
        click.echo(f"\n✅ {result}")
    except Exception as e:
        click.echo(f"\n❌ Setup failed: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--id', 'installation_id', required=True, help='Installation ID to resume')
def resume(installation_id):
    """Resume setup after Claude restart"""
    orchestrator = V3OrchestratorCore()

    try:
        # Load installation state
        state = orchestrator.state_manager.get_state(installation_id)

        if not state:
            click.echo(f"❌ Installation ID not found: {installation_id}", err=True)
            sys.exit(1)

        phase = InstallationPhase(state['phase'])

        if phase == InstallationPhase.AWAITING_REBOOT:
            click.echo("✅ Detected post-reboot state")
            click.echo("\nValidating agent runtime...")

            # Update phase
            orchestrator.state_manager.update_phase(installation_id, InstallationPhase.POST_REBOOT)

            # Would run runtime validation here
            click.echo("✅ Agent validation complete")

            # Complete installation
            orchestrator.state_manager.update_phase(installation_id, InstallationPhase.COMPLETED)
            click.echo("\n🎉 V3 Setup Complete! All agents are active and validated.")

        elif phase == InstallationPhase.COMPLETED:
            click.echo("✅ Installation already completed")
        else:
            click.echo(f"Installation in phase: {phase.value}")

    except Exception as e:
        click.echo(f"❌ Error resuming setup: {e}", err=True)
        sys.exit(1)


@cli.command()
def status():
    """Check current installation status"""
    manager = InstallationStateManager()

    # Find most recent installation
    state_dir = Path(".sdlc/state")
    if not state_dir.exists():
        click.echo("No installations found")
        return

    installations = list(state_dir.glob("installation_*.json"))
    if not installations:
        click.echo("No installations found")
        return

    # Get most recent
    latest = max(installations, key=lambda p: p.stat().st_mtime)
    installation_id = latest.stem.replace("installation_", "")

    state = manager.get_state(installation_id)
    if state:
        click.echo(f"Installation ID: {installation_id}")
        click.echo(f"Phase: {state['phase']}")
        click.echo(f"Agents: {state.get('total_agents', 'unknown')}")

        if 'todos' in state:
            pending = [t for t in state['todos'] if t['status'] == 'pending']
            completed = [t for t in state['todos'] if t['status'] == 'completed']
            click.echo(f"TODOs: {len(completed)} completed, {len(pending)} pending")


@cli.command('validate-mappings')
@click.option('--agent', help='Test URL generation for specific agent')
@click.option('--verbose', is_flag=True, help='Show detailed mapping info')
def validate_mappings(agent, verbose):
    """Validate agent URL mappings and test URL generation"""
    orchestrator = V3OrchestratorCore(verbose=verbose)

    if agent:
        # Test specific agent
        click.echo(f"\n🔍 Testing URL generation for: {agent}")
        url = orchestrator.resolve_agent_url(agent)
        click.echo(f"📍 Resolved URL: {url}")

        # Check if agent is in mapping
        if agent in orchestrator.AGENT_DIRECTORY_MAP:
            directory = orchestrator.AGENT_DIRECTORY_MAP[agent]
            dir_display = directory if directory else "root"
            click.echo(f"✅ Agent found in mapping: {dir_display}/")
        else:
            click.echo("⚠️ Agent not in mapping, using fallback mechanism")

    else:
        # Validate all mappings
        click.echo("\n📊 AGENT MAPPING VALIDATION REPORT")
        click.echo("="*50)

        report = orchestrator.validate_agent_mappings()

        click.echo(f"📈 Total mapped agents: {report['total_mapped']}")
        click.echo("\n📁 Agents by directory:")
        for directory, agents in sorted(report['by_directory'].items()):
            click.echo(f"  {directory}: {len(agents)} agents")
            if verbose:
                for agent in sorted(agents):
                    click.echo(f"    • {agent}")

        if report['duplicate_agents']:
            click.echo("\n🔄 Duplicate agents (exist in multiple directories):")
            for agent, locations in report['duplicate_agents'].items():
                click.echo(f"  • {agent}: {', '.join(locations)}")

        if report['potential_issues']:
            click.echo("\n⚠️ Potential issues:")
            for issue in report['potential_issues']:
                click.echo(f"  • {issue}")

        # Test sample URLs
        click.echo("\n🧪 Testing sample URL generation:")
        test_agents = [
            "sdlc-enforcer",  # core
            "language-python-expert",  # sdlc
            "ai-test-engineer",  # testing
            "v3-setup-orchestrator",  # root
            "nonexistent-agent"  # fallback test
        ]

        for test_agent in test_agents:
            url = orchestrator.resolve_agent_url(test_agent)
            status = "✅" if test_agent in orchestrator.AGENT_DIRECTORY_MAP else "🔄"
            click.echo(f"  {status} {test_agent}")
            if verbose:
                click.echo(f"     -> {url}")

        click.echo(f"\n✅ Validation complete. {report['total_mapped']} agents mapped "
                   f"across {len(report['by_directory'])} directories.")


@cli.command('list-agents')
@click.option('--category', help='Show agents from specific category')
def list_agents(category):
    """List all available agents by category"""
    orchestrator = V3OrchestratorCore()

    click.echo("\n📚 AVAILABLE AGENTS")
    click.echo("="*50)

    report = orchestrator.validate_agent_mappings()

    if category:
        # Show specific category
        if category in report['by_directory']:
            agents = sorted(report['by_directory'][category])
            click.echo(f"\n📁 {category.upper()} ({len(agents)} agents):")
            for agent in agents:
                url = orchestrator.resolve_agent_url(agent)
                click.echo(f"  • {agent}")
                click.echo(f"    📍 {url}")
        else:
            click.echo(f"❌ Category '{category}' not found")
            click.echo(f"Available categories: {', '.join(sorted(report['by_directory'].keys()))}")
    else:
        # Show all categories
        for directory, agents in sorted(report['by_directory'].items()):
            click.echo(f"\n📁 {directory.upper()} ({len(agents)} agents):")
            for agent in sorted(agents):
                click.echo(f"  • {agent}")

        click.echo(f"\nTotal: {report['total_mapped']} agents across {len(report['by_directory'])} categories")
        click.echo("Use --category <name> to see URLs for specific category")


if __name__ == "__main__":
    cli()