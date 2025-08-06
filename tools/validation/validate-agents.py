#!/usr/bin/env python3
"""Agent Validation Tool for AI-First SDLC Framework

Validates agent files for:
- Proper YAML frontmatter structure
- Required metadata fields
- Valid category assignment
- Dependency resolution
- Content quality checks
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple
import click
import yaml
from rich.console import Console
from rich.table import Table

console = Console()

REQUIRED_FIELDS = {
    "name",
    "version",
    "category",
    "description",
    "expertise",
    "triggers",
}

CORE_CATEGORIES = {
    "core/governance",
    "core/architecture",
    "core/testing",
    "core/review",
}

VALID_PRIORITIES = {"critical", "high", "medium", "low"}


class AgentValidator:
    """Validates agent files for correctness and quality."""

    def __init__(self, agent_dir: Path):
        self.agent_dir = agent_dir
        self.all_agents: Dict[str, Dict] = {}
        self.errors: List[Tuple[str, str]] = []
        self.warnings: List[Tuple[str, str]] = []

    def validate_all(self) -> bool:
        """Validate all agents in the directory."""
        console.print(f"[bold]Validating agents in: {self.agent_dir}[/bold]\n")

        # First pass: Load all agents
        self._load_all_agents()

        # Second pass: Validate each agent
        for agent_path in self.agent_dir.rglob("*.md"):
            if agent_path.name.startswith("."):
                continue
            self._validate_agent(agent_path)

        # Third pass: Cross-agent validation
        self._validate_dependencies()
        self._validate_categories()

        # Report results
        self._report_results()

        return len(self.errors) == 0

    def _load_all_agents(self):
        """Load metadata for all agents."""
        for agent_path in self.agent_dir.rglob("*.md"):
            if agent_path.name.startswith("."):
                continue

            try:
                metadata = self._parse_agent_metadata(agent_path)
                self.all_agents[metadata["name"]] = {
                    "path": agent_path,
                    "metadata": metadata,
                }
            except Exception as e:
                self.errors.append((str(agent_path), f"Failed to parse: {e}"))

    def _parse_agent_metadata(self, agent_path: Path) -> Dict:
        """Parse agent YAML frontmatter."""
        with open(agent_path) as f:
            content = f.read()

        if not content.startswith("---"):
            raise ValueError("Missing YAML frontmatter")

        parts = content.split("---", 2)
        if len(parts) < 3:
            raise ValueError("Invalid agent format")

        metadata = yaml.safe_load(parts[1])
        metadata["_content"] = parts[2].strip()
        metadata["_content_lines"] = len(parts[2].strip().split("\n"))
        return metadata

    def _validate_agent(self, agent_path: Path):
        """Validate a single agent file."""
        relative_path = agent_path.relative_to(self.agent_dir)

        try:
            metadata = self._parse_agent_metadata(agent_path)
            agent_name = metadata.get("name", str(relative_path))

            # Check required fields
            missing_fields = REQUIRED_FIELDS - set(metadata.keys())
            if missing_fields:
                self.errors.append(
                    (
                        agent_name,
                        f"Missing required fields: {', '.join(missing_fields)}",
                    )
                )

            # Validate version format
            version = metadata.get("version", "")
            if not self._is_valid_version(version):
                self.errors.append((agent_name, f"Invalid version format: {version}"))

            # Validate category
            category = metadata.get("category", "")
            if not self._is_valid_category(category):
                self.warnings.append((agent_name, f"Non-standard category: {category}"))

            # Check priority if specified
            if "priority" in metadata:
                if metadata["priority"] not in VALID_PRIORITIES:
                    self.warnings.append(
                        (agent_name, f"Invalid priority: {metadata['priority']}")
                    )

            # Validate expertise list
            if "expertise" in metadata:
                if not isinstance(metadata["expertise"], list):
                    self.errors.append((agent_name, "Expertise must be a list"))
                elif len(metadata["expertise"]) < 3:
                    self.warnings.append(
                        (agent_name, "Agent should have at least 3 areas of expertise")
                    )

            # Validate triggers
            if "triggers" in metadata:
                if not isinstance(metadata["triggers"], list):
                    self.errors.append((agent_name, "Triggers must be a list"))
                elif len(metadata["triggers"]) < 2:
                    self.warnings.append(
                        (agent_name, "Agent should have at least 2 triggers")
                    )

            # Content quality checks
            content_lines = metadata.get("_content_lines", 0)
            if content_lines < 50:
                self.warnings.append(
                    (
                        agent_name,
                        f"Agent content seems too short ({content_lines} lines)",
                    )
                )

            # Check for key sections in content
            content = metadata.get("_content", "")
            required_sections = [
                "## Core",
                "## Primary Responsibilities",
                "## When",
                "## Output",
            ]

            missing_sections = []
            for section in required_sections:
                if section not in content:
                    missing_sections.append(section)

            if missing_sections:
                self.warnings.append(
                    (
                        agent_name,
                        f"Missing content sections: {', '.join(missing_sections)}",
                    )
                )

        except Exception as e:
            self.errors.append((str(relative_path), str(e)))

    def _is_valid_version(self, version: str) -> bool:
        """Check if version follows semantic versioning."""
        parts = version.split(".")
        if len(parts) != 3:
            return False

        try:
            for part in parts:
                int(part)
            return True
        except ValueError:
            return False

    def _is_valid_category(self, category: str) -> bool:
        """Check if category follows expected patterns."""
        valid_patterns = [
            "core/",
            "languages/",
            "ux/",
            "devops/",
            "data/",
            "compliance/",
            "ai-ml/",
            "agent-development/",
            "mcp/",
            "testing/",
            "architecture/",
            "review/",
        ]

        return any(category.startswith(pattern) for pattern in valid_patterns)

    def _validate_dependencies(self):
        """Validate that all agent dependencies exist."""
        for agent_name, agent_info in self.all_agents.items():
            metadata = agent_info["metadata"]
            if "dependencies" in metadata:
                for dep in metadata["dependencies"]:
                    if dep not in self.all_agents:
                        # Check if it's a category reference
                        if not any(
                            dep.startswith(cat)
                            for cat in [
                                "testing/",
                                "review/",
                                "architecture/",
                                "languages/",
                            ]
                        ):
                            self.warnings.append(
                                (agent_name, f"Unknown dependency: {dep}")
                            )

    def _validate_categories(self):
        """Ensure proper category distribution."""
        category_counts = {}

        for agent_info in self.all_agents.values():
            category = agent_info["metadata"].get("category", "")
            base_category = category.split("/")[0]
            category_counts[base_category] = category_counts.get(base_category, 0) + 1

        # Check for required core agents
        if "core" not in category_counts or category_counts["core"] < 10:
            self.warnings.append(
                (
                    "Framework",
                    f"Only {category_counts.get('core', 0)} core agents found (expected 10+)",
                )
            )

    def _report_results(self):
        """Display validation results."""
        total_agents = len(self.all_agents)

        # Summary
        console.print("\n[bold]Validation Summary[/bold]")
        console.print(f"Total agents: {total_agents}")
        console.print(f"Errors: {len(self.errors)}")
        console.print(f"Warnings: {len(self.warnings)}")

        # Errors
        if self.errors:
            console.print("\n[bold red]Errors[/bold red]")
            table = Table(show_header=True)
            table.add_column("Agent", style="red")
            table.add_column("Error")

            for agent, error in self.errors:
                table.add_row(agent, error)

            console.print(table)

        # Warnings
        if self.warnings:
            console.print("\n[bold yellow]Warnings[/bold yellow]")
            table = Table(show_header=True)
            table.add_column("Agent", style="yellow")
            table.add_column("Warning")

            for agent, warning in self.warnings:
                table.add_row(agent, warning)

            console.print(table)

        # Success message
        if not self.errors:
            console.print("\n[bold green]✓ All agents passed validation![/bold green]")
        else:
            console.print("\n[bold red]✗ Validation failed![/bold red]")

    def generate_manifest(self, output_path: Path):
        """Generate a manifest of all valid agents."""
        manifest = {"version": "1.0.0", "agents": {}}

        for agent_name, agent_info in self.all_agents.items():
            metadata = agent_info["metadata"]
            # Only include agents without errors
            has_error = any(agent == agent_name for agent, _ in self.errors)

            if not has_error:
                manifest["agents"][agent_name] = {
                    "version": metadata.get("version", "1.0.0"),
                    "category": metadata.get("category", "unknown"),
                    "description": metadata.get("description", ""),
                    "dependencies": metadata.get("dependencies", []),
                    "priority": metadata.get("priority", "medium"),
                    "path": str(agent_info["path"].relative_to(self.agent_dir)),
                }

        with open(output_path, "w") as f:
            yaml.dump(manifest, f, default_flow_style=False, sort_keys=False)

        console.print(f"\n[green]Generated manifest: {output_path}[/green]")


@click.command()
@click.argument("agent_dir", type=click.Path(exists=True))
@click.option("--strict", is_flag=True, help="Treat warnings as errors")
@click.option("--manifest", type=click.Path(), help="Generate agent manifest file")
@click.option("--fix", is_flag=True, help="Attempt to fix common issues")
def main(agent_dir, strict, manifest, fix):
    """Validate AI agent files for the AI-First SDLC framework."""

    agent_path = Path(agent_dir).resolve()
    validator = AgentValidator(agent_path)

    # Run validation
    success = validator.validate_all()
    # In strict mode, warnings are errors
    if strict and validator.warnings:
        success = False
    # Generate manifest if requested
    if manifest and success:
        manifest_path = Path(manifest)
        validator.generate_manifest(manifest_path)

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
