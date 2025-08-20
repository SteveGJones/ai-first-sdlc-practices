#!/usr/bin/env python3
"""
Create Agent from Template - Last resort agent creation following strict template.
This tool should ONLY be used when no existing agent or combination can meet needs.
"""

import json
import sys
from pathlib import Path
from typing import List, Optional
from datetime import datetime

import click
# import yaml  # Not used in this file


AGENT_TEMPLATE = """---
name: {name}
description: {description}
examples:{examples}
color: {color}
---

You are the {display_name}, {expanded_description}.

Your core competencies include:
{competencies}

## Your Approach

{approach}

## Key Responsibilities

{responsibilities}

## Integration with Team

You work closely with:
{team_integration}

## Success Metrics

Your effectiveness is measured by:
{success_metrics}
"""

EXAMPLE_TEMPLATE = """
  - context: {context}
    user: "{user}"
    assistant: "{assistant}" """

# Valid colors per the agent format spec
VALID_COLORS = ["blue", "green", "purple", "red", "cyan", "yellow", "orange"]


class TemplateAgentCreator:
    """
    Creates agents following the strict template format.
    Validates before writing to ensure compliance.
    """
    
    def __init__(self, validate_strict: bool = True):
        self.validate_strict = validate_strict
        self.validator = self._load_validator()
    
    def _load_validator(self):
        """Load the agent format validator if available"""
        validator_path = Path(__file__).parent.parent / "validation" / "validate-agent-format.py"
        if validator_path.exists():
            import importlib.spec
            spec = importlib.spec.spec_from_file_location("agent_validator", validator_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module.AgentValidator(strict=self.validate_strict)
        return None
    
    def justify_creation(self, name: str, reason: str) -> bool:
        """
        Verify that creation is justified.
        
        Args:
            name: Agent name
            reason: Justification for creation
        
        Returns:
            True if justified, False otherwise
        """
        # Check if agent already exists
        existing_agents = [
            "sdlc-enforcer", "critical-goal-reviewer", "solution-architect",
            "api-architect", "backend-engineer", "frontend-engineer",
            "database-architect", "devops-specialist", "sre-specialist",
            "ai-test-engineer", "performance-engineer", "integration-orchestrator",
            "security-specialist", "documentation-architect", "technical-writer",
            "language-python-expert", "language-javascript-expert", "language-go-expert"
        ]
        
        if any(existing in name.lower() for existing in existing_agents):
            click.echo("❌ ERROR: Similar agent already exists", err=True)
            click.echo("Check existing agents before creating new ones", err=True)
            return False
        
        if len(reason) < 50:
            click.echo("❌ ERROR: Justification too short", err=True)
            click.echo("Provide detailed reason why existing agents can't meet this need", err=True)
            return False
        
        return True
    
    def create_agent(self, 
                    name: str,
                    description: str,
                    competencies: List[str],
                    examples: List[dict],
                    color: str = "blue",
                    approach: Optional[str] = None,
                    responsibilities: Optional[List[str]] = None,
                    team_integration: Optional[List[str]] = None,
                    success_metrics: Optional[List[str]] = None) -> str:
        """
        Create an agent following the strict template.
        
        Args:
            name: Agent name (lowercase-hyphenated)
            description: Short description (max 150 chars)
            competencies: List of core competencies
            examples: List of usage examples
            color: Agent color
            approach: How the agent approaches tasks
            responsibilities: Key responsibilities
            team_integration: Which agents it works with
            success_metrics: How to measure effectiveness
        
        Returns:
            Agent content as string
        """
        # Validate inputs
        if not name.replace("-", "").replace("_", "").isalnum():
            raise ValueError("Name must be alphanumeric with hyphens only")
        
        if len(description) > 150:
            raise ValueError(f"Description too long: {len(description)} chars (max 150)")
        
        if color not in VALID_COLORS:
            raise ValueError(f"Invalid color: {color}. Must be one of {VALID_COLORS}")
        
        # Format examples
        examples_str = ""
        for ex in examples:
            examples_str += EXAMPLE_TEMPLATE.format(
                context=ex.get("context", "When to use this agent"),
                user=ex.get("user", "Example request"),
                assistant=ex.get("assistant", f"I'll use the {name} to help")
            )
        
        # Format competencies
        competencies_str = "\n".join(f"- {comp}" for comp in competencies)
        
        # Default values
        if not approach:
            approach = (f"As the {name}, I focus on delivering high-quality results through "
                       "systematic analysis and careful consideration of requirements.")
        
        if not responsibilities:
            responsibilities = [
                "Analyze requirements thoroughly",
                "Provide expert guidance in my domain",
                "Collaborate with other specialists",
                "Ensure quality and compliance",
                "Document decisions and rationale"
            ]
        
        if not team_integration:
            team_integration = [
                "sdlc-enforcer for process compliance",
                "solution-architect for system design",
                "critical-goal-reviewer for alignment"
            ]
        
        if not success_metrics:
            success_metrics = [
                "Quality of deliverables",
                "Alignment with requirements",
                "Team collaboration effectiveness",
                "Compliance with standards"
            ]
        
        # Format lists
        responsibilities_str = "\n".join(f"- {resp}" for resp in responsibilities)
        team_integration_str = "\n".join(f"- {team}" for team in team_integration)
        success_metrics_str = "\n".join(f"- {metric}" for metric in success_metrics)
        
        # Create display name
        display_name = name.replace("-", " ").title()
        
        # Expand description for body
        expanded_description = description
        if len(expanded_description) < 100:
            expanded_description += " specializing in delivering high-quality solutions"
        
        # Generate agent content
        agent_content = AGENT_TEMPLATE.format(
            name=name,
            description=description,
            examples=examples_str,
            color=color,
            display_name=display_name,
            expanded_description=expanded_description,
            competencies=competencies_str,
            approach=approach,
            responsibilities=responsibilities_str,
            team_integration=team_integration_str,
            success_metrics=success_metrics_str
        )
        
        return agent_content
    
    def validate_agent(self, content: str) -> tuple[bool, List[str]]:
        """
        Validate agent content against template requirements.
        
        Args:
            content: Agent content to validate
        
        Returns:
            Tuple of (is_valid, errors)
        """
        if self.validator:
            # Write to temp file for validation
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as tmp:
                tmp.write(content)
                tmp_path = tmp.name
            
            try:
                is_valid, errors, warnings = self.validator.validate_file(tmp_path)
                return is_valid, errors
            finally:
                Path(tmp_path).unlink()
        
        # Basic validation if validator not available
        errors = []
        
        # Check YAML frontmatter
        if not content.startswith("---\n"):
            errors.append("Missing YAML frontmatter")
        
        # Check required fields
        required = ["name:", "description:", "examples:", "color:"]
        for field in required:
            if field not in content:
                errors.append(f"Missing required field: {field}")
        
        return len(errors) == 0, errors
    
    def save_agent(self, content: str, name: str, output_dir: Path) -> Path:
        """
        Save agent to file after validation.
        
        Args:
            content: Agent content
            name: Agent name
            output_dir: Output directory
        
        Returns:
            Path to saved agent
        """
        # Validate first
        is_valid, errors = self.validate_agent(content)
        
        if not is_valid:
            raise ValueError(f"Agent validation failed: {', '.join(errors)}")
        
        # Create output directory
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save agent
        agent_path = output_dir / f"{name}.md"
        agent_path.write_text(content)
        
        return agent_path
    
    def log_creation(self, name: str, reason: str, path: Path):
        """
        Log agent creation for audit trail.
        
        Args:
            name: Agent name
            reason: Why it was created
            path: Where it was saved
        """
        log_dir = Path(".sdlc/logs")
        log_dir.mkdir(parents=True, exist_ok=True)
        
        log_file = log_dir / "agent-creation.log"
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "agent_name": name,
            "justification": reason,
            "path": str(path),
            "created_by": "create-agent-from-template.py"
        }
        
        # Append to log
        with open(log_file, "a") as f:
            f.write(json.dumps(log_entry) + "\n")


@click.command()
@click.option('--name', required=True, help='Agent name (lowercase-hyphenated)')
@click.option('--description', required=True, help='Short description (max 150 chars)')
@click.option('--competencies', required=True, help='Comma-separated core competencies')
@click.option('--reason', required=True, help='Justification for creating this agent')
@click.option('--color', default='blue', type=click.Choice(VALID_COLORS), help='Agent color')
@click.option('--examples', help='JSON file with examples')
@click.option('--output', default='.claude/agents', help='Output directory')
@click.option('--validate-strict/--no-validate-strict', default=True, help='Use strict validation')
@click.option('--force', is_flag=True, help='Skip justification check')
def create_agent(name, description, competencies, reason, color, examples, output, validate_strict, force):
    """
    Create a new agent from template (LAST RESORT ONLY).
    
    This tool should only be used when:
    1. No existing agent provides the needed expertise
    2. No combination of agents can cover the need
    3. The need is critical and specific
    
    Example:
        python create-agent-from-template.py \\
            --name "quantum-specialist" \\
            --description "Quantum computing and algorithm specialist" \\
            --competencies "quantum algorithms,quantum gates,QML" \\
            --reason "Project requires quantum computing expertise not covered by existing agents"
    """
    creator = TemplateAgentCreator(validate_strict=validate_strict)
    
    # Check justification
    if not force and not creator.justify_creation(name, reason):
        click.echo("\n❌ Creation not justified. Use existing agents or combinations.", err=True)
        sys.exit(1)
    
    # Parse competencies
    competencies_list = [c.strip() for c in competencies.split(",")]
    
    # Load or create examples
    if examples:
        with open(examples) as f:
            examples_list = json.load(f)
    else:
        # Default examples
        examples_list = [
            {
                "context": f"When {name.replace('-', ' ')} expertise is needed",
                "user": f"I need help with {competencies_list[0]}",
                "assistant": f"I'll engage the {name} to provide expert guidance"
            },
            {
                "context": f"For specialized {name.replace('-', ' ')} tasks",
                "user": f"Can you review this {competencies_list[0]} implementation?",
                "assistant": f"Let me have the {name} analyze this for you"
            }
        ]
    
    try:
        # Create agent
        click.echo(f"\n📝 Creating agent: {name}")
        content = creator.create_agent(
            name=name,
            description=description,
            competencies=competencies_list,
            examples=examples_list,
            color=color
        )
        
        # Validate
        click.echo("🔍 Validating agent format...")
        is_valid, errors = creator.validate_agent(content)
        
        if not is_valid:
            click.echo("\n❌ Validation failed:", err=True)
            for error in errors:
                click.echo(f"  - {error}", err=True)
            sys.exit(1)
        
        # Save
        click.echo("💾 Saving agent...")
        agent_path = creator.save_agent(content, name, Path(output))
        
        # Log creation
        creator.log_creation(name, reason, agent_path)
        
        click.echo(f"\n✅ Agent created successfully: {agent_path}")
        click.echo("\n⚠️ REMEMBER: This was a last resort. Document why existing agents couldn't meet this need.")
        
        # Show next steps
        click.echo("\n📋 Next steps:")
        click.echo("1. Restart Claude for the agent to become active")
        click.echo("2. Run post-reboot validation:")
        click.echo("   python .sdlc/tools/validation/validate-agent-runtime.py")
        click.echo("3. Document in retrospective why this agent was necessary")
        
    except Exception as e:
        click.echo(f"\n❌ Failed to create agent: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    create_agent()