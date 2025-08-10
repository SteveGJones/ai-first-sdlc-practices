#!/usr/bin/env python3
"""
Check Crisis Ready - Validate Team Crisis Response Readiness

Determines if a team is ready for crisis simulation based on their
collaboration scores, experience level, and past performance.
"""

import json
import sys
from pathlib import Path
from typing import Dict, Tuple


PROGRESS_FILE = ".github/coaching/team_progress.json"


def load_progress() -> Dict:
    """Load team progress data"""
    progress_path = Path(PROGRESS_FILE)

    if not progress_path.exists():
        return {
            "level": 1,
            "experience": 0,
            "collaboration_scores": [],
            "crisis_simulations": 0,
        }

    with open(progress_path, "r") as f:
        return json.load(f)


def check_crisis_readiness(progress: Dict) -> Tuple[bool, str, Dict]:
    """
    Check if team is ready for crisis simulation

    Requirements:
    - Level 2+ (Contributors or higher)
    - Average collaboration score > 50
    - At least 5 successful PRs
    - No recent failures
    """
    readiness_checks = {
        "level": False,
        "collaboration": False,
        "experience": False,
        "stability": False,
    }

    issues = []

    # Check level
    if progress.get("level", 1) >= 2:
        readiness_checks["level"] = True
    else:
        issues.append("Need to reach Level 2 (Contributor)")

    # Check collaboration average
    scores = progress.get("collaboration_scores", [])
    if scores:
        avg_score = sum(scores) / len(scores)
        if avg_score >= 50:
            readiness_checks["collaboration"] = True
        else:
            issues.append(f"Collaboration score too low ({avg_score:.1f}/50)")
    else:
        issues.append("No collaboration history")

    # Check experience
    if progress.get("successful_prs", 0) >= 5:
        readiness_checks["experience"] = True
    else:
        prs_needed = 5 - progress.get("successful_prs", 0)
        issues.append(f"Need {prs_needed} more successful PRs")

    # Check stability (no recent streak breaks)
    if progress.get("current_streak", 0) > 0 or progress.get("best_streak", 0) >= 3:
        readiness_checks["stability"] = True
    else:
        issues.append("Build a streak of 3+ team-coordinated PRs")

    # Determine overall readiness
    is_ready = all(readiness_checks.values())

    # Generate recommendation
    if is_ready:
        recommendation = "🚀 Team is READY for crisis simulation!"
    elif sum(readiness_checks.values()) >= 3:
        recommendation = "⚡ Almost ready! Address remaining issues."
    elif sum(readiness_checks.values()) >= 2:
        recommendation = "💡 Making progress. Keep building team coordination."
    else:
        recommendation = "🌱 Focus on fundamentals before crisis training."

    return (
        is_ready,
        recommendation,
        {
            "checks": readiness_checks,
            "issues": issues,
            "crisis_level": determine_crisis_level(progress),
        },
    )


def determine_crisis_level(progress: Dict) -> str:
    """Determine appropriate crisis level based on experience"""
    level = progress.get("level", 1)
    simulations_completed = progress.get("crisis_simulations", 0)

    if level >= 4 and simulations_completed >= 5:
        return "🔥 EXTREME"
    elif level >= 3 and simulations_completed >= 3:
        return "⚡ HARD"
    elif level >= 2 and simulations_completed >= 1:
        return "💡 MODERATE"
    else:
        return "🌱 BEGINNER"


def main():
    """Main entry point for GitHub Actions"""
    progress = load_progress()

    # Check readiness
    is_ready, recommendation, details = check_crisis_readiness(progress)

    # Output results
    print("=" * 60)
    print("🚨 CRISIS SIMULATION READINESS CHECK")
    print("=" * 60)

    # Current status
    print(f"\nTeam Level: {progress.get('level', 1)}")
    print(f"Experience: {progress.get('experience', 0)} XP")
    print(f"Successful PRs: {progress.get('successful_prs', 0)}")
    print(f"Crisis Simulations Completed: {progress.get('crisis_simulations', 0)}")

    # Readiness checks
    print("\n📋 Readiness Criteria:")
    for check, passed in details["checks"].items():
        status = "✅" if passed else "❌"
        print(f"  {status} {check.replace('_', ' ').title()}")

    # Issues
    if details["issues"]:
        print("\n⚠️  Requirements Not Met:")
        for issue in details["issues"]:
            print(f"  - {issue}")

    # Recommendation
    print(f"\n{recommendation}")

    if is_ready:
        print(f"Recommended Crisis Level: {details['crisis_level']}")

    # GitHub Actions output
    if "--github-output" in sys.argv:
        print(f"::set-output name=is_ready::{str(is_ready).lower()}")
        print(f"::set-output name=crisis_level::{details['crisis_level']}")

    sys.exit(0 if is_ready else 1)


if __name__ == "__main__":
    main()
