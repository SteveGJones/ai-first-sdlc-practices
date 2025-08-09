#!/usr/bin/env python3
"""
Agentic SDLC Coach - The Stan Cullis System for AI Development

This is REAL coaching. Not suggestions. Not advice. ENFORCEMENT.

Like Stan Cullis, we:
- DEMAND standards before allowing work
- BLOCK non-compliant development
- MEASURE everything
- TEACH through enforcement

Like Billy Wright, we:
- LEAD by example with perfect compliance
- COORDINATE teams with discipline
- NEVER compromise on quality
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime


class AgenticSDLCCoach:
    """The Stan Cullis of AI Development - No compromise, total discipline"""

    def __init__(self):
        self.project_root = self._find_project_root()
        self.framework_tools = self._validate_framework_installation()
        self.enforcement_history = []
        self.blocked_attempts = 0
        self.compliance_score = 0

    def _find_project_root(self) -> Path:
        """Find project root with CLAUDE-CORE.md"""
        current = Path.cwd()
        while current != current.parent:
            if (current / "CLAUDE-CORE.md").exists():
                return current
            current = current.parent
        return Path.cwd()

    def _validate_framework_installation(self) -> Dict:
        """Verify ALL framework tools are present"""
        required_tools = {
            "architecture_validator": "tools/validation/validate-architecture.py",
            "debt_checker": "tools/validation/check-technical-debt.py",
            "pipeline_validator": "tools/validation/validate-pipeline.py",
            "progress_tracker": "tools/automation/progress-tracker.py",
            "context_manager": "tools/automation/context-manager.py",
            "proposal_checker": "tools/validation/check-feature-proposal.py",
        }

        available = {}
        for name, path in required_tools.items():
            full_path = self.project_root / path
            available[name] = full_path.exists()

        if not all(available.values()):
            missing = [k for k, v in available.items() if not v]
            raise RuntimeError(
                f"BLOCKED: Missing framework tools: {missing}\n"
                f"Run: python tools/setup.py to install framework"
            )

        return required_tools

    def start_project(self, description: str) -> Dict:
        """
        Start project WITH FULL SDLC ENFORCEMENT
        This is where Stan Cullis discipline begins
        """
        self._print_header()

        # Run all validation steps
        validation_result = self._run_validation_steps(description)

        if validation_result["status"] != "AUTHORIZED":
            return validation_result

        # Development authorized
        self._print_authorization_success()

        return self._build_success_response(
            validation_result["proposal"],
            validation_result["architecture"],
            validation_result["team"],
            validation_result["gates"],
            validation_result["tracking"],
            validation_result["retrospective"],
            description,
        )

    def _print_header(self):
        """Print the enforcement header"""
        print("=" * 80)
        print("AGENTIC SDLC COACH - ZERO TOLERANCE ENFORCEMENT")
        print("=" * 80)
        print()

    def _print_authorization_success(self):
        """Print authorization success message"""
        print("\n" + "=" * 80)
        print("✅ SDLC COMPLIANCE VERIFIED - DEVELOPMENT AUTHORIZED")
        print("=" * 80)

    def _run_validation_steps(self, description: str) -> Dict:
        """Run all validation steps"""
        # Step 1: Feature Proposal
        print("📋 STEP 1: Feature Proposal (MANDATORY)")
        print("-" * 40)
        proposal_path = self._enforce_feature_proposal(description)
        if not proposal_path:
            return self._block_development(
                "No feature proposal = NO DEVELOPMENT")

        # Step 2: Architecture
        print("\n📐 STEP 2: Architecture Documents (ALL 6 REQUIRED)")
        print("-" * 40)
        arch_status = self._enforce_architecture_documents()
        if not arch_status["complete"]:
            return self._block_development(
                f"Missing architecture docs: {arch_status['missing']}"
            )

        # Step 3: Technical Debt
        print("\n🚫 STEP 3: Zero Technical Debt Check")
        print("-" * 40)
        debt_status = self._check_technical_debt()
        if debt_status["violations"] > 0:
            return self._block_development(
                f"Technical debt found: {debt_status['details']}"
            )

        # Step 4: Agents
        print("\n🤖 STEP 4: Agent Discovery and Validation")
        print("-" * 40)
        team = self._discover_and_validate_agents(description)
        if not team["valid"]:
            return self._block_development(
                f"Invalid team composition: {team['issues']}"
            )

        # Step 5-7: Setup steps
        gates = self._run_setup_steps(description)

        return {
            "status": "AUTHORIZED",
            "proposal": proposal_path,
            "architecture": arch_status,
            "team": team,
            "gates": gates["gates"],
            "tracking": gates["tracking"],
            "retrospective": gates["retrospective"],
        }

    def _run_setup_steps(self, description: str) -> Dict:
        """Run setup steps (gates, tracking, retrospective)"""
        print("\n🚧 STEP 5: Quality Gates Setup")
        print("-" * 40)
        gates = self._setup_quality_gates()

        print("\n📊 STEP 6: Progress Tracking Initialization")
        print("-" * 40)
        tracking = self._initialize_progress_tracking(description)

        print("\n📝 STEP 7: Retrospective Template")
        print("-" * 40)
        retro_path = self._create_retrospective_template()

        return {
            "gates": gates,
            "tracking": tracking,
            "retrospective": retro_path}

    def _build_success_response(
        self, proposal, arch, team, gates, tracking, retro, desc
    ) -> Dict:
        """Build the success response"""
        return {
            "status": "AUTHORIZED",
            "proposal": proposal,
            "architecture": arch,
            "team": team,
            "gates": gates,
            "tracking": tracking,
            "retrospective": retro,
            "next_steps": self._generate_coaching_plan(team, desc),
        }

    def _enforce_feature_proposal(self, description: str) -> Optional[Path]:
        """Create and validate feature proposal"""
        proposal_dir = self.project_root / "docs" / "feature-proposals"
        proposal_dir.mkdir(parents=True, exist_ok=True)

        # Generate proposal filename
        timestamp = datetime.now().strftime("%Y%m%d")
        proposal_file = proposal_dir / f"{timestamp}-project-kickoff.md"

        if not proposal_file.exists():
            print(f"⚠️  No feature proposal found!")
            print(f"Creating template at: {proposal_file}")

            template = f"""# Feature Proposal: Project Kickoff

## Motivation
{description}

## Proposed Solution
[AI MUST COMPLETE]

## Detailed Design
[AI MUST COMPLETE]

## Test Plan
[AI MUST COMPLETE]

## Rollout Plan
[AI MUST COMPLETE]
"""
            proposal_file.write_text(template)

            print(f"❌ BLOCKED: Complete the feature proposal first")
            print(f"   Edit: {proposal_file}")
            return None

        # Validate proposal (check-feature-proposal.py uses branch, not file
        # path)
        result = self._run_validation_tool(
            self.framework_tools["proposal_checker"])

        if not result["success"]:
            print(f"❌ BLOCKED: Invalid feature proposal")
            print(f"   Issues: {result['output']}")
            return None

        print(f"✅ Feature proposal validated: {proposal_file.name}")
        return proposal_file

    def _enforce_architecture_documents(self) -> Dict:
        """Ensure ALL 6 architecture documents exist"""
        required_docs = [
            "requirements-traceability-matrix.md",
            "what-if-analysis.md",
            "architecture-decision-record.md",
            "system-invariants.md",
            "integration-design.md",
            "failure-mode-analysis.md",
        ]

        arch_dir = self.project_root / "templates" / "architecture"
        arch_dir.mkdir(parents=True, exist_ok=True)

        missing = []
        for doc in required_docs:
            if not (arch_dir / doc).exists():
                missing.append(doc)

        if missing:
            print(f"❌ Missing architecture documents: {missing}")
            print(
                f"   Run: python {self.framework_tools['architecture_validator']} --strict"
            )
            return {"complete": False, "missing": missing}

        # Validate architecture
        result = self._run_validation_tool(
            self.framework_tools["architecture_validator"], "--strict"
        )

        if not result["success"]:
            print(f"❌ Architecture validation failed")
            print(f"   {result['output']}")
            return {"complete": False, "issues": result["output"]}

        print(f"✅ All 6 architecture documents validated")
        return {"complete": True, "documents": required_docs}

    def _check_technical_debt(self) -> Dict:
        """Zero tolerance for technical debt"""
        result = self._run_validation_tool(
            self.framework_tools["debt_checker"], "--threshold", "0"
        )

        if not result["success"]:
            violations = self._parse_debt_violations(result["output"])
            print(f"❌ Technical debt detected: {len(violations)} violations")
            for v in violations[:3]:  # Show first 3
                print(f"   - {v}")
            return {"violations": len(violations), "details": violations}

        print(f"✅ Zero technical debt verified")
        return {"violations": 0}

    def _discover_and_validate_agents(self, description: str) -> Dict:
        """Discover available agents and validate team composition"""
        agents_dir = self.project_root / "agents"

        if not agents_dir.exists():
            return {"valid": False, "issues": "No agents directory found"}

        # Scan for available agents
        available_agents = self._scan_available_agents(agents_dir)

        print(f"📊 Found {len(available_agents)} agents across categories")

        # Select team based on project type
        team = self._select_optimal_team(description, available_agents)

        # Validate each agent exists
        invalid = []
        for role, agent_name in team.items():
            if not any(a["name"] == agent_name for a in available_agents):
                invalid.append(f"{role}: {agent_name} NOT FOUND")

        if invalid:
            return {
                "valid": False,
                "issues": invalid,
                "available": available_agents}

        print(f"✅ Team validated with {len(team)} specialists")
        return {
            "valid": True,
            "team": team,
            "available": len(available_agents)}

    def _scan_available_agents(self, agents_dir: Path) -> List[Dict]:
        """Scan for all available agents in the repository"""
        available_agents = []
        
        # Scan ALL directories that contain agents
        for category_dir in agents_dir.iterdir():
            if category_dir.is_dir() and not category_dir.name.startswith('.'):
                category = category_dir.name
                agents = self._scan_category_agents(category_dir, category)
                available_agents.extend(agents)

        return available_agents

    def _scan_category_agents(
            self,
            cat_dir: Path,
            category: str) -> List[Dict]:
        """Scan agents in a specific category"""
        if not cat_dir.exists():
            return []

        agents = []
        for agent_file in cat_dir.glob("*.md"):
            agents.append({"name": agent_file.stem,
                           "category": category, "path": agent_file})
        return agents

    def _select_optimal_team(
            self,
            description: str,
            available_agents: List) -> Dict:
        """Select team WITH SDLC ENFORCEMENT ROLES"""
        desc_lower = description.lower()

        # ALWAYS include enforcement agents
        team = {
            "enforcer": "ai-first-kick-starter",  # Or sdlc-enforcer when available
            "reviewer": "critical-goal-reviewer",
            "tracker": "project-plan-tracker",
        }

        # Add domain specialists
        if "web" in desc_lower or "app" in desc_lower:
            team.update(
                {
                    "architect": "solution-architect",
                    "database": "database-architect",
                    "api": "api-architect",
                    "frontend": "frontend-engineer",
                }
            )
        elif "ai" in desc_lower or "ml" in desc_lower:
            team.update(
                {
                    "architect": "ai-solution-architect",
                    "prompt": "prompt-engineer",
                    "context": "context-engineer",
                }
            )

        return team

    def _setup_quality_gates(self) -> Dict:
        """Configure automatic validation gates"""
        gates = {
            "pre_commit": [
                "python tools/validation/local-validation.py --syntax",
                "python tools/validation/check-technical-debt.py --threshold 0",
            ],
            "pre_push": [
                "python tools/validation/validate-pipeline.py --ci",
                "python tools/validation/validate-architecture.py --strict",
            ],
            "continuous": [
                "python tools/automation/progress-tracker.py list",
                "python tools/validation/check-feature-proposal.py",
            ],
        }

        print("🚧 Quality gates configured:")
        for gate, checks in gates.items():
            print(f"   {gate}: {len(checks)} checks")

        return gates

    def _initialize_progress_tracking(self, description: str) -> Dict:
        """Start progress tracking"""
        result = self._run_validation_tool(
            self.framework_tools["progress_tracker"],
            "add",
            f"Project kickoff: {description}",
        )

        tracking = {
            "initialized": result["success"],
            "first_task": f"Project kickoff: {description}",
        }

        if result["success"]:
            print(f"✅ Progress tracking initialized")
        else:
            print(f"⚠️  Progress tracking setup failed (non-blocking)")

        return tracking

    def _create_retrospective_template(self) -> Path:
        """Create retrospective that MUST be completed"""
        retro_dir = self.project_root / "retrospectives"
        retro_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d")
        retro_file = retro_dir / f"{timestamp}-project-retrospective.md"

        if not retro_file.exists():
            template = """# Project Retrospective

## What Went Well
- [MUST COMPLETE BEFORE PR]

## What Could Be Improved
- [MUST COMPLETE BEFORE PR]

## Lessons Learned
- [MUST COMPLETE BEFORE PR]

## SDLC Compliance Score
- Feature Proposal: [YES/NO]
- Architecture Docs: [YES/NO]
- Zero Technical Debt: [YES/NO]
- Progress Tracked: [YES/NO]
- Tests Written: [YES/NO]
"""
            retro_file.write_text(template)

        print(f"📝 Retrospective template: {retro_file.name}")
        return retro_file

    def _generate_coaching_plan(
            self,
            team: Dict,
            description: str) -> List[str]:
        """Generate ENFORCED coaching plan"""
        plan = [
            "1. Complete feature proposal (if not done)",
            "2. Fill ALL architecture documents",
            "3. Run validation suite after EVERY change:",
            "   - python tools/validation/local-validation.py --syntax",
            "   - python tools/validation/check-technical-debt.py --threshold 0",
            "4. Use your team:",
        ]

        for role, agent in team["team"].items():
            plan.append(
                f"   - {role}: Engage {agent} for {role} responsibilities")

        plan.extend(
            [
                "5. Track progress continuously:",
                "   - python tools/automation/progress-tracker.py add 'task'",
                "6. Update retrospective incrementally",
                "7. Run full validation before PR:",
                "   - python tools/validation/validate-pipeline.py --ci",
            ]
        )

        return plan

    def _block_development(self, reason: str) -> Dict:
        """BLOCK non-compliant work - The Stan Cullis way"""
        self.blocked_attempts += 1

        print("\n" + "🚫" * 40)
        print("DEVELOPMENT BLOCKED - NON-COMPLIANT")
        print("🚫" * 40)
        print(f"\nReason: {reason}")
        print(f"\nThis is block #{self.blocked_attempts}")
        print("\nNO SHORTCUTS. NO EXCEPTIONS. FIX IT OR DON'T DEVELOP.")
        print("\nStan Cullis says: 'Standards aren't optional. Meet them or sit out.'")

        return {
            "status": "BLOCKED",
            "reason": reason,
            "attempts_blocked": self.blocked_attempts,
            "message": "Fix compliance issues and try again",
        }

    def _run_validation_tool(self, tool_path: str, *args) -> Dict:
        """Run framework validation tool"""
        full_path = self.project_root / tool_path

        if not full_path.exists():
            return {"success": False, "output": f"Tool not found: {tool_path}"}

        try:
            result = subprocess.run(
                ["python", str(full_path)] + list(args),
                capture_output=True,
                text=True,
                timeout=30,
            )
            return {
                "success": result.returncode == 0,
                "output": result.stdout or result.stderr,
            }
        except Exception as e:
            return {"success": False, "output": str(e)}

    def _parse_debt_violations(self, output: str) -> List[str]:
        """Parse technical debt violations from output"""
        violations = []
        for line in output.split("\n"):
            if any(
                marker in line for marker in [
                    "TODO",
                    "FIXME",
                    "HACK",
                    "any type"]):
                violations.append(line.strip())
        return violations


def main():
    """Stan Cullis coaching system - No compromise"""
    if len(sys.argv) < 2:
        print("Agentic SDLC Coach - Professional Standards Enforcement")
        print()
        print("Usage:")
        print("  python agentic_sdlc_coach.py 'project description'")
        print()
        print("This coach ENFORCES:")
        print("  - Feature proposals (mandatory)")
        print("  - Architecture documents (all 6)")
        print("  - Zero technical debt")
        print("  - Progress tracking")
        print("  - Quality gates")
        print("  - Team validation")
        print()
        print("NO SHORTCUTS. PROFESSIONAL STANDARDS ONLY.")
        return

    project = " ".join(sys.argv[1:])
    coach = AgenticSDLCCoach()
    result = coach.start_project(project)

    if result["status"] == "AUTHORIZED":
        print("\n📋 YOUR COACHING PLAN:")
        print("-" * 40)
        for step in result["next_steps"]:
            print(step)
        print()
        print("Follow this plan. No deviations. No shortcuts.")
        print("Billy Wright says: 'Excellence is habit, not accident.'")
    else:
        print("\nFix the issues above and try again.")
        print("No development until compliance is achieved.")


if __name__ == "__main__":
    main()
