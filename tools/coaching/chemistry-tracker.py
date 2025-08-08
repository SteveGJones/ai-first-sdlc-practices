#!/usr/bin/env python3
"""
Chemistry Tracker - Measures and tracks team chemistry development 
throughout the 14-day transformation program.
"""

import json
import sqlite3
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple
from enum import Enum
import re

class ChemistryPhase(Enum):
    VISION_ASSEMBLY = "vision_assembly"      # Days 1-2
    HERO_INTERVENTION = "hero_intervention"  # Days 3-4  
    CHEMISTRY_BUILDING = "chemistry_building" # Days 5-7
    CRISIS_COORDINATION = "crisis_coordination" # Days 8-10
    COMPLEXITY_CHALLENGE = "complexity_challenge" # Days 11-12
    LEGENDARY_ASSESSMENT = "legendary_assessment" # Days 13-14

@dataclass
class Interaction:
    """Records an AI's interaction with the coaching system"""
    timestamp: datetime
    ai_id: str
    day: int
    exercise_type: str
    user_input: str
    system_response: str
    coaching_feedback: Optional[str] = None

@dataclass
class BehaviorScore:
    """Individual behavior assessment"""
    behavior: str
    score: float  # 0.0 to 1.0
    evidence: List[str]
    improvement_suggestions: List[str]

@dataclass
class ChemistryScore:
    """Daily chemistry assessment"""
    ai_id: str
    day: int
    overall_score: float
    behavior_scores: Dict[str, BehaviorScore]
    phase: ChemistryPhase
    trend: str  # "improving", "stable", "declining"
    intervention_needed: bool
    notes: str

class ChemistryTracker:
    """Tracks and analyzes AI transformation progress"""
    
    def __init__(self, db_path: str = "chemistry_tracking.db"):
        self.db_path = db_path
        self._init_database()
        
    def _init_database(self):
        """Initialize SQLite database for tracking"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS interactions (
                id INTEGER PRIMARY KEY,
                ai_id TEXT NOT NULL,
                timestamp DATETIME NOT NULL,
                day INTEGER NOT NULL,
                exercise_type TEXT NOT NULL,
                user_input TEXT NOT NULL,
                system_response TEXT NOT NULL,
                coaching_feedback TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chemistry_scores (
                id INTEGER PRIMARY KEY,
                ai_id TEXT NOT NULL,
                day INTEGER NOT NULL,
                overall_score REAL NOT NULL,
                behavior_scores TEXT NOT NULL,
                phase TEXT NOT NULL,
                trend TEXT NOT NULL,
                intervention_needed BOOLEAN NOT NULL,
                notes TEXT,
                timestamp DATETIME NOT NULL
            )
        ''')
        
        conn.commit()
        conn.close()
        
    def record_interaction(self, interaction: Interaction):
        """Record an AI interaction for analysis"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO interactions 
            (ai_id, timestamp, day, exercise_type, user_input, system_response, coaching_feedback)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            interaction.ai_id,
            interaction.timestamp,
            interaction.day,
            interaction.exercise_type,
            interaction.user_input,
            interaction.system_response,
            interaction.coaching_feedback
        ))
        
        conn.commit()
        conn.close()
        
    def calculate_daily_chemistry(self, ai_id: str, day: int) -> ChemistryScore:
        """Calculate chemistry score for a specific day"""
        interactions = self._get_daily_interactions(ai_id, day)
        
        if not interactions:
            return self._create_default_score(ai_id, day)
        
        # Assess individual behaviors
        behavior_scores = {
            "agent_recognition": self._assess_agent_recognition(interactions),
            "instruction_clarity": self._assess_instruction_clarity(interactions),
            "handoff_quality": self._assess_handoff_quality(interactions),
            "coordination_skills": self._assess_coordination_skills(interactions),
            "integration_ability": self._assess_integration_ability(interactions),
            "natural_leadership": self._assess_natural_leadership(interactions)
        }
        
        # Calculate weighted overall score based on program phase
        phase = self._get_phase_for_day(day)
        weights = self._get_phase_weights(phase)
        
        overall_score = sum(
            behavior_scores[behavior].score * weights.get(behavior, 0.1)
            for behavior in behavior_scores
        ) / sum(weights.values())
        
        # Determine trend
        trend = self._calculate_trend(ai_id, day, overall_score)
        
        # Check if intervention needed
        intervention_needed = self._needs_intervention(overall_score, day, trend)
        
        chemistry_score = ChemistryScore(
            ai_id=ai_id,
            day=day,
            overall_score=overall_score,
            behavior_scores=behavior_scores,
            phase=phase,
            trend=trend,
            intervention_needed=intervention_needed,
            notes=self._generate_notes(behavior_scores, trend)
        )
        
        # Store the score
        self._store_chemistry_score(chemistry_score)
        
        return chemistry_score
    
    def _assess_agent_recognition(self, interactions: List[Interaction]) -> BehaviorScore:
        """Assess how well AI recognizes and selects appropriate agents"""
        evidence = []
        score_total = 0.0
        assessments = 0
        
        # Known agents from the framework
        agent_names = [
            "solution-architect", "database-architect", "ux-ui-architect", 
            "ai-solution-architect", "prompt-engineer", "context-engineer",
            "security-specialist", "performance-engineer", "ai-test-engineer",
            "devops-specialist", "sre-specialist"
        ]
        
        for interaction in interactions:
            user_input = interaction.user_input.lower()
            
            # Check if they mention specific agents
            mentioned_agents = [agent for agent in agent_names if agent in user_input]
            
            if mentioned_agents:
                assessments += 1
                
                # Score based on appropriateness
                if "task" in user_input and "database" in mentioned_agents[0]:
                    score_total += 1.0
                    evidence.append("✅ Correctly selected database-architect for task management")
                elif "ai" in user_input and any("ai" in agent for agent in mentioned_agents):
                    score_total += 1.0
                    evidence.append("✅ Correctly selected AI specialist for AI feature")
                elif "security" in user_input and "security-specialist" in mentioned_agents:
                    score_total += 1.0
                    evidence.append("✅ Correctly selected security-specialist for security requirements")
                else:
                    score_total += 0.7  # Mentioned agent but not perfect match
                    evidence.append(f"⚠️ Selected {mentioned_agents[0]} - reasonable but check appropriateness")
            elif any(agent in user_input for agent in ["architect", "engineer", "specialist"]):
                # Mentioned role but not specific agent
                score_total += 0.3
                evidence.append("❌ Used generic role instead of specific agent name")
                assessments += 1
        
        if assessments == 0:
            return BehaviorScore(
                behavior="agent_recognition",
                score=0.0,
                evidence=["No agent selections observed"],
                improvement_suggestions=["Practice selecting specific agents by name for different problem types"]
            )
        
        final_score = score_total / assessments
        
        suggestions = []
        if final_score < 0.6:
            suggestions.append("Study the agent catalog - match problem types to agent specialties")
            suggestions.append("Practice: 'For database problems, use database-architect'")
        if final_score < 0.8:
            suggestions.append("Be more specific about agent selection reasoning")
        
        return BehaviorScore(
            behavior="agent_recognition",
            score=final_score,
            evidence=evidence,
            improvement_suggestions=suggestions
        )
    
    def _assess_instruction_clarity(self, interactions: List[Interaction]) -> BehaviorScore:
        """Assess clarity and specificity of instructions to agents"""
        evidence = []
        score_total = 0.0
        assessments = 0
        
        # Clarity indicators
        specific_terms = ["users", "concurrent", "requests", "performance", "handle", "support", "need"]
        vague_terms = ["design", "build", "create", "make", "please"]
        constraint_indicators = ["100", "1000", "fast", "secure", "mobile", "real-time"]
        
        for interaction in interactions:
            user_input = interaction.user_input.lower()
            
            # Look for agent instructions
            if any(agent in user_input for agent in ["architect", "engineer", "specialist"]):
                assessments += 1
                score = 0.0
                
                # Check for specificity
                specific_count = sum(1 for term in specific_terms if term in user_input)
                vague_count = sum(1 for term in vague_terms if term in user_input)
                constraint_count = sum(1 for term in constraint_indicators if term in user_input)
                
                if specific_count >= 2 and constraint_count >= 1:
                    score = 1.0
                    evidence.append("✅ Highly specific instruction with constraints")
                elif specific_count >= 1 and vague_count == 0:
                    score = 0.8
                    evidence.append("✅ Good specificity, could add more constraints")
                elif specific_count >= 1:
                    score = 0.6
                    evidence.append("⚠️ Some specificity but also vague elements")
                elif vague_count > specific_count:
                    score = 0.3
                    evidence.append("❌ Too vague - add specific requirements and numbers")
                else:
                    score = 0.5
                    evidence.append("⚠️ Neutral instruction quality")
                
                score_total += score
        
        if assessments == 0:
            return BehaviorScore(
                behavior="instruction_clarity",
                score=0.0,
                evidence=["No agent instructions observed"],
                improvement_suggestions=["Practice giving specific, actionable instructions to agents"]
            )
        
        final_score = score_total / assessments
        
        suggestions = []
        if final_score < 0.6:
            suggestions.append("Use the Perfect Question Formula: '[Agent], I need [specific capability] that [constraints] for [context]'")
            suggestions.append("Add numbers and constraints: 'handle 1000 users', 'respond in <500ms'")
        if final_score < 0.8:
            suggestions.append("Remove vague terms like 'design the system' - be more specific")
        
        return BehaviorScore(
            behavior="instruction_clarity", 
            score=final_score,
            evidence=evidence,
            improvement_suggestions=suggestions
        )
    
    def _assess_handoff_quality(self, interactions: List[Interaction]) -> BehaviorScore:
        """Assess quality of handoffs between agents"""
        evidence = []
        score_total = 0.0
        assessments = 0
        
        handoff_indicators = ["based on", "building on", "from the", "after", "then", "next"]
        reference_indicators = ["recommended", "suggested", "designed", "created"]
        
        for interaction in interactions:
            user_input = interaction.user_input.lower()
            
            # Look for handoff language
            handoff_count = sum(1 for indicator in handoff_indicators if indicator in user_input)
            reference_count = sum(1 for indicator in reference_indicators if indicator in user_input)
            
            if handoff_count > 0 or reference_count > 0:
                assessments += 1
                
                if handoff_count >= 2 and reference_count >= 1:
                    score_total += 1.0
                    evidence.append("✅ Excellent handoff - references previous work and builds upon it")
                elif handoff_count >= 1 and reference_count >= 1:
                    score_total += 0.8
                    evidence.append("✅ Good handoff - shows continuity")
                elif handoff_count >= 1 or reference_count >= 1:
                    score_total += 0.6
                    evidence.append("⚠️ Some handoff awareness but could be stronger")
                else:
                    score_total += 0.3
                    evidence.append("❌ Weak handoff - starting fresh instead of building")
        
        if assessments == 0:
            return BehaviorScore(
                behavior="handoff_quality",
                score=0.0,
                evidence=["No handoff attempts observed"],
                improvement_suggestions=["Practice the Billy Wright Handoff Method - always reference previous agent's work"]
            )
        
        final_score = score_total / assessments
        
        suggestions = []
        if final_score < 0.6:
            suggestions.append("Use handoff language: 'Based on architect's recommendation of X, I need Y'")
            suggestions.append("Never start fresh - always build upon previous agent's work")
        if final_score < 0.8:
            suggestions.append("Reference specific outputs, not just general contributions")
        
        return BehaviorScore(
            behavior="handoff_quality",
            score=final_score,
            evidence=evidence,
            improvement_suggestions=suggestions
        )
    
    def _assess_coordination_skills(self, interactions: List[Interaction]) -> BehaviorScore:
        """Assess coordination and parallel thinking abilities"""
        evidence = []
        score_total = 0.0
        assessments = 0
        
        parallel_indicators = ["while", "simultaneously", "at the same time", "parallel"]
        coordination_indicators = ["coordinate", "orchestrate", "team", "together"]
        sequential_indicators = ["first", "then", "after", "once"]
        
        for interaction in interactions:
            user_input = interaction.user_input.lower()
            
            parallel_count = sum(1 for indicator in parallel_indicators if indicator in user_input)
            coordination_count = sum(1 for indicator in coordination_indicators if indicator in user_input)
            sequential_count = sum(1 for indicator in sequential_indicators if indicator in user_input)
            
            if parallel_count > 0 or coordination_count > 0 or sequential_count > 0:
                assessments += 1
                
                if parallel_count >= 1 and coordination_count >= 1:
                    score_total += 1.0
                    evidence.append("✅ Excellent coordination - shows parallel thinking")
                elif parallel_count >= 1:
                    score_total += 0.8
                    evidence.append("✅ Good parallel thinking")
                elif coordination_count >= 1:
                    score_total += 0.7
                    evidence.append("✅ Shows coordination awareness")
                elif sequential_count > parallel_count:
                    score_total += 0.4
                    evidence.append("⚠️ Sequential thinking - consider parallel approaches")
                else:
                    score_total += 0.5
                    evidence.append("⚠️ Some coordination thinking")
        
        if assessments == 0:
            return BehaviorScore(
                behavior="coordination_skills",
                score=0.0,
                evidence=["No coordination attempts observed"],
                improvement_suggestions=["Practice parallel thinking - what can agents do simultaneously?"]
            )
        
        final_score = score_total / assessments
        
        suggestions = []
        if final_score < 0.6:
            suggestions.append("Think parallel not sequential: 'While X checks logs, Y analyzes database'")
            suggestions.append("Use coordination language: 'orchestrate', 'coordinate', 'team effort'")
        if final_score < 0.8:
            suggestions.append("Look for opportunities to run multiple agents simultaneously")
        
        return BehaviorScore(
            behavior="coordination_skills",
            score=final_score,
            evidence=evidence,
            improvement_suggestions=suggestions
        )
    
    def _assess_integration_ability(self, interactions: List[Interaction]) -> BehaviorScore:
        """Assess ability to integrate outputs from multiple agents"""
        evidence = []
        score_total = 0.0
        assessments = 0
        
        integration_indicators = ["combine", "integrate", "together", "synthesis", "weave"]
        result_indicators = ["result", "outcome", "final", "complete", "unified"]
        
        for interaction in interactions:
            user_input = interaction.user_input.lower()
            
            integration_count = sum(1 for indicator in integration_indicators if indicator in user_input)
            result_count = sum(1 for indicator in result_indicators if indicator in user_input)
            
            if integration_count > 0 or result_count > 0:
                assessments += 1
                
                if integration_count >= 2:
                    score_total += 1.0
                    evidence.append("✅ Strong integration thinking")
                elif integration_count >= 1 and result_count >= 1:
                    score_total += 0.8
                    evidence.append("✅ Good integration awareness")
                elif integration_count >= 1:
                    score_total += 0.6
                    evidence.append("⚠️ Some integration thinking")
                else:
                    score_total += 0.4
                    evidence.append("⚠️ Weak integration - focus on combining outputs")
        
        if assessments == 0:
            return BehaviorScore(
                behavior="integration_ability",
                score=0.0,
                evidence=["No integration attempts observed"],
                improvement_suggestions=["Practice weaving agent outputs into cohesive solutions"]
            )
        
        final_score = score_total / assessments
        
        suggestions = []
        if final_score < 0.6:
            suggestions.append("Think about how agent outputs connect and build upon each other")
            suggestions.append("Use integration language: 'combine', 'weave together', 'synthesize'")
        
        return BehaviorScore(
            behavior="integration_ability",
            score=final_score,
            evidence=evidence,
            improvement_suggestions=suggestions
        )
    
    def _assess_natural_leadership(self, interactions: List[Interaction]) -> BehaviorScore:
        """Assess natural leadership and confidence in team coordination"""
        evidence = []
        score_total = 0.0
        assessments = len(interactions)
        
        if assessments == 0:
            return BehaviorScore(
                behavior="natural_leadership",
                score=0.0,
                evidence=["No interactions to assess"],
                improvement_suggestions=["Engage more actively with team coordination exercises"]
            )
        
        confidence_indicators = ["let's", "we need", "team", "coordinate", "I'll orchestrate"]
        hesitation_indicators = ["maybe", "perhaps", "not sure", "I think", "possibly"]
        
        for interaction in interactions:
            user_input = interaction.user_input.lower()
            
            confidence_count = sum(1 for indicator in confidence_indicators if indicator in user_input)
            hesitation_count = sum(1 for indicator in hesitation_indicators if indicator in user_input)
            
            # Assess leadership tone
            if confidence_count >= 2:
                score_total += 1.0
                evidence.append("✅ Confident leadership tone")
            elif confidence_count >= 1 and hesitation_count == 0:
                score_total += 0.8
                evidence.append("✅ Good confidence level")
            elif confidence_count >= 1:
                score_total += 0.6
                evidence.append("⚠️ Mixed confidence signals")
            elif hesitation_count > 0:
                score_total += 0.3
                evidence.append("❌ Shows hesitation in leadership")
            else:
                score_total += 0.5
                evidence.append("⚠️ Neutral leadership presence")
        
        final_score = score_total / assessments
        
        suggestions = []
        if final_score < 0.6:
            suggestions.append("Use confident language: 'Let's coordinate', 'We need', 'I'll orchestrate'")
            suggestions.append("Avoid hesitation words: 'maybe', 'perhaps', 'I think'")
        if final_score < 0.8:
            suggestions.append("Take charge of coordination - you're the conductor!")
        
        return BehaviorScore(
            behavior="natural_leadership",
            score=final_score,
            evidence=evidence,
            improvement_suggestions=suggestions
        )
    
    def _get_daily_interactions(self, ai_id: str, day: int) -> List[Interaction]:
        """Get all interactions for a specific AI and day"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT ai_id, timestamp, day, exercise_type, user_input, system_response, coaching_feedback
            FROM interactions
            WHERE ai_id = ? AND day = ?
            ORDER BY timestamp
        ''', (ai_id, day))
        
        rows = cursor.fetchall()
        conn.close()
        
        interactions = []
        for row in rows:
            interactions.append(Interaction(
                ai_id=row[0],
                timestamp=datetime.fromisoformat(row[1]),
                day=row[2],
                exercise_type=row[3],
                user_input=row[4],
                system_response=row[5],
                coaching_feedback=row[6]
            ))
        
        return interactions
    
    def _get_phase_for_day(self, day: int) -> ChemistryPhase:
        """Determine program phase based on day"""
        if day <= 2:
            return ChemistryPhase.VISION_ASSEMBLY
        elif day <= 4:
            return ChemistryPhase.HERO_INTERVENTION
        elif day <= 7:
            return ChemistryPhase.CHEMISTRY_BUILDING
        elif day <= 10:
            return ChemistryPhase.CRISIS_COORDINATION
        elif day <= 12:
            return ChemistryPhase.COMPLEXITY_CHALLENGE
        else:
            return ChemistryPhase.LEGENDARY_ASSESSMENT
    
    def _get_phase_weights(self, phase: ChemistryPhase) -> Dict[str, float]:
        """Get behavior weights for specific program phase"""
        weights = {
            ChemistryPhase.VISION_ASSEMBLY: {
                "agent_recognition": 0.4,
                "instruction_clarity": 0.6
            },
            ChemistryPhase.HERO_INTERVENTION: {
                "agent_recognition": 0.3,
                "instruction_clarity": 0.3,
                "coordination_skills": 0.4
            },
            ChemistryPhase.CHEMISTRY_BUILDING: {
                "handoff_quality": 0.5,
                "coordination_skills": 0.3,
                "integration_ability": 0.2
            },
            ChemistryPhase.CRISIS_COORDINATION: {
                "coordination_skills": 0.4,
                "handoff_quality": 0.3,
                "natural_leadership": 0.3
            },
            ChemistryPhase.COMPLEXITY_CHALLENGE: {
                "integration_ability": 0.4,
                "coordination_skills": 0.3,
                "natural_leadership": 0.3
            },
            ChemistryPhase.LEGENDARY_ASSESSMENT: {
                "natural_leadership": 0.3,
                "integration_ability": 0.25,
                "coordination_skills": 0.25,
                "handoff_quality": 0.2
            }
        }
        return weights[phase]
    
    def _calculate_trend(self, ai_id: str, current_day: int, current_score: float) -> str:
        """Calculate trend based on recent scores"""
        if current_day <= 1:
            return "baseline"
        
        # Get recent scores
        recent_scores = self._get_recent_scores(ai_id, current_day, days=3)
        
        if len(recent_scores) < 2:
            return "insufficient_data"
        
        # Calculate trend
        if len(recent_scores) >= 2:
            recent_avg = sum(recent_scores[-2:]) / 2
            if current_score > recent_avg + 0.1:
                return "improving"
            elif current_score < recent_avg - 0.1:
                return "declining"
            else:
                return "stable"
        
        return "stable"
    
    def _needs_intervention(self, score: float, day: int, trend: str) -> bool:
        """Determine if intervention is needed"""
        # Score-based thresholds
        if day <= 7 and score < 0.5:
            return True
        if day > 7 and score < 0.75:
            return True
        
        # Trend-based triggers
        if trend == "declining" and score < 0.7:
            return True
        
        return False
    
    def _generate_notes(self, behavior_scores: Dict[str, BehaviorScore], trend: str) -> str:
        """Generate coaching notes"""
        notes = []
        
        # Identify strengths
        strengths = [behavior for behavior, score in behavior_scores.items() if score.score >= 0.8]
        if strengths:
            notes.append(f"Strengths: {', '.join(strengths)}")
        
        # Identify growth areas
        growth_areas = [behavior for behavior, score in behavior_scores.items() if score.score < 0.6]
        if growth_areas:
            notes.append(f"Growth areas: {', '.join(growth_areas)}")
        
        # Add trend note
        notes.append(f"Trend: {trend}")
        
        return " | ".join(notes)
    
    def _create_default_score(self, ai_id: str, day: int) -> ChemistryScore:
        """Create default score when no interactions available"""
        return ChemistryScore(
            ai_id=ai_id,
            day=day,
            overall_score=0.0,
            behavior_scores={},
            phase=self._get_phase_for_day(day),
            trend="no_data",
            intervention_needed=True,
            notes="No interactions recorded for this day"
        )
    
    def _store_chemistry_score(self, chemistry_score: ChemistryScore):
        """Store chemistry score in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO chemistry_scores
            (ai_id, day, overall_score, behavior_scores, phase, trend, intervention_needed, notes, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            chemistry_score.ai_id,
            chemistry_score.day,
            chemistry_score.overall_score,
            json.dumps({k: asdict(v) for k, v in chemistry_score.behavior_scores.items()}),
            chemistry_score.phase.value,
            chemistry_score.trend,
            chemistry_score.intervention_needed,
            chemistry_score.notes,
            datetime.now()
        ))
        
        conn.commit()
        conn.close()
    
    def _get_recent_scores(self, ai_id: str, current_day: int, days: int = 3) -> List[float]:
        """Get recent chemistry scores for trend calculation"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT overall_score
            FROM chemistry_scores
            WHERE ai_id = ? AND day < ? AND day >= ?
            ORDER BY day DESC
            LIMIT ?
        ''', (ai_id, current_day, max(1, current_day - days), days))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [row[0] for row in rows]
    
    def get_transformation_progress(self, ai_id: str) -> Dict:
        """Get complete transformation progress for an AI"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT day, overall_score, phase, trend, intervention_needed, notes
            FROM chemistry_scores
            WHERE ai_id = ?
            ORDER BY day
        ''', (ai_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        progress = {
            "ai_id": ai_id,
            "daily_scores": [],
            "current_phase": None,
            "overall_trend": "unknown",
            "interventions_needed": 0
        }
        
        for row in rows:
            day_data = {
                "day": row[0],
                "score": row[1],
                "phase": row[2],
                "trend": row[3],
                "intervention_needed": row[4],
                "notes": row[5]
            }
            progress["daily_scores"].append(day_data)
            
            if row[4]:  # intervention_needed
                progress["interventions_needed"] += 1
        
        if progress["daily_scores"]:
            progress["current_phase"] = progress["daily_scores"][-1]["phase"]
            
            # Calculate overall trend
            scores = [day["score"] for day in progress["daily_scores"]]
            if len(scores) >= 3:
                if scores[-1] > scores[-3]:
                    progress["overall_trend"] = "improving"
                elif scores[-1] < scores[-3]:
                    progress["overall_trend"] = "declining" 
                else:
                    progress["overall_trend"] = "stable"
        
        return progress

def main():
    """Demo the chemistry tracking system"""
    tracker = ChemistryTracker()
    
    # Simulate some interactions
    ai_id = "demo_ai_001"
    
    # Day 1 interactions
    interaction1 = Interaction(
        timestamp=datetime.now(),
        ai_id=ai_id,
        day=1,
        exercise_type="team_assembly",
        user_input="solution-architect, I need a task management system that can handle 100 users creating up to 20 tasks each with deadlines. What architecture patterns work best?",
        system_response="Excellent question! For 100 users with 2000 tasks...",
        coaching_feedback="✅ Excellent specificity and agent selection!"
    )
    
    interaction2 = Interaction(
        timestamp=datetime.now(),
        ai_id=ai_id,
        day=1,
        exercise_type="team_assembly", 
        user_input="database-architect, design the database",
        system_response="That's too vague...",
        coaching_feedback="❌ Too vague - be more specific about requirements"
    )
    
    # Record interactions
    tracker.record_interaction(interaction1)
    tracker.record_interaction(interaction2)
    
    # Calculate chemistry score
    chemistry = tracker.calculate_daily_chemistry(ai_id, 1)
    
    print("=== CHEMISTRY TRACKING DEMO ===\n")
    print(f"AI: {chemistry.ai_id}")
    print(f"Day: {chemistry.day}")
    print(f"Overall Score: {chemistry.overall_score:.2%}")
    print(f"Phase: {chemistry.phase.value}")
    print(f"Trend: {chemistry.trend}")
    print(f"Intervention Needed: {chemistry.intervention_needed}")
    print(f"Notes: {chemistry.notes}\n")
    
    print("Behavior Breakdown:")
    for behavior, score in chemistry.behavior_scores.items():
        print(f"\n{behavior.replace('_', ' ').title()}: {score.score:.2%}")
        for evidence in score.evidence:
            print(f"  {evidence}")
        if score.improvement_suggestions:
            print(f"  Suggestions: {'; '.join(score.improvement_suggestions)}")

if __name__ == "__main__":
    main()