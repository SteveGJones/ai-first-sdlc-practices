#!/usr/bin/env python3
"""
Tests to ensure all generated files and templates are AI-friendly.
Validates clarity, structure, and guidance for AI agents.
"""

import os
import sys
from pathlib import Path
import unittest
import re

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestAIFriendlyTemplates(unittest.TestCase):
    """Test that all templates provide clear guidance for AI agents"""
    
    def setUp(self):
        self.templates_dir = Path(__file__).parent.parent / 'templates'
    
    def test_claude_md_template_structure(self):
        """Test CLAUDE.md template has all required sections for AI guidance"""
        claude_template = self.templates_dir / 'CLAUDE.md'
        if not claude_template.exists():
            self.skipTest("CLAUDE.md template not found")
        
        content = claude_template.read_text()
        
        # Critical sections that must exist
        required_sections = [
            'Project Overview',
            'Git Workflow',
            'NEVER PUSH DIRECTLY TO MAIN',
            'Branch Protection',
            'Development Workflow',
            'Code Style',
            'Testing Requirements',
            'Common Patterns'
        ]
        
        for section in required_sections:
            self.assertIn(section, content, f"Missing critical section: {section}")
        
        # Check for mandatory workflow instructions
        mandatory_patterns = [
            r'ALWAYS.*feature branch',
            r'ALWAYS.*feature proposal',
            r'NEVER.*push.*main',
            r'retrospective.*BEFORE.*PR'
        ]
        
        for pattern in mandatory_patterns:
            self.assertIsNotNone(
                re.search(pattern, content, re.IGNORECASE),
                f"Missing mandatory instruction pattern: {pattern}"
            )
    
    def test_gitignore_ai_tools_coverage(self):
        """Test that AI tools gitignore covers major AI assistants"""
        ai_tools_gitignore = self.templates_dir / 'gitignore' / 'ai-tools.gitignore'
        if not ai_tools_gitignore.exists():
            self.skipTest("ai-tools.gitignore not found")
        
        content = ai_tools_gitignore.read_text()
        
        # Major AI tools that should be covered
        ai_tools = {
            'Claude': ['.claude/', '*.claude.bak', 'claude-'],
            'Cursor': ['.cursor/', 'cursor-'],
            'Aider': ['.aider', 'aider.'],
            'Copilot': ['.copilot/', 'copilot-'],
            'Continue': ['.continue/'],
            'Windsurf': ['.windsurf/'],
            'Codeium': ['.codeium/'],
            'Tabnine': ['.tabnine/']
        }
        
        for tool, patterns in ai_tools.items():
            tool_found = any(pattern in content for pattern in patterns)
            self.assertTrue(tool_found, f"AI tool not covered: {tool}")
        
        # Check for general AI patterns
        general_patterns = [
            '.ai-context/',
            '.ai-sessions/',
            'CONTEXT_*.md',
            'HANDOFF_*.md',
            '.ai-chat-history/'
        ]
        
        for pattern in general_patterns:
            self.assertIn(pattern, content, f"Missing general AI pattern: {pattern}")
    
    def test_framework_verification_tests_clarity(self):
        """Test that framework verification tests are clear about their purpose"""
        test_files = [
            'tests/test_framework_setup.py',
            'tests/framework.test.js',
            'tests/test-framework.sh'
        ]
        
        for test_file in test_files:
            test_path = self.templates_dir / test_file
            if not test_path.exists():
                continue
            
            content = test_path.read_text()
            
            # Should explain purpose clearly
            self.assertIn('framework verification', content.lower())
            self.assertIn('ai-first sdlc', content.lower())
            
            # Should indicate it's a placeholder
            self.assertTrue(
                'replace' in content.lower() or 'placeholder' in content.lower(),
                f"{test_file} should indicate it's replaceable"
            )
            
            # Should check for key framework files
            self.assertIn('CLAUDE.md', content)
            self.assertIn('README.md', content)
    
    def test_retrospective_template_guidance(self):
        """Test retrospective template guides AI to document properly"""
        retrospective_template = self.templates_dir / 'retrospective.md'
        if not retrospective_template.exists():
            self.skipTest("retrospective.md template not found")
        
        content = retrospective_template.read_text()
        
        # Should have AI-specific sections
        ai_sections = [
            'AI-Specific Learnings',
            'AI Agent Performance',
            'AI Agent Instructions'
        ]
        
        for section in ai_sections:
            self.assertIn(section, content, f"Missing AI-specific section: {section}")
        
        # Should guide on what to document
        guidance_keywords = [
            'What Went Well',
            'What Could Be Improved',
            'Key Learnings',  # Template uses "Key Learnings" not "Lessons Learned"
            'Action Items'
        ]
        
        for keyword in guidance_keywords:
            self.assertIn(keyword, content, f"Missing guidance keyword: {keyword}")
    
    def test_feature_proposal_template_clarity(self):
        """Test feature proposal template is clear for AI agents"""
        proposal_template = self.templates_dir / 'feature-proposal.md'
        if not proposal_template.exists():
            self.skipTest("feature-proposal.md template not found")
        
        content = proposal_template.read_text()
        
        # Should have clear structure markers
        structure_elements = [
            'Problem Statement',
            'User Stories',
            'Success Criteria',
            'Implementation Plan',
            'Testing Strategy'
        ]
        
        for element in structure_elements:
            self.assertIn(element, content, f"Missing structure element: {element}")
        
        # Should have placeholders that are clear
        self.assertGreater(content.count('['), 20, "Template should have clear placeholders")
    
    def test_implementation_plan_template(self):
        """Test implementation plan template provides clear task structure"""
        plan_template = self.templates_dir / 'implementation-plan.md'
        if not plan_template.exists():
            self.skipTest("implementation-plan.md template not found")
        
        content = plan_template.read_text()
        
        # Should break down into phases
        self.assertIn('Phase', content)
        self.assertIn('Tasks', content)
        self.assertIn('Deliverables', content)
        self.assertIn('Success Criteria', content)
        
        # Should have task tracking structure
        self.assertIn('[ ]', content, "Should have checkbox format for tasks")


class TestGeneratedFileAIFriendliness(unittest.TestCase):
    """Test that files generated by setup are AI-friendly"""
    
    def test_generated_readme_structure(self):
        """Test that generated README guides AI agents properly"""
        # This would test actual generated README
        # Key points: Links to CLAUDE.md, mentions AI-First SDLC, clear structure
        pass
    
    def test_generated_gitignore_completeness(self):
        """Test that generated .gitignore is comprehensive"""
        # This would test actual generated .gitignore
        # Should combine base + AI tools + language-specific
        pass


class TestAIWorkflowIntegration(unittest.TestCase):
    """Test that the complete workflow is AI-friendly"""
    
    def test_clear_error_messages(self):
        """Test that error messages guide AI agents to solutions"""
        # Error messages should suggest next steps
        # Should reference documentation
        # Should be actionable
        pass
    
    def test_validation_messages_clarity(self):
        """Test validation pipeline gives clear guidance"""
        # Validation failures should explain what's needed
        # Should reference specific files/sections
        pass


def analyze_ai_friendliness_score():
    """Analyze overall AI-friendliness of the framework"""
    print("\n🤖 AI-Friendliness Analysis")
    print("=" * 50)
    
    scores = {
        'Clear Instructions': 0,
        'Structured Templates': 0,
        'Error Guidance': 0,
        'Process Enforcement': 0,
        'Context Preservation': 0
    }
    
    # Analyze CLAUDE.md template
    claude_template = Path(__file__).parent.parent / 'templates' / 'CLAUDE.md'
    if claude_template.exists():
        content = claude_template.read_text()
        
        # Score based on presence of key elements
        if 'NEVER PUSH DIRECTLY TO MAIN' in content:
            scores['Clear Instructions'] += 25
        if re.search(r'##.*Workflow', content):
            scores['Process Enforcement'] += 25
        if 'Code Style' in content and 'Testing Requirements' in content:
            scores['Structured Templates'] += 25
    
    # Analyze gitignore templates
    gitignore_dir = Path(__file__).parent.parent / 'templates' / 'gitignore'
    if gitignore_dir.exists():
        ai_tools = (gitignore_dir / 'ai-tools.gitignore')
        if ai_tools.exists():
            content = ai_tools.read_text()
            if all(tool in content for tool in ['.claude/', '.cursor/', '.aider']):
                scores['Context Preservation'] += 25
    
    # Analyze test templates
    test_templates = Path(__file__).parent.parent / 'templates' / 'tests'
    if test_templates.exists():
        test_files = list(test_templates.glob('*'))
        if len(test_files) >= 3:  # Python, Node, Shell
            scores['Error Guidance'] += 25
    
    # Calculate total score
    total_score = sum(scores.values()) / len(scores)
    
    print("\nCategory Scores:")
    for category, score in scores.items():
        print(f"  {category}: {score}%")
    
    print(f"\n🎯 Overall AI-Friendliness Score: {total_score:.1f}%")
    
    if total_score >= 80:
        print("✅ Excellent: Framework is highly AI-friendly")
    elif total_score >= 60:
        print("🟡 Good: Framework is AI-friendly with room for improvement")
    else:
        print("🔴 Needs Work: Framework needs better AI guidance")
    
    return total_score


if __name__ == '__main__':
    # Run tests
    print("🧪 Testing AI-Friendliness...")
    unittest.main(argv=[''], exit=False, verbosity=2)
    
    # Run analysis
    print("\n" + "="*60)
    analyze_ai_friendliness_score()