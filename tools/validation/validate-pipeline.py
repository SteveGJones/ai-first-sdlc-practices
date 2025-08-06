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
import configparser
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any
import argparse
from datetime import datetime


class ValidationPipeline:
    """Comprehensive validation for AI-First SDLC projects"""

    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path.cwd()
        self.results: List[Dict[str, Any]] = []
        self.has_errors = False
        self.has_warnings = False
        self.is_empty_repo = False
        self.is_framework_repo = self._detect_framework_repository()

    def _detect_framework_repository(self) -> bool:
        """Detect if this is the AI-First SDLC framework repository itself"""
        # Check for framework-specific markers
        framework_markers = [
            "tools/validation/validate-pipeline.py",
            "tools/validation/check-technical-debt.py",
            "templates/CLAUDE.md",
            "setup-smart.py",
            "docs/FRAMEWORK-COMPLIANCE-POLICY.md",
        ]

        # Count how many framework markers exist
        marker_count = sum(
            1 for marker in framework_markers if (self.project_root / marker).exists()
        )

        # If we have most framework markers, this is the framework repo
        return marker_count >= 3

    def run_validation(self, checks: Optional[List[str]] = None) -> bool:
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
            "architecture": self.check_architecture_documentation,
            "logging": self.check_logging_compliance,
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

    def check_branch_compliance(self) -> None:
        """Check if on a feature branch"""
        # Check if we're in GitHub Actions CI environment
        if os.environ.get("GITHUB_ACTIONS") == "true":
            # In GitHub Actions, get branch from environment variables
            if os.environ.get("GITHUB_EVENT_NAME") == "pull_request":
                # For PRs, use the head ref
                branch = os.environ.get("GITHUB_HEAD_REF", "")
            else:
                # For pushes, extract from GITHUB_REF
                ref = os.environ.get("GITHUB_REF", "")
                if ref.startswith("refs/heads/"):
                    branch = ref.replace("refs/heads/", "")
                else:
                    branch = ""

            if not branch:
                self.add_warning(
                    "Branch Compliance",
                    "Unable to detect branch in CI environment",
                    "Check GITHUB_REF environment variable",
                )
                return
        else:
            # Local environment - use git command
            try:
                result = subprocess.run(
                    ["git", "symbolic-ref", "--short", "HEAD"],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                branch = result.stdout.strip()
            except subprocess.CalledProcessError:
                self.add_error(
                    "Branch Compliance",
                    "Not in a git repository",
                    "Initialize git: git init",
                )
                return

        # Validate branch name
        if branch in ["main", "master"]:
            self.add_error(
                "Branch Compliance",
                f"Working directly on '{branch}' branch",
                "Create a feature branch: git checkout -b feature/your-feature",
            )
        elif not branch.startswith(("feature/", "fix/", "enhancement/")):
            self.add_warning(
                "Branch Compliance",
                f"Non-standard branch name: '{branch}'",
                "Consider using feature/, fix/, or enhancement/ prefix",
            )
        else:
            self.add_success("Branch Compliance", f"Valid branch: {branch}")

    def check_feature_proposal(self) -> None:
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
                        with open(file, "r") as f:
                            content = f.read()
                            if branch in content:
                                found = True
                                self.add_success("Feature Proposal", f"Found in {file}")
                                break
                    except Exception:
                        continue
                if found:
                    break

        if not found:
            self.add_error(
                "Feature Proposal",
                "No proposal found for current branch",
                "Create a proposal in docs/feature-proposals/",
            )

    def check_implementation_plan(self) -> None:
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
                                "complex",
                                "multi-phase",
                                "multiple components",
                                "architecture change",
                                "breaking change",
                                "phases",
                                "migration",
                                "refactor",
                            ]
                            if any(
                                indicator in content
                                for indicator in complexity_indicators
                            ):
                                requires_plan = True
                                proposal_content = file.name
                                break
                        except Exception:
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
                    "Create plan/ directory and implementation plan",
                )
            else:
                self.add_skip(
                    "Implementation Plan", "No plans required (simple feature)"
                )
            return

        plans = list(plan_dir.glob("*.md"))
        if requires_plan and not plans:
            self.add_error(
                "Implementation Plan",
                f"Complex feature '{proposal_content}' requires implementation plan",
                "Create plan in plan/ directory before implementing",
            )
        elif plans:
            self.add_success("Implementation Plan", f"Found {len(plans)} plan(s)")
        else:
            self.add_skip("Implementation Plan", "No plans required (simple feature)")

    def check_ai_documentation(self) -> None:
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
                "Create CLAUDE.md, GEMINI.md, or GPT.md from templates",
            )

    def check_test_coverage(self) -> None:
        """Check test coverage"""
        # Check for framework verification test in empty repos
        if self.is_empty_repo:
            framework_tests = [
                "test_framework_setup.py",
                "test/framework.test.js",
                "tests/framework.test.js",
                "test-framework.sh",
            ]

            for test_file in framework_tests:
                if (self.project_root / test_file).exists():
                    # Try to run the framework test
                    if test_file.endswith(".py"):
                        cmd = ["python", test_file]
                    elif test_file.endswith(".js"):
                        cmd = ["node", test_file]
                    elif test_file.endswith(".sh"):
                        cmd = ["bash", test_file]
                    else:
                        continue

                    try:
                        result = subprocess.run(
                            cmd, capture_output=True, text=True, timeout=30
                        )
                        if result.returncode == 0:
                            self.add_success(
                                "Test Coverage", "Framework verification test passing"
                            )
                        else:
                            self.add_warning(
                                "Test Coverage",
                                "Framework test failing",
                                f"Fix {test_file}",
                            )
                        return
                    except Exception:
                        continue

            # No framework test found
            self.add_warning(
                "Test Coverage",
                "No framework verification test found",
                "Run setup-smart.py --quickstart to create initial test",
            )
            return

        # Regular test checking for non-empty repos
        test_commands = [
            (
                ["python", "-m", "pytest", "--version"],
                ["python", "-m", "pytest", "tests/"],
            ),
            (["go", "version"], ["go", "test", "-cover", "./..."]),
            (["npm", "--version"], ["npm", "test"]),
            (["make", "--version"], ["make", "test"]),
        ]

        for check_cmd, test_cmd in test_commands:
            try:
                # Check if tool exists
                subprocess.run(check_cmd, capture_output=True, check=True)

                # For framework repository, check if tests directory exists
                if (
                    test_cmd[0] == "pytest"
                    and not (self.project_root / "tests").exists()
                ):
                    self.add_warning(
                        "Test Coverage",
                        "No tests directory found",
                        "Create tests directory with test files",
                    )
                    return

                # Run tests
                result = subprocess.run(
                    test_cmd, capture_output=True, text=True, timeout=60
                )

                if result.returncode == 0:
                    self.add_success("Test Coverage", "Tests passing")
                else:
                    # In CI environment, provide more context about failure
                    if os.environ.get("CI") == "true":
                        stderr_msg = (
                            result.stderr[:200] if result.stderr else "No error output"
                        )
                        self.add_error(
                            "Test Coverage",
                            f"Tests failing: {stderr_msg}",
                            "Fix failing tests",
                        )
                    else:
                        self.add_error(
                            "Test Coverage", "Tests failing", "Fix failing tests"
                        )
                return

            except (
                subprocess.CalledProcessError,
                subprocess.TimeoutExpired,
                FileNotFoundError,
            ):
                continue

        self.add_warning(
            "Test Coverage", "No test runner found", "Set up testing framework"
        )

    def check_security_scan(self) -> None:
        """Run security scans"""
        # Check for secrets
        try:
            result = subprocess.run(
                ["git", "diff", "--cached", "--name-only"],
                capture_output=True,
                text=True,
                check=True,
            )

            files = result.stdout.strip().split("\n")
            suspicious_patterns = [
                "password",
                "secret",
                "key",
                "token",
                "api_key",
                "private_key",
                "access_key",
            ]

            for file in files:
                if not file or not Path(file).exists():
                    continue

                try:
                    with open(file, "r") as f:
                        content = f.read().lower()
                        for pattern in suspicious_patterns:
                            if pattern in content:
                                self.add_warning(
                                    "Security Scan",
                                    f"Potential secret in {file}",
                                    "Review file for hardcoded secrets",
                                )
                                return
                except Exception:
                    continue

            self.add_success("Security Scan", "No obvious secrets detected")

        except subprocess.CalledProcessError:
            self.add_skip("Security Scan", "No staged files to scan")

    def check_code_quality(self) -> None:
        """Check code quality with linters"""
        # Skip linting in empty repos
        if self.is_empty_repo:
            self.add_skip("Code Quality", "Empty repository - no code to lint")
            return

        linters = [
            (["flake8", "--version"], ["flake8", "."]),
            (["pylint", "--version"], ["pylint", "*.py"]),
            (["golangci-lint", "version"], ["golangci-lint", "run"]),
            (["eslint", "--version"], ["eslint", "."]),
        ]

        for check_cmd, lint_cmd in linters:
            try:
                # Check if linter exists
                subprocess.run(check_cmd, capture_output=True, check=True)

                # Run linter
                result = subprocess.run(
                    lint_cmd, capture_output=True, text=True, timeout=30
                )

                if result.returncode == 0:
                    self.add_success("Code Quality", f"{lint_cmd[0]} passed")
                else:
                    self.add_warning(
                        "Code Quality",
                        f"{lint_cmd[0]} found issues",
                        "Fix linting issues",
                    )
                return

            except (
                subprocess.CalledProcessError,
                subprocess.TimeoutExpired,
                FileNotFoundError,
            ):
                continue

        self.add_skip("Code Quality", "No linters configured")

    def check_dependencies(self) -> None:
        """Check for dependency issues"""
        # Skip or adjust for empty repos
        if self.is_empty_repo:
            # Just check if dependency file exists and is valid
            dep_files: List[Tuple[str, Optional[str]]] = [
                ("requirements.txt", None),
                ("package.json", None),
                ("go.mod", None),
                ("Gemfile", None),
            ]

            for dep_file, _ in dep_files:
                if (self.project_root / dep_file).exists():
                    self.add_skip(
                        "Dependencies",
                        f"Empty repository - {dep_file} exists but no code to check",
                    )
                    return

            self.add_skip("Dependencies", "Empty repository - no dependencies")
            return

        dep_files_with_checks: List[Tuple[str, Optional[str]]] = [
            ("requirements.txt", "pip check"),
            ("package.json", "npm audit"),
            ("go.mod", "go mod verify"),
            ("Gemfile", "bundle check"),
        ]

        for dep_file, check_cmd in dep_files_with_checks:
            if (self.project_root / dep_file).exists() and check_cmd:
                try:
                    result = subprocess.run(
                        check_cmd.split(), capture_output=True, text=True, timeout=30
                    )

                    if result.returncode == 0:
                        self.add_success("Dependencies", f"{dep_file} dependencies OK")
                    else:
                        self.add_warning(
                            "Dependencies",
                            f"Issues found in {dep_file}",
                            f"Run: {check_cmd}",
                        )
                    return

                except (
                    subprocess.CalledProcessError,
                    subprocess.TimeoutExpired,
                    FileNotFoundError,
                ):
                    continue

        self.add_skip("Dependencies", "No dependency files found")

    def check_commit_compliance(self) -> None:
        """Check commit message compliance"""
        try:
            # Get last 5 commits
            result = subprocess.run(
                ["git", "log", "--oneline", "-5"],
                capture_output=True,
                text=True,
                check=True,
            )

            commits = result.stdout.strip().split("\n")
            non_compliant = []

            # Simple conventional commit check
            prefixes = [
                "feat:",
                "fix:",
                "docs:",
                "style:",
                "refactor:",
                "test:",
                "chore:",
                "perf:",
                "ci:",
                "build:",
            ]

            for commit in commits:
                if commit and not any(prefix in commit.lower() for prefix in prefixes):
                    parts = commit.split(" ", 1)
                    if len(parts) > 1:
                        non_compliant.append(parts[1][:50])

            if non_compliant:
                self.add_warning(
                    "Commit Compliance",
                    f"{len(non_compliant)} non-conventional commits",
                    "Use conventional commit format: type: description",
                )
            else:
                self.add_success("Commit Compliance", "All commits follow conventions")

        except subprocess.CalledProcessError:
            self.add_skip("Commit Compliance", "No commit history")

    def check_retrospective(self) -> None:
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
                        with open(file, "r") as f:
                            content = f.read()
                            # Check if retrospective mentions the branch or feature
                            branch_name = branch.replace("feature/", "").replace(
                                "fix/", ""
                            )
                            if branch_name in content or branch in content:
                                found = True
                                # Check retrospective freshness
                                try:

                                    file_mtime = datetime.fromtimestamp(
                                        file.stat().st_mtime
                                    )
                                    now = datetime.now()
                                    days_old = (now - file_mtime).days

                                    if days_old > 3:
                                        self.add_warning(
                                            "Retrospective",
                                            f"Retrospective not updated in {days_old} days",
                                            "Update retrospective with recent progress",
                                        )
                                    else:
                                        self.add_success(
                                            "Retrospective", f"Found in {file}"
                                        )
                                except Exception:
                                    self.add_success(
                                        "Retrospective", f"Found in {file}"
                                    )
                                break
                    except Exception:
                        continue
                if found:
                    break

        if not found:
            # Check if this is a PR validation (CI environment)
            is_pr = (
                os.environ.get("GITHUB_EVENT_NAME") == "pull_request"
                or os.environ.get("CI") == "true"
            )

            if is_pr:
                self.add_error(
                    "Retrospective",
                    "No retrospective found for current branch",
                    "Create a retrospective in retrospectives/ before creating PR",
                )
            else:
                self.add_warning(
                    "Retrospective",
                    "No retrospective found for current branch",
                    "Remember to create a retrospective before PR",
                )

    def check_design_documentation(self) -> None:
        """Check design documents for excessive implementation details"""
        if self.is_empty_repo:
            return

        import glob
        import re

        print("\n8️⃣  Checking Design Documentation...")

        # Find design documentation files
        design_patterns = [
            "**/design-*.md",
            "**/design_*.md",
            "**/designs/*.md",
            "**/architecture/*.md",
            "**/specs/*.md",
        ]

        design_files = []
        for pattern in design_patterns:
            design_files.extend(glob.glob(pattern, recursive=True))

        if not design_files:
            print("   No design documentation found")
            return

        for file_path in design_files:
            # Skip template files
            if "templates/" in file_path or "examples/" in file_path:
                continue

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                # Count total lines (excluding empty lines)
                lines = content.splitlines()
                total_lines = len([line for line in lines if line.strip()])

                if total_lines == 0:
                    continue

                # Find code blocks (excluding mermaid/diagram blocks)
                code_block_pattern = r"```(?!mermaid|diagram|plantuml|graphviz|dot|svg|ascii)[^\n]*\n([\s\S]*?)```"
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
                        "Consider moving implementation details to technical docs or code comments",
                    )

                # Check for specific implementation patterns
                impl_patterns = [
                    (r"\bclass\s+\w+", "class definitions"),
                    (r"\bdef\s+\w+\s*\(", "function definitions"),
                    (r"\bimport\s+\w+", "import statements"),
                    (r"\bCREATE\s+TABLE", "SQL DDL statements"),
                    (r"\bSELECT\s+.*\s+FROM", "SQL queries"),
                    (r"npm\s+install", "package installation commands"),
                    (r"pip\s+install", "package installation commands"),
                ]

                for pattern, description in impl_patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        # Check if it's in a code block (which we already warned about)
                        if not any(
                            re.search(pattern, block, re.IGNORECASE)
                            for block in code_blocks
                        ):
                            relative_path = os.path.relpath(
                                file_path, self.project_root
                            )
                            self.add_warning(
                                "Design Documentation",
                                f"{relative_path} contains {description}",
                                "Design docs should focus on WHAT and WHY, not HOW",
                            )
                            break  # Only warn once per file

            except Exception as e:
                self.add_warning(
                    "Design Documentation", f"Could not analyze {file_path}", str(e)
                )

    def check_technical_debt(self) -> None:
        """Check for technical debt indicators"""
        if self.is_empty_repo:
            self.add_skip("Technical Debt", "Empty repository - no code to check")
            return

        debt_indicators, files_checked = self._scan_for_debt_indicators()
        self._report_debt_results(debt_indicators, files_checked)

    def _scan_for_debt_indicators(self) -> Tuple[List[str], int]:
        """Scan all code files for technical debt indicators"""
        debt_indicators = []
        files_checked = 0

        code_patterns = [
            "**/*.py",
            "**/*.js",
            "**/*.ts",
            "**/*.jsx",
            "**/*.tsx",
            "**/*.go",
            "**/*.rs",
            "**/*.java",
            "**/*.rb",
            "**/*.cpp",
        ]

        for pattern in code_patterns:
            for file_path in Path(self.project_root).glob(pattern):
                if self._should_skip_file(file_path):
                    continue

                files_checked += 1
                indicators = self._check_file_for_debt(file_path)
                debt_indicators.extend(indicators)

        return debt_indicators, files_checked

    def _should_skip_file(self, file_path: Path) -> bool:
        """Check if file should be skipped during debt analysis"""
        skip_patterns = ["node_modules", ".git", "__pycache__", "venv"]
        return any(skip in str(file_path) for skip in skip_patterns)

    def _check_file_for_debt(self, file_path: Path) -> List[str]:
        """Check a single file for technical debt indicators"""
        indicators = []

        try:
            content = file_path.read_text(encoding="utf-8")

            # Check for TODO/FIXME comments (excluding strings and regular words)
            # Only match when preceded by comment markers and not in strings
            todo_pattern = r"(?:#|//|/\*)\s*(TODO|FIXME|HACK|XXX|BUG):"
            todos = len(re.findall(todo_pattern, content, re.IGNORECASE))
            if todos > 0:
                indicators.append(f"{file_path.name}: {todos} TODO/FIXME comments")

            # Check for commented-out code
            commented_lines = self._count_commented_code(content, file_path.suffix)
            if commented_lines > 0:
                indicators.append(
                    f"{file_path.name}: {commented_lines} lines of commented code"
                )

            # Check for any types (TypeScript)
            if file_path.suffix in [".ts", ".tsx"]:
                any_types = len(re.findall(r":\s*any\b", content))
                if any_types > 0:
                    indicators.append(f"{file_path.name}: {any_types} 'any' types")

            # Check for error suppressions
            suppressions = self._count_error_suppressions(content)
            if suppressions > 0:
                indicators.append(
                    f"{file_path.name}: {suppressions} error suppressions"
                )

        except Exception:
            pass  # Skip files we can't read

        return indicators

    def _count_commented_code(self, content: str, suffix: str) -> int:
        """Count lines of commented-out code"""
        comment_patterns = {
            ".py": r"^\s*#\s*(import|def|class|if|for|while|return)",
            ".js": r"^\s*//\s*(import|function|class|if|for|while|return)",
            ".ts": r"^\s*//\s*(import|function|class|if|for|while|return)",
            ".go": r"^\s*//\s*(import|func|type|if|for|return)",
        }

        if suffix in comment_patterns:
            return len(re.findall(comment_patterns[suffix], content, re.MULTILINE))
        return 0

    def _count_error_suppressions(self, content: str) -> int:
        """Count error suppression patterns"""
        ignore_patterns = [
            r"@ts-ignore",
            r"@ts-nocheck",
            r"# type: ignore",
            r"# noqa",
            r"# pylint: disable",
            r"// eslint-disable",
        ]

        for pattern in ignore_patterns:
            suppressions = len(re.findall(pattern, content))
            if suppressions > 0:
                return suppressions
        return 0

    def _report_debt_results(
        self, debt_indicators: List[str], files_checked: int
    ) -> None:
        """Report technical debt scan results"""
        if debt_indicators:
            # Apply Framework Compliance Policy thresholds for framework repo
            if self.is_framework_repo:
                # Count error suppressions separately as they have a specific threshold
                suppression_count = sum(
                    1 for ind in debt_indicators if "error suppressions" in ind
                )
                todo_count = sum(
                    1 for ind in debt_indicators if "TODO" in ind or "FIXME" in ind
                )

                # Framework allows up to 13 error suppressions
                if suppression_count <= 13 and todo_count == 0:
                    self.add_warning(
                        "Technical Debt",
                        f"Found {len(debt_indicators)} debt indicators (within framework limits)",
                        "Monitor debt levels per Framework Compliance Policy",
                    )
                    # Show examples
                    for indicator in debt_indicators[:3]:
                        print(f"   - {indicator}")
                    if len(debt_indicators) > 3:
                        print(f"   ... and {len(debt_indicators) - 3} more")
                else:
                    # Exceeds framework limits
                    self.add_error(
                        "Technical Debt",
                        f"Found {len(debt_indicators)} debt indicators (exceeds framework limits)",
                        f"Framework allows max 13 suppressions (found {suppression_count}), zero TODOs (found {todo_count})",
                    )
            else:
                # Application code - zero tolerance
                self.add_error(
                    "Technical Debt",
                    f"Found {len(debt_indicators)} debt indicators",
                    "Remove all TODOs, commented code, and type suppressions",
                )
                # Show first 5 examples
                for indicator in debt_indicators[:5]:
                    print(f"   - {indicator}")
                if len(debt_indicators) > 5:
                    print(f"   ... and {len(debt_indicators) - 5} more")
        elif files_checked > 0:
            self.add_success(
                "Technical Debt", f"No debt indicators in {files_checked} files"
            )
        else:
            self.add_skip("Technical Debt", "No code files to check")

    def check_type_safety(self) -> None:
        """Check for type safety issues"""
        if self.is_empty_repo:
            self.add_skip("Type Safety", "Empty repository - no code to check")
            return

        type_issues = []

        # Check TypeScript configuration
        ts_issues = self._check_typescript_config()
        type_issues.extend(ts_issues)

        # Check Python configuration
        py_issues = self._check_python_type_config()
        type_issues.extend(py_issues)

        # Check Python code annotations
        annotation_issues = self._check_python_annotations()
        type_issues.extend(annotation_issues)

        self._report_type_safety_results(type_issues)

    def _check_typescript_config(self) -> List[str]:
        """Check TypeScript configuration for type safety"""
        issues: List[str] = []
        ts_config = self.project_root / "tsconfig.json"

        if not ts_config.exists():
            return issues

        try:
            config_content = ts_config.read_text()
            config_json = json.loads(config_content)
            compiler_options = config_json.get("compilerOptions", {})

            # Check strict mode
            if not compiler_options.get("strict", False):
                issues.append("TypeScript strict mode is disabled")

            # Check for weak type settings
            weak_settings = {
                "noImplicitAny": False,
                "strictNullChecks": False,
                "strictFunctionTypes": False,
                "strictBindCallApply": False,
                "strictPropertyInitialization": False,
                "noImplicitThis": False,
                "alwaysStrict": False,
            }

            for setting, expected in weak_settings.items():
                if compiler_options.get(setting, True) == expected:
                    issues.append(f"TypeScript {setting} is not enabled")

        except Exception:
            issues.append("Could not parse tsconfig.json")

        return issues

    def _check_python_type_config(self) -> List[str]:
        """Check Python mypy configuration"""
        issues: List[str] = []
        config_files = [
            self.project_root / "mypy.ini",
            self.project_root / "setup.cfg",
            self.project_root / "pyproject.toml",
        ]

        if not any(f.exists() for f in config_files):
            return issues

        mypy_config_found = False

        # Check mypy.ini
        if config_files[0].exists():
            content = config_files[0].read_text()

            # For framework repos, check that main [mypy] section has strict=True
            # Allow relaxed rules in specific sections
            if self.is_framework_repo:
                # Parse INI to check main section
                config = configparser.ConfigParser()
                try:
                    config.read_string(content)

                    # Check main mypy section
                    if 'mypy' in config:
                        mypy_section = config['mypy']
                        # Check for strict=True
                        if mypy_section.get('strict', '').lower() == 'true':
                            mypy_config_found = True
                        # Or check individual strict settings in main section
                        elif (mypy_section.get('disallow_untyped_defs', '').lower() == 'true' or
                              mypy_section.get('check_untyped_defs', '').lower() == 'true'):
                            mypy_config_found = True
                        else:
                            issues.append(
                                "mypy main section not configured for strict type checking "
                                "(Framework allows relaxed rules in tool-specific sections)"
                            )
                    else:
                        issues.append("mypy configuration missing [mypy] section")
                except configparser.Error:
                    # Fall back to simple check if parsing fails
                    if "strict = True" in content or "strict=True" in content:
                        mypy_config_found = True
                    else:
                        issues.append("mypy configuration cannot be parsed")
            else:
                # For application code, enforce strict type checking throughout
                if "disallow_untyped_defs" not in content or "False" in content:
                    issues.append("mypy not configured for strict type checking")
                else:
                    mypy_config_found = True

        # Check setup.cfg
        if not mypy_config_found and config_files[1].exists():
            content = config_files[1].read_text()
            if "[mypy]" not in content:
                issues.append("mypy configuration missing")

        return issues

    def _check_python_annotations(self) -> List[str]:
        """Check Python code for type annotations"""
        issues: List[str] = []
        py_files = list(Path(self.project_root).glob("**/*.py"))
        py_files = [
            f for f in py_files if "venv" not in str(f) and "__pycache__" not in str(f)
        ]

        if not py_files:
            return issues

        missing_annotations = 0
        for py_file in py_files[:10]:  # Sample first 10 files
            try:
                content = py_file.read_text()
                functions = re.findall(r"def\s+\w+\s*\([^)]*\)\s*:", content)
                typed_functions = re.findall(
                    r"def\s+\w+\s*\([^)]*\)\s*->\s*\w+\s*:", content
                )

                if functions and len(typed_functions) < len(functions) * 0.8:
                    missing_annotations += 1
            except Exception:
                continue

        if missing_annotations > len(py_files) * 0.2:
            issues.append(f"{missing_annotations} Python files lack type annotations")

        return issues

    def _report_type_safety_results(self, type_issues: List[str]) -> None:
        """Report type safety check results"""
        if type_issues:
            self.add_error(
                "Type Safety",
                f"Found {len(type_issues)} type safety issues",
                "Enable strict type checking in all languages",
            )
            for issue in type_issues:
                print(f"   - {issue}")
        else:
            self.add_success("Type Safety", "Strong typing enforced")

    def check_architecture_documentation(self) -> None:
        """Check if architecture documents exist and are complete"""
        arch_dir = self.project_root / "docs" / "architecture"

        if not arch_dir.exists():
            self.add_error(
                "Architecture Documentation",
                "Architecture directory missing",
                "Run: python tools/validation/validate-architecture.py for details",
            )
            return

        # Run architecture validator
        try:
            result = subprocess.run(
                ["python", "tools/validation/validate-architecture.py"],
                capture_output=True,
                text=True,
                cwd=self.project_root,
            )

            if result.returncode != 0:
                self.add_error(
                    "Architecture Documentation",
                    "Architecture validation failed",
                    "Complete all architecture documents before coding",
                )
            else:
                self.add_success(
                    "Architecture Documentation", "All architecture documents complete"
                )

        except FileNotFoundError:
            self.add_warning(
                "Architecture Documentation",
                "Architecture validator not found",
                "Ensure validate-architecture.py exists",
            )

    def check_logging_compliance(self) -> None:
        """Check if code has proper logging at mandatory points"""
        if self.is_empty_repo:
            self.add_skip("Logging Compliance", "Empty repository - no code to check")
            return

        # Framework tools have different logging requirements
        if self.is_framework_repo:
            self.add_skip(
                "Logging Compliance",
                "Framework tools exempt from application logging requirements",
            )
            return

        # Check if logging validator exists
        validator_path = (
            self.project_root / "tools" / "validation" / "check-logging-compliance.py"
        )
        if not validator_path.exists():
            self.add_warning(
                "Logging Compliance",
                "Logging validator not found",
                "Download check-logging-compliance.py from framework",
            )
            return

        # Run logging compliance check
        try:
            result = subprocess.run(
                ["python", str(validator_path), "--threshold", "0"],
                capture_output=True,
                text=True,
                cwd=self.project_root,
            )

            if result.returncode != 0:
                # Extract violation count from output
                output_lines = result.stdout.strip().split("\n")
                violation_line = next(
                    (line for line in output_lines if "Total Violations:" in line), None
                )

                if violation_line:
                    self.add_error(
                        "Logging Compliance",
                        f"Missing mandatory logging - {violation_line}",
                        "Add logging at all 10 mandatory points",
                    )
                else:
                    self.add_error(
                        "Logging Compliance",
                        "Logging compliance check failed",
                        "Run: python tools/validation/check-logging-compliance.py",
                    )
            else:
                self.add_success(
                    "Logging Compliance", "All mandatory logging points covered"
                )

        except Exception as e:
            self.add_error(
                "Logging Compliance",
                f"Failed to run logging check: {e}",
                "Ensure Python dependencies are installed",
            )

    def _get_current_branch(self) -> Optional[str]:
        """Get current git branch"""
        # Check if we're in GitHub Actions CI environment
        if os.environ.get("GITHUB_ACTIONS") == "true":
            # In GitHub Actions, get branch from environment variables
            if os.environ.get("GITHUB_EVENT_NAME") == "pull_request":
                # For PRs, use the head ref
                return os.environ.get("GITHUB_HEAD_REF", "")
            else:
                # For pushes, extract from GITHUB_REF
                ref = os.environ.get("GITHUB_REF", "")
                if ref.startswith("refs/heads/"):
                    return ref.replace("refs/heads/", "")
            return None
        else:
            # Local environment - use git command
            try:
                result = subprocess.run(
                    ["git", "symbolic-ref", "--short", "HEAD"],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                return result.stdout.strip()
            except subprocess.CalledProcessError:
                return None

    def _detect_empty_repository(self) -> None:
        """Detect if this is an empty repository with only framework files"""
        import glob

        # Code file patterns
        code_patterns = [
            "*.py",
            "*.js",
            "*.ts",
            "*.jsx",
            "*.tsx",
            "*.go",
            "*.rs",
            "*.java",
            "*.cs",
            "*.cpp",
            "*.c",
            "*.h",
            "*.rb",
            "*.php",
            "*.swift",
        ]

        # Count code files (excluding framework tools)
        code_file_count = 0
        for pattern in code_patterns:
            files = glob.glob(f"**/{pattern}", recursive=True)
            # Exclude framework tools directory
            code_files = [
                f for f in files if not f.startswith(("tools/", ".ai-sdlc-temp/"))
            ]
            code_file_count += len(code_files)

        # Check if we only have framework files
        framework_files = ["CLAUDE.md", "README.md", ".gitignore"]
        has_framework = all(
            (self.project_root / f).exists() for f in framework_files[:2]
        )  # At least CLAUDE.md and README

        self.is_empty_repo = code_file_count == 0 and has_framework

    def add_success(self, check: str, message: str) -> None:
        """Add success result"""
        self.results.append({"icon": "✅", "check": check, "message": message, "fix": None})

    def add_error(self, check: str, message: str, fix: str) -> None:
        """Add error result"""
        self.has_errors = True
        self.results.append({"icon": "❌", "check": check, "message": message, "fix": fix})

    def add_warning(self, check: str, message: str, fix: str) -> None:
        """Add warning result"""
        self.has_warnings = True
        self.results.append({"icon": "⚠️ ", "check": check, "message": message, "fix": fix})

    def add_skip(self, check: str, reason: str) -> None:
        """Add skipped check"""
        self.results.append({"icon": "⏭️ ", "check": check, "message": reason, "fix": None})

    def print_summary(self) -> None:
        """Print validation summary"""
        print("\n" + "=" * 50)
        print("📊 Validation Summary")
        print("=" * 50)

        for result in self.results:
            print(f"{result['icon']} {result['check']}: {result['message']}")
            if result.get('fix'):
                print(f"   └─ Fix: {result['fix']}")

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
                        "fix": fix,
                    }
                    for icon, check, message, fix in self.results
                ],
            }
            return json.dumps(data, indent=2)

        elif format == "markdown":
            md = "# Validation Report\n\n"
            md += f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

            md += "## Results\n\n"
            for icon, check, message, fix in self.results:
                md += f"- {icon} **{check}**: {message}\n"
                if fix:
                    md += f"  - Fix: {fix}\n"

            md += "\n## Summary\n"
            if self.has_errors:
                md += "❌ **FAILED** - Errors must be fixed\n"
            elif self.has_warnings:
                md += "⚠️  **PASSED** with warnings\n"
            else:
                md += "✅ **PASSED** - Fully compliant\n"

            return md

        else:
            raise ValueError(f"Unsupported format: {format}")


def main() -> None:
    parser = argparse.ArgumentParser(description="AI-First SDLC Validation Pipeline")
    parser.add_argument(
        "--checks",
        nargs="+",
        choices=[
            "branch",
            "proposal",
            "plan",
            "ai-docs",
            "tests",
            "security",
            "code-quality",
            "dependencies",
            "commit-history",
            "retrospective",
            "design-docs",
            "technical-debt",
            "type-safety",
            "architecture",
            "logging",
        ],
        help="Specific checks to run (default: all)",
    )
    parser.add_argument(
        "--export", choices=["json", "markdown"], help="Export results to format"
    )
    parser.add_argument("--output", help="Output file for export (default: stdout)")
    parser.add_argument(
        "--ci", action="store_true", help="CI mode - exit with error code on failures"
    )

    args = parser.parse_args()

    # Run validation
    pipeline = ValidationPipeline()
    success = pipeline.run_validation(args.checks)

    # Export if requested
    if args.export:
        output = pipeline.export_results(args.export)

        if args.output:
            with open(args.output, "w") as f:
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
