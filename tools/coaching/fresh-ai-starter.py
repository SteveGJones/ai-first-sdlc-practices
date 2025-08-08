#!/usr/bin/env python3
"""
Fresh AI Starter - Get team coordination working in 5 minutes

The SIMPLEST possible system to transform a fresh AI from solo hero to team coordinator.
No complex frameworks, no 14-day programs - just immediate practical coordination.

Usage:
  python fresh-ai-starter.py "I want to build a task management app"
"""

import sys
import json
from datetime import datetime

def get_team_formation(project_description):
    """Determine team formation from project description"""
    
    desc_lower = project_description.lower()
    
    # Simple keyword matching for formation type
    # Check AI/ML first (highest priority for specific tech)
    if any(word in desc_lower for word in ['ai', 'ml', 'machine learning', 'chatbot', 'intelligent', 'llm', 'gpt']):
        return 'ai_system'
    # Check data platforms
    elif any(word in desc_lower for word in ['data', 'analytics', 'pipeline', 'etl', 'warehouse', 'dashboard']):
        return 'data_platform'
    # Check API/service (before web to catch pure API projects)
    elif any(word in desc_lower for word in ['api', 'service', 'microservice', 'rest', 'graphql', 'endpoint']):
        return 'api_service'
    # Check mobile specifically (not just "app")
    elif any(word in desc_lower for word in ['mobile', 'ios', 'android', 'phone', 'native app']):
        return 'mobile_app'
    # Default to web_app for general applications including task management
    # This catches: task management, project management, todo, collaboration tools, etc.
    elif any(word in desc_lower for word in ['web', 'website', 'frontend', 'backend', 'full-stack', 
                                              'task', 'project', 'management', 'todo', 'collaboration',
                                              'team', 'workflow', 'portal', 'platform']):
        return 'web_app'
    else:
        return 'web_app'  # Default

def generate_day1_coordination_plan(project_description):
    """Generate immediate actionable coordination plan"""
    
    formations = {
        "web_app": {
            "core_team": ["solution-architect", "database-architect", "ux-ui-architect"],
            "first_question": "solution-architect, I need a web application for [PROJECT] that handles [USER_SCENARIO]. What architecture pattern works best?",
            "handoff_pattern": "Based on solution-architect's [RECOMMENDATION], database-architect, I need data storage that..."
        },
        "ai_system": {
            "core_team": ["ai-solution-architect", "prompt-engineer", "ai-test-engineer"],
            "first_question": "ai-solution-architect, I need an AI system for [PROJECT] that provides [CAPABILITY]. What approach works?",
            "handoff_pattern": "Following ai-solution-architect's [APPROACH], prompt-engineer, I need prompts that..."
        },
        "data_platform": {
            "core_team": ["data-architect", "database-architect", "performance-engineer"],
            "first_question": "data-architect, I need to process data for [PROJECT] with [REQUIREMENTS]. What pipeline patterns work?",
            "handoff_pattern": "Based on data-architect's [PIPELINE_DESIGN], database-architect, I need storage that..."
        },
        "mobile_app": {
            "core_team": ["mobile-architect", "ux-ui-architect", "performance-engineer"],
            "first_question": "mobile-architect, I need a mobile app for [PROJECT] supporting [PLATFORMS]. What framework works?",
            "handoff_pattern": "Following mobile-architect's [FRAMEWORK_CHOICE], ux-ui-architect, I need interfaces that..."
        },
        "api_service": {
            "core_team": ["api-architect", "database-architect", "security-specialist"],
            "first_question": "api-architect, I need an API for [PROJECT] serving [DATA_TYPES]. What design patterns work?",
            "handoff_pattern": "Based on api-architect's [API_DESIGN], database-architect, I need data models that..."
        }
    }
    
    formation_type = get_team_formation(project_description)
    formation = formations[formation_type]
    
    # Customize the question with actual project
    first_question = formation["first_question"].replace("[PROJECT]", project_description)
    handoff = formation["handoff_pattern"]
    
    return {
        "project": project_description,
        "formation_type": formation_type.replace('_', ' ').title(),
        "core_team": formation["core_team"],
        "your_first_question": first_question,
        "handoff_template": handoff,
        "success_pattern": "Always reference the previous agent's specific output when talking to the next agent",
        "next_steps": [
            f"Ask: {first_question}",
            f"Wait for {formation['core_team'][0]}'s response",
            f"Use their recommendation to guide {formation['core_team'][1]}",
            f"Have {formation['core_team'][2]} validate the complete approach",
            "Start building with coordinated team plan"
        ]
    }

def measure_coordination_chemistry(interaction_text):
    """Simple measurement of actual coordination behavior"""
    
    text_lower = interaction_text.lower()
    score = 0
    feedback = []
    
    # Specific agent engagement (30 points)
    agent_count = 0
    agents = ["solution-architect", "database-architect", "ux-ui-architect", 
              "ai-solution-architect", "prompt-engineer", "ai-test-engineer",
              "data-architect", "performance-engineer", "mobile-architect",
              "api-architect", "security-specialist"]
    
    for agent in agents:
        if agent in text_lower:
            agent_count += 1
    
    if agent_count >= 3:
        score += 30
        feedback.append("✅ EXCELLENT: Engaging multiple specific agents")
    elif agent_count >= 2:
        score += 20
        feedback.append("✅ GOOD: Using multiple agents")
    elif agent_count >= 1:
        score += 10
        feedback.append("✅ PROGRESS: Engaging specific agents")
    else:
        feedback.append("❌ ISSUE: No specific agent engagement")
    
    # Specific questions with context (25 points)
    if all(word in text_lower for word in ['i need', 'what']):
        score += 25
        feedback.append("✅ GOOD: Asking specific questions")
    elif 'what' in text_lower:
        score += 15
        feedback.append("✅ PROGRESS: Asking questions")
    else:
        feedback.append("❌ ISSUE: Questions too vague")
    
    # Building on previous work (25 points)
    handoff_phrases = ['based on', 'following', 'using', 'building on', 'with your']
    if any(phrase in text_lower for phrase in handoff_phrases):
        score += 25
        feedback.append("✅ EXCELLENT: Building on previous agent work")
    else:
        feedback.append("❌ ISSUE: Not connecting agent outputs")
    
    # Coordination patterns (20 points)
    if agent_count >= 3 and any(phrase in text_lower for phrase in handoff_phrases):
        score += 20
        feedback.append("✅ OUTSTANDING: True team coordination")
    elif agent_count >= 2:
        score += 10
        feedback.append("✅ GOOD: Multi-agent thinking")
    
    # Determine status and next action
    if score >= 80:
        status = "COORDINATING"
        next_action = "Perfect! Keep using this coordination pattern for complex features."
    elif score >= 60:
        status = "LEARNING" 
        next_action = "Try: 'Based on [agent]'s recommendation of [specific thing], [next-agent], I need...'"
    elif score >= 40:
        status = "IMPROVING"
        next_action = "Use format: '[agent], I need [specific capability] for [scenario]. What works?'"
    else:
        status = "STARTING"
        next_action = "Start with: 'solution-architect, I need [your project goal]. What architecture works?'"
    
    return {
        "chemistry_score": score,
        "status": status,
        "feedback": feedback,
        "next_action": next_action
    }

def main():
    """Main CLI interface"""
    
    if len(sys.argv) < 2:
        print("Fresh AI Starter - Get team coordination working TODAY")
        print()
        print("Examples:")
        print('  python fresh-ai-starter.py "I want to build a task management app"')
        print('  python fresh-ai-starter.py "I need an AI chatbot for customer service"')
        print('  python fresh-ai-starter.py track "solution-architect, I need..."')
        print()
        return
    
    if sys.argv[1] == "track":
        if len(sys.argv) < 3:
            print("Provide your coordination attempt to track:")
            print('Example: python fresh-ai-starter.py track "solution-architect, I need..."')
            return
        
        interaction = sys.argv[2]
        result = measure_coordination_chemistry(interaction)
        
        print("=== COORDINATION CHEMISTRY CHECK ===")
        print(f"Score: {result['chemistry_score']}/100")
        print(f"Status: {result['status']}")
        print()
        print("Feedback:")
        for item in result['feedback']:
            print(f"  {item}")
        print()
        print("Next Action:")
        print(f"  {result['next_action']}")
        
    else:
        # Generate coordination plan
        project = sys.argv[1]
        plan = generate_day1_coordination_plan(project)
        
        print("=== YOUR TEAM COORDINATION PLAN ===")
        print()
        print(f"Project: {plan['project']}")
        print(f"Formation: {plan['formation_type']}")
        print(f"Core Team: {', '.join(plan['core_team'])}")
        print()
        print("🎯 YOUR FIRST QUESTION:")
        print(f"   {plan['your_first_question']}")
        print()
        print("🔄 HANDOFF PATTERN:")
        print(f"   {plan['handoff_template']}")
        print()
        print("✅ SUCCESS CHECK:")
        print(f"   {plan['success_pattern']}")
        print()
        print("📋 NEXT STEPS:")
        for i, step in enumerate(plan['next_steps'], 1):
            print(f"   {i}. {step}")
        print()
        print("🧪 TEST YOUR COORDINATION:")
        print(f'   python fresh-ai-starter.py track "your actual coordination attempt"')

if __name__ == "__main__":
    main()