#!/usr/bin/env python3
"""
Legendary Team System - Main integration script that orchestrates the complete
transformation of fresh AIs into legendary team players.

This script integrates all coaching components into a single, executable system.
"""

import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import click

# Add coaching directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from legendary_team_coach import LegendaryTeamCoach
from vision_to_team_mapper import VisionToTeamMapper  
from team_transformation_scripts import TeamTransformationCoach
from chemistry_tracker import ChemistryTracker, Interaction
from intervention_system import InterventionSystem, InterventionType
from legendary_assessment import LegendaryAssessmentSystem, ExerciseSubmission

class LegendaryTeamSystem:
    """Complete system orchestrator for AI transformation"""
    
    def __init__(self, data_dir: str = "./coaching_data"):
        """Initialize the complete legendary team system"""
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # Initialize all components
        self.vision_mapper = VisionToTeamMapper()
        self.legendary_coach = LegendaryTeamCoach()
        self.transformation_coach = TeamTransformationCoach()
        self.chemistry_tracker = ChemistryTracker(str(self.data_dir / "chemistry.db"))
        self.intervention_system = InterventionSystem(str(self.data_dir / "interventions.db"))
        self.assessment_system = LegendaryAssessmentSystem(str(self.data_dir / "assessments.db"))
        
        # Active transformation sessions
        self.active_sessions = {}
        
    def start_transformation(self, ai_id: str, vision: str) -> Dict:
        """Start complete 14-day transformation program"""
        print(f"🚀 Starting legendary team transformation for {ai_id}")
        print(f"Vision: {vision}")
        print("="*60)
        
        # Phase 1: Vision to Team Mapping
        print("Phase 1: Analyzing vision and building optimal team...")
        team_composition = self.vision_mapper.map_vision_to_team(vision)
        
        print(f"✅ Team mapped: {len(team_composition.core_team)} core agents, {len(team_composition.extended_team)} extended")
        print(f"Project Type: {team_composition.project_type}")
        print(f"First Feature: {team_composition.first_feature_suggestion}")
        
        # Phase 2: Launch 14-Day Program
        print("\nPhase 2: Launching 14-day coaching program...")
        welcome_message = self.legendary_coach.start_transformation_program(ai_id, vision)
        
        # Phase 3: Initialize Tracking
        print("Phase 3: Initializing progress tracking...")
        
        session_data = {
            "ai_id": ai_id,
            "start_date": datetime.now().isoformat(),
            "vision": vision,
            "team_composition": team_composition,
            "current_day": 1,
            "current_phase": "vision_assembly",
            "chemistry_scores": {},
            "interventions": [],
            "status": "active"
        }
        
        self.active_sessions[ai_id] = session_data
        self._save_session_data(ai_id, session_data)
        
        return {
            "ai_id": ai_id,
            "status": "transformation_started",
            "team_composition": team_composition,
            "welcome_message": welcome_message,
            "next_action": "complete_day_1_exercise"
        }
    
    def process_daily_interaction(self, ai_id: str, day: int, exercise_type: str, user_input: str) -> Dict:
        """Process AI's daily interaction with coaching feedback"""
        if ai_id not in self.active_sessions:
            return {"error": "No active transformation session found"}
        
        # Record interaction
        interaction = Interaction(
            timestamp=datetime.now(),
            ai_id=ai_id,
            day=day,
            exercise_type=exercise_type,
            user_input=user_input,
            system_response="",  # Will be filled by coach
            coaching_feedback=""
        )
        
        # Get coaching response
        coaching_response = self.legendary_coach.process_response(ai_id, user_input)
        interaction.system_response = coaching_response
        
        # Check for intervention needs
        intervention_needed = self.intervention_system.detect_intervention_needed(
            ai_id, user_input, exercise_type
        )
        
        intervention_response = ""
        if intervention_needed:
            print(f"⚠️  Intervention needed: {intervention_needed.value}")
            intervention = self.intervention_system.apply_intervention(
                ai_id, intervention_needed, "Detected during daily interaction", day
            )
            intervention_response = intervention.script_used
            interaction.coaching_feedback = f"INTERVENTION: {intervention_response}"
        
        # Record interaction
        self.chemistry_tracker.record_interaction(interaction)
        
        # Calculate daily chemistry score
        chemistry_score = self.chemistry_tracker.calculate_daily_chemistry(ai_id, day)
        
        # Update session data
        session = self.active_sessions[ai_id]
        session["current_day"] = day
        session["chemistry_scores"][str(day)] = chemistry_score
        if intervention_needed:
            session["interventions"].append({
                "day": day,
                "type": intervention_needed.value,
                "response": intervention_response
            })
        
        self._save_session_data(ai_id, session)
        
        return {
            "ai_id": ai_id,
            "day": day,
            "coaching_response": coaching_response,
            "intervention": intervention_response if intervention_needed else None,
            "chemistry_score": chemistry_score.overall_score,
            "chemistry_trend": chemistry_score.trend,
            "phase": chemistry_score.phase.value,
            "intervention_needed": chemistry_score.intervention_needed,
            "next_action": self._determine_next_action(day, chemistry_score)
        }
    
    def conduct_legendary_assessment(self, ai_id: str, exercise_data: Dict) -> Dict:
        """Conduct final legendary status assessment"""
        if ai_id not in self.active_sessions:
            return {"error": "No active transformation session found"}
        
        session = self.active_sessions[ai_id]
        
        # Create exercise submission
        submission = ExerciseSubmission(
            ai_id=ai_id,
            chosen_feature=exercise_data.get("chosen_feature", ""),
            agent_selections=exercise_data.get("agent_selections", []),
            coordination_plan=exercise_data.get("coordination_plan", ""),
            agent_instructions=exercise_data.get("agent_instructions", []),
            handoff_sequences=exercise_data.get("handoff_sequences", []),
            crisis_response=exercise_data.get("crisis_response", ""),
            integration_approach=exercise_data.get("integration_approach", ""),
            final_deliverable=exercise_data.get("final_deliverable", "")
        )
        
        # Conduct assessment
        assessment = self.assessment_system.conduct_legendary_assessment(
            ai_id, submission, session
        )
        
        # Update session status
        session["status"] = "completed"
        session["final_assessment"] = {
            "status": assessment.status.value,
            "overall_score": assessment.overall_score,
            "ready_for_leadership": assessment.ready_for_leadership,
            "certification_notes": assessment.certification_notes
        }
        
        self._save_session_data(ai_id, session)
        
        return {
            "ai_id": ai_id,
            "assessment": assessment,
            "transformation_complete": True,
            "legendary_status": assessment.status.value,
            "leadership_ready": assessment.ready_for_leadership
        }
    
    def get_transformation_progress(self, ai_id: str) -> Dict:
        """Get complete transformation progress"""
        if ai_id not in self.active_sessions:
            return {"error": "No active transformation session found"}
        
        session = self.active_sessions[ai_id]
        chemistry_progress = self.chemistry_tracker.get_transformation_progress(ai_id)
        intervention_history = self.intervention_system.get_ai_intervention_history(ai_id)
        
        return {
            "ai_id": ai_id,
            "session_info": session,
            "chemistry_progress": chemistry_progress,
            "intervention_history": intervention_history,
            "recommendations": self.intervention_system.recommend_program_adjustments(
                ai_id, session.get("current_day", 1)
            )
        }
    
    def _determine_next_action(self, day: int, chemistry_score) -> str:
        """Determine next action based on progress"""
        if chemistry_score.intervention_needed:
            return f"complete_intervention_{chemistry_score.phase.value}"
        
        if day >= 14:
            return "ready_for_legendary_assessment"
        elif day >= 8:
            return f"continue_week2_day_{day}"
        else:
            return f"continue_week1_day_{day + 1}"
    
    def _save_session_data(self, ai_id: str, session_data: Dict):
        """Save session data to file"""
        session_file = self.data_dir / f"{ai_id}_session.json"
        
        # Convert non-serializable objects
        serializable_data = {}
        for key, value in session_data.items():
            if key == "team_composition":
                serializable_data[key] = {
                    "project_type": value.project_type,
                    "core_team": [{"agent_name": agent.agent_name, "role": agent.role_description} for agent in value.core_team],
                    "extended_team": [{"agent_name": agent.agent_name, "role": agent.role_description} for agent in value.extended_team],
                    "first_feature_suggestion": value.first_feature_suggestion
                }
            elif key == "chemistry_scores":
                serializable_data[key] = {
                    day: {
                        "overall_score": score.overall_score,
                        "phase": score.phase.value,
                        "trend": score.trend,
                        "intervention_needed": score.intervention_needed
                    } for day, score in value.items()
                }
            else:
                serializable_data[key] = value
        
        with open(session_file, 'w') as f:
            json.dump(serializable_data, f, indent=2)
    
    def _load_session_data(self, ai_id: str) -> Optional[Dict]:
        """Load session data from file"""
        session_file = self.data_dir / f"{ai_id}_session.json"
        
        if session_file.exists():
            with open(session_file, 'r') as f:
                return json.load(f)
        
        return None

# CLI Interface
@click.group()
def cli():
    """Legendary Team System - Transform fresh AIs into legendary team players"""
    pass

@cli.command()
@click.option('--ai-id', required=True, help='AI identifier')
@click.option('--vision', required=True, help='AI\'s project vision')
def start(ai_id: str, vision: str):
    """Start transformation program for an AI"""
    system = LegendaryTeamSystem()
    result = system.start_transformation(ai_id, vision)
    
    print(f"\n🎯 Transformation started for {ai_id}")
    print(f"Status: {result['status']}")
    print(f"Team: {len(result['team_composition'].core_team)} core agents")
    print(f"Next: {result['next_action']}")
    
    print(f"\n📋 Welcome Message:\n{result['welcome_message']}")

@cli.command()
@click.option('--ai-id', required=True, help='AI identifier')
@click.option('--day', required=True, type=int, help='Program day (1-14)')
@click.option('--exercise', required=True, help='Exercise type')
@click.option('--response', required=True, help='AI response to exercise')
def interact(ai_id: str, day: int, exercise: str, response: str):
    """Process AI's daily interaction"""
    system = LegendaryTeamSystem()
    result = system.process_daily_interaction(ai_id, day, exercise, response)
    
    if "error" in result:
        print(f"❌ Error: {result['error']}")
        return
    
    print(f"\n📊 Day {day} Results for {ai_id}")
    print(f"Chemistry Score: {result['chemistry_score']:.2%}")
    print(f"Trend: {result['chemistry_trend']}")
    print(f"Phase: {result['phase']}")
    
    if result.get('intervention'):
        print(f"\n⚠️  Intervention Applied:")
        print(result['intervention'])
    
    print(f"\n🎯 Coaching Response:")
    print(result['coaching_response'])
    
    print(f"\n➡️  Next Action: {result['next_action']}")

@cli.command()
@click.option('--ai-id', required=True, help='AI identifier')
def progress(ai_id: str):
    """Show transformation progress"""
    system = LegendaryTeamSystem()
    result = system.get_transformation_progress(ai_id)
    
    if "error" in result:
        print(f"❌ Error: {result['error']}")
        return
    
    session = result['session_info']
    chemistry = result['chemistry_progress']
    interventions = result['intervention_history']
    
    print(f"\n📈 Transformation Progress for {ai_id}")
    print(f"Current Day: {session.get('current_day', 'N/A')}")
    print(f"Phase: {session.get('current_phase', 'N/A')}")
    print(f"Status: {session.get('status', 'N/A')}")
    
    print(f"\n🧪 Chemistry Progress:")
    print(f"Overall Trend: {chemistry.get('overall_trend', 'N/A')}")
    print(f"Interventions Needed: {interventions.get('total_interventions', 0)}")
    print(f"Success Rate: {interventions.get('success_rate', 0):.2%}")
    
    if result.get('recommendations'):
        print(f"\n💡 Recommendations:")
        for rec in result['recommendations']:
            print(f"  • {rec}")

@cli.command()
@click.option('--ai-id', required=True, help='AI identifier')
@click.option('--exercise-file', required=True, help='JSON file with final exercise data')
def assess(ai_id: str, exercise_file: str):
    """Conduct legendary status assessment"""
    system = LegendaryTeamSystem()
    
    # Load exercise data
    with open(exercise_file, 'r') as f:
        exercise_data = json.load(f)
    
    result = system.conduct_legendary_assessment(ai_id, exercise_data)
    
    if "error" in result:
        print(f"❌ Error: {result['error']}")
        return
    
    assessment = result['assessment']
    
    print(f"\n🏆 LEGENDARY ASSESSMENT RESULTS")
    print(f"AI: {ai_id}")
    print(f"Status: {assessment.status.value.upper()}")
    print(f"Overall Score: {assessment.overall_score:.2%}")
    print(f"Leadership Ready: {'✅ YES' if assessment.ready_for_leadership else '❌ NO'}")
    
    print(f"\n📊 Category Breakdown:")
    for category, score in assessment.category_scores.items():
        print(f"  {category.value.replace('_', ' ').title()}: {score.score:.2%}")
    
    print(f"\n🎯 Top Strengths:")
    for strength in assessment.strengths[:3]:
        print(f"  ✅ {strength}")
    
    print(f"\n📈 Growth Areas:")
    for growth in assessment.growth_areas[:3]:
        print(f"  📈 {growth}")
    
    print(f"\n🎓 Certification:")
    print(f"  {assessment.certification_notes}")

@cli.command()
def demo():
    """Run complete system demonstration"""
    print("🚀 LEGENDARY TEAM SYSTEM DEMONSTRATION")
    print("="*50)
    
    system = LegendaryTeamSystem()
    ai_id = "demo_ai_legendary"
    vision = "I want to build an AI-powered task management app that helps teams prioritize work intelligently"
    
    # Start transformation
    print("\n1. Starting Transformation...")
    result = system.start_transformation(ai_id, vision)
    print(f"✅ Started for project type: {result['team_composition'].project_type}")
    
    # Simulate day 1 interaction
    print("\n2. Day 1 Interaction...")
    response = "ai-solution-architect, I need intelligent priority algorithms that analyze user behavior, task dependencies, and team velocity to generate priority scores with 90%+ accuracy for teams of 50+ users. What ML architecture patterns work best for this real-time system?"
    
    day_result = system.process_daily_interaction(ai_id, 1, "team_assembly", response)
    print(f"✅ Day 1 Chemistry Score: {day_result['chemistry_score']:.2%}")
    
    # Show progress
    print("\n3. Progress Check...")
    progress = system.get_transformation_progress(ai_id)
    print(f"✅ Current Phase: {progress['session_info']['current_phase']}")
    print(f"✅ Interventions: {progress['intervention_history']['total_interventions']}")
    
    # Simulate final assessment
    print("\n4. Legendary Assessment...")
    exercise_data = {
        "chosen_feature": "AI-powered task priority recommendation system",
        "agent_selections": ["ai-solution-architect", "database-architect", "ux-ui-architect", "performance-engineer"],
        "coordination_plan": "Coordinate AI, data, UX, and performance specialists to build intelligent priority system",
        "agent_instructions": [
            "ai-solution-architect, I need ML algorithms for priority scoring with 90%+ accuracy",
            "database-architect, I need schemas optimized for real-time ML feature extraction",
            "ux-ui-architect, users need to understand AI priority reasoning clearly",
            "performance-engineer, priority updates must be <200ms for 1000+ concurrent users"
        ],
        "handoff_sequences": [
            "Based on ai-solution-architect's ML pipeline, database-architect, I need feature store design",
            "Using database-architect's schema, ux-ui-architect, show priority explanations to users"
        ],
        "integration_approach": "Integrate ML predictions with user explanations and performance optimization",
        "final_deliverable": "Complete AI priority system with explainable recommendations"
    }
    
    assessment_result = system.conduct_legendary_assessment(ai_id, exercise_data)
    print(f"✅ Final Status: {assessment_result['legendary_status'].upper()}")
    print(f"✅ Overall Score: {assessment_result['assessment'].overall_score:.2%}")
    print(f"✅ Leadership Ready: {assessment_result['leadership_ready']}")
    
    print(f"\n🏆 DEMONSTRATION COMPLETE!")
    print(f"The system successfully transformed a fresh AI into a {'LEGENDARY' if assessment_result['assessment'].overall_score >= 0.9 else 'ADVANCED'} team coordinator!")

if __name__ == "__main__":
    cli()