#!/usr/bin/env python3
"""
Analyze Collaboration - Team Coordination Pattern Analyzer

Analyzes how well AI agents coordinate as a team, measuring
collaboration quality, communication patterns, and team synergy.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime


def analyze_collaboration_patterns(pr_data: Dict) -> Dict:
    """
    Analyze collaboration patterns in pull request
    
    Looks for:
    - Multi-agent coordination
    - Clear communication
    - Shared responsibility
    - Complementary skills usage
    """
    collaboration_score = 0
    patterns = []
    issues = []
    
    # Check for multi-file coordination
    files = pr_data.get("files_changed", [])
    if "docs/" in str(files) and "tests/" in str(files):
        collaboration_score += 20
        patterns.append("Documentation + Tests (good coverage)")
    
    # Check commit patterns
    commits = pr_data.get("commits", [])
    if len(commits) > 1:
        # Look for iterative improvement
        if any("fix" in c.lower() for c in commits) and any("test" in c.lower() for c in commits):
            collaboration_score += 15
            patterns.append("Iterative improvement with testing")
    
    # Check for agent mentions
    description = pr_data.get("description", "").lower()
    agent_mentions = [
        "architect", "engineer", "reviewer", "validator",
        "tester", "documenter", "coordinator"
    ]
    
    mentioned_agents = [a for a in agent_mentions if a in description]
    if len(mentioned_agents) >= 3:
        collaboration_score += 25
        patterns.append(f"Multiple agents coordinated: {', '.join(mentioned_agents)}")
    elif len(mentioned_agents) == 1:
        issues.append("Single agent work - needs more coordination")
    
    # Check for validation and review
    if "validated" in description or "reviewed" in description:
        collaboration_score += 20
        patterns.append("Peer review process followed")
    
    # Check for planning artifacts
    if any("proposal" in f for f in files) or any("plan" in f for f in files):
        collaboration_score += 20
        patterns.append("Planning before implementation")
    
    return {
        "collaboration_score": collaboration_score,
        "collaboration_level": get_collaboration_level(collaboration_score),
        "patterns": patterns,
        "issues": issues,
        "recommendation": get_collaboration_recommendation(collaboration_score)
    }


def get_collaboration_level(score: int) -> str:
    """Determine collaboration level"""
    if score >= 80:
        return "🏆 LEGENDARY"
    elif score >= 60:
        return "⭐ EXCELLENT"
    elif score >= 40:
        return "✅ GOOD"
    elif score >= 20:
        return "💡 DEVELOPING"
    else:
        return "⚠️ NEEDS IMPROVEMENT"


def get_collaboration_recommendation(score: int) -> str:
    """Get Billy Wright style recommendation"""
    if score >= 80:
        return "Legendary teamwork! This is how champions play."
    elif score >= 60:
        return "Excellent coordination. Keep setting up your teammates."
    elif score >= 40:
        return "Good team play. Consider more cross-functional coordination."
    elif score >= 20:
        return "You're learning to pass. Focus on team communication."
    else:
        return "Remember: No one wins alone. Engage your team."


def main():
    """Main entry point for GitHub Actions"""
    # Parse PR data from environment or args
    pr_data = {
        "files_changed": sys.argv[1].split(',') if len(sys.argv) > 1 else [],
        "commits": sys.argv[2].split(',') if len(sys.argv) > 2 else [],
        "description": sys.argv[3] if len(sys.argv) > 3 else ""
    }
    
    # Analyze collaboration
    result = analyze_collaboration_patterns(pr_data)
    
    # Output results
    print("=" * 60)
    print("🤝 BILLY WRIGHT COLLABORATION ANALYZER")
    print("=" * 60)
    print(f"\nCollaboration Level: {result['collaboration_level']}")
    print(f"Score: {result['collaboration_score']}/100")
    
    if result["patterns"]:
        print("\n✅ Positive Patterns:")
        for pattern in result["patterns"]:
            print(f"  + {pattern}")
    
    if result["issues"]:
        print("\n⚠️  Areas for Improvement:")
        for issue in result["issues"]:
            print(f"  - {issue}")
    
    print(f"\n💡 {result['recommendation']}")
    
    # Set output for GitHub Actions
    if len(sys.argv) > 4 and sys.argv[4] == "--github-output":
        print(f"::set-output name=score::{result['collaboration_score']}")
        print(f"::set-output name=level::{result['collaboration_level']}")
    
    sys.exit(0)


if __name__ == "__main__":
    main()