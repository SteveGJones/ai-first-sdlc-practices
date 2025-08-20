#!/usr/bin/env python3
"""
Team Engagement Validation - AUTOMATIC TEAM-FIRST ENFORCEMENT

This validator ensures that NO solo work is possible by checking for mandatory
team engagement patterns and blocking any work that doesn't involve specialists.

ZERO TOLERANCE: If team engagement is not detected, ALL work is BLOCKED.
"""

import argparse
import sys
import re
import os
from pathlib import Path

# from typing import List  # Not used


class TeamEngagementValidator:
    """Validates that team-first behavior is being followed"""

    def __init__(self, strict_mode: bool = True):
        self.strict_mode = strict_mode
        self.violations = []
        self.team_engagement_score = 0
        self.required_agents = {
            "code_writing": [
                "solution-architect",
                "test-engineer",
                "critical-goal-reviewer",
            ],
            "bug_fixing": [
                "debugging-specialist",
                "test-engineer",
                "regression-analyst",
            ],
            "performance": [
                "performance-engineer",
                "profiling-specialist",
                "monitoring-specialist",
            ],
            "api_design": [
                "api-designer",
                "integration-orchestrator",
                "documentation-architect",
            ],
            "documentation": [
                "documentation-architect",
                "technical-writer",
                "information-architect",
            ],
            "deployment": [
                "devops-specialist",
                "sre-specialist",
                "monitoring-specialist",
            ],
            "security": ["security-specialist", "compliance-auditor", "threat-modeler"],
            "refactoring": [
                "solution-architect",
                "test-engineer",
                "code-quality-analyst",
            ],
            "architecture": [
                "solution-architect",
                "database-architect",
                "integration-orchestrator",
            ],
            "compliance": [
                "sdlc-enforcer",
                "compliance-auditor",
                "critical-goal-reviewer",
            ],
        }

    def validate_all(self) -> bool:
        """Run all team engagement validations"""
        print("🤝 TEAM ENGAGEMENT VALIDATION - ENFORCING TEAM-FIRST BEHAVIOR")
        print("=" * 70)

        success = True

        # Check for solo work patterns
        if not self._check_no_solo_patterns():
            success = False

        # Validate team consultation requirements
        if not self._validate_team_consultations():
            success = False

        # Check for mandatory agent engagement in commits
        if not self._check_commit_team_engagement():
            success = False

        # Validate project has team structure
        if not self._validate_team_structure():
            success = False

        # Check for team handoff protocols
        if not self._check_handoff_protocols():
            success = False

        self._print_final_report(success)
        return success

    def _check_no_solo_patterns(self) -> bool:
        """Check for forbidden solo work patterns"""
        print("\n🚫 CHECKING FOR FORBIDDEN SOLO WORK PATTERNS...")

        solo_patterns = [
            r"(I will|I'll)\s+(implement|create|fix|write|deploy)",
            r"Let me\s+(implement|create|fix|write|deploy)\s+(?!.*team|.*specialist|.*agent)",
            r"(Working on|Implementing|Creating|Fixing)\s+(?!.*with team|.*specialist input)",
            r"Solo\s+(development|work|implementation)",
            r"Working\s+alone\s+on",
            r"Without\s+(team|specialist|agent)\s+(input|consultation|review)",
        ]

        violations_found = []

        # Check commit messages for solo patterns
        try:
            import subprocess

            result = subprocess.run(
                ["git", "log", "--oneline", "-10"], capture_output=True, text=True
            )
            if result.returncode == 0:
                commits = result.stdout
                for pattern in solo_patterns:
                    matches = re.findall(pattern, commits, re.IGNORECASE)
                    if matches:
                        violations_found.extend(matches)
        except (OSError, PermissionError):
            pass

        # Check recent files for solo patterns
        for file_path in Path(".").rglob("*.py"):
            if (
                file_path.is_file() and file_path.stat().st_size < 1000000
            ):  # Skip large files
                try:
                    content = file_path.read_text()
                    for pattern in solo_patterns:
                        matches = re.findall(pattern, content, re.IGNORECASE)
                        if matches:
                            violations_found.extend(
                                [(str(file_path), match) for match in matches]
                            )
                except (OSError, PermissionError):
                    continue

        if violations_found:
            print("❌ SOLO WORK PATTERNS DETECTED:")
            for violation in violations_found[:5]:  # Show first 5
                print(f"   • {violation}")
            print(f"   Total violations: {len(violations_found)}")
            self.violations.append("Solo work patterns detected")
            return False

        print("✅ No solo work patterns found")
        return True

    def _validate_team_consultations(self) -> bool:
        """Validate that team consultations are happening"""
        print("\n🤝 VALIDATING TEAM CONSULTATIONS...")

        required_consultations = [
            "solution-architect consultation",
            "sdlc-enforcer compliance check",
            "critical-goal-reviewer validation",
            "test-engineer input",
            "specialist engagement",
        ]

        found_consultations = []

        # Check documentation for team consultations
        docs_paths = ["docs/feature-proposals", "retrospectives", "plan", "docs"]

        for docs_path in docs_paths:
            if os.path.exists(docs_path):
                for file_path in Path(docs_path).rglob("*.md"):
                    try:
                        content = file_path.read_text().lower()
                        for consultation in required_consultations:
                            if consultation.lower() in content:
                                found_consultations.append(consultation)
                    except (OSError, PermissionError):
                        continue

        consultation_score = len(set(found_consultations)) / len(required_consultations)

        if consultation_score < 0.6:  # Require 60% consultation coverage
            print(f"❌ INSUFFICIENT TEAM CONSULTATIONS: {consultation_score:.1%}")
            print("   Missing consultations:")
            for consultation in required_consultations:
                if consultation not in found_consultations:
                    print(f"   • {consultation}")
            self.violations.append("Insufficient team consultations")
            return False

        print(f"✅ Team consultations: {consultation_score:.1%} coverage")
        return True

    def _check_commit_team_engagement(self) -> bool:
        """Check if commits show team engagement"""
        print("\n📝 CHECKING COMMIT TEAM ENGAGEMENT...")

        team_indicators = [
            "with team",
            "specialist input",
            "agent consultation",
            "solution-architect",
            "test-engineer",
            "sdlc-enforcer",
            "team review",
            "collaborative",
            "peer review",
        ]

        try:
            import subprocess

            result = subprocess.run(
                ["git", "log", "--oneline", "-5"], capture_output=True, text=True
            )
            if result.returncode == 0:
                commits = result.stdout.lower()
                team_mentions = sum(
                    1 for indicator in team_indicators if indicator in commits
                )

                if team_mentions == 0:
                    print("❌ NO TEAM ENGAGEMENT IN RECENT COMMITS")
                    print("   Recent commits show no team collaboration indicators")
                    self.violations.append("No team engagement in commits")
                    return False

                print(f"✅ Team engagement indicators found: {team_mentions}")
                return True
        except (OSError, PermissionError):
            print("⚠️  Could not check commit history")

        return True  # Don't fail if we can't check git

    def _validate_team_structure(self) -> bool:
        """Validate that project has team-oriented structure"""
        print("\n🏗️  VALIDATING TEAM STRUCTURE...")

        required_team_files = [
            "CLAUDE-TEAM-FIRST.md",
            "AGENTIC-SDLC-TEAM-PRINCIPLES.md",
        ]

        required_dirs = ["docs/feature-proposals", "retrospectives"]

        missing_files = []
        missing_dirs = []

        for file_path in required_team_files:
            if not os.path.exists(file_path):
                missing_files.append(file_path)

        for dir_path in required_dirs:
            if not os.path.exists(dir_path):
                missing_dirs.append(dir_path)

        if missing_files or missing_dirs:
            print("❌ MISSING TEAM STRUCTURE:")
            for file_path in missing_files:
                print(f"   • Missing file: {file_path}")
            for dir_path in missing_dirs:
                print(f"   • Missing directory: {dir_path}")
            self.violations.append("Missing team structure")
            return False

        print("✅ Team structure present")
        return True

    def _check_handoff_protocols(self) -> bool:
        """Check for proper team handoff protocols"""
        print("\n🔄 CHECKING HANDOFF PROTOCOLS...")

        handoff_patterns = [
            r"HANDOFF TO:\s*(\w+)",
            r"@(\w+):\s*\"(.+?)\"",
            r"Team assembly for",
            r"Specialist consult needed",
            r"Engaging\s+(\w+-\w+)",
            r"Consulting\s+(\w+-\w+)",
        ]

        handoffs_found = []

        # Check recent documentation for handoff patterns
        docs_paths = ["docs", "retrospectives", "plan"]
        for docs_path in docs_paths:
            if os.path.exists(docs_path):
                for file_path in Path(docs_path).rglob("*.md"):
                    try:
                        content = file_path.read_text()
                        for pattern in handoff_patterns:
                            matches = re.findall(pattern, content, re.IGNORECASE)
                            handoffs_found.extend(matches)
                    except (OSError, PermissionError):
                        continue

        if len(handoffs_found) < 2:  # Require at least 2 handoff instances
            print("❌ INSUFFICIENT HANDOFF PROTOCOLS")
            print("   Team handoffs not being used properly")
            self.violations.append("Insufficient handoff protocols")
            return False

        print(f"✅ Handoff protocols found: {len(handoffs_found)} instances")
        return True

    def _print_final_report(self, success: bool):
        """Print final validation report"""
        print("\n" + "=" * 70)
        print("🏆 TEAM ENGAGEMENT VALIDATION REPORT")
        print("=" * 70)

        if success:
            print("✅ TEAM-FIRST BEHAVIOR VALIDATED")
            print("   • All team engagement requirements met")
            print("   • No solo work patterns detected")
            print("   • Proper team consultations in place")
            print("   • Team structure correctly configured")
        else:
            print("❌ TEAM-FIRST BEHAVIOR VIOLATIONS DETECTED")
            print("   VIOLATIONS:")
            for violation in self.violations:
                print(f"   • {violation}")
            print("\n   🚨 WORK MUST BE BLOCKED UNTIL VIOLATIONS ARE FIXED")
            print("   🚨 NO SOLO WORK IS PERMITTED")

        print("=" * 70)


def main():
    parser = argparse.ArgumentParser(description="Validate team engagement compliance")
    parser.add_argument(
        "--strict", action="store_true", help="Enable strict mode (zero tolerance)"
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=0,
        help="Maximum violations allowed (default: 0)",
    )

    args = parser.parse_args()

    validator = TeamEngagementValidator(strict_mode=args.strict)
    success = validator.validate_all()

    if not success:
        print("\n🛑 TEAM ENGAGEMENT VALIDATION FAILED")
        print("🛑 ALL WORK MUST BE BLOCKED UNTIL COMPLIANCE IS ACHIEVED")
        sys.exit(1)

    print("\n✅ TEAM ENGAGEMENT VALIDATION PASSED")
    sys.exit(0)


if __name__ == "__main__":
    main()
