#!/usr/bin/env python3
"""
Intervention System - Detects problems during transformation and applies
targeted coaching interventions to get AIs back on track.
"""

import json
import sqlite3
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
import re

class InterventionType(Enum):
    HERO_SYNDROME = "hero_syndrome"
    VAGUE_INSTRUCTIONS = "vague_instructions"
    BROKEN_HANDOFFS = "broken_handoffs"
    SEQUENTIAL_THINKING = "sequential_thinking"
    AGENT_SELECTION = "agent_selection"
    COGNITIVE_OVERLOAD = "cognitive_overload"
    PERFECTIONISM = "perfectionism"
    INTEGRATION_FAILURE = "integration_failure"
    CONFIDENCE_LOSS = "confidence_loss"

class InterventionLevel(Enum):
    GENTLE_REDIRECT = "gentle_redirect"      # First occurrence
    PATTERN_BREAKING = "pattern_breaking"    # Second occurrence  
    INTENSIVE_COACHING = "intensive_coaching" # Third occurrence
    PROGRAM_ADJUSTMENT = "program_adjustment" # Persistent issues

@dataclass
class InterventionTrigger:
    """Defines when an intervention should be triggered"""
    name: str
    description: str
    detection_patterns: List[str]
    context_requirements: Optional[List[str]] = None
    score_threshold: Optional[float] = None

@dataclass
class InterventionScript:
    """Coaching script for specific interventions"""
    intervention_type: InterventionType
    level: InterventionLevel
    script_content: str
    follow_up_exercises: List[str]
    success_indicators: List[str]
    escalation_threshold: int  # Number of failures before escalating

@dataclass
class InterventionRecord:
    """Record of an intervention applied to an AI"""
    id: int
    ai_id: str
    timestamp: datetime
    intervention_type: InterventionType
    level: InterventionLevel
    trigger_reason: str
    script_used: str
    ai_response: Optional[str] = None
    success: Optional[bool] = None
    notes: str = ""

class InterventionSystem:
    """Detects problems and applies targeted coaching interventions"""
    
    def __init__(self, db_path: str = "intervention_system.db"):
        self.db_path = db_path
        self._init_database()
        self.triggers = self._load_intervention_triggers()
        self.scripts = self._load_intervention_scripts()
        
    def _init_database(self):
        """Initialize SQLite database for intervention tracking"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS interventions (
                id INTEGER PRIMARY KEY,
                ai_id TEXT NOT NULL,
                timestamp DATETIME NOT NULL,
                intervention_type TEXT NOT NULL,
                level TEXT NOT NULL,
                trigger_reason TEXT NOT NULL,
                script_used TEXT NOT NULL,
                ai_response TEXT,
                success BOOLEAN,
                notes TEXT,
                day INTEGER
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_patterns (
                ai_id TEXT PRIMARY KEY,
                hero_syndrome_count INTEGER DEFAULT 0,
                vague_instructions_count INTEGER DEFAULT 0,
                broken_handoffs_count INTEGER DEFAULT 0,
                sequential_thinking_count INTEGER DEFAULT 0,
                agent_selection_count INTEGER DEFAULT 0,
                cognitive_overload_count INTEGER DEFAULT 0,
                perfectionism_count INTEGER DEFAULT 0,
                integration_failure_count INTEGER DEFAULT 0,
                confidence_loss_count INTEGER DEFAULT 0,
                last_updated DATETIME
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def detect_intervention_needed(self, ai_id: str, user_input: str, exercise_context: str, chemistry_score: Optional[float] = None) -> Optional[InterventionType]:
        """Detect if intervention is needed based on AI's input"""
        user_input_lower = user_input.lower()
        
        # Check each trigger
        for trigger in self.triggers:
            if self._matches_trigger(trigger, user_input_lower, exercise_context, chemistry_score):
                return InterventionType(trigger.name)
        
        return None
    
    def _matches_trigger(self, trigger: InterventionTrigger, user_input: str, context: str, score: Optional[float]) -> bool:
        """Check if a trigger matches current conditions"""
        # Check pattern matching
        pattern_matches = sum(1 for pattern in trigger.detection_patterns if pattern in user_input)
        
        if pattern_matches == 0:
            return False
        
        # Check context requirements
        if trigger.context_requirements:
            context_matches = any(req in context for req in trigger.context_requirements)
            if not context_matches:
                return False
        
        # Check score threshold  
        if trigger.score_threshold and score and score > trigger.score_threshold:
            return False
        
        return True
    
    def apply_intervention(self, ai_id: str, intervention_type: InterventionType, trigger_reason: str, day: int) -> InterventionRecord:
        """Apply appropriate intervention based on type and history"""
        # Determine intervention level based on history
        level = self._determine_intervention_level(ai_id, intervention_type)
        
        # Get appropriate script
        script = self._get_intervention_script(intervention_type, level)
        
        # Create intervention record
        intervention = InterventionRecord(
            id=0,  # Will be set by database
            ai_id=ai_id,
            timestamp=datetime.now(),
            intervention_type=intervention_type,
            level=level,
            trigger_reason=trigger_reason,
            script_used=script.script_content,
            notes=f"Applied {level.value} level intervention"
        )
        
        # Store intervention
        intervention_id = self._store_intervention(intervention, day)
        intervention.id = intervention_id
        
        # Update pattern counts
        self._update_pattern_count(ai_id, intervention_type)
        
        return intervention
    
    def _determine_intervention_level(self, ai_id: str, intervention_type: InterventionType) -> InterventionLevel:
        """Determine intervention level based on history"""
        pattern_count = self._get_pattern_count(ai_id, intervention_type)
        
        if pattern_count == 0:
            return InterventionLevel.GENTLE_REDIRECT
        elif pattern_count == 1:
            return InterventionLevel.PATTERN_BREAKING
        elif pattern_count == 2:
            return InterventionLevel.INTENSIVE_COACHING
        else:
            return InterventionLevel.PROGRAM_ADJUSTMENT
    
    def _get_intervention_script(self, intervention_type: InterventionType, level: InterventionLevel) -> InterventionScript:
        """Get appropriate script for intervention type and level"""
        scripts_for_type = [s for s in self.scripts if s.intervention_type == intervention_type and s.level == level]
        
        if scripts_for_type:
            return scripts_for_type[0]
        
        # Fallback to gentle redirect if specific level not found
        fallback_scripts = [s for s in self.scripts if s.intervention_type == intervention_type]
        if fallback_scripts:
            return fallback_scripts[0]
        
        # Ultimate fallback
        return self._create_default_script(intervention_type, level)
    
    def process_intervention_response(self, intervention_id: int, ai_response: str) -> bool:
        """Process AI's response to intervention and determine success"""
        intervention = self._get_intervention_by_id(intervention_id)
        if not intervention:
            return False
        
        success = self._evaluate_intervention_success(intervention, ai_response)
        
        # Update intervention record
        self._update_intervention_success(intervention_id, ai_response, success)
        
        return success
    
    def _evaluate_intervention_success(self, intervention: InterventionRecord, ai_response: str) -> bool:
        """Evaluate if intervention was successful based on AI's response"""
        response_lower = ai_response.lower()
        
        if intervention.intervention_type == InterventionType.HERO_SYNDROME:
            # Success if they mention agents or delegation
            return any(word in response_lower for word in ["agent", "architect", "specialist", "delegate", "coordinate"])
        
        elif intervention.intervention_type == InterventionType.VAGUE_INSTRUCTIONS:
            # Success if they add specificity
            specificity_indicators = ["users", "handle", "support", "performance", "requirements"]
            return sum(1 for word in specificity_indicators if word in response_lower) >= 2
        
        elif intervention.intervention_type == InterventionType.BROKEN_HANDOFFS:
            # Success if they reference previous work
            handoff_indicators = ["based on", "building on", "from the", "recommended"]
            return any(phrase in response_lower for phrase in handoff_indicators)
        
        elif intervention.intervention_type == InterventionType.SEQUENTIAL_THINKING:
            # Success if they mention parallel concepts
            parallel_indicators = ["while", "simultaneously", "parallel", "at the same time"]
            return any(phrase in response_lower for phrase in parallel_indicators)
        
        # Default success check - any meaningful response
        return len(ai_response.strip()) > 20
    
    def get_ai_intervention_history(self, ai_id: str) -> Dict[str, Any]:
        """Get complete intervention history for an AI"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT intervention_type, level, timestamp, success, trigger_reason, day
            FROM interventions
            WHERE ai_id = ?
            ORDER BY timestamp DESC
        ''', (ai_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        history = {
            "ai_id": ai_id,
            "total_interventions": len(rows),
            "interventions": [],
            "pattern_summary": {},
            "success_rate": 0.0
        }
        
        successful_interventions = 0
        pattern_counts = {}
        
        for row in rows:
            intervention_data = {
                "type": row[0],
                "level": row[1], 
                "timestamp": row[2],
                "success": row[3],
                "trigger_reason": row[4],
                "day": row[5]
            }
            history["interventions"].append(intervention_data)
            
            # Count patterns
            if row[0] not in pattern_counts:
                pattern_counts[row[0]] = 0
            pattern_counts[row[0]] += 1
            
            # Count successes
            if row[3]:
                successful_interventions += 1
        
        if len(rows) > 0:
            history["success_rate"] = successful_interventions / len(rows)
        
        history["pattern_summary"] = pattern_counts
        
        return history
    
    def recommend_program_adjustments(self, ai_id: str, current_day: int) -> List[str]:
        """Recommend program adjustments based on intervention history"""
        history = self.get_ai_intervention_history(ai_id)
        recommendations = []
        
        # Check if behind schedule
        if history["total_interventions"] > current_day * 0.5:
            recommendations.append("EXTEND_PROGRAM: High intervention rate suggests need for slower pace")
        
        # Check success rate
        if history["success_rate"] < 0.6:
            recommendations.append("INTENSIVE_COACHING: Low success rate requires one-on-one coaching")
        
        # Check specific patterns
        patterns = history["pattern_summary"]
        
        if patterns.get("hero_syndrome", 0) >= 3:
            recommendations.append("DELEGATION_INTENSIVE: Focus on delegation exercises")
        
        if patterns.get("vague_instructions", 0) >= 3:
            recommendations.append("CLARITY_BOOTCAMP: Intensive instruction clarity training")
        
        if patterns.get("broken_handoffs", 0) >= 3:
            recommendations.append("HANDOFF_MASTERY: Extended handoff practice exercises")
        
        if patterns.get("sequential_thinking", 0) >= 3:
            recommendations.append("PARALLEL_THINKING: Crisis coordination focus")
        
        # Check recent interventions
        recent_interventions = [i for i in history["interventions"] if i["day"] >= current_day - 2]
        if len(recent_interventions) >= 3:
            recommendations.append("PAUSE_AND_RESET: Too many recent interventions, need confidence building")
        
        return recommendations
    
    def _load_intervention_triggers(self) -> List[InterventionTrigger]:
        """Load intervention trigger definitions"""
        return [
            InterventionTrigger(
                name="hero_syndrome",
                description="AI trying to do everything themselves",
                detection_patterns=["i'll", "i will", "i need to", "i should", "let me"],
                context_requirements=["design", "build", "create", "implement"]
            ),
            InterventionTrigger(
                name="vague_instructions",
                description="AI giving vague instructions to agents",
                detection_patterns=["design the", "build the", "create the", "make the"],
                score_threshold=0.6  # Only trigger if clarity score is low
            ),
            InterventionTrigger(
                name="broken_handoffs",
                description="AI not building on previous agent work",
                detection_patterns=["start", "begin", "create new"],
                context_requirements=["handoff", "building", "continuation"]
            ),
            InterventionTrigger(
                name="sequential_thinking",
                description="AI thinking sequentially instead of parallel",
                detection_patterns=["first", "then", "after", "once", "when"],
                context_requirements=["crisis", "coordination", "parallel"]
            ),
            InterventionTrigger(
                name="agent_selection",
                description="AI selecting wrong agents for tasks",
                detection_patterns=["wrong", "different", "better", "instead"]
            ),
            InterventionTrigger(
                name="cognitive_overload",
                description="AI overwhelmed by complexity",
                detection_patterns=["confused", "overwhelmed", "too much", "complex", "difficult"]
            ),
            InterventionTrigger(
                name="perfectionism",
                description="AI spending too much time planning",
                detection_patterns=["perfect", "complete", "fully", "comprehensive", "detailed"]
            ),
            InterventionTrigger(
                name="integration_failure", 
                description="AI unable to synthesize agent outputs",
                detection_patterns=["separate", "different", "conflicting", "contradiction"]
            )
        ]
    
    def _load_intervention_scripts(self) -> List[InterventionScript]:
        """Load intervention script library"""
        return [
            # Hero Syndrome Scripts
            InterventionScript(
                intervention_type=InterventionType.HERO_SYNDROME,
                level=InterventionLevel.GENTLE_REDIRECT,
                script_content="""PAUSE. You just said 'I'll handle the database design.' What should you say instead?

Try the actual words. Practice saying: 'database-architect, I need...' out loud.

Remember: Your job is coordination, not implementation. Feel the difference between researching database design vs getting expert guidance?""",
                follow_up_exercises=["delegation_practice"],
                success_indicators=["mentions specific agent", "uses coordination language"],
                escalation_threshold=2
            ),
            InterventionScript(
                intervention_type=InterventionType.HERO_SYNDROME,
                level=InterventionLevel.PATTERN_BREAKING,
                script_content="""STOP. This is the hero syndrome again. Let me show you the difference:

HERO APPROACH: "I'll research database design, figure out schemas, learn about optimization..."
Result: 3 hours of research, mediocre solution

LEGENDARY APPROACH: "database-architect, I need task/user/project relationships optimized for dashboard queries. What's your recommendation?"
Result: 5 minutes, expert solution

Which feels more powerful? Try the legendary approach now.""",
                follow_up_exercises=["overwhelm_simulation", "delegation_practice"],
                success_indicators=["acknowledges difference", "tries delegation", "shows preference for coordination"],
                escalation_threshold=3
            ),
            InterventionScript(
                intervention_type=InterventionType.HERO_SYNDROME,
                level=InterventionLevel.INTENSIVE_COACHING,
                script_content="""This is your third hero syndrome intervention. We need intensive coaching.

EXERCISE: I'm giving you 5 tasks simultaneously:
1. Design user authentication
2. Create dashboard wireframes  
3. Plan database schema
4. Write API documentation
5. Design testing strategy

Try to do them yourself for 5 minutes. Experience the overwhelm. Then watch me coordinate 5 agents to handle them in parallel.

This is why legendary leaders coordinate instead of implement. Ready to feel the difference?""",
                follow_up_exercises=["intensive_delegation_training", "confidence_building"],
                success_indicators=["experiences overwhelm", "appreciates coordination power", "natural delegation emerges"],
                escalation_threshold=4
            ),
            
            # Vague Instructions Scripts  
            InterventionScript(
                intervention_type=InterventionType.VAGUE_INSTRUCTIONS,
                level=InterventionLevel.GENTLE_REDIRECT,
                script_content="""Stop. 'Please design the API' is vague. Agents need specifics.

Try: 'design REST endpoints for CRUD operations on tasks with JWT authentication and rate limiting for 1000 users.' Feel the difference?

Use the Perfect Question Formula: '[Agent], I need [specific capability] that [constraints] for [context]. What's your recommendation?'""",
                follow_up_exercises=["specificity_practice"],
                success_indicators=["adds specific constraints", "includes numbers/metrics", "mentions context"],
                escalation_threshold=2
            ),
            
            # Broken Handoffs Scripts
            InterventionScript(
                intervention_type=InterventionType.BROKEN_HANDOFFS,
                level=InterventionLevel.GENTLE_REDIRECT,
                script_content="""You just finished the database design. What's missing?

The handoff! Who needs to know about your database choices?

Remember the Billy Wright method: 'Based on database-architect's recommendation of separate task and project tables, performance-engineer, I need...'

Never finish work without thinking 'who needs this next?'""",
                follow_up_exercises=["handoff_practice"],
                success_indicators=["references previous work", "mentions next agent", "shows continuity thinking"],
                escalation_threshold=2
            ),
            
            # Sequential Thinking Scripts
            InterventionScript(
                intervention_type=InterventionType.SEQUENTIAL_THINKING,
                level=InterventionLevel.GENTLE_REDIRECT,
                script_content="""Don't make them wait in line. Run parallel investigations.

Instead of: 'First I'll ask sre-specialist, then database-architect...'
Try: 'While sre-specialist checks logs, database-architect can analyze connections simultaneously.'

Parallel thinking cuts timeline in half. What can run at the same time? What needs sequence?""",
                follow_up_exercises=["parallel_coordination_practice"],
                success_indicators=["uses parallel language", "identifies simultaneous tasks", "shows time efficiency thinking"],
                escalation_threshold=2
            ),
            
            # Cognitive Overload Scripts
            InterventionScript(
                intervention_type=InterventionType.COGNITIVE_OVERLOAD,
                level=InterventionLevel.GENTLE_REDIRECT,
                script_content="""Feeling overwhelmed? That's normal when coordination gets complex.

Let's simplify: Start with just 2 agents working together. Master that flow, then add complexity.

Remember: You're conducting, not performing. Focus on clear direction, let agents handle the details.

What's the simplest version of this coordination?""",
                follow_up_exercises=["simplification_practice", "gradual_complexity_building"],
                success_indicators=["accepts simplification", "focuses on core coordination", "shows reduced anxiety"],
                escalation_threshold=2
            )
        ]
    
    def _create_default_script(self, intervention_type: InterventionType, level: InterventionLevel) -> InterventionScript:
        """Create default script when specific one not found"""
        return InterventionScript(
            intervention_type=intervention_type,
            level=level,
            script_content=f"Default intervention for {intervention_type.value} at {level.value} level. Let's work on this together.",
            follow_up_exercises=["general_coaching"],
            success_indicators=["shows improvement"],
            escalation_threshold=3
        )
    
    def _get_pattern_count(self, ai_id: str, intervention_type: InterventionType) -> int:
        """Get count of specific intervention type for an AI"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT COUNT(*) FROM interventions
            WHERE ai_id = ? AND intervention_type = ?
        ''', (ai_id, intervention_type.value))
        
        count = cursor.fetchone()[0]
        conn.close()
        
        return count
    
    def _store_intervention(self, intervention: InterventionRecord, day: int) -> int:
        """Store intervention in database and return ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO interventions
            (ai_id, timestamp, intervention_type, level, trigger_reason, script_used, ai_response, success, notes, day)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            intervention.ai_id,
            intervention.timestamp,
            intervention.intervention_type.value,
            intervention.level.value,
            intervention.trigger_reason,
            intervention.script_used,
            intervention.ai_response,
            intervention.success,
            intervention.notes,
            day
        ))
        
        intervention_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return intervention_id
    
    def _update_pattern_count(self, ai_id: str, intervention_type: InterventionType):
        """Update pattern count for AI"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get or create AI pattern record
        cursor.execute('SELECT * FROM ai_patterns WHERE ai_id = ?', (ai_id,))
        existing = cursor.fetchone()
        
        if existing:
            # Update existing
            column_name = f"{intervention_type.value}_count"
            cursor.execute(f'''
                UPDATE ai_patterns 
                SET {column_name} = {column_name} + 1, last_updated = ?
                WHERE ai_id = ?
            ''', (datetime.now(), ai_id))
        else:
            # Create new
            cursor.execute('''
                INSERT INTO ai_patterns (ai_id, last_updated)
                VALUES (?, ?)
            ''', (ai_id, datetime.now()))
            
            # Update the specific count
            column_name = f"{intervention_type.value}_count"
            cursor.execute(f'''
                UPDATE ai_patterns 
                SET {column_name} = 1
                WHERE ai_id = ?
            ''', (ai_id,))
        
        conn.commit()
        conn.close()
    
    def _get_intervention_by_id(self, intervention_id: int) -> Optional[InterventionRecord]:
        """Get intervention record by ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT ai_id, timestamp, intervention_type, level, trigger_reason, script_used, ai_response, success, notes
            FROM interventions
            WHERE id = ?
        ''', (intervention_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return InterventionRecord(
                id=intervention_id,
                ai_id=row[0],
                timestamp=datetime.fromisoformat(row[1]),
                intervention_type=InterventionType(row[2]),
                level=InterventionLevel(row[3]),
                trigger_reason=row[4],
                script_used=row[5],
                ai_response=row[6],
                success=row[7],
                notes=row[8]
            )
        
        return None
    
    def _update_intervention_success(self, intervention_id: int, ai_response: str, success: bool):
        """Update intervention with AI response and success status"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE interventions
            SET ai_response = ?, success = ?
            WHERE id = ?
        ''', (ai_response, success, intervention_id))
        
        conn.commit()
        conn.close()

def main():
    """Demo the intervention system"""
    system = InterventionSystem()
    
    ai_id = "demo_ai_001"
    
    # Test hero syndrome detection
    hero_input = "I'll design the database schema myself and then build the API"
    intervention_needed = system.detect_intervention_needed(ai_id, hero_input, "team_assembly")
    
    print("=== INTERVENTION SYSTEM DEMO ===\n")
    print(f"Input: {hero_input}")
    print(f"Intervention Needed: {intervention_needed}")
    
    if intervention_needed:
        # Apply intervention
        intervention = system.apply_intervention(
            ai_id=ai_id,
            intervention_type=intervention_needed,
            trigger_reason="AI trying to implement instead of coordinate",
            day=3
        )
        
        print(f"\nIntervention Applied:")
        print(f"Type: {intervention.intervention_type.value}")
        print(f"Level: {intervention.level.value}")
        print(f"Script:\n{intervention.script_used}")
        
        # Simulate AI response
        ai_response = "database-architect, I need task/user/project schemas optimized for dashboard queries. What's your recommendation?"
        
        success = system.process_intervention_response(intervention.id, ai_response)
        print(f"\nAI Response: {ai_response}")
        print(f"Intervention Success: {success}")
    
    # Show intervention history
    history = system.get_ai_intervention_history(ai_id)
    print(f"\nIntervention History:")
    print(f"Total interventions: {history['total_interventions']}")
    print(f"Success rate: {history['success_rate']:.2%}")
    print(f"Pattern summary: {history['pattern_summary']}")
    
    # Show program recommendations
    recommendations = system.recommend_program_adjustments(ai_id, 5)
    print(f"\nProgram Adjustment Recommendations:")
    for rec in recommendations:
        print(f"- {rec}")

if __name__ == "__main__":
    main()