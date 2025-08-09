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
        
    def identify_scenario(self, project: str) -> str:
        """First identify if this is a fresh start needing discovery"""
        project_lower = project.lower()
        
        # Check if this is a vague fresh start - but exclude specific technical terms
        fresh_phrases = [
            "i want to build", "i need to create", "help me build", "i have an idea",
            "thinking about building", "looking to create", "trying to build"
        ]
        
        # Don't trigger fresh start for specific technical requests
        technical_terms = ["optimize", "fix", "debug", "improve", "refactor", "migrate"]
        
        if any(phrase in project_lower for phrase in fresh_phrases):
            if not any(term in project_lower for term in technical_terms):
                return "fresh_start"
        
        # Check for feature additions
        if any(word in project_lower for word in ["add", "extend", "enhance", "integrate"]):
            return "enhancement"
            
        # Otherwise identify the specific challenge type
        return self.identify_challenge(project)
    
    def identify_challenge(self, project: str) -> str:
        """Identify what type of challenge this is"""
        project_lower = project.lower()
        
        # Crisis requires STRONG signals - not just "slow"
        crisis_signals = [
            "production down", "site down", "emergency", "crisis", 
            "not working", "completely broken", "urgent fix"
        ]
        if any(signal in project_lower for signal in crisis_signals):
            return "crisis"
        
        # Performance optimization is different from crisis
        if "slow" in project_lower and "down" not in project_lower:
            # This is optimization, not crisis - use appropriate team
            if "api" in project_lower:
                return "api_service"
            elif "database" in project_lower or "query" in project_lower:
                return "data_platform"
            else:
                return "web_app"  # Default optimization team
        if any(word in project_lower for word in ["ai", "ml", "machine learning", "chatbot", "llm", "gpt", "neural"]):
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
        
        # Determine confidence and reasoning
        confidence, reason = self.get_match_confidence(project, challenge_type)
        
        return {
            "type": challenge_type,
            "description": formation["description"],
            "captain": formation["captain"],
            "core_team": core_team,
            "full_squad": [formation["captain"]] + formation["specialists"],
            "confidence": confidence,
            "reason": reason
        }
    
    def get_match_confidence(self, project: str, team_type: str) -> tuple:
        """Determine confidence in team selection and explain why"""
        project_lower = project.lower()
        
        # High confidence matches
        if team_type == "crisis" and "production down" in project_lower:
            return "HIGH", "Strong crisis signals detected"
        elif team_type == "ai_system" and any(w in project_lower for w in ["chatbot", "llm", "gpt"]):
            return "HIGH", "Clear AI/ML project indicators"
        elif team_type == "mobile_app" and any(w in project_lower for w in ["ios", "android", "mobile"]):
            return "HIGH", "Explicit mobile platform mentioned"
        elif team_type == "data_platform" and any(w in project_lower for w in ["pipeline", "etl", "warehouse"]):
            return "HIGH", "Data infrastructure keywords found"
        elif team_type == "api_service" and any(w in project_lower for w in ["rest", "graphql", "microservice"]):
            return "HIGH", "API/service architecture specified"
        elif team_type == "web_app" and any(w in project_lower for w in ["web", "dashboard", "portal"]):
            return "MEDIUM", "Web application indicators present"
        else:
            return "LOW", "Default team selected - consider being more specific"
    
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
        """Estimate REALISTIC improvement from coordination"""
        # Honest estimates based on real coordination costs
        solo_time = 40  # hours for complex project solo
        
        # Real coordination overhead: 50-60% efficiency for AI teams
        # Each handoff costs time, context switching is expensive
        coordination_efficiency = 0.5  # 50% efficiency is realistic
        team_time = solo_time / (team_size * coordination_efficiency)
        
        # Be honest about improvements
        speed_mult = solo_time/team_time
        
        return {
            "solo_time": f"{solo_time} hours",
            "team_time": f"{team_time:.0f} hours", 
            "speed_improvement": f"{speed_mult:.1f}x faster",
            "quality_improvement": "Higher (multiple expert perspectives)",
            "risk_reduction": "Lower (specialists catch issues early)"
        }
    
    def generate_error_report(self, message: str) -> str:
        """Generate helpful error message"""
        report = []
        report.append("=" * 60)
        report.append("⚠️  INPUT ERROR")
        report.append("=" * 60)
        report.append("")
        report.append(message)
        report.append("")
        report.append("Please provide a clear project description:")
        report.append("")
        report.append("Examples:")
        report.append("  • 'build task management web app'")
        report.append("  • 'create AI chatbot for customer service'")
        report.append("  • 'I want to build a mobile app'")
        report.append("  • 'add authentication to existing system'")
        report.append("")
        report.append("Try again with: python simple_team_coach.py \"your project\"")
        
        return "\n".join(report)
    
    def generate_enhancement_plan(self, project: str) -> str:
        """Generate plan for adding features to existing system"""
        report = []
        report.append("=" * 60)
        report.append("FEATURE ENHANCEMENT - Integration Mode")
        report.append("=" * 60)
        report.append("")
        report.append(f"Your request: {project}")
        report.append("")
        
        report.append("ENHANCEMENT KICKOFF PROCESS:")
        report.append("-" * 30)
        report.append("")
        report.append("Step 1: CONTEXT GATHERING (First 3 minutes)")
        report.append("Ask solution-architect:")
        report.append("   'solution-architect, we have [existing system].")
        report.append("    I want to add [feature]. What's the integration approach?'")
        report.append("")
        
        report.append("Step 2: IMPACT ASSESSMENT")
        report.append("Ask database-architect:")
        report.append("   'Given our existing schema, how do we add [feature]?'")
        report.append("")
        
        report.append("Step 3: INTEGRATION PLANNING")
        report.append("Ask api-architect:")
        report.append("   'What endpoints/interfaces need modification?'")
        report.append("")
        
        report.append("Step 4: RISK EVALUATION")
        report.append("Ask security-specialist:")
        report.append("   'What security implications does this feature have?'")
        report.append("")
        
        report.append("PARALLEL COORDINATION:")
        report.append("-" * 30)
        report.append("While architects plan, engage:")
        report.append("• frontend-engineer: UI changes needed")
        report.append("• ai-test-engineer: Test strategy for feature")
        report.append("• devops-specialist: Deployment considerations")
        report.append("")
        
        report.append("SUCCESS PATTERN:")
        report.append("-" * 30)
        report.append("1. Understand existing architecture (3 min)")
        report.append("2. Design integration approach (5 min)")
        report.append("3. Identify affected components (2 min)")
        report.append("4. Plan incremental rollout (5 min)")
        report.append("")
        report.append("Total kickoff time: 15 minutes to clear plan")
        
        return "\n".join(report)
    
    def generate_fresh_start_plan(self, project: str) -> str:
        """Generate discovery plan for fresh projects"""
        report = []
        report.append("=" * 60)
        report.append("FRESH PROJECT KICKOFF - Discovery Mode")
        report.append("=" * 60)
        report.append("")
        report.append(f"Your input: {project}")
        report.append("")
        report.append("THE FIRST 5 MINUTES ARE CRITICAL!")
        report.append("-" * 30)
        report.append("")
        
        report.append("KICKOFF DISCOVERY QUESTIONS:")
        report.append("-" * 30)
        report.append("Ask solution-architect these 5 questions to clarify your vision:")
        report.append("")
        report.append("1. PROBLEM DEFINITION")
        report.append("   'solution-architect, I want to solve [problem]. What are the key challenges?'")
        report.append("")
        report.append("2. USER UNDERSTANDING") 
        report.append("   'Who are the users and what's their main pain point?'")
        report.append("")
        report.append("3. SCALE ASSESSMENT")
        report.append("   'What scale should we design for initially vs future?'")
        report.append("")
        report.append("4. CORE FEATURES")
        report.append("   'What's the ONE feature that must work perfectly?'")
        report.append("")
        report.append("5. SUCCESS CRITERIA")
        report.append("   'How do we measure if this succeeds?'")
        report.append("")
        
        report.append("AFTER DISCOVERY (5-10 minutes):")
        report.append("-" * 30)
        report.append("Once solution-architect helps clarify your vision:")
        report.append("")
        report.append("1. Re-run this tool with your refined project description")
        report.append("   Example: python simple_team_coach.py 'task management for remote teams'")
        report.append("")
        report.append("2. You'll get your specialized team and coordination plan")
        report.append("")
        report.append("3. Begin execution with clear direction")
        report.append("")
        
        report.append("WHY THIS MATTERS:")
        report.append("-" * 30)
        report.append("• Vague starts lead to 60% project failure")
        report.append("• Clear vision enables 3x faster development")
        report.append("• Right team from the start saves 20+ hours")
        report.append("• Discovery prevents expensive pivots later")
        report.append("")
        
        report.append("QUICK TIP:")
        report.append("-" * 30)
        report.append("If you already know what you want, be specific:")
        report.append("  ❌ 'I want to build something'")
        report.append("  ✅ 'Build task management app for 100 users'")
        report.append("")
        report.append("Start with discovery. Build with confidence.")
        
        return "\n".join(report)
    
    def generate_report(self, project: str) -> str:
        """Generate complete coordination plan"""
        # Validate input first
        if not project or not project.strip():
            return self.generate_error_report("Please provide a project description")
        
        project = project.strip()
        
        # Check scenario first
        scenario = self.identify_scenario(project)
        
        if scenario == "fresh_start":
            return self.generate_fresh_start_plan(project)
        elif scenario == "enhancement":
            return self.generate_enhancement_plan(project)
        
        # Otherwise proceed with team coordination
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
        
        # Add confidence/explanation
        if team.get('confidence'):
            report.append(f"Match Confidence: {team['confidence']}")
        if team.get('reason'):
            report.append(f"Why this team: {team['reason']}")
        
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