#!/usr/bin/env python3
"""
Technical Debt Detection Tool for Zero Technical Debt Policy
Scans codebase for any indicators of technical debt
"""

import os
import sys
import re
import json
from pathlib import Path
from typing import Dict, List, Optional
import argparse
from datetime import datetime
from collections import defaultdict


class TechnicalDebtDetector:
    """Detects all forms of technical debt in a codebase"""
    
    def __init__(self, project_root: Optional[Path] = None, context: str = 'application'):
        self.project_root = project_root or Path.cwd()
        self.debt_items = defaultdict(list)
        self.file_count = 0
        self.total_lines = 0
        self.context = context  # 'application' or 'framework'
        
        # Patterns to skip
        self.skip_dirs = {
            'node_modules', '.git', '__pycache__', 'venv', 'env',
            '.venv', 'dist', 'build', 'coverage', '.pytest_cache',
            '.mypy_cache', 'target', '.idea', '.vscode'
        }
        
        # File extensions to check
        self.code_extensions = {
            '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.go',
            '.rs', '.cpp', '.c', '.h', '.rb', '.php', '.cs',
            '.swift', '.kt', '.scala', '.r', '.m', '.mm'
        }
        
        # Context-specific thresholds
        self.thresholds = self._get_thresholds()
    
    def _get_thresholds(self) -> Dict[str, int]:
        """Get context-specific thresholds"""
        if self.context == 'framework':
            return {
                'security_issues': 0,        # Zero tolerance
                'todos_fixmes': 0,           # Zero tolerance
                'type_issues': 150,          # Pragmatic limit
                'error_suppressions': 20,    # Documented justifications
                'magic_numbers': 2000,       # Common constants allowed
                'deprecated_usage': 50,      # Migration timeline required
                'commented_code': 10,        # Examples and documentation
                'complexity_issues': 10,     # Framework utility complexity
            }
        else:  # application
            return {
                'security_issues': 0,
                'todos_fixmes': 0,
                'type_issues': 0,
                'error_suppressions': 0,
                'magic_numbers': 0,
                'deprecated_usage': 0,
                'commented_code': 0,
                'complexity_issues': 0,
            }
    
    def _determine_file_context(self, file_path: Path) -> str:
        """Determine if file is framework infrastructure or application code"""
        relative_path = str(file_path.relative_to(self.project_root))
        
        framework_patterns = [
            'tools/',
            'templates/',
            'examples/',
            'setup.py',
            'setup-smart.py',
            'migrate-',
            'fix-',
            'test-',
            '.github/',
            'docs/',
            'retrospectives/'
        ]
        
        if any(pattern in relative_path for pattern in framework_patterns):
            return 'framework'
        else:
            return 'application'
    
    def scan(self) -> Dict[str, List[Dict]]:
        """Scan the entire codebase for technical debt"""
        print("🔍 Scanning for Technical Debt Indicators...")
        print("=" * 60)
        
        # Auto-detect context if not explicitly set
        framework_files = 0
        application_files = 0
        
        for root, dirs, files in os.walk(self.project_root):
            # Skip unwanted directories
            dirs[:] = [d for d in dirs if d not in self.skip_dirs]
            
            for file in files:
                file_path = Path(root) / file
                if file_path.suffix in self.code_extensions:
                    # Determine file context for auto-detection
                    file_context = self._determine_file_context(file_path)
                    if file_context == 'framework':
                        framework_files += 1
                    else:
                        application_files += 1
                    
                    self._analyze_file(file_path)
        
        # Auto-adjust context based on file distribution
        if self.context == 'application' and framework_files > application_files * 0.5:
            print(f"🏗️  Auto-detected Framework Context ({framework_files} framework files)")
            self.context = 'framework'
            self.thresholds = self._get_thresholds()
        
        return self.debt_items
    
    def _analyze_file(self, file_path: Path) -> None:
        """Analyze a single file for technical debt"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.splitlines()
                
            self.file_count += 1
            self.total_lines += len(lines)
            relative_path = file_path.relative_to(self.project_root)
            
            # Check for various debt indicators
            self._check_todos(relative_path, lines)
            self._check_commented_code(relative_path, lines, file_path.suffix)
            self._check_type_issues(relative_path, content, file_path.suffix)
            self._check_error_suppression(relative_path, content)
            self._check_code_smells(relative_path, content, file_path.suffix)
            self._check_deprecated_usage(relative_path, content)
            self._check_security_issues(relative_path, content)
            self._check_complexity(relative_path, content, file_path.suffix)
            
        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")
    
    def _check_todos(self, file_path: Path, lines: List[str]) -> None:
        """Check for TODO/FIXME comments"""
        # Only match actual comments, not words in strings or regular text
        todo_pattern = re.compile(r'(?:#|//|/\*|<!--)\s*(TODO|FIXME|HACK|XXX|BUG|REFACTOR|OPTIMIZE):?\s*(.*)$', re.IGNORECASE)
        
        for line_no, line in enumerate(lines, 1):
            # Skip strings that contain TODO as part of normal text (like "todo app")
            if any(marker in line for marker in ['"todo', "'todo", "todo app", "Todo App", "TODO App"]):
                continue
                
            match = todo_pattern.search(line)
            if match:
                self.debt_items['todos'].append({
                    'file': str(file_path),
                    'line': line_no,
                    'type': match.group(1).upper(),
                    'message': match.group(2).strip(),
                    'severity': 'high' if match.group(1).upper() in ['BUG', 'FIXME'] else 'medium'
                })
    
    def _check_commented_code(self, file_path: Path, lines: List[str], suffix: str) -> None:
        """Check for commented-out code"""
        comment_patterns = {
            '.py': (r'^\s*#\s*', ['import', 'def', 'class', 'if', 'for', 'while', 'return', 'raise', 'try']),
            '.js': (r'^\s*//\s*', ['import', 'export', 'function', 'class', 'if', 'for', 'while', 'return', 'const', 'let', 'var']),
            '.ts': (r'^\s*//\s*', ['import', 'export', 'function', 'class', 'if', 'for', 'while', 'return', 'const', 'let', 'var']),
            '.java': (r'^\s*//\s*', ['import', 'public', 'private', 'class', 'if', 'for', 'while', 'return', 'throw']),
            '.go': (r'^\s*//\s*', ['import', 'func', 'type', 'if', 'for', 'return', 'package']),
            '.rs': (r'^\s*//\s*', ['use', 'fn', 'impl', 'struct', 'if', 'for', 'while', 'return']),
            '.cpp': (r'^\s*//\s*', ['#include', 'class', 'if', 'for', 'while', 'return', 'namespace']),
            '.rb': (r'^\s*#\s*', ['require', 'def', 'class', 'if', 'for', 'while', 'return']),
        }
        
        if suffix not in comment_patterns:
            return
        
        prefix, keywords = comment_patterns[suffix]
        pattern = re.compile(prefix + r'(' + '|'.join(keywords) + r')\b')
        
        for line_no, line in enumerate(lines, 1):
            if pattern.match(line):
                self.debt_items['commented_code'].append({
                    'file': str(file_path),
                    'line': line_no,
                    'code': line.strip(),
                    'severity': 'medium'
                })
    
    def _check_type_issues(self, file_path: Path, content: str, suffix: str) -> None:
        """Check for type safety issues"""
        # TypeScript/JavaScript any types
        if suffix in ['.ts', '.tsx']:
            any_matches = re.finditer(r':\s*any\b', content)
            for match in any_matches:
                line_no = content[:match.start()].count('\n') + 1
                self.debt_items['type_issues'].append({
                    'file': str(file_path),
                    'line': line_no,
                    'issue': 'any type used',
                    'severity': 'high'
                })
        
        # Python missing type hints (simple heuristic)
        elif suffix == '.py':
            # Check for functions without return type hints
            func_pattern = re.compile(r'^\s*def\s+(\w+)\s*\([^)]*\)\s*:', re.MULTILINE)
            typed_func_pattern = re.compile(r'^\s*def\s+(\w+)\s*\([^)]*\)\s*->\s*[^:]+:', re.MULTILINE)
            
            all_funcs = func_pattern.findall(content)
            typed_funcs = typed_func_pattern.findall(content)
            
            if len(all_funcs) > len(typed_funcs):
                untyped = set(all_funcs) - set(typed_funcs)
                for func_name in untyped:
                    # Skip special methods
                    if not func_name.startswith('__'):
                        self.debt_items['type_issues'].append({
                            'file': str(file_path),
                            'function': func_name,
                            'issue': 'missing return type annotation',
                            'severity': 'medium'
                        })
    
    def _check_error_suppression(self, file_path: Path, content: str) -> None:
        """Check for error suppression directives"""
        suppressions = [
            (r'@ts-ignore', 'TypeScript error ignored'),
            (r'@ts-nocheck', 'TypeScript checking disabled'),
            (r'# type:\s*ignore', 'mypy type checking ignored'),
            (r'# noqa', 'flake8 checking ignored'),
            (r'# pylint:\s*disable', 'pylint rule disabled'),
            (r'// eslint-disable', 'ESLint rule disabled'),
            (r'// @ts-expect-error', 'TypeScript error expected'),
            (r'#pragma warning disable', 'C# warning disabled'),
            (r'@SuppressWarnings', 'Java warnings suppressed'),
        ]
        
        for pattern, description in suppressions:
            matches = re.finditer(pattern, content)
            for match in matches:
                line_no = content[:match.start()].count('\n') + 1
                self.debt_items['suppressions'].append({
                    'file': str(file_path),
                    'line': line_no,
                    'type': description,
                    'severity': 'high'
                })
    
    def _check_code_smells(self, file_path: Path, content: str, suffix: str) -> None:
        """Check for common code smells"""
        # Long functions
        if suffix in ['.py', '.js', '.ts', '.java', '.go', '.rs']:
            self._check_long_functions(file_path, content, suffix)
        
        # Deeply nested code
        self._check_deep_nesting(file_path, content)
        
        # Magic numbers
        magic_number_pattern = re.compile(r'\b(?<!\.)\d{2,}(?!\.)\b')
        for match in magic_number_pattern.finditer(content):
            # Skip years and common ports
            number = int(match.group())
            if 1900 <= number <= 2100 or number in [80, 443, 3000, 8080, 8000]:
                continue
                
            line_no = content[:match.start()].count('\n') + 1
            self.debt_items['code_smells'].append({
                'file': str(file_path),
                'line': line_no,
                'issue': f'magic number: {number}',
                'severity': 'low'
            })
    
    def _check_long_functions(self, file_path: Path, content: str, suffix: str) -> None:
        """Check for functions that are too long"""
        patterns = {
            '.py': r'^\s*def\s+\w+.*?(?=^\s*def|\Z)',
            '.js': r'function\s+\w+\s*\([^)]*\)\s*\{[^}]*\}',
            '.ts': r'function\s+\w+\s*\([^)]*\)\s*\{[^}]*\}',
            '.java': r'(public|private|protected)\s+\w+\s+\w+\s*\([^)]*\)\s*\{[^}]*\}',
        }
        
        if suffix not in patterns:
            return
        
        # This is a simplified check - real parsing would be better
        lines = content.split('\n')
        if suffix == '.py':
            current_func = None
            func_start = 0
            indent_level = 0
            
            for i, line in enumerate(lines):
                if re.match(r'^\s*def\s+(\w+)', line):
                    if current_func and i - func_start > 50:
                        self.debt_items['code_smells'].append({
                            'file': str(file_path),
                            'line': func_start + 1,
                            'issue': f'function {current_func} is {i - func_start} lines long',
                            'severity': 'medium'
                        })
                    match = re.match(r'^\s*def\s+(\w+)', line)
                    current_func = match.group(1)
                    func_start = i

    
    def _check_deep_nesting(self, file_path: Path, content: str) -> None:
        """Check for deeply nested code"""
        lines = content.split('\n')
        max_nesting = 0
        nesting_levels = []
        
        for i, line in enumerate(lines):
            # Count leading spaces/tabs
            indent = len(line) - len(line.lstrip())
            if line.strip():  # Non-empty line
                nesting_level = indent // 4  # Assume 4 spaces per level
                if nesting_level > 4:  # More than 4 levels deep
                    self.debt_items['code_smells'].append({
                        'file': str(file_path),
                        'line': i + 1,
                        'issue': f'deeply nested code ({nesting_level} levels)',
                        'severity': 'medium'
                    })
    
    def _check_deprecated_usage(self, file_path: Path, content: str) -> None:
        """Check for deprecated API usage"""
        deprecated_patterns = [
            # Python
            (r'urllib\.urlopen', 'urllib.urlopen is deprecated, use urllib.request.urlopen'),
            (r'assertEquals', 'assertEquals is deprecated, use assertEqual'),
            
            # JavaScript/TypeScript
            (r'componentWillMount', 'componentWillMount is deprecated in React'),
            (r'componentWillReceiveProps', 'componentWillReceiveProps is deprecated in React'),
            (r'findDOMNode', 'findDOMNode is deprecated in React'),
            
            # General
            (r'@deprecated', 'Using deprecated API'),
            (r'DEPRECATED', 'Reference to deprecated functionality'),
        ]
        
        for pattern, message in deprecated_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                line_no = content[:match.start()].count('\n') + 1
                self.debt_items['deprecated'].append({
                    'file': str(file_path),
                    'line': line_no,
                    'issue': message,
                    'severity': 'high'
                })
    
    def _check_security_issues(self, file_path: Path, content: str) -> None:
        """Check for potential security issues"""
        security_patterns = [
            (r'eval\s*\(', 'eval() usage is a security risk'),
            (r'exec\s*\(', 'exec() usage is a security risk'),
            (r'innerHTML\s*=', 'innerHTML assignment can lead to XSS'),
            (r'dangerouslySetInnerHTML', 'dangerouslySetInnerHTML can lead to XSS'),
            (r'password\s*=\s*["\'][^"\']+["\']', 'Hardcoded password detected'),
            (r'api_key\s*=\s*["\'][^"\']+["\']', 'Hardcoded API key detected'),
            (r'secret\s*=\s*["\'][^"\']+["\']', 'Hardcoded secret detected'),
            (r'token\s*=\s*["\'][^"\']+["\']', 'Hardcoded token detected'),
        ]
        
        lines = content.split('\n')
        for pattern, message in security_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                line_no = content[:match.start()].count('\n') + 1
                line = lines[line_no - 1].strip()
                
                # Skip pattern definitions, comments, and strings
                if (line.startswith('#') or 
                    line.startswith('//') or
                    '(r\'' in line or 
                    '"' in line and 'pattern' in line.lower() or
                    'security_patterns' in line):
                    continue
                    
                self.debt_items['security'].append({
                    'file': str(file_path),
                    'line': line_no,
                    'issue': message,
                    'severity': 'critical'
                })
    
    def _check_complexity(self, file_path: Path, content: str, suffix: str) -> None:
        """Check for high cyclomatic complexity"""
        # This is a simplified check - real complexity calculation would be better
        complexity_keywords = ['if', 'elif', 'else', 'for', 'while', 'case', 'catch', 'except']
        
        # Count complexity indicators per function (simplified)
        lines = content.split('\n')
        current_func = None
        complexity_count = 0
        func_start = 0
        
        for i, line in enumerate(lines):
            # Detect function start (simplified for Python)
            if suffix == '.py' and re.match(r'^\s*def\s+(\w+)', line):
                if current_func and complexity_count > 10:
                    self.debt_items['complexity'].append({
                        'file': str(file_path),
                        'line': func_start + 1,
                        'function': current_func,
                        'complexity': complexity_count,
                        'severity': 'high'
                    })
                match = re.match(r'^\s*def\s+(\w+)', line)
                current_func = match.group(1)
                func_start = i
                complexity_count = 0
            
            # Count complexity indicators
            for keyword in complexity_keywords:
                if re.search(r'\b' + keyword + r'\b', line):
                    complexity_count += 1
    
    def generate_report(self, format: str = 'console') -> str:
        """Generate a report of all technical debt found"""
        total_issues = sum(len(items) for items in self.debt_items.values())
        
        if format == 'console':
            print(f"\n🛑 TECHNICAL DEBT SCAN - {self.context.upper()} MODE")
            print("=" * 60)
            print(f"Files Scanned: {self.file_count}")
            print(f"Total Lines: {self.total_lines:,}")
            print(f"DEBT FOUND: {total_issues}")
            
            # Show policy compliance
            print(f"\n📋 Policy Compliance Check")
            print("-" * 30)
            policy_violations = self._check_policy_compliance()
            if policy_violations == 0:
                print(f"✅ {self.context.title()} Policy: COMPLIANT")
            else:
                print(f"❌ {self.context.title()} Policy: {policy_violations} violations")
            print()
            
            if total_issues == 0:
                print("✅ ZERO DEBT - Proceed")
                return ""
            
            # Group by category
            categories = [
                ('todos', '📝 TODOs and FIXMEs'),
                ('commented_code', '💬 Commented Code'),
                ('type_issues', '🔤 Type Issues'),
                ('suppressions', '🚫 Error Suppressions'),
                ('code_smells', '👃 Code Smells'),
                ('deprecated', '⚠️  Deprecated Usage'),
                ('security', '🔒 Security Issues'),
                ('complexity', '🌀 High Complexity'),
            ]
            
            for key, title in categories:
                items = self.debt_items.get(key, [])
                if items:
                    print(f"\n{title} ({len(items)} issues)")
                    print("-" * 50)
                    
                    # Show first 5 items of each category
                    for item in items[:5]:
                        self._print_item(item)
                    
                    if len(items) > 5:
                        print(f"... and {len(items) - 5} more")
            
            # Summary by severity
            print(f"\n📈 Summary by Severity")
            print("-" * 30)
            severity_counts = defaultdict(int)
            for items in self.debt_items.values():
                for item in items:
                    severity_counts[item.get('severity', 'unknown')] += 1
            
            for severity in ['critical', 'high', 'medium', 'low']:
                if severity in severity_counts:
                    print(f"{severity.upper()}: {severity_counts[severity]}")
            
            return ""
        
        elif format == 'json':
            report = {
                'timestamp': datetime.now().isoformat(),
                'summary': {
                    'files_scanned': self.file_count,
                    'total_lines': self.total_lines,
                    'total_issues': total_issues,
                },
                'issues': dict(self.debt_items),
                'severity_summary': self._get_severity_summary()
            }
            return json.dumps(report, indent=2)
        
        elif format == 'markdown':
            md = f"# Technical Debt Report\n\n"
            md += f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            md += f"## Summary\n\n"
            md += f"- Files Scanned: {self.file_count}\n"
            md += f"- Total Lines: {self.total_lines:,}\n"
            md += f"- Total Issues: {total_issues}\n\n"
            
            if total_issues == 0:
                md += "✅ **No technical debt detected!**\n"
                return md
            
            md += "## Issues by Category\n\n"
            
            for key, title in [
                ('todos', 'TODOs and FIXMEs'),
                ('commented_code', 'Commented Code'),
                ('type_issues', 'Type Issues'),
                ('suppressions', 'Error Suppressions'),
                ('code_smells', 'Code Smells'),
                ('deprecated', 'Deprecated Usage'),
                ('security', 'Security Issues'),
                ('complexity', 'High Complexity'),
            ]:
                items = self.debt_items.get(key, [])
                if items:
                    md += f"### {title} ({len(items)})\n\n"
                    for item in items[:10]:
                        md += f"- `{item.get('file', 'unknown')}`"
                        if 'line' in item:
                            md += f":{item['line']}"
                        md += f" - {self._get_item_description(item)}\n"
                    if len(items) > 10:
                        md += f"- ... and {len(items) - 10} more\n"
                    md += "\n"
            
            return md
        
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def _print_item(self, item: Dict) -> None:
        """Print a single debt item"""
        file_info = f"{item.get('file', 'unknown')}"
        if 'line' in item:
            file_info += f":{item['line']}"
        
        print(f"  {file_info}")
        print(f"    {self._get_item_description(item)}")
    
    def _get_item_description(self, item: Dict) -> str:
        """Get a description for a debt item"""
        if 'message' in item:
            return f"{item.get('type', '')}: {item['message']}"
        elif 'issue' in item:
            return item['issue']
        elif 'code' in item:
            return f"Commented: {item['code'][:50]}..."
        elif 'function' in item:
            return f"Function '{item['function']}': {item.get('issue', 'issue detected')}"
        else:
            return "Issue detected"
    
    def _get_severity_summary(self) -> Dict[str, int]:
        """Get count of issues by severity"""
        severity_counts = defaultdict(int)
        for items in self.debt_items.values():
            for item in items:
                severity_counts[item.get('severity', 'unknown')] += 1
        return dict(severity_counts)
    
    def _check_policy_compliance(self) -> int:
        """Check compliance against context-specific policy thresholds"""
        violations = 0
        
        # Map debt categories to threshold keys
        category_mapping = {
            'security': 'security_issues',
            'todos': 'todos_fixmes',
            'type_issues': 'type_issues',
            'suppressions': 'error_suppressions',
            'code_smells': 'magic_numbers',  # Most code smells are magic numbers
            'deprecated': 'deprecated_usage',
            'commented_code': 'commented_code',
            'complexity': 'complexity_issues'
        }
        
        for category, threshold_key in category_mapping.items():
            count = len(self.debt_items.get(category, []))
            threshold = self.thresholds.get(threshold_key, 0)
            
            if count > threshold:
                violations += count - threshold
                if self.context == 'framework':
                    print(f"  ⚠️  {category}: {count}/{threshold} (over by {count - threshold})")
                else:
                    print(f"  ❌ {category}: {count} (Zero Tolerance Policy)")
        
        return violations


def main():
    parser = argparse.ArgumentParser(
        description="Detect technical debt in your codebase"
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Path to scan (default: current directory)"
    )
    parser.add_argument(
        "--format",
        choices=["console", "json", "markdown"],
        default="console",
        help="Output format (default: console)"
    )
    parser.add_argument(
        "--output",
        help="Output file (default: stdout)"
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=0,
        help="Exit with error if issues exceed threshold (default: 0)"
    )
    parser.add_argument(
        "--ignore",
        nargs="+",
        help="Patterns to ignore (e.g., 'test_*.py', '*.spec.js')"
    )
    parser.add_argument(
        "--context",
        choices=["application", "framework"],
        default="application",
        help="Code context for policy compliance (default: application, auto-detects framework)"
    )
    
    args = parser.parse_args()
    
    # Create detector and run scan
    detector = TechnicalDebtDetector(Path(args.path), context=args.context)
    
    # Ignore patterns not implemented - Zero Technical Debt Policy
    # requires fixing issues, not ignoring them
    if args.ignore:
        print("Warning: --ignore flag is not supported.")
        print("Zero Technical Debt Policy requires fixing all issues.")
    
    # Run scan
    debt_items = detector.scan()
    
    # Generate report
    report = detector.generate_report(args.format)
    
    # Output report
    if args.output:
        with open(args.output, 'w') as f:
            f.write(report)
        print(f"Report written to: {args.output}")
    elif args.format != 'console':
        print(report)
    
    # Check policy compliance
    total_issues = sum(len(items) for items in debt_items.values())
    policy_violations = detector._check_policy_compliance()
    
    # Use legacy threshold for backward compatibility, but policy takes precedence
    threshold_exceeded = total_issues > args.threshold
    
    if policy_violations > 0 or threshold_exceeded:
        print(f"\n🚫 POLICY VIOLATION DETECTED")
        print("=" * 60)
        
        if detector.context == 'framework':
            print(f"\n⚠️  FRAMEWORK POLICY VIOLATIONS: {policy_violations}")
            print("📋 Framework Code Standards:")
            print("- Security issues: ZERO tolerance")
            print("- TODOs/FIXMEs: ZERO tolerance") 
            print("- Other issues: Within documented thresholds")
            print("\n⚠️  YOU SHOULD:")
            print("- Review violations against Framework Compliance Policy")
            print("- Fix critical issues (security, TODOs)")
            print("- Document justifications for acceptable debt")
            print("- See docs/FRAMEWORK-COMPLIANCE-POLICY.md")
        else:
            print(f"\n❌ APPLICATION POLICY VIOLATIONS: {policy_violations}")
            print("🛑 Zero Technical Debt Policy:")
            print("- ALL issues must be fixed immediately")
            print("- NO exceptions for application code")
            print("\n⛔ YOU ARE FORBIDDEN FROM:")
            print("- Committing this code")
            print("- Creating a PR")
            print("- Proceeding with ANY other work")
            print("\n⛔ YOU MUST:")
            print("- Fix ALL issues immediately")
            print("- Run this check again")
            print("- Only proceed when debt = 0")
            print("\nNO EXCEPTIONS. NO EXCUSES.")
        
        sys.exit(1)
    else:
        context_msg = detector.context.title()
        print(f"\n✅ {context_msg} Policy: COMPLIANT - You may proceed")
        sys.exit(0)


if __name__ == "__main__":
    main()