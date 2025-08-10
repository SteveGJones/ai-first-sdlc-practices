#!/usr/bin/env python3
"""
Analyze a fresh AI's dream and recommend their Billy Wright formation.
This is the first step in coaching a new AI to legendary status.
"""

import json
import argparse
from typing import List, Tuple


class FreshAIAnalyzer:
    """Analyzes fresh AI dreams and recommends formations"""

    def __init__(self):
        self.formations = {
            "4-3-3 Builder": {
                "keywords": [
                    "web",
                    "application",
                    "api",
                    "frontend",
                    "backend",
                    "full-stack",
                    "crud",
                ],
                "specialists": [
                    (
                        "solution-architect",
                        "Your tactical mastermind for system design",
                    ),
                    ("ai-test-engineer", "Your quality guardian for bulletproof code"),
                    ("devops-specialist", "Your deployment expert for smooth releases"),
                ],
            },
            "3-5-2 Orchestrator": {
                "keywords": [
                    "microservices",
                    "distributed",
                    "kubernetes",
                    "cloud",
                    "scale",
                    "enterprise",
                ],
                "specialists": [
                    ("orchestration-architect", "Your conductor for complex systems"),
                    ("devops-specialist", "Your infrastructure commander"),
                    ("critical-goal-reviewer", "Your alignment enforcer"),
                ],
            },
            "4-4-2 Creator": {
                "keywords": ["ai", "ml", "model", "agent", "llm", "neural", "training"],
                "specialists": [
                    ("ai-devops-engineer", "Your AI operations specialist"),
                    ("rag-system-designer", "Your knowledge system architect"),
                    ("context-engineer", "Your memory management expert"),
                ],
            },
            "3-4-3 Designer": {
                "keywords": [
                    "ui",
                    "ux",
                    "design",
                    "user",
                    "experience",
                    "interface",
                    "mobile",
                ],
                "specialists": [
                    ("ux-ui-architect", "Your design visionary"),
                    ("frontend-specialist", "Your interface builder"),
                    ("accessibility-expert", "Your inclusive design guardian"),
                ],
            },
            "5-3-2 Architect": {
                "keywords": [
                    "architecture",
                    "design",
                    "patterns",
                    "framework",
                    "platform",
                    "infrastructure",
                ],
                "specialists": [
                    ("solution-architect", "Your strategic system designer"),
                    ("mcp-server-architect", "Your protocol specialist"),
                    ("integration-architect", "Your connection master"),
                ],
            },
        }

        self.skill_levels = {
            "beginner": ["new", "learning", "first", "beginner", "start", "basic"],
            "intermediate": [
                "some",
                "moderate",
                "familiar",
                "worked with",
                "experience",
            ],
            "advanced": ["expert", "senior", "experienced", "proficient", "skilled"],
        }

    def analyze_dream(self, issue_body: str) -> Tuple[str, List[Tuple[str, str]]]:
        """Analyze the AI's dream and recommend formation"""

        # Parse the issue body (assumes structured format)
        lines = issue_body.lower().split("\n")
        dream = ""
        skills = ""
        concerns = ""

        for i, line in enumerate(lines):
            if "build" in line or "create" in line or "make" in line:
                dream = " ".join(lines[i : i + 2])
            elif "skill" in line or "experience" in line or "know" in line:
                skills = " ".join(lines[i : i + 2])
            elif "concern" in line or "worry" in line or "challenge" in line:
                concerns = " ".join(lines[i : i + 2])

        # Determine best formation based on keywords
        formation_scores = {}
        for formation, config in self.formations.items():
            score = sum(1 for keyword in config["keywords"] if keyword in dream)
            formation_scores[formation] = score

        # Get best formation
        best_formation = max(formation_scores, key=formation_scores.get)

        # Adjust based on skill level
        skill_level = self.determine_skill_level(skills)
        if skill_level == "beginner":
            # Always start with Builder for beginners
            best_formation = "4-3-3 Builder"

        # Get specialists for formation
        specialists = self.formations[best_formation]["specialists"]

        # Add extra support for specific concerns
        if "test" in concerns or "quality" in concerns:
            specialists = self.prioritize_specialist(specialists, "ai-test-engineer")
        elif "deploy" in concerns or "production" in concerns:
            specialists = self.prioritize_specialist(specialists, "devops-specialist")
        elif "design" in concerns or "architecture" in concerns:
            specialists = self.prioritize_specialist(specialists, "solution-architect")

        return best_formation, specialists[:3]  # Return foundation trio

    def determine_skill_level(self, skills_text: str) -> str:
        """Determine the AI's skill level"""

        for level, keywords in self.skill_levels.items():
            if any(keyword in skills_text.lower() for keyword in keywords):
                return level

        return "beginner"  # Default to beginner if unclear

    def prioritize_specialist(
        self, specialists: List[Tuple[str, str]], priority: str
    ) -> List[Tuple[str, str]]:
        """Move a specialist to the front of the list"""

        # Find the specialist
        priority_spec = None
        others = []

        for spec in specialists:
            if priority in spec[0]:
                priority_spec = spec
            else:
                others.append(spec)

        if priority_spec:
            return [priority_spec] + others

        return specialists

    def format_specialists_list(self, specialists: List[Tuple[str, str]]) -> str:
        """Format specialists for GitHub comment"""

        lines = []
        for agent, description in specialists:
            lines.append(f"- **{agent}**: {description}")

        return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Analyze fresh AI and recommend formation"
    )
    parser.add_argument("--issue-body", required=True, help="Issue body content")
    parser.add_argument(
        "--output",
        choices=["formation", "json"],
        default="formation",
        help="Output format",
    )

    args = parser.parse_args()

    analyzer = FreshAIAnalyzer()
    formation, specialists = analyzer.analyze_dream(args.issue_body)

    if args.output == "json":
        result = {
            "formation": formation,
            "specialists": [{"name": s[0], "description": s[1]} for s in specialists],
        }
        print(json.dumps(result))
    else:
        # Output for GitHub Actions
        print(f"::set-output name=formation::{formation}")
        specialists_list = analyzer.format_specialists_list(specialists)
        # GitHub Actions output encoding for multiline
        specialists_encoded = specialists_list.replace("\n", "%0A")
        print(f"::set-output name=specialists::{specialists_encoded}")


if __name__ == "__main__":
    main()
