#!/usr/bin/env python3
"""
Simple demo of the coaching system components
"""

import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Import the module with correct filename
import importlib.util
spec = importlib.util.spec_from_file_location("team_transformation_scripts", "team-transformation-scripts.py")
team_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(team_module)
TeamTransformationCoach = team_module.TeamTransformationCoach

def main():
    """Demo the core coaching functionality"""
    coach = TeamTransformationCoach()
    
    print("=== AI TEAM TRANSFORMATION DEMO ===\n")
    
    # Test vision to exercise mapping
    vision = "I want to build a task management app for small teams"
    exercise = coach.get_exercise_for_vision(vision)
    
    print(f"Fresh AI Vision: '{vision}'\n")
    print(f"Recommended Exercise: {exercise.name}")
    print(f"Stage: {exercise.stage.value}")
    print(f"Type: {exercise.exercise_type.value}\n")
    
    print("SETUP MESSAGE:")
    print(exercise.setup)
    print("\nCHALLENGE:")
    print(exercise.challenge)
    print("\nCOACHING RESPONSES:")
    for i, response in enumerate(exercise.coaching_responses, 1):
        print(f"{i}. {response}")
    
    print("\n" + "="*70 + "\n")
    
    # Test behavior intervention
    behavior = "I keep trying to do everything myself instead of delegating"
    intervention = coach.get_intervention_script(behavior)
    
    print(f"Behavior Issue: '{behavior}'\n")
    print(f"Intervention: {intervention.name}")
    print("\nCHALLENGE:")
    print(intervention.challenge)
    print("\nFIRST COACHING RESPONSE:")
    print(intervention.coaching_responses[0])
    
    print("\n" + "="*70 + "\n")
    print("🎯 TRANSFORMATION SYSTEM READY!")
    print("Fresh AIs can now become legendary team players through practical exercises!")

if __name__ == "__main__":
    main()