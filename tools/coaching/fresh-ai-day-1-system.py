#!/usr/bin/env python3
"""
Fresh AI Day 1 System - Get coordination working TODAY

This is the simplest possible system that transforms a fresh AI from 
"I'll do everything myself" to "Let me coordinate the right team"
in 15 minutes, not 14 days.

No complex scoring, no theoretical frameworks - just working tactics.
"""

import json
import sys
from datetime import datetime
from pathlib import Path

class FreshAIDay1System:
    """The simplest team coordination system that actually works"""
    
    def __init__(self):
        self.core_formations = {
            # SIMPLE: Just 3-5 core roles per formation type
            "web_app": {
                "core": ["solution-architect", "database-architect", "ux-ui-architect"],
                "first_question": "solution-architect, I need a web app for [USER_SCENARIO] with [KEY_CONSTRAINT]. What architecture handles this elegantly?",
                "success_pattern": "Based on solution-architect's recommendation, database-architect, I need..."
            },
            "ai_system": {
                "core": ["ai-solution-architect", "prompt-engineer", "ai-test-engineer"],
                "first_question": "ai-solution-architect, I need AI that [SPECIFIC_CAPABILITY] for [USER_CONTEXT]. What approach works?",
                "success_pattern": "Building on ai-solution-architect's design, prompt-engineer, I need..."
            },
            "data_platform": {
                "core": ["data-architect", "database-architect", "performance-engineer"],
                "first_question": "data-architect, I need to process [DATA_VOLUME] of [DATA_TYPE] for [BUSINESS_USE]. What patterns work?",
                "success_pattern": "Following data-architect's pipeline design, database-architect, I need..."
            },
            "mobile_app": {
                "core": ["mobile-architect", "ux-ui-architect", "performance-engineer"],
                "first_question": "mobile-architect, I need [DEVICE_TYPES] app for [USER_BEHAVIOR] with [PERFORMANCE_REQUIREMENT]. What architecture works?",
                "success_pattern": "Based on mobile-architect's framework choice, ux-ui-architect, I need..."
            },
            "api_service": {
                "core": ["api-architect", "database-architect", "security-specialist"],
                "first_question": "api-architect, I need API serving [DATA_TYPE] to [CLIENT_TYPES] with [SCALE_REQUIREMENT]. What patterns work?",
                "success_pattern": "Following api-architect's REST design, database-architect, I need..."
            }
        }
        
        self.coordination_tactics = {
            "perfect_question": "[Agent], I need [specific capability] for [user scenario] with [constraint]. What's your recommendation?",
            "handoff_pattern": "Based on [previous-agent]'s recommendation of [specific output], [next-agent], I need...",
            "parallel_pattern": "While [agent1] handles [task1], [agent2], please [task2] so we can [merge_point]",
            "crisis_pattern": "Emergency: [agent1] check [area1], [agent2] analyze [area2], [agent3] verify [area3] - report findings"
        }

    def assess_fresh_ai(self, project_description):
        """5-question assessment that gets fresh AI started immediately"""
        
        print("=== FRESH AI TEAM COORDINATION ASSESSMENT ===")
        print("Answer these 5 questions to get your team working TODAY\n")
        
        # Question 1: Project Type
        print("1. What type of project is this?")
        print("   a) Web application")
        print("   b) AI/ML system") 
        print("   c) Data platform")
        print("   d) Mobile app")
        print("   e) API service")
        
        project_type = input("Your choice (a-e): ").strip().lower()
        
        type_mapping = {
            'a': 'web_app', 'b': 'ai_system', 'c': 'data_platform', 
            'd': 'mobile_app', 'e': 'api_service'
        }
        
        formation_key = type_mapping.get(project_type, 'web_app')
        formation = self.core_formations[formation_key]
        
        # Question 2: Core Challenge
        print(f"\n2. What's your biggest challenge with this {formation_key.replace('_', ' ')}?")
        challenge = input("Describe: ").strip()
        
        # Question 3: User Scenario  
        print(f"\n3. Who uses this and what do they need it to do?")
        user_scenario = input("User scenario: ").strip()
        
        # Question 4: Constraints
        print(f"\n4. What are your key constraints? (performance, budget, timeline, etc.)")
        constraints = input("Key constraint: ").strip()
        
        # Question 5: First Feature
        print(f"\n5. What's the ONE feature you want to build first?")
        first_feature = input("First feature: ").strip()
        
        return self._generate_day1_plan(formation_key, challenge, user_scenario, constraints, first_feature)
    
    def _generate_day1_plan(self, formation_key, challenge, user_scenario, constraint, first_feature):
        """Generate immediate actionable plan"""
        
        formation = self.core_formations[formation_key]
        
        plan = {
            "formation_type": formation_key,
            "core_team": formation["core"],
            "first_question_template": formation["first_question"],
            "actual_first_question": self._customize_question(
                formation["first_question"], user_scenario, constraint
            ),
            "handoff_pattern": formation["success_pattern"],
            "next_steps": [
                f"Ask your first question to {formation['core'][0]}",
                f"Use their answer to guide {formation['core'][1]}",  
                f"Have {formation['core'][2]} validate the approach",
                "Build your first feature with this coordinated plan"
            ],
            "success_check": "Did you reference the previous agent's specific output when talking to the next agent?"
        }
        
        return plan
    
    def _customize_question(self, template, user_scenario, constraint):
        """Convert template to actual question"""
        # Simple replacement - in real system would be smarter
        question = template.replace("[USER_SCENARIO]", user_scenario)
        question = question.replace("[KEY_CONSTRAINT]", constraint)
        question = question.replace("[SPECIFIC_CAPABILITY]", f"handles {user_scenario}")
        question = question.replace("[USER_CONTEXT]", user_scenario)
        return question
    
    def track_real_coordination(self, ai_interaction_log):
        """Simple chemistry tracker that measures ACTUAL coordination behavior"""
        
        chemistry_score = 0
        feedback = []
        
        # Check 1: Did they use specific agent names?
        agent_names = ["solution-architect", "database-architect", "ux-ui-architect", 
                      "ai-solution-architect", "prompt-engineer", "ai-test-engineer"]
        
        used_agents = sum(1 for name in agent_names if name in ai_interaction_log.lower())
        if used_agents >= 2:
            chemistry_score += 30
            feedback.append("✅ Good: Using specific agent names")
        else:
            feedback.append("❌ Issue: Not engaging specific agents")
        
        # Check 2: Did they ask specific questions?
        if "what" in ai_interaction_log.lower() and ("for" in ai_interaction_log.lower() or "with" in ai_interaction_log.lower()):
            chemistry_score += 25
            feedback.append("✅ Good: Asking specific questions with context")
        else:
            feedback.append("❌ Issue: Questions too vague")
        
        # Check 3: Did they reference previous agent work?
        if "based on" in ai_interaction_log.lower() or "following" in ai_interaction_log.lower():
            chemistry_score += 25
            feedback.append("✅ Great: Building on previous agent work")
        else:
            feedback.append("❌ Issue: Not connecting agent outputs")
        
        # Check 4: Did they coordinate multiple agents?
        if used_agents >= 3:
            chemistry_score += 20
            feedback.append("✅ Excellent: Coordinating multiple agents")
        elif used_agents == 2:
            chemistry_score += 10
            feedback.append("✅ Good: Using multiple agents")
        
        return {
            "chemistry_score": chemistry_score,
            "status": self._get_status(chemistry_score),
            "feedback": feedback,
            "next_action": self._get_next_action(chemistry_score, feedback)
        }
    
    def _get_status(self, score):
        if score >= 80: return "COORDINATING"
        elif score >= 60: return "LEARNING"
        elif score >= 40: return "IMPROVING"
        else: return "STARTING"
    
    def _get_next_action(self, score, feedback):
        if score < 40:
            return "Try asking: '[agent-name], I need [specific thing] for [user scenario] with [constraint]. What works?'"
        elif score < 60:
            return "Try building: 'Based on [previous-agent]'s recommendation of [specific output], [next-agent], I need...'"
        elif score < 80:
            return "Try parallel work: 'While [agent1] handles [task1], [agent2] please [task2]'"
        else:
            return "Great! Keep using this coordination pattern for complex features"

def main():
    """Command-line interface for fresh AI day 1 system"""
    
    system = FreshAIDay1System()
    
    if len(sys.argv) < 2:
        print("Fresh AI Day 1 System - Get team coordination working TODAY")
        print()
        print("Commands:")
        print("  assess    - 5-question assessment to get started")
        print("  track     - Check if your coordination is working")  
        print("  demo      - See working example")
        print()
        print("Usage: python fresh-ai-day-1-system.py <command>")
        return
    
    command = sys.argv[1]
    
    if command == "assess":
        if len(sys.argv) < 3:
            print("Describe your project in one sentence:")
            description = input("> ").strip()
        else:
            description = sys.argv[2]
            
        plan = system.assess_fresh_ai(description)
        
        print("\n" + "="*60)
        print("YOUR TEAM COORDINATION PLAN")
        print("="*60)
        print(f"Formation: {plan['formation_type'].replace('_', ' ').title()}")
        print(f"Core Team: {', '.join(plan['core_team'])}")
        print()
        print("YOUR FIRST QUESTION:")
        print(f"  {plan['actual_first_question']}")
        print()
        print("NEXT STEPS:")
        for i, step in enumerate(plan['next_steps'], 1):
            print(f"  {i}. {step}")
        print()
        print("SUCCESS CHECK:")
        print(f"  {plan['success_check']}")
        
        # Save plan for tracking
        plan_file = Path("day1_plan.json")
        with plan_file.open('w') as f:
            json.dump(plan, f, indent=2)
        print(f"\nPlan saved to {plan_file}")
        
    elif command == "track":
        print("Paste your team coordination attempt (agent questions/responses):")
        print("(Press Ctrl+D when done)")
        lines = []
        try:
            while True:
                line = input()
                lines.append(line)
        except EOFError:
            pass
        
        interaction_log = "\n".join(lines)
        result = system.track_real_coordination(interaction_log)
        
        print(f"\nCHEMISTRY SCORE: {result['chemistry_score']}/100")
        print(f"STATUS: {result['status']}")
        print("\nFEEDBACK:")
        for item in result['feedback']:
            print(f"  {item}")
        print(f"\nNEXT ACTION:")
        print(f"  {result['next_action']}")
        
    elif command == "demo":
        print("=== FRESH AI TEAM COORDINATION DEMO ===")
        print()
        print("SCENARIO: Fresh AI wants to build a task management app")
        print()
        print("❌ BEFORE (Solo Hero):")
        print('  "I\'ll design the database, create the API, build the frontend..."')
        print("  Result: Overwhelmed, poor decisions, slow progress")
        print()
        print("✅ AFTER (Team Coordinator):")
        print('  "solution-architect, I need task management for teams of 10-50 people')  
        print('   with real-time collaboration. What architecture handles this elegantly?"')
        print()
        print('  Based on solution-architect\'s microservices recommendation,')
        print('  database-architect, I need task storage that supports...')
        print()
        print('  Following database-architect\'s event-sourcing design,')
        print('  ux-ui-architect, I need interfaces that...')
        print()
        print("RESULT: Coordinated team, expert decisions, 3x faster progress")
        print()
        
        # Show actual chemistry tracking
        demo_log = """
        solution-architect, I need task management for teams of 10-50 people with real-time collaboration. What architecture handles this elegantly?
        
        Based on solution-architect's microservices recommendation, database-architect, I need task storage that supports concurrent updates and event streaming.
        
        Following database-architect's event-sourcing design, ux-ui-architect, I need interfaces that show real-time task updates without overwhelming users.
        """
        
        result = system.track_real_coordination(demo_log)
        print("CHEMISTRY ANALYSIS:")
        print(f"  Score: {result['chemistry_score']}/100")
        print(f"  Status: {result['status']}")
        for item in result['feedback']:
            print(f"  {item}")
        
    else:
        print(f"Unknown command: {command}")
        print("Use 'assess', 'track', or 'demo'")

if __name__ == "__main__":
    main()