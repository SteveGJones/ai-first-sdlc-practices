#!/usr/bin/env python3
"""
SDLC Gate Enforcer for AI-First SDLC Framework

Enforces mandatory checkpoints and agent validations at each SDLC phase.
Prevents progression without required approvals and validations.
"""

import click
import yaml
import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple


class SDLCGateEnforcer:
    """Enforces mandatory SDLC gates and agent validations."""

    def __init__(self, project_path: Path = None):
        self.project_path = project_path or Path.cwd()
        self.gates_config_file = (
            self.project_path / ".sdlc" / "config" / "sdlc-gates.yaml"
        )
        self.gate_status_file = self.project_path / ".sdlc" / "gate-status.json"
        self.level_file = self.project_path / ".sdlc" / "level.json"
        self.gates_config = self._load_gates_config()
        self.current_level = self._get_current_level()

    def _load_gates_config(self) -> Dict:
        """Load SDLC gates configuration."""
        if not self.gates_config_file.exists():
            # Use default configuration
            return self._get_default_gates_config()

        with open(self.gates_config_file) as f:
            return yaml.safe_load(f)

    def _get_default_gates_config(self) -> Dict:
        """Get default gates configuration."""
        return {
            "gates": {
                "requirements": {
                    "mandatory": True,
                    "required_agents": ["solution-architect", "critical-goal-reviewer"],
                    "consensus_type": "all",
                    "documents_required": ["docs/feature-proposals/XX-feature.md"],
                },
                "design": {
                    "mandatory": True,
                    "required_agents": ["solution-architect", "security-architect"],
                    "consensus_type": "majority",
                    "documents_required": [
                        "docs/architecture/requirements-traceability-matrix.md",
                        "docs/architecture/what-if-analysis.md",
                        "docs/architecture/architecture-decision-record.md",
                        "docs/architecture/system-invariants.md",
                        "docs/architecture/integration-design.md",
                        "docs/architecture/failure-mode-analysis.md",
                    ],
                },
                "implementation": {
                    "mandatory": True,
                    "required_agents": ["sdlc-enforcer", "test-manager"],
                    "continuous_validation": True,
                },
                "review": {
                    "mandatory": True,
                    "required_agents": ["critical-goal-reviewer", "test-manager"],
                },
                "deployment": {
                    "mandatory": True,
                    "required_agents": ["sre-specialist", "compliance-auditor"],
                },
            }
        }

    def _get_current_level(self) -> str:
        """Get current SDLC level."""
        if self.level_file.exists():
            with open(self.level_file) as f:
                return json.load(f).get("level", "production")
        return "production"

    def _get_gate_config(self, gate_name: str) -> Dict:
        """Get configuration for a specific gate, including level overrides."""
        gate_config = self.gates_config.get("gates", {}).get(gate_name, {}).copy()

        # Apply level-specific overrides
        level_overrides = self.gates_config.get("level_overrides", {}).get(
            self.current_level, {}
        )
        for key, value in level_overrides.items():
            gate_config[key] = value

        return gate_config

    def _load_gate_status(self) -> Dict:
        """Load current gate status."""
        if self.gate_status_file.exists():
            with open(self.gate_status_file) as f:
                return json.load(f)
        return {}

    def _save_gate_status(self, status: Dict):
        """Save gate status."""
        self.gate_status_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.gate_status_file, "w") as f:
            json.dump(status, f, indent=2)

    def check_gate(self, gate_name: str) -> Tuple[bool, List[str]]:
        """Check if a gate's requirements are met."""
        gate_config = self._get_gate_config(gate_name)
        if not gate_config:
            return False, [f"Unknown gate: {gate_name}"]

        issues = []

        # Check required documents
        docs_required = gate_config.get("required_docs", [])
        for doc_pattern in docs_required:
            if "XX" in doc_pattern:
                # Pattern-based check
                doc_dir = self.project_path / Path(doc_pattern).parent
                if not doc_dir.exists() or not any(doc_dir.iterdir()):
                    issues.append(f"Missing required document matching: {doc_pattern}")
            else:
                # Exact file check
                if not (self.project_path / doc_pattern).exists():
                    issues.append(f"Missing required document: {doc_pattern}")

        # Check validation status
        validation_checks = gate_config.get("validation_checks", [])
        for check in validation_checks:
            if not self._is_validation_passing(check):
                issues.append(f"Validation failing: {check}")

        # Check agent approvals
        required_agents = gate_config.get("required_agents", [])
        if required_agents:
            approvals = self._get_agent_approvals(gate_name)
            for agent in required_agents:
                if agent not in approvals:
                    issues.append(f"Missing approval from: {agent}")

        return len(issues) == 0, issues

    def _is_validation_passing(self, check_name: str) -> bool:
        """Check if a specific validation is passing."""
        # Map check names to actual validation commands
        check_commands = {
            "technical-debt": "python tools/validation/check-technical-debt.py",
            "test-coverage": "python -m pytest --cov",
            "security-scan": "python tools/validation/security-scan.py",
            "architecture-complete": "python tools/validation/validate-architecture.py",
        }

        cmd = check_commands.get(check_name)
        if not cmd:
            return True  # Unknown checks pass by default

        try:
            result = subprocess.run(
                cmd.split(), capture_output=True, cwd=self.project_path
            )
            return result.returncode == 0
        except Exception:
            return False

    def _get_agent_approvals(self, gate_name: str) -> List[str]:
        """Get list of agents that have approved this gate."""
        status = self._load_gate_status()
        gate_status = status.get(gate_name, {})
        return gate_status.get("approvals", [])

    def approve_gate(self, gate_name: str, agent_name: str):
        """Record agent approval for a gate."""
        status = self._load_gate_status()

        if gate_name not in status:
            status[gate_name] = {
                "approvals": [],
                "status": "pending",
                "last_updated": datetime.now().isoformat(),
            }

        if agent_name not in status[gate_name]["approvals"]:
            status[gate_name]["approvals"].append(agent_name)

        # Check if gate is now complete
        gate_config = self._get_gate_config(gate_name)
        required_agents = gate_config.get("required_agents", [])
        consensus_type = gate_config.get("consensus_type", "all")

        if consensus_type == "all":
            if all(
                agent in status[gate_name]["approvals"] for agent in required_agents
            ):
                status[gate_name]["status"] = "approved"
        elif consensus_type == "majority":
            approved_count = sum(
                1
                for agent in required_agents
                if agent in status[gate_name]["approvals"]
            )
            if approved_count > len(required_agents) / 2:
                status[gate_name]["status"] = "approved"

        self._save_gate_status(status)

    def can_proceed_to_next_phase(
        self, current_phase: str, next_phase: str
    ) -> Tuple[bool, List[str]]:
        """Check if progression to next phase is allowed."""
        # Define phase progression order
        phase_order = [
            "requirements",
            "design",
            "implementation",
            "review",
            "deployment",
        ]

        if current_phase not in phase_order or next_phase not in phase_order:
            return False, ["Invalid phase names"]

        current_idx = phase_order.index(current_phase)
        next_idx = phase_order.index(next_phase)

        if next_idx != current_idx + 1:
            return False, ["Can only proceed to next sequential phase"]

        # Check if current phase gate is complete
        gate_complete, issues = self.check_gate(current_phase)
        if not gate_complete:
            return False, [f"Current phase '{current_phase}' not complete:"] + issues

        return True, []

    def get_agent_sequence(self, scenario: str) -> List[str]:
        """Get mandatory agent sequence for a scenario."""
        sequences = self.gates_config.get("sequences", {})
        scenario_config = sequences.get(scenario, {})
        return scenario_config.get("sequence", [])

    def resolve_conflict(self, gate_name: str, conflicting_agents: List[str]) -> str:
        """Resolve conflicts between agent decisions."""
        conflict_rules = self.gates_config.get("conflict_resolution", {})

        # Check for single veto power
        veto_agents = (
            conflict_rules.get("resolution_strategies", {})
            .get("single_veto", {})
            .get("agents", [])
        )
        for agent in conflicting_agents:
            if agent in veto_agents:
                return f"{agent} has veto power - their decision stands"

        # Follow escalation path
        escalation = conflict_rules.get("escalation_path", [])
        return f"Escalate to: {' -> '.join(escalation)}"


@click.group()
def cli():
    """SDLC Gate Enforcer - Mandatory checkpoints for AI-First development"""


@cli.command()
@click.argument("gate_name")
def check(gate_name):
    """Check if a gate's requirements are met."""
    enforcer = SDLCGateEnforcer()
    passed, issues = enforcer.check_gate(gate_name)

    if passed:
        click.echo(f"✅ Gate '{gate_name}' requirements met")
    else:
        click.echo(f"❌ Gate '{gate_name}' has issues:")
        for issue in issues:
            click.echo(f"   • {issue}")


@cli.command()
@click.argument("gate_name")
@click.argument("agent_name")
def approve(gate_name, agent_name):
    """Record agent approval for a gate."""
    enforcer = SDLCGateEnforcer()
    enforcer.approve_gate(gate_name, agent_name)
    click.echo(f"✅ {agent_name} approved gate '{gate_name}'")

    # Check if gate is now complete
    passed, _ = enforcer.check_gate(gate_name)
    if passed:
        click.echo(f"🎉 Gate '{gate_name}' is now COMPLETE")


@cli.command()
@click.argument("current_phase")
@click.argument("next_phase")
def proceed(current_phase, next_phase):
    """Check if progression to next phase is allowed."""
    enforcer = SDLCGateEnforcer()
    allowed, issues = enforcer.can_proceed_to_next_phase(current_phase, next_phase)

    if allowed:
        click.echo(f"✅ Can proceed from '{current_phase}' to '{next_phase}'")
    else:
        click.echo(f"🚫 Cannot proceed to '{next_phase}':")
        for issue in issues:
            click.echo(f"   • {issue}")


@cli.command()
def status():
    """Show current gate status."""
    enforcer = SDLCGateEnforcer()
    status = enforcer._load_gate_status()

    click.echo("📊 SDLC Gate Status")
    click.echo(f"   Level: {enforcer.current_level}")
    click.echo()

    phases = ["requirements", "design", "implementation", "review", "deployment"]
    for phase in phases:
        gate_status = status.get(phase, {})
        status_icon = "✅" if gate_status.get("status") == "approved" else "⏳"
        approvals = gate_status.get("approvals", [])

        click.echo(f"{status_icon} {phase.capitalize()}")
        if approvals:
            click.echo(f"   Approved by: {', '.join(approvals)}")
        else:
            click.echo("   No approvals yet")


@cli.command()
@click.argument("scenario")
def sequence(scenario):
    """Show mandatory agent sequence for a scenario."""
    enforcer = SDLCGateEnforcer()
    sequence = enforcer.get_agent_sequence(scenario)

    if sequence:
        click.echo(f"🔄 Agent sequence for '{scenario}':")
        for i, agent in enumerate(sequence, 1):
            click.echo(f"   {i}. {agent}")
    else:
        click.echo(f"No defined sequence for scenario: {scenario}")


@cli.command()
@click.option("--gate", help="Gate where conflict occurred")
@click.option("--agents", multiple=True, help="Conflicting agents")
def resolve(gate, agents):
    """Resolve conflicts between agent decisions."""
    enforcer = SDLCGateEnforcer()
    resolution = enforcer.resolve_conflict(gate, list(agents))
    click.echo(f"🤝 Conflict resolution: {resolution}")


if __name__ == "__main__":
    cli()
