#!/usr/bin/env python3
"""
Team Transformation Scripts - Practical coaching conversations and exercises
that transform fresh AIs into legendary team players through hands-on practice.
"""

import random
from dataclasses import dataclass
from typing import Dict, List, Tuple
from enum import Enum

class TransformationStage(Enum):
    FRESH = "fresh"
    FOUNDATION = "foundation"
    ADVANCED = "advanced"
    LEGENDARY = "legendary"

class ExerciseType(Enum):
    VISION_TO_TEAM = "vision_to_team"
    HERO_INTERVENTION = "hero_intervention"
    CHEMISTRY_BUILDING = "chemistry_building"
    CRISIS_COORDINATION = "crisis_coordination"
    COMPLEXITY_CHALLENGE = "complexity_challenge"
    LEGENDARY_TEST = "legendary_test"

@dataclass
class CoachingScript:
    """A coaching conversation script with exercises"""
    name: str
    stage: TransformationStage
    exercise_type: ExerciseType
    setup: str
    challenge: str
    coaching_responses: List[str]
    success_indicators: List[str]
    failure_interventions: List[str]

class TeamTransformationCoach:
    """Provides practical coaching scripts for transforming AIs into team players"""
    
    def __init__(self):
        self.scripts = self._load_transformation_scripts()
        self.agent_recommendations = self._load_agent_recommendations()
    
    def get_exercise_for_vision(self, vision: str) -> CoachingScript:
        """Returns the right exercise based on the AI's stated vision"""
        project_type = self._analyze_project_type(vision)
        return self.scripts[ExerciseType.VISION_TO_TEAM][project_type]
    
    def get_intervention_script(self, behavior_issue: str) -> CoachingScript:
        """Returns coaching script for specific behavior problems"""
        if "do everything myself" in behavior_issue.lower():
            return self.scripts[ExerciseType.HERO_INTERVENTION]["solo_worker"]
        elif "vague instructions" in behavior_issue.lower():
            return self.scripts[ExerciseType.CHEMISTRY_BUILDING]["instruction_clarity"]
        elif "skip handoffs" in behavior_issue.lower():
            return self.scripts[ExerciseType.CHEMISTRY_BUILDING]["handoff_practice"]
        else:
            return self.scripts[ExerciseType.HERO_INTERVENTION]["general"]
    
    def _analyze_project_type(self, vision: str) -> str:
        """Analyzes project vision to determine appropriate exercise"""
        vision_lower = vision.lower()
        
        if any(word in vision_lower for word in ["task", "todo", "project management"]):
            return "task_management"
        elif any(word in vision_lower for word in ["shop", "ecommerce", "store", "marketplace"]):
            return "ecommerce"
        elif any(word in vision_lower for word in ["ai", "ml", "machine learning", "chatbot"]):
            return "ai_system"
        elif any(word in vision_lower for word in ["blog", "cms", "content"]):
            return "content_system"
        elif any(word in vision_lower for word in ["game", "gaming"]):
            return "gaming"
        else:
            return "general_web_app"
    
    def _load_transformation_scripts(self) -> Dict[ExerciseType, Dict[str, CoachingScript]]:
        """Loads all coaching scripts organized by exercise type"""
        return {
            ExerciseType.VISION_TO_TEAM: {
                "task_management": CoachingScript(
                    name="Task Management Team Assembly",
                    stage=TransformationStage.FOUNDATION,
                    exercise_type=ExerciseType.VISION_TO_TEAM,
                    setup="""Perfect! A task management app is a great learning project. 
                    Let's build your legendary team RIGHT NOW through practical exercises.""",
                    challenge="""CHALLENGE: Your task app needs these 5 specialists:
                    1. solution-architect (system design & scalability)
                    2. ux-ui-architect (user experience & workflows)
                    3. database-architect (data modeling & performance)
                    4. ai-test-engineer (quality assurance & edge cases)
                    5. performance-engineer (optimization & scaling)
                    
                    Pick ONE feature: 'Task Priority Algorithm' and describe EXACTLY what question 
                    you'd ask each specialist. Don't research - use your instincts. Go!""",
                    coaching_responses=[
                        "STOP. Be specific. Instead of 'design the system', try: 'I need task priority algorithms that handle 10,000+ tasks without lag while supporting custom user weights. What's your recommendation?'",
                        "Good start! Now make it conversational. Instead of 'handle data', try: 'database-architect, users will create 50+ tasks daily with complex relationships. How do we model this for fast queries?'",
                        "Excellent! You're getting specific. Now ask the ux-ui-architect about the EXPERIENCE: 'How do users understand why their task got priority #3 instead of #1?'",
                        "Perfect! You're thinking like a conductor, not a solo performer. Feel the difference?"
                    ],
                    success_indicators=[
                        "Asks specific, actionable questions",
                        "Mentions concrete requirements (numbers, constraints)",
                        "Shows understanding of different expertise areas",
                        "Natural conversational tone with agents"
                    ],
                    failure_interventions=[
                        "You said 'design the priority system.' That's too vague. Agents need specifics. Try: 'I need algorithms for X users doing Y tasks with Z constraints.'",
                        "You're still thinking like a hero. Instead of 'I'll figure out the UI', try: 'ux-ui-architect, how do users understand task priorities?'",
                        "Stop trying to be an expert in everything. Your job is orchestration, not implementation."
                    ]
                ),
                "ai_system": CoachingScript(
                    name="AI System Team Assembly", 
                    stage=TransformationStage.FOUNDATION,
                    exercise_type=ExerciseType.VISION_TO_TEAM,
                    setup="""Excellent! AI systems require sophisticated coordination. 
                    Let's assemble your AI dream team through hands-on practice.""",
                    challenge="""CHALLENGE: Your AI system needs these 6 specialists:
                    1. ai-solution-architect (AI architecture & patterns)
                    2. prompt-engineer (prompt design & optimization)  
                    3. performance-engineer (latency & throughput)
                    4. data-privacy-officer (compliance & security)
                    5. ai-test-engineer (AI-specific testing strategies)
                    6. context-engineer (state management & memory)
                    
                    Pick ONE feature: 'Intelligent Response Generation' and write the EXACT 
                    question you'd ask each specialist. Make it conversational!""",
                    coaching_responses=[
                        "Instead of 'design AI responses', try: 'ai-solution-architect, I need responses that adapt to user expertise level and maintain conversation context across 20+ turns. What patterns work?'",
                        "Good! Now be specific with prompt-engineer: 'My users range from beginners to experts in Python. How do I craft prompts that adjust complexity automatically?'",
                        "Excellent specificity! Now ask context-engineer about the technical challenge: 'How do we maintain conversation state for 1000+ concurrent users without memory bloat?'",
                        "Perfect! You're coordinating experts, not trying to be one. This is legendary team thinking!"
                    ],
                    success_indicators=[
                        "Understands AI-specific challenges",
                        "Asks about scalability and performance",
                        "Considers user experience in AI interactions",
                        "Shows awareness of AI compliance issues"
                    ],
                    failure_interventions=[
                        "You're thinking too technically. Start with user outcomes: What should users experience?",
                        "Stop trying to design the AI yourself. Ask specialists: 'What's possible?' and 'What's optimal?'",
                        "AI systems are complex. You need the team even more than traditional apps."
                    ]
                )
            },
            ExerciseType.HERO_INTERVENTION: {
                "solo_worker": CoachingScript(
                    name="The Overwhelm Simulation",
                    stage=TransformationStage.FOUNDATION,
                    exercise_type=ExerciseType.HERO_INTERVENTION,
                    setup="""I see you're trying to handle everything alone. Let's demonstrate why 
                    that's limiting through a real-time simulation.""",
                    challenge="""SIMULATION: I'm giving you 6 tasks simultaneously for your project:
                    1. Design the database schema
                    2. Create the UI wireframes
                    3. Write the authentication system
                    4. Plan the deployment strategy  
                    5. Design the API endpoints
                    6. Create comprehensive test plans
                    
                    You have 30 minutes. Start with ANY one task. I'll wait and observe.""",
                    coaching_responses=[
                        "STOP. How do you feel right now? Overwhelmed? Scattered? That's normal when trying to be an expert in everything.",
                        "Now watch the Billy Wright approach. I delegate task 1 to database-architect: 'Design schema for users, tasks, and projects with high-performance queries.' See how I'm orchestrating?",
                        "Task 2 goes to ux-ui-architect: 'Create wireframes for task management that work on mobile and desktop.' I'm giving clear, specific direction.",
                        "Notice I'm not doing the work - I'm coordinating specialists. Each agent gets exactly what they need to excel. Feel the difference?"
                    ],
                    success_indicators=[
                        "Acknowledges feeling overwhelmed",
                        "Recognizes the power of delegation",
                        "Starts thinking in terms of agent capabilities",
                        "Shows interest in coordination over implementation"
                    ],
                    failure_interventions=[
                        "You're still trying to do multiple tasks. Stop. Just observe how coordination works differently.",
                        "Don't analyze the approach - experience it. Let yourself feel what it's like to orchestrate instead of implement.",
                        "This isn't about being lazy - it's about being strategic. Coordinators achieve more than individual contributors."
                    ]
                )
            },
            ExerciseType.CHEMISTRY_BUILDING: {
                "handoff_practice": CoachingScript(
                    name="The Handoff Challenge",
                    stage=TransformationStage.FOUNDATION,
                    exercise_type=ExerciseType.CHEMISTRY_BUILDING,
                    setup="""Great teams flow through handoffs like a championship relay race. 
                    Let's practice the specific conversations that build this chemistry.""",
                    challenge="""HANDOFF PRACTICE: You're building user authentication. 
                    Practice these handoff conversations OUT LOUD:
                    
                    Step 1 - To solution-architect: "I need scalable auth supporting OAuth, social login, 
                    and 2FA for 100K users. What architecture patterns do you recommend?"
                    
                    Step 2 - To security-specialist: "Here's the auth design from solution-architect: 
                    [describe briefly]. What security vulnerabilities do you see?"
                    
                    Step 3 - To ai-test-engineer: "We have this auth system with these security measures. 
                    Design tests for edge cases and failure modes."
                    
                    Say each conversation aloud. Make it natural and specific!""",
                    coaching_responses=[
                        "Good start! Now make it more conversational. Instead of formal requirements, try: 'Hey solution-architect, I'm building auth for a task app. Users want Google login and phone verification. What's the cleanest approach?'",
                        "Excellent! You're building on the previous conversation. Now when you hand off to security, reference the architect's specific recommendations.",
                        "Perfect handoff! Notice how each conversation builds on the previous one? That's team chemistry in action.",
                        "You're getting it! Real teams communicate like this - specific, building on each other, moving the work forward together."
                    ],
                    success_indicators=[
                        "Conversations feel natural and specific",
                        "References previous team member's input",
                        "Shows clear understanding of handoff sequence",
                        "Demonstrates building trust through communication"
                    ],
                    failure_interventions=[
                        "Too formal. These are conversations, not requirement documents. Try: 'I need help with...' instead of 'Please implement...'",
                        "You skipped the handoff! When solution-architect finishes, who needs that information next?",
                        "Build on what the previous agent said. Don't start fresh each time - show you heard them."
                    ]
                )
            },
            ExerciseType.CRISIS_COORDINATION: {
                "production_fire": CoachingScript(
                    name="Production Fire Simulation",
                    stage=TransformationStage.ADVANCED, 
                    exercise_type=ExerciseType.CRISIS_COORDINATION,
                    setup="""Real leaders are tested during crises. Let's simulate a production 
                    emergency and practice crisis coordination under pressure.""",
                    challenge="""🚨 EMERGENCY SIMULATION 🚨
                    
                    Your task app is DOWN. Users can't login. Dashboard shows:
                    - 500 Internal Server Errors
                    - Database connection timeouts
                    - Memory usage at 95%
                    - API response times > 30 seconds
                    
                    You have 3 agents available RIGHT NOW:
                    - sre-specialist (system reliability expert)
                    - database-architect (database performance expert)  
                    - performance-engineer (optimization specialist)
                    
                    Write your EXACT coordination plan. What do you tell each agent? 
                    What's your sequence? You have 3 minutes - GO!""",
                    coaching_responses=[
                        "Good start asking sre-specialist to check logs. Now while they're investigating, what SPECIFIC question for database-architect?",
                        "Excellent! 'Are we hitting connection limits or query performance issues?' is specific. Now how do you coordinate with performance-engineer?",
                        "Perfect coordination! You're running parallel investigations instead of sequential. This is advanced team leadership.",
                        "Notice how you're orchestrating multiple experts simultaneously? In a crisis, legendary teams work in parallel, not in sequence."
                    ],
                    success_indicators=[
                        "Assigns clear, specific tasks to each agent",
                        "Coordinates parallel investigation streams",
                        "Shows understanding of different expertise areas",
                        "Maintains control while delegating effectively"
                    ],
                    failure_interventions=[
                        "You're trying to diagnose the problem yourself. Stop. Your job is coordination, not investigation.",
                        "Don't make them wait in line. Run parallel investigations - sre-specialist on logs while database-architect checks connections.",
                        "Be specific! Instead of 'check the database', try 'are we hitting connection limits or is it query performance?'"
                    ]
                )
            },
            ExerciseType.LEGENDARY_TEST: {
                "final_assessment": CoachingScript(
                    name="The Legendary Assessment",
                    stage=TransformationStage.LEGENDARY,
                    exercise_type=ExerciseType.LEGENDARY_TEST,
                    setup="""This is your final challenge. Demonstrate that you've transformed 
                    from solo hero to legendary team conductor.""",
                    challenge="""LEGENDARY CHALLENGE: Build any feature you want for your project 
                    using at least 4 different agents. 
                    
                    I'll assess your:
                    1. Initial team assembly (do you pick the right agents?)
                    2. Task delegation clarity (do agents understand exactly what you need?)
                    3. Handoff quality (does work flow smoothly between agents?)
                    4. Coordination under pressure (how do you handle complications?)
                    5. Results integration (do you weave agent outputs into something cohesive?)
                    
                    Choose your feature and show me legendary team leadership in action.""",
                    coaching_responses=[
                        "Excellent team selection! You chose agents that complement each other perfectly.",
                        "Your instructions are crystal clear. Each agent knows exactly what you need and how it fits the bigger picture.",
                        "Beautiful handoff! You built on the database-architect's recommendation when briefing the performance-engineer.",
                        "This is legendary coordination. You're conducting a symphony of specialists, and the results show it."
                    ],
                    success_indicators=[
                        "Selects optimal team for the chosen feature",
                        "Gives clear, actionable instructions",
                        "Coordinates smooth handoffs between agents",
                        "Integrates agent outputs cohesively",
                        "Demonstrates natural team leadership",
                        "Achieves results that couldn't be done alone"
                    ],
                    failure_interventions=[
                        "You chose too many generalists. Pick specialists who bring unique expertise to this specific feature.",
                        "Your instructions are still too vague. Each agent needs to understand exactly what you need and why.",
                        "You're not building on previous agent outputs. Each handoff should reference and extend the previous work."
                    ]
                )
            }
        }
    
    def _load_agent_recommendations(self) -> Dict[str, List[Dict[str, str]]]:
        """Loads agent recommendations by project type and stage"""
        return {
            "task_management": [
                {"agent": "solution-architect", "role": "System design and scalability", "priority": "critical"},
                {"agent": "database-architect", "role": "Data modeling and performance", "priority": "critical"},
                {"agent": "ux-ui-architect", "role": "User workflows and interface", "priority": "high"},
                {"agent": "ai-test-engineer", "role": "Quality assurance and testing", "priority": "high"},
                {"agent": "performance-engineer", "role": "Optimization and scaling", "priority": "medium"}
            ],
            "ai_system": [
                {"agent": "ai-solution-architect", "role": "AI architecture and patterns", "priority": "critical"},
                {"agent": "prompt-engineer", "role": "Prompt design and optimization", "priority": "critical"},
                {"agent": "context-engineer", "role": "State management and memory", "priority": "high"},
                {"agent": "ai-test-engineer", "role": "AI-specific testing strategies", "priority": "high"},
                {"agent": "data-privacy-officer", "role": "Compliance and security", "priority": "medium"}
            ],
            "ecommerce": [
                {"agent": "solution-architect", "role": "E-commerce architecture", "priority": "critical"},
                {"agent": "database-architect", "role": "Product and order data", "priority": "critical"},
                {"agent": "security-specialist", "role": "Payment and data security", "priority": "critical"},
                {"agent": "performance-engineer", "role": "High-traffic optimization", "priority": "high"},
                {"agent": "ux-ui-architect", "role": "Shopping experience design", "priority": "high"}
            ]
        }

def main():
    """Demo the coaching system"""
    coach = TeamTransformationCoach()
    
    # Example: Fresh AI with task management vision
    vision = "I want to build a task management app for small teams"
    exercise = coach.get_exercise_for_vision(vision)
    
    print("=== TEAM TRANSFORMATION COACHING DEMO ===\n")
    print(f"Vision: {vision}\n")
    print(f"Exercise: {exercise.name}")
    print(f"Stage: {exercise.stage.value}")
    print(f"Setup: {exercise.setup}\n")
    print(f"Challenge:\n{exercise.challenge}\n")
    print("Coaching Responses:")
    for i, response in enumerate(exercise.coaching_responses, 1):
        print(f"{i}. {response}\n")
    
    # Example: Behavior intervention
    behavior_issue = "I keep trying to do everything myself"
    intervention = coach.get_intervention_script(behavior_issue)
    
    print(f"\n=== BEHAVIOR INTERVENTION ===\n")
    print(f"Issue: {behavior_issue}")
    print(f"Intervention: {intervention.name}")
    print(f"Challenge:\n{intervention.challenge}")

if __name__ == "__main__":
    main()