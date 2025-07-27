#!/usr/bin/env python3
"""
Logging Compliance Checker for Zero Technical Debt Policy
Ensures all code has proper logging at mandatory points
"""

import ast
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple
import argparse


class LoggingComplianceChecker:
    """Validates that code includes mandatory logging"""
    
    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path.cwd()
        self.violations = []
        self.stats = {
            'files_checked': 0,
            'functions_checked': 0,
            'missing_entry_logs': 0,
            'missing_error_logs': 0,
            'missing_external_logs': 0,
            'missing_state_logs': 0,
            'missing_security_logs': 0,
            'missing_business_logs': 0,
            'missing_performance_logs': 0,
            'missing_config_logs': 0,
            'missing_validation_logs': 0,
            'missing_resource_logs': 0,
            'sensitive_data_logs': 0
        }
        
        # Patterns indicating logging calls by language
        self.log_patterns = {
            '.py': [
                r'logger\.(debug|info|warning|warn|error|critical)',
                r'logging\.(debug|info|warning|warn|error|critical)',
                r'log\.(debug|info|warning|warn|error|critical)',
            ],
            '.js': [
                r'logger\.(debug|info|warn|error)',
                r'console\.(log|info|warn|error)',
                r'winston\.',
                r'bunyan\.',
            ],
            '.ts': [
                r'logger\.(debug|info|warn|error)',
                r'console\.(log|info|warn|error)',
                r'winston\.',
                r'bunyan\.',
            ],
        }
        
        # Sensitive data patterns that should NEVER be logged
        self.sensitive_patterns = [
            # Authentication & Secrets
            r'\bpassword\b',
            r'\bpasswd\b',
            r'\btoken\b',
            r'\bapi_key\b',
            r'\bapikey\b',
            r'\bsecret\b',
            r'\bprivate_key\b',
            r'\bjwt\b',
            r'\boauth\b',
            r'\brefresh_token\b',
            r'\bsession_id\b',
            r'\bcookie\b',
            r'\bauth\b',
            
            # Financial Data
            r'\bcredit_card\b',
            r'\bcard_number\b',
            r'\bbank_account\b',
            r'\brouting_number\b',
            r'\biban\b',
            r'\bswift\b',
            r'\bcvv\b',
            
            # Personal Identifiers
            r'\bssn\b',
            r'\bsocial_security\b',
            r'\bdriver_license\b',
            r'\bpassport\b',
            r'\bnational_id\b',
            r'\bgovernment_id\b',
            r'\btax_id\b',
            
            # Health Information
            r'\bpatient_id\b',
            r'\bmedical_record\b',
            r'\bhealth_insurance\b',
            r'\bprescription\b',
            r'\bdiagnosis\b',
            
            # Biometric & Device Data
            r'\bfingerprint\b',
            r'\bface_data\b',
            r'\bvoice_print\b',
            r'\bbiometric\b',
            r'\bmac_address\b',
            r'\bimei\b',
            r'\bdevice_id\b',
            r'\budid\b',
            
            # Location & Contact
            r'\bgps_coord\b',
            r'\blatitude\b',
            r'\blongitude\b',
            r'\bip_address\b',
            r'\bphone_number\b',
            r'\bemail_address\b',
            r'\bdate_of_birth\b',
            r'\bdob\b',
            
            # Cryptographic Material
            r'\bprivate_key\b',
            r'\bcertificate\b',
            r'\bencryption_key\b',
            r'\bcrypto_key\b',
        ]
        
        # Patterns indicating external calls
        self.external_patterns = [
            r'requests\.',
            r'urllib\.',
            r'http\.',
            r'fetch\(',
            r'axios\.',
            r'\.get\(',
            r'\.post\(',
            r'\.put\(',
            r'\.delete\(',
            r'\.execute\(',
            r'\.query\(',
            r'\.save\(',
            r'\.create\(',
            r'\.update\(',
        ]
        
        # Patterns for different logging categories
        self.state_change_patterns = [
            r'\.save\b', r'\.update\b', r'\.create\b', r'\.delete\b',
            r'\.set\b', r'\.assign\b', r'\.modify\b', r'\.change\b',
            r'setState', r'dispatch\(', r'commit\(',
        ]
        
        self.security_patterns = [
            r'login\b', r'logout\b', r'authenticate\b', r'authorize\b',
            r'permission', r'access_denied', r'forbidden', r'unauthorized',
            r'verify_token', r'check_permission', r'validate_user',
        ]
        
        self.performance_patterns = [
            r'duration', r'elapsed', r'response_time', r'latency',
            r'slow', r'timeout', r'performance', r'threshold',
        ]
        
        self.config_patterns = [
            r'config\[', r'settings\[', r'environ\[', r'feature_flag',
            r'toggle', r'enable', r'disable', r'update_config',
        ]
        
        self.validation_patterns = [
            r'validate', r'is_valid', r'check_', r'verify_',
            r'sanitize', r'parse', r'clean', r'normalize',
        ]
        
        self.resource_patterns = [
            r'limit', r'quota', r'capacity', r'threshold',
            r'pool', r'connection', r'rate_limit', r'throttle',
        ]
        
        # Functions to skip
        self.skip_patterns = [
            r'^get[A-Z]',  # Getters
            r'^set[A-Z]',  # Setters
            r'^__\w+__$',  # Python magic methods
            r'^_',         # Private methods (optional)
        ]
    
    def should_skip_function(self, func_name: str) -> bool:
        """Check if function should be skipped from logging requirements"""
        for pattern in self.skip_patterns:
            if re.match(pattern, func_name):
                return True
        return False
    
    def check_file(self, file_path: Path) -> List[Dict]:
        """Check a single file for logging compliance"""
        violations = []
        self.stats['files_checked'] += 1
        
        try:
            content = file_path.read_text(encoding='utf-8')
            
            # Check for sensitive data in logs
            sensitive_violations = self._check_sensitive_data(file_path, content)
            violations.extend(sensitive_violations)
            
            # Language-specific checks
            if file_path.suffix == '.py':
                violations.extend(self._check_python_file(file_path, content))
            elif file_path.suffix in ['.js', '.ts']:
                violations.extend(self._check_javascript_file(file_path, content))
                
        except Exception as e:
            print(f"Error checking {file_path}: {e}")
            
        return violations
    
    def _check_sensitive_data(self, file_path: Path, content: str) -> List[Dict]:
        """Check for sensitive data being logged"""
        violations = []
        lines = content.split('\n')
        
        log_patterns = self.log_patterns.get(file_path.suffix, [])
        if not log_patterns:
            return violations
            
        for i, line in enumerate(lines, 1):
            # Check if line contains logging
            has_log = any(re.search(pattern, line) for pattern in log_patterns)
            if not has_log:
                continue
                
            # Check for sensitive data
            for sensitive in self.sensitive_patterns:
                if re.search(sensitive, line, re.IGNORECASE):
                    # Skip if it's checking for sensitive data (not logging it)
                    if any(safe_word in line.lower() for safe_word in 
                           ['sanitize', 'mask', 'redact', 'hash', 'encrypt', 'remove']):
                        continue
                    
                    # Skip if it's in a comment
                    if line.strip().startswith('#') or line.strip().startswith('//'):
                        continue
                        
                    violations.append({
                        'file': str(file_path),
                        'line': i,
                        'function': 'N/A',
                        'violation': 'sensitive_data_log',
                        'message': f'Potential sensitive data "{sensitive}" in log'
                    })
                    self.stats['sensitive_data_logs'] += 1
                    
        return violations
    
    def _check_python_file(self, file_path: Path, content: str) -> List[Dict]:
        """Check Python file for logging compliance"""
        violations = []
        
        try:
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    self.stats['functions_checked'] += 1
                    
                    if self.should_skip_function(node.name):
                        continue
                        
                    func_violations = self._check_python_function(
                        node, content, file_path
                    )
                    violations.extend(func_violations)
                    
        except SyntaxError:
            pass  # Skip files with syntax errors
            
        return violations
    
    def _check_python_function(self, func_node: ast.FunctionDef, 
                              content: str, file_path: Path) -> List[Dict]:
        """Check if Python function has required logging"""
        violations = []
        func_name = func_node.name
        
        # Get function lines
        func_lines = content.split('\n')[
            func_node.lineno - 1:func_node.end_lineno
        ]
        func_body = '\n'.join(func_lines)
        
        # Skip very short functions
        if len(func_lines) < 3:
            return violations
        
        # Check for any logging
        has_logging = self._has_logging_pattern(func_body, '.py')
        
        # Check for entry/exit logging (for functions > 5 lines)
        if len(func_lines) > 5 and not has_logging:
            violations.append({
                'file': str(file_path),
                'line': func_node.lineno,
                'function': func_name,
                'violation': 'missing_entry_log',
                'message': f'Function {func_name} missing entry/exit logging'
            })
            self.stats['missing_entry_logs'] += 1
        
        # Check for error handling with logging
        has_try = any('try:' in line for line in func_lines)
        has_except = any('except' in line for line in func_lines)
        
        if has_try and has_except:
            # Find except blocks
            in_except = False
            except_has_log = False
            
            for line in func_lines:
                if 'except' in line and ':' in line:
                    in_except = True
                    except_has_log = False
                elif in_except:
                    if self._has_logging_pattern(line, '.py'):
                        except_has_log = True
                    elif line.strip() and not line.strip().startswith('#'):
                        # End of except block
                        if not except_has_log and 'pass' not in line:
                            violations.append({
                                'file': str(file_path),
                                'line': func_node.lineno,
                                'function': func_name,
                                'violation': 'missing_error_log',
                                'message': 'Exception handler missing error logging'
                            })
                            self.stats['missing_error_logs'] += 1
                        in_except = False
        
        # Check for external calls
        for pattern in self.external_patterns:
            if re.search(pattern, func_body):
                # Check if there's logging near the external call
                if not has_logging:
                    violations.append({
                        'file': str(file_path),
                        'line': func_node.lineno,
                        'function': func_name,
                        'violation': 'missing_external_log',
                        'message': 'External call without logging'
                    })
                    self.stats['missing_external_logs'] += 1
                    break
        
        # Check for state changes
        for pattern in self.state_change_patterns:
            if re.search(pattern, func_body):
                if not has_logging:
                    violations.append({
                        'file': str(file_path),
                        'line': func_node.lineno,
                        'function': func_name,
                        'violation': 'missing_state_log',
                        'message': 'State change without logging'
                    })
                    self.stats['missing_state_logs'] += 1
                    break
        
        # Check for security operations
        for pattern in self.security_patterns:
            if re.search(pattern, func_body, re.IGNORECASE):
                if not has_logging:
                    violations.append({
                        'file': str(file_path),
                        'line': func_node.lineno,
                        'function': func_name,
                        'violation': 'missing_security_log',
                        'message': 'Security operation without logging'
                    })
                    self.stats['missing_security_logs'] += 1
                    break
        
        # Check for performance checks
        if any(re.search(p, func_body) for p in self.performance_patterns):
            if '>=' in func_body or '<=' in func_body or 'threshold' in func_body.lower():
                if not has_logging:
                    violations.append({
                        'file': str(file_path),
                        'line': func_node.lineno,
                        'function': func_name,
                        'violation': 'missing_performance_log',
                        'message': 'Performance check without logging'
                    })
                    self.stats['missing_performance_logs'] += 1
        
        # Check for config changes
        for pattern in self.config_patterns:
            if re.search(pattern, func_body):
                if not has_logging:
                    violations.append({
                        'file': str(file_path),
                        'line': func_node.lineno,
                        'function': func_name,
                        'violation': 'missing_config_log',
                        'message': 'Configuration change without logging'
                    })
                    self.stats['missing_config_logs'] += 1
                    break
        
        # Check for validation operations
        for pattern in self.validation_patterns:
            if re.search(pattern, func_body):
                if 'raise' in func_body or 'throw' in func_body or 'reject' in func_body:
                    if not has_logging:
                        violations.append({
                            'file': str(file_path),
                            'line': func_node.lineno,
                            'function': func_name,
                            'violation': 'missing_validation_log',
                            'message': 'Validation failure without logging'
                        })
                        self.stats['missing_validation_logs'] += 1
                        break
        
        # Check for resource limits
        for pattern in self.resource_patterns:
            if re.search(pattern, func_body):
                if any(op in func_body for op in ['>=', '>', '<', '<=', '==']):
                    if not has_logging:
                        violations.append({
                            'file': str(file_path),
                            'line': func_node.lineno,
                            'function': func_name,
                            'violation': 'missing_resource_log',
                            'message': 'Resource check without logging'
                        })
                        self.stats['missing_resource_logs'] += 1
                        break
        
        return violations
    
    def _check_javascript_file(self, file_path: Path, content: str) -> List[Dict]:
        """Check JavaScript/TypeScript file for logging compliance"""
        violations = []
        
        # Simple regex-based checking for JS/TS
        func_pattern = r'(?:function\s+(\w+)|(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?(?:function|\())'
        
        for match in re.finditer(func_pattern, content):
            func_name = match.group(1) or match.group(2)
            if not func_name or self.should_skip_function(func_name):
                continue
                
            self.stats['functions_checked'] += 1
            func_start = match.start()
            
            # Find function body (simplified)
            brace_count = 0
            func_end = func_start
            in_func = False
            
            for i, char in enumerate(content[func_start:], func_start):
                if char == '{':
                    brace_count += 1
                    in_func = True
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0 and in_func:
                        func_end = i
                        break
            
            if func_end > func_start:
                func_body = content[func_start:func_end]
                line_no = content[:func_start].count('\n') + 1
                
                # Check for logging
                has_logging = self._has_logging_pattern(func_body, file_path.suffix)
                
                # Skip very short functions
                if func_body.count('\n') < 3:
                    continue
                
                if not has_logging and func_body.count('\n') > 5:
                    violations.append({
                        'file': str(file_path),
                        'line': line_no,
                        'function': func_name,
                        'violation': 'missing_entry_log',
                        'message': f'Function {func_name} missing logging'
                    })
                    self.stats['missing_entry_logs'] += 1
        
        return violations
    
    def _has_logging_pattern(self, code: str, file_ext: str) -> bool:
        """Check if code contains logging patterns"""
        patterns = self.log_patterns.get(file_ext, [])
        return any(re.search(pattern, code) for pattern in patterns)
    
    def scan_project(self) -> Dict:
        """Scan entire project for logging compliance"""
        print("🔍 Scanning for Logging Compliance...")
        print("=" * 60)
        
        # Skip directories
        skip_dirs = {
            'node_modules', '.git', '__pycache__', 'venv', '.venv',
            'dist', 'build', 'coverage', '.pytest_cache', 'logs'
        }
        
        # File extensions to check
        check_extensions = {'.py', '.js', '.ts'}
        
        for root, dirs, files in os.walk(self.project_root):
            # Skip unwanted directories
            dirs[:] = [d for d in dirs if d not in skip_dirs]
            
            for file in files:
                file_path = Path(root) / file
                
                # Skip test files
                if 'test' in file.lower() or 'spec' in file.lower():
                    continue
                    
                if file_path.suffix in check_extensions:
                    violations = self.check_file(file_path)
                    self.violations.extend(violations)
        
        return {
            'violations': self.violations,
            'stats': self.stats
        }
    
    def generate_report(self) -> None:
        """Generate compliance report"""
        total_violations = len(self.violations)
        
        print(f"\n📊 LOGGING COMPLIANCE REPORT")
        print("=" * 60)
        print(f"Files Checked: {self.stats['files_checked']}")
        print(f"Functions Checked: {self.stats['functions_checked']}")
        print(f"Total Violations: {total_violations}")
        print()
        
        if total_violations == 0:
            print("✅ FULL COMPLIANCE - All mandatory logging present")
            return
        
        # Group violations by type
        by_type = {}
        for v in self.violations:
            vtype = v['violation']
            if vtype not in by_type:
                by_type[vtype] = []
            by_type[vtype].append(v)
        
        # Print violations by type
        violation_names = {
            'missing_entry_log': 'Missing Function Entry/Exit Logs',
            'missing_error_log': 'Missing Error Logs',
            'missing_external_log': 'Missing External Call Logs',
            'missing_state_log': 'Missing State Change Logs',
            'missing_security_log': 'Missing Security Event Logs',
            'missing_business_log': 'Missing Business Milestone Logs',
            'missing_performance_log': 'Missing Performance Anomaly Logs',
            'missing_config_log': 'Missing Configuration Change Logs',
            'missing_validation_log': 'Missing Validation Failure Logs',
            'missing_resource_log': 'Missing Resource Limit Logs',
            'sensitive_data_log': 'Sensitive Data in Logs'
        }
        
        for vtype, violations in by_type.items():
            print(f"\n❌ {violation_names.get(vtype, vtype)}: {len(violations)} violations")
            print("-" * 50)
            
            for v in violations[:5]:  # Show first 5
                print(f"  {v['file']}:{v['line']} - {v['function']}")
                print(f"    {v['message']}")
            
            if len(violations) > 5:
                print(f"  ... and {len(violations) - 5} more")
        
        # Summary
        print(f"\n🚫 LOGGING COMPLIANCE FAILED")
        print("=" * 60)
        print("ADD proper logging at ALL 10 mandatory points:")
        print("1. Function entry/exit (with context)")
        print("2. Error handling (with stack traces)")
        print("3. External API/DB calls")
        print("4. State mutations")
        print("5. Security events")
        print("6. Business milestones")
        print("7. Performance anomalies")
        print("8. Configuration changes")
        print("9. Validation failures")
        print("10. Resource limits")
        print("\nNEVER log sensitive data (passwords, tokens, PII, biometrics)")
        print("\nDetails: Load CLAUDE-CONTEXT-logging.md")


def main():
    parser = argparse.ArgumentParser(
        description="Check logging compliance for Zero Technical Debt"
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Path to check (default: current directory)"
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=0,
        help="Maximum allowed violations (default: 0)"
    )
    
    args = parser.parse_args()
    
    checker = LoggingComplianceChecker(Path(args.path))
    results = checker.scan_project()
    checker.generate_report()
    
    total_violations = len(results['violations'])
    if total_violations > args.threshold:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()