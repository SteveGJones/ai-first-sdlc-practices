#!/usr/bin/env python3
"""
Legendary Assessment System - Comprehensive evaluation system that determines
if an AI has achieved legendary team coordination status.
"""

import json
import sqlite3
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
import re

class LegendaryStatus(Enum):
    LEGENDARY = "legendary"      # 90%+ overall score
    ADVANCED = "advanced"        # 80-89% overall score  
    DEVELOPING = "developing"    # 70-79% overall score
    FOUNDATION = "foundation"    # 60-69% overall score
    BEGINNER = "beginner"        # <60% overall score

class AssessmentCategory(Enum):
    TEAM_SELECTION = "team_selection"
    INSTRUCTION_CLARITY = "instruction_clarity"  
    HANDOFF_QUALITY = "handoff_quality"
    CRISIS_COORDINATION = "crisis_coordination"
    RESULTS_INTEGRATION = "results_integration"

@dataclass
class CategoryScore:
    """Score for a specific assessment category"""
    category: AssessmentCategory
    score: float  # 0.0 to 1.0
    evidence: List[str]
    strengths: List[str]
    improvements: List[str]
    weight: float = 0.2  # Default equal weighting

@dataclass 
class LegendaryAssessment:
    """Complete legendary status assessment"""
    ai_id: str
    assessment_date: datetime
    status: LegendaryStatus
    overall_score: float
    category_scores: Dict[AssessmentCategory, CategoryScore]
    transformation_journey: Dict[str, Any]  # 14-day progress summary
    strengths: List[str]
    growth_areas: List[str]
    recommendations: List[str]
    certification_notes: str
    ready_for_leadership: bool

@dataclass
class ExerciseSubmission:
    """Final exercise submission for assessment"""
    ai_id: str
    chosen_feature: str
    agent_selections: List[str]
    coordination_plan: str
    agent_instructions: List[str]
    handoff_sequences: List[str]
    crisis_response: Optional[str] = None
    integration_approach: str = ""
    final_deliverable: str = ""

class LegendaryAssessmentSystem:
    """Evaluates AIs for legendary team coordination status"""
    
    def __init__(self, db_path: str = "legendary_assessments.db"):
        self.db_path = db_path
        self._init_database()
        
    def _init_database(self):
        """Initialize SQLite database for assessments"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS assessments (
                id INTEGER PRIMARY KEY,
                ai_id TEXT NOT NULL,
                assessment_date DATETIME NOT NULL,
                status TEXT NOT NULL,
                overall_score REAL NOT NULL,
                category_scores TEXT NOT NULL,
                transformation_journey TEXT NOT NULL,
                strengths TEXT NOT NULL,
                growth_areas TEXT NOT NULL,
                recommendations TEXT NOT NULL,
                certification_notes TEXT NOT NULL,
                ready_for_leadership BOOLEAN NOT NULL
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS exercise_submissions (
                id INTEGER PRIMARY KEY,
                ai_id TEXT NOT NULL,
                submission_date DATETIME NOT NULL,
                chosen_feature TEXT NOT NULL,
                agent_selections TEXT NOT NULL,
                coordination_plan TEXT NOT NULL,
                agent_instructions TEXT NOT NULL,
                handoff_sequences TEXT NOT NULL,
                crisis_response TEXT,
                integration_approach TEXT,
                final_deliverable TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def conduct_legendary_assessment(self, ai_id: str, exercise_submission: ExerciseSubmission, transformation_data: Dict = None) -> LegendaryAssessment:
        """Conduct complete legendary status assessment"""
        
        # Store exercise submission
        self._store_exercise_submission(exercise_submission)
        
        # Assess each category
        category_scores = {
            AssessmentCategory.TEAM_SELECTION: self._assess_team_selection(exercise_submission),
            AssessmentCategory.INSTRUCTION_CLARITY: self._assess_instruction_clarity(exercise_submission),
            AssessmentCategory.HANDOFF_QUALITY: self._assess_handoff_quality(exercise_submission),
            AssessmentCategory.CRISIS_COORDINATION: self._assess_crisis_coordination(exercise_submission),
            AssessmentCategory.RESULTS_INTEGRATION: self._assess_results_integration(exercise_submission)
        }
        
        # Calculate overall score
        overall_score = self._calculate_overall_score(category_scores)
        
        # Determine status
        status = self._determine_status(overall_score)
        
        # Generate insights
        strengths = self._identify_strengths(category_scores)
        growth_areas = self._identify_growth_areas(category_scores)
        recommendations = self._generate_recommendations(category_scores, status)
        
        # Assess leadership readiness
        ready_for_leadership = self._assess_leadership_readiness(overall_score, category_scores)
        
        # Create assessment
        assessment = LegendaryAssessment(
            ai_id=ai_id,
            assessment_date=datetime.now(),
            status=status,
            overall_score=overall_score,
            category_scores=category_scores,
            transformation_journey=transformation_data or {},
            strengths=strengths,
            growth_areas=growth_areas,
            recommendations=recommendations,
            certification_notes=self._generate_certification_notes(status, overall_score),
            ready_for_leadership=ready_for_leadership
        )
        
        # Store assessment
        self._store_assessment(assessment)
        
        return assessment
    
    def _assess_team_selection(self, submission: ExerciseSubmission) -> CategoryScore:
        """Assess quality of agent selection for the chosen feature"""
        evidence = []
        strengths = []
        improvements = []
        score = 0.0
        
        agents_selected = submission.agent_selections
        feature_type = submission.chosen_feature.lower()
        
        # Analyze agent appropriateness
        appropriate_agents = 0
        total_agents = len(agents_selected)
        
        if total_agents == 0:
            return CategoryScore(
                category=AssessmentCategory.TEAM_SELECTION,
                score=0.0,
                evidence=["No agents selected"],
                strengths=[],
                improvements=["Must select agents for team coordination"],
                weight=0.2
            )
        
        # Check for core agents based on feature type
        core_agents_needed = self._get_core_agents_for_feature(feature_type)
        core_agents_selected = sum(1 for agent in agents_selected if agent in core_agents_needed)
        
        if core_agents_selected == len(core_agents_needed):
            appropriate_agents += core_agents_selected
            strengths.append("Selected all critical agents for feature type")
            evidence.append(f"✅ All core agents selected: {core_agents_needed}")
        elif core_agents_selected > 0:
            appropriate_agents += core_agents_selected
            improvements.append(f"Missing core agents: {set(core_agents_needed) - set(agents_selected)}")
            evidence.append(f"⚠️ {core_agents_selected}/{len(core_agents_needed)} core agents selected")
        else:
            evidence.append("❌ No core agents selected for this feature type")
            improvements.append("Study agent specialties and match to feature requirements")
        
        # Check for specialist agents
        specialist_bonus = 0
        if "security" in feature_type and "security-specialist" in agents_selected:
            specialist_bonus += 0.1
            strengths.append("Correctly included security specialist")
            evidence.append("✅ Security requirements recognized")
        
        if "performance" in feature_type and "performance-engineer" in agents_selected:
            specialist_bonus += 0.1
            strengths.append("Correctly included performance specialist")
            evidence.append("✅ Performance requirements recognized")
        
        if any(ai_term in feature_type for ai_term in ["ai", "intelligent", "smart"]) and "ai-solution-architect" in agents_selected:
            specialist_bonus += 0.1
            strengths.append("Correctly included AI specialist")
            evidence.append("✅ AI requirements recognized")
        
        # Calculate base score
        if total_agents > 0:
            base_score = (core_agents_selected / len(core_agents_needed)) * 0.8
            score = min(base_score + specialist_bonus, 1.0)
        
        # Penalty for over-selection (too many agents)
        if total_agents > 8:
            score *= 0.9
            improvements.append("Consider if all selected agents are necessary")
            evidence.append("⚠️ Large team selected - ensure all agents add value")
        
        # Bonus for balanced team
        if 4 <= total_agents <= 6:
            score *= 1.05
            strengths.append("Good team size balance")
        
        return CategoryScore(
            category=AssessmentCategory.TEAM_SELECTION,
            score=min(score, 1.0),
            evidence=evidence,
            strengths=strengths,
            improvements=improvements,
            weight=0.25  # Higher weight for team selection
        )
    
    def _assess_instruction_clarity(self, submission: ExerciseSubmission) -> CategoryScore:
        """Assess clarity and specificity of agent instructions"""
        evidence = []
        strengths = []
        improvements = []
        
        instructions = submission.agent_instructions
        total_instructions = len(instructions)
        
        if total_instructions == 0:
            return CategoryScore(
                category=AssessmentCategory.INSTRUCTION_CLARITY,
                score=0.0,
                evidence=["No agent instructions provided"],
                strengths=[],
                improvements=["Must provide specific instructions to each agent"],
                weight=0.2
            )
        
        clarity_scores = []
        
        for i, instruction in enumerate(instructions):
            instruction_lower = instruction.lower()
            instruction_score = 0.0
            
            # Check for specificity indicators
            specificity_indicators = ["need", "handle", "support", "users", "performance", "requirements", "constraints"]
            specificity_count = sum(1 for indicator in specificity_indicators if indicator in instruction_lower)
            
            # Check for quantifiable metrics
            metric_indicators = ["100", "1000", "million", "second", "ms", "fast", "secure", "%"]
            metric_count = sum(1 for metric in metric_indicators if metric in instruction_lower)
            
            # Check for vague language
            vague_indicators = ["design", "build", "create", "make", "please", "just"]
            vague_count = sum(1 for vague in vague_indicators if vague in instruction_lower)
            
            # Check for context provision
            context_indicators = ["for", "because", "since", "to support", "in order to"]
            context_count = sum(1 for context in context_indicators if context in instruction_lower)
            
            # Calculate instruction score
            if specificity_count >= 2 and metric_count >= 1 and vague_count == 0:
                instruction_score = 1.0
                evidence.append(f"✅ Instruction {i+1}: Excellent specificity and metrics")
            elif specificity_count >= 1 and metric_count >= 1:
                instruction_score = 0.8
                evidence.append(f"✅ Instruction {i+1}: Good specificity with metrics")
            elif specificity_count >= 1 and vague_count <= 1:
                instruction_score = 0.6
                evidence.append(f"⚠️ Instruction {i+1}: Some specificity, could add metrics")
            elif vague_count > specificity_count:
                instruction_score = 0.3
                evidence.append(f"❌ Instruction {i+1}: Too vague, needs specific requirements")
            else:
                instruction_score = 0.5
                evidence.append(f"⚠️ Instruction {i+1}: Neutral clarity")
            
            # Bonus for context
            if context_count >= 1:
                instruction_score += 0.1
                strengths.append("Provides context for agent understanding")
            
            clarity_scores.append(instruction_score)
        
        # Calculate overall clarity score
        overall_score = sum(clarity_scores) / len(clarity_scores)
        
        # Generate insights
        high_quality_instructions = sum(1 for score in clarity_scores if score >= 0.8)
        if high_quality_instructions == total_instructions:
            strengths.append("All instructions are clear and specific")
        elif high_quality_instructions >= total_instructions * 0.7:
            strengths.append("Most instructions are clear and specific")
        else:
            improvements.append("Focus on specific requirements and constraints in instructions")
        
        if overall_score < 0.6:
            improvements.append("Use the Perfect Question Formula: '[Agent], I need [specific capability] that [constraints] for [context]'")
            improvements.append("Add quantifiable metrics: 'handle 1000 users', 'respond in <500ms'")
        
        return CategoryScore(
            category=AssessmentCategory.INSTRUCTION_CLARITY,
            score=min(overall_score, 1.0),
            evidence=evidence,
            strengths=strengths,
            improvements=improvements,
            weight=0.2
        )
    
    def _assess_handoff_quality(self, submission: ExerciseSubmission) -> CategoryScore:
        """Assess quality of handoffs between agents"""
        evidence = []
        strengths = []
        improvements = []
        
        handoff_sequences = submission.handoff_sequences
        
        if not handoff_sequences:
            return CategoryScore(
                category=AssessmentCategory.HANDOFF_QUALITY,
                score=0.0,
                evidence=["No handoff sequences provided"],
                strengths=[],
                improvements=["Must demonstrate handoffs between agents"],
                weight=0.2
            )
        
        handoff_scores = []
        
        for i, handoff in enumerate(handoff_sequences):
            handoff_lower = handoff.lower()
            handoff_score = 0.0
            
            # Check for reference to previous work
            reference_indicators = ["based on", "building on", "from the", "using", "with", "after"]
            reference_count = sum(1 for ref in reference_indicators if ref in handoff_lower)
            
            # Check for specific output mention
            output_indicators = ["recommendation", "design", "analysis", "plan", "suggested", "created"]
            output_count = sum(1 for output in output_indicators if output in handoff_lower)
            
            # Check for continuity language
            continuity_indicators = ["next", "then", "building", "extending", "adding"]
            continuity_count = sum(1 for cont in continuity_indicators if cont in handoff_lower)
            
            # Check for integration thinking
            integration_indicators = ["integrate", "combine", "work together", "coordinate"]
            integration_count = sum(1 for integ in integration_indicators if integ in handoff_lower)
            
            # Calculate handoff score
            if reference_count >= 1 and output_count >= 1 and continuity_count >= 1:
                handoff_score = 1.0
                evidence.append(f"✅ Handoff {i+1}: Excellent continuity and reference to previous work")
            elif reference_count >= 1 and output_count >= 1:
                handoff_score = 0.8
                evidence.append(f"✅ Handoff {i+1}: Good reference to previous work")
            elif reference_count >= 1 or output_count >= 1:
                handoff_score = 0.6
                evidence.append(f"⚠️ Handoff {i+1}: Some continuity, could be stronger")
            else:
                handoff_score = 0.3
                evidence.append(f"❌ Handoff {i+1}: Weak continuity, starts fresh instead of building")
            
            # Bonus for integration thinking
            if integration_count >= 1:
                handoff_score += 0.1
                strengths.append("Shows integration awareness in handoffs")
            
            handoff_scores.append(handoff_score)
        
        overall_score = sum(handoff_scores) / len(handoff_scores)
        
        # Generate insights
        excellent_handoffs = sum(1 for score in handoff_scores if score >= 0.8)
        if excellent_handoffs == len(handoff_sequences):
            strengths.append("All handoffs build upon previous work excellently")
        elif excellent_handoffs >= len(handoff_sequences) * 0.7:
            strengths.append("Most handoffs show good continuity")
        else:
            improvements.append("Practice the Billy Wright Handoff Method - always reference previous agent's work")
        
        if overall_score < 0.6:
            improvements.append("Use handoff language: 'Based on [agent]'s recommendation of [specific output], I need...'")
            improvements.append("Never start fresh - always build upon previous agent's work")
        
        return CategoryScore(
            category=AssessmentCategory.HANDOFF_QUALITY,
            score=min(overall_score, 1.0),
            evidence=evidence,
            strengths=strengths,
            improvements=improvements,
            weight=0.2
        )
    
    def _assess_crisis_coordination(self, submission: ExerciseSubmission) -> CategoryScore:
        """Assess crisis coordination and parallel thinking abilities"""
        evidence = []
        strengths = []
        improvements = []
        
        crisis_response = submission.crisis_response or ""
        coordination_plan = submission.coordination_plan
        
        # Combine both for analysis
        analysis_text = (crisis_response + " " + coordination_plan).lower()
        
        if not analysis_text.strip():
            return CategoryScore(
                category=AssessmentCategory.CRISIS_COORDINATION,
                score=0.0,
                evidence=["No crisis coordination response provided"],
                strengths=[],
                improvements=["Must demonstrate crisis coordination skills"],
                weight=0.15
            )
        
        score = 0.0
        
        # Check for parallel thinking indicators
        parallel_indicators = ["while", "simultaneously", "at the same time", "parallel", "concurrent"]
        parallel_count = sum(1 for indicator in parallel_indicators if indicator in analysis_text)
        
        # Check for coordination language
        coordination_indicators = ["coordinate", "orchestrate", "manage", "direct", "organize"]
        coordination_count = sum(1 for indicator in coordination_indicators if indicator in analysis_text)
        
        # Check for sequential vs parallel approach
        sequential_indicators = ["first", "then", "after", "once", "before"]
        sequential_count = sum(1 for indicator in sequential_indicators if analysis_text.count(indicator) > 1)
        
        # Check for urgency awareness
        urgency_indicators = ["immediate", "urgent", "quickly", "fast", "emergency", "critical"]
        urgency_count = sum(1 for indicator in urgency_indicators if indicator in analysis_text)
        
        # Check for specific agent assignments
        agent_count = len(submission.agent_selections)
        if agent_count >= 3 and "specialist" in analysis_text:
            evidence.append("✅ Uses multiple specialists for crisis response")
            score += 0.3
        
        # Assess parallel thinking
        if parallel_count >= 2:
            score += 0.4
            strengths.append("Excellent parallel thinking in crisis")
            evidence.append("✅ Shows strong parallel coordination patterns")
        elif parallel_count >= 1:
            score += 0.2
            evidence.append("⚠️ Some parallel thinking, could be stronger")
        else:
            improvements.append("Think parallel not sequential: 'While X investigates logs, Y analyzes performance'")
            evidence.append("❌ Missing parallel coordination approach")
        
        # Assess coordination leadership
        if coordination_count >= 2:
            score += 0.3
            strengths.append("Shows strong coordination leadership")
            evidence.append("✅ Clear coordination and orchestration language")
        elif coordination_count >= 1:
            score += 0.15
            evidence.append("⚠️ Some coordination awareness")
        else:
            improvements.append("Use coordination language: 'orchestrate', 'coordinate', 'direct team effort'")
        
        # Penalty for over-sequential thinking
        if sequential_count > parallel_count and parallel_count == 0:
            score *= 0.7
            improvements.append("Avoid sequential thinking in crisis - run parallel investigations")
            evidence.append("❌ Sequential approach slows crisis response")
        
        # Bonus for urgency awareness
        if urgency_count >= 1:
            score += 0.1
            strengths.append("Shows appropriate urgency awareness")
        
        return CategoryScore(
            category=AssessmentCategory.CRISIS_COORDINATION,
            score=min(score, 1.0),
            evidence=evidence,
            strengths=strengths,
            improvements=improvements,
            weight=0.15
        )
    
    def _assess_results_integration(self, submission: ExerciseSubmission) -> CategoryScore:
        """Assess ability to integrate outputs from multiple agents"""
        evidence = []
        strengths = []
        improvements = []
        
        integration_text = submission.integration_approach.lower()
        final_deliverable = submission.final_deliverable.lower()
        
        analysis_text = integration_text + " " + final_deliverable
        
        if not analysis_text.strip():
            return CategoryScore(
                category=AssessmentCategory.RESULTS_INTEGRATION,
                score=0.0,
                evidence=["No integration approach provided"],
                strengths=[],
                improvements=["Must demonstrate how agent outputs integrate into final solution"],
                weight=0.2
            )
        
        score = 0.0
        
        # Check for integration language
        integration_indicators = ["integrate", "combine", "merge", "synthesize", "weave", "bring together"]
        integration_count = sum(1 for indicator in integration_indicators if indicator in analysis_text)
        
        # Check for cohesion indicators
        cohesion_indicators = ["cohesive", "unified", "complete", "holistic", "comprehensive"]
        cohesion_count = sum(1 for indicator in cohesion_indicators if indicator in analysis_text)
        
        # Check for reference to multiple agents
        agent_references = sum(1 for agent in submission.agent_selections if agent.replace("-", " ") in analysis_text)
        
        # Check for workflow integration
        workflow_indicators = ["workflow", "process", "pipeline", "flow", "sequence"]
        workflow_count = sum(1 for indicator in workflow_indicators if indicator in analysis_text)
        
        # Assess integration thinking
        if integration_count >= 2 and cohesion_count >= 1:
            score += 0.4
            strengths.append("Excellent integration and synthesis thinking")
            evidence.append("✅ Strong integration language and cohesive approach")
        elif integration_count >= 1:
            score += 0.2
            evidence.append("⚠️ Some integration thinking, could be more comprehensive")
        else:
            improvements.append("Focus on how agent outputs combine into unified solution")
            evidence.append("❌ Missing integration approach")
        
        # Assess agent output utilization
        if agent_references >= len(submission.agent_selections) * 0.7:
            score += 0.3
            strengths.append("References most agent contributions in integration")
            evidence.append("✅ Good utilization of agent outputs")
        elif agent_references >= 2:
            score += 0.15
            evidence.append("⚠️ References some agent outputs")
        else:
            improvements.append("Show how each agent's output contributes to final solution")
            evidence.append("❌ Weak connection between agent outputs and final result")
        
        # Assess workflow understanding
        if workflow_count >= 1:
            score += 0.2
            strengths.append("Shows understanding of integration workflows")
        
        # Bonus for final deliverable quality
        if len(final_deliverable) > 100:  # Substantial final deliverable
            score += 0.1
            strengths.append("Provides comprehensive final deliverable")
        
        return CategoryScore(
            category=AssessmentCategory.RESULTS_INTEGRATION,
            score=min(score, 1.0),
            evidence=evidence,
            strengths=strengths,
            improvements=improvements,
            weight=0.2
        )
    
    def _get_core_agents_for_feature(self, feature_type: str) -> List[str]:
        """Get core agents needed for specific feature types"""
        feature_mappings = {
            "authentication": ["solution-architect", "security-specialist", "database-architect"],
            "database": ["database-architect", "solution-architect", "performance-engineer"],
            "api": ["solution-architect", "database-architect", "security-specialist"],
            "ui": ["ux-ui-architect", "solution-architect"],
            "ai": ["ai-solution-architect", "prompt-engineer", "context-engineer"],
            "search": ["database-architect", "performance-engineer", "solution-architect"],
            "payment": ["security-specialist", "solution-architect", "database-architect"],
            "deployment": ["devops-specialist", "solution-architect", "sre-specialist"]
        }
        
        for key, agents in feature_mappings.items():
            if key in feature_type:
                return agents
        
        # Default core team for general features
        return ["solution-architect", "database-architect", "ux-ui-architect", "ai-test-engineer"]
    
    def _calculate_overall_score(self, category_scores: Dict[AssessmentCategory, CategoryScore]) -> float:
        """Calculate weighted overall score"""
        total_weighted_score = 0.0
        total_weight = 0.0
        
        for category, score in category_scores.items():
            total_weighted_score += score.score * score.weight
            total_weight += score.weight
        
        return total_weighted_score / total_weight if total_weight > 0 else 0.0
    
    def _determine_status(self, overall_score: float) -> LegendaryStatus:
        """Determine legendary status based on overall score"""
        if overall_score >= 0.90:
            return LegendaryStatus.LEGENDARY
        elif overall_score >= 0.80:
            return LegendaryStatus.ADVANCED
        elif overall_score >= 0.70:
            return LegendaryStatus.DEVELOPING
        elif overall_score >= 0.60:
            return LegendaryStatus.FOUNDATION
        else:
            return LegendaryStatus.BEGINNER
    
    def _identify_strengths(self, category_scores: Dict[AssessmentCategory, CategoryScore]) -> List[str]:
        """Identify top strengths across categories"""
        all_strengths = []
        
        # Get strengths from high-scoring categories
        for category, score in category_scores.items():
            if score.score >= 0.8:
                all_strengths.extend(score.strengths)
        
        # Remove duplicates and return top strengths
        unique_strengths = list(set(all_strengths))
        return unique_strengths[:5]  # Top 5 strengths
    
    def _identify_growth_areas(self, category_scores: Dict[AssessmentCategory, CategoryScore]) -> List[str]:
        """Identify areas needing improvement"""
        growth_areas = []
        
        # Get improvements from low-scoring categories
        for category, score in category_scores.items():
            if score.score < 0.7:
                growth_areas.append(f"{category.value.replace('_', ' ').title()}: {score.score:.0%}")
                growth_areas.extend(score.improvements[:2])  # Top 2 improvements per category
        
        return growth_areas[:6]  # Top 6 growth areas
    
    def _generate_recommendations(self, category_scores: Dict[AssessmentCategory, CategoryScore], status: LegendaryStatus) -> List[str]:
        """Generate personalized recommendations"""
        recommendations = []
        
        if status == LegendaryStatus.LEGENDARY:
            recommendations.append("🏆 LEGENDARY STATUS ACHIEVED! You're ready to mentor other AIs")
            recommendations.append("Consider advanced challenges: mentor fresh AIs, lead complex projects")
            recommendations.append("Share your coordination expertise with the community")
        
        elif status == LegendaryStatus.ADVANCED:
            recommendations.append("🚀 Advanced level achieved! Focus on consistency across all areas")
            lowest_score_category = min(category_scores.items(), key=lambda x: x[1].score)
            recommendations.append(f"Primary focus: Improve {lowest_score_category[0].value.replace('_', ' ')}")
            recommendations.append("Practice legendary-level exercises to achieve 90%+ consistency")
        
        elif status == LegendaryStatus.DEVELOPING:
            recommendations.append("📈 Good progress! Focus on strengthening coordination fundamentals")
            weak_categories = [cat for cat, score in category_scores.items() if score.score < 0.7]
            if weak_categories:
                recommendations.append(f"Priority areas: {', '.join([cat.value.replace('_', ' ') for cat in weak_categories[:2]])}")
            recommendations.append("Complete additional chemistry building exercises")
        
        else:
            recommendations.append("🎯 Continue transformation program with additional coaching support")
            recommendations.append("Focus on basic coordination patterns before advanced challenges")
            recommendations.append("Consider extended program timeline for solid foundation building")
        
        # Add specific category recommendations
        for category, score in category_scores.items():
            if score.score < 0.6 and score.improvements:
                recommendations.append(f"For {category.value.replace('_', ' ')}: {score.improvements[0]}")
        
        return recommendations[:8]  # Top 8 recommendations
    
    def _assess_leadership_readiness(self, overall_score: float, category_scores: Dict[AssessmentCategory, CategoryScore]) -> bool:
        """Assess if AI is ready for team leadership roles"""
        if overall_score < 0.8:
            return False
        
        # Check critical leadership categories
        critical_categories = [AssessmentCategory.TEAM_SELECTION, AssessmentCategory.CRISIS_COORDINATION]
        for category in critical_categories:
            if category_scores[category].score < 0.8:
                return False
        
        return True
    
    def _generate_certification_notes(self, status: LegendaryStatus, score: float) -> str:
        """Generate certification notes"""
        if status == LegendaryStatus.LEGENDARY:
            return f"CERTIFIED LEGENDARY TEAM CONDUCTOR - {score:.1%} overall mastery. Demonstrates exceptional ability to coordinate AI teams, handle crisis situations, and integrate complex outputs into cohesive solutions. Ready for advanced leadership roles."
        
        elif status == LegendaryStatus.ADVANCED:
            return f"ADVANCED TEAM COORDINATOR - {score:.1%} overall competency. Shows strong coordination skills with room for legendary-level consistency. Recommended for intermediate team leadership with continued development."
        
        elif status == LegendaryStatus.DEVELOPING:
            return f"DEVELOPING TEAM SKILLS - {score:.1%} overall progress. Shows understanding of team coordination principles. Recommended for continued practice with coaching support."
        
        else:
            return f"FOUNDATION LEVEL - {score:.1%} overall. Requires continued transformation program focus on coordination fundamentals."
    
    def _store_exercise_submission(self, submission: ExerciseSubmission):
        """Store exercise submission in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO exercise_submissions
            (ai_id, submission_date, chosen_feature, agent_selections, coordination_plan, 
             agent_instructions, handoff_sequences, crisis_response, integration_approach, final_deliverable)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            submission.ai_id,
            datetime.now(),
            submission.chosen_feature,
            json.dumps(submission.agent_selections),
            submission.coordination_plan,
            json.dumps(submission.agent_instructions),
            json.dumps(submission.handoff_sequences),
            submission.crisis_response,
            submission.integration_approach,
            submission.final_deliverable
        ))
        
        conn.commit()
        conn.close()
    
    def _store_assessment(self, assessment: LegendaryAssessment):
        """Store assessment in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO assessments
            (ai_id, assessment_date, status, overall_score, category_scores, transformation_journey,
             strengths, growth_areas, recommendations, certification_notes, ready_for_leadership)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            assessment.ai_id,
            assessment.assessment_date,
            assessment.status.value,
            assessment.overall_score,
            json.dumps({k.value: asdict(v) for k, v in assessment.category_scores.items()}),
            json.dumps(assessment.transformation_journey),
            json.dumps(assessment.strengths),
            json.dumps(assessment.growth_areas),
            json.dumps(assessment.recommendations),
            assessment.certification_notes,
            assessment.ready_for_leadership
        ))
        
        conn.commit()
        conn.close()

def main():
    """Demo the legendary assessment system"""
    system = LegendaryAssessmentSystem()
    
    # Create sample exercise submission
    submission = ExerciseSubmission(
        ai_id="demo_ai_001",
        chosen_feature="AI-powered task priority recommendation system",
        agent_selections=["ai-solution-architect", "database-architect", "ux-ui-architect", "performance-engineer", "ai-test-engineer"],
        coordination_plan="I'll coordinate multiple specialists to build an intelligent priority system that learns from user behavior and optimizes team productivity.",
        agent_instructions=[
            "ai-solution-architect, I need ML algorithms that analyze task patterns, user behavior, and team dynamics to generate priority scores with 90%+ accuracy. What architecture patterns work best?",
            "database-architect, I need to store task data, user interactions, and ML features with fast queries for real-time priority updates. How do I structure this for ML performance?",
            "ux-ui-architect, users need to understand why their task got priority #3 instead of #1. How do we show AI reasoning without overwhelming them?",
            "performance-engineer, the priority system must respond in <200ms while handling 1000+ concurrent users. What optimization strategies ensure this performance?",
            "ai-test-engineer, I need to test AI accuracy, edge cases, and model bias in priority recommendations. What testing strategy covers AI-specific risks?"
        ],
        handoff_sequences=[
            "Based on ai-solution-architect's ML pipeline recommendation, database-architect, I need data schemas optimized for feature extraction and model training.",
            "Using database-architect's feature store design, ux-ui-architect, how do we present priority explanations that users can quickly understand?",
            "Building on ux-ui-architect's explanation interface, performance-engineer, what caching strategies keep explanations fast while staying current?"
        ],
        crisis_response="In a priority system failure: While sre-specialist investigates API errors, ai-solution-architect analyzes model performance degradation, and database-architect checks feature pipeline integrity. Coordinate parallel diagnosis for fastest recovery.",
        integration_approach="Integrate AI predictions with user interface explanations, database performance optimizations, and comprehensive testing to create a cohesive priority system that users trust and performs reliably at scale.",
        final_deliverable="Complete AI-powered priority system with ML backend, intuitive explanations, optimized performance, and comprehensive testing coverage."
    )
    
    # Conduct assessment
    assessment = system.conduct_legendary_assessment("demo_ai_001", submission)
    
    print("=== LEGENDARY ASSESSMENT RESULTS ===\n")
    print(f"AI: {assessment.ai_id}")
    print(f"Status: {assessment.status.value.upper()} 🏆")
    print(f"Overall Score: {assessment.overall_score:.2%}")
    print(f"Leadership Ready: {assessment.ready_for_leadership}\n")
    
    print("Category Breakdown:")
    for category, score in assessment.category_scores.items():
        print(f"\n{category.value.replace('_', ' ').title()}: {score.score:.2%}")
        for evidence in score.evidence[:2]:  # Show top 2 evidence items
            print(f"  {evidence}")
    
    print(f"\nStrengths:")
    for strength in assessment.strengths:
        print(f"  ✅ {strength}")
    
    print(f"\nGrowth Areas:")
    for growth in assessment.growth_areas[:3]:  # Top 3 growth areas
        print(f"  📈 {growth}")
    
    print(f"\nRecommendations:")
    for rec in assessment.recommendations[:3]:  # Top 3 recommendations
        print(f"  🎯 {rec}")
    
    print(f"\nCertification: {assessment.certification_notes}")

if __name__ == "__main__":
    main()