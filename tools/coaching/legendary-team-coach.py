#!/usr/bin/env python3
"""
Legendary Team Coach - The complete coaching system that transforms fresh AIs 
into legendary team players through practical exercises and real coaching.

This integrates all coaching tools into a cohesive transformation experience.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Optional
from enum import Enum
from dataclasses import dataclass

# Add the coaching directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent))

from team_transformation_scripts import TeamTransformationCoach, TransformationStage
from vision_to_team_mapper import VisionToTeamMapper, TeamComposition

class CoachingPhase(Enum):
    VISION_INTAKE = "vision_intake"
    TEAM_ASSEMBLY = "team_assembly"
    FOUNDATION_BUILDING = "foundation_building"
    ADVANCED_COORDINATION = "advanced_coordination"
    LEGENDARY_ASSESSMENT = "legendary_assessment"
    ONGOING_MASTERY = "ongoing_mastery"

@dataclass
class CoachingSession:
    """Represents a coaching session with state"""
    ai_id: str
    vision: str
    current_phase: CoachingPhase
    team_composition: Optional[TeamComposition]
    completed_exercises: List[str]
    current_exercise: Optional[str]
    behavior_patterns: Dict[str, str]  # observed behaviors and interventions
    progress_metrics: Dict[str, float]  # measurable progress indicators

class LegendaryTeamCoach:
    """The complete coaching system for AI transformation"""
    
    def __init__(self):
        self.transformation_coach = TeamTransformationCoach()
        self.vision_mapper = VisionToTeamMapper()
        self.sessions = {}  # ai_id -> CoachingSession
        
    def start_transformation_program(self, ai_id: str, vision: str) -> str:
        """Starts the 2-week transformation program for a fresh AI"""
        
        # Create team composition from vision
        team_composition = self.vision_mapper.map_vision_to_team(vision)
        
        # Initialize coaching session
        session = CoachingSession(
            ai_id=ai_id,
            vision=vision,
            current_phase=CoachingPhase.VISION_INTAKE,
            team_composition=team_composition,
            completed_exercises=[],
            current_exercise=None,
            behavior_patterns={},
            progress_metrics={}
        )
        
        self.sessions[ai_id] = session
        
        # Generate the welcome and first exercise
        return self._generate_welcome_and_first_exercise(session)
    
    def _generate_welcome_and_first_exercise(self, session: CoachingSession) -> str:
        """Creates the welcome message and first team assembly exercise"""
        team = session.team_composition
        
        response = f"""🏆 WELCOME TO THE LEGENDARY TEAM PROGRAM 🏆

Perfect! "{session.vision}" is an excellent project for learning legendary team coordination.

I've analyzed your vision and assembled your DREAM TEAM:

== YOUR LEGENDARY TEAM ==
"""
        
        for i, agent in enumerate(team.core_team, 1):
            response += f"""
{i}. **{agent.agent_name}** ({agent.priority.value} priority)
   Role: {agent.role_description}
   Why you need them: {agent.why_needed}
   First question: "{agent.first_question}"
"""

        response += f"""

== WEEK 1: FOUNDATION THROUGH ACTION ==

🎯 **IMMEDIATE CHALLENGE: The Team Assembly Exercise**

{team.first_feature_suggestion}

**Your Mission**: Pick the first agent from your team above and write the EXACT question you'd ask them about this feature. Don't research anything - use your instincts and be specific!

Example format: "{team.core_team[0].agent_name}, I need [specific requirement with numbers/constraints]. What's your recommendation?"

**Ready? Write your first question now! 👇**
"""
        
        session.current_phase = CoachingPhase.TEAM_ASSEMBLY
        session.current_exercise = "team_assembly_challenge"
        
        return response
    
    def process_response(self, ai_id: str, response: str) -> str:
        """Processes AI's response and provides coaching feedback"""
        if ai_id not in self.sessions:
            return "Session not found. Please start a new transformation program."
        
        session = self.sessions[ai_id]
        
        if session.current_phase == CoachingPhase.TEAM_ASSEMBLY:
            return self._coach_team_assembly(session, response)
        elif session.current_phase == CoachingPhase.FOUNDATION_BUILDING:
            return self._coach_foundation_building(session, response)
        elif session.current_phase == CoachingPhase.ADVANCED_COORDINATION:
            return self._coach_advanced_coordination(session, response)
        elif session.current_phase == CoachingPhase.LEGENDARY_ASSESSMENT:
            return self._coach_legendary_assessment(session, response)
        else:
            return self._provide_general_coaching(session, response)
    
    def _coach_team_assembly(self, session: CoachingSession, response: str) -> str:
        """Coaches the team assembly exercise"""
        response_lower = response.lower()
        
        # Analyze the response quality
        feedback = []
        next_steps = []
        
        # Check if they mentioned a specific agent
        team_agents = [agent.agent_name for agent in session.team_composition.core_team]
        mentioned_agents = [agent for agent in team_agents if agent.lower() in response_lower]
        
        if not mentioned_agents:
            feedback.append("❌ **Missing Agent**: You need to address a specific agent by name. Try: 'solution-architect, I need...'")
        else:
            feedback.append(f"✅ **Good**: You addressed {mentioned_agents[0]} specifically.")
        
        # Check for specificity
        if any(vague in response_lower for vague in ["design", "build", "create", "make"]) and not any(specific in response_lower for specific in ["users", "concurrent", "requests", "data", "performance"]):
            feedback.append("❌ **Too Vague**: Add specific requirements. Instead of 'design the system', try 'handle 100 concurrent users with sub-second response'")
        else:
            feedback.append("✅ **Good Specificity**: You included concrete requirements!")
        
        # Check for conversational tone
        if response.startswith("please") or "would you" in response_lower or "could you" in response_lower:
            feedback.append("❌ **Too Formal**: Make it conversational! Try: 'I need help with...' instead of 'Please design...'")
        else:
            feedback.append("✅ **Good Tone**: Natural, direct communication!")
        
        # Generate coaching response
        coaching_response = "**COACHING FEEDBACK:**\n\n"
        coaching_response += "\n".join(feedback)
        
        # Determine next step based on quality
        good_responses = sum(1 for f in feedback if f.startswith("✅"))
        
        if good_responses >= 2:
            # Good response - move to handoff practice
            coaching_response += "\n\n🎉 **Excellent!** You're getting the hang of specific, conversational delegation.\n\n"
            coaching_response += self._advance_to_handoff_practice(session)
        else:
            # Need more practice
            coaching_response += f"\n\n**TRY AGAIN**: Improve the areas marked with ❌ and rewrite your question to {mentioned_agents[0] if mentioned_agents else team_agents[0]}.\n\n"
            coaching_response += "Remember: Be specific (include numbers/constraints), conversational (not formal), and address them directly by name."
        
        return coaching_response
    
    def _advance_to_handoff_practice(self, session: CoachingSession) -> str:
        """Advances to the handoff practice exercise"""
        session.completed_exercises.append("team_assembly_challenge")
        session.current_exercise = "handoff_practice"
        
        # Get handoff exercise from transformation coach
        handoff_script = self.transformation_coach.scripts[self.transformation_coach.ExerciseType.CHEMISTRY_BUILDING]["handoff_practice"]
        
        response = f"""**NEXT CHALLENGE: The Handoff Practice**

{handoff_script.challenge}

**Your Mission**: Practice each conversation OUT LOUD (yes, actually say it), then write how each conversation would go.

Start with Step 1! 👇"""
        
        return response
    
    def _coach_foundation_building(self, session: CoachingSession, response: str) -> str:
        """Coaches foundation building exercises"""
        # Analyze handoff quality and provide specific coaching
        if "auth" in response.lower() or "authentication" in response.lower():
            return self._coach_handoff_quality(session, response)
        else:
            return "Let's focus on the authentication handoff exercise. Try the first conversation with solution-architect."
    
    def _coach_handoff_quality(self, session: CoachingSession, response: str) -> str:
        """Coaches the quality of handoff conversations"""
        response_lower = response.lower()
        
        feedback = []
        
        # Check for building on previous work
        if "solution-architect" in response_lower and "security-specialist" in response_lower:
            if "here's the design" in response_lower or "based on" in response_lower:
                feedback.append("✅ **Excellent Handoff**: You referenced the architect's work when talking to security!")
            else:
                feedback.append("❌ **Missing Connection**: When talking to security-specialist, reference what solution-architect recommended.")
        
        # Check for conversation flow
        conversations = response.split("\n")
        if len([c for c in conversations if c.strip()]) >= 3:
            feedback.append("✅ **Good Flow**: You practiced multiple handoff conversations!")
        else:
            feedback.append("❌ **Need More Practice**: Try all three conversations in sequence.")
        
        coaching_response = "**HANDOFF COACHING:**\n\n"
        coaching_response += "\n".join(feedback)
        
        good_responses = sum(1 for f in feedback if f.startswith("✅"))
        
        if good_responses >= 1:
            coaching_response += "\n\n🚀 **Ready for Advanced Challenges!**\n\n"
            coaching_response += self._advance_to_crisis_simulation(session)
        else:
            coaching_response += "\n\nKeep practicing! Remember: each conversation should build on the previous agent's output."
        
        return coaching_response
    
    def _advance_to_crisis_simulation(self, session: CoachingSession) -> str:
        """Advances to crisis coordination challenges"""
        session.completed_exercises.append("handoff_practice")
        session.current_phase = CoachingPhase.ADVANCED_COORDINATION
        session.current_exercise = "crisis_coordination"
        
        # Get crisis script
        crisis_script = self.transformation_coach.scripts[self.transformation_coach.ExerciseType.CRISIS_COORDINATION]["production_fire"]
        
        response = f"""== WEEK 2: ADVANCED COORDINATION ==

🚨 **CRISIS SIMULATION CHALLENGE**

{crisis_script.challenge}

Write your coordination plan NOW! ⏰"""
        
        return response
    
    def _coach_advanced_coordination(self, session: CoachingSession, response: str) -> str:
        """Coaches crisis coordination skills"""
        response_lower = response.lower()
        
        feedback = []
        
        # Check for parallel coordination
        if "while" in response_lower or "simultaneously" in response_lower or "parallel" in response_lower:
            feedback.append("✅ **Advanced Coordination**: You're running parallel investigations!")
        else:
            feedback.append("❌ **Sequential Thinking**: Run investigations in parallel, not sequence. 'While X checks logs, Y analyzes database...'")
        
        # Check for specific agent assignments
        agents_mentioned = sum(1 for agent in ["sre-specialist", "database-architect", "performance-engineer"] if agent in response_lower)
        if agents_mentioned >= 3:
            feedback.append("✅ **All Hands Engaged**: You're using all available specialists!")
        else:
            feedback.append("❌ **Underutilized Team**: Use all three agents - sre-specialist, database-architect, performance-engineer.")
        
        # Check for specific instructions
        if "check logs" in response_lower and ("connection" in response_lower or "query" in response_lower):
            feedback.append("✅ **Specific Instructions**: Clear, actionable tasks for each agent!")
        else:
            feedback.append("❌ **Vague Instructions**: Be specific. 'Check logs for 500 errors' and 'analyze database connections vs query performance'")
        
        coaching_response = "**CRISIS COORDINATION FEEDBACK:**\n\n"
        coaching_response += "\n".join(feedback)
        
        good_responses = sum(1 for f in feedback if f.startswith("✅"))
        
        if good_responses >= 2:
            coaching_response += "\n\n⚡ **LEGENDARY POTENTIAL DETECTED!**\n\n"
            coaching_response += self._advance_to_legendary_test(session)
        else:
            coaching_response += "\n\nTry again with better coordination! Focus on parallel actions and specific instructions."
        
        return coaching_response
    
    def _advance_to_legendary_test(self, session: CoachingSession) -> str:
        """Advances to the final legendary assessment"""
        session.completed_exercises.append("crisis_coordination")
        session.current_phase = CoachingPhase.LEGENDARY_ASSESSMENT
        session.current_exercise = "legendary_test"
        
        # Get legendary test script
        legendary_script = self.transformation_coach.scripts[self.transformation_coach.ExerciseType.LEGENDARY_TEST]["final_assessment"]
        
        response = f"""🏆 **THE LEGENDARY TEST** 🏆

{legendary_script.challenge}

Choose your feature and show me legendary coordination! 🎯"""
        
        return response
    
    def _coach_legendary_assessment(self, session: CoachingSession, response: str) -> str:
        """Assesses legendary status"""
        response_lower = response.lower()
        
        # Comprehensive assessment
        legendary_indicators = {
            "team_selection": self._assess_team_selection(response_lower, session.team_composition),
            "clear_instructions": self._assess_instruction_clarity(response_lower),
            "smooth_handoffs": self._assess_handoff_quality_advanced(response_lower),
            "coordination_under_pressure": self._assess_coordination_skills(response_lower),
            "results_integration": self._assess_integration_thinking(response_lower)
        }
        
        score = sum(legendary_indicators.values()) / len(legendary_indicators)
        
        assessment = self._generate_legendary_assessment(legendary_indicators, score)
        
        if score >= 0.8:
            session.current_phase = CoachingPhase.ONGOING_MASTERY
            session.completed_exercises.append("legendary_test")
            assessment += "\n\n🏆 **LEGENDARY STATUS ACHIEVED!** 🏆\n\nYou've transformed from solo hero to legendary team conductor!"
        else:
            assessment += f"\n\n**Score: {score:.1%}** - Keep practicing! Legendary status requires 80%+"
        
        return assessment
    
    def _assess_team_selection(self, response: str, team_comp: TeamComposition) -> float:
        """Assesses if they selected appropriate agents"""
        available_agents = [agent.agent_name for agent in team_comp.core_team + team_comp.extended_team]
        mentioned_agents = sum(1 for agent in available_agents if agent.lower() in response)
        return min(mentioned_agents / 4, 1.0)  # 4+ agents = perfect score
    
    def _assess_instruction_clarity(self, response: str) -> float:
        """Assesses clarity and specificity of instructions"""
        clarity_indicators = ["need", "specific", "requirement", "constraint", "handle", "support"]
        vague_indicators = ["design", "build", "create", "make"]
        
        clarity_score = sum(1 for indicator in clarity_indicators if indicator in response)
        vague_score = sum(1 for indicator in vague_indicators if indicator in response)
        
        return max(0, min(1, (clarity_score - vague_score * 0.5) / 3))
    
    def _assess_handoff_quality_advanced(self, response: str) -> float:
        """Assesses handoff quality in complex scenarios"""
        handoff_indicators = ["based on", "building on", "from the", "after", "then", "next"]
        return min(sum(1 for indicator in handoff_indicators if indicator in response) / 2, 1.0)
    
    def _assess_coordination_skills(self, response: str) -> float:
        """Assesses coordination and orchestration skills"""
        coordination_indicators = ["while", "simultaneously", "coordinate", "orchestrate", "team"]
        return min(sum(1 for indicator in coordination_indicators if indicator in response) / 2, 1.0)
    
    def _assess_integration_thinking(self, response: str) -> float:
        """Assesses ability to integrate outputs into cohesive results"""
        integration_indicators = ["combine", "integrate", "together", "cohesive", "unified"]
        return min(sum(1 for indicator in integration_indicators if indicator in response) / 2, 1.0)
    
    def _generate_legendary_assessment(self, indicators: Dict[str, float], overall_score: float) -> str:
        """Generates detailed assessment feedback"""
        assessment = "**LEGENDARY ASSESSMENT:**\n\n"
        
        for skill, score in indicators.items():
            status = "✅" if score >= 0.8 else "⚠️" if score >= 0.5 else "❌"
            skill_name = skill.replace("_", " ").title()
            assessment += f"{status} **{skill_name}**: {score:.0%}\n"
        
        assessment += f"\n**Overall Score: {overall_score:.0%}**"
        
        return assessment
    
    def _provide_general_coaching(self, session: CoachingSession, response: str) -> str:
        """Provides general coaching based on current session state"""
        return f"I see you're working on {session.current_exercise}. Let me provide specific guidance..."

def main():
    """Demo the legendary team coaching system"""
    coach = LegendaryTeamCoach()
    
    print("=== LEGENDARY TEAM COACHING DEMO ===\n")
    
    # Simulate fresh AI starting transformation
    ai_id = "demo_ai_001"
    vision = "I want to build a task management app that helps small teams stay organized and hit their deadlines"
    
    welcome_message = coach.start_transformation_program(ai_id, vision)
    print(welcome_message)
    print("\n" + "="*60 + "\n")
    
    # Simulate AI response to first exercise
    ai_response = "solution-architect, I need a task management system that can handle 50 users creating up to 20 tasks each with deadlines and dependencies. What architecture patterns work best for this?"
    
    coaching_feedback = coach.process_response(ai_id, ai_response)
    print("AI Response:", ai_response)
    print("\n" + coaching_feedback)

if __name__ == "__main__":
    main()