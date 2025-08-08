#!/usr/bin/env python3
"""
Verify Agent Integration - Ensure coaching system references valid agents

This script verifies that all agents referenced in fresh-ai-starter.py
actually exist in the agents directory with matching names.
"""

import os
import yaml
import re
from pathlib import Path

def get_referenced_agents():
    """Extract all agent names referenced in fresh-ai-starter.py"""
    agents = set()
    
    # Read fresh-ai-starter.py
    starter_file = Path("fresh-ai-starter.py")
    if not starter_file.exists():
        print("ERROR: fresh-ai-starter.py not found!")
        return agents
    
    content = starter_file.read_text()
    
    # Find all agent names in formations
    formations = {
        "web_app": ["solution-architect", "database-architect", "ux-ui-architect"],
        "ai_system": ["ai-solution-architect", "prompt-engineer", "ai-test-engineer"],
        "data_platform": ["data-architect", "database-architect", "performance-engineer"],
        "mobile_app": ["mobile-architect", "ux-ui-architect", "performance-engineer"],
        "api_service": ["api-architect", "database-architect", "security-specialist"]
    }
    
    for formation, team in formations.items():
        agents.update(team)
    
    # Also check chemistry measurement
    chemistry_agents = [
        "solution-architect", "database-architect", "ux-ui-architect",
        "ai-solution-architect", "prompt-engineer", "ai-test-engineer",
        "data-architect", "performance-engineer", "mobile-architect",
        "api-architect", "security-specialist"
    ]
    agents.update(chemistry_agents)
    
    return agents

def get_actual_agents():
    """Find all actual agent files and their YAML names"""
    agents_dir = Path("/Users/stevejones/Documents/Development/ai-first-sdlc-practices/agents")
    agent_map = {}
    
    if not agents_dir.exists():
        print(f"ERROR: Agents directory not found at {agents_dir}")
        return agent_map
    
    # Find all .md files
    for agent_file in agents_dir.rglob("*.md"):
        if agent_file.name == "agent-template.md":
            continue
            
        try:
            content = agent_file.read_text()
            # Extract YAML frontmatter
            if content.startswith("---"):
                yaml_end = content.find("---", 3)
                if yaml_end > 0:
                    yaml_content = content[3:yaml_end]
                    data = yaml.safe_load(yaml_content)
                    if "name" in data:
                        agent_map[data["name"]] = str(agent_file)
        except Exception as e:
            print(f"Warning: Could not parse {agent_file}: {e}")
    
    return agent_map

def verify_integration():
    """Verify all referenced agents exist"""
    print("=" * 80)
    print("AGENT INTEGRATION VERIFICATION")
    print("=" * 80)
    print()
    
    # Get referenced agents
    referenced = get_referenced_agents()
    print(f"Found {len(referenced)} agents referenced in fresh-ai-starter.py:")
    for agent in sorted(referenced):
        print(f"  - {agent}")
    print()
    
    # Get actual agents
    actual = get_actual_agents()
    print(f"Found {len(actual)} agents in agents directory")
    print()
    
    # Check for mismatches
    print("VERIFICATION RESULTS:")
    print("-" * 40)
    
    missing = []
    found = []
    
    for agent in sorted(referenced):
        if agent in actual:
            found.append(agent)
            print(f"✅ {agent:30} -> {actual[agent]}")
        else:
            missing.append(agent)
            print(f"❌ {agent:30} -> NOT FOUND!")
            
            # Check for similar names (underscore vs hyphen)
            similar = agent.replace("-", "_")
            if similar in actual:
                print(f"   ⚠️  Found similar: {similar} at {actual[similar]}")
            
            similar = agent.replace("_", "-")
            if similar in actual:
                print(f"   ⚠️  Found similar: {similar} at {actual[similar]}")
    
    print()
    print("SUMMARY:")
    print("-" * 40)
    print(f"✅ Found: {len(found)}/{len(referenced)} agents")
    print(f"❌ Missing: {len(missing)}/{len(referenced)} agents")
    
    if missing:
        print()
        print("CRITICAL FAILURES:")
        for agent in missing:
            print(f"  - {agent} is referenced but doesn't exist!")
        print()
        print("The system WILL FAIL when tested with another agent!")
        return False
    else:
        print()
        print("SUCCESS: All referenced agents exist!")
        return True

def suggest_fixes():
    """Suggest fixes for integration issues"""
    print()
    print("SUGGESTED FIXES:")
    print("-" * 40)
    print("1. Fix agent name mismatches:")
    print("   - Change 'database_architect' to 'database-architect' in agent file")
    print("   - OR update fresh-ai-starter.py to use 'database_architect'")
    print()
    print("2. Standardize naming convention:")
    print("   - Use hyphens everywhere (recommended)")
    print("   - Update all agent YAML 'name' fields to match")
    print()
    print("3. Create missing agents or update references")
    print()
    print("4. Run this verification again after fixes")

if __name__ == "__main__":
    success = verify_integration()
    
    if not success:
        suggest_fixes()
        exit(1)
    else:
        print()
        print("✅ SYSTEM IS READY FOR TESTING!")
        exit(0)