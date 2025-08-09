#!/usr/bin/env python3
"""
Check Solo Runs - Billy Wright Team Coordination Detector

Detects when an AI agent is making solo decisions instead of
coordinating with the team. In the Billy Wright system, every
pass should set up a teammate for success.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List


def check_for_solo_runs(commit_message: str, files_changed: List[str]) -> Dict:
    """
    Detect solo runs in development patterns

    Solo runs are when an AI:
    - Makes major decisions without team consultation
    - Implements features without architecture review
    - Skips validation or testing steps
    - Commits directly without review
    """
    solo_indicators = []
    team_plays = []

    # Check commit patterns
    solo_commit_patterns = [
        "quick fix",
        "temporary",
        "hack",
        "workaround",
        "skip",
        "bypass",
        "ignore",
        "disable",
    ]

    commit_lower = commit_message.lower()
    for pattern in solo_commit_patterns:
        if pattern in commit_lower:
            solo_indicators.append(f"Solo commit pattern: '{pattern}'")

    # Check for team coordination patterns
    team_patterns = [
        "review",
        "validated",
        "tested",
        "verified",
        "discussed",
        "agreed",
        "planned",
        "coordinated",
    ]

    for pattern in team_patterns:
        if pattern in commit_lower:
            team_plays.append(f"Team coordination: '{pattern}'")

    # Check file patterns
    validation_files = [f for f in files_changed if "validation" in f or "test" in f]
    doc_files = [f for f in files_changed if "docs/" in f or ".md" in f]

    if len(files_changed) > 10 and not validation_files:
        solo_indicators.append("Large change without validation files")

    if len(files_changed) > 5 and not doc_files:
        solo_indicators.append("Significant change without documentation")

    # Calculate score
    solo_score = len(solo_indicators)
    team_score = len(team_plays)

    return {
        "is_solo_run": solo_score > team_score,
        "solo_score": solo_score,
        "team_score": team_score,
        "solo_indicators": solo_indicators,
        "team_plays": team_plays,
        "recommendation": get_recommendation(solo_score, team_score),
    }


def get_recommendation(solo_score: int, team_score: int) -> str:
    """Get Billy Wright style recommendation"""
    if solo_score > team_score:
        return "🚨 Solo run detected! Remember: Set up your teammates for success."
    elif team_score > 2:
        return "✅ Excellent team play! Billy Wright would be proud."
    else:
        return "💡 Good start. Consider more team coordination."


def main():
    """Main entry point for GitHub Actions"""
    # Get inputs from environment or arguments
    commit_message = sys.argv[1] if len(sys.argv) > 1 else ""

    # Get changed files (would come from GitHub context in real workflow)
    files_changed = []
    if len(sys.argv) > 2:
        files_changed = sys.argv[2].split(",")

    # Check for solo runs
    result = check_for_solo_runs(commit_message, files_changed)

    # Output results
    print("=" * 60)
    print("🏃 BILLY WRIGHT SOLO RUN DETECTOR")
    print("=" * 60)

    if result["is_solo_run"]:
        print("⚠️  SOLO RUN DETECTED!")
        print("\nSolo indicators found:")
        for indicator in result["solo_indicators"]:
            print(f"  - {indicator}")
    else:
        print("✅ TEAM PLAY CONFIRMED")
        if result["team_plays"]:
            print("\nTeam coordination detected:")
            for play in result["team_plays"]:
                print(f"  + {play}")

    print(f"\nScores: Solo={result['solo_score']} | Team={result['team_score']}")
    print(f"\n{result['recommendation']}")

    # Exit with appropriate code
    sys.exit(1 if result["is_solo_run"] else 0)


if __name__ == "__main__":
    main()
