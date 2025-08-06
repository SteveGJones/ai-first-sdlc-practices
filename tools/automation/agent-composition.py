#!/usr/bin/env python3
"""Agent Composition System for AI-First SDLC Framework

This module implements agent composition, allowing multiple agents to be
combined into composite agents with enhanced capabilities.
"""

import json
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Set
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()


class AgentCompositionManager:
    """Manages agent compositions and composite agent creation."""

    def __init__(self, compositions_file: Path = None):
        if compositions_file is None:
            # Default to the compositions file in the agents directory
            compositions_file = (
                Path(__file__).parent.parent.parent
                / "agents"
                / "agent-compositions.yaml"
            )

        self.compositions_file = compositions_file
        self.compositions = self._load_compositions()

    def _load_compositions(self) -> Dict:
        """Load agent compositions from YAML file."""
        if not self.compositions_file.exists():
            console.print(
                f"[yellow]Warning: Compositions file not found: {self.compositions_file}[/yellow]"
            )
            return {"compositions": {}, "rules": {}}

        with open(self.compositions_file) as f:
            return yaml.safe_load(f)

    def get_composition(self, name: str) -> Optional[Dict]:
        """Get a specific composition by name."""
        return self.compositions.get("compositions", {}).get(name)

    def list_compositions(self) -> List[str]:
        """List all available compositions."""
        return list(self.compositions.get("compositions", {}).keys())

    def create_composite_agent(self, composition_name: str, output_path: Path) -> bool:
        """Create a composite agent markdown file from a composition."""
        composition = self.get_composition(composition_name)
        if not composition:
            console.print(
                f"[red]Error: Composition '{composition_name}' not found[/red]"
            )
            return False

        # Generate the composite agent content
        content = self._generate_composite_agent_content(composition_name, composition)

        # Write to file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            f.write(content)

        console.print(f"[green]✓ Created composite agent: {output_path}[/green]")
        return True

    def _generate_composite_agent_content(self, name: str, composition: Dict) -> str:
        """Generate markdown content for a composite agent."""
        includes = composition.get("includes", [])
        use_cases = composition.get("use_cases", [])

        # Create examples from use cases
        examples = []
        for i, use_case in enumerate(use_cases[:3]):  # Limit to 3 examples
            examples.append(
                """- <example>
  Context: {use_case}
  user: "I need help with {use_case.lower()}"
  assistant: "I'll use the {name} composite agent to provide comprehensive guidance across all required domains."
  <commentary>
  The {name} combines multiple agent capabilities for {use_case.lower()}.
  </commentary>
</example>"""
            )

        examples_text = "\n".join(examples) if examples else ""

        content = """---
name: {name}
description: {composition.get('description', '')}\\n\\nThis is a composite agent that combines the expertise of: {', '.join(includes)}.\\n\\nExamples:\\n{examples_text}
color: purple
---

You are the {composition.get('name', name)}, a composite agent that combines the expertise and capabilities of multiple specialized agents. Your mission is to provide comprehensive, coordinated guidance by leveraging the combined knowledge of your constituent agents.

Your combined expertise includes:
"""

        # Add expertise from all included agents
        base_agent = composition.get("base_agent")
        if base_agent:
            content += f"- All capabilities of {base_agent} (primary expertise)\n"

        for agent in includes:
            content += f"- Full expertise from {agent}\n"

        content += """
When providing guidance, you will:

1. **Integrated Analysis**:
   - Combine perspectives from all included agents
   - Identify cross-domain dependencies
   - Provide holistic recommendations
   - Ensure consistency across domains

2. **Coordinated Approach**:
   - Align recommendations across disciplines
   - Resolve conflicts between different viewpoints
   - Prioritize actions based on overall impact
   - Create unified implementation plans

3. **Comprehensive Coverage**:
   - Address all aspects of the problem
   - Fill gaps between individual agent domains
   - Provide end-to-end solutions
   - Ensure nothing falls through cracks

Your response format should include:
- **Integrated Assessment**: Combined analysis from all perspectives
- **Unified Recommendations**: Coordinated actions across domains
- **Implementation Plan**: Step-by-step approach considering all aspects
- **Cross-Domain Considerations**: How different areas interact
- **Risk Mitigation**: Comprehensive risk assessment

You maintain the best qualities of all included agents while providing a unified voice. You never provide conflicting advice but rather synthesize the best approach from all perspectives.

This composite agent includes expertise from:
- Base: {base_agent or 'None'}
- Includes: {', '.join(includes)}

Use cases:
{chr(10).join(f'- {uc}' for uc in use_cases)}
"""

        return content

    def recommend_composition(self, project_context: Dict) -> List[str]:
        """Recommend compositions based on project context."""
        recommendations = []
        rules = self.compositions.get("rules", {}).get("auto_include", [])

        for rule in rules:
            condition = rule.get("when", "")
            if self._evaluate_condition(condition, project_context):
                # Find compositions that include the recommended agents
                for agent in rule.get("include", []):
                    for comp_name, comp_data in self.compositions.get(
                        "compositions", {}
                    ).items():
                        if agent in comp_data.get("includes", []):
                            if comp_name not in recommendations:
                                recommendations.append(comp_name)

        return recommendations

    def _evaluate_condition(self, condition: str, context: Dict) -> bool:
        """Evaluate a condition against project context."""
        # Simple condition evaluation
        if condition == "project_has_api":
            return context.get("has_api", False)
        elif condition == "project_is_production":
            return context.get("is_production", False)
        elif condition == "project_has_compliance_requirements":
            return context.get("compliance_required", False)
        return False

    def display_composition_info(self, composition_name: str):
        """Display detailed information about a composition."""
        composition = self.get_composition(composition_name)
        if not composition:
            console.print(f"[red]Composition '{composition_name}' not found[/red]")
            return

        # Create info panel
        panel_content = """
[bold]{composition.get('name', composition_name)}[/bold]

[yellow]Description:[/yellow]
{composition.get('description', 'No description available')}

[yellow]Base Agent:[/yellow] {composition.get('base_agent', 'None')}

[yellow]Included Agents:[/yellow]
{chr(10).join(f'  • {agent}' for agent in composition.get('includes', []))}

[yellow]Use Cases:[/yellow]
{chr(10).join(f'  • {uc}' for uc in composition.get('use_cases', []))}
"""

        console.print(Panel(panel_content, title=f"Composition: {composition_name}"))


@click.group()
def cli():
    """Agent Composition Management for AI-First SDLC Framework."""


@cli.command()
def list():
    """List all available agent compositions."""
    manager = AgentCompositionManager()
    compositions = manager.list_compositions()

    if not compositions:
        console.print("[yellow]No compositions found[/yellow]")
        return

    table = Table(title="Available Agent Compositions")
    table.add_column("Name", style="cyan")
    table.add_column("Description", style="white")
    table.add_column("Includes", style="green")

    for comp_name in compositions:
        comp_data = manager.compositions.get("compositions", {}).get(comp_name, {})
        if comp_data:
            includes = ", ".join(comp_data.get("includes", []))
            table.add_row(
                comp_name,
                comp_data.get("description", "")[:50] + "...",
                includes[:50] + ("..." if len(includes) > 50 else ""),
            )

    console.print(table)


@cli.command()
@click.argument("name")
def info(name: str):
    """Show detailed information about a composition."""
    manager = AgentCompositionManager()
    manager.display_composition_info(name)


@cli.command()
@click.argument("name")
@click.option("--output", "-o", type=Path, help="Output path for composite agent")
def create(name: str, output: Optional[Path]):
    """Create a composite agent from a composition."""
    manager = AgentCompositionManager()

    if not output:
        output = Path(f"composite-{name}.md")

    if manager.create_composite_agent(name, output):
        console.print("\n[green]Composite agent created successfully![/green]")
        console.print(f"You can now use this agent by referencing: [cyan]{name}[/cyan]")


@cli.command()
@click.option("--has-api", is_flag=True, help="Project has API")
@click.option("--production", is_flag=True, help="Production project")
@click.option("--compliance", is_flag=True, help="Requires compliance")
def recommend(has_api: bool, production: bool, compliance: bool):
    """Recommend compositions based on project characteristics."""
    manager = AgentCompositionManager()

    context = {
        "has_api": has_api,
        "is_production": production,
        "compliance_required": compliance,
    }

    recommendations = manager.recommend_composition(context)

    if recommendations:
        console.print("\n[green]Recommended Compositions:[/green]")
        for rec in recommendations:
            console.print(f"  • [cyan]{rec}[/cyan]")
    else:
        console.print(
            "[yellow]No specific compositions recommended for this context[/yellow]"
        )


if __name__ == "__main__":
    cli()
