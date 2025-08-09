#!/usr/bin/env python3
"""Agent Help - Quick agent discovery and installation

Simple commands to get agent help when you need it:
- agent-help                  # Show this help
- agent-help testing         # Find testing-related agents
- agent-help performance     # Find performance agents
- agent-help security        # Find security agents
- agent-help <challenge>     # Find agents for any challenge
"""

import sys
from pathlib import Path
from typing import List, Dict
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

# Agent catalog with keywords and use cases
AGENT_CATALOG = {
    "sdlc-enforcer": {
        "keywords": [
            "process",
            "workflow",
            "sdlc",
            "framework",
            "compliance",
            "best practices",
            "enforcement",
        ],
        "helps_with": "Framework compliance, process improvement, workflow optimization, GitHub integration",
        "when_to_use": "When unsure about AI-First SDLC practices or need process guidance",
    },
    "test-manager": {
        "keywords": ["testing", "test", "quality", "qa", "coverage", "test strategy"],
        "helps_with": "Test strategy, coverage analysis, quality metrics, test coordination",
        "when_to_use": "Planning testing approach or managing test activities",
    },
    "solution-architect": {
        "keywords": [
            "architecture",
            "design",
            "system",
            "scalability",
            "integration",
            "technology",
        ],
        "helps_with": "System design, technology selection, architecture decisions, scalability",
        "when_to_use": "Designing new features or making architectural decisions",
    },
    "security-architect": {
        "keywords": [
            "security",
            "threat",
            "vulnerability",
            "authentication",
            "authorization",
            "compliance",
        ],
        "helps_with": "Security design, threat modeling, compliance requirements, secure coding",
        "when_to_use": "Implementing security features or addressing vulnerabilities",
    },
    "language-python-expert": {
        "keywords": [
            "python",
            "pythonic",
            "pep",
            "django",
            "flask",
            "fastapi",
            "pytest",
            "zero-debt",
        ],
        "helps_with": "Python best practices, code optimization, framework guidance, AI-First SDLC integration",
        "when_to_use": "Writing Python code or solving Python-specific challenges with Zero Technical Debt",
    },
    "javascript-expert": {
        "keywords": [
            "javascript",
            "js",
            "typescript",
            "node",
            "npm",
            "webpack",
            "babel",
        ],
        "helps_with": "JavaScript patterns, TypeScript, Node.js, build tools",
        "when_to_use": "JavaScript development or frontend/backend JS challenges",
    },
    "react-architect": {
        "keywords": [
            "react",
            "hooks",
            "redux",
            "context",
            "component",
            "jsx",
            "frontend",
        ],
        "helps_with": "React patterns, state management, performance optimization",
        "when_to_use": "Building React applications or solving React-specific issues",
    },
    "api-designer": {
        "keywords": ["api", "rest", "graphql", "endpoint", "swagger", "openapi"],
        "helps_with": "API design, RESTful patterns, GraphQL schemas, API documentation",
        "when_to_use": "Designing APIs or improving API architecture",
    },
    "database-architect": {
        "keywords": [
            "database",
            "sql",
            "nosql",
            "schema",
            "query",
            "optimization",
            "migration",
        ],
        "helps_with": "Database design, query optimization, schema migrations, scaling",
        "when_to_use": "Database design or performance issues",
    },
    "kubernetes-architect": {
        "keywords": [
            "kubernetes",
            "k8s",
            "container",
            "docker",
            "helm",
            "deployment",
            "scaling",
        ],
        "helps_with": "K8s deployments, container orchestration, scaling strategies",
        "when_to_use": "Deploying to Kubernetes or container orchestration",
    },
    "performance-reviewer": {
        "keywords": [
            "performance",
            "speed",
            "optimization",
            "slow",
            "bottleneck",
            "profiling",
        ],
        "helps_with": "Performance analysis, optimization strategies, bottleneck identification",
        "when_to_use": "Application is slow or needs performance improvement",
    },
    "ml-architect": {
        "keywords": [
            "machine learning",
            "ml",
            "ai",
            "model",
            "training",
            "mlops",
            "tensorflow",
            "pytorch",
        ],
        "helps_with": "ML system design, model architecture, MLOps, deployment strategies",
        "when_to_use": "Building ML systems or integrating AI capabilities",
    },
    "frontend-performance": {
        "keywords": [
            "frontend",
            "performance",
            "lighthouse",
            "core web vitals",
            "loading",
            "rendering",
        ],
        "helps_with": "Frontend optimization, bundle size, loading performance, rendering",
        "when_to_use": "Improving web application performance",
    },
    "accessibility-expert": {
        "keywords": [
            "accessibility",
            "a11y",
            "wcag",
            "screen reader",
            "aria",
            "inclusive",
        ],
        "helps_with": "WCAG compliance, accessibility testing, inclusive design",
        "when_to_use": "Making applications accessible to all users",
    },
    "ci-cd-architect": {
        "keywords": [
            "cicd",
            "pipeline",
            "automation",
            "deployment",
            "github actions",
            "jenkins",
        ],
        "helps_with": "Pipeline design, deployment automation, CI/CD best practices",
        "when_to_use": "Setting up or optimizing CI/CD pipelines",
    },
    "critical-goal-reviewer": {
        "keywords": [
            "review",
            "goals",
            "requirements",
            "validation",
            "alignment",
            "devil advocate",
        ],
        "helps_with": "Goal alignment review, requirement validation, gap identification",
        "when_to_use": "After completing features to ensure alignment with original goals",
    },
    "ai-first-kick-starter": {
        "keywords": [
            "setup",
            "kickstart",
            "framework",
            "sdlc",
            "initialization",
            "bootstrap",
        ],
        "helps_with": "AI-First SDLC framework setup, project initialization, directory structure",
        "when_to_use": "Setting up AI-First SDLC practices in a new or existing project",
    },
    "github-integration-specialist": {
        "keywords": [
            "github",
            "git",
            "pr",
            "branch",
            "protection",
            "repository",
            "api",
        ],
        "helps_with": "GitHub API operations, repository management, PR automation, branch protection",
        "when_to_use": "Automating GitHub workflows or repository management",
    },
    "ai-solution-architect": {
        "keywords": [
            "ai",
            "ml",
            "machine learning",
            "llm",
            "architecture",
            "mlops",
            "models",
        ],
        "helps_with": "AI/ML system design, architecture review, best practices validation",
        "when_to_use": "Designing or reviewing AI/ML systems and implementations",
    },
    "project-plan-tracker": {
        "keywords": [
            "project",
            "plan",
            "tracking",
            "progress",
            "deliverables",
            "timeline",
        ],
        "helps_with": "Project progress monitoring, plan adherence, deliverable tracking",
        "when_to_use": "Monitoring project execution against established plans",
    },
}


def find_agents(query: str) -> List[Dict]:
    """Find agents matching the query."""
    query_lower = query.lower()
    query_words = query_lower.split()

    matches = []

    for agent_name, agent_info in AGENT_CATALOG.items():
        score = 0

        # Check keywords
        for keyword in agent_info["keywords"]:
            if keyword in query_lower:
                score += 10
            elif any(word in keyword for word in query_words):
                score += 5

        # Check helps_with
        if any(word in agent_info["helps_with"].lower() for word in query_words):
            score += 3

        # Check when_to_use
        if any(word in agent_info["when_to_use"].lower() for word in query_words):
            score += 2

        if score > 0:
            matches.append(
                {
                    "name": agent_name,
                    "score": score,
                    "helps_with": agent_info["helps_with"],
                    "when_to_use": agent_info["when_to_use"],
                }
            )

    # Sort by score
    matches.sort(key=lambda x: x["score"], reverse=True)
    return matches[:5]  # Top 5 matches


def show_quick_help():
    """Show quick help for common scenarios."""
    scenarios = [
        ("🧪 Testing", "agent-help testing"),
        ("⚡ Performance", "agent-help performance"),
        ("🔒 Security", "agent-help security"),
        ("🏗️ Architecture", "agent-help architecture"),
        ("🐍 Python", "agent-help python"),
        ("📱 Frontend", "agent-help frontend"),
        ("☁️ Cloud/K8s", "agent-help kubernetes"),
        ("🤖 AI/ML", "agent-help machine learning"),
    ]

    console.print(
        Panel.fit(
            "[bold]Quick Agent Discovery[/bold]\n\n"
            "Find the right AI agent for your challenge:\n\n"
            + "\n".join(
                f"  {icon} {name:<15} → {cmd}"
                for (name, cmd), (icon, _) in zip(
                    [(s[0].replace(s[0].split()[0], s[0].split()[0][2:]), s[1]) for s in scenarios],
                    scenarios,
                )
            ),
            border_style="blue",
        )
    )

    console.print('\n[dim]Or describe your challenge: agent-help "optimize database queries"[/dim]')


def check_installed(agent_name: str) -> bool:
    """Check if an agent is already installed."""
    manifest_path = Path.cwd() / ".agent-manifest.json"
    if manifest_path.exists():
        import json

        with open(manifest_path) as f:
            manifest = json.load(f)
        return agent_name in manifest
    return False


@click.command()
@click.argument("query", nargs=-1)
@click.option("--install", "-i", is_flag=True, help="Install recommended agent")
def main(query, install):
    """Find AI agents to help with your development challenges."""

    if not query:
        show_quick_help()
        return

    query_str = " ".join(query)
    console.print(f"\n[bold]Searching for agents to help with:[/bold] {query_str}\n")

    matches = find_agents(query_str)

    if not matches:
        console.print("[yellow]No specific agents found for that query.[/yellow]")
        console.print("Try: agent-help testing, security, performance, or architecture")
        return

    # Display matches
    table = Table(show_header=True, title="Recommended Agents")
    table.add_column("Agent", style="cyan", width=20)
    table.add_column("Helps With", width=40)
    table.add_column("Status", width=12)

    for match in matches:
        status = "[green]Installed[/green]" if check_installed(match["name"]) else "[dim]Available[/dim]"
        table.add_row(match["name"], match["helps_with"], status)

    console.print(table)

    # Show when to use
    best_match = matches[0]
    console.print(f"\n[bold]Best match:[/bold] {best_match['name']}")
    console.print(f"[dim]Use when:[/dim] {best_match['when_to_use']}")

    # Installation instructions
    if not check_installed(best_match["name"]):
        console.print("\n[bold]To install:[/bold]")
        console.print(f"  python tools/automation/agent-installer.py --install {best_match['name']}")

        if install:
            console.print("\n[dim]Installing agent...[/dim]")
            import subprocess

            result = subprocess.run(
                [
                    sys.executable,
                    "tools/automation/agent-installer.py",
                    "--install",
                    best_match["name"],
                ],
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                console.print(f"[green]✓ Installed {best_match['name']}[/green]")
            else:
                console.print("[red]Failed to install. Run manually:[/red]")
                console.print(f"  python tools/automation/agent-installer.py --install {best_match['name']}")
    else:
        console.print(f"\n[green]✓ {best_match['name']} is already installed![/green]")
        console.print(f"[dim]Use with: @{best_match['name']}[/dim]")


if __name__ == "__main__":
    main()
