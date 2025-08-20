#!/usr/bin/env python3
"""
Team Discovery Tool - AI Team Orchestration System

Provides interactive assessment to determine optimal AI agent team formation
for software development projects.
"""

import json
import click
from pathlib import Path
from typing import Dict, List, Tuple, Any


class ProjectArchetype:
    """Represents a project archetype with its characteristics"""

    def __init__(
        self,
        name: str,
        description: str,
        formation: str,
        core_agents: List[str],
        characteristics: Dict[str, Any],
    ):
        self.name = name
        self.description = description
        self.formation = formation
        self.core_agents = core_agents
        self.characteristics = characteristics


# Project Archetypes Definition
ARCHETYPES = {
    "builder": ProjectArchetype(
        name="The Builder",
        description="Simple applications, MVPs, proof of concepts",
        formation="3-3-2",
        core_agents=[
            "sdlc-enforcer",
            "solution-architect",
            "critical-goal-reviewer",
            "language-expert",
            "test-manager",
            "technical-writer",
        ],
        characteristics={
            "complexity": "low",
            "integrations": "0-2",
            "team_size": "small",
            "requirements_stability": "high",
        },
    ),
    "specialist": ProjectArchetype(
        name="The Specialist",
        description="Domain-specific applications, specialized requirements",
        formation="4-3-2",
        core_agents=[
            "sdlc-enforcer",
            "solution-architect",
            "critical-goal-reviewer",
            "domain-specialist",
            "compliance-auditor",
            "language-expert",
            "test-manager",
            "technical-writer",
            "devops-specialist",
        ],
        characteristics={
            "complexity": "medium",
            "integrations": "2-4",
            "team_size": "medium",
            "requirements_stability": "medium",
        },
    ),
    "innovator": ProjectArchetype(
        name="The Innovator",
        description="AI/ML applications, cutting-edge technology",
        formation="4-4-2",
        core_agents=[
            "sdlc-enforcer",
            "ai-solution-architect",
            "critical-goal-reviewer",
            "prompt-engineer",
            "langchain-architect",
            "ai-test-engineer",
            "performance-engineer",
            "language-expert",
            "test-manager",
            "devops-specialist",
        ],
        characteristics={
            "complexity": "high",
            "integrations": "3-6",
            "team_size": "medium-large",
            "requirements_stability": "low-medium",
        },
    ),
    "transformer": ProjectArchetype(
        name="The Transformer",
        description="Enterprise integration, high compliance requirements",
        formation="3-5-2",
        core_agents=[
            "sdlc-enforcer",
            "solution-architect",
            "critical-goal-reviewer",
            "integration-orchestrator",
            "devops-specialist",
            "sre-specialist",
            "security-specialist",
            "compliance-auditor",
            "performance-engineer",
            "language-expert",
        ],
        characteristics={
            "complexity": "high",
            "integrations": "4-8",
            "team_size": "large",
            "requirements_stability": "medium-high",
        },
    ),
    "orchestrator": ProjectArchetype(
        name="The Orchestrator",
        description="Multi-agent systems, extreme complexity",
        formation="4-4-2-1",
        core_agents=[
            "sdlc-enforcer",
            "orchestration-architect",
            "a2a-architect",
            "agent-developer",
            "mcp-server-architect",
            "integration-orchestrator",
            "ai-solution-architect",
            "performance-engineer",
            "devops-specialist",
            "sre-specialist",
            "critical-goal-reviewer",
            "mcp-quality-assurance",
        ],
        characteristics={
            "complexity": "extreme",
            "integrations": "9+",
            "team_size": "large",
            "requirements_stability": "low",
        },
    ),
}


class TeamDiscoveryEngine:
    """Core engine for discovering optimal team formations"""

    def __init__(self):
        self.responses = {}
        self.scores = {archetype: 0 for archetype in ARCHETYPES.keys()}

    def ask_question(
        self, question: str, options: List[Tuple[str, Dict[str, int]]]
    ) -> str:
        """Ask a question and return the selected option"""
        click.echo(f"\n{question}")
        for i, (option, _) in enumerate(options, 1):
            click.echo(f"{i}. {option}")

        while True:
            try:
                choice = click.prompt("Select option (number)", type=int)
                if 1 <= choice <= len(options):
                    selected_option, scoring = options[choice - 1]
                    # Update archetype scores based on this answer
                    for archetype, points in scoring.items():
                        self.scores[archetype] += points
                    return selected_option
                else:
                    click.echo(f"Please enter a number between 1 and {len(options)}")
            except click.Abort:
                raise
            except BaseException:
                click.echo("Please enter a valid number")

    def run_assessment(self) -> str:
        """Run the complete team discovery assessment"""
        click.echo("=== AI Team Discovery Assessment ===")
        click.echo(
            "Answer the following questions to discover your optimal team formation"
        )

        # Question 1: Project Type
        self.responses["project_type"] = self.ask_question(
            "What type of application are you building?",
            [
                ("Simple CRUD application or MVP", {"builder": 3, "specialist": 1}),
                (
                    "Domain-specific application (fintech, healthcare, etc.)",
                    {"specialist": 3, "transformer": 1},
                ),
                (
                    "AI/ML application or AI-enhanced features",
                    {"innovator": 3, "orchestrator": 1},
                ),
                (
                    "Enterprise integration or microservices",
                    {"transformer": 3, "orchestrator": 1},
                ),
                (
                    "Multi-agent system or agent-to-agent communication",
                    {"orchestrator": 3, "innovator": 1},
                ),
            ],
        )

        # Question 2: Integration Complexity
        self.responses["integrations"] = self.ask_question(
            "How many external systems will you integrate with?",
            [
                (
                    "0-1 systems (mostly self-contained)",
                    {"builder": 2, "specialist": 1},
                ),
                (
                    "2-3 systems (moderate integration)",
                    {"specialist": 2, "innovator": 1, "transformer": 1},
                ),
                (
                    "4-6 systems (complex integration)",
                    {"transformer": 2, "orchestrator": 1, "innovator": 1},
                ),
                (
                    "7+ systems (enterprise-scale integration)",
                    {"orchestrator": 3, "transformer": 2},
                ),
            ],
        )

        # Question 3: Technical Complexity
        self.responses["complexity"] = self.ask_question(
            "What's the technical complexity of your project?",
            [
                (
                    "Low - Well-understood patterns and technologies",
                    {"builder": 3, "specialist": 1},
                ),
                (
                    "Medium - Some new technologies, moderate challenges",
                    {"specialist": 2, "innovator": 1, "transformer": 1},
                ),
                (
                    "High - Cutting-edge tech, significant technical challenges",
                    {"innovator": 3, "orchestrator": 1},
                ),
                (
                    "Extreme - Research-level problems, unprecedented challenges",
                    {"orchestrator": 3, "innovator": 2},
                ),
            ],
        )

        # Question 4: Compliance Requirements
        self.responses["compliance"] = self.ask_question(
            "What are your regulatory/compliance requirements?",
            [
                ("None or minimal compliance needs", {"builder": 2, "innovator": 1}),
                (
                    "Standard industry compliance (basic security, etc.)",
                    {"specialist": 2, "innovator": 1},
                ),
                (
                    "Heavy compliance (SOX, HIPAA, PCI-DSS, etc.)",
                    {"transformer": 3, "specialist": 1},
                ),
                (
                    "Extreme compliance (government, defense, finance)",
                    {"transformer": 3, "orchestrator": 1},
                ),
            ],
        )

        # Question 5: Team Collaboration Needs
        self.responses["collaboration"] = self.ask_question(
            "How complex will the AI agent collaboration be?",
            [
                (
                    "Simple - Agents work mostly independently",
                    {"builder": 2, "specialist": 1},
                ),
                (
                    "Moderate - Some coordination between agents needed",
                    {"specialist": 2, "innovator": 1},
                ),
                (
                    "Complex - Frequent agent-to-agent communication",
                    {"innovator": 2, "transformer": 1, "orchestrator": 1},
                ),
                (
                    "Extreme - Agents must orchestrate complex workflows",
                    {"orchestrator": 3, "transformer": 1},
                ),
            ],
        )

        # Question 6: Performance Requirements
        self.responses["performance"] = self.ask_question(
            "What are your performance and scalability requirements?",
            [
                (
                    "Basic - Handle expected load without issues",
                    {"builder": 2, "specialist": 1},
                ),
                (
                    "Moderate - Good performance under normal conditions",
                    {"specialist": 2, "innovator": 1},
                ),
                (
                    "High - Must perform well under heavy load",
                    {"transformer": 2, "innovator": 2, "orchestrator": 1},
                ),
                (
                    "Extreme - Mission-critical performance requirements",
                    {"orchestrator": 3, "transformer": 2},
                ),
            ],
        )

        # Question 7: Change Tolerance
        self.responses["change_tolerance"] = self.ask_question(
            "How frequently do you expect requirements to change?",
            [
                (
                    "Rarely - Requirements are well-defined and stable",
                    {"builder": 2, "transformer": 1},
                ),
                (
                    "Occasionally - Some changes expected",
                    {"specialist": 2, "builder": 1},
                ),
                (
                    "Frequently - Agile environment with regular changes",
                    {"innovator": 2, "specialist": 1},
                ),
                (
                    "Constantly - Experimental/research environment",
                    {"orchestrator": 2, "innovator": 2},
                ),
            ],
        )

        # Determine winning archetype
        winning_archetype = max(self.scores.items(), key=lambda x: x[1])
        return winning_archetype[0]

    def generate_recommendations(self, archetype_key: str) -> Dict[str, Any]:
        """Generate detailed recommendations for the selected archetype"""
        archetype = ARCHETYPES[archetype_key]

        # Calculate installation phases
        core_agents = archetype.core_agents[:3]  # First 3 are always core
        phase_2_agents = (
            archetype.core_agents[3:6] if len(archetype.core_agents) > 3 else []
        )
        phase_3_agents = (
            archetype.core_agents[6:9] if len(archetype.core_agents) > 6 else []
        )
        phase_4_agents = (
            archetype.core_agents[9:] if len(archetype.core_agents) > 9 else []
        )

        return {
            "archetype": archetype.name,
            "description": archetype.description,
            "formation": archetype.formation,
            "total_agents": len(archetype.core_agents),
            "installation_phases": {
                "phase_1_foundation": {
                    "agents": core_agents,
                    "timeline": "Days 1-3",
                    "description": "Essential foundation agents",
                },
                "phase_2_specialization": {
                    "agents": phase_2_agents,
                    "timeline": "Days 4-7",
                    "description": "Domain-specific expertise",
                },
                "phase_3_quality": {
                    "agents": phase_3_agents,
                    "timeline": "Days 8-14",
                    "description": "Quality and operational support",
                },
                "phase_4_optimization": {
                    "agents": phase_4_agents,
                    "timeline": "Days 15+",
                    "description": "Full formation optimization",
                },
            },
            "characteristics": archetype.characteristics,
            "readiness_criteria": self._get_readiness_criteria(archetype_key),
            "chemistry_exercises": self._get_chemistry_exercises(archetype_key),
        }

    def _get_readiness_criteria(self, archetype_key: str) -> List[str]:
        """Get readiness criteria specific to this archetype"""
        base_criteria = [
            "Core trio (sdlc-enforcer, solution-architect, critical-goal-reviewer) installed and responsive",
            "Basic workflow completes without errors",
            "Clean handoff protocols demonstrated",
        ]

        archetype_criteria = {
            "builder": [
                "Simple feature implementation succeeds",
                "Documentation generation works",
                "Basic testing pipeline functional",
            ],
            "specialist": [
                "Domain-specific validation passes",
                "Compliance checks functional",
                "Integration testing pipeline ready",
            ],
            "innovator": [
                "AI/ML workflow pipeline functional",
                "Prompt engineering validation works",
                "AI testing capabilities verified",
            ],
            "transformer": [
                "Enterprise integration patterns work",
                "Security and compliance gates active",
                "Production deployment pipeline ready",
            ],
            "orchestrator": [
                "Agent-to-agent communication functional",
                "Complex orchestration patterns work",
                "Multi-system integration validated",
            ],
        }

        return base_criteria + archetype_criteria.get(archetype_key, [])

    def _get_chemistry_exercises(self, archetype_key: str) -> List[Dict[str, str]]:
        """Get chemistry development exercises for this archetype"""
        base_exercises = [
            {
                "name": "Simple Feature Challenge",
                "description": "Implement a basic CRUD endpoint with full team collaboration",
                "agents": "Core trio",
                "success_criteria": "Clean handoffs, no duplicated effort, all agents contribute",
            }
        ]

        archetype_exercises = {
            "builder": [
                {
                    "name": "Documentation Flow",
                    "description": "Create feature documentation with technical-writer integration",
                    "agents": "solution-architect, language-expert, technical-writer",
                    "success_criteria": "Complete docs generated, review process smooth",
                }
            ],
            "specialist": [
                {
                    "name": "Compliance Validation",
                    "description": "Implement feature with full compliance checking",
                    "agents": "domain-specialist, compliance-auditor, solution-architect",
                    "success_criteria": "All compliance gates pass, domain rules enforced",
                }
            ],
            "innovator": [
                {
                    "name": "AI Pipeline Integration",
                    "description": "Implement AI feature with testing and optimization",
                    "agents": "ai-solution-architect, prompt-engineer, ai-test-engineer",
                    "success_criteria": "AI functionality works, tests comprehensive, performance acceptable",
                }
            ],
            "transformer": [
                {
                    "name": "Multi-System Integration",
                    "description": "Connect to external API with full error handling and monitoring",
                    "agents": "integration-orchestrator, sre-specialist, devops-specialist",
                    "success_criteria": "Robust integration, monitoring active, failure handling works",
                }
            ],
            "orchestrator": [
                {
                    "name": "Agent Orchestration Challenge",
                    "description": "Coordinate multiple agents on complex multi-step workflow",
                    "agents": "orchestration-architect, a2a-architect, agent-developer",
                    "success_criteria": "Complex workflow completes, agent coordination seamless",
                }
            ],
        }

        return base_exercises + archetype_exercises.get(archetype_key, [])


@click.command()
@click.option("--interactive", is_flag=True, help="Run interactive assessment")
@click.option("--output", type=click.Path(), help="Output file for recommendations")
@click.option(
    "--format",
    type=click.Choice(["json", "markdown"]),
    default="markdown",
    help="Output format",
)
def main(interactive: bool, output: str, format: str):
    """AI Team Discovery Tool - Find your perfect agent team formation"""

    if not interactive:
        click.echo("Use --interactive to run the team discovery assessment")
        return

    try:
        engine = TeamDiscoveryEngine()
        winning_archetype = engine.run_assessment()
        recommendations = engine.generate_recommendations(winning_archetype)

        if format == "json":
            output_content = json.dumps(recommendations, indent=2)
        else:
            output_content = generate_markdown_report(
                recommendations, engine.responses, engine.scores
            )

        if output:
            Path(output).write_text(output_content)
            click.echo(f"\nRecommendations saved to {output}")
        else:
            click.echo("\n" + "=" * 60)
            click.echo(output_content)

        # Show next steps
        click.echo("\n🎯 Next Steps:")
        click.echo(f"1. Review the {recommendations['archetype']} formation details")
        click.echo(
            f"2. Install Phase 1 agents: {', '.join(recommendations['installation_phases']['phase_1_foundation']['agents'])}"
        )
        click.echo(
            f"3. Run: python tools/automation/validate-team-readiness.py --formation {winning_archetype}"
        )
        click.echo("4. Begin chemistry development exercises")

    except click.Abort:
        click.echo("\nAssessment cancelled.")
    except Exception as e:
        click.echo(f"Error: {e}")


def generate_markdown_report(
    recommendations: Dict[str, Any], responses: Dict[str, str], scores: Dict[str, int]
) -> str:
    """Generate a markdown report of the team discovery results"""

    report = """# AI Team Discovery Report

## Recommended Formation: {recommendations['archetype']}

**Formation Pattern**: {recommendations['formation']}
**Total Agents**: {recommendations['total_agents']}

### Description
{recommendations['description']}

## Installation Plan

### Phase 1: Foundation ({recommendations['installation_phases']['phase_1_foundation']['timeline']})
**Agents**: {', '.join(recommendations['installation_phases']['phase_1_foundation']['agents'])}
**Focus**: {recommendations['installation_phases']['phase_1_foundation']['description']}

### Phase 2: Specialization ({recommendations['installation_phases']['phase_2_specialization']['timeline']})
**Agents**: {', '.join(recommendations['installation_phases']['phase_2_specialization']['agents'])}
**Focus**: {recommendations['installation_phases']['phase_2_specialization']['description']}

### Phase 3: Quality & Operations ({recommendations['installation_phases']['phase_3_quality']['timeline']})
**Agents**: {', '.join(recommendations['installation_phases']['phase_3_quality']['agents'])}
**Focus**: {recommendations['installation_phases']['phase_3_quality']['description']}

### Phase 4: Full Formation ({recommendations['installation_phases']['phase_4_optimization']['timeline']})
**Agents**: {', '.join(recommendations['installation_phases']['phase_4_optimization']['agents'])}
**Focus**: {recommendations['installation_phases']['phase_4_optimization']['description']}

## Readiness Criteria

Your team will be ready when:
"""

    for i, criterion in enumerate(recommendations["readiness_criteria"], 1):
        report += f"{i}. {criterion}\n"

    report += "\n## Chemistry Development Exercises\n\n"

    for exercise in recommendations["chemistry_exercises"]:
        report += f"### {exercise['name']}\n"
        report += f"**Description**: {exercise['description']}\n"
        report += f"**Agents**: {exercise['agents']}\n"
        report += f"**Success Criteria**: {exercise['success_criteria']}\n\n"

    report += "## Assessment Summary\n\n"
    report += "### Your Responses\n"
    for question, answer in responses.items():
        report += f"- **{question.replace('_', ' ').title()}**: {answer}\n"

    report += "\n### Archetype Scores\n"
    for archetype, score in sorted(scores.items(), key=lambda x: x[1], reverse=True):
        archetype_name = ARCHETYPES[archetype].name
        report += f"- **{archetype_name}**: {score} points\n"

    report += """
## Next Steps

1. **Install Foundation Agents**: Start with the Phase 1 agents to establish your core team
2. **Validate Readiness**: Use the readiness criteria to ensure each phase is successful
3. **Develop Team Chemistry**: Complete the chemistry exercises to optimize collaboration
4. **Monitor Performance**: Track team metrics and adjust formation as needed

## Commands to Run

```bash
# Validate team readiness after each phase
python tools/automation/validate-team-readiness.py --formation {list(scores.keys())[0]}

# Run chemistry development exercises
python tools/automation/team-chemistry.py --exercise simple-feature-challenge

# Monitor team performance
python tools/automation/team-dashboard.py --live
```

Remember: The perfect team formation is the one that fits your specific project's needs!
"""

    return report


if __name__ == "__main__":
    main()
