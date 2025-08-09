#!/usr/bin/env python3
"""
Update Progress - Track AI Agent Development Journey

Tracks progress of AI agents learning Billy Wright team principles
and Stan Cullis discipline. Updates metrics and progress indicators.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime


PROGRESS_FILE = ".github/coaching/team_progress.json"


def load_progress() -> Dict:
    """Load existing progress or initialize new"""
    progress_path = Path(PROGRESS_FILE)

    if progress_path.exists():
        with open(progress_path, "r") as f:
            return json.load(f)

    return {
        "level": 1,
        "experience": 0,
        "total_prs": 0,
        "successful_prs": 0,
        "collaboration_scores": [],
        "achievements": [],
        "current_streak": 0,
        "best_streak": 0,
        "last_updated": datetime.now().isoformat(),
    }


def calculate_experience_gain(pr_result: Dict) -> int:
    """Calculate XP gained from PR"""
    xp = 10  # Base XP for any PR

    # Bonus for success
    if pr_result.get("merged", False):
        xp += 20

    # Bonus for collaboration
    collab_score = pr_result.get("collaboration_score", 0)
    xp += collab_score // 5

    # Bonus for no solo runs
    if not pr_result.get("has_solo_runs", False):
        xp += 15

    # Bonus for validation
    if pr_result.get("validation_passed", False):
        xp += 10

    return xp


def check_level_up(progress: Dict) -> Tuple[bool, str]:
    """Check if user levels up"""
    xp_for_level = {
        1: 100,
        2: 250,
        3: 500,
        4: 1000,
        5: 2000,  # Legendary status
    }

    current_level = progress["level"]
    current_xp = progress["experience"]

    if current_level < 5:
        required_xp = xp_for_level.get(current_level, 9999)
        if current_xp >= required_xp:
            progress["level"] = current_level + 1
            return True, get_level_title(current_level + 1)

    return False, ""


def get_level_title(level: int) -> str:
    """Get title for level"""
    titles = {
        1: "🌱 Rookie",
        2: "⚡ Contributor",
        3: "⭐ Team Player",
        4: "🎯 Team Captain",
        5: "🏆 LEGENDARY",
    }
    return titles.get(level, "Unknown")


def check_achievements(progress: Dict, pr_result: Dict) -> List[str]:
    """Check for new achievements"""
    new_achievements = []

    # First PR
    if progress["total_prs"] == 1:
        new_achievements.append("🎯 First Contribution")

    # Perfect collaboration
    if pr_result.get("collaboration_score", 0) >= 100:
        if "🤝 Perfect Collaboration" not in progress["achievements"]:
            new_achievements.append("🤝 Perfect Collaboration")

    # No solo runs streak
    if not pr_result.get("has_solo_runs", False):
        progress["current_streak"] += 1
        if progress["current_streak"] > progress["best_streak"]:
            progress["best_streak"] = progress["current_streak"]

        if progress["current_streak"] == 5:
            new_achievements.append("🔥 Team Streak (5 PRs)")
        elif progress["current_streak"] == 10:
            new_achievements.append("💫 Team Streak (10 PRs)")
    else:
        progress["current_streak"] = 0

    # Add new achievements
    for achievement in new_achievements:
        if achievement not in progress["achievements"]:
            progress["achievements"].append(achievement)

    return new_achievements


def update_progress(pr_result: Dict) -> Dict:
    """Update progress based on PR results"""
    progress = load_progress()

    # Update counters
    progress["total_prs"] += 1
    if pr_result.get("merged", False):
        progress["successful_prs"] += 1

    # Update collaboration history
    collab_score = pr_result.get("collaboration_score", 0)
    progress["collaboration_scores"].append(collab_score)
    if len(progress["collaboration_scores"]) > 10:
        progress["collaboration_scores"] = progress["collaboration_scores"][-10:]

    # Calculate and add XP
    xp_gained = calculate_experience_gain(pr_result)
    progress["experience"] += xp_gained

    # Check for level up
    leveled_up, new_title = check_level_up(progress)

    # Check for achievements
    new_achievements = check_achievements(progress, pr_result)

    # Update timestamp
    progress["last_updated"] = datetime.now().isoformat()

    # Save progress
    progress_path = Path(PROGRESS_FILE)
    progress_path.parent.mkdir(parents=True, exist_ok=True)
    with open(progress_path, "w") as f:
        json.dump(progress, f, indent=2)

    return {
        "progress": progress,
        "xp_gained": xp_gained,
        "leveled_up": leveled_up,
        "new_title": new_title,
        "new_achievements": new_achievements,
    }


def main():
    """Main entry point for GitHub Actions"""
    # Parse PR result from arguments
    pr_result = {
        "merged": sys.argv[1].lower() == "true" if len(sys.argv) > 1 else False,
        "collaboration_score": int(sys.argv[2]) if len(sys.argv) > 2 else 0,
        "has_solo_runs": sys.argv[3].lower() == "true" if len(sys.argv) > 3 else False,
        "validation_passed": sys.argv[4].lower() == "true"
        if len(sys.argv) > 4
        else False,
    }

    # Update progress
    result = update_progress(pr_result)

    # Output results
    print("=" * 60)
    print("📊 PROGRESS UPDATE")
    print("=" * 60)

    progress = result["progress"]
    print(f"\nLevel: {get_level_title(progress['level'])} (Level {progress['level']})")
    print(f"Experience: {progress['experience']} XP (+{result['xp_gained']})")
    print(f"Total PRs: {progress['total_prs']}")
    print(f"Success Rate: {progress['successful_prs']}/{progress['total_prs']}")
    print(f"Current Streak: {progress['current_streak']}")

    if result["leveled_up"]:
        print(f"\n🎉 LEVEL UP! You are now: {result['new_title']}")

    if result["new_achievements"]:
        print("\n🏆 NEW ACHIEVEMENTS:")
        for achievement in result["new_achievements"]:
            print(f"  {achievement}")

    # Average collaboration score
    if progress["collaboration_scores"]:
        avg_collab = sum(progress["collaboration_scores"]) / len(
            progress["collaboration_scores"]
        )
        print(f"\nAvg Collaboration: {avg_collab:.1f}/100")

    sys.exit(0)


if __name__ == "__main__":
    main()
