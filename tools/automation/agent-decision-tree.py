#!/usr/bin/env python3
"""
Agent Decision Tree for AI-First SDLC Framework

Provides structured decision trees for agent selection based on scenarios.
Replaces ad-hoc "proactive" usage with deterministic agent sequences.
"""

import click
import json
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from enum import Enum


class ScenarioType(Enum):
    """Common development scenarios."""
    NEW_FEATURE = "new_feature"
    BUG_FIX = "bug_fix"
    PERFORMANCE_ISSUE = "performance_issue"
    SECURITY_ISSUE = "security_issue"
    DEPLOYMENT = "deployment"
    ARCHITECTURE_CHANGE = "architecture_change"
    CODE_REVIEW = "code_review"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    COMPLIANCE = "compliance"
    INCIDENT = "incident"
    MIGRATION = "migration"


class AgentDecisionTree:
    """Manages agent selection decision trees."""
    
    def __init__(self, project_path: Path = None):
        self.project_path = project_path or Path.cwd()
        self.level_file = self.project_path / '.sdlc' / 'level.json'
        self.current_level = self._get_current_level()
        self.decision_trees = self._load_decision_trees()
        
    def _get_current_level(self) -> str:
        """Get current SDLC level."""
        if self.level_file.exists():
            with open(self.level_file) as f:
                return json.load(f).get('level', 'production')
        return 'production'
        
    def _load_decision_trees(self) -> Dict:
        """Load decision tree configurations."""
        return {
            ScenarioType.NEW_FEATURE: {
                'description': 'Implementing a new feature or capability',
                'initial_questions': [
                    {
                        'question': 'Is this a major architectural change?',
                        'yes': ['solution-architect', 'security-architect', 'performance-engineer'],
                        'no': ['solution-architect']
                    },
                    {
                        'question': 'Does this involve external integrations?',
                        'yes': ['integration-orchestrator'],
                        'no': []
                    },
                    {
                        'question': 'Does this handle sensitive data?',
                        'yes': ['security-architect', 'compliance-auditor'],
                        'no': []
                    }
                ],
                'mandatory_sequence': [
                    'critical-goal-reviewer',  # Always review against goals
                    'test-manager'  # Always plan testing
                ],
                'level_specific': {
                    'prototype': ['solution-architect', 'critical-goal-reviewer'],
                    'production': ['solution-architect', 'security-architect', 'test-manager', 'critical-goal-reviewer'],
                    'enterprise': ['solution-architect', 'security-architect', 'performance-engineer', 'compliance-auditor', 'test-manager', 'critical-goal-reviewer']
                }
            },
            
            ScenarioType.BUG_FIX: {
                'description': 'Fixing a bug or defect',
                'initial_questions': [
                    {
                        'question': 'Is this a security vulnerability?',
                        'yes': ['security-architect', 'sre-specialist'],
                        'no': []
                    },
                    {
                        'question': 'Is this a performance issue?',
                        'yes': ['performance-engineer'],
                        'no': []
                    },
                    {
                        'question': 'Does this affect multiple systems?',
                        'yes': ['integration-orchestrator'],
                        'no': []
                    }
                ],
                'mandatory_sequence': [
                    'critical-goal-reviewer',  # Ensure fix aligns with goals
                    'test-manager',  # Ensure proper testing
                    'ai-test-engineer'  # Regression testing
                ]
            },
            
            ScenarioType.PERFORMANCE_ISSUE: {
                'description': 'Addressing performance problems',
                'mandatory_sequence': [
                    'performance-engineer',  # Lead performance analysis
                    'sre-specialist',  # Production insights
                    'solution-architect',  # Architectural impact
                    'test-manager'  # Performance testing
                ]
            },
            
            ScenarioType.SECURITY_ISSUE: {
                'description': 'Addressing security vulnerabilities',
                'mandatory_sequence': [
                    'security-architect',  # Lead security response
                    'compliance-auditor',  # Compliance implications
                    'sre-specialist',  # Production impact
                    'critical-goal-reviewer'  # Ensure proper resolution
                ],
                'escalation': 'immediate'
            },
            
            ScenarioType.DEPLOYMENT: {
                'description': 'Deploying to production',
                'mandatory_sequence': [
                    'sre-specialist',  # Production readiness
                    'security-architect',  # Security clearance
                    'compliance-auditor',  # Compliance check
                    'performance-engineer'  # Performance validation
                ],
                'level_specific': {
                    'prototype': ['sre-specialist'],
                    'production': ['sre-specialist', 'security-architect'],
                    'enterprise': ['sre-specialist', 'security-architect', 'compliance-auditor', 'performance-engineer']
                }
            },
            
            ScenarioType.ARCHITECTURE_CHANGE: {
                'description': 'Making architectural changes',
                'mandatory_sequence': [
                    'solution-architect',  # Lead architecture
                    'security-architect',  # Security review
                    'performance-engineer',  # Performance impact
                    'integration-orchestrator',  # Integration impact
                    'critical-goal-reviewer'  # Goal alignment
                ],
                'requires_consensus': True
            },
            
            ScenarioType.CODE_REVIEW: {
                'description': 'Reviewing code changes',
                'initial_questions': [
                    {
                        'question': 'Is this AI/ML code?',
                        'yes': ['ai-solution-architect', 'ai-test-engineer'],
                        'no': []
                    },
                    {
                        'question': 'Is this infrastructure code?',
                        'yes': ['devops-specialist', 'sre-specialist'],
                        'no': []
                    }
                ],
                'mandatory_sequence': [
                    'critical-goal-reviewer',
                    'test-manager'
                ]
            },
            
            ScenarioType.TESTING: {
                'description': 'Planning or implementing tests',
                'initial_questions': [
                    {
                        'question': 'Is this for AI/ML systems?',
                        'yes': ['ai-test-engineer'],
                        'no': []
                    },
                    {
                        'question': 'Is this integration testing?',
                        'yes': ['integration-orchestrator'],
                        'no': []
                    },
                    {
                        'question': 'Is this performance testing?',
                        'yes': ['performance-engineer'],
                        'no': []
                    }
                ],
                'mandatory_sequence': ['test-manager']
            },
            
            ScenarioType.DOCUMENTATION: {
                'description': 'Creating or updating documentation',
                'initial_questions': [
                    {
                        'question': 'Is this technical documentation?',
                        'yes': ['technical-writer', 'documentation-architect'],
                        'no': ['technical-writer']
                    },
                    {
                        'question': 'Is this architecture documentation?',
                        'yes': ['solution-architect'],
                        'no': []
                    }
                ]
            },
            
            ScenarioType.COMPLIANCE: {
                'description': 'Compliance and audit activities',
                'mandatory_sequence': [
                    'compliance-auditor',
                    'security-architect',
                    'documentation-architect'
                ]
            },
            
            ScenarioType.INCIDENT: {
                'description': 'Production incident response',
                'mandatory_sequence': [
                    'sre-specialist',  # Immediate response
                    'security-architect',  # Security assessment
                    'performance-engineer',  # Performance impact
                    'critical-goal-reviewer'  # Post-mortem
                ],
                'escalation': 'immediate'
            },
            
            ScenarioType.MIGRATION: {
                'description': 'System or data migration',
                'mandatory_sequence': [
                    'solution-architect',  # Migration architecture
                    'devops-specialist',  # Infrastructure changes
                    'integration-orchestrator',  # System coordination
                    'test-manager',  # Migration testing
                    'sre-specialist'  # Production cutover
                ]
            }
        }
        
    def get_agents_for_scenario(self, scenario: ScenarioType, answers: Dict[str, bool] = None) -> List[str]:
        """Get ordered list of agents for a scenario."""
        if scenario not in self.decision_trees:
            return []
            
        tree = self.decision_trees[scenario]
        agents = []
        
        # Check level-specific overrides first
        if 'level_specific' in tree and self.current_level in tree['level_specific']:
            return tree['level_specific'][self.current_level]
        
        # Process initial questions if answers provided
        if 'initial_questions' in tree and answers:
            for question_config in tree['initial_questions']:
                question = question_config['question']
                if question in answers:
                    answer = 'yes' if answers[question] else 'no'
                    agents.extend(question_config.get(answer, []))
        
        # Add mandatory sequence
        mandatory = tree.get('mandatory_sequence', [])
        for agent in mandatory:
            if agent not in agents:
                agents.append(agent)
                
        return agents
        
    def get_questions_for_scenario(self, scenario: ScenarioType) -> List[str]:
        """Get questions that need answering for a scenario."""
        if scenario not in self.decision_trees:
            return []
            
        tree = self.decision_trees[scenario]
        questions = []
        
        if 'initial_questions' in tree:
            for q in tree['initial_questions']:
                questions.append(q['question'])
                
        return questions
        
    def requires_consensus(self, scenario: ScenarioType) -> bool:
        """Check if scenario requires agent consensus."""
        tree = self.decision_trees.get(scenario, {})
        return tree.get('requires_consensus', False)
        
    def get_escalation_priority(self, scenario: ScenarioType) -> str:
        """Get escalation priority for scenario."""
        tree = self.decision_trees.get(scenario, {})
        return tree.get('escalation', 'normal')


@click.group()
def cli():
    """Agent Decision Tree - Structured agent selection for scenarios"""
    pass


@cli.command()
def scenarios():
    """List all available scenarios."""
    click.echo("📋 Available Scenarios:")
    for scenario in ScenarioType:
        dt = AgentDecisionTree()
        tree = dt.decision_trees.get(scenario, {})
        desc = tree.get('description', 'No description')
        click.echo(f"\n{scenario.value}:")
        click.echo(f"   {desc}")
        

@cli.command()
@click.argument('scenario')
@click.option('--answer', '-a', multiple=True, help='Answer to question (format: "question=yes/no")')
def agents(scenario, answer):
    """Get agents for a specific scenario."""
    try:
        scenario_type = ScenarioType(scenario)
    except ValueError:
        click.echo(f"❌ Unknown scenario: {scenario}")
        click.echo("Run 'agent-decision-tree scenarios' to see available options")
        return
        
    dt = AgentDecisionTree()
    
    # Parse answers
    answers = {}
    for a in answer:
        if '=' in a:
            q, v = a.split('=', 1)
            answers[q] = v.lower() in ['yes', 'true', '1']
    
    # Get questions first if not all answered
    questions = dt.get_questions_for_scenario(scenario_type)
    unanswered = [q for q in questions if q not in answers]
    
    if unanswered and questions:
        click.echo(f"❓ Answer these questions for scenario '{scenario}':")
        for q in unanswered:
            click.echo(f"   • {q}")
        click.echo("\nExample: --answer \"Is this a major architectural change?=yes\"")
        return
    
    # Get agents
    agents = dt.get_agents_for_scenario(scenario_type, answers)
    
    click.echo(f"🤖 Agents for '{scenario}' (Level: {dt.current_level}):")
    for i, agent in enumerate(agents, 1):
        click.echo(f"   {i}. {agent}")
        
    if dt.requires_consensus(scenario_type):
        click.echo("\n⚠️  This scenario requires consensus among all agents")
        
    if dt.get_escalation_priority(scenario_type) == 'immediate':
        click.echo("\n🚨 This scenario requires immediate escalation")
        

@cli.command()
@click.argument('scenario')
def questions(scenario):
    """Show questions for a scenario."""
    try:
        scenario_type = ScenarioType(scenario)
    except ValueError:
        click.echo(f"❌ Unknown scenario: {scenario}")
        return
        
    dt = AgentDecisionTree()
    questions = dt.get_questions_for_scenario(scenario_type)
    
    if questions:
        click.echo(f"❓ Questions for scenario '{scenario}':")
        for q in questions:
            click.echo(f"   • {q}")
    else:
        click.echo(f"No questions needed for scenario '{scenario}'")
        

@cli.command()
@click.argument('current_scenario')
@click.argument('next_scenario')
def sequence(current_scenario, next_scenario):
    """Show agent handoff sequence between scenarios."""
    dt = AgentDecisionTree()
    
    try:
        current = ScenarioType(current_scenario)
        next_type = ScenarioType(next_scenario)
    except ValueError as e:
        click.echo(f"❌ Unknown scenario: {e}")
        return
        
    current_agents = dt.get_agents_for_scenario(current)
    next_agents = dt.get_agents_for_scenario(next_type)
    
    # Find handoff agent (last of current, first of next)
    handoff_from = current_agents[-1] if current_agents else None
    handoff_to = next_agents[0] if next_agents else None
    
    click.echo(f"🔄 Scenario transition: {current_scenario} → {next_scenario}")
    if handoff_from and handoff_to:
        click.echo(f"   Handoff: {handoff_from} → {handoff_to}")
    
    # Show full sequence
    click.echo(f"\n📋 Complete agent sequence:")
    all_agents = current_agents + [a for a in next_agents if a not in current_agents]
    for i, agent in enumerate(all_agents, 1):
        if agent in current_agents and agent in next_agents:
            click.echo(f"   {i}. {agent} (both scenarios)")
        elif agent in current_agents:
            click.echo(f"   {i}. {agent} ({current_scenario})")
        else:
            click.echo(f"   {i}. {agent} ({next_scenario})")


if __name__ == '__main__':
    cli()