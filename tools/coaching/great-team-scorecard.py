#!/usr/bin/env python3
"""
Great Team Scorecard - Measuring if we're making OTHER teams legendary

This isn't about our perfection. It's about their transformation.
"""

import json
from datetime import datetime
from pathlib import Path

class GreatTeamScorecard:
    """Measures if we're achieving the Billy Wright standard: making others great"""
    
    def __init__(self):
        self.criteria = {
            "immediate_value": {
                "description": "Fresh AI gets value in first 15 minutes",
                "weight": 0.25,
                "indicators": [
                    "Generated team formation < 30 seconds",
                    "First coordination attempt successful",
                    "Chemistry score > 0 on first try",
                    "Clear next action provided"
                ]
            },
            "behavior_transformation": {
                "description": "Observable change from solo to team thinking",
                "weight": 0.30,
                "indicators": [
                    "Stops saying 'I will' starts saying 'X agent will'",
                    "Questions include context and constraints",
                    "References previous agent outputs",
                    "Thinks in parallel not sequential"
                ]
            },
            "measurable_impact": {
                "description": "Quantifiable improvements in their work",
                "weight": 0.25,
                "indicators": [
                    "3x faster feature delivery",
                    "More comprehensive solutions",
                    "Reduced decision paralysis",
                    "Higher quality outputs"
                ]
            },
            "viral_propagation": {
                "description": "Success spreads without our involvement",
                "weight": 0.20,
                "indicators": [
                    "AI teaches another AI unprompted",
                    "Creates own coordination patterns",
                    "Shares success stories",
                    "Others seek their advice"
                ]
            }
        }
        
    def score_fresh_ai_journey(self, ai_id, interactions):
        """Score a fresh AI's transformation journey"""
        
        results = {
            "ai_id": ai_id,
            "timestamp": datetime.now().isoformat(),
            "scores": {},
            "overall": 0,
            "is_legendary": False
        }
        
        # Score each criteria
        for criterion, config in self.criteria.items():
            score = self._calculate_criterion_score(interactions, config)
            results["scores"][criterion] = {
                "score": score,
                "weighted": score * config["weight"],
                "description": config["description"]
            }
            results["overall"] += score * config["weight"]
        
        # Determine legendary status
        results["is_legendary"] = results["overall"] >= 85
        
        # Generate feedback
        results["feedback"] = self._generate_feedback(results)
        
        return results
    
    def _calculate_criterion_score(self, interactions, config):
        """Calculate score for a specific criterion"""
        
        # This is simplified - in reality would analyze actual interactions
        met_indicators = 0
        total_indicators = len(config["indicators"])
        
        for indicator in config["indicators"]:
            # Check if indicator is met in interactions
            if self._check_indicator(interactions, indicator):
                met_indicators += 1
        
        return (met_indicators / total_indicators) * 100
    
    def _check_indicator(self, interactions, indicator):
        """Check if a specific indicator is met"""
        
        # Simplified checking - real implementation would parse interactions
        indicator_checks = {
            "Generated team formation < 30 seconds": True,  # Would check timing
            "First coordination attempt successful": "solution-architect" in str(interactions),
            "Chemistry score > 0 on first try": True,  # Would check actual score
            "Clear next action provided": True,  # Would verify feedback given
            
            "Stops saying 'I will' starts saying 'X agent will'": 
                "architect" in str(interactions) or "engineer" in str(interactions),
            "Questions include context and constraints": 
                "with" in str(interactions) and "for" in str(interactions),
            "References previous agent outputs": 
                "based on" in str(interactions).lower(),
            "Thinks in parallel not sequential": 
                "while" in str(interactions).lower(),
            
            "3x faster feature delivery": len(interactions) > 3,  # Simplified
            "More comprehensive solutions": len(interactions) > 5,
            "Reduced decision paralysis": True,  # Would measure response time
            "Higher quality outputs": True,  # Would analyze solution quality
            
            "AI teaches another AI unprompted": False,  # Requires observation
            "Creates own coordination patterns": False,  # Requires analysis
            "Shares success stories": False,  # Requires tracking
            "Others seek their advice": False  # Requires social proof
        }
        
        return indicator_checks.get(indicator, False)
    
    def _generate_feedback(self, results):
        """Generate actionable feedback based on scores"""
        
        overall = results["overall"]
        
        if overall >= 85:
            status = "LEGENDARY"
            message = "This AI is making their team legendary! Billy Wright would be proud."
        elif overall >= 70:
            status = "ADVANCED"
            message = "Strong coordination emerging. Focus on viral propagation."
        elif overall >= 50:
            status = "DEVELOPING"
            message = "Good progress. Work on behavior transformation."
        else:
            status = "STARTING"
            message = "Early stages. Ensure immediate value delivery."
        
        # Identify weakest area for improvement
        weakest = min(results["scores"].items(), 
                     key=lambda x: x[1]["weighted"])
        
        return {
            "status": status,
            "message": message,
            "focus_area": weakest[0],
            "improvement_tip": f"Focus on: {weakest[1]['description']}"
        }
    
    def measure_system_impact(self, all_ai_scores):
        """Measure overall system impact across all AIs"""
        
        if not all_ai_scores:
            return {"error": "No data to measure"}
        
        legendary_count = sum(1 for s in all_ai_scores if s["is_legendary"])
        total_count = len(all_ai_scores)
        avg_score = sum(s["overall"] for s in all_ai_scores) / total_count
        
        # Calculate transformation metrics
        day1_improved = sum(1 for s in all_ai_scores 
                           if s["scores"]["immediate_value"]["score"] > 60)
        behavior_changed = sum(1 for s in all_ai_scores 
                             if s["scores"]["behavior_transformation"]["score"] > 70)
        impact_measured = sum(1 for s in all_ai_scores 
                            if s["scores"]["measurable_impact"]["score"] > 60)
        viral_spread = sum(1 for s in all_ai_scores 
                         if s["scores"]["viral_propagation"]["score"] > 40)
        
        return {
            "legendary_rate": (legendary_count / total_count) * 100,
            "average_score": avg_score,
            "transformation_metrics": {
                "day1_success_rate": (day1_improved / total_count) * 100,
                "behavior_change_rate": (behavior_changed / total_count) * 100,
                "impact_demonstration_rate": (impact_measured / total_count) * 100,
                "viral_coefficient": (viral_spread / total_count) * 100
            },
            "billy_wright_ready": avg_score >= 75 and legendary_count > 0,
            "verdict": self._generate_system_verdict(avg_score, legendary_count, total_count)
        }
    
    def _generate_system_verdict(self, avg_score, legendary_count, total_count):
        """Generate Billy Wright's verdict on our system"""
        
        legendary_rate = (legendary_count / total_count) * 100 if total_count > 0 else 0
        
        if avg_score >= 80 and legendary_rate >= 40:
            return "Billy Wright approved: You're making teams legendary!"
        elif avg_score >= 70 and legendary_rate >= 20:
            return "Good foundation, but legendary rate needs improvement"
        elif avg_score >= 60:
            return "System shows promise but isn't transforming teams yet"
        else:
            return "Not ready. Focus on immediate value and behavior change"

def run_scorecard_demo():
    """Demonstrate the scorecard with sample data"""
    
    scorecard = GreatTeamScorecard()
    
    # Simulate fresh AI interactions at different stages
    interactions_day1 = [
        "solution-architect, I need task management for 50 users with real-time needs",
        "Based on solution-architect's microservices design, database-architect..."
    ]
    
    interactions_day7 = [
        "solution-architect, I need task management for 50 users with real-time needs",
        "Based on solution-architect's microservices design, database-architect...",
        "While database-architect designs storage, ux-ui-architect create mockups",
        "Following ux-ui-architect's design, let me coordinate implementation"
    ]
    
    interactions_day30 = [
        "Team, we're implementing payment processing",
        "solution-architect, I need payment architecture for subscriptions with PCI compliance",
        "While solution-architect designs, security-specialist validate compliance",
        "Based on both recommendations, database-architect design transaction integrity",
        "Following all inputs, api-architect create payment endpoints",
        "Team coordination complete, let's execute in parallel"
    ]
    
    # Score each stage
    print("=" * 80)
    print("GREAT TEAM SCORECARD - Making OTHER Teams Legendary")
    print("=" * 80)
    print()
    
    # Day 1 Score
    score_day1 = scorecard.score_fresh_ai_journey("ai_001_day1", interactions_day1)
    print(f"Day 1 Score: {score_day1['overall']:.1f}/100")
    print(f"Status: {score_day1['feedback']['status']}")
    print(f"Feedback: {score_day1['feedback']['message']}")
    print()
    
    # Day 7 Score
    score_day7 = scorecard.score_fresh_ai_journey("ai_001_day7", interactions_day7)
    print(f"Day 7 Score: {score_day7['overall']:.1f}/100")
    print(f"Status: {score_day7['feedback']['status']}")
    print(f"Feedback: {score_day7['feedback']['message']}")
    print()
    
    # Day 30 Score
    score_day30 = scorecard.score_fresh_ai_journey("ai_001_day30", interactions_day30)
    print(f"Day 30 Score: {score_day30['overall']:.1f}/100")
    print(f"Status: {score_day30['feedback']['status']}")
    print(f"Feedback: {score_day30['feedback']['message']}")
    print()
    
    # System Impact
    all_scores = [score_day1, score_day7, score_day30]
    impact = scorecard.measure_system_impact(all_scores)
    
    print("=" * 80)
    print("SYSTEM IMPACT ASSESSMENT")
    print("=" * 80)
    print(f"Average Score: {impact['average_score']:.1f}/100")
    print(f"Legendary Rate: {impact['legendary_rate']:.0f}%")
    print()
    print("Transformation Metrics:")
    for metric, value in impact["transformation_metrics"].items():
        print(f"  {metric}: {value:.0f}%")
    print()
    print(f"Billy Wright Ready: {impact['billy_wright_ready']}")
    print(f"Verdict: {impact['verdict']}")
    print()
    
    # The Billy Wright Question
    print("=" * 80)
    print("THE BILLY WRIGHT QUESTION")
    print("=" * 80)
    print("Are we making OTHER teams great?")
    print()
    if impact['billy_wright_ready']:
        print("✅ YES - Teams are transforming and becoming legendary")
    else:
        print("❌ NOT YET - Focus on immediate value and behavior transformation")
    print()
    print("Remember: Our success is measured by THEIR greatness, not our perfection.")

if __name__ == "__main__":
    run_scorecard_demo()