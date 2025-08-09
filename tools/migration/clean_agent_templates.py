#!/usr/bin/env python3
"""
Clean Agent Templates - Remove forbidden sections while preserving valid content

This script removes Team Chemistry, Success Metrics, Manifestos, and other
forbidden sections from agent files that already have valid YAML frontmatter.
"""

import re
import os
import shutil
from pathlib import Path
from typing import List, Tuple, Optional
import argparse

class AgentTemplateCleaner:
    """Removes forbidden sections from agent templates"""
    
    def __init__(self, backup_dir: str = "backups/template-cleaning"):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Files identified as having forbidden sections
        self.files_to_clean = [
            "agents/ai-builders/context-engineer.md",
            "agents/ai-builders/orchestration-architect.md",
            "agents/ai-builders/rag-system-designer.md",
            "agents/future/a2a-mesh-controller.md",
            "agents/future/evolution-engine.md",
            "agents/future/mcp-orchestrator.md",
            "agents/future/swarm-coordinator.md",
            "agents/core/api-design-specialist.md",
            "agents/core/data-privacy-officer.md",
            "agents/core/database-architect.md",
            "agents/core/frontend-security-specialist.md",
            "agents/core/sdlc-coach.md",
            "agents/core/ux-ui-architect.md",
            "agents/creative/ux-ui-architect.md",
            "agents/security/frontend-security-specialist.md",
            "agents/project-management/delivery-manager.md",
            "agents/ai-development/prompt-engineer.md"
        ]
        
        # Sections to remove (with their subsections)
        self.forbidden_sections = [
            r'## Agent Card.*?(?=\n##|\n---|\Z)',
            r'## Team Chemistry.*?(?=\n##|\n---|\Z)',
            r'## Power Combinations.*?(?=\n##|\n---|\Z)',
            r'## Success Metrics.*?(?=\n##|\n---|\Z)',
            r'## .*?Manifesto.*?(?=\n##|\n---|\Z)',
            r'## Legendary Moments.*?(?=\n##|\n---|\Z)',
            r'## Communication Style.*?(?=\n##|\n---|\Z)',
            r'## Working Patterns.*?(?=\n##|\n---|\Z)',
            r'## Quality Gates.*?(?=\n##|\n---|\Z)',
            r'## Business Impact.*?(?=\n##|\n---|\Z)',
            r'## The .*? Way.*?(?=\n##|\n---|\Z)',
        ]
    
    def clean_file(self, file_path: str) -> Tuple[bool, str, List[str]]:
        """
        Clean a single agent file by removing forbidden sections
        
        Returns:
            (success, cleaned_content, removed_sections)
        """
        
        try:
            # Read the file
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Track what we remove
            removed_sections = []
            cleaned_content = content
            
            # Find the end of YAML frontmatter
            yaml_end_match = re.search(r'^---\s*\n.*?\n---\s*\n', content, re.DOTALL | re.MULTILINE)
            if not yaml_end_match:
                return False, content, ["No YAML frontmatter found"]
            
            yaml_end = yaml_end_match.end()
            yaml_section = content[:yaml_end]
            body_section = content[yaml_end:]
            
            # Clean each forbidden section from the body
            for pattern in self.forbidden_sections:
                matches = re.findall(pattern, body_section, re.DOTALL | re.IGNORECASE)
                if matches:
                    # Extract section name for reporting
                    section_match = re.search(r'##\s+([^\n]+)', matches[0])
                    if section_match:
                        section_name = section_match.group(1).strip()
                        removed_sections.append(section_name)
                    
                    # Remove the section
                    body_section = re.sub(pattern, '', body_section, flags=re.DOTALL | re.IGNORECASE)
            
            # Clean up excessive blank lines (more than 2 consecutive)
            body_section = re.sub(r'\n{3,}', '\n\n', body_section)
            
            # Ensure file ends with single newline
            body_section = body_section.rstrip() + '\n'
            
            # Combine YAML and cleaned body
            cleaned_content = yaml_section + body_section
            
            return True, cleaned_content, removed_sections
            
        except Exception as e:
            return False, "", [f"Error: {str(e)}"]
    
    def process_all_files(self) -> dict:
        """Process all files that need cleaning"""
        
        results = {
            'processed': 0,
            'cleaned': 0,
            'failed': 0,
            'sections_removed': 0,
            'details': []
        }
        
        for file_path in self.files_to_clean:
            if not Path(file_path).exists():
                print(f"⚠️  File not found: {file_path}")
                results['failed'] += 1
                results['details'].append({
                    'file': file_path,
                    'status': 'not_found',
                    'sections_removed': []
                })
                continue
            
            print(f"Processing: {file_path}")
            
            # Create backup
            backup_path = self.backup_dir / Path(file_path).name
            shutil.copy2(file_path, backup_path)
            
            # Clean the file
            success, cleaned_content, removed_sections = self.clean_file(file_path)
            
            if success and removed_sections:
                # Write cleaned content
                with open(file_path, 'w') as f:
                    f.write(cleaned_content)
                
                print(f"  ✅ Cleaned - Removed {len(removed_sections)} sections:")
                for section in removed_sections:
                    print(f"     - {section}")
                
                results['cleaned'] += 1
                results['sections_removed'] += len(removed_sections)
                results['details'].append({
                    'file': file_path,
                    'status': 'cleaned',
                    'sections_removed': removed_sections,
                    'backup': str(backup_path)
                })
            elif success and not removed_sections:
                print(f"  ✓ Already clean (no forbidden sections found)")
                results['details'].append({
                    'file': file_path,
                    'status': 'already_clean',
                    'sections_removed': []
                })
            else:
                print(f"  ❌ Failed: {removed_sections[0] if removed_sections else 'Unknown error'}")
                results['failed'] += 1
                results['details'].append({
                    'file': file_path,
                    'status': 'failed',
                    'error': removed_sections[0] if removed_sections else 'Unknown error'
                })
            
            results['processed'] += 1
        
        return results
    
    def validate_cleaned_files(self) -> List[Tuple[str, List[str]]]:
        """Validate that cleaned files have no forbidden sections"""
        
        validation_results = []
        
        for file_path in self.files_to_clean:
            if not Path(file_path).exists():
                continue
            
            with open(file_path, 'r') as f:
                content = f.read()
            
            violations = []
            
            # Check for any remaining forbidden patterns
            forbidden_patterns = [
                (r'##\s+Agent Card', 'Agent Card'),
                (r'##\s+Team Chemistry', 'Team Chemistry'),
                (r'##\s+Power Combinations', 'Power Combinations'),
                (r'##\s+Success Metrics', 'Success Metrics'),
                (r'##\s+.*?Manifesto', 'Manifesto'),
                (r'##\s+Legendary Moments', 'Legendary Moments'),
            ]
            
            for pattern, name in forbidden_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    violations.append(f"Still contains {name} section")
            
            if violations:
                validation_results.append((file_path, violations))
        
        return validation_results

def main():
    parser = argparse.ArgumentParser(description='Clean forbidden sections from agent templates')
    parser.add_argument('--validate-only', action='store_true',
                       help='Only validate files without cleaning')
    parser.add_argument('--file', help='Clean single file instead of all')
    
    args = parser.parse_args()
    
    cleaner = AgentTemplateCleaner()
    
    if args.validate_only:
        print("Validating agent templates...")
        print("=" * 60)
        
        violations = cleaner.validate_cleaned_files()
        
        if not violations:
            print("✅ All files are clean!")
        else:
            print(f"❌ Found violations in {len(violations)} files:")
            for file_path, file_violations in violations:
                print(f"\n{file_path}:")
                for violation in file_violations:
                    print(f"  - {violation}")
        
        return
    
    if args.file:
        # Process single file
        if args.file not in cleaner.files_to_clean:
            cleaner.files_to_clean = [args.file]
        else:
            cleaner.files_to_clean = [args.file]
    
    print("=" * 60)
    print("AGENT TEMPLATE CLEANING")
    print("=" * 60)
    print(f"Files to process: {len(cleaner.files_to_clean)}")
    print(f"Backup directory: {cleaner.backup_dir}")
    print("-" * 60)
    
    # Process all files
    results = cleaner.process_all_files()
    
    print("\n" + "=" * 60)
    print("CLEANING SUMMARY")
    print("=" * 60)
    print(f"Files processed: {results['processed']}")
    print(f"Files cleaned: {results['cleaned']}")
    print(f"Files failed: {results['failed']}")
    print(f"Total sections removed: {results['sections_removed']}")
    
    if results['cleaned'] > 0:
        print(f"\n✅ Successfully cleaned {results['cleaned']} files")
        print(f"Backups saved to: {cleaner.backup_dir}")
    
    # Validate after cleaning
    print("\n" + "-" * 60)
    print("POST-CLEANING VALIDATION")
    print("-" * 60)
    
    violations = cleaner.validate_cleaned_files()
    
    if not violations:
        print("✅ All files pass validation!")
    else:
        print(f"⚠️  {len(violations)} files still have issues:")
        for file_path, file_violations in violations:
            print(f"\n{file_path}:")
            for violation in file_violations:
                print(f"  - {violation}")

if __name__ == '__main__':
    main()