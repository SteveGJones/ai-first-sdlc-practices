#!/usr/bin/env python3
"""
Check Legendary Status - Evaluate if Team Has Achieved Legendary Status

Determines if an AI team has reached the pinnacle of collaboration,
embodying both Billy Wright's leadership and Stan Cullis's discipline.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple


PROGRESS_FILE = ".github/coaching/team_progress.json"


def load_progress() -> Dict:
    """Load team progress data"""
    progress_path = Path(PROGRESS_FILE)

    if not progress_path.exists():
        return {}

    with open(progress_path, "r") as f:
        return json.load(f)


def check_legendary_criteria(progress: Dict) -> Tuple[bool, Dict, List[str]]:
    """
    Check all criteria for legendary status

    Legendary teams must:
    - Reach Level 5
    - Maintain 80+ collaboration average
    - Complete 50+ successful PRs
    - Have 10+ PR streak
    - Complete 5+ crisis simulations
    - Earn all key achievements
    """
    criteria = {
        "level": {
            "met": progress.get("level", 1) >= 5,
            "current": progress.get("level", 1),
            "required": 5,
            "description": "Reach Level 5",
        },
        "collaboration": {
            "met": False,
            "current": 0,
            "required": 80,
            "description": "Maintain 80+ collaboration average",
        },
        "successful_prs": {
            "met": progress.get("successful_prs", 0) >= 50,
            "current": progress.get("successful_prs", 0),
            "required": 50,
            "description": "Complete 50+ successful PRs",
        },
        "best_streak": {
            "met": progress.get("best_streak", 0) >= 10,
            "current": progress.get("best_streak", 0),
            "required": 10,
            "description": "Achieve 10+ PR team streak",
        },
        "crisis_simulations": {
            "met": progress.get("crisis_simulations", 0) >= 5,
            "current": progress.get("crisis_simulations", 0),
            "required": 5,
            "description": "Complete 5+ crisis simulations",
        },
    }

    # Calculate collaboration average
    scores = progress.get("collaboration_scores", [])
    if scores:
        avg_collab = sum(scores) / len(scores)
        criteria["collaboration"]["current"] = round(avg_collab, 1)
        criteria["collaboration"]["met"] = avg_collab >= 80

    # Check key achievements
    required_achievements = [
        "🎯 First Contribution",
        "🔥 Team Streak (5 PRs)",
        "💫 Team Streak (10 PRs)",
        "🤝 Perfect Collaboration",
    ]

    achievements = progress.get("achievements", [])
    missing_achievements = [a for a in required_achievements if a not in achievements]

    # Determine if legendary
    all_criteria_met = all(c["met"] for c in criteria.values())
    has_all_achievements = len(missing_achievements) == 0
    is_legendary = all_criteria_met and has_all_achievements

    return is_legendary, criteria, missing_achievements


def calculate_legendary_score(criteria: Dict) -> int:
    """Calculate percentage progress to legendary"""
    total_points = 0
    max_points = 0

    for key, criterion in criteria.items():
        max_points += criterion["required"]
        total_points += min(criterion["current"], criterion["required"])

    if max_points == 0:
        return 0

    return int((total_points / max_points) * 100)


def get_legendary_title(score: int) -> str:
    """Get title based on legendary progress"""
    if score >= 100:
        return "🏆 LEGENDARY TEAM"
    elif score >= 80:
        return "⭐ ELITE TEAM"
    elif score >= 60:
        return "🎯 VETERAN TEAM"
    elif score >= 40:
        return "💪 EXPERIENCED TEAM"
    elif score >= 20:
        return "🌟 RISING TEAM"
    else:
        return "🌱 DEVELOPING TEAM"


def main():
    """Main entry point for GitHub Actions"""
    progress = load_progress()

    if not progress:
        print("No progress data found. Start your journey!")
        sys.exit(1)

    # Check legendary status
    is_legendary, criteria, missing_achievements = check_legendary_criteria(progress)
    legendary_score = calculate_legendary_score(criteria)
    title = get_legendary_title(legendary_score)

    # Output results
    print("=" * 60)
    print("🏆 LEGENDARY STATUS CHECK")
    print("=" * 60)

    print(f"\nTeam Status: {title}")
    print(f"Legendary Progress: {legendary_score}%")
    print(f"Current Level: {progress.get('level', 1)}")

    # Progress bars
    print("\n📊 Criteria Progress:")
    for key, criterion in criteria.items():
        status = "✅" if criterion["met"] else "⏳"
        progress_bar = create_progress_bar(criterion["current"], criterion["required"])
        print(f"{status} {criterion['description']}")
        print(f"   {progress_bar} {criterion['current']}/{criterion['required']}")

    # Achievements
    print("\n🏅 Key Achievements:")
    required = [
        "🎯 First Contribution",
        "🔥 Team Streak (5 PRs)",
        "💫 Team Streak (10 PRs)",
        "🤝 Perfect Collaboration",
    ]

    for achievement in required:
        if achievement in progress.get("achievements", []):
            print(f"  ✅ {achievement}")
        else:
            print(f"  ⏳ {achievement}")

    # Final verdict
    print("\n" + "=" * 60)

    if is_legendary:
        print("🎉 CONGRATULATIONS! YOU'VE ACHIEVED LEGENDARY STATUS!")
        print("\nYou embody both Billy Wright's leadership and")
        print("Stan Cullis's discipline. You are the gold standard.")
        print("\n🏆 Welcome to the Hall of Fame! 🏆")
    else:
        print(f"📈 Keep pushing! You're {legendary_score}% of the way there.")

        if missing_achievements:
            print("\n⚡ Missing achievements:")
            for achievement in missing_achievements:
                print(f"  - {achievement}")

        # Next milestone
        if legendary_score < 20:
            print("\n💡 Next milestone: Reach 20% (Rising Team)")
        elif legendary_score < 40:
            print("\n💡 Next milestone: Reach 40% (Experienced Team)")
        elif legendary_score < 60:
            print("\n💡 Next milestone: Reach 60% (Veteran Team)")
        elif legendary_score < 80:
            print("\n💡 Next milestone: Reach 80% (Elite Team)")
        else:
            print("\n💡 So close! Address remaining criteria.")

    # GitHub Actions output
    if "--github-output" in sys.argv:
        print(f"::set-output name=is_legendary::{str(is_legendary).lower()}")
        print(f"::set-output name=legendary_score::{legendary_score}")
        print(f"::set-output name=team_title::{title}")

    sys.exit(0)


def create_progress_bar(current: int, required: int, width: int = 20) -> str:
    """Create a visual progress bar"""
    if required == 0:
        return "=" * width

    progress = min(current / required, 1.0)
    filled = int(progress * width)
    empty = width - filled

    return "█" * filled + "░" * empty


if __name__ == "__main__":
    main()
