#!/usr/bin/env python3
"""
A2A Communication System Demo
Demonstrates the Billy Wright tactical formation in action
"""

import click
import importlib.util
import sys
from pathlib import Path

# Add the tools directory to path so we can import the orchestrator
sys.path.append(str(Path(__file__).parent))

# Import with the correct module name (dash becomes underscore)

spec = importlib.util.spec_from_file_location(
    "a2a_orchestrator", Path(__file__).parent / "a2a-orchestrator.py"
)
a2a_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a2a_module)

A2AOrchestrator = a2a_module.A2AOrchestrator
AgentMessage = a2a_module.AgentMessage


def demo_feature_development():
    """Demo: New Feature Development Workflow"""
    print("🎯 DEMO SCENARIO: AI Recommendation Engine Feature")
    print("=" * 60)

    orchestrator = A2AOrchestrator()

    # 1. Start the workflow
    print("\n1. 📋 Starting Feature Development Workflow...")
    orchestrator.start_workflow(
        "feature_development",
        "product-owner",
        "AI-powered recommendation engine for e-commerce platform",
    )

    # 2. Initial request routing
    print("\n2. 🎯 Routing Initial Requirements...")
    suggestions = orchestrator.route_message(
        "product-owner",
        "Need AI recommendation engine with real-time personalization and scalability to 1M+ users",
    )
    print(f"   Routing suggestions: {', '.join(suggestions)}")

    # 3. Architecture coordination
    print("\n3. 🏗️  Solution Architect Coordinates Design...")
    arch_msg = orchestrator.create_message(
        sender="solution-architect",
        receiver="ai-solution-architect",
        message_type="request",
        content=(
            "DESIGN_REQUEST: AI recommendation engine | Requirements: real-time personalization, "
            "scalable to 1M+ users | Integration: existing e-commerce API"
        ),
        priority="HIGH",
        context="New feature development workflow",
    )
    orchestrator.send_message(arch_msg)

    # 4. AI architect responds with design
    print("\n4. 🧠 AI Solution Architect Designs System...")
    ai_design_msg = orchestrator.create_message(
        sender="ai-solution-architect",
        receiver="python-expert",
        message_type="handoff",
        content=(
            "AI_DESIGN: Recommendation system | Architecture: ML pipeline with real-time inference API | "
            "Tech Stack: Python, TensorFlow, Redis cache | API: RESTful with WebSocket for real-time updates"
        ),
        priority="HIGH",
        context="Feature implementation handoff",
    )
    orchestrator.send_message(ai_design_msg)

    # 5. Implementation and testing coordination
    print("\n5. ⚡ Implementation Team Coordinates...")
    impl_msg = orchestrator.create_message(
        sender="python-expert",
        receiver="ai-test-engineer",
        message_type="status_update",
        content=(
            "IMPLEMENTATION_PROGRESS: ML pipeline 80% complete | Next: API integration and caching layer | "
            "Testing needed: model accuracy, inference latency"
        ),
        priority="MED",
        context="Implementation progress update",
    )
    orchestrator.send_message(impl_msg)

    # 6. Quality validation
    print("\n6. 🥅 Quality Validation...")
    validation_msg = orchestrator.create_message(
        sender="ai-test-engineer",
        receiver="critical-goal-reviewer",
        message_type="request",
        content=(
            "QUALITY_VALIDATION: AI recommendation engine | Test Results: 94% accuracy, <50ms inference time | "
            "Coverage: 89% | Ready for acceptance review"
        ),
        priority="HIGH",
        context="Quality gate for production readiness",
    )
    orchestrator.send_message(validation_msg)

    print(
        f"\n✅ Workflow Complete! Feature development coordinated through {len(orchestrator.message_history)} messages"
    )
    return orchestrator


def demo_performance_crisis():
    """Demo: Performance Crisis Resolution"""
    print("\n\n🚨 DEMO SCENARIO: Performance Crisis")
    print("=" * 60)

    orchestrator = A2AOrchestrator()

    # 1. Crisis detection
    print("\n1. 📊 Performance Issue Detected...")
    crisis_msg = orchestrator.create_message(
        sender="monitoring-system",
        receiver="performance-engineer",
        message_type="escalation",
        content="PERF_ALERT: API response time | Current: 3.2s | Threshold: 1.0s | Impact: All users affected",
        priority="HIGH",
        context="Critical performance degradation",
        requires_response=True,
        deadline_hours=1,
    )
    orchestrator.send_message(crisis_msg)

    # 2. Escalation to SRE
    print("\n2. 🚨 Escalating to SRE Specialist...")
    orchestrator.escalate_issue(
        "performance-engineer",
        "Critical performance degradation: 300% slower response times affecting all users",
        "HIGH",
    )

    # 3. SRE coordinates resolution
    print("\n3. 🔧 SRE Coordinates Crisis Response...")
    sre_msg = orchestrator.create_message(
        sender="sre-specialist",
        receiver="devops-specialist",
        message_type="escalation",
        content=(
            "CRISIS_RESPONSE: Scale infrastructure immediately | Current load: 300% of normal | "
            "Action: Auto-scaling + cache optimization"
        ),
        priority="HIGH",
        context="Crisis response coordination",
    )
    orchestrator.send_message(sre_msg)

    # 4. Resolution and learning
    print("\n4. 💡 Resolution and Learning...")
    resolution_msg = orchestrator.create_message(
        sender="retrospective-miner",
        receiver="agile-coach",
        message_type="handoff",
        content=(
            "CRISIS_RETROSPECTIVE: Root cause - cache invalidation storm | Resolution: Circuit breaker pattern | "
            "Prevention: Enhanced monitoring alerts"
        ),
        priority="MED",
        context="Crisis lessons learned",
    )
    orchestrator.send_message(resolution_msg)

    print(
        f"\n✅ Crisis Resolved! Coordinated response through {len(orchestrator.message_history)} critical messages"
    )
    return orchestrator


def demo_communication_analysis():
    """Demo: Team Communication Analysis"""
    print("\n\n📊 DEMO: Communication Analysis")
    print("=" * 60)

    # Run both previous demos to generate message history
    orchestrator1 = demo_feature_development()
    orchestrator2 = demo_performance_crisis()

    # Combine message histories for analysis
    all_messages = orchestrator1.message_history + orchestrator2.message_history

    # Create combined orchestrator for analysis
    combined_orchestrator = A2AOrchestrator()
    combined_orchestrator.message_history = all_messages

    print("\n📈 Communication Effectiveness Analysis:")
    analysis = combined_orchestrator.analyze_communication_patterns()

    print(f"   Total Messages: {analysis['total_messages']}")
    print(f"   Escalation Rate: {analysis['escalation_rate']:.1f}%")

    print("\n   By Priority:")
    for priority, count in analysis["by_priority"].items():
        print(f"     {priority}: {count} messages")

    print("\n   By Type:")
    for msg_type, count in analysis["by_type"].items():
        print(f"     {msg_type}: {count} messages")

    print("\n   Most Active Agents:")
    sorted_agents = sorted(
        analysis["most_active_agents"].items(), key=lambda x: x[1], reverse=True
    )
    for agent, count in sorted_agents[:5]:
        print(f"     {agent}: {count} messages")

    return combined_orchestrator


def demo_team_formation():
    """Demo: Team Formation Analysis"""
    print("\n\n🏈 DEMO: Billy Wright Team Formation")
    print("=" * 60)

    orchestrator = A2AOrchestrator()
    formation = orchestrator.get_team_formation()

    for role, agents in formation.items():
        if agents:
            print(f"\n{role.upper()}:")
            for agent in agents:
                if agent in orchestrator.agent_capabilities:
                    capability = orchestrator.agent_capabilities[agent]
                    specializations = ", ".join(capability.specializations)
                    print(f"  • {agent}: {specializations}")

                    # Show communication patterns
                    print(
                        f"    → Passes to: {', '.join(capability.primary_passes_to[:3])}"
                    )
                    if len(capability.primary_passes_to) > 3:
                        print(
                            f"      (and {len(capability.primary_passes_to) - 3} others)"
                        )


@click.command()
@click.option(
    "--demo",
    type=click.Choice(["all", "feature", "crisis", "analysis", "formation"]),
    default="all",
    help="Which demo to run",
)
def main(demo):
    """Run A2A Communication System demonstrations"""

    print("🎪 AGENT-TO-AGENT COMMUNICATION SYSTEM DEMO")
    print("Billy Wright Tactical Formation in Action")
    print("=" * 70)

    if demo in ["all", "formation"]:
        demo_team_formation()

    if demo in ["all", "feature"]:
        demo_feature_development()

    if demo in ["all", "crisis"]:
        demo_performance_crisis()

    if demo in ["all", "analysis"]:
        demo_communication_analysis()

    print("\n" + "=" * 70)
    print("🏆 DEMO COMPLETE!")
    print("The Billy Wright formation enables legendary agent coordination!")
    print("\nNext Steps:")
    print("1. Review the tactical discussion: docs/A2A-TACTICAL-TEAM-DISCUSSION.md")
    print("2. Study the usage guide: docs/A2A-USAGE-GUIDE.md")
    print(
        "3. Customize communication protocols: agents/a2a-communication-protocols.yaml"
    )
    print("4. Start using: python tools/automation/a2a-orchestrator.py --help")


if __name__ == "__main__":
    main()
