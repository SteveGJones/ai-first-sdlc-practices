#!/usr/bin/env python3
"""
Automatic Team Assembly System - FORCES TEAM ENGAGEMENT

This system automatically triggers team assembly for ALL significant actions.
It makes solo work impossible by requiring team engagement at every step.

ZERO SOLO WORK: Every action must involve the appropriate team of specialists.
"""

import argparse
import sys
import os
from pathlib import Path
from typing import List, Dict, Set
from datetime import datetime
import re


class AutoTeamAssembly:
    """Automatically assembles teams for different types of work"""
    
    def __init__(self):
        self.team_configurations = {
            'feature_development': {
                'mandatory': ['sdlc-enforcer', 'solution-architect', 'critical-goal-reviewer'],
                'conditional': {
                    'has_api': ['api-designer', 'integration-orchestrator'],
                    'has_database': ['database-architect', 'data-engineer'],
                    'has_ui': ['ux-architect', 'frontend-specialist'],
                    'has_performance': ['performance-engineer', 'monitoring-specialist'],
                    'has_security': ['security-specialist', 'compliance-auditor']
                }
            },
            'bug_fixing': {
                'mandatory': ['debugging-specialist', 'test-engineer', 'regression-analyst'],
                'conditional': {
                    'performance_bug': ['performance-engineer', 'profiling-specialist'],
                    'security_bug': ['security-specialist', 'vulnerability-analyst'],
                    'ui_bug': ['frontend-specialist', 'ux-architect'],
                    'data_bug': ['database-architect', 'data-validation-specialist']
                }
            },
            'architecture_change': {
                'mandatory': ['solution-architect', 'system-architect', 'integration-orchestrator'],
                'conditional': {
                    'database_change': ['database-architect', 'migration-specialist'],
                    'api_change': ['api-designer', 'versioning-specialist'],
                    'security_change': ['security-architect', 'compliance-auditor'],
                    'performance_change': ['performance-architect', 'scalability-specialist']
                }
            },
            'deployment': {
                'mandatory': ['devops-specialist', 'sre-specialist', 'monitoring-specialist'],
                'conditional': {
                    'production_deployment': ['release-manager', 'rollback-specialist'],
                    'security_deployment': ['security-operations', 'compliance-auditor'],
                    'database_deployment': ['database-administrator', 'migration-specialist']
                }
            },
            'documentation': {
                'mandatory': ['documentation-architect', 'technical-writer'],
                'conditional': {
                    'api_docs': ['api-documentation-specialist', 'integration-specialist'],
                    'architecture_docs': ['solution-architect', 'system-architect'],
                    'user_docs': ['ux-writer', 'user-experience-specialist']
                }
            },
            'testing': {
                'mandatory': ['test-engineer', 'quality-assurance-specialist'],
                'conditional': {
                    'performance_testing': ['performance-test-engineer', 'load-test-specialist'],
                    'security_testing': ['security-test-engineer', 'penetration-tester'],
                    'integration_testing': ['integration-test-specialist', 'end-to-end-tester']
                }
            },
            'refactoring': {
                'mandatory': ['solution-architect', 'code-quality-analyst', 'test-engineer'],
                'conditional': {
                    'performance_refactoring': ['performance-engineer', 'optimization-specialist'],
                    'security_refactoring': ['security-specialist', 'code-security-analyst'],
                    'database_refactoring': ['database-architect', 'query-optimization-specialist']
                }
            }
        }
        
        self.work_type_patterns = {
            'feature_development': [
                r'implement.*feature', r'add.*functionality', r'create.*component',
                r'build.*system', r'develop.*module', r'new.*feature'
            ],
            'bug_fixing': [
                r'fix.*bug', r'resolve.*issue', r'patch.*problem',
                r'debug.*error', r'troubleshoot.*issue', r'repair.*defect'
            ],
            'architecture_change': [
                r'architecture.*change', r'system.*design', r'refactor.*architecture',
                r'redesign.*system', r'architectural.*decision', r'design.*pattern'
            ],
            'deployment': [
                r'deploy.*to', r'release.*version', r'production.*deployment',
                r'staging.*deployment', r'rollout.*update', r'ship.*feature'
            ],
            'documentation': [
                r'document.*', r'write.*docs', r'update.*documentation',
                r'create.*guide', r'api.*documentation', r'user.*manual'
            ],
            'testing': [
                r'test.*', r'write.*tests', r'unit.*test',
                r'integration.*test', r'e2e.*test', r'quality.*assurance'
            ],
            'refactoring': [
                r'refactor.*', r'cleanup.*code', r'improve.*structure',
                r'optimize.*code', r'restructure.*', r'code.*improvement'
            ]
        }
    
    def detect_work_type(self, description: str) -> str:
        """Detect the type of work from description"""
        description_lower = description.lower()
        
        for work_type, patterns in self.work_type_patterns.items():
            for pattern in patterns:
                if re.search(pattern, description_lower):
                    return work_type
        
        # Default to feature development if no specific type detected
        return 'feature_development'
    
    def detect_context_conditions(self, description: str, project_files: List[str]) -> Set[str]:
        """Detect context conditions that require additional specialists"""
        conditions = set()
        description_lower = description.lower()
        
        # API-related conditions
        if any(keyword in description_lower for keyword in ['api', 'endpoint', 'rest', 'graphql']):
            conditions.add('has_api')
        
        # Database conditions
        if any(keyword in description_lower for keyword in ['database', 'sql', 'query', 'migration']):
            conditions.add('has_database')
        
        # UI conditions
        if any(keyword in description_lower for keyword in ['ui', 'frontend', 'component', 'interface']):
            conditions.add('has_ui')
        
        # Performance conditions
        if any(keyword in description_lower for keyword in ['performance', 'optimization', 'speed', 'latency']):
            conditions.add('has_performance')
        
        # Security conditions
        if any(keyword in description_lower for keyword in ['security', 'auth', 'permission', 'encryption']):
            conditions.add('has_security')
        
        # Check project files for additional context
        for file_path in project_files:
            file_lower = file_path.lower()
            if any(ext in file_lower for ext in ['.sql', '.db', 'migration']):
                conditions.add('has_database')
            if any(ext in file_lower for ext in ['.html', '.css', '.js', '.tsx', '.vue']):
                conditions.add('has_ui')
            if 'test' in file_lower:
                conditions.add('performance_testing')
        
        return conditions
    
    def assemble_team(self, work_type: str, description: str = "") -> Dict[str, List[str]]:
        """Assemble the required team for the work type"""
        if work_type not in self.team_configurations:
            work_type = 'feature_development'  # Default fallback
        
        config = self.team_configurations[work_type]
        team = {
            'mandatory': config['mandatory'].copy(),
            'recommended': [],
            'optional': []
        }
        
        # Get project files for context
        project_files = []
        try:
            for file_path in Path('.').rglob('*'):
                if file_path.is_file() and not str(file_path).startswith('.git'):
                    project_files.append(str(file_path))
        except (OSError, PermissionError):
            pass
        
        # Detect conditions and add conditional specialists
        conditions = self.detect_context_conditions(description, project_files)
        
        for condition in conditions:
            if condition in config.get('conditional', {}):
                team['recommended'].extend(config['conditional'][condition])
        
        # Remove duplicates
        team['mandatory'] = list(set(team['mandatory']))
        team['recommended'] = list(set(team['recommended']))
        
        return team
    
    def generate_team_assembly_script(self, work_type: str, description: str) -> str:
        """Generate a script that forces team engagement"""
        team = self.assemble_team(work_type, description)
        
        script = f"""
# AUTOMATIC TEAM ASSEMBLY FOR: {work_type.upper()}
# Description: {description}
# Generated: {datetime.now().isoformat()}

echo "🚨 AUTOMATIC TEAM ASSEMBLY TRIGGERED"
echo "🚨 SOLO WORK IS FORBIDDEN - ENGAGING TEAM"
echo ""
echo "Work Type: {work_type}"
echo "Description: {description}"
echo ""

# MANDATORY TEAM MEMBERS (MUST BE ENGAGED):
"""
        
        for agent in team['mandatory']:
            script += f"""
echo "✅ ENGAGING MANDATORY SPECIALIST: {agent}"
echo "   → {agent}: Required for {work_type}"
"""
        
        if team['recommended']:
            script += """
# RECOMMENDED TEAM MEMBERS (HIGHLY SUGGESTED):
"""
            for agent in team['recommended']:
                script += f"""
echo "⭐ RECOMMENDING SPECIALIST: {agent}"
echo "   → {agent}: Recommended based on work context"
"""
        
        script += """
echo ""
echo "🔒 WORK BLOCKED UNTIL TEAM ENGAGEMENT CONFIRMED"
echo "🔒 USE: python tools/validation/validate-team-engagement.py --strict"
echo "🔒 BEFORE PROCEEDING WITH ANY WORK"
echo ""

# Validate team engagement before allowing work
echo "Running team engagement validation..."
python tools/validation/validate-team-engagement.py --strict

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ TEAM ENGAGEMENT VALIDATION FAILED"
    echo "❌ ALL WORK IS BLOCKED UNTIL TEAM IS PROPERLY ENGAGED"
    echo "❌ NO SOLO WORK PERMITTED"
    exit 1
fi

echo ""
echo "✅ TEAM ENGAGEMENT VALIDATED - WORK MAY PROCEED"
echo "✅ REMEMBER: ALL DECISIONS MUST INVOLVE THE TEAM"
"""
        
        return script
    
    def create_team_engagement_blocker(self, description: str) -> bool:
        """Create a script that blocks solo work and forces team engagement"""
        work_type = self.detect_work_type(description)
        script = self.generate_team_assembly_script(work_type, description)
        
        # Create the blocker script
        blocker_path = Path('.') / 'team-engagement-blocker.sh'
        try:
            blocker_path.write_text(script)
            os.chmod(blocker_path, 0o755)  # Make executable
            
            print(f"🔒 TEAM ENGAGEMENT BLOCKER CREATED: {blocker_path}")
            print("🔒 RUN THIS SCRIPT BEFORE ANY WORK:")
            print("🔒 ./team-engagement-blocker.sh")
            
            return True
        except Exception as e:
            print(f"❌ Failed to create team engagement blocker: {e}")
            return False
    
    def check_current_engagement(self) -> bool:
        """Check if team is currently properly engaged"""
        # Run the team engagement validator
        try:
            import subprocess
            result = subprocess.run(['python', 'tools/validation/validate-team-engagement.py', '--strict'],
                                 capture_output=True, text=True)
            return result.returncode == 0
        except (OSError, subprocess.SubprocessError):
            print("⚠️  Could not validate team engagement")
            return False
    
    def force_team_consultation(self, work_description: str) -> None:
        """Force team consultation before any work can proceed"""
        print("🚨 AUTOMATIC TEAM CONSULTATION REQUIRED")
        print("=" * 50)
        print(f"Work Description: {work_description}")
        print("")
        
        work_type = self.detect_work_type(work_description)
        team = self.assemble_team(work_type, work_description)
        
        print(f"Detected Work Type: {work_type}")
        print("")
        print("MANDATORY TEAM CONSULTATION REQUIRED:")
        
        for agent in team['mandatory']:
            print(f"  🔴 {agent} - MUST BE CONSULTED")
        
        if team['recommended']:
            print("\nRECOMMENDED ADDITIONAL CONSULTATION:")
            for agent in team['recommended']:
                print(f"  🟡 {agent} - SHOULD BE CONSULTED")
        
        print("")
        print("🚫 NO WORK CAN PROCEED WITHOUT PROPER TEAM ENGAGEMENT")
        print("🚫 SOLO WORK IS ABSOLUTELY FORBIDDEN")
        print("")
        print("NEXT STEPS:")
        print("1. Engage each mandatory specialist")
        print("2. Document their input and approval")
        print("3. Run: python tools/validation/validate-team-engagement.py --strict")
        print("4. Only proceed if validation passes")


def main():
    parser = argparse.ArgumentParser(description='Automatic team assembly system')
    parser.add_argument('description', help='Description of work to be done')
    parser.add_argument('--create-blocker', action='store_true',
                       help='Create team engagement blocker script')
    parser.add_argument('--check-engagement', action='store_true',
                       help='Check current team engagement status')
    parser.add_argument('--force-consultation', action='store_true',
                       help='Force team consultation display')
    
    args = parser.parse_args()
    
    assembler = AutoTeamAssembly()
    
    if args.check_engagement:
        if assembler.check_current_engagement():
            print("✅ TEAM PROPERLY ENGAGED")
            sys.exit(0)
        else:
            print("❌ TEAM ENGAGEMENT INSUFFICIENT")
            print("❌ WORK MUST BE BLOCKED")
            sys.exit(1)
    
    if args.force_consultation:
        assembler.force_team_consultation(args.description)
        sys.exit(1)  # Block work until team is engaged
    
    if args.create_blocker:
        if assembler.create_team_engagement_blocker(args.description):
            print("✅ Team engagement blocker created successfully")
            sys.exit(0)
        else:
            print("❌ Failed to create team engagement blocker")
            sys.exit(1)
    
    # Default: show team assembly requirements
    work_type = assembler.detect_work_type(args.description)
    team = assembler.assemble_team(work_type, args.description)
    
    print(f"WORK TYPE: {work_type}")
    print(f"DESCRIPTION: {args.description}")
    print("")
    print("REQUIRED TEAM:")
    for agent in team['mandatory']:
        print(f"  🔴 {agent}")
    
    if team['recommended']:
        print("\nRECOMMENDED:")
        for agent in team['recommended']:
            print(f"  🟡 {agent}")


if __name__ == '__main__':
    main()