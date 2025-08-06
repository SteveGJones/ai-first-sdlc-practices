#!/usr/bin/env python3
"""Agent Recommender for AI-First SDLC Framework

Recommends appropriate AI agents based on:
- Project analysis results
- Stated project objectives
- Current project phase
- Identified challenges
"""

import json
from pathlib import Path
from typing import Dict, List, Set, Tuple
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()


class AgentRecommender:
    """Recommends agents based on project characteristics and objectives."""

    def __init__(self, agent_manifest_path: Path = None):
        self.agent_manifest_path = agent_manifest_path
        self.agent_registry = self._load_agent_registry()

    def _load_agent_registry(self) -> Dict:
        """Load the agent registry with recommendations rules."""
        # This would normally load from the manifest, but we'll define rules here
        return {
            "core": {
                "sdlc-coach": {
                    "always": True,
                    "description": "Essential for AI-First SDLC compliance",
                },
                "test-manager": {
                    "always": True,
                    "description": "Oversees all testing activities",
                },
                "solution-architect": {
                    "always": True,
                    "description": "Ensures architectural coherence",
                },
                "security-architect": {
                    "conditions": ["web-app", "api", "production"],
                    "description": "Security best practices and threat modeling",
                },
            },
            "sdlc": {
                "framework-validator": {
                    "always": True,
                    "description": "Real-time compliance validation",
                },
                "kickstart-architect": {
                    "new_project": True,
                    "description": "Optimal project kickstarters",
                },
                "project-bootstrapper": {
                    "new_project": True,
                    "description": "One-command project setup",
                },
                "retrospective-miner": {
                    "mature_project": True,
                    "description": "Extract insights from retrospectives",
                },
                "language-python-expert": {
                    "languages": ["python"],
                    "description": "Python-specific SDLC guidance",
                },
            },
            "languages": {
                "python-expert": {
                    "languages": ["python"],
                    "description": "Python best practices and patterns",
                },
                "python-test-engineer": {
                    "languages": ["python"],
                    "testing": True,
                    "description": "Python testing strategies",
                },
                "javascript-expert": {
                    "languages": ["javascript", "typescript"],
                    "description": "JavaScript/TypeScript best practices",
                },
                "react-architect": {
                    "frameworks": ["react"],
                    "description": "React patterns and optimization",
                },
                "go-expert": {
                    "languages": ["go"],
                    "description": "Go idioms and concurrency",
                },
                "java-architect": {
                    "languages": ["java"],
                    "description": "Java patterns and Spring expertise",
                },
            },
            "specialized": {
                "api-designer": {
                    "project_types": ["api"],
                    "description": "RESTful and GraphQL API design",
                },
                "database-architect": {
                    "databases": True,
                    "description": "Database design and optimization",
                },
                "kubernetes-architect": {
                    "tools": ["kubernetes"],
                    "description": "K8s deployment and scaling",
                },
                "aws-solutions-architect": {
                    "cloud_platforms": ["aws"],
                    "description": "AWS services and cost optimization",
                },
                "ml-architect": {
                    "domains": ["machine-learning"],
                    "description": "ML system design and MLOps",
                },
                "frontend-performance": {
                    "project_types": ["frontend"],
                    "description": "Web performance optimization",
                },
                "microservices-architect": {
                    "architecture": ["microservices"],
                    "description": "Distributed system design",
                },
                "event-streaming-expert": {
                    "tools": ["kafka"],
                    "architecture": ["event-driven"],
                    "description": "Event-driven architecture",
                },
                "ci-cd-architect": {
                    "ci_cd": True,
                    "description": "Pipeline optimization and automation",
                },
                "accessibility-expert": {
                    "project_types": ["frontend", "web-app"],
                    "description": "WCAG compliance and a11y",
                },
            },
        }

    def recommend(
        self, analysis: Dict, objectives: str = None
    ) -> Dict[str, List[Dict]]:
        """Recommend agents based on project analysis."""
        recommendations = {
            "essential": [],
            "strongly_recommended": [],
            "recommended": [],
            "optional": [],
        }

        # Always include core agents
        for agent_name, agent_info in self.agent_registry["core"].items():
            if agent_info.get("always"):
                recommendations["essential"].append(
                    {
                        "name": agent_name,
                        "category": "core",
                        "reason": agent_info["description"],
                    }
                )
            else:
                if self._matches_conditions(agent_info, analysis):
                    recommendations["strongly_recommended"].append(
                        {
                            "name": agent_name,
                            "category": "core",
                            "reason": agent_info["description"],
                        }
                    )

        # SDLC-specific agents
        for agent_name, agent_info in self.agent_registry["sdlc"].items():
            if agent_info.get("always"):
                recommendations["essential"].append(
                    {
                        "name": agent_name,
                        "category": "sdlc",
                        "reason": agent_info["description"],
                    }
                )
            elif agent_info.get("new_project") and analysis.get("is_new_project", True):
                recommendations["strongly_recommended"].append(
                    {
                        "name": agent_name,
                        "category": "sdlc",
                        "reason": agent_info["description"],
                    }
                )
            elif agent_info.get("languages"):
                if self._matches_language(agent_info, analysis):
                    recommendations["strongly_recommended"].append(
                        {
                            "name": agent_name,
                            "category": "sdlc",
                            "reason": agent_info["description"],
                        }
                    )

        # Language-specific agents
        for agent_name, agent_info in self.agent_registry["languages"].items():
            if self._matches_language(agent_info, analysis):
                priority = (
                    "strongly_recommended"
                    if analysis.get("primary_language")
                    in agent_info.get("languages", [])
                    else "recommended"
                )
                recommendations[priority].append(
                    {
                        "name": agent_name,
                        "category": "languages",
                        "reason": agent_info["description"],
                    }
                )

        # Specialized agents based on project characteristics
        for agent_name, agent_info in self.agent_registry["specialized"].items():
            if self._matches_specialized(agent_info, analysis):
                recommendations["recommended"].append(
                    {
                        "name": agent_name,
                        "category": "specialized",
                        "reason": agent_info["description"],
                    }
                )

        # Adjust based on objectives
        if objectives:
            recommendations = self._adjust_for_objectives(
                recommendations, objectives, analysis
            )

        # Adjust based on project size and team
        recommendations = self._adjust_for_scale(recommendations, analysis)

        return recommendations

    def _matches_conditions(self, agent_info: Dict, analysis: Dict) -> bool:
        """Check if agent conditions match project."""
        conditions = agent_info.get("conditions", [])

        for condition in conditions:
            if condition in analysis.get("project_types", []):
                return True
            if condition == "production" and analysis.get("project_size") in [
                "large",
                "enterprise",
            ]:
                return True

        return False

    def _matches_language(self, agent_info: Dict, analysis: Dict) -> bool:
        """Check if language agent matches project."""
        agent_langs = agent_info.get("languages", [])
        project_langs = set(analysis.get("languages", {}).keys())

        if any(lang in project_langs for lang in agent_langs):
            # Check additional conditions
            if agent_info.get("frameworks"):
                if not any(
                    fw in analysis.get("frameworks", [])
                    for fw in agent_info["frameworks"]
                ):
                    return False
            if agent_info.get("testing") and not analysis.get("testing"):
                return False
            return True

        return False

    def _matches_specialized(self, agent_info: Dict, analysis: Dict) -> bool:
        """Check if specialized agent matches project."""
        # Check project types
        if agent_info.get("project_types"):
            if any(
                pt in analysis.get("project_types", [])
                for pt in agent_info["project_types"]
            ):
                return True

        # Check databases
        if agent_info.get("databases") and analysis.get("databases"):
            return True

        # Check tools
        if agent_info.get("tools"):
            if any(tool in analysis.get("tools", []) for tool in agent_info["tools"]):
                return True

        # Check cloud platforms
        if agent_info.get("cloud_platforms"):
            if any(
                cp in analysis.get("cloud_platforms", [])
                for cp in agent_info["cloud_platforms"]
            ):
                return True

        # Check domains
        if agent_info.get("domains"):
            if any(
                domain in analysis.get("domains", [])
                for domain in agent_info["domains"]
            ):
                return True

        # Check architecture
        if agent_info.get("architecture"):
            if any(
                arch in analysis.get("architecture", [])
                for arch in agent_info["architecture"]
            ):
                return True

        # Check CI/CD
        if agent_info.get("ci_cd") and analysis.get("ci_cd"):
            return True

        return False

    def _adjust_for_objectives(
        self, recommendations: Dict, objectives: str, analysis: Dict
    ) -> Dict:
        """Adjust recommendations based on stated objectives."""
        objectives_lower = objectives.lower()

        # Performance focus
        if any(
            word in objectives_lower
            for word in ["performance", "speed", "fast", "optimize"]
        ):
            self._promote_agent(recommendations, "frontend-performance")
            self._promote_agent(recommendations, "database-architect")

        # Security focus
        if any(
            word in objectives_lower
            for word in ["security", "secure", "compliance", "audit"]
        ):
            self._promote_agent(recommendations, "security-architect", "essential")

        # Scale focus
        if any(
            word in objectives_lower for word in ["scale", "growth", "million", "users"]
        ):
            self._promote_agent(recommendations, "microservices-architect")
            self._promote_agent(recommendations, "kubernetes-architect")

        # Quality focus
        if any(
            word in objectives_lower for word in ["quality", "testing", "reliability"]
        ):
            self._promote_agent(recommendations, "test-strategist")

        # AI/ML focus
        if any(
            word in objectives_lower
            for word in ["ai", "ml", "machine learning", "artificial"]
        ):
            self._add_agent(
                recommendations,
                "ml-architect",
                "specialized",
                "ML system design based on objectives",
                "strongly_recommended",
            )

        return recommendations

    def _adjust_for_scale(self, recommendations: Dict, analysis: Dict) -> Dict:
        """Adjust recommendations based on project scale."""
        size = analysis.get("project_size", "small")
        team_size = analysis.get("team_size", 1)

        if size in ["large", "enterprise"] or team_size > 10:
            # Large projects need more governance
            self._add_agent(
                recommendations,
                "process-auditor",
                "core",
                "Process compliance for large teams",
                "strongly_recommended",
            )
            self._add_agent(
                recommendations,
                "quality-metrics-analyst",
                "testing",
                "Quality tracking for complex projects",
                "recommended",
            )

        if "microservices" in analysis.get("architecture", []):
            # Microservices need special attention
            self._promote_agent(
                recommendations, "integration-architect", "strongly_recommended"
            )

        return recommendations

    def _promote_agent(
        self,
        recommendations: Dict,
        agent_name: str,
        target_level: str = "strongly_recommended",
    ):
        """Promote an agent to a higher recommendation level."""
        # Find and move the agent
        for level in ["optional", "recommended", "strongly_recommended"]:
            for i, agent in enumerate(recommendations[level]):
                if agent["name"] == agent_name:
                    if level != target_level:
                        agent = recommendations[level].pop(i)
                        recommendations[target_level].append(agent)
                    return

    def _add_agent(
        self,
        recommendations: Dict,
        agent_name: str,
        category: str,
        reason: str,
        level: str = "recommended",
    ):
        """Add a new agent to recommendations if not already present."""
        # Check if already recommended
        for rec_level in recommendations.values():
            if any(agent["name"] == agent_name for agent in rec_level):
                return

        recommendations[level].append(
            {"name": agent_name, "category": category, "reason": reason}
        )

    def generate_phase_recommendations(self, phase: str, analysis: Dict) -> List[Dict]:
        """Recommend agents for specific project phases."""
        phase_agents = {
            "planning": [
                "solution-architect",
                "security-architect",
                "database-architect",
            ],
            "development": [
                "language-experts",
                "framework-specialists",
                "api-designer",
            ],
            "testing": ["test-manager", "test-strategist", "performance-tester"],
            "deployment": [
                "kubernetes-architect",
                "ci-cd-architect",
                "cloud-architects",
            ],
            "maintenance": [
                "process-auditor",
                "quality-metrics-analyst",
                "security-reviewer",
            ],
        }

        recommendations = []

        if phase in phase_agents:
            for agent_type in phase_agents[phase]:
                if agent_type == "language-experts":
                    # Add language-specific experts
                    for lang in analysis.get("languages", {}).keys():
                        agent_name = f"{lang}-expert"
                        if agent_name in self.agent_registry.get("languages", {}):
                            recommendations.append(
                                {
                                    "name": agent_name,
                                    "reason": f"Expert guidance for {lang} development",
                                }
                            )
                elif agent_type == "cloud-architects":
                    # Add cloud-specific architects
                    for platform in analysis.get("cloud_platforms", []):
                        agent_name = f"{platform}-solutions-architect"
                        recommendations.append(
                            {
                                "name": agent_name,
                                "reason": f"{platform.upper()} optimization and best practices",
                            }
                        )
                else:
                    recommendations.append(
                        {"name": agent_type, "reason": f"Critical for {phase} phase"}
                    )

        return recommendations


def display_recommendations(recommendations: Dict[str, List[Dict]], analysis: Dict):
    """Display agent recommendations in a nice format."""
    console.print("\n[bold green]AI Agent Recommendations[/bold green]\n")

    # Summary panel
    total = sum(len(agents) for agents in recommendations.values())
    summary = f"Based on your {analysis.get('primary_language', 'multi-language')} "
    summary += f"{', '.join(analysis.get('project_types', ['general']))} project"
    if analysis.get("frameworks"):
        summary += f" using {', '.join(list(analysis['frameworks'])[:2])}"
    summary += f"\nRecommending {total} specialized AI agents"

    console.print(Panel(summary, title="Analysis Summary", border_style="blue"))
    console.print()

    # Recommendations by priority
    priority_colors = {
        "essential": "red",
        "strongly_recommended": "yellow",
        "recommended": "green",
        "optional": "cyan",
    }

    priority_labels = {
        "essential": "🔴 Essential (Required for AI-First SDLC)",
        "strongly_recommended": "🟡 Strongly Recommended",
        "recommended": "🟢 Recommended",
        "optional": "🔵 Optional",
    }

    for priority, agents in recommendations.items():
        if agents:
            console.print(f"[bold]{priority_labels[priority]}[/bold]")

            table = Table(show_header=True, box=None, padding=(0, 2))
            table.add_column("Agent", style=priority_colors[priority])
            table.add_column("Category", style="dim")
            table.add_column("Reason")

            for agent in agents:
                table.add_row(agent["name"], agent["category"], agent["reason"])

            console.print(table)
            console.print()

    # Installation command
    console.print("[bold]To install these agents:[/bold]")
    console.print("[dim]python tools/automation/agent-installer.py[/dim]")
    console.print()


@click.command()
@click.option(
    "--analysis-file", type=click.Path(exists=True), help="Project analysis JSON file"
)
@click.option(
    "--project-dir",
    type=click.Path(exists=True),
    default=".",
    help="Project directory (will analyze if no analysis file)",
)
@click.option("--objectives", help="Project objectives/goals")
@click.option(
    "--phase",
    type=click.Choice(
        ["planning", "development", "testing", "deployment", "maintenance"]
    ),
    help="Current project phase",
)
@click.option("--output", type=click.Path(), help="Save recommendations to JSON")
def main(analysis_file, project_dir, objectives, phase, output):
    """Recommend AI agents based on project analysis and objectives."""

    # Load or generate analysis
    if analysis_file:
        with open(analysis_file) as f:
            analysis = json.load(f)
    else:
        # Run analysis
        from project_analyzer import ProjectAnalyzer

        console.print("[dim]Analyzing project...[/dim]\n")
        analyzer = ProjectAnalyzer(Path(project_dir))
        analysis = analyzer.analyze()

    # Generate recommendations
    recommender = AgentRecommender()
    recommendations = recommender.recommend(analysis, objectives)

    # Add phase-specific recommendations if provided
    if phase:
        phase_recs = recommender.generate_phase_recommendations(phase, analysis)
        if phase_recs:
            console.print(f"\n[bold]Additional agents for {phase} phase:[/bold]")
            for rec in phase_recs:
                console.print(f"  • {rec['name']}: {rec['reason']}")

    # Display recommendations
    display_recommendations(recommendations, analysis)

    # Save if requested
    if output:
        _output_data =
            "analysis_summary": {
                "primary_language": analysis.get("primary_language"),
                "project_types": list(analysis.get("project_types", [])),
                "frameworks": list(analysis.get("frameworks", [])),
                "team_size": analysis.get("team_size", 1),
                "project_size": analysis.get("project_size", "unknown"),
            },
            "recommendations": recommendations,
            "objectives": objectives,
            "phase": phase,
        }

        with open(output, "w") as f:
            json.dump(output_data, f, indent=2)
        console.print(f"[green]Recommendations saved to: {output}[/green]")


if __name__ == "__main__":
    main()
