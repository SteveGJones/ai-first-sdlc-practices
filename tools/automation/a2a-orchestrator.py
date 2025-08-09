#!/usr/bin/env python3
"""
Agent-to-Agent Communication Orchestrator

This tool implements the Billy Wright tactical communication patterns
identified in our team discussion. It provides structured coordination
for multi-agent workflows with proper message passing and escalation.

Based on the A2A Tactical Team Discussion findings.
"""

import yaml
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import click


@dataclass
class AgentMessage:
    """Structured message format for agent communication"""

    id: str
    sender: str
    receiver: str
    message_type: str  # request, status_update, escalation, handoff
    content: str
    priority: str  # HIGH, MED, LOW
    context: str
    timestamp: datetime
    requires_response: bool = False
    deadline: Optional[datetime] = None

    def to_dict(self) -> Dict:
        result = asdict(self)
        result["timestamp"] = self.timestamp.isoformat()
        if self.deadline:
            result["deadline"] = self.deadline.isoformat()
        return result


@dataclass
class AgentCapability:
    """Agent capability and communication pattern definition"""

    name: str
    role: str  # goalkeeper, defender, midfielder, playmaker, striker
    position: str  # specific position like "solution-architect"
    primary_passes_to: List[str]
    receives_from: List[str]
    escalation_targets: List[str]
    specializations: List[str]
    communication_patterns: Dict[str, str]


class A2AOrchestrator:
    """Orchestrates agent-to-agent communication workflows"""

    def __init__(self, config_path: str = "agents/agent-compositions.yaml"):
        self.config_path = Path(config_path)
        self.message_history: List[AgentMessage] = []
        self.active_workflows: Dict[str, Dict] = {}
        self.agent_capabilities: Dict[str, AgentCapability] = {}
        self.load_configurations()

    def load_configurations(self):
        """Load agent configurations and communication patterns"""
        try:
            if self.config_path.exists():
                with open(self.config_path, "r") as f:
                    config = yaml.safe_load(f)
                self._parse_agent_config(config)
        except Exception as e:
            click.echo(f"Warning: Could not load config from {self.config_path}: {e}")
            self._load_default_formation()

    def _load_default_formation(self):
        """Load the Billy Wright tactical formation from our team discussion"""
        formation = {
            # Goalkeepers
            "critical-goal-reviewer": AgentCapability(
                name="critical-goal-reviewer",
                role="goalkeeper",
                position="quality-validator",
                primary_passes_to=["solution-architect", "delivery-manager"],
                receives_from=["all"],
                escalation_targets=["sdlc-enforcer"],
                specializations=["quality-validation", "objective-assessment"],
                communication_patterns={
                    "validates": "solution quality against objectives",
                    "escalates": "quality gaps to solution-architect",
                    "reports": "completion status to delivery-manager",
                },
            ),
            "sdlc-enforcer": AgentCapability(
                name="sdlc-enforcer",
                role="goalkeeper",
                position="compliance-referee",
                primary_passes_to=["framework-validator", "compliance-auditor"],
                receives_from=["all"],
                escalation_targets=["compliance-auditor"],
                specializations=["compliance-enforcement", "process-governance"],
                communication_patterns={
                    "monitors": "all agent activities for compliance",
                    "alerts": "compliance violations immediately",
                    "guides": "proper framework usage",
                },
            ),
            # Defenders
            "compliance-auditor": AgentCapability(
                name="compliance-auditor",
                role="defender",
                position="compliance-specialist",
                primary_passes_to=["documentation-architect", "delivery-manager"],
                receives_from=["sdlc-enforcer", "security-architect"],
                escalation_targets=["delivery-manager"],
                specializations=["regulatory-compliance", "audit-trails"],
                communication_patterns={
                    "audits": "all processes for compliance gaps",
                    "documents": "compliance evidence and audit trails",
                    "blocks": "non-compliant activities",
                },
            ),
            "framework-validator": AgentCapability(
                name="framework-validator",
                role="defender",
                position="structure-enforcer",
                primary_passes_to=["solution-architect"],
                receives_from=["sdlc-enforcer", "all"],
                escalation_targets=["sdlc-enforcer"],
                specializations=["framework-adherence", "structure-validation"],
                communication_patterns={
                    "validates": "framework structure and compliance",
                    "recommends": "structural improvements",
                    "enforces": "framework standards",
                },
            ),
            # Midfielders
            "solution-architect": AgentCapability(
                name="solution-architect",
                role="midfielder",
                position="team-captain",
                primary_passes_to=[
                    "ai-solution-architect",
                    "python-expert",
                    "devops-specialist",
                ],
                receives_from=["all"],
                escalation_targets=["critical-goal-reviewer"],
                specializations=["system-architecture", "technical-leadership"],
                communication_patterns={
                    "coordinates": "all technical decisions",
                    "designs": "system architecture and patterns",
                    "distributes": "work to specialist agents",
                },
            ),
            "agile-coach": AgentCapability(
                name="agile-coach",
                role="midfielder",
                position="process-coordinator",
                primary_passes_to=["delivery-manager", "retrospective-miner"],
                receives_from=["all"],
                escalation_targets=["delivery-manager"],
                specializations=["agile-facilitation", "team-coordination"],
                communication_patterns={
                    "facilitates": "cross-agent ceremonies and coordination",
                    "coaches": "optimal team communication patterns",
                    "optimizes": "workflow efficiency",
                },
            ),
            # Playmakers
            "ai-solution-architect": AgentCapability(
                name="ai-solution-architect",
                role="playmaker",
                position="ai-specialist",
                primary_passes_to=["mcp-server-architect", "ai-test-engineer"],
                receives_from=["solution-architect", "prompt-engineer"],
                escalation_targets=["solution-architect"],
                specializations=["ai-architecture", "intelligent-systems"],
                communication_patterns={
                    "designs": "AI-specific system architectures",
                    "coordinates": "AI agent interactions",
                    "optimizes": "AI system performance",
                },
            ),
            # Strikers
            "python-expert": AgentCapability(
                name="python-expert",
                role="striker",
                position="implementation-specialist",
                primary_passes_to=["ai-test-engineer", "performance-engineer"],
                receives_from=["solution-architect", "ai-solution-architect"],
                escalation_targets=["solution-architect"],
                specializations=["python-implementation", "code-quality"],
                communication_patterns={
                    "implements": "technical designs with precision",
                    "delivers": "production-ready code",
                    "validates": "implementation against architecture",
                },
            ),
        }

        self.agent_capabilities = formation

    def _parse_agent_config(self, config: Dict):
        """Parse YAML configuration into agent capabilities"""
        # Implementation for parsing existing config format
        # This would adapt the current agent-compositions.yaml format

    def create_message(
        self,
        sender: str,
        receiver: str,
        message_type: str,
        content: str,
        priority: str = "MED",
        context: str = "",
        requires_response: bool = False,
        deadline_hours: Optional[int] = None,
    ) -> AgentMessage:
        """Create a structured agent message"""

        message_id = str(uuid.uuid4())[:8]
        deadline = None
        if deadline_hours:
            deadline = datetime.now() + timedelta(hours=deadline_hours)

        message = AgentMessage(
            id=message_id,
            sender=sender,
            receiver=receiver,
            message_type=message_type,
            content=content,
            priority=priority,
            context=context,
            timestamp=datetime.now(),
            requires_response=requires_response,
            deadline=deadline,
        )

        self.message_history.append(message)
        return message

    def send_message(self, message: AgentMessage) -> bool:
        """Send message and validate receiver capability"""
        if message.receiver not in self.agent_capabilities and message.receiver != "all":
            click.echo(f"⚠️  Warning: Receiver '{message.receiver}' not found in agent formation")
            return False

        click.echo(f"📨 {message.sender} → {message.receiver}: {message.content}")
        if message.priority == "HIGH":
            click.echo(f"🚨 HIGH PRIORITY MESSAGE - Deadline: {message.deadline}")

        return True

    def route_message(self, sender: str, content: str, **kwargs) -> List[str]:
        """Intelligently route message to appropriate agents"""
        if sender not in self.agent_capabilities:
            return ["solution-architect"]  # Default routing

        sender_agent = self.agent_capabilities[sender]

        # Route based on content analysis and sender's primary passes
        suggested_receivers = []

        # Check for keywords that suggest specific routing
        content_lower = content.lower()

        if any(word in content_lower for word in ["security", "vulnerability", "threat"]):
            suggested_receivers.append("security-architect")
        if any(word in content_lower for word in ["performance", "slow", "optimization"]):
            suggested_receivers.append("performance-engineer")
        if any(word in content_lower for word in ["test", "validation", "quality"]):
            suggested_receivers.append("ai-test-engineer")
        if any(word in content_lower for word in ["deploy", "infrastructure", "scaling"]):
            suggested_receivers.append("devops-specialist")

        # If no specific routing found, use sender's primary pass targets
        if not suggested_receivers:
            suggested_receivers = sender_agent.primary_passes_to

        return suggested_receivers

    def start_workflow(self, workflow_name: str, initiator: str, description: str) -> str:
        """Start a coordinated multi-agent workflow"""
        workflow_id = str(uuid.uuid4())[:8]

        workflow = {
            "id": workflow_id,
            "name": workflow_name,
            "initiator": initiator,
            "description": description,
            "status": "active",
            "created_at": datetime.now().isoformat(),
            "participants": [],
            "messages": [],
            "milestones": [],
        }

        self.active_workflows[workflow_id] = workflow

        # Route initial workflow setup based on workflow type
        if workflow_name == "feature_development":
            sequence = [
                "solution-architect",
                "ai-solution-architect",
                "python-expert",
                "ai-test-engineer",
                "critical-goal-reviewer",
            ]
        elif workflow_name == "issue_resolution":
            sequence = [
                "sre-specialist",
                "relevant-specialist",
                "test-manager",
                "retrospective-miner",
            ]
        else:
            sequence = ["solution-architect"]  # Default

        workflow["planned_sequence"] = sequence

        click.echo(f"🚀 Started workflow '{workflow_name}' (ID: {workflow_id})")
        click.echo(f"📋 Planned sequence: {' → '.join(sequence)}")

        return workflow_id

    def get_workflow_status(self, workflow_id: str) -> Dict:
        """Get current status of a workflow"""
        if workflow_id not in self.active_workflows:
            return {"error": "Workflow not found"}

        return self.active_workflows[workflow_id]

    def escalate_issue(self, agent: str, issue: str, urgency: str = "HIGH") -> bool:
        """Escalate issue through proper channels"""
        if agent not in self.agent_capabilities:
            click.echo(f"❌ Agent {agent} not found in formation")
            return False

        escalation_targets = self.agent_capabilities[agent].escalation_targets

        for target in escalation_targets:
            escalation_msg = self.create_message(
                sender=agent,
                receiver=target,
                message_type="escalation",
                content=issue,
                priority=urgency,
                context=f"Escalated from {agent}",
                requires_response=True,
                deadline_hours=2 if urgency == "HIGH" else 24,
            )

            self.send_message(escalation_msg)
            click.echo(f"🚨 Issue escalated: {agent} → {target}")

        return True

    def get_team_formation(self) -> Dict[str, List[str]]:
        """Get current team formation by role"""
        formation = {
            "goalkeepers": [],
            "defenders": [],
            "midfielders": [],
            "playmakers": [],
            "strikers": [],
        }

        for agent_name, capability in self.agent_capabilities.items():
            if capability.role in formation:
                formation[capability.role].append(agent_name)

        return formation

    def analyze_communication_patterns(self) -> Dict[str, Any]:
        """Analyze communication effectiveness and patterns"""
        if not self.message_history:
            return {"status": "No messages to analyze"}

        analysis = {
            "total_messages": len(self.message_history),
            "by_priority": {"HIGH": 0, "MED": 0, "LOW": 0},
            "by_type": {},
            "most_active_agents": {},
            "response_times": [],
            "escalation_rate": 0,
        }

        for msg in self.message_history:
            analysis["by_priority"][msg.priority] += 1
            analysis["by_type"][msg.message_type] = analysis["by_type"].get(msg.message_type, 0) + 1

            # Track agent activity
            analysis["most_active_agents"][msg.sender] = analysis["most_active_agents"].get(msg.sender, 0) + 1

            if msg.message_type == "escalation":
                analysis["escalation_rate"] += 1

        analysis["escalation_rate"] = (analysis["escalation_rate"] / len(self.message_history)) * 100

        return analysis


@click.group()
def cli():
    """Agent-to-Agent Communication Orchestrator - Billy Wright Formation"""


@cli.command()
@click.option("--sender", required=True, help="Agent sending the message")
@click.option("--receiver", required=True, help="Agent receiving the message")
@click.option("--content", required=True, help="Message content")
@click.option("--priority", default="MED", type=click.Choice(["HIGH", "MED", "LOW"]))
@click.option(
    "--type",
    "msg_type",
    default="request",
    type=click.Choice(["request", "status_update", "escalation", "handoff"]),
)
@click.option("--context", default="", help="Additional context")
@click.option("--deadline-hours", type=int, help="Deadline in hours")
def send(sender, receiver, content, priority, msg_type, context, deadline_hours):
    """Send a structured message between agents"""
    orchestrator = A2AOrchestrator()

    message = orchestrator.create_message(
        sender=sender,
        receiver=receiver,
        message_type=msg_type,
        content=content,
        priority=priority,
        context=context,
        deadline_hours=deadline_hours,
    )

    success = orchestrator.send_message(message)
    if success:
        click.echo(f"✅ Message sent successfully (ID: {message.id})")
    else:
        click.echo("❌ Failed to send message")


@cli.command()
@click.option("--sender", required=True, help="Agent requesting routing")
@click.option("--content", required=True, help="Content to route")
def route(sender, content):
    """Get routing suggestions for a message"""
    orchestrator = A2AOrchestrator()
    suggestions = orchestrator.route_message(sender, content)

    click.echo(f"📍 Routing suggestions for {sender}:")
    for receiver in suggestions:
        if receiver in orchestrator.agent_capabilities:
            role = orchestrator.agent_capabilities[receiver].role
            click.echo(f"  → {receiver} ({role})")
        else:
            click.echo(f"  → {receiver}")


@cli.command()
@click.option("--name", required=True, help="Workflow name")
@click.option("--initiator", required=True, help="Agent starting the workflow")
@click.option("--description", required=True, help="Workflow description")
def start_workflow(name, initiator, description):
    """Start a coordinated multi-agent workflow"""
    orchestrator = A2AOrchestrator()
    workflow_id = orchestrator.start_workflow(name, initiator, description)
    click.echo(f"✅ Workflow started with ID: {workflow_id}")


@cli.command()
@click.option("--agent", required=True, help="Agent escalating the issue")
@click.option("--issue", required=True, help="Issue to escalate")
@click.option("--urgency", default="HIGH", type=click.Choice(["HIGH", "MED", "LOW"]))
def escalate(agent, issue, urgency):
    """Escalate an issue through proper channels"""
    orchestrator = A2AOrchestrator()
    success = orchestrator.escalate_issue(agent, issue, urgency)
    if success:
        click.echo("✅ Issue escalated successfully")
    else:
        click.echo("❌ Escalation failed")


@cli.command()
def formation():
    """Show current team formation"""
    orchestrator = A2AOrchestrator()
    team_formation = orchestrator.get_team_formation()

    click.echo("🏈 CURRENT TEAM FORMATION (Billy Wright 4-3-3)")
    click.echo("=" * 50)

    for role, agents in team_formation.items():
        if agents:
            click.echo(f"\n{role.upper()}:")
            for agent in agents:
                if agent in orchestrator.agent_capabilities:
                    specializations = orchestrator.agent_capabilities[agent].specializations
                    click.echo(f"  • {agent} - {', '.join(specializations)}")
                else:
                    click.echo(f"  • {agent}")


@cli.command()
def analyze():
    """Analyze communication patterns and effectiveness"""
    orchestrator = A2AOrchestrator()
    analysis = orchestrator.analyze_communication_patterns()

    click.echo("📊 COMMUNICATION ANALYSIS")
    click.echo("=" * 30)

    if "status" in analysis:
        click.echo(analysis["status"])
        return

    click.echo(f"Total Messages: {analysis['total_messages']}")
    click.echo(f"Escalation Rate: {analysis['escalation_rate']:.1f}%")

    click.echo("\nBy Priority:")
    for priority, count in analysis["by_priority"].items():
        click.echo(f"  {priority}: {count}")

    click.echo("\nBy Type:")
    for msg_type, count in analysis["by_type"].items():
        click.echo(f"  {msg_type}: {count}")

    click.echo("\nMost Active Agents:")
    sorted_agents = sorted(analysis["most_active_agents"].items(), key=lambda x: x[1], reverse=True)
    for agent, count in sorted_agents[:5]:
        click.echo(f"  {agent}: {count} messages")


if __name__ == "__main__":
    cli()
