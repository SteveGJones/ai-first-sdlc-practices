#!/usr/bin/env python3
"""
Team Readiness Validation Tool - AI Team Orchestration System

Validates whether an AI agent team is ready for production work based on
formation requirements, chemistry metrics, and performance indicators.
"""

import json
import click
import subprocess
from pathlib import Path
from typing import Dict, List, Any
from dataclasses import dataclass
from enum import Enum


class ReadinessLevel(Enum):
    """Team readiness levels"""

    GREEN = "ready"
    YELLOW = "needs_improvement"
    RED = "not_ready"


@dataclass
class ValidationResult:
    """Result of a single validation check"""

    name: str
    passed: bool
    score: float
    details: str
    recommendations: List[str]


@dataclass
class TeamReadinessReport:
    """Complete team readiness assessment"""

    formation_type: str
    overall_readiness: ReadinessLevel
    overall_score: float
    foundation_metrics: List[ValidationResult]
    formation_metrics: List[ValidationResult]
    chemistry_metrics: List[ValidationResult]
    recommendations: List[str]
    next_steps: List[str]


class TeamReadinessValidator:
    """Core validator for AI agent team readiness"""

    def __init__(self, formation_type: str):
        self.formation_type = formation_type
        self.formation_configs = self._load_formation_configs()
        self.agents_available = self._detect_available_agents()

    def _load_formation_configs(self) -> Dict[str, Any]:
        """Load formation configuration data"""
        return {
            "builder": {
                "required_agents": [
                    "sdlc-enforcer",
                    "solution-architect",
                    "critical-goal-reviewer",
                    "language-expert",
                    "test-manager",
                    "technical-writer",
                ],
                "formation": "3-3-2",
                "min_agents": 6,
                "chemistry_thresholds": {
                    "communication": 0.8,
                    "role_clarity": 0.85,
                    "collaboration": 0.75,
                    "quality": 0.9,
                },
            },
            "specialist": {
                "required_agents": [
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
                "formation": "4-3-2",
                "min_agents": 9,
                "chemistry_thresholds": {
                    "communication": 0.8,
                    "role_clarity": 0.85,
                    "collaboration": 0.75,
                    "quality": 0.9,
                },
            },
            "innovator": {
                "required_agents": [
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
                "formation": "4-4-2",
                "min_agents": 10,
                "chemistry_thresholds": {
                    "communication": 0.85,
                    "role_clarity": 0.85,
                    "collaboration": 0.8,
                    "quality": 0.92,
                },
            },
            "transformer": {
                "required_agents": [
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
                "formation": "3-5-2",
                "min_agents": 10,
                "chemistry_thresholds": {
                    "communication": 0.85,
                    "role_clarity": 0.9,
                    "collaboration": 0.8,
                    "quality": 0.95,
                },
            },
            "orchestrator": {
                "required_agents": [
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
                "formation": "4-4-2-1",
                "min_agents": 12,
                "chemistry_thresholds": {
                    "communication": 0.9,
                    "role_clarity": 0.9,
                    "collaboration": 0.85,
                    "quality": 0.95,
                },
            },
        }

    def _detect_available_agents(self) -> List[str]:
        """Detect which agents are currently available/installed"""
        # In a real implementation, this would query the AI platform
        # For now, we'll simulate this by checking for agent definition files
        agents_dir = Path("agents")
        if agents_dir.exists():
            return [f.stem for f in agents_dir.glob("*.md")]
        return []

    def validate_foundation_metrics(self) -> List[ValidationResult]:
        """Validate foundation readiness metrics"""
        results = []

        # Core trio availability
        core_trio = ["sdlc-enforcer", "solution-architect", "critical-goal-reviewer"]
        core_available = all(agent in self.agents_available for agent in core_trio)

        results.append(
            ValidationResult(
                name="Core Trio Installed",
                passed=core_available,
                score=1.0 if core_available else 0.0,
                details=f"Required: {core_trio}. Available: {[a for a in core_trio if a in self.agents_available]}",
                recommendations=(
                    []
                    if core_available
                    else ["Install missing core agents before proceeding"]
                ),
            )
        )

        # Basic workflow test
        workflow_result = self._test_basic_workflow()
        results.append(
            ValidationResult(
                name="Basic Workflow Test",
                passed=workflow_result["passed"],
                score=workflow_result["score"],
                details=workflow_result["details"],
                recommendations=workflow_result["recommendations"],
            )
        )

        # Handoff protocol test
        handoff_result = self._test_handoff_protocol()
        results.append(
            ValidationResult(
                name="Handoff Protocol",
                passed=handoff_result["passed"],
                score=handoff_result["score"],
                details=handoff_result["details"],
                recommendations=handoff_result["recommendations"],
            )
        )

        return results

    def validate_formation_metrics(self) -> List[ValidationResult]:
        """Validate formation-specific readiness metrics"""
        results = []

        if self.formation_type not in self.formation_configs:
            results.append(
                ValidationResult(
                    name="Formation Configuration",
                    passed=False,
                    score=0.0,
                    details=f"Unknown formation type: {self.formation_type}",
                    recommendations=[
                        f"Use one of: {list(self.formation_configs.keys())}"
                    ],
                )
            )
            return results

        config = self.formation_configs[self.formation_type]

        # All required agents installed
        required_agents = config["required_agents"]
        missing_agents = [
            agent for agent in required_agents if agent not in self.agents_available
        ]
        agents_complete = len(missing_agents) == 0

        results.append(
            ValidationResult(
                name="All Agents Installed",
                passed=agents_complete,
                score=1.0 - (len(missing_agents) / len(required_agents)),
                details=f"Missing {len(missing_agents)}/{len(required_agents)} agents: {missing_agents}",
                recommendations=(
                    [f"Install missing agents: {', '.join(missing_agents)}"]
                    if missing_agents
                    else []
                ),
            )
        )

        # Formation workflow test
        workflow_result = self._test_formation_workflow()
        results.append(
            ValidationResult(
                name="Formation Workflow",
                passed=workflow_result["passed"],
                score=workflow_result["score"],
                details=workflow_result["details"],
                recommendations=workflow_result["recommendations"],
            )
        )

        # Role conflict detection
        conflict_result = self._detect_role_conflicts()
        results.append(
            ValidationResult(
                name="No Role Conflicts",
                passed=conflict_result["passed"],
                score=conflict_result["score"],
                details=conflict_result["details"],
                recommendations=conflict_result["recommendations"],
            )
        )

        # Quality gates active
        quality_gates_result = self._test_quality_gates()
        results.append(
            ValidationResult(
                name="Quality Gates Active",
                passed=quality_gates_result["passed"],
                score=quality_gates_result["score"],
                details=quality_gates_result["details"],
                recommendations=quality_gates_result["recommendations"],
            )
        )

        return results

    def validate_chemistry_metrics(self) -> List[ValidationResult]:
        """Validate team chemistry metrics"""
        results = []

        if self.formation_type not in self.formation_configs:
            return results

        thresholds = self.formation_configs[self.formation_type]["chemistry_thresholds"]

        # Communication fluency
        comm_result = self._assess_communication_quality()
        comm_passed = comm_result["score"] >= thresholds["communication"]
        results.append(
            ValidationResult(
                name="Communication Fluency",
                passed=comm_passed,
                score=comm_result["score"],
                details=f"Score: {comm_result['score']:.1%} (Threshold: {thresholds['communication']:.1%})",
                recommendations=(
                    comm_result["recommendations"] if not comm_passed else []
                ),
            )
        )

        # Role clarity
        role_result = self._assess_role_clarity()
        role_passed = role_result["score"] >= thresholds["role_clarity"]
        results.append(
            ValidationResult(
                name="Role Clarity",
                passed=role_passed,
                score=role_result["score"],
                details=f"Score: {role_result['score']:.1%} (Threshold: {thresholds['role_clarity']:.1%})",
                recommendations=(
                    role_result["recommendations"] if not role_passed else []
                ),
            )
        )

        # Collaboration rhythm
        collab_result = self._assess_collaboration_rhythm()
        collab_passed = collab_result["score"] >= thresholds["collaboration"]
        results.append(
            ValidationResult(
                name="Collaboration Rhythm",
                passed=collab_passed,
                score=collab_result["score"],
                details=f"Score: {collab_result['score']:.1%} (Threshold: {thresholds['collaboration']:.1%})",
                recommendations=(
                    collab_result["recommendations"] if not collab_passed else []
                ),
            )
        )

        # Quality integration
        quality_result = self._assess_quality_integration()
        quality_passed = quality_result["score"] >= thresholds["quality"]
        results.append(
            ValidationResult(
                name="Quality Integration",
                passed=quality_passed,
                score=quality_result["score"],
                details=f"Score: {quality_result['score']:.1%} (Threshold: {thresholds['quality']:.1%})",
                recommendations=(
                    quality_result["recommendations"] if not quality_passed else []
                ),
            )
        )

        return results

    def _test_basic_workflow(self) -> Dict[str, Any]:
        """Test basic workflow functionality"""
        # Simulate a basic workflow test
        try:
            # Check if core framework files exist
            required_files = ["CLAUDE.md", "tools/validation/validate-pipeline.py"]
            missing_files = [f for f in required_files if not Path(f).exists()]

            if missing_files:
                return {
                    "passed": False,
                    "score": 0.0,
                    "details": f"Missing framework files: {missing_files}",
                    "recommendations": [
                        "Ensure AI-First SDLC framework is properly installed"
                    ],
                }

            # Try running a simple validation
            result = subprocess.run(
                ["python", "tools/validation/validate-pipeline.py", "--quick"],
                capture_output=True,
                text=True,
                timeout=30,
            )

            success = result.returncode == 0
            return {
                "passed": success,
                "score": 1.0 if success else 0.3,
                "details": (
                    "Basic validation pipeline functional"
                    if success
                    else f"Validation failed: {result.stderr[:200]}"
                ),
                "recommendations": (
                    []
                    if success
                    else ["Fix validation pipeline issues before proceeding"]
                ),
            }
        except Exception as e:
            return {
                "passed": False,
                "score": 0.0,
                "details": f"Workflow test failed: {str(e)}",
                "recommendations": ["Debug basic workflow issues"],
            }

    def _test_handoff_protocol(self) -> Dict[str, Any]:
        """Test agent handoff protocol"""
        # In a real implementation, this would test actual agent handoffs
        # For now, we simulate based on available documentation

        handoff_files = [
            "templates/agent-handoff-patterns.md",
            "AGENTIC-TEAM-STANDARDS.md",
        ]

        existing_files = [f for f in handoff_files if Path(f).exists()]

        if len(existing_files) >= 1:
            return {
                "passed": True,
                "score": len(existing_files) / len(handoff_files),
                "details": f"Handoff protocols documented: {existing_files}",
                "recommendations": [],
            }
        else:
            return {
                "passed": False,
                "score": 0.0,
                "details": "No handoff protocols found",
                "recommendations": [
                    "Implement agent handoff protocols before proceeding"
                ],
            }

    def _test_formation_workflow(self) -> Dict[str, Any]:
        """Test formation-specific workflow"""
        # Simulate formation workflow test based on formation type
        formation_tests = {
            "builder": "Simple CRUD feature implementation",
            "specialist": "Domain-specific validation workflow",
            "innovator": "AI/ML pipeline integration",
            "transformer": "Multi-system integration workflow",
            "orchestrator": "Agent-to-agent orchestration workflow",
        }

        test_name = formation_tests.get(
            self.formation_type, "Unknown formation workflow"
        )

        # Simulate test based on available agents
        config = self.formation_configs.get(self.formation_type, {})
        required_agents = config.get("required_agents", [])
        available_count = len(
            [a for a in required_agents if a in self.agents_available]
        )
        total_count = len(required_agents)

        if total_count == 0:
            return {
                "passed": False,
                "score": 0.0,
                "details": f"Unknown formation: {self.formation_type}",
                "recommendations": ["Specify a valid formation type"],
            }

        score = available_count / total_count
        passed = score >= 0.8  # Need at least 80% of agents for formation workflow

        return {
            "passed": passed,
            "score": score,
            "details": f"{test_name}: {available_count}/{total_count} agents available",
            "recommendations": (
                []
                if passed
                else [
                    f"Install more {self.formation_type} agents to enable formation workflow"
                ]
            ),
        }

    def _detect_role_conflicts(self) -> Dict[str, Any]:
        """Detect conflicts between agent roles"""
        # In a real implementation, this would analyze agent role definitions
        # For now, we assume no conflicts if we have proper formation structure

        config = self.formation_configs.get(self.formation_type, {})
        required_agents = config.get("required_agents", [])

        # Check for obvious conflicts (e.g., multiple architects without
        # coordination)
        architects = [
            a
            for a in required_agents
            if "architect" in a and a in self.agents_available
        ]

        if len(architects) > 3 and "orchestration-architect" not in architects:
            return {
                "passed": False,
                "score": 0.6,
                "details": f"Multiple architects without coordination: {architects}",
                "recommendations": [
                    "Add orchestration-architect to coordinate multiple architects"
                ],
            }

        return {
            "passed": True,
            "score": 1.0,
            "details": "No obvious role conflicts detected",
            "recommendations": [],
        }

    def _test_quality_gates(self) -> Dict[str, Any]:
        """Test quality gate functionality"""
        try:
            # Check if quality validation tools exist and work
            quality_tools = [
                "tools/validation/validate-pipeline.py",
                "tools/validation/check-technical-debt.py",
            ]

            working_tools = []
            for tool in quality_tools:
                if Path(tool).exists():
                    try:
                        result = subprocess.run(
                            ["python", tool, "--help"],
                            capture_output=True,
                            text=True,
                            timeout=10,
                        )
                        if result.returncode == 0:
                            working_tools.append(tool)
                    except BaseException:
                        pass

            score = len(working_tools) / len(quality_tools)
            passed = score >= 0.5

            return {
                "passed": passed,
                "score": score,
                "details": f"Quality tools functional: {working_tools}",
                "recommendations": (
                    [] if passed else ["Fix quality gate tools before proceeding"]
                ),
            }
        except Exception as e:
            return {
                "passed": False,
                "score": 0.0,
                "details": f"Quality gate test failed: {str(e)}",
                "recommendations": ["Debug quality gate issues"],
            }

    def _assess_communication_quality(self) -> Dict[str, Any]:
        """Assess communication quality between agents"""
        # In a real implementation, this would analyze actual communication patterns
        # For now, we simulate based on available collaboration documentation

        communication_indicators = [
            "AGENTIC-TEAM-STANDARDS.md",
            "templates/agent-handoff-patterns.md",
            "docs/AI-TEAM-ORCHESTRATION-GUIDE.md",
        ]

        score_factors = []

        for indicator in communication_indicators:
            if Path(indicator).exists():
                content = Path(indicator).read_text()
                # Check for communication quality indicators
                if "hando" in content.lower():
                    score_factors.append(0.3)
                if "protocol" in content.lower():
                    score_factors.append(0.3)
                if "communication" in content.lower():
                    score_factors.append(0.4)

        score = min(1.0, sum(score_factors))

        recommendations = []
        if score < 0.8:
            recommendations.append("Implement structured agent handoff protocols")
        if score < 0.6:
            recommendations.append("Create agent communication guidelines")

        return {"score": score, "recommendations": recommendations}

    def _assess_role_clarity(self) -> Dict[str, Any]:
        """Assess role clarity among team agents"""
        # config = self.formation_configs.get(self.formation_type, {})
        # required_agents = config.get("required_agents", [])  # May be used for
        # future agent validation

        # Score based on having clear formation structure
        if self.formation_type in self.formation_configs:
            base_score = 0.7  # Having defined formation gives baseline clarity
        else:
            base_score = 0.3

        # Bonus for having orchestration or coordination agents
        coordination_agents = [
            "orchestration-architect",
            "solution-architect",
            "a2a-architect",
        ]
        has_coordinator = any(
            agent in self.agents_available for agent in coordination_agents
        )

        if has_coordinator:
            base_score += 0.2

        # Penalty for too many agents without coordination
        if len(self.agents_available) > 8 and not has_coordinator:
            base_score -= 0.1

        score = min(1.0, max(0.0, base_score))

        recommendations = []
        if score < 0.85:
            recommendations.append("Add coordination agent to improve role clarity")
        if len(self.agents_available) > 6 and not has_coordinator:
            recommendations.append(
                "Consider adding orchestration-architect for large teams"
            )

        return {"score": score, "recommendations": recommendations}

    def _assess_collaboration_rhythm(self) -> Dict[str, Any]:
        """Assess collaboration rhythm and workflow smoothness"""
        # Score based on team size and formation appropriateness
        config = self.formation_configs.get(self.formation_type, {})
        ideal_agents = len(config.get("required_agents", []))
        actual_agents = len(
            [a for a in config.get("required_agents", []) if a in self.agents_available]
        )

        if ideal_agents == 0:
            return {"score": 0.0, "recommendations": ["Define formation requirements"]}

        # Score based on how complete the formation is
        completeness_score = actual_agents / ideal_agents

        # Adjust based on formation complexity
        complexity_multiplier = {
            "builder": 1.0,
            "specialist": 0.95,
            "innovator": 0.9,
            "transformer": 0.85,
            "orchestrator": 0.8,
        }.get(self.formation_type, 0.7)

        score = completeness_score * complexity_multiplier

        recommendations = []
        if score < 0.75:
            recommendations.append(
                f"Complete {self.formation_type} formation to improve collaboration"
            )
        if self.formation_type in ["transformer", "orchestrator"] and score < 0.8:
            recommendations.append(
                "Complex formations require more chemistry development"
            )

        return {"score": score, "recommendations": recommendations}

    def _assess_quality_integration(self) -> Dict[str, Any]:
        """Assess how well quality processes are integrated"""
        quality_agents = [
            "critical-goal-reviewer",
            "test-manager",
            "compliance-auditor",
        ]
        quality_agents_available = len(
            [a for a in quality_agents if a in self.agents_available]
        )

        # Base score from having quality agents
        base_score = min(0.8, quality_agents_available / len(quality_agents))

        # Bonus for having validation tools
        if Path("tools/validation/validate-pipeline.py").exists():
            base_score += 0.1

        if Path("tools/validation/check-technical-debt.py").exists():
            base_score += 0.1

        score = min(1.0, base_score)

        recommendations = []
        if quality_agents_available < 2:
            recommendations.append("Install more quality-focused agents")
        if score < 0.9:
            recommendations.append("Enhance quality validation tooling")

        return {"score": score, "recommendations": recommendations}

    def generate_report(self) -> TeamReadinessReport:
        """Generate complete team readiness report"""
        foundation_metrics = self.validate_foundation_metrics()
        formation_metrics = self.validate_formation_metrics()
        chemistry_metrics = self.validate_chemistry_metrics()

        # Calculate overall scores
        foundation_score = sum(r.score for r in foundation_metrics) / len(
            foundation_metrics
        )
        formation_score = (
            sum(r.score for r in formation_metrics) / len(formation_metrics)
            if formation_metrics
            else 0
        )
        chemistry_score = (
            sum(r.score for r in chemistry_metrics) / len(chemistry_metrics)
            if chemistry_metrics
            else 0
        )

        overall_score = (
            foundation_score * 0.4 + formation_score * 0.35 + chemistry_score * 0.25
        )

        # Determine readiness level
        if overall_score >= 0.85 and all(r.passed for r in foundation_metrics):
            readiness_level = ReadinessLevel.GREEN
        elif overall_score >= 0.6:
            readiness_level = ReadinessLevel.YELLOW
        else:
            readiness_level = ReadinessLevel.RED

        # Generate recommendations
        all_recommendations = []
        for metrics in [foundation_metrics, formation_metrics, chemistry_metrics]:
            for result in metrics:
                all_recommendations.extend(result.recommendations)

        # Generate next steps
        next_steps = self._generate_next_steps(
            readiness_level, foundation_score, formation_score, chemistry_score
        )

        return TeamReadinessReport(
            formation_type=self.formation_type,
            overall_readiness=readiness_level,
            overall_score=overall_score,
            foundation_metrics=foundation_metrics,
            formation_metrics=formation_metrics,
            chemistry_metrics=chemistry_metrics,
            recommendations=list(set(all_recommendations)),
            # Remove duplicates
            next_steps=next_steps,
        )

    def _generate_next_steps(
        self,
        readiness_level: ReadinessLevel,
        foundation_score: float,
        formation_score: float,
        chemistry_score: float,
    ) -> List[str]:
        """Generate specific next steps based on readiness assessment"""
        steps = []

        if readiness_level == ReadinessLevel.RED:
            if foundation_score < 0.8:
                steps.append(
                    "🚨 Fix foundation issues before proceeding - team is not ready"
                )
                steps.append("Install and verify core trio functionality")
            if formation_score < 0.6:
                steps.append("Complete agent installation for your formation")
            steps.append("Do not attempt complex development until readiness improves")

        elif readiness_level == ReadinessLevel.YELLOW:
            steps.append("⚠️ Team shows promise but needs improvement")
            if chemistry_score < 0.75:
                steps.append("Focus on chemistry development exercises")
            if formation_score < 0.85:
                steps.append("Complete formation setup and test workflows")
            steps.append("Proceed with simple features while improving team readiness")

        else:  # GREEN
            steps.append("✅ Team is ready for production development!")
            steps.append("Begin with complex feature development")
            steps.append("Monitor team performance and optimize as needed")
            steps.append("Consider formation evolution as project grows")

        return steps


@click.command()
@click.option(
    "--formation",
    required=True,
    type=click.Choice(
        ["builder", "specialist", "innovator", "transformer", "orchestrator"]
    ),
    help="Formation type to validate",
)
@click.option("--output", type=click.Path(), help="Output file for detailed report")
@click.option(
    "--format",
    type=click.Choice(["json", "markdown"]),
    default="markdown",
    help="Output format",
)
@click.option("--quick", is_flag=True, help="Run quick validation (foundation only)")
@click.option("--verbose", is_flag=True, help="Show detailed validation steps")
def main(formation: str, output: str, format: str, quick: bool, verbose: bool):
    """Validate AI agent team readiness for production development"""

    if verbose:
        click.echo(f"🔍 Validating {formation} formation readiness...")
        click.echo("=" * 50)

    try:
        validator = TeamReadinessValidator(formation)

        if quick:
            # Quick validation - foundation only
            foundation_metrics = validator.validate_foundation_metrics()
            foundation_score = sum(r.score for r in foundation_metrics) / len(
                foundation_metrics
            )

            click.echo("\n📊 Quick Validation Results:")
            click.echo(f"Foundation Score: {foundation_score:.1%}")

            for result in foundation_metrics:
                status = "✅" if result.passed else "❌"
                click.echo(f"{status} {result.name}: {result.score:.1%}")
                if not result.passed and result.recommendations:
                    for rec in result.recommendations:
                        click.echo(f"   → {rec}")

            if foundation_score >= 0.8:
                click.echo(
                    "\n✅ Foundation is solid! Run full validation for complete assessment."
                )
            else:
                click.echo("\n❌ Foundation needs work before proceeding.")

        else:
            # Full validation
            report = validator.generate_report()

            # Display summary
            readiness_emoji = {
                "ready": "✅",
                "needs_improvement": "⚠️",
                "not_ready": "❌",
            }
            click.echo(
                f"\n🎯 Team Readiness: {readiness_emoji[report.overall_readiness.value]} "
                f"{report.overall_readiness.value.replace('_', ' ').title()}"
            )
            click.echo(f"📊 Overall Score: {report.overall_score:.1%}")

            # Show metric summaries
            if verbose:
                click.echo("\n📋 Foundation Metrics:")
                for result in report.foundation_metrics:
                    status = "✅" if result.passed else "❌"
                    click.echo(f"  {status} {result.name}: {result.score:.1%}")

                click.echo("\n🏗️ Formation Metrics:")
                for result in report.formation_metrics:
                    status = "✅" if result.passed else "❌"
                    click.echo(f"  {status} {result.name}: {result.score:.1%}")

                click.echo("\n🤝 Chemistry Metrics:")
                for result in report.chemistry_metrics:
                    status = "✅" if result.passed else "❌"
                    click.echo(f"  {status} {result.name}: {result.score:.1%}")

            # Show next steps
            click.echo("\n🚀 Next Steps:")
            for i, step in enumerate(report.next_steps, 1):
                click.echo(f"{i}. {step}")

            # Generate detailed report if requested
            if output:
                if format == "json":
                    report_data = {
                        "formation_type": report.formation_type,
                        "overall_readiness": report.overall_readiness.value,
                        "overall_score": report.overall_score,
                        "foundation_metrics": [
                            {
                                "name": r.name,
                                "passed": r.passed,
                                "score": r.score,
                                "details": r.details,
                                "recommendations": r.recommendations,
                            }
                            for r in report.foundation_metrics
                        ],
                        "formation_metrics": [
                            {
                                "name": r.name,
                                "passed": r.passed,
                                "score": r.score,
                                "details": r.details,
                                "recommendations": r.recommendations,
                            }
                            for r in report.formation_metrics
                        ],
                        "chemistry_metrics": [
                            {
                                "name": r.name,
                                "passed": r.passed,
                                "score": r.score,
                                "details": r.details,
                                "recommendations": r.recommendations,
                            }
                            for r in report.chemistry_metrics
                        ],
                        "recommendations": report.recommendations,
                        "next_steps": report.next_steps,
                    }
                    Path(output).write_text(json.dumps(report_data, indent=2))
                else:
                    markdown_report = generate_markdown_report(report)
                    Path(output).write_text(markdown_report)

                click.echo(f"\n📄 Detailed report saved to {output}")

    except Exception as e:
        click.echo(f"❌ Validation failed: {e}")
        if verbose:
            import traceback

            traceback.print_exc()


def generate_markdown_report(report: TeamReadinessReport) -> str:
    """Generate markdown report from validation results"""

    # readiness_emoji = {"ready": "✅", "needs_improvement": "⚠️", "not_ready": "❌"}
    # emoji = readiness_emoji[report.overall_readiness.value]  # Will be used
    # in emoji support

    markdown = """# Team Readiness Validation Report

## Overall Assessment

**Formation**: {report.formation_type.title()}
**Readiness**: {emoji} {report.overall_readiness.value.replace('_', ' ').title()}
**Overall Score**: {report.overall_score:.1%}

## Foundation Metrics

| Metric | Status | Score | Details |
|--------|--------|-------|---------|
"""

    for result in report.foundation_metrics:
        status = "✅" if result.passed else "❌"
        markdown += (
            f"| {result.name} | {status} | {result.score:.1%} | {result.details} |\n"
        )

    markdown += """
## Formation Metrics

| Metric | Status | Score | Details |
|--------|--------|-------|---------|
"""

    for result in report.formation_metrics:
        status = "✅" if result.passed else "❌"
        markdown += (
            f"| {result.name} | {status} | {result.score:.1%} | {result.details} |\n"
        )

    markdown += """
## Chemistry Metrics

| Metric | Status | Score | Details |
|--------|--------|-------|---------|
"""

    for result in report.chemistry_metrics:
        status = "✅" if result.passed else "❌"
        markdown += (
            f"| {result.name} | {status} | {result.score:.1%} | {result.details} |\n"
        )

    if report.recommendations:
        markdown += "\n## Recommendations\n\n"
        for rec in report.recommendations:
            markdown += f"- {rec}\n"

    markdown += "\n## Next Steps\n\n"
    for i, step in enumerate(report.next_steps, 1):
        markdown += f"{i}. {step}\n"

    markdown += """
## Commands for Improvement

```bash
# Run chemistry development exercises
python tools/automation/team-chemistry.py --exercise simple-feature-challenge

# Monitor team performance
python tools/automation/team-dashboard.py --live

# Re-validate after improvements
python tools/automation/validate-team-readiness.py --formation {report.formation_type}
```

---
*Generated by AI Team Orchestration System*
"""

    return markdown


if __name__ == "__main__":
    main()
