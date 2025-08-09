#!/usr/bin/env python3
"""
SDLC Level Management Tool for AI-First SDLC Framework

Detects, manages, and helps migrate between progressive SDLC levels:
- Level 1: Prototype (lightweight)
- Level 2: Production (full architecture)
- Level 3: Enterprise (team scale)
"""

import click
import json
import os
from pathlib import Path
from datetime import datetime
import subprocess
from typing import Dict, Tuple


class SDLCLevelManager:
    """Manages SDLC levels for projects."""

    LEVELS = {
        "prototype": {
            "name": "Prototype",
            "description": "Quick starts for exploration and MVPs",
            "required_docs": [
                "feature-intent.md",
                "basic-design.md",
                "retrospective.md",
            ],
            "validation_checks": ["branch", "intent", "retrospective", "security"],
            "allows_todos": True,
            "branch_protection": "optional",
        },
        "production": {
            "name": "Production",
            "description": "Professional applications with full architecture",
            "required_docs": [
                "requirements-traceability-matrix.md",
                "what-if-analysis.md",
                "architecture-decision-record.md",
                "system-invariants.md",
                "integration-design.md",
                "failure-mode-analysis.md",
                "feature-proposal.md",
                "retrospective.md",
            ],
            "validation_checks": [
                "branch",
                "proposal",
                "architecture",
                "technical-debt",
                "type-safety",
                "security",
                "tests",
                "retrospective",
            ],
            "allows_todos": False,
            "branch_protection": "required",
        },
        "enterprise": {
            "name": "Enterprise",
            "description": "Large teams with compliance requirements",
            "required_docs": [
                # All production docs plus:
                "compliance-mapping.md",
                "team-coordination.md",
                "stakeholder-log.md",
                "audit-trail.md",
            ],
            "validation_checks": [
                "all",
                "compliance",
                "team-coordination",
                "audit-trail",
            ],
            "allows_todos": False,
            "branch_protection": "strict",
        },
    }

    def __init__(self, project_path: Path = None):
        self.project_path = project_path or Path.cwd()
        self.config_file = self.project_path / ".sdlc" / "level.json"

    def detect_current_level(self) -> Tuple[str, Dict]:
        """Detect the current SDLC level based on project state."""
        # Always analyze the project to get current metrics
        analysis = self._analyze_project()

        # Check if level is explicitly set
        if self.config_file.exists():
            with open(self.config_file) as f:
                config = json.load(f)
                # Use the configured level but return the analysis
                return config["level"], analysis

        # Otherwise, suggest level based on analysis
        suggested_level = self._suggest_level(analysis)

        return suggested_level, analysis

    def _analyze_project(self) -> Dict:
        """Analyze project characteristics."""
        analysis = {
            "has_architecture_docs": self._check_architecture_docs(),
            "has_todos": self._check_for_todos(),
            "team_size": self._estimate_team_size(),
            "has_ci_cd": self._check_ci_cd(),
            "project_age_days": self._get_project_age(),
            "file_count": self._count_files(),
            "has_tests": self._check_for_tests(),
            "branch_protection": self._check_branch_protection(),
        }
        return analysis

    def _check_architecture_docs(self) -> Dict[str, bool]:
        """Check which architecture documents exist."""
        docs = {}
        arch_dir = self.project_path / "docs" / "architecture"

        for level, config in self.LEVELS.items():
            for doc in config["required_docs"]:
                doc_path = arch_dir / doc
                docs[doc] = doc_path.exists()

        return docs

    def _check_for_todos(self) -> bool:
        """Check if project has TODO/FIXME comments."""
        try:
            result = subprocess.run(
                [
                    "grep",
                    "-r",
                    "-E",
                    "TODO|FIXME|HACK",
                    "--include=*.py",
                    "--include=*.js",
                    "--include=*.ts",
                    ".",
                ],
                cwd=self.project_path,
                capture_output=True,
            )
            return result.returncode == 0  # Found TODOs
        except Exception:
            return False

    def _estimate_team_size(self) -> int:
        """Estimate team size from git contributors."""
        try:
            result = subprocess.run(
                ["git", "log", "--format=%ae"],
                cwd=self.project_path,
                capture_output=True,
                text=True,
            )
            unique_emails = set(result.stdout.strip().split("\n"))
            return len(unique_emails)
        except Exception:
            return 1

    def _check_ci_cd(self) -> bool:
        """Check if CI/CD is configured."""
        ci_indicators = [
            ".github/workflows",
            ".gitlab-ci.yml",
            "Jenkinsfile",
            ".circleci",
            "azure-pipelines.yml",
        ]

        for indicator in ci_indicators:
            if (self.project_path / indicator).exists():
                return True
        return False

    def _get_project_age(self) -> int:
        """Get project age in days."""
        try:
            result = subprocess.run(
                ["git", "log", "--reverse", "--format=%at", "-1"],
                cwd=self.project_path,
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                first_commit = float(result.stdout.strip())
                age_seconds = datetime.now().timestamp() - first_commit
                return int(age_seconds / 86400)  # Convert to days
        except Exception:
            return 0

    def _count_files(self) -> int:
        """Count source files in project."""
        count = 0
        for root, dirs, files in os.walk(self.project_path):
            # Skip hidden and build directories
            dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ["node_modules", "__pycache__", "dist", "build"]]

            for file in files:
                if any(file.endswith(ext) for ext in [".py", ".js", ".ts", ".java", ".go"]):
                    count += 1
        return count

    def _check_for_tests(self) -> bool:
        """Check if project has tests."""
        test_dirs = ["tests", "test", "__tests__", "spec"]
        for test_dir in test_dirs:
            if (self.project_path / test_dir).exists():
                return True
        return False

    def _check_branch_protection(self) -> str:
        """Check branch protection status."""
        try:
            result = subprocess.run(
                ["gh", "api", "repos/:owner/:repo/branches/main/protection"],
                capture_output=True,
            )
            if result.returncode == 0:
                return "enabled"
        except Exception:
            return "unknown"

    def _suggest_level(self, analysis: Dict) -> str:
        """Suggest appropriate level based on analysis."""
        # Enterprise indicators
        if analysis["team_size"] > 5 or "compliance" in str(self.project_path):
            return "enterprise"

        # Production indicators
        if (
            analysis["has_ci_cd"]
            and analysis["has_tests"]
            and analysis["file_count"] > 20
            and analysis["project_age_days"] > 30
        ):
            return "production"

        # Default to prototype
        return "prototype"

    def set_level(self, level: str) -> bool:
        """Set the SDLC level for the project."""
        if level not in self.LEVELS:
            return False

        config = {
            "level": level,
            "set_date": datetime.now().isoformat(),
            "framework_version": self._get_framework_version(),
        }

        # Create .sdlc directory if needed
        self.config_file.parent.mkdir(exist_ok=True)

        with open(self.config_file, "w") as f:
            json.dump(config, f, indent=2)

        return True

    def _get_framework_version(self) -> str:
        """Get framework version."""
        version_file = self.project_path / "VERSION"
        if version_file.exists():
            return version_file.read_text().strip()
        return "unknown"

    def check_readiness(self, target_level: str) -> Dict[str, bool]:
        """Check if project is ready for target level."""
        if target_level not in self.LEVELS:
            return {}

        level_config = self.LEVELS[target_level]
        readiness = {}

        # Check required documents
        arch_docs = self._check_architecture_docs()
        for doc in level_config["required_docs"]:
            readiness[f"doc_{doc}"] = arch_docs.get(doc, False)

        # Check other requirements
        if not level_config["allows_todos"]:
            readiness["no_todos"] = not self._check_for_todos()

        if level_config["branch_protection"] in ["required", "strict"]:
            readiness["branch_protection"] = self._check_branch_protection() == "enabled"

        return readiness


@click.group()
def cli():
    """SDLC Level Management for AI-First Framework"""


@cli.command()
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
def check(output_json):
    """Check current SDLC level and project status."""
    manager = SDLCLevelManager()
    current_level, analysis = manager.detect_current_level()

    if output_json:
        output = {
            "current_level": current_level,
            "level_config": manager.LEVELS[current_level],
            "analysis": analysis,
        }
        click.echo(json.dumps(output, indent=2))
    else:
        level_config = manager.LEVELS[current_level]
        click.echo(f"🎯 Current SDLC Level: {level_config['name']}")
        click.echo(f"   {level_config['description']}")
        click.echo()

        click.echo("📊 Project Analysis:")
        click.echo(f"   Team size: {analysis['team_size']} developer(s)")
        click.echo(f"   Project age: {analysis['project_age_days']} days")
        click.echo(f"   File count: {analysis['file_count']} source files")
        click.echo(f"   Has tests: {'Yes' if analysis['has_tests'] else 'No'}")
        click.echo(f"   Has CI/CD: {'Yes' if analysis['has_ci_cd'] else 'No'}")
        click.echo(f"   Has TODOs: {'Yes' if analysis['has_todos'] else 'No'}")


@cli.command()
@click.argument("level", type=click.Choice(["prototype", "production", "enterprise"]))
@click.option("--force", is_flag=True, help="Force level change without checks")
def set(level, force):
    """Set the SDLC level for this project."""
    manager = SDLCLevelManager()

    if not force:
        # Check readiness
        readiness = manager.check_readiness(level)
        not_ready = [k for k, v in readiness.items() if not v]

        if not_ready:
            click.echo(f"⚠️  Project not ready for {level} level:")
            for item in not_ready:
                click.echo(f"   ❌ {item}")
            click.echo("\nUse --force to override")
            return

    if manager.set_level(level):
        level_config = manager.LEVELS[level]
        click.echo(f"✅ SDLC level set to: {level_config['name']}")
        click.echo(f"   {level_config['description']}")
    else:
        click.echo("❌ Failed to set level")


@cli.command()
@click.argument("target_level", type=click.Choice(["prototype", "production", "enterprise"]))
def migrate(target_level):
    """Guide migration to a different SDLC level."""
    manager = SDLCLevelManager()
    current_level, _ = manager.detect_current_level()

    if current_level == target_level:
        click.echo(f"Already at {target_level} level")
        return

    # Check what's needed
    readiness = manager.check_readiness(target_level)
    ready_items = [k for k, v in readiness.items() if v]
    todo_items = [k for k, v in readiness.items() if not v]

    click.echo(f"🔄 Migration Guide: {current_level} → {target_level}")
    click.echo()

    if ready_items:
        click.echo("✅ Already completed:")
        for item in ready_items:
            click.echo(f"   • {item}")

    if todo_items:
        click.echo("\n📋 To-do items:")
        for item in todo_items:
            if item.startswith("doc_"):
                doc_name = item[4:]
                click.echo(f"   • Create {doc_name}")
            elif item == "no_todos":
                click.echo("   • Remove all TODO/FIXME comments")
            elif item == "branch_protection":
                click.echo("   • Enable branch protection")

    click.echo(f"\n💡 When ready, run: sdlc-level set {target_level}")


@cli.command()
def graduation():
    """Check if project is ready to graduate to next level."""
    manager = SDLCLevelManager()
    current_level, analysis = manager.detect_current_level()

    # Determine next level
    level_order = ["prototype", "production", "enterprise"]
    current_index = level_order.index(current_level)

    if current_index >= len(level_order) - 1:
        click.echo("🎓 Already at highest level (Enterprise)")
        return

    next_level = level_order[current_index + 1]

    click.echo(f"🎓 Graduation Readiness: {current_level} → {next_level}")
    click.echo()

    # Check readiness
    readiness = manager.check_readiness(next_level)
    ready_count = sum(1 for v in readiness.values() if v)
    total_count = len(readiness)

    percentage = (ready_count / total_count * 100) if total_count > 0 else 0

    click.echo(f"📊 Readiness: {ready_count}/{total_count} ({percentage:.0f}%)")

    if percentage >= 100:
        click.echo("\n✅ Ready to graduate!")
        click.echo(f"   Run: sdlc-level set {next_level}")
    else:
        click.echo("\n⏳ Not quite ready yet. Complete the remaining items:")
        not_ready = [k for k, v in readiness.items() if not v]
        for item in not_ready:
            click.echo(f"   • {item}")


if __name__ == "__main__":
    cli()
