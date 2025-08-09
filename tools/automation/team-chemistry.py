#!/usr/bin/env python3
"""
Team Chemistry Development Tool - AI Team Orchestration System

Facilitates team chemistry development exercises and measures collaboration
effectiveness between AI agents in different formation patterns.
"""

import json
import click
import time
import random
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass
from enum import Enum


class ExerciseType(Enum):
    """Types of chemistry development exercises"""
    SIMPLE_FEATURE = "simple-feature-challenge"
    INTEGRATION = "integration-challenge"
    CRISIS_SIMULATION = "crisis-simulation"
    HANDOFF_PROTOCOL = "handoff-protocol"
    ROLE_CLARITY = "role-clarity"
    QUALITY_GATES = "quality-gates"


@dataclass
class ExerciseResult:
    """Result of a chemistry exercise"""
    exercise_name: str
    exercise_type: ExerciseType
    participants: List[str]
    success_score: float
    duration_minutes: int
    observations: List[str]
    improvements: List[str]
    next_exercises: List[str]


@dataclass
class ChemistryMetrics:
    """Team chemistry measurement metrics"""
    communication_fluency: float
    role_clarity: float
    collaboration_rhythm: float
    quality_integration: float
    overall_chemistry: float


class ChemistryExercise:
    """Base class for team chemistry exercises"""
    
    def __init__(self, name: str, description: str, participants: List[str], 
                 success_criteria: List[str], duration_estimate: int):
        self.name = name
        self.description = description
        self.participants = participants
        self.success_criteria = success_criteria
        self.duration_estimate = duration_estimate
    
    def run(self, formation_type: str) -> ExerciseResult:
        """Run the exercise and return results"""
        raise NotImplementedError("Subclasses must implement run method")


class SimpleFeatureChallenge(ChemistryExercise):
    """Simple feature implementation exercise"""
    
    def __init__(self):
        super().__init__(
            name="Simple Feature Challenge",
            description="Implement a basic CRUD endpoint with full team collaboration",
            participants=["solution-architect", "language-expert", "critical-goal-reviewer"],
            success_criteria=[
                "Clean handoffs between design, implementation, and review",
                "All agents contribute meaningfully",
                "No duplicated effort or missed responsibilities",
                "Quality gates function properly"
            ],
            duration_estimate=30
        )
    
    def run(self, formation_type: str) -> ExerciseResult:
        """Simulate running the simple feature challenge"""
        click.echo(f"🎯 Starting {self.name}")
        click.echo(f"📝 {self.description}")
        click.echo(f"👥 Participants: {', '.join(self.participants)}")
        click.echo("=" * 50)
        
        # Simulate exercise phases
        observations = []
        success_factors = []
        
        # Phase 1: Design
        click.echo("Phase 1: Architecture and Design")
        time.sleep(1)
        if "solution-architect" in self.participants:
            observations.append("Solution architect provided clear system design")
            success_factors.append(0.25)
        else:
            observations.append("No dedicated architect - design phase struggled")
            success_factors.append(0.1)
        
        # Phase 2: Implementation
        click.echo("Phase 2: Implementation")
        time.sleep(1)
        if "language-expert" in self.participants:
            observations.append("Language expert implemented with best practices")
            success_factors.append(0.25)
        else:
            observations.append("Implementation lacked language expertise")
            success_factors.append(0.15)
        
        # Phase 3: Review and Quality
        click.echo("Phase 3: Review and Quality Assurance")
        time.sleep(1)
        if "critical-goal-reviewer" in self.participants:
            observations.append("Critical goal reviewer ensured requirements met")
            success_factors.append(0.25)
        else:
            observations.append("Quality review phase was incomplete")
            success_factors.append(0.1)
        
        # Phase 4: Integration
        click.echo("Phase 4: Integration and Testing")
        time.sleep(1)
        if formation_type in ["transformer", "orchestrator"]:
            observations.append("Complex formation handled integration well")
            success_factors.append(0.25)
        else:
            observations.append("Basic integration completed successfully")
            success_factors.append(0.2)
        
        # Calculate success score
        success_score = min(1.0, sum(success_factors))
        
        # Generate improvements based on score
        improvements = []
        if success_score < 0.7:
            improvements.append("Improve agent role coordination")
        if success_score < 0.8:
            improvements.append("Enhance handoff protocols between phases")
        if "No" in str(observations):
            improvements.append("Ensure all required agents are available")
        
        # Suggest next exercises
        next_exercises = []
        if success_score >= 0.8:
            next_exercises.extend(["integration-challenge", "quality-gates"])
        else:
            next_exercises.extend(["handoff-protocol", "role-clarity"])
        
        click.echo(f"\n✅ Exercise completed!")
        click.echo(f"📊 Success Score: {success_score:.1%}")
        
        return ExerciseResult(
            exercise_name=self.name,
            exercise_type=ExerciseType.SIMPLE_FEATURE,
            participants=self.participants,
            success_score=success_score,
            duration_minutes=self.duration_estimate,
            observations=observations,
            improvements=improvements,
            next_exercises=next_exercises
        )


class IntegrationChallenge(ChemistryExercise):
    """Complex system integration exercise"""
    
    def __init__(self):
        super().__init__(
            name="Integration Challenge",
            description="Integrate with external API and handle failures gracefully",
            participants=["integration-orchestrator", "devops-specialist", "sre-specialist"],
            success_criteria=[
                "Multiple agents coordinate without conflict",
                "Error handling involves appropriate specialists",
                "Quality gates catch integration issues",
                "Monitoring and alerting configured"
            ],
            duration_estimate=45
        )
    
    def run(self, formation_type: str) -> ExerciseResult:
        """Simulate running the integration challenge"""
        click.echo(f"🎯 Starting {self.name}")
        click.echo(f"📝 {self.description}")
        click.echo(f"👥 Participants: {', '.join(self.participants)}")
        click.echo("=" * 50)
        
        observations = []
        success_factors = []
        
        # Simulate complex integration phases
        phases = [
            ("API Discovery and Planning", "integration-orchestrator"),
            ("Infrastructure Setup", "devops-specialist"), 
            ("Monitoring Configuration", "sre-specialist"),
            ("Error Handling Implementation", "integration-orchestrator"),
            ("Testing and Validation", "All participants")
        ]
        
        for phase_name, responsible_agent in phases:
            click.echo(f"Phase: {phase_name}")
            time.sleep(1)
            
            if responsible_agent == "All participants":
                success_factors.append(0.2)
                observations.append(f"All agents collaborated on {phase_name.lower()}")
            elif responsible_agent in self.participants:
                success_factors.append(0.2)
                observations.append(f"{responsible_agent} handled {phase_name.lower()} effectively")
            else:
                success_factors.append(0.1)
                observations.append(f"Missing {responsible_agent} for {phase_name.lower()}")
        
        # Formation-specific adjustments
        if formation_type in ["transformer", "orchestrator"]:
            success_factors.append(0.1)  # Bonus for appropriate formation
            observations.append("Formation well-suited for integration complexity")
        
        success_score = min(1.0, sum(success_factors))
        
        improvements = []
        if success_score < 0.8:
            improvements.append("Add missing integration specialists")
        if "Missing" in str(observations):
            improvements.append("Install required agents for complex integrations")
        
        next_exercises = []
        if success_score >= 0.8:
            next_exercises.extend(["crisis-simulation"])
        else:
            next_exercises.extend(["simple-feature-challenge", "role-clarity"])
        
        click.echo(f"\n✅ Exercise completed!")
        click.echo(f"📊 Success Score: {success_score:.1%}")
        
        return ExerciseResult(
            exercise_name=self.name,
            exercise_type=ExerciseType.INTEGRATION,
            participants=self.participants,
            success_score=success_score,
            duration_minutes=self.duration_estimate,
            observations=observations,
            improvements=improvements,
            next_exercises=next_exercises
        )


class CrisisSimulation(ChemistryExercise):
    """Crisis response and recovery exercise"""
    
    def __init__(self):
        super().__init__(
            name="Crisis Simulation",
            description="Resolve a production-blocking CI failure under time pressure",
            participants=["All available agents"],
            success_criteria=[
                "Escalation protocols followed correctly",
                "Right agents engage at right time",
                "Solution is systematic, not patched",
                "Communication remains clear under pressure"
            ],
            duration_estimate=60
        )
    
    def run(self, formation_type: str) -> ExerciseResult:
        """Simulate running the crisis simulation"""
        click.echo(f"🚨 CRISIS SIMULATION STARTED")
        click.echo(f"📝 {self.description}")
        click.echo("⏰ Time pressure: Production is down!")
        click.echo("=" * 50)
        
        observations = []
        success_factors = []
        
        # Simulate crisis response phases
        click.echo("🔥 CRISIS: Production deployment failing, users affected!")
        time.sleep(1)
        
        # Phase 1: Initial Response
        click.echo("Phase 1: Initial Response and Triage")
        observations.append("Crisis detected and initial response initiated")
        
        # Check for proper crisis response agents
        crisis_agents = ["sre-specialist", "devops-specialist", "orchestration-architect"]
        available_crisis_agents = [agent for agent in crisis_agents if agent in self.participants or formation_type == "orchestrator"]
        
        if available_crisis_agents:
            success_factors.append(0.2)
            observations.append(f"Crisis response agents available: {', '.join(available_crisis_agents)}")
        else:
            success_factors.append(0.1)
            observations.append("No dedicated crisis response agents available")
        
        # Phase 2: Diagnosis
        click.echo("Phase 2: Root Cause Analysis")
        time.sleep(1)
        if formation_type in ["transformer", "orchestrator"]:
            success_factors.append(0.2)
            observations.append("Complex formation enabled thorough diagnosis")
        else:
            success_factors.append(0.15)
            observations.append("Basic diagnosis completed with available agents")
        
        # Phase 3: Escalation Protocol
        click.echo("Phase 3: Escalation and Coordination")
        time.sleep(1)
        if "orchestration-architect" in self.participants or formation_type == "orchestrator":
            success_factors.append(0.2)
            observations.append("Proper escalation protocols followed")
        else:
            success_factors.append(0.1)
            observations.append("Escalation ad-hoc without orchestration")
        
        # Phase 4: Solution Implementation
        click.echo("Phase 4: Solution Implementation")
        time.sleep(1)
        if formation_type != "builder":  # Non-builder formations handle crisis better
            success_factors.append(0.2)
            observations.append("Systematic solution implemented")
        else:
            success_factors.append(0.15)
            observations.append("Solution implemented with basic formation")
        
        # Phase 5: Recovery and Learning
        click.echo("Phase 5: Recovery Verification and Post-Incident Review")
        time.sleep(1)
        if "critical-goal-reviewer" in self.participants:
            success_factors.append(0.2)
            observations.append("Recovery verified and lessons documented")
        else:
            success_factors.append(0.1)
            observations.append("Recovery verification incomplete")
        
        success_score = min(1.0, sum(success_factors))
        
        improvements = []
        if success_score < 0.7:
            improvements.append("Add crisis response specialists to formation")
        if success_score < 0.8:
            improvements.append("Improve escalation protocols and coordination")
        if "ad-hoc" in str(observations):
            improvements.append("Consider adding orchestration-architect for crisis coordination")
        
        next_exercises = []
        if success_score >= 0.8:
            next_exercises.append("Team is crisis-ready!")
        else:
            next_exercises.extend(["handoff-protocol", "role-clarity", "integration-challenge"])
        
        click.echo(f"\n✅ Crisis simulation completed!")
        click.echo(f"📊 Crisis Response Score: {success_score:.1%}")
        
        return ExerciseResult(
            exercise_name=self.name,
            exercise_type=ExerciseType.CRISIS_SIMULATION,
            participants=self.participants,
            success_score=success_score,
            duration_minutes=self.duration_estimate,
            observations=observations,
            improvements=improvements,
            next_exercises=next_exercises
        )


class HandoffProtocolExercise(ChemistryExercise):
    """Agent handoff protocol development exercise"""
    
    def __init__(self):
        super().__init__(
            name="Handoff Protocol Exercise",
            description="Practice structured context handoffs between agents",
            participants=["Any two agents"],
            success_criteria=[
                "Complete context transfer achieved",
                "No information lost in handoff",
                "Clear acceptance confirmation",
                "Structured handoff format used"
            ],
            duration_estimate=20
        )
    
    def run(self, formation_type: str) -> ExerciseResult:
        """Simulate running handoff protocol exercise"""
        click.echo(f"🤝 Starting {self.name}")
        click.echo(f"📝 {self.description}")
        click.echo("=" * 50)
        
        observations = []
        success_factors = []
        
        # Simulate handoff scenarios
        handoff_scenarios = [
            ("Design → Implementation", 0.25),
            ("Implementation → Testing", 0.25),
            ("Testing → Deployment", 0.25), 
            ("Cross-cutting Concerns", 0.25)
        ]
        
        for scenario, weight in handoff_scenarios:
            click.echo(f"Practicing: {scenario}")
            time.sleep(0.5)
            
            # Simulate handoff quality based on formation complexity
            if formation_type in ["orchestrator", "transformer"]:
                scenario_success = random.uniform(0.8, 1.0)  # Complex formations are better at handoffs
            elif formation_type in ["innovator", "specialist"]:
                scenario_success = random.uniform(0.7, 0.95)
            else:  # builder
                scenario_success = random.uniform(0.6, 0.9)
            
            success_factors.append(scenario_success * weight)
            
            if scenario_success > 0.85:
                observations.append(f"Excellent {scenario.lower()} handoff")
            elif scenario_success > 0.7:
                observations.append(f"Good {scenario.lower()} handoff with minor improvements needed")
            else:
                observations.append(f"Poor {scenario.lower()} handoff - needs work")
        
        success_score = sum(success_factors)
        
        improvements = []
        if success_score < 0.8:
            improvements.append("Implement structured handoff templates")
        if success_score < 0.7:
            improvements.append("Practice handoff scenarios more frequently")
        if "Poor" in str(observations):
            improvements.append("Focus on complete context transfer")
        
        next_exercises = []
        if success_score >= 0.8:
            next_exercises.extend(["simple-feature-challenge", "integration-challenge"])
        else:
            next_exercises.extend(["role-clarity"])
        
        click.echo(f"\n✅ Handoff practice completed!")
        click.echo(f"📊 Handoff Quality Score: {success_score:.1%}")
        
        return ExerciseResult(
            exercise_name=self.name,
            exercise_type=ExerciseType.HANDOFF_PROTOCOL,
            participants=["Agent A", "Agent B"],  # Simulated
            success_score=success_score,
            duration_minutes=self.duration_estimate,
            observations=observations,
            improvements=improvements,
            next_exercises=next_exercises
        )


class TeamChemistryEngine:
    """Engine for managing team chemistry development"""
    
    def __init__(self):
        self.exercises = {
            ExerciseType.SIMPLE_FEATURE: SimpleFeatureChallenge(),
            ExerciseType.INTEGRATION: IntegrationChallenge(),
            ExerciseType.CRISIS_SIMULATION: CrisisSimulation(),
            ExerciseType.HANDOFF_PROTOCOL: HandoffProtocolExercise()
        }
        self.results_history = []
    
    def run_exercise(self, exercise_type: ExerciseType, formation_type: str, 
                    available_agents: List[str] = None) -> ExerciseResult:
        """Run a specific chemistry exercise"""
        
        if exercise_type not in self.exercises:
            raise ValueError(f"Unknown exercise type: {exercise_type}")
        
        exercise = self.exercises[exercise_type]
        
        # Update participants if agents provided
        if available_agents:
            exercise.participants = available_agents
        
        result = exercise.run(formation_type)
        self.results_history.append(result)
        
        return result
    
    def assess_team_chemistry(self, formation_type: str) -> ChemistryMetrics:
        """Assess overall team chemistry based on exercise results"""
        
        if not self.results_history:
            # No exercises completed yet - return baseline assessment
            return ChemistryMetrics(
                communication_fluency=0.5,
                role_clarity=0.5,
                collaboration_rhythm=0.5,
                quality_integration=0.5,
                overall_chemistry=0.5
            )
        
        # Calculate metrics based on recent exercise performance
        recent_results = self.results_history[-5:]  # Last 5 exercises
        
        # Communication fluency from handoff exercises
        handoff_scores = [r.success_score for r in recent_results 
                         if r.exercise_type == ExerciseType.HANDOFF_PROTOCOL]
        communication_fluency = sum(handoff_scores) / len(handoff_scores) if handoff_scores else 0.7
        
        # Role clarity from role conflicts and coordination
        role_indicators = []
        for result in recent_results:
            if "conflict" in str(result.observations).lower():
                role_indicators.append(0.3)
            elif "coordination" in str(result.observations).lower():
                role_indicators.append(0.9)
            else:
                role_indicators.append(0.7)
        role_clarity = sum(role_indicators) / len(role_indicators) if role_indicators else 0.7
        
        # Collaboration rhythm from overall exercise success
        avg_success = sum(r.success_score for r in recent_results) / len(recent_results)
        collaboration_rhythm = avg_success
        
        # Quality integration from crisis and quality-focused exercises
        quality_exercises = [r for r in recent_results 
                           if r.exercise_type in [ExerciseType.CRISIS_SIMULATION, ExerciseType.INTEGRATION]]
        if quality_exercises:
            quality_integration = sum(r.success_score for r in quality_exercises) / len(quality_exercises)
        else:
            quality_integration = 0.75  # Default if no quality exercises
        
        # Overall chemistry with formation bonus
        formation_multiplier = {
            "builder": 1.0,
            "specialist": 1.05,
            "innovator": 1.1,
            "transformer": 1.15,
            "orchestrator": 1.2
        }.get(formation_type, 1.0)
        
        base_chemistry = (communication_fluency + role_clarity + collaboration_rhythm + quality_integration) / 4
        overall_chemistry = min(1.0, base_chemistry * formation_multiplier)
        
        return ChemistryMetrics(
            communication_fluency=communication_fluency,
            role_clarity=role_clarity,
            collaboration_rhythm=collaboration_rhythm,
            quality_integration=quality_integration,
            overall_chemistry=overall_chemistry
        )
    
    def recommend_next_exercise(self, formation_type: str, current_chemistry: ChemistryMetrics) -> ExerciseType:
        """Recommend the next chemistry exercise based on current state"""
        
        # Identify weakest area
        weak_areas = []
        if current_chemistry.communication_fluency < 0.8:
            weak_areas.append(("communication", ExerciseType.HANDOFF_PROTOCOL))
        if current_chemistry.role_clarity < 0.8:
            weak_areas.append(("role_clarity", ExerciseType.SIMPLE_FEATURE))
        if current_chemistry.collaboration_rhythm < 0.8:
            weak_areas.append(("collaboration", ExerciseType.INTEGRATION))
        if current_chemistry.quality_integration < 0.8:
            weak_areas.append(("quality", ExerciseType.CRISIS_SIMULATION))
        
        if weak_areas:
            # Focus on weakest area
            weakest_area, exercise = min(weak_areas, 
                key=lambda x: getattr(current_chemistry, x[0]))
            return exercise
        
        # If all areas are strong, cycle through exercises for maintenance
        if not self.results_history:
            return ExerciseType.SIMPLE_FEATURE
        
        last_exercise = self.results_history[-1].exercise_type
        exercise_cycle = [
            ExerciseType.SIMPLE_FEATURE,
            ExerciseType.HANDOFF_PROTOCOL,
            ExerciseType.INTEGRATION,
            ExerciseType.CRISIS_SIMULATION
        ]
        
        current_index = exercise_cycle.index(last_exercise)
        return exercise_cycle[(current_index + 1) % len(exercise_cycle)]
    
    def save_results(self, output_path: str):
        """Save exercise results to file"""
        results_data = {
            "results_history": [
                {
                    "exercise_name": r.exercise_name,
                    "exercise_type": r.exercise_type.value,
                    "participants": r.participants,
                    "success_score": r.success_score,
                    "duration_minutes": r.duration_minutes,
                    "observations": r.observations,
                    "improvements": r.improvements,
                    "next_exercises": r.next_exercises
                }
                for r in self.results_history
            ]
        }
        
        Path(output_path).write_text(json.dumps(results_data, indent=2))


@click.command()
@click.option('--exercise', type=click.Choice([e.value for e in ExerciseType]), 
              help='Specific exercise to run')
@click.option('--formation', type=click.Choice(['builder', 'specialist', 'innovator', 'transformer', 'orchestrator']),
              default='builder', help='Formation type')
@click.option('--agents', help='Comma-separated list of available agents')
@click.option('--assess', is_flag=True, help='Assess current team chemistry')
@click.option('--recommend', is_flag=True, help='Get exercise recommendations')
@click.option('--output', type=click.Path(), help='Save results to file')
@click.option('--interactive', is_flag=True, help='Interactive chemistry development session')
def main(exercise: str, formation: str, agents: str, assess: bool, recommend: bool, 
         output: str, interactive: bool):
    """AI Team Chemistry Development Tool"""
    
    engine = TeamChemistryEngine()
    available_agents = agents.split(',') if agents else []
    
    try:
        if interactive:
            run_interactive_session(engine, formation, available_agents)
        elif assess:
            metrics = engine.assess_team_chemistry(formation)
            display_chemistry_metrics(metrics)
        elif recommend:
            metrics = engine.assess_team_chemistry(formation)
            next_exercise = engine.recommend_next_exercise(formation, metrics)
            click.echo(f"🎯 Recommended next exercise: {next_exercise.value}")
            click.echo(f"📝 This will help improve your team's weakest chemistry areas")
        elif exercise:
            exercise_type = ExerciseType(exercise)
            click.echo(f"🚀 Running {exercise_type.value} for {formation} formation")
            result = engine.run_exercise(exercise_type, formation, available_agents)
            display_exercise_result(result)
            
            if output:
                engine.save_results(output)
                click.echo(f"📄 Results saved to {output}")
        else:
            click.echo("Use --exercise, --assess, --recommend, or --interactive")
            
    except Exception as e:
        click.echo(f"❌ Error: {e}")


def run_interactive_session(engine: TeamChemistryEngine, formation: str, available_agents: List[str]):
    """Run an interactive chemistry development session"""
    click.echo("🎯 Interactive Team Chemistry Development Session")
    click.echo(f"Formation: {formation.title()}")
    click.echo("=" * 50)
    
    while True:
        click.echo("\nWhat would you like to do?")
        click.echo("1. Run chemistry exercise")
        click.echo("2. Assess current chemistry")
        click.echo("3. Get exercise recommendations")
        click.echo("4. View exercise history")
        click.echo("5. Exit")
        
        choice = click.prompt("Select option", type=int)
        
        if choice == 1:
            click.echo("\nAvailable exercises:")
            for i, exercise_type in enumerate(ExerciseType, 1):
                click.echo(f"{i}. {exercise_type.value}")
            
            exercise_choice = click.prompt("Select exercise", type=int)
            exercise_types = list(ExerciseType)
            
            if 1 <= exercise_choice <= len(exercise_types):
                exercise_type = exercise_types[exercise_choice - 1]
                result = engine.run_exercise(exercise_type, formation, available_agents)
                display_exercise_result(result)
            else:
                click.echo("Invalid selection")
        
        elif choice == 2:
            metrics = engine.assess_team_chemistry(formation)
            display_chemistry_metrics(metrics)
        
        elif choice == 3:
            metrics = engine.assess_team_chemistry(formation)
            next_exercise = engine.recommend_next_exercise(formation, metrics)
            click.echo(f"🎯 Recommended: {next_exercise.value}")
        
        elif choice == 4:
            if engine.results_history:
                click.echo("\n📊 Exercise History:")
                for i, result in enumerate(engine.results_history[-5:], 1):
                    click.echo(f"{i}. {result.exercise_name} - Score: {result.success_score:.1%}")
            else:
                click.echo("No exercises completed yet")
        
        elif choice == 5:
            click.echo("👋 Chemistry development session completed!")
            break
        
        else:
            click.echo("Invalid selection")


def display_exercise_result(result: ExerciseResult):
    """Display exercise result in a formatted way"""
    click.echo(f"\n📊 {result.exercise_name} Results:")
    click.echo(f"Success Score: {result.success_score:.1%}")
    click.echo(f"Duration: {result.duration_minutes} minutes")
    
    if result.observations:
        click.echo("\n👁️ Observations:")
        for obs in result.observations:
            click.echo(f"  • {obs}")
    
    if result.improvements:
        click.echo("\n🔧 Improvements Needed:")
        for imp in result.improvements:
            click.echo(f"  • {imp}")
    
    if result.next_exercises:
        click.echo("\n🎯 Recommended Next Exercises:")
        for next_ex in result.next_exercises:
            click.echo(f"  • {next_ex}")


def display_chemistry_metrics(metrics: ChemistryMetrics):
    """Display team chemistry metrics"""
    click.echo("\n🧪 Team Chemistry Assessment:")
    click.echo("=" * 40)
    click.echo(f"Communication Fluency: {metrics.communication_fluency:.1%}")
    click.echo(f"Role Clarity:          {metrics.role_clarity:.1%}")
    click.echo(f"Collaboration Rhythm:  {metrics.collaboration_rhythm:.1%}")
    click.echo(f"Quality Integration:    {metrics.quality_integration:.1%}")
    click.echo("-" * 40)
    click.echo(f"Overall Chemistry:     {metrics.overall_chemistry:.1%}")
    
    # Provide interpretation
    if metrics.overall_chemistry >= 0.9:
        click.echo("🎉 Excellent team chemistry!")
    elif metrics.overall_chemistry >= 0.8:
        click.echo("✅ Good team chemistry with room for optimization")
    elif metrics.overall_chemistry >= 0.7:
        click.echo("⚠️ Moderate team chemistry - continued development needed")
    else:
        click.echo("❌ Poor team chemistry - focus on foundational exercises")


if __name__ == '__main__':
    main()