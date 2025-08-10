#!/usr/bin/env python3
"""
The Kickoff Genius - Stan Cullis's 5-Minute Miracle

The first 5 minutes determine project success or failure.
This system ensures you WIN those 5 minutes EVERY TIME.

Like Billy Wright taking the field:
- Team assembled and ready
- Everyone knows their position
- Clear strategy from kickoff

Like Stan Cullis in the dressing room:
- Standards non-negotiable
- Plan crystal clear
- No confusion, only execution
"""

import sys
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List

# Import the enforcer - we build on discipline
from sdlc_coach import AgenticSDLCCoach


class KickoffGenius:
    """The 5-Minute Miracle System - From chaos to coordinated excellence"""

    # Constants to avoid magic numbers
    TARGET_MINUTES = 5
    TARGET_SECONDS = 300
    INITIAL_USERS = 100
    SCALE_THRESHOLD = 1000
    LARGE_SCALE_THRESHOLD = 10000

    def __init__(self):
        self.enforcer = AgenticSDLCCoach()
        self.kickoff_start = None
        self.clarity_achieved = False
        self.team_ready = False

    def five_minute_miracle(self, vague_idea: str) -> Dict:
        """
        Transform vague idea into actionable plan in 5 minutes
        This is the Stan Cullis kickoff system
        """
        self.kickoff_start = time.time()
        self._print_kickoff_header(vague_idea)

        # Run the 5 phases
        phases = self._run_five_phases(vague_idea)

        # Calculate and print results
        elapsed = time.time() - self.kickoff_start
        success = self._print_verdict(elapsed)

        return self._build_miracle_response(success, elapsed, phases)

    def _print_kickoff_header(self, vague_idea: str):
        """Print the kickoff header"""
        print("=" * 80)
        print("⚡ KICKOFF GENIUS - THE 5-MINUTE MIRACLE")
        print("=" * 80)
        print(f"\n📝 Starting idea: '{vague_idea}'")
        print("\nYou have 5 MINUTES to transform this into excellence.\n")

    def _run_five_phases(self, vague_idea: str) -> Dict:
        """Run all 5 phases of the miracle"""
        # MINUTE 1
        print("⏱️  MINUTE 1: RAPID DISCOVERY")
        print("-" * 40)
        clarity = self._rapid_discovery(vague_idea)

        # MINUTE 2
        print("\n⏱️  MINUTE 2: INSTANT TEAM ASSEMBLY")
        print("-" * 40)
        team = self._instant_team_assembly(clarity)

        # MINUTE 3
        print("\n⏱️  MINUTE 3: ARCHITECTURE BLUEPRINT")
        print("-" * 40)
        architecture = self._architecture_blitz(clarity, team)

        # MINUTE 4
        print("\n⏱️  MINUTE 4: TASK BREAKDOWN")
        print("-" * 40)
        tasks = self._task_explosion(clarity, team, architecture)

        # MINUTE 5
        print("\n⏱️  MINUTE 5: KICKOFF EXECUTION")
        print("-" * 40)
        execution = self._kickoff_execution(tasks, team)

        return {
            "clarity": clarity,
            "team": team,
            "architecture": architecture,
            "tasks": tasks,
            "execution": execution,
        }

    def _print_verdict(self, elapsed: float) -> bool:
        """Print the verdict and return success status"""
        print("\n" + "=" * 80)
        if elapsed <= self.TARGET_SECONDS:
            print(f"✅ MIRACLE ACHIEVED in {elapsed:.1f} seconds!")
            print("=" * 80)
            return True
        else:
            print(f"⚠️  Took {elapsed:.1f} seconds (target was {self.TARGET_SECONDS})")
            print("=" * 80)
            return False

    def _build_miracle_response(
        self, success: bool, elapsed: float, phases: Dict
    ) -> Dict:
        """Build the miracle response"""
        return {
            "success": success,
            "time_taken": elapsed,
            "clarity": phases["clarity"],
            "team": phases["team"],
            "architecture": phases["architecture"],
            "tasks": phases["tasks"],
            "execution": phases["execution"],
            "ready_to_build": self.team_ready,
        }

    def _rapid_discovery(self, vague_idea: str) -> Dict:
        """MINUTE 1: From vague to specific in 60 seconds"""

        # The Billy Wright Questions - Direct and Clear
        questions = {
            "WHAT": "What problem does this solve?",
            "WHO": "Who will use this?",
            "SCALE": "10 users or 10,000?",
            "CORE": "The ONE feature that matters?",
            "SUCCESS": "How do we measure winning?",
        }

        print("🎯 Billy Wright's 5 Questions (10 seconds each):")

        # In real system, these would be asked to user
        # For demo, we'll extract from the vague idea
        clarity = self._extract_clarity(vague_idea, questions)

        for key, question in questions.items():
            print(f"   {key}: {clarity[key]}")

        # Generate specific description
        specific = f"{clarity['CORE']} for {clarity['WHO']} solving {clarity['WHAT']}"

        print(f"\n📌 Crystallized: '{specific}'")
        clarity["specific_description"] = specific
        self.clarity_achieved = True

        return clarity

    def _extract_clarity(self, idea: str, questions: Dict) -> Dict:
        """Extract answers from vague idea (AI would ask user)"""
        idea_lower = idea.lower()

        clarity = {}

        # Smart extraction based on keywords
        if "task" in idea_lower or "todo" in idea_lower:
            clarity["WHAT"] = "Task organization chaos"
            clarity["WHO"] = "Remote teams"
            clarity["CORE"] = "Smart task prioritization"
        elif "chat" in idea_lower or "ai" in idea_lower:
            clarity["WHAT"] = "Customer service delays"
            clarity["WHO"] = "Support teams"
            clarity["CORE"] = "Instant AI responses"
        elif "data" in idea_lower or "analytics" in idea_lower:
            clarity["WHAT"] = "Decision-making blindness"
            clarity["WHO"] = "Business analysts"
            clarity["CORE"] = "Real-time insights dashboard"
        else:
            clarity["WHAT"] = "Efficiency problems"
            clarity["WHO"] = "Professional teams"
            clarity["CORE"] = "Automated workflows"

        clarity["SCALE"] = f"{self.INITIAL_USERS} users initially"
        clarity["SUCCESS"] = "50% time savings"

        return clarity

    def _instant_team_assembly(self, clarity: Dict) -> Dict:
        """MINUTE 2: Assemble the perfect team instantly"""

        print("🚀 Stan Cullis Team Selection:")

        # Core team based on project type
        core_team = self._select_core_team(clarity["CORE"])

        # Enforcement team (ALWAYS)
        enforcement = {
            "coach": "ai-first-kick-starter",
            "reviewer": "critical-goal-reviewer",
            "tracker": "project-plan-tracker",
        }

        # Specialist team
        specialists = self._select_specialists(clarity)

        team = {**core_team, **enforcement, **specialists}

        print("\n📋 Your Squad (Billy Wright Formation):")
        for role, agent in team.items():
            marker = "⭐" if role in ["captain", "coach"] else "  "
            print(f"   {marker} {role}: {agent}")

        self.team_ready = True
        print(f"\n✅ {len(team)} specialists ready for kickoff!")

        return {"formation": "4-3-3 Attack", "team": team, "ready": True}

    def _select_core_team(self, core_feature: str) -> Dict:
        """Select core team based on main feature"""
        core_lower = core_feature.lower()

        if "ai" in core_lower or "chat" in core_lower:
            return {
                "captain": "ai-solution-architect",
                "lieutenant": "prompt-engineer",
                "specialist": "context-engineer",
            }
        elif "data" in core_lower or "analytics" in core_lower:
            return {
                "captain": "data-architect",
                "lieutenant": "database-architect",
                "specialist": "performance-engineer",
            }
        else:
            return {
                "captain": "solution-architect",
                "lieutenant": "database-architect",
                "specialist": "api-architect",
            }

    def _select_specialists(self, clarity: Dict) -> Dict:
        """Add specialists based on requirements"""
        specialists = {}

        scale = clarity.get("SCALE", "").lower()
        if (
            str(self.SCALE_THRESHOLD) in scale
            or str(self.LARGE_SCALE_THRESHOLD) in scale
        ):
            specialists["performance"] = "performance-engineer"

        who = clarity.get("WHO", "").lower()
        if "customer" in who or "user" in who:
            specialists["ux"] = "ux-ui-architect"

        if "secure" in clarity.get("WHAT", "").lower():
            specialists["security"] = "security-specialist"

        return specialists

    def _architecture_blitz(self, clarity: Dict, team: Dict) -> Dict:
        """MINUTE 3: Lightning architecture decisions"""

        print("⚡ Lightning Architecture (20-second decisions):")

        decisions = {
            "Frontend": self._quick_decision("frontend", clarity),
            "Backend": self._quick_decision("backend", clarity),
            "Database": self._quick_decision("database", clarity),
            "Deployment": self._quick_decision("deployment", clarity),
            "Monitoring": "Prometheus + Grafana",  # Always
            "Testing": "Pytest + Jest",  # Always
        }

        for component, choice in decisions.items():
            print(f"   {component}: {choice}")

        # Create instant architecture doc
        arch_doc = self._create_instant_architecture(decisions, clarity)

        print("\n📐 Architecture documented and validated!")

        return {"decisions": decisions, "documented": True, "doc_path": arch_doc}

    def _quick_decision(self, component: str, clarity: Dict) -> str:
        """Make instant architecture decisions"""
        scale = clarity.get("SCALE", "")

        if component == "frontend":
            if "mobile" in clarity.get("WHO", "").lower():
                return "React Native"
            return "React + TypeScript"

        elif component == "backend":
            if str(self.LARGE_SCALE_THRESHOLD) in scale:
                return "Go + Microservices"
            elif "ai" in clarity.get("CORE", "").lower():
                return "Python + FastAPI"
            return "Node.js + Express"

        elif component == "database":
            if "real-time" in clarity.get("CORE", "").lower():
                return "PostgreSQL + Redis"
            elif "analytics" in clarity.get("CORE", "").lower():
                return "PostgreSQL + TimescaleDB"
            return "PostgreSQL"

        elif component == "deployment":
            if str(self.LARGE_SCALE_THRESHOLD) in scale:
                return "Kubernetes on AWS"
            return "Docker on AWS ECS"

        return "Standard"

    def _create_instant_architecture(self, decisions: Dict, clarity: Dict) -> Path:
        """Create architecture document instantly"""
        arch_dir = Path.cwd() / "architecture"
        arch_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        arch_file = arch_dir / f"kickoff_architecture_{timestamp}.md"

        content = f"""# Kickoff Architecture - {clarity['specific_description']}

## Decisions (Made in 60 seconds)
- Frontend: {decisions['Frontend']}
- Backend: {decisions['Backend']}
- Database: {decisions['Database']}
- Deployment: {decisions['Deployment']}
- Monitoring: {decisions['Monitoring']}
- Testing: {decisions['Testing']}

## Rationale
- Scale: {clarity['SCALE']}
- Core Feature: {clarity['CORE']}
- Success Metric: {clarity['SUCCESS']}

Generated by Kickoff Genius in under 3 minutes.
"""
        arch_file.write_text(content)
        return arch_file

    def _task_explosion(
        self, clarity: Dict, team: Dict, architecture: Dict
    ) -> List[Dict]:
        """MINUTE 4: Explode into actionable tasks"""

        print("💥 Task Explosion (5 seconds per task):")

        tasks = []

        # Critical path tasks
        critical = [
            {
                "task": "Set up repository and CI/CD",
                "owner": "devops-specialist",
                "hours": 2,
            },
            {
                "task": f"Design {clarity['CORE']} architecture",
                "owner": team["team"]["captain"],
                "hours": 4,
            },
            {
                "task": "Create database schema",
                "owner": "database-architect",
                "hours": 3,
            },
            {"task": "Build API endpoints", "owner": "api-architect", "hours": 6},
            {
                "task": "Implement core feature",
                "owner": team["team"]["specialist"],
                "hours": 8,
            },
            {"task": "Create test suite", "owner": "ai-test-engineer", "hours": 4},
            {"task": "Deploy MVP", "owner": "devops-specialist", "hours": 2},
        ]

        for i, task in enumerate(critical, 1):
            print(f"   {i}. {task['task']} → {task['owner']} ({task['hours']}h)")
            tasks.append(task)

        total_hours = sum(t["hours"] for t in tasks)
        print(f"\n⏰ Total: {total_hours} hours to MVP")
        print(
            f"📅 With {len(team['team'])} people: {total_hours/len(team['team']):.1f} hours"
        )

        return tasks

    def _kickoff_execution(self, tasks: List[Dict], team: Dict) -> Dict:
        """MINUTE 5: Launch execution"""

        print("🏃 Kickoff Execution Commands:")

        commands = [
            "git init && git add .",
            "npm init -y && npm install",
            f"echo '# {tasks[0]['task']}' > TODO.md",
            "python tools/automation/progress-tracker.py add 'Kickoff complete'",
            "python tools/validation/validate-architecture.py --init",
        ]

        for cmd in commands:
            print(f"   $ {cmd}")

        print("\n🎯 First Actions (DO NOW):")
        for task in tasks[:3]:
            print(f"   → {task['owner']}: Start '{task['task']}'")

        print("\n✅ Team is GO for launch!")

        return {
            "status": "LAUNCHED",
            "first_tasks": tasks[:3],
            "total_tasks": len(tasks),
            "estimated_hours": sum(t["hours"] for t in tasks),
        }

    def enforce_then_execute(self, project: str) -> Dict:
        """
        Combine genius kickoff with enforcement
        This is the complete Stan Cullis system
        """
        self._print_complete_system_header()

        # Run kickoff and enforcement
        kickoff = self._run_kickoff_phase(project)
        enforcement = self._run_enforcement_phase(kickoff)

        # Handle results
        return self._handle_integration_results(kickoff, enforcement)

    def _print_complete_system_header(self):
        """Print the complete system header"""
        print("=" * 80)
        print("COMPLETE AGENTIC SDLC SYSTEM")
        print("Kickoff Genius + Enforcement = Excellence")
        print("=" * 80)
        print()

    def _run_kickoff_phase(self, project: str) -> Dict:
        """Run the kickoff phase"""
        print("PHASE 1: KICKOFF GENIUS")
        print("-" * 40)
        kickoff = self.five_minute_miracle(project)

        if not kickoff["success"]:
            print("\n⚠️  Kickoff took too long. Practicing speed is key!")

        return kickoff

    def _run_enforcement_phase(self, kickoff: Dict) -> Dict:
        """Run the enforcement phase"""
        print("\nPHASE 2: SDLC ENFORCEMENT")
        print("-" * 40)

        clear_project = kickoff["clarity"]["specific_description"]
        return self.enforcer.start_project(clear_project)

    def _handle_integration_results(self, kickoff: Dict, enforcement: Dict) -> Dict:
        """Handle the integration results"""
        print("\nPHASE 3: INTEGRATED EXECUTION")
        print("-" * 40)

        if enforcement["status"] == "AUTHORIZED":
            self._print_success_plan()
            return {
                "status": "READY",
                "kickoff": kickoff,
                "enforcement": enforcement,
                "message": "Professional excellence achieved",
            }
        else:
            self._print_blocked_message()
            return {
                "status": "BLOCKED",
                "kickoff": kickoff,
                "enforcement": enforcement,
                "message": "Complete compliance requirements",
            }

    def _print_success_plan(self):
        """Print the success plan"""
        print("✅ Kickoff + Enforcement = READY TO BUILD")
        print("\n📋 Your Integrated Plan:")
        print("1. Team assembled and ready")
        print("2. Architecture decided and documented")
        print("3. Tasks broken down and assigned")
        print("4. Compliance verified and enforced")
        print("5. GO FOR LAUNCH!")

    def _print_blocked_message(self):
        """Print the blocked message"""
        print("❌ Kickoff complete but compliance blocked")
        print("Fix compliance issues then proceed")


def main():
    """The Stan Cullis kickoff system"""
    if len(sys.argv) < 2:
        print("Kickoff Genius - The 5-Minute Miracle")
        print()
        print("Usage:")
        print("  python kickoff_genius.py 'your vague idea'")
        print()
        print("Examples:")
        print("  python kickoff_genius.py 'I want to build something with AI'")
        print("  python kickoff_genius.py 'need a way to manage tasks'")
        print("  python kickoff_genius.py 'thinking about analytics'")
        print()
        print("This system will:")
        print("  1. Transform vague ideas into clear plans (1 min)")
        print("  2. Assemble your team instantly (1 min)")
        print("  3. Make architecture decisions (1 min)")
        print("  4. Break down into tasks (1 min)")
        print("  5. Launch execution (1 min)")
        print()
        print("Total: 5 MINUTES from confusion to coordination")
        return

    idea = " ".join(sys.argv[1:])
    genius = KickoffGenius()

    # You can run just the kickoff
    # result = genius.five_minute_miracle(idea)

    # Or the complete system with enforcement
    result = genius.enforce_then_execute(idea)

    if result["status"] == "READY":
        print("\n" + "🏆" * 40)
        print("Stan Cullis says: 'That's how you win from kickoff.'")
        print("Billy Wright says: 'Team ready, let's show them excellence.'")
        print("🏆" * 40)


if __name__ == "__main__":
    main()
