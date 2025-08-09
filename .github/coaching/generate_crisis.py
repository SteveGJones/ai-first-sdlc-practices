#!/usr/bin/env python3
"""
Generate Crisis - Create Team Coordination Crisis Scenarios

Generates crisis scenarios to test team coordination under pressure.
Like Billy Wright facing a crucial match, teams must work together.
"""

import json
import random
import sys
from pathlib import Path
from typing import Dict, List
from datetime import datetime


def generate_crisis_scenario(level: str = "BEGINNER") -> Dict:
    """Generate a crisis scenario based on difficulty level"""

    scenarios = {
        "BEGINNER": [
            {
                "title": "🔥 Production API Down",
                "description": "The main API endpoint is returning 500 errors",
                "required_agents": [
                    "api-architect",
                    "devops-specialist",
                    "critical-goal-reviewer",
                ],
                "time_limit": "30 minutes",
                "success_criteria": [
                    "Identify root cause",
                    "Deploy hotfix",
                    "Update monitoring",
                ],
            },
            {
                "title": "📊 Data Inconsistency",
                "description": "Customer data showing different values in different systems",
                "required_agents": [
                    "database-architect",
                    "data-architect",
                    "ai-test-engineer",
                ],
                "time_limit": "45 minutes",
                "success_criteria": [
                    "Identify data source conflict",
                    "Create reconciliation plan",
                    "Implement data validation",
                ],
            },
        ],
        "MODERATE": [
            {
                "title": "🚨 Security Breach Detected",
                "description": "Unusual access patterns detected in production logs",
                "required_agents": [
                    "security-specialist",
                    "devops-specialist",
                    "critical-goal-reviewer",
                    "sre-specialist",
                ],
                "time_limit": "20 minutes",
                "success_criteria": [
                    "Isolate affected systems",
                    "Audit access logs",
                    "Implement emergency patches",
                    "Create incident report",
                ],
            },
            {
                "title": "⚡ Performance Degradation",
                "description": "Response times increased 10x in the last hour",
                "required_agents": [
                    "performance-engineer",
                    "database-architect",
                    "sre-specialist",
                ],
                "time_limit": "25 minutes",
                "success_criteria": [
                    "Profile system bottlenecks",
                    "Optimize critical paths",
                    "Scale resources",
                    "Update caching strategy",
                ],
            },
        ],
        "HARD": [
            {
                "title": "💥 Multi-System Failure",
                "description": "Database, cache, and message queue all failing simultaneously",
                "required_agents": [
                    "solution-architect",
                    "database-architect",
                    "devops-specialist",
                    "sre-specialist",
                    "critical-goal-reviewer",
                ],
                "time_limit": "15 minutes",
                "success_criteria": [
                    "Establish command center",
                    "Prioritize system recovery",
                    "Coordinate parallel fixes",
                    "Implement fallback systems",
                    "Communicate with stakeholders",
                ],
            }
        ],
        "EXTREME": [
            {
                "title": "🌊 Complete Infrastructure Failure",
                "description": "Primary data center offline, customers can't access any services",
                "required_agents": [
                    "solution-architect",
                    "devops-specialist",
                    "sre-specialist",
                    "security-specialist",
                    "critical-goal-reviewer",
                    "project-plan-tracker",
                ],
                "time_limit": "10 minutes",
                "success_criteria": [
                    "Activate disaster recovery",
                    "Failover to secondary systems",
                    "Coordinate cross-team response",
                    "Maintain data integrity",
                    "Update status page",
                    "Prepare post-mortem",
                ],
            }
        ],
    }

    # Select random scenario from level
    level_scenarios = scenarios.get(level, scenarios["BEGINNER"])
    scenario = random.choice(level_scenarios)

    # Add metadata
    scenario["id"] = f"crisis_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    scenario["level"] = level
    scenario["generated_at"] = datetime.now().isoformat()

    return scenario


def create_crisis_files(scenario: Dict) -> List[str]:
    """Create crisis simulation files"""
    crisis_dir = Path(".github/crisis_scenarios")
    crisis_dir.mkdir(parents=True, exist_ok=True)

    created_files = []

    # Create scenario file
    scenario_file = crisis_dir / f"{scenario['id']}.json"
    with open(scenario_file, "w") as f:
        json.dump(scenario, f, indent=2)
    created_files.append(str(scenario_file))

    # Create markdown brief
    brief_file = crisis_dir / f"{scenario['id']}_brief.md"
    brief_content = f"""# Crisis Scenario: {scenario['title']}

## Situation
{scenario['description']}

## Time Limit
⏰ {scenario['time_limit']}

## Required Team
{', '.join(scenario['required_agents'])}

## Success Criteria
{chr(10).join(f"- [ ] {criteria}" for criteria in scenario['success_criteria'])}

## Your Mission
Coordinate as a team to resolve this crisis. Remember Billy Wright's principles:
- Communicate clearly
- Support each other
- No solo runs
- Everyone contributes

## Start Time
{datetime.now().isoformat()}

---
*Generated by Crisis Simulator*
"""

    with open(brief_file, "w") as f:
        f.write(brief_content)
    created_files.append(str(brief_file))

    return created_files


def main():
    """Main entry point for GitHub Actions"""
    # Get crisis level from arguments
    level = sys.argv[1].upper() if len(sys.argv) > 1 else "BEGINNER"

    # Validate level
    valid_levels = ["BEGINNER", "MODERATE", "HARD", "EXTREME"]
    if level not in valid_levels:
        level = "BEGINNER"

    # Generate scenario
    scenario = generate_crisis_scenario(level)

    # Create files
    files = create_crisis_files(scenario)

    # Output results
    print("=" * 60)
    print("🚨 CRISIS SCENARIO GENERATED")
    print("=" * 60)
    print(f"\n{scenario['title']}")
    print(f"Level: {scenario['level']}")
    print(f"Time Limit: {scenario['time_limit']}")

    print(f"\n📝 Scenario: {scenario['description']}")

    print("\n👥 Required Team:")
    for agent in scenario["required_agents"]:
        print(f"  - {agent}")

    print("\n✅ Success Criteria:")
    for i, criteria in enumerate(scenario["success_criteria"], 1):
        print(f"  {i}. {criteria}")

    print("\n📁 Files Created:")
    for file in files:
        print(f"  - {file}")

    print("\n" + "=" * 60)
    print("⚡ CRISIS ACTIVE - Team must respond immediately!")
    print("Remember: Coordinate, communicate, conquer together.")

    # GitHub Actions output
    if "--github-output" in sys.argv:
        print(f"::set-output name=scenario_id::{scenario['id']}")
        print(f"::set-output name=scenario_title::{scenario['title']}")
        print(f"::set-output name=time_limit::{scenario['time_limit']}")

    sys.exit(0)


if __name__ == "__main__":
    main()
