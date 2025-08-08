#!/usr/bin/env python3
"""
Simple Team Coach - Coordinate AI specialists for better results

The simplest way to get AI teams working together.
No complexity. Just coordination that works.

Usage:
    python simple_team_coach.py "your project description"
    
Example:
    python simple_team_coach.py "build a task management app"
    
This gives you:
    1. The right team for your project
    2. How to coordinate them
    3. What results to expect
"""

import sys
from typing import List, Dict, Tuple

class SimpleTeamCoach:
    """Dead simple AI team coordination. Works every time."""
    
    def __init__(self):
        # Each formation has a captain (Billy Wright role) and specialists
        self.formations = {
            "web_app": {
                "captain": "solution-architect",
                "specialists": ["database-architect", "api-architect", "frontend-engineer", "backend-engineer"],
                "description": "Full-stack web application team"
            },
            "ai_system": {
                "captain": "ai-solution-architect", 
                "specialists": ["prompt-engineer", "ai-test-engineer", "context-engineer"],
                "description": "AI/ML system development team"
            },
            "mobile_app": {
                "captain": "mobile-architect",
                "specialists": ["ux-ui-architect", "api-architect", "performance-engineer"],
                "description": "Mobile application team"
            },
            "api_service": {
                "captain": "api-architect",
                "specialists": ["database-architect", "security-specialist", "backend-engineer"],
                "description": "API/microservice team"
            },
            "data_platform": {
                "captain": "data-architect",
                "specialists": ["database-architect", "performance-engineer", "devops-specialist"],
                "description": "Data platform and analytics team"
            },
            "crisis": {
                "captain": "sre-specialist",
                "specialists": ["performance-engineer", "database-architect", "security-specialist"],
                "description": "Production crisis response team"
            }
        }
        
    def identify_challenge(self, project: str) -> str:
        """Identify what type of challenge this is"""
        project_lower = project.lower()
        
        # Simple keyword matching - ORDER MATTERS
        if any(word in project_lower for word in ["crisis", "down", "slow", "broken", "emergency"]):
            return "crisis"
        elif any(word in project_lower for word in ["ai", "ml", "machine learning", "chatbot", "llm"]):
            return "ai_system"
        elif any(word in project_lower for word in ["mobile", "ios", "android", "iphone", "native app"]):
            return "mobile_app"
        elif any(word in project_lower for word in ["data", "analytics", "warehouse", "pipeline", "etl"]):
            return "data_platform"
        elif any(word in project_lower for word in ["api", "microservice", "rest", "graphql", "endpoint"]):
            return "api_service"
        elif any(word in project_lower for word in ["web", "website", "webapp", "dashboard", "portal", "task", "management"]):
            return "web_app"
        else:
            return "web_app"  # Default for general projects
    
    def get_team(self, project: str) -> Dict:
        """Get the right team for the challenge"""
        challenge_type = self.identify_challenge(project)
        formation = self.formations[challenge_type]
        
        # Build the core team (captain + 3 key specialists)
        core_team = [formation["captain"]] + formation["specialists"][:3]
        
        return {
            "type": challenge_type,
            "description": formation["description"],
            "captain": formation["captain"],
            "core_team": core_team,
            "full_squad": [formation["captain"]] + formation["specialists"]
        }
    
    def get_coordination_plan(self, team: Dict, project: str) -> List[str]:
        """Get simple coordination steps"""
        captain = team["captain"]
        specialists = team["core_team"][1:]  # Everyone except captain
        
        steps = [
            f"Step 1: Ask {captain}",
            f"   '{captain}, I need {project}. What's the best approach?'",
            "",
            f"Step 2: Coordinate specialists based on {captain}'s approach"
        ]
        
        for specialist in specialists:
            steps.append(f"   'Based on that, {specialist}, what's your part?'")
        
        steps.extend([
            "",
            "Step 3: Integrate responses",
            f"   'Team, based on all inputs, here's the plan...'",
            "",
            "Step 4: Execute with coordination",
            "   Each specialist works their part in parallel"
        ])
        
        return steps
    
    def estimate_improvement(self, team_size: int) -> Dict:
        """Estimate improvement from coordination"""
        # Simple but realistic estimates
        solo_time = 40  # hours for complex project solo
        team_time = 40 / (team_size * 0.7)  # Accounting for coordination overhead
        
        return {
            "solo_time": f"{solo_time} hours",
            "team_time": f"{team_time:.0f} hours", 
            "speed_improvement": f"{solo_time/team_time:.1f}x faster",
            "quality_improvement": "Higher (multiple expert perspectives)",
            "risk_reduction": "Lower (specialists catch issues early)"
        }
    
    def generate_report(self, project: str) -> str:
        """Generate complete coordination plan"""
        team = self.get_team(project)
        steps = self.get_coordination_plan(team, project)
        improvement = self.estimate_improvement(len(team["core_team"]))
        
        report = []
        report.append("=" * 60)
        report.append("AI TEAM COORDINATION PLAN")
        report.append("=" * 60)
        report.append("")
        report.append(f"Project: {project}")
        report.append(f"Team Type: {team['description']}")
        report.append("")
        
        report.append("YOUR CORE TEAM:")
        report.append("-" * 30)
        report.append(f"Captain: {team['captain']} (sets strategy)")
        for specialist in team['core_team'][1:]:
            report.append(f"Specialist: {specialist}")
        report.append("")
        
        report.append("COORDINATION STEPS:")
        report.append("-" * 30)
        for step in steps:
            report.append(step)
        report.append("")
        
        report.append("EXPECTED IMPROVEMENTS:")
        report.append("-" * 30)
        report.append(f"Solo approach: {improvement['solo_time']}")
        report.append(f"Team approach: {improvement['team_time']}")
        report.append(f"Speed: {improvement['speed_improvement']}")
        report.append(f"Quality: {improvement['quality_improvement']}")
        report.append(f"Risk: {improvement['risk_reduction']}")
        report.append("")
        
        report.append("QUICK START:")
        report.append("-" * 30)
        report.append(f"1. Copy this exact question:")
        report.append(f"   '{team['captain']}, I need {project}. What's the best approach?'")
        report.append(f"2. Use the response to coordinate your specialists")
        report.append(f"3. Integrate their inputs into a complete solution")
        report.append("")
        
        report.append("That's it. Simple coordination. Better results.")
        
        return "\n".join(report)

def main():
    """Simple CLI interface"""
    if len(sys.argv) < 2:
        print("Simple Team Coach - AI Team Coordination Made Easy")
        print()
        print("Usage:")
        print("  python simple_team_coach.py 'your project description'")
        print()
        print("Examples:")
        print("  python simple_team_coach.py 'build a task management app'")
        print("  python simple_team_coach.py 'create an AI chatbot'")
        print("  python simple_team_coach.py 'fix slow database queries'")
        print()
        print("This tool helps you:")
        print("  1. Pick the right AI specialist team")
        print("  2. Coordinate them effectively")
        print("  3. Get better results faster")
        return
    
    project = " ".join(sys.argv[1:])
    coach = SimpleTeamCoach()
    report = coach.generate_report(project)
    print(report)

if __name__ == "__main__":
    main()