#!/usr/bin/env python3
"""
Agent Context Coordinator for AI-First SDLC
Manages memory coordination between specialized agents in shared Claude context
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import argparse
from dataclasses import dataclass, asdict
from enum import Enum


class AgentStatus(Enum):
    ACTIVE = "active"
    WAITING = "waiting"
    COMPLETE = "complete"
    BLOCKED = "blocked"
    HANDED_OFF = "handed_of"


@dataclass
class AgentMemoryBlock:
    agent_type: str
    session_context: str
    timestamp: str
    decisions_made: List[Dict[str, str]]
    current_focus: str
    status: AgentStatus
    handoff_notes: str
    expertise_tags: List[str]
    cross_agent_dependencies: List[str]

    def to_markdown(self) -> str:
        """Convert memory block to markdown format"""
        icon_map = {
            "solution-architect": "🏗️",
            "security-architect": "🔒",
            "performance-engineer": "⚡",
            "ai-test-engineer": "🧪",
            "devops-specialist": "🚀",
            "critical-goal-reviewer": "🎯",
        }

        icon = icon_map.get(self.agent_type, "🤖")

        md = f"## {icon} {self.agent_type.upper()} MEMORY BANK\n"
        md += f"**Session Context**: {self.timestamp} - {self.session_context}\n"
        md += f"**Current Focus**: {self.current_focus}\n"
        md += f"**Status**: {self.status.value.upper()}\n\n"

        if self.decisions_made:
            md += "**Decisions Made**:\n"
            for decision in self.decisions_made:
                md += f"- {decision['decision']}: {decision['rationale']} - {decision['timestamp']}\n"
            md += "\n"

        if self.expertise_tags:
            md += "**Expertise Tags**: " + ", ".join([f"#{tag}" for tag in self.expertise_tags]) + "\n\n"

        if self.cross_agent_dependencies:
            md += "**Cross-Agent Dependencies**:\n"
            for dep in self.cross_agent_dependencies:
                md += f"- {dep}\n"
            md += "\n"

        if self.handoff_notes:
            md += f"**Handoff Notes**: {self.handoff_notes}\n\n"

        md += "---\n\n"
        return md


@dataclass
class AgentTransition:
    from_agent: str
    to_agent: str
    timestamp: str
    context_transfer: str
    requirements: List[str]
    acknowledged: bool = False


@dataclass
class CollaborativeDecision:
    decision_id: str
    title: str
    participants: List[str]
    context: str
    agent_perspectives: Dict[str, str]
    consensus: str
    implementation_owner: str
    review_checkpoint: str
    timestamp: str


class AgentContextCoordinator:
    """Manages memory coordination between specialized agents"""

    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path.cwd()
        self.context_dir = self.project_root / ".ai-context"
        self.agent_memory_file = self.context_dir / "agent_memory.json"
        self.transitions_file = self.context_dir / "agent_transitions.json"
        self.decisions_file = self.context_dir / "collaborative_decisions.json"
        self._ensure_directories()

    def _ensure_directories(self):
        """Ensure context directories exist"""
        self.context_dir.mkdir(exist_ok=True)

        # Initialize files if they don't exist
        for file_path in [
            self.agent_memory_file,
            self.transitions_file,
            self.decisions_file,
        ]:
            if not file_path.exists():
                file_path.write_text("[]")

    def create_agent_memory_block(
        self,
        agent_type: str,
        session_context: str,
        current_focus: str,
        status: AgentStatus = AgentStatus.ACTIVE,
    ) -> str:
        """Create a new agent memory block"""

        memory_block = AgentMemoryBlock(
            agent_type=agent_type,
            session_context=session_context,
            timestamp=datetime.now().isoformat(),
            decisions_made=[],
            current_focus=current_focus,
            status=status,
            handoff_notes="",
            expertise_tags=[],
            cross_agent_dependencies=[],
        )

        # Save to memory
        memories = self._load_agent_memories()
        memories.append(asdict(memory_block))
        self._save_agent_memories(memories)

        # Generate markdown
        markdown = memory_block.to_markdown()
        print(f"✅ Agent memory block created for {agent_type}")
        print("\n" + markdown)

        return memory_block.timestamp

    def update_agent_memory(
        self,
        agent_type: str,
        decision: Optional[Dict[str, str]] = None,
        expertise_tag: Optional[str] = None,
        dependency: Optional[str] = None,
        handoff_notes: Optional[str] = None,
        status: Optional[AgentStatus] = None,
        current_focus: Optional[str] = None,
    ) -> bool:
        """Update an existing agent memory block"""

        memories = self._load_agent_memories()

        # Find the most recent memory block for this agent
        agent_memories = [m for m in memories if m["agent_type"] == agent_type]
        if not agent_memories:
            print(f"❌ No memory block found for {agent_type}")
            return False

        # Update the most recent memory
        latest_memory = max(agent_memories, key=lambda x: x["timestamp"])

        if decision:
            decision["timestamp"] = datetime.now().isoformat()
            latest_memory["decisions_made"].append(decision)

        if expertise_tag:
            if expertise_tag not in latest_memory["expertise_tags"]:
                latest_memory["expertise_tags"].append(expertise_tag)

        if dependency:
            if dependency not in latest_memory["cross_agent_dependencies"]:
                latest_memory["cross_agent_dependencies"].append(dependency)

        if handoff_notes:
            latest_memory["handoff_notes"] = handoff_notes

        if status:
            latest_memory["status"] = status.value

        if current_focus:
            latest_memory["current_focus"] = current_focus

        # Update timestamp
        latest_memory["timestamp"] = datetime.now().isoformat()

        # Save updated memories
        self._save_agent_memories(memories)

        print(f"✅ Updated memory block for {agent_type}")
        return True

    def create_agent_transition(
        self,
        from_agent: str,
        to_agent: str,
        context_transfer: str,
        requirements: List[str],
    ) -> str:
        """Document an agent transition/handof"""

        transition = AgentTransition(
            from_agent=from_agent,
            to_agent=to_agent,
            timestamp=datetime.now().isoformat(),
            context_transfer=context_transfer,
            requirements=requirements,
            acknowledged=False,
        )

        # Save transition
        transitions = self._load_transitions()
        transitions.append(asdict(transition))
        self._save_transitions(transitions)

        # Update agent statuses
        self.update_agent_memory(from_agent, status=AgentStatus.HANDED_OFF)
        self.update_agent_memory(
            to_agent,
            status=AgentStatus.ACTIVE,
            current_focus=f"Handoff from {from_agent}",
        )

        # Generate handoff markdown
        markdown = self._generate_handoff_markdown(transition)
        print(f"✅ Agent transition documented: {from_agent} → {to_agent}")
        print("\n" + markdown)

        return transition.timestamp

    def acknowledge_handoff(self, from_agent: str, to_agent: str) -> bool:
        """Acknowledge receipt of handof"""
        transitions = self._load_transitions()

        for transition in reversed(transitions):  # Most recent first
            if (
                transition["from_agent"] == from_agent
                and transition["to_agent"] == to_agent
                and not transition["acknowledged"]
            ):
                transition["acknowledged"] = True
                transition["acknowledged_at"] = datetime.now().isoformat()
                self._save_transitions(transitions)

                print(f"✅ Handoff acknowledged: {from_agent} → {to_agent}")
                return True

        print(f"❌ No pending handoff found: {from_agent} → {to_agent}")
        return False

    def create_collaborative_decision(
        self,
        title: str,
        participants: List[str],
        context: str,
        agent_perspectives: Dict[str, str],
        consensus: str,
        implementation_owner: str,
        review_checkpoint: str,
    ) -> str:
        """Document a multi-agent collaborative decision"""

        decision_id = f"decision_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        decision = CollaborativeDecision(
            decision_id=decision_id,
            title=title,
            participants=participants,
            context=context,
            agent_perspectives=agent_perspectives,
            consensus=consensus,
            implementation_owner=implementation_owner,
            review_checkpoint=review_checkpoint,
            timestamp=datetime.now().isoformat(),
        )

        # Save decision
        decisions = self._load_decisions()
        decisions.append(asdict(decision))
        self._save_decisions(decisions)

        # Generate decision markdown
        markdown = self._generate_decision_markdown(decision)
        print(f"✅ Collaborative decision documented: {decision_id}")
        print("\n" + markdown)

        return decision_id

    def generate_agent_status_board(self) -> str:
        """Generate current agent status board"""
        memories = self._load_agent_memories()

        # Get latest status for each agent
        agent_status = {}
        for memory in memories:
            agent = memory["agent_type"]
            if agent not in agent_status or memory["timestamp"] > agent_status[agent]["timestamp"]:
                agent_status[agent] = memory

        # Generate markdown table
        markdown = "## 👥 AGENT COLLABORATION STATUS\n\n"
        markdown += "| Agent | Current Task | Status | Next Action | Last Update |\n"
        markdown += "|-------|-------------|--------|-------------|-------------|\n"

        for agent, status in agent_status.items():
            current_task = status["current_focus"]
            agent_status_str = status["status"].upper()
            next_action = status.get("handoff_notes", "Continue current work")
            last_update = datetime.fromisoformat(status["timestamp"]).strftime("%Y-%m-%d %H:%M")

            markdown += f"| {agent} | {current_task} | {agent_status_str} | {next_action} | {last_update} |\n"

        # Add cross-agent dependencies
        dependencies = []
        for memory in memories:
            for dep in memory.get("cross_agent_dependencies", []):
                dependencies.append(dep)

        if dependencies:
            markdown += "\n**Cross-Agent Dependencies**:\n"
            for dep in set(dependencies):  # Remove duplicates
                markdown += f"- {dep}\n"

        return markdown

    def validate_context_integrity(self) -> Dict[str, Any]:
        """Validate the integrity of agent context coordination"""
        memories = self._load_agent_memories()
        transitions = self._load_transitions()
        decisions = self._load_decisions()

        # Check for memory coverage
        active_agents = [m for m in memories if m["status"] == "active"]
        agents_with_recent_updates = []

        cutoff_time = datetime.now()
        for memory in memories:
            memory_time = datetime.fromisoformat(memory["timestamp"])
            if (cutoff_time - memory_time).hours < 24:  # Updated in last 24 hours
                agents_with_recent_updates.append(memory["agent_type"])

        # Check for unacknowledged handoffs
        unacknowledged_handoffs = [t for t in transitions if not t["acknowledged"]]

        # Check for conflicting decisions
        decision_conflicts = self._detect_decision_conflicts(decisions)

        # Calculate health score
        total_agents = len(set(m["agent_type"] for m in memories))
        recent_update_coverage = len(set(agents_with_recent_updates)) / max(total_agents, 1)
        handoff_health = 1 - (len(unacknowledged_handoffs) / max(len(transitions), 1))
        decision_health = 1 - (len(decision_conflicts) / max(len(decisions), 1))

        health_score = recent_update_coverage * 0.4 + handoff_health * 0.3 + decision_health * 0.3

        return {
            "health_score": health_score,
            "active_agents": len(active_agents),
            "recent_updates": len(agents_with_recent_updates),
            "unacknowledged_handoffs": len(unacknowledged_handoffs),
            "decision_conflicts": len(decision_conflicts),
            "total_memories": len(memories),
            "total_transitions": len(transitions),
            "total_decisions": len(decisions),
        }

    def _generate_handoff_markdown(self, transition: AgentTransition) -> str:
        """Generate markdown for agent transition"""
        md = f"## 🔄 AGENT TRANSITION: {transition.from_agent} → {transition.to_agent}\n\n"
        md += f"**CONTEXT TRANSFER**:\n{transition.context_transfer}\n\n"

        if transition.requirements:
            md += "**REQUIREMENTS FOR NEXT AGENT**:\n"
            for req in transition.requirements:
                md += f"- [ ] {req}\n"
            md += "\n"

        md += f"**HANDOFF STATUS**: {'✅ Acknowledged' if transition.acknowledged else '⏳ Pending acknowledgment'}\n"
        md += "**NEXT CHECKPOINT**: Review handoff completion\n\n"

        return md

    def _generate_decision_markdown(self, decision: CollaborativeDecision) -> str:
        """Generate markdown for collaborative decision"""
        md = f"## 🧠 COLLABORATIVE DECISION: {decision.title}\n\n"
        md += f"**Decision ID**: {decision.decision_id}\n"
        md += f"**Participants**: {', '.join(decision.participants)}\n"
        md += f"**Context**: {decision.context}\n\n"

        md += "**Agent Perspectives**:\n"
        for agent, perspective in decision.agent_perspectives.items():
            md += f"- **{agent}**: {perspective}\n"

        md += f"\n**CONSENSUS**: {decision.consensus}\n"
        md += f"**Implementation Owner**: {decision.implementation_owner}\n"
        md += f"**Review Checkpoint**: {decision.review_checkpoint}\n\n"

        return md

    def _detect_decision_conflicts(self, decisions: List[Dict]) -> List[str]:
        """Detect potentially conflicting decisions"""
        conflicts = []

        # Simple keyword-based conflict detection
        # In practice, this would be more sophisticated
        decision_keywords = {}
        for decision in decisions:
            title_words = set(decision["title"].lower().split())
            for word in title_words:
                if len(word) > 3:  # Ignore short words
                    if word not in decision_keywords:
                        decision_keywords[word] = []
                    decision_keywords[word].append(decision)

        # Look for decisions with overlapping keywords but different consensus
        for word, related_decisions in decision_keywords.items():
            if len(related_decisions) > 1:
                consensus_set = set(d["consensus"] for d in related_decisions)
                if len(consensus_set) > 1:
                    conflicts.append(
                        f"Potential conflict in decisions about '{word}': {len(related_decisions)} decisions with different outcomes"
                    )

        return conflicts

    def _load_agent_memories(self) -> List[Dict]:
        """Load agent memory blocks"""
        try:
            with open(self.agent_memory_file, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def _save_agent_memories(self, memories: List[Dict]):
        """Save agent memory blocks"""
        with open(self.agent_memory_file, "w") as f:
            json.dump(memories, f, indent=2)

    def _load_transitions(self) -> List[Dict]:
        """Load agent transitions"""
        try:
            with open(self.transitions_file, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def _save_transitions(self, transitions: List[Dict]):
        """Save agent transitions"""
        with open(self.transitions_file, "w") as f:
            json.dump(transitions, f, indent=2)

    def _load_decisions(self) -> List[Dict]:
        """Load collaborative decisions"""
        try:
            with open(self.decisions_file, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def _save_decisions(self, decisions: List[Dict]):
        """Save collaborative decisions"""
        with open(self.decisions_file, "w") as f:
            json.dump(decisions, f, indent=2)


def main():
    parser = argparse.ArgumentParser(description="Agent Context Coordinator")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Create memory block
    create_parser = subparsers.add_parser("create_memory", help="Create agent memory block")
    create_parser.add_argument("agent_type", help="Type of agent")
    create_parser.add_argument("session_context", help="Current session context")
    create_parser.add_argument("current_focus", help="Current focus area")

    # Update memory
    update_parser = subparsers.add_parser("update_memory", help="Update agent memory")
    update_parser.add_argument("agent_type", help="Type of agent")
    update_parser.add_argument("--decision", help="Decision in format 'decision:rationale'")
    update_parser.add_argument("--tag", help="Expertise tag")
    update_parser.add_argument("--dependency", help="Cross-agent dependency")
    update_parser.add_argument("--handof", help="Handoff notes")
    update_parser.add_argument("--status", choices=["active", "waiting", "complete", "blocked", "handed_of"])
    update_parser.add_argument("--focus", help="Current focus")

    # Create transition
    transition_parser = subparsers.add_parser("create_transition", help="Create agent transition")
    transition_parser.add_argument("from_agent", help="Source agent")
    transition_parser.add_argument("to_agent", help="Destination agent")
    transition_parser.add_argument("context", help="Context transfer description")
    transition_parser.add_argument("--requirements", nargs="+", default=[], help="Requirements for next agent")

    # Acknowledge handoff
    ack_parser = subparsers.add_parser("acknowledge", help="Acknowledge handof")
    ack_parser.add_argument("from_agent", help="Source agent")
    ack_parser.add_argument("to_agent", help="Destination agent")

    # Create collaborative decision
    decision_parser = subparsers.add_parser("create_decision", help="Create collaborative decision")
    decision_parser.add_argument("title", help="Decision title")
    decision_parser.add_argument("--participants", nargs="+", required=True, help="Participating agents")
    decision_parser.add_argument("--context", required=True, help="Decision context")
    decision_parser.add_argument("--consensus", required=True, help="Agreed consensus")
    decision_parser.add_argument("--owner", required=True, help="Implementation owner")
    decision_parser.add_argument("--review", required=True, help="Review checkpoint")

    # Status board
    subparsers.add_parser("status_board", help="Generate agent status board")

    # Validate
    subparsers.add_parser("validate", help="Validate context integrity")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    coordinator = AgentContextCoordinator()

    if args.command == "create_memory":
        coordinator.create_agent_memory_block(args.agent_type, args.session_context, args.current_focus)

    elif args.command == "update_memory":
        updates = {}
        if args.decision:
            parts = args.decision.split(":", 1)
            if len(parts) == 2:
                updates["decision"] = {"decision": parts[0], "rationale": parts[1]}
        if args.tag:
            updates["expertise_tag"] = args.tag
        if args.dependency:
            updates["dependency"] = args.dependency
        if args.handoff:
            updates["handoff_notes"] = args.handoff
        if args.status:
            updates["status"] = AgentStatus(args.status)
        if args.focus:
            updates["current_focus"] = args.focus

        coordinator.update_agent_memory(args.agent_type, **updates)

    elif args.command == "create_transition":
        coordinator.create_agent_transition(args.from_agent, args.to_agent, args.context, args.requirements)

    elif args.command == "acknowledge":
        coordinator.acknowledge_handoff(args.from_agent, args.to_agent)

    elif args.command == "create_decision":
        # Parse perspectives from stdin or assume empty for now
        perspectives = {}
        for participant in args.participants:
            perspectives[participant] = f"Perspective from {participant}"

        coordinator.create_collaborative_decision(
            args.title,
            args.participants,
            args.context,
            perspectives,
            args.consensus,
            args.owner,
            args.review,
        )

    elif args.command == "status_board":
        print(coordinator.generate_agent_status_board())

    elif args.command == "validate":
        health = coordinator.validate_context_integrity()
        print(f"Context Health Score: {health['health_score']:.2f}")
        print(f"Active Agents: {health['active_agents']}")
        print(f"Recent Updates: {health['recent_updates']}")
        print(f"Unacknowledged Handoffs: {health['unacknowledged_handoffs']}")
        print(f"Decision Conflicts: {health['decision_conflicts']}")


if __name__ == "__main__":
    main()
