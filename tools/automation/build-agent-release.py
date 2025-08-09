#!/usr/bin/env python3
"""Build Agent Release Package

This script prepares agents for distribution by:
1. Validating all agent files
2. Copying validated agents to release directory
3. Generating manifest files
4. Creating versioned release packages
"""

import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
import click
import yaml
from rich.console import Console

console = Console()


class AgentReleaseBuilder:
    """Builds release packages for agent distribution."""

    def __init__(self, source_dir: Path, release_dir: Path):
        self.source_dir = source_dir
        self.release_dir = release_dir
        self.release_agents_dir = release_dir / "agents"
        self.build_timestamp = datetime.now().isoformat()

    def clean_release_dir(self) -> None:
        """Clean the release directory."""
        if self.release_agents_dir.exists():
            console.print("[yellow]Cleaning existing release directory...[/yellow]")
            shutil.rmtree(self.release_agents_dir)

        self.release_agents_dir.mkdir(parents=True, exist_ok=True)

    def validate_agents(self) -> bool:
        """Run agent validation."""
        console.print("[bold]Validating agents...[/bold]")

        # Run the validation script
        result = subprocess.run(
            [
                sys.executable,
                "tools/validation/validate-agents.py",
                str(self.source_dir),
            ],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            console.print("[red]Agent validation failed![/red]")
            console.print(result.stdout)
            console.print(result.stderr)
            return False

        console.print("[green]✓ All agents validated successfully[/green]")
        return True

    def copy_agents(self) -> bool:
        """Copy validated agents to release directory."""
        console.print("\n[bold]Copying agents to release directory...[/bold]")

        copied_count = 0
        for agent_file in self.source_dir.rglob("*.md"):
            if agent_file.name.startswith("."):
                continue

            # Preserve directory structure
            relative_path = agent_file.relative_to(self.source_dir)
            target_path = self.release_agents_dir / relative_path

            # Create parent directory
            target_path.parent.mkdir(parents=True, exist_ok=True)

            # Copy file
            shutil.copy2(agent_file, target_path)
            copied_count += 1

        console.print(f"[green]✓ Copied {copied_count} agents[/green]")

    def generate_release_manifest(self) -> bool:
        """Generate comprehensive release manifest."""
        console.print("\n[bold]Generating release manifest...[/bold]")

        manifest = {
            "version": "1.0.0",
            "build_date": self.build_timestamp,
            "categories": {},
            "agents": {},
            "core_agents": [],
            "statistics": {
                "total_agents": 0,
                "core_agents": 0,
                "optional_agents": 0,
                "categories": {},
            },
        }

        # Scan all agents
        for agent_file in self.release_agents_dir.rglob("*.md"):
            relative_path = agent_file.relative_to(self.release_agents_dir)
            category = relative_path.parent.as_posix()

            # Parse agent metadata
            with open(agent_file) as f:
                content = f.read()

            if content.startswith("---"):
                parts = content.split("---", 2)
                metadata = yaml.safe_load(parts[1])
                agent_name = metadata.get("name", agent_file.stem)

                # Add to manifest
                manifest["agents"][agent_name] = {
                    "version": metadata.get("version", "1.0.0"),
                    "category": metadata.get("category", category),
                    "description": metadata.get("description", ""),
                    "path": str(relative_path),
                    "priority": metadata.get("priority", "medium"),
                    "dependencies": metadata.get("dependencies", []),
                }

                # Track core agents
                if category == "core" or metadata.get("category", "").startswith("core/"):
                    manifest["core_agents"].append(agent_name)
                    manifest["statistics"]["core_agents"] += 1
                else:
                    manifest["statistics"]["optional_agents"] += 1

                # Category statistics
                if category not in manifest["categories"]:
                    manifest["categories"][category] = []
                manifest["categories"][category].append(agent_name)

                # Update statistics
                manifest["statistics"]["total_agents"] += 1

                cat_base = category.split("/")[0]
                if cat_base not in manifest["statistics"]["categories"]:
                    manifest["statistics"]["categories"][cat_base] = 0
                manifest["statistics"]["categories"][cat_base] += 1

        # Save manifest
        manifest_path = self.release_dir / "agent-manifest.json"
        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)

        console.print(f"[green]✓ Generated manifest with {manifest['statistics']['total_agents']} agents[/green]")

        # Display statistics
        console.print("\n[bold]Release Statistics:[/bold]")
        console.print(f"  Core agents: {manifest['statistics']['core_agents']}")
        console.print(f"  Optional agents: {manifest['statistics']['optional_agents']}")
        console.print(f"  Categories: {len(manifest['categories'])}")

    def create_agent_index(self) -> bool:
        """Create an index file for easy agent discovery."""
        console.print("\n[bold]Creating agent index...[/bold]")

        index_content = """# AI-First SDLC Agent Library

This directory contains specialized AI agents for the AI-First SDLC framework.

## Agent Categories

### Core Agents (Required)
Essential agents that every project needs:
"""

        # Add core agents
        core_dir = self.release_agents_dir / "core"
        if core_dir.exists():
            for agent_file in sorted(core_dir.glob("*.md")):
                agent_name = agent_file.stem
                index_content += f"- `{agent_name}` - Core SDLC functionality\n"

        index_content += """
### Language-Specific Agents
Specialized agents for different programming languages:
"""

        # Add language agents
        languages_dir = self.release_agents_dir / "languages"
        if languages_dir.exists():
            for lang_dir in sorted(languages_dir.iterdir()):
                if lang_dir.is_dir():
                    index_content += f"\n#### {lang_dir.name.title()}\n"
                    for agent_file in sorted(lang_dir.glob("*.md")):
                        agent_name = agent_file.stem
                        index_content += f"- `{agent_name}`\n"

        index_content += """
### Specialized Agents
Domain-specific agents for various use cases:
"""

        # Add other categories
        for category_dir in sorted(self.release_agents_dir.iterdir()):
            if category_dir.is_dir() and category_dir.name not in ["core", "languages"]:
                index_content += f"\n#### {category_dir.name.replace('-', ' ').title()}\n"
                for agent_file in sorted(category_dir.rglob("*.md")):
                    agent_name = agent_file.stem
                    relative_path = agent_file.relative_to(category_dir)
                    index_content += f"- `{agent_name}` ({relative_path.parent})\n"

        index_content += """
## Installation

Agents are automatically installed when setting up a new project:
```bash
python setup-smart.py "Your project description"
```

To install agents manually:
```bash
python tools/automation/agent-installer.py
```

## Validation

All agents are validated before release:
```bash
python tools/validation/validate-agents.py agents/
```
"""

        # Save index
        index_path = self.release_agents_dir / "README.md"
        with open(index_path, "w") as f:
            f.write(index_content)

        console.print("[green]✓ Created agent index[/green]")

    def create_version_file(self) -> None:
        """Create version tracking file."""
        version_info = {
            "agent_library_version": "1.0.0",
            "build_date": self.build_timestamp,
            "framework_version": self._get_framework_version(),
        }

        version_path = self.release_dir / "agent-version.json"
        with open(version_path, "w") as f:
            json.dump(version_info, f, indent=2)

        console.print("[green]✓ Created version file[/green]")

    def _get_framework_version(self) -> str:
        """Get the framework version."""
        version_file = Path("VERSION")
        if version_file.exists():
            return version_file.read_text().strip()
        return "1.0.0"

    def build(self) -> bool:
        """Execute the complete build process."""
        console.print("[bold]Building Agent Release Package[/bold]\n")

        # Step 1: Validate
        if not self.validate_agents():
            return False

        # Step 2: Clean
        self.clean_release_dir()

        # Step 3: Copy
        self.copy_agents()

        # Step 4: Generate manifest
        self.generate_release_manifest()

        # Step 5: Create index
        self.create_agent_index()

        # Step 6: Version info
        self.create_version_file()

        console.print("\n[bold green]✓ Agent release build complete![/bold green]")
        console.print(f"Release directory: {self.release_dir}")

        return True


@click.command()
@click.option(
    "--source",
    "-s",
    type=click.Path(exists=True),
    default="agents",
    help="Source agent directory",
)
@click.option(
    "--release",
    "-r",
    type=click.Path(),
    default="release",
    help="Release output directory",
)
@click.option("--clean", is_flag=True, help="Clean release directory first")
def main(source: str, release: str, clean: bool) -> None:
    """Build agent release package for distribution."""

    source_dir = Path(source).resolve()
    release_dir = Path(release).resolve()

    if not source_dir.exists():
        console.print(f"[red]Source directory not found: {source_dir}[/red]")
        sys.exit(1)

    builder = AgentReleaseBuilder(source_dir, release_dir)

    if clean and release_dir.exists():
        console.print("[yellow]Cleaning entire release directory...[/yellow]")
        shutil.rmtree(release_dir)

    success = builder.build()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
