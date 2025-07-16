#!/usr/bin/env python3
"""
Automated Validation Pipeline for AI-First SDLC
Runs comprehensive checks to ensure compliance with framework requirements
"""

import subprocess
import sys
import json
import os
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
            "retrospective": self.check_retrospective
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
                "security", "code-quality", "dependencies", "commit-history"],
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