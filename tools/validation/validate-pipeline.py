#!/usr/bin/env python3
"""
Automated Validation Pipeline for AI-First SDLC
Runs comprehensive checks to ensure compliance with framework requirements
"""

import subprocess
import sys
import json
import os
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import argparse
from datetime import datetime


class ValidationPipeline:
    """Comprehensive validation for AI-First SDLC projects"""
    
    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path.cwd()
        self.results = []
        self.has_errors = False
        self.has_warnings = False
        self.is_empty_repo = False
    
    def run_validation(self, checks: List[str] = None) -> bool:
        """Run validation checks"""
        available_checks = {
            "branch": self.check_branch_compliance,
            "proposal": self.check_feature_proposal,
            "plan": self.check_implementation_plan,
            "ai-docs": self.check_ai_documentation,
            "tests": self.check_test_coverage,
            "security": self.check_security_scan,
            "code-quality": self.check_code_quality,
            "dependencies": self.check_dependencies,
            "commit-history": self.check_commit_compliance,
            "retrospective": self.check_retrospective,
            "design-docs": self.check_design_documentation,
            "technical-debt": self.check_technical_debt,
            "type-safety": self.check_type_safety,
            "architecture": self.check_architecture_documentation
        }
        
        # Default to all checks
        if not checks:
            checks = list(available_checks.keys())
        
        # Check if this is an empty repository
        self._detect_empty_repository()
        
        print("🔍 AI-First SDLC Validation Pipeline")
        print("=" * 50)
        
        if self.is_empty_repo:
            print("\n📦 Empty repository detected - adjusting validation...")
        
        for check_name in checks:
            if check_name in available_checks:
                print(f"\n▶️  Running {check_name} check...")
                available_checks[check_name]()
        
        # Print summary
        self.print_summary()
        
        return not self.has_errors
    
    def check_branch_compliance(self):
        """Check if on a feature branch"""
        try:
            result = subprocess.run(
                ["git", "symbolic-ref", "--short", "HEAD"],
                capture_output=True,
                text=True,
                check=True
            )
            branch = result.stdout.strip()
            
            if branch in ["main", "master"]:
                self.add_error(
                    "Branch Compliance",
                    f"Working directly on '{branch}' branch",
                    "Create a feature branch: git checkout -b feature/your-feature"
                )
            elif not branch.startswith(("feature/", "fix/", "enhancement/")):
                self.add_warning(
                    "Branch Compliance",
                    f"Non-standard branch name: '{branch}'",
                    "Consider using feature/, fix/, or enhancement/ prefix"
                )
            else:
                self.add_success("Branch Compliance", f"Valid branch: {branch}")
                
        except subprocess.CalledProcessError:
            self.add_error("Branch Compliance", "Not in a git repository", "Initialize git: git init")
    
    def check_feature_proposal(self):
        """Check for feature proposal"""
        branch = self._get_current_branch()
        if not branch or branch in ["main", "master"]:
            self.add_skip("Feature Proposal", "Not on feature branch")
            return
        
        # Look for proposal
        proposal_dirs = ["docs/feature-proposals", "feature-proposals", "proposals"]
        found = False
        
        for dir_path in proposal_dirs:
            if Path(dir_path).exists():
                for file in Path(dir_path).glob("*.md"):
                    try:
                        with open(file, 'r') as f:
                            content = f.read()
                            if branch in content:
                                found = True
                                self.add_success("Feature Proposal", f"Found in {file}")
                                break
                    except:
                        continue
                if found:
                    break
        
        if not found:
            self.add_error(
                "Feature Proposal",
                "No proposal found for current branch",
                "Create a proposal in docs/feature-proposals/"
            )
    
    def check_implementation_plan(self):
        """Check for implementation plan"""
        # First check if we have a complex feature proposal
        branch = self._get_current_branch()
        requires_plan = False
        proposal_content = ""
        
        if branch and branch not in ["main", "master"]:
            # Look for current feature proposal
            proposal_dirs = ["docs/feature-proposals", "feature-proposals", "proposals"]
            for dir_path in proposal_dirs:
                path = self.project_root / dir_path
                if path.exists():
                    for file in path.glob("*.md"):
                        try:
                            content = file.read_text().lower()
                            # Check if proposal indicates complexity
                            complexity_indicators = [
                                'complex', 'multi-phase', 'multiple components',
                                'architecture change', 'breaking change',
                                'phases', 'migration', 'refactor'
                            ]
                            if any(indicator in content for indicator in complexity_indicators):
                                requires_plan = True
                                proposal_content = file.name
                                break
                        except:
                            continue
                if requires_plan:
                    break
        
        # Now check for plans
        plan_dir = self.project_root / "plan"
        
        if not plan_dir.exists():
            if requires_plan:
                self.add_error(
                    "Implementation Plan",
                    f"Complex feature '{proposal_content}' requires plan directory",
                    "Create plan/ directory and implementation plan"
                )
            else:
                self.add_skip("Implementation Plan", "No plans required (simple feature)")
            return
        
        plans = list(plan_dir.glob("*.md"))
        if requires_plan and not plans:
            self.add_error(
                "Implementation Plan",
                f"Complex feature '{proposal_content}' requires implementation plan",
                "Create plan in plan/ directory before implementing"
            )
        elif plans:
            self.add_success("Implementation Plan", f"Found {len(plans)} plan(s)")
        else:
            self.add_skip("Implementation Plan", "No plans required (simple feature)")
    
    def check_ai_documentation(self):
        """Check for AI instruction files"""
        ai_files = ["CLAUDE.md", "GEMINI.md", "GPT.md"]
        found_files = []
        
        for ai_file in ai_files:
            if (self.project_root / ai_file).exists():
                found_files.append(ai_file)
        
        if found_files:
            self.add_success("AI Documentation", f"Found: {', '.join(found_files)}")
        else:
            self.add_error(
                "AI Documentation",
                "No AI instruction file found",
                "Create CLAUDE.md, GEMINI.md, or GPT.md from templates"
            )
    
    def check_test_coverage(self):
        """Check test coverage"""
        # Check for framework verification test in empty repos
        if self.is_empty_repo:
            framework_tests = [
                'test_framework_setup.py',
                'test/framework.test.js',
                'tests/framework.test.js',
                'test-framework.sh'
            ]
            
            for test_file in framework_tests:
                if (self.project_root / test_file).exists():
                    # Try to run the framework test
                    if test_file.endswith('.py'):
                        cmd = ["python", test_file]
                    elif test_file.endswith('.js'):
                        cmd = ["node", test_file]
                    elif test_file.endswith('.sh'):
                        cmd = ["bash", test_file]
                    else:
                        continue
                    
                    try:
                        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                        if result.returncode == 0:
                            self.add_success("Test Coverage", "Framework verification test passing")
                        else:
                            self.add_warning("Test Coverage", "Framework test failing", f"Fix {test_file}")
                        return
                    except:
                        continue
            
            # No framework test found
            self.add_warning(
                "Test Coverage",
                "No framework verification test found",
                "Run setup-smart.py --quickstart to create initial test"
            )
            return
        
        # Regular test checking for non-empty repos
        test_commands = [
            (["pytest", "--version"], ["pytest", "--cov", "--cov-report=term-missing"]),
            (["go", "version"], ["go", "test", "-cover", "./..."]),
            (["npm", "--version"], ["npm", "test"]),
            (["make", "--version"], ["make", "test"])
        ]
        
        for check_cmd, test_cmd in test_commands:
            try:
                # Check if tool exists
                subprocess.run(check_cmd, capture_output=True, check=True)
                
                # Run tests
                result = subprocess.run(
                    test_cmd,
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                if result.returncode == 0:
                    self.add_success("Test Coverage", "Tests passing")
                else:
                    self.add_error("Test Coverage", "Tests failing", "Fix failing tests")
                return
                
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
                continue
        
        self.add_warning("Test Coverage", "No test runner found", "Set up testing framework")
    
    def check_security_scan(self):
        """Run security scans"""
        # Check for secrets
        try:
            result = subprocess.run(
                ["git", "diff", "--cached", "--name-only"],
                capture_output=True,
                text=True,
                check=True
            )
            
            files = result.stdout.strip().split('\n')
            suspicious_patterns = [
                "password", "secret", "key", "token", "api_key",
                "private_key", "access_key"
            ]
            
            for file in files:
                if not file or not Path(file).exists():
                    continue
                    
                try:
                    with open(file, 'r') as f:
                        content = f.read().lower()
                        for pattern in suspicious_patterns:
                            if pattern in content:
                                self.add_warning(
                                    "Security Scan",
                                    f"Potential secret in {file}",
                                    "Review file for hardcoded secrets"
                                )
                                return
                except:
                    continue
            
            self.add_success("Security Scan", "No obvious secrets detected")
            
        except subprocess.CalledProcessError:
            self.add_skip("Security Scan", "No staged files to scan")
    
    def check_code_quality(self):
        """Check code quality with linters"""
        # Skip linting in empty repos
        if self.is_empty_repo:
            self.add_skip("Code Quality", "Empty repository - no code to lint")
            return
            
        linters = [
            (["flake8", "--version"], ["flake8", "."]),
            (["pylint", "--version"], ["pylint", "*.py"]),
            (["golangci-lint", "version"], ["golangci-lint", "run"]),
            (["eslint", "--version"], ["eslint", "."])
        ]
        
        for check_cmd, lint_cmd in linters:
            try:
                # Check if linter exists
                subprocess.run(check_cmd, capture_output=True, check=True)
                
                # Run linter
                result = subprocess.run(
                    lint_cmd,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode == 0:
                    self.add_success("Code Quality", f"{lint_cmd[0]} passed")
                else:
                    self.add_warning("Code Quality", f"{lint_cmd[0]} found issues", "Fix linting issues")
                return
                
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
                continue
        
        self.add_skip("Code Quality", "No linters configured")
    
    def check_dependencies(self):
        """Check for dependency issues"""
        # Skip or adjust for empty repos
        if self.is_empty_repo:
            # Just check if dependency file exists and is valid
            dep_files = [
                ("requirements.txt", None),
                ("package.json", None),
                ("go.mod", None),
                ("Gemfile", None)
            ]
            
            for dep_file, _ in dep_files:
                if (self.project_root / dep_file).exists():
                    self.add_skip("Dependencies", f"Empty repository - {dep_file} exists but no code to check")
                    return
            
            self.add_skip("Dependencies", "Empty repository - no dependencies")
            return
            
        dep_files = [
            ("requirements.txt", "pip check"),
            ("package.json", "npm audit"),
            ("go.mod", "go mod verify"),
            ("Gemfile", "bundle check")
        ]
        
        for dep_file, check_cmd in dep_files:
            if (self.project_root / dep_file).exists():
                try:
                    result = subprocess.run(
                        check_cmd.split(),
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    
                    if result.returncode == 0:
                        self.add_success("Dependencies", f"{dep_file} dependencies OK")
                    else:
                        self.add_warning(
                            "Dependencies",
                            f"Issues found in {dep_file}",
                            f"Run: {check_cmd}"
                        )
                    return
                    
                except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
                    continue
        
        self.add_skip("Dependencies", "No dependency files found")
    
    def check_commit_compliance(self):
        """Check commit message compliance"""
        try:
            # Get last 5 commits
            result = subprocess.run(
                ["git", "log", "--oneline", "-5"],
                capture_output=True,
                text=True,
                check=True
            )
            
            commits = result.stdout.strip().split('\n')
            non_compliant = []
            
            # Simple conventional commit check
            prefixes = ["feat:", "fix:", "docs:", "style:", "refactor:", 
                       "test:", "chore:", "perf:", "ci:", "build:"]
            
            for commit in commits:
                if commit and not any(prefix in commit.lower() for prefix in prefixes):
                    parts = commit.split(' ', 1)
                    if len(parts) > 1:
                        non_compliant.append(parts[1][:50])
            
            if non_compliant:
                self.add_warning(
                    "Commit Compliance",
                    f"{len(non_compliant)} non-conventional commits",
                    "Use conventional commit format: type: description"
                )
            else:
                self.add_success("Commit Compliance", "All commits follow conventions")
                
        except subprocess.CalledProcessError:
            self.add_skip("Commit Compliance", "No commit history")
    
    def check_retrospective(self):
        """Check for retrospective document"""
        branch = self._get_current_branch()
        if not branch or branch in ["main", "master"]:
            self.add_skip("Retrospective", "Not on feature branch")
            return
        
        # Look for retrospective
        retro_dirs = ["retrospectives", "docs/retrospectives", "retros"]
        found = False
        
        for dir_path in retro_dirs:
            if Path(dir_path).exists():
                for file in Path(dir_path).glob("*.md"):
                    try:
                        with open(file, 'r') as f:
                            content = f.read()
                            # Check if retrospective mentions the branch or feature
                            branch_name = branch.replace("feature/", "").replace("fix/", "")
                            if branch_name in content or branch in content:
                                found = True
                                # Check retrospective freshness
                                try:
                                    from datetime import datetime, timedelta
                                    file_mtime = datetime.fromtimestamp(file.stat().st_mtime)
                                    now = datetime.now()
                                    days_old = (now - file_mtime).days
                                    
                                    if days_old > 3:
                                        self.add_warning(
                                            "Retrospective",
                                            f"Retrospective not updated in {days_old} days",
                                            "Update retrospective with recent progress"
                                        )
                                    else:
                                        self.add_success("Retrospective", f"Found in {file}")
                                except:
                                    self.add_success("Retrospective", f"Found in {file}")
                                break
                    except:
                        continue
                if found:
                    break
        
        if not found:
            # Check if this is a PR validation (CI environment)
            is_pr = os.environ.get('GITHUB_EVENT_NAME') == 'pull_request' or \
                    os.environ.get('CI') == 'true'
            
            if is_pr:
                self.add_error(
                    "Retrospective",
                    "No retrospective found for current branch",
                    "Create a retrospective in retrospectives/ before creating PR"
                )
            else:
                self.add_warning(
                    "Retrospective",
                    "No retrospective found for current branch",
                    "Remember to create a retrospective before PR"
                )
    
    def check_design_documentation(self):
        """Check design documents for excessive implementation details"""
        if self.is_empty_repo:
            return
            
        import glob
        import re
        
        print("\n8️⃣  Checking Design Documentation...")
        
        # Find design documentation files
        design_patterns = [
            '**/design-*.md',
            '**/design_*.md',
            '**/designs/*.md',
            '**/architecture/*.md',
            '**/specs/*.md'
        ]
        
        design_files = []
        for pattern in design_patterns:
            design_files.extend(glob.glob(pattern, recursive=True))
        
        if not design_files:
            print("   No design documentation found")
            return
        
        for file_path in design_files:
            # Skip template files
            if 'templates/' in file_path or 'examples/' in file_path:
                continue
                
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Count total lines (excluding empty lines)
                lines = content.splitlines()
                total_lines = len([line for line in lines if line.strip()])
                
                if total_lines == 0:
                    continue
                
                # Find code blocks (excluding mermaid/diagram blocks)
                code_block_pattern = r'```(?!mermaid|diagram|plantuml|graphviz|dot|svg|ascii)[^\n]*\n([\s\S]*?)```'
                code_blocks = re.findall(code_block_pattern, content, re.MULTILINE)
                
                # Count lines in code blocks
                code_lines = 0
                for block in code_blocks:
                    block_lines = block.splitlines()
                    code_lines += len([line for line in block_lines if line.strip()])
                
                # Calculate ratio
                code_ratio = code_lines / total_lines if total_lines > 0 else 0
                
                # Check if too much code
                if code_ratio > 0.2:  # More than 20% code
                    relative_path = os.path.relpath(file_path, self.project_root)
                    self.add_warning(
                        "Design Documentation",
                        f"{relative_path} contains {code_ratio:.0%} code content",
                        "Consider moving implementation details to technical docs or code comments"
                    )
                    
                # Check for specific implementation patterns
                impl_patterns = [
                    (r'\bclass\s+\w+', "class definitions"),
                    (r'\bdef\s+\w+\s*\(', "function definitions"),
                    (r'\bimport\s+\w+', "import statements"),
                    (r'\bCREATE\s+TABLE', "SQL DDL statements"),
                    (r'\bSELECT\s+.*\s+FROM', "SQL queries"),
                    (r'npm\s+install', "package installation commands"),
                    (r'pip\s+install', "package installation commands")
                ]
                
                for pattern, description in impl_patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        # Check if it's in a code block (which we already warned about)
                        if not any(re.search(pattern, block, re.IGNORECASE) for block in code_blocks):
                            relative_path = os.path.relpath(file_path, self.project_root)
                            self.add_warning(
                                "Design Documentation",
                                f"{relative_path} contains {description}",
                                "Design docs should focus on WHAT and WHY, not HOW"
                            )
                            break  # Only warn once per file
                            
            except Exception as e:
                self.add_warning(
                    "Design Documentation",
                    f"Could not analyze {file_path}",
                    str(e)
                )
    
    def check_technical_debt(self):
        """Check for technical debt indicators"""
        if self.is_empty_repo:
            self.add_skip("Technical Debt", "Empty repository - no code to check")
            return
        
        debt_indicators = []
        files_checked = 0
        
        # Check all code files
        code_patterns = ['**/*.py', '**/*.js', '**/*.ts', '**/*.jsx', '**/*.tsx',
                        '**/*.go', '**/*.rs', '**/*.java', '**/*.rb', '**/*.cpp']
        
        for pattern in code_patterns:
            for file_path in Path(self.project_root).glob(pattern):
                # Skip framework tools and node_modules
                if any(skip in str(file_path) for skip in ['node_modules', '.git', '__pycache__', 'venv']):
                    continue
                
                files_checked += 1
                try:
                    content = file_path.read_text(encoding='utf-8')
                    
                    # Check for TODO/FIXME comments
                    todos = len(re.findall(r'(TODO|FIXME|HACK|XXX|BUG):', content, re.IGNORECASE))
                    if todos > 0:
                        debt_indicators.append(f"{file_path.name}: {todos} TODO/FIXME comments")
                    
                    # Check for commented-out code (simple heuristic)
                    comment_patterns = {
                        '.py': r'^\s*#\s*(import|def|class|if|for|while|return)',
                        '.js': r'^\s*//\s*(import|function|class|if|for|while|return)',
                        '.ts': r'^\s*//\s*(import|function|class|if|for|while|return)',
                        '.go': r'^\s*//\s*(import|func|type|if|for|return)',
                    }
                    
                    suffix = file_path.suffix
                    if suffix in comment_patterns:
                        commented_code = len(re.findall(comment_patterns[suffix], content, re.MULTILINE))
                        if commented_code > 0:
                            debt_indicators.append(f"{file_path.name}: {commented_code} lines of commented code")
                    
                    # Check for any types (TypeScript)
                    if suffix in ['.ts', '.tsx']:
                        any_types = len(re.findall(r':\s*any\b', content))
                        if any_types > 0:
                            debt_indicators.append(f"{file_path.name}: {any_types} 'any' types")
                    
                    # Check for ignored errors
                    ignore_patterns = [
                        r'@ts-ignore',
                        r'@ts-nocheck',
                        r'# type: ignore',
                        r'# noqa',
                        r'# pylint: disable',
                        r'// eslint-disable',
                    ]
                    
                    for pattern in ignore_patterns:
                        ignores = len(re.findall(pattern, content))
                        if ignores > 0:
                            debt_indicators.append(f"{file_path.name}: {ignores} error suppressions")
                            break
                
                except Exception:
                    continue
        
        if debt_indicators:
            self.add_error(
                "Technical Debt",
                f"Found {len(debt_indicators)} debt indicators",
                "Remove all TODOs, commented code, and type suppressions"
            )
            # Show first 5 examples
            for indicator in debt_indicators[:5]:
                print(f"   - {indicator}")
            if len(debt_indicators) > 5:
                print(f"   ... and {len(debt_indicators) - 5} more")
        elif files_checked > 0:
            self.add_success("Technical Debt", f"No debt indicators in {files_checked} files")
        else:
            self.add_skip("Technical Debt", "No code files to check")
    
    def check_type_safety(self):
        """Check for type safety issues"""
        if self.is_empty_repo:
            self.add_skip("Type Safety", "Empty repository - no code to check")
            return
        
        type_issues = []
        
        # TypeScript/JavaScript projects
        ts_config = self.project_root / "tsconfig.json"
        if ts_config.exists():
            try:
                config_content = ts_config.read_text()
                config_json = json.loads(config_content)
                
                # Check strict mode
                compiler_options = config_json.get('compilerOptions', {})
                if not compiler_options.get('strict', False):
                    type_issues.append("TypeScript strict mode is disabled")
                
                # Check for weak type settings
                weak_settings = {
                    'noImplicitAny': False,
                    'strictNullChecks': False,
                    'strictFunctionTypes': False,
                    'strictBindCallApply': False,
                    'strictPropertyInitialization': False,
                    'noImplicitThis': False,
                    'alwaysStrict': False
                }
                
                for setting, expected in weak_settings.items():
                    if compiler_options.get(setting, True) == expected:
                        type_issues.append(f"TypeScript {setting} is not enabled")
                
            except Exception:
                type_issues.append("Could not parse tsconfig.json")
        
        # Python projects
        mypy_ini = self.project_root / "mypy.ini"
        setup_cfg = self.project_root / "setup.cfg"
        pyproject_toml = self.project_root / "pyproject.toml"
        
        if any(f.exists() for f in [mypy_ini, setup_cfg, pyproject_toml]):
            # Check if mypy is configured strictly
            mypy_config_found = False
            
            if mypy_ini.exists():
                content = mypy_ini.read_text()
                if "disallow_untyped_defs" not in content or "False" in content:
                    type_issues.append("mypy not configured for strict type checking")
                else:
                    mypy_config_found = True
            
            if not mypy_config_found and setup_cfg.exists():
                content = setup_cfg.read_text()
                if "[mypy]" not in content:
                    type_issues.append("mypy configuration missing")
        
        # Check actual code for type annotations (Python)
        py_files = list(Path(self.project_root).glob("**/*.py"))
        py_files = [f for f in py_files if "venv" not in str(f) and "__pycache__" not in str(f)]
        
        if py_files:
            missing_annotations = 0
            for py_file in py_files[:10]:  # Sample first 10 files
                try:
                    content = py_file.read_text()
                    # Simple heuristic: functions without type hints
                    functions = re.findall(r'def\s+\w+\s*\([^)]*\)\s*:', content)
                    typed_functions = re.findall(r'def\s+\w+\s*\([^)]*\)\s*->\s*\w+\s*:', content)
                    
                    if functions and len(typed_functions) < len(functions) * 0.8:
                        missing_annotations += 1
                except Exception:
                    continue
            
            if missing_annotations > len(py_files) * 0.2:
                type_issues.append(f"{missing_annotations} Python files lack type annotations")
        
        if type_issues:
            self.add_error(
                "Type Safety",
                f"Found {len(type_issues)} type safety issues",
                "Enable strict type checking in all languages"
            )
            for issue in type_issues:
                print(f"   - {issue}")
        else:
            self.add_success("Type Safety", "Strong typing enforced")
    
    def check_architecture_documentation(self):
        """Check if architecture documents exist and are complete"""
        arch_dir = self.project_root / "docs" / "architecture"
        
        if not arch_dir.exists():
            self.add_error(
                "Architecture Documentation",
                "Architecture directory missing",
                "Run: python tools/validation/validate-architecture.py for details"
            )
            return
        
        # Run architecture validator
        try:
            result = subprocess.run(
                ["python", "tools/validation/validate-architecture.py"],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            
            if result.returncode != 0:
                self.add_error(
                    "Architecture Documentation",
                    "Architecture validation failed",
                    "Complete all architecture documents before coding"
                )
            else:
                self.add_success("Architecture Documentation", "All architecture documents complete")
                
        except FileNotFoundError:
            self.add_warning(
                "Architecture Documentation",
                "Architecture validator not found",
                "Ensure validate-architecture.py exists"
            )
    
    def _get_current_branch(self) -> Optional[str]:
        """Get current git branch"""
        try:
            result = subprocess.run(
                ["git", "symbolic-ref", "--short", "HEAD"],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except:
            return None
    
    def _detect_empty_repository(self):
        """Detect if this is an empty repository with only framework files"""
        import glob
        
        # Code file patterns
        code_patterns = [
            '*.py', '*.js', '*.ts', '*.jsx', '*.tsx',
            '*.go', '*.rs', '*.java', '*.cs', '*.cpp',
            '*.c', '*.h', '*.rb', '*.php', '*.swift'
        ]
        
        # Count code files (excluding framework tools)
        code_file_count = 0
        for pattern in code_patterns:
            files = glob.glob(f'**/{pattern}', recursive=True)
            # Exclude framework tools directory
            code_files = [f for f in files if not f.startswith(('tools/', '.ai-sdlc-temp/'))]
            code_file_count += len(code_files)
        
        # Check if we only have framework files
        framework_files = ['CLAUDE.md', 'README.md', '.gitignore']
        has_framework = all((self.project_root / f).exists() for f in framework_files[:2])  # At least CLAUDE.md and README
        
        self.is_empty_repo = code_file_count == 0 and has_framework
    
    def add_success(self, check: str, message: str):
        """Add success result"""
        self.results.append(("✅", check, message, None))
    
    def add_error(self, check: str, message: str, fix: str):
        """Add error result"""
        self.has_errors = True
        self.results.append(("❌", check, message, fix))
    
    def add_warning(self, check: str, message: str, fix: str):
        """Add warning result"""
        self.has_warnings = True
        self.results.append(("⚠️ ", check, message, fix))
    
    def add_skip(self, check: str, reason: str):
        """Add skipped check"""
        self.results.append(("⏭️ ", check, reason, None))
    
    def print_summary(self):
        """Print validation summary"""
        print("\n" + "=" * 50)
        print("📊 Validation Summary")
        print("=" * 50)
        
        for icon, check, message, fix in self.results:
            print(f"{icon} {check}: {message}")
            if fix:
                print(f"   └─ Fix: {fix}")
        
        print("\n" + "-" * 50)
        
        if self.has_errors:
            print("❌ Validation FAILED - errors must be fixed")
            print("\n💡 Run with --help to see available options")
        elif self.has_warnings:
            print("⚠️  Validation passed with warnings")
            print("\n💡 Consider addressing warnings for better compliance")
        else:
            print("✅ All validation checks passed!")
            print("\n🚀 Your project is AI-First SDLC compliant!")
    
    def export_results(self, format: str = "json") -> str:
        """Export results in specified format"""
        if format == "json":
            data = {
                "timestamp": datetime.now().isoformat(),
                "has_errors": self.has_errors,
                "has_warnings": self.has_warnings,
                "results": [
                    {
                        "status": icon.strip(),
                        "check": check,
                        "message": message,
                        "fix": fix
                    }
                    for icon, check, message, fix in self.results
                ]
            }
            return json.dumps(data, indent=2)
        
        elif format == "markdown":
            md = f"# Validation Report\n\n"
            md += f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            
            md += "## Results\n\n"
            for icon, check, message, fix in self.results:
                md += f"- {icon} **{check}**: {message}\n"
                if fix:
                    md += f"  - Fix: {fix}\n"
            
            md += f"\n## Summary\n"
            if self.has_errors:
                md += "❌ **FAILED** - Errors must be fixed\n"
            elif self.has_warnings:
                md += "⚠️  **PASSED** with warnings\n"
            else:
                md += "✅ **PASSED** - Fully compliant\n"
            
            return md
        
        else:
            raise ValueError(f"Unsupported format: {format}")


def main():
    parser = argparse.ArgumentParser(
        description="AI-First SDLC Validation Pipeline"
    )
    parser.add_argument(
        "--checks",
        nargs="+",
        choices=["branch", "proposal", "plan", "ai-docs", "tests", 
                "security", "code-quality", "dependencies", "commit-history", "retrospective", "design-docs",
                "technical-debt", "type-safety", "architecture"],
        help="Specific checks to run (default: all)"
    )
    parser.add_argument(
        "--export",
        choices=["json", "markdown"],
        help="Export results to format"
    )
    parser.add_argument(
        "--output",
        help="Output file for export (default: stdout)"
    )
    parser.add_argument(
        "--ci",
        action="store_true",
        help="CI mode - exit with error code on failures"
    )
    
    args = parser.parse_args()
    
    # Run validation
    pipeline = ValidationPipeline()
    success = pipeline.run_validation(args.checks)
    
    # Export if requested
    if args.export:
        output = pipeline.export_results(args.export)
        
        if args.output:
            with open(args.output, 'w') as f:
                f.write(output)
            print(f"\n📄 Results exported to: {args.output}")
        else:
            print(f"\n📄 Exported Results ({args.export}):")
            print(output)
    
    # Exit code for CI
    if args.ci and not success:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()