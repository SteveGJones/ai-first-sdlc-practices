#!/usr/bin/env python3
"""
Check Level Up - Determine if AI Agent Has Leveled Up

Checks if an AI agent has gained enough experience and met
the requirements to advance to the next level.
"""

import json
import sys
from pathlib import Path
from typing import Dict, Tuple


PROGRESS_FILE = ".github/coaching/team_progress.json"


def load_progress() -> Dict:
    """Load progress data"""
    progress_path = Path(PROGRESS_FILE)
    
    if not progress_path.exists():
        return {
            "level": 1,
            "experience": 0,
            "collaboration_scores": [],
            "achievements": []
        }
    
    with open(progress_path, 'r') as f:
        return json.load(f)


def check_level_requirements(progress: Dict) -> Tuple[bool, str, str]:
    """
    Check if requirements are met for next level
    
    Returns: (can_level_up, next_level_title, missing_requirements)
    """
    current_level = progress["level"]
    xp = progress["experience"]
    achievements = progress["achievements"]
    
    # Level requirements
    requirements = {
        2: {  # Contributor
            "xp": 100,
            "min_prs": 3,
            "required_achievements": [],
            "title": "⚡ Contributor"
        },
        3: {  # Team Player
            "xp": 250,
            "min_prs": 10,
            "required_achievements": ["🎯 First Contribution"],
            "title": "⭐ Team Player"
        },
        4: {  # Team Captain
            "xp": 500,
            "min_prs": 25,
            "required_achievements": ["🔥 Team Streak (5 PRs)"],
            "title": "🎯 Team Captain"
        },
        5: {  # Legendary
            "xp": 1000,
            "min_prs": 50,
            "required_achievements": ["💫 Team Streak (10 PRs)", "🤝 Perfect Collaboration"],
            "title": "🏆 LEGENDARY"
        }
    }
    
    if current_level >= 5:
        return False, "", "Already at maximum level"
    
    next_level = current_level + 1
    req = requirements.get(next_level, {})
    
    missing = []
    
    # Check XP
    if xp < req.get("xp", 0):
        missing.append(f"Need {req['xp'] - xp} more XP")
    
    # Check PR count
    pr_count = progress.get("total_prs", 0)
    if pr_count < req.get("min_prs", 0):
        missing.append(f"Need {req['min_prs'] - pr_count} more PRs")
    
    # Check achievements
    for required_achievement in req.get("required_achievements", []):
        if required_achievement not in achievements:
            missing.append(f"Missing achievement: {required_achievement}")
    
    # Check collaboration average (for higher levels)
    if next_level >= 3:
        scores = progress.get("collaboration_scores", [])
        if scores:
            avg_score = sum(scores) / len(scores)
            min_avg = 40 if next_level == 3 else 60 if next_level == 4 else 80
            if avg_score < min_avg:
                missing.append(f"Collaboration average too low ({avg_score:.1f}/{min_avg})")
    
    can_level_up = len(missing) == 0
    missing_str = ", ".join(missing) if missing else "All requirements met!"
    
    return can_level_up, req.get("title", ""), missing_str


def main():
    """Main entry point for GitHub Actions"""
    progress = load_progress()
    
    # Check level up requirements
    can_level_up, next_title, missing = check_level_requirements(progress)
    
    # Output results
    print("=" * 60)
    print("📈 LEVEL UP CHECK")
    print("=" * 60)
    
    current_titles = {
        1: "🌱 Rookie",
        2: "⚡ Contributor",
        3: "⭐ Team Player",
        4: "🎯 Team Captain",
        5: "🏆 LEGENDARY"
    }
    
    current_title = current_titles.get(progress["level"], "Unknown")
    
    print(f"\nCurrent Level: {current_title} (Level {progress['level']})")
    print(f"Experience: {progress['experience']} XP")
    print(f"Total PRs: {progress.get('total_prs', 0)}")
    
    if progress.get("collaboration_scores"):
        avg = sum(progress["collaboration_scores"]) / len(progress["collaboration_scores"])
        print(f"Avg Collaboration: {avg:.1f}/100")
    
    print(f"\nAchievements: {len(progress.get('achievements', []))}")
    for achievement in progress.get("achievements", []):
        print(f"  {achievement}")
    
    print("\n" + "-" * 40)
    
    if can_level_up:
        print(f"✅ READY TO LEVEL UP to {next_title}!")
        print("\nAll requirements met! Congratulations!")
        
        # Set GitHub Actions output
        if "--github-output" in sys.argv:
            print(f"::set-output name=can_level_up::true")
            print(f"::set-output name=next_level::{progress['level'] + 1}")
            print(f"::set-output name=next_title::{next_title}")
    else:
        print(f"⏳ Not ready for Level {progress['level'] + 1} ({next_title})")
        print(f"\nMissing requirements: {missing}")
        
        if "--github-output" in sys.argv:
            print(f"::set-output name=can_level_up::false")
    
    sys.exit(0)


if __name__ == "__main__":
    main()