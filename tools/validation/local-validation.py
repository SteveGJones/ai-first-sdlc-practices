#!/usr/bin/env python3
"""
Local Validation Script - Pre-Push Validation for AI-First SDLC

This script mirrors CI/CD checks locally to prevent push-fail-fix cycles.
Run this before every commit to ensure code quality.

Usage:
    python tools/validation/local-validation.py           # Full validation
    python tools/validation/local-validation.py --syntax  # Syntax only
    python tools/validation/local-validation.py --quick   # Fast checks only
    python tools/validation/local-validation.py --pre-push # Pre-push validation
"""

import ast
import os
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple
import argparse
import time


class ValidationRunner:
    """Runs comprehensive local validation checks"""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.start_time = time.time()

    def log(self, message: str, level: str = "INFO") -> None:
        """Log messages with timestamps"""
        if self.verbose or level in ["ERROR", "WARNING"]:
            timestamp = time.strftime("%H:%M:%S")
            prefix = {"INFO": "ℹ️", "WARNING": "⚠️", "ERROR": "❌", "SUCCESS": "✅"}
            print(f"[{timestamp}] {prefix.get(level, '')} {message}")

    def run_command(
        self, cmd: List[str], description: str = ""
    ) -> Tuple[int, str, str]:
        """Run shell command and capture output"""
        self.log(f"Running: {' '.join(cmd)}")
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=300  # 5 minute timeout
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            error_msg = f"Command timed out: {' '.join(cmd)}"
            self.errors.append(error_msg)
            return 1, "", error_msg
        except Exception as e:
            error_msg = f"Command failed: {' '.join(cmd)} - {str(e)}"
            self.errors.append(error_msg)
            return 1, "", error_msg

    def check_python_syntax(self) -> bool:
        """Check Python syntax using AST parsing"""
        self.log("🐍 Checking Python syntax...", "INFO")

        python_files = []
        for root, dirs, files in os.walk("."):
            # Skip hidden dirs and test dirs
            dirs[:] = [d for d in dirs if not d.startswith(".") and "test-" not in d]
            for file in files:
                if file.endswith(".py"):
                    python_files.append(os.path.join(root, file))

        syntax_errors = []
        for file_path in python_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    source = f.read()
                ast.parse(source, filename=file_path)
                self.log(f"✓ {file_path}")
            except SyntaxError as e:
                error_msg = (
                    f"SYNTAX ERROR in {file_path}:{e.lineno}:{e.offset}: {e.msg}"
                )
                syntax_errors.append(error_msg)
                self.log(error_msg, "ERROR")
            except Exception as e:
                error_msg = f"FILE ERROR in {file_path}: {str(e)}"
                syntax_errors.append(error_msg)
                self.log(error_msg, "ERROR")

        if syntax_errors:
            self.errors.extend(syntax_errors)
            self.log(f"Found {len(syntax_errors)} syntax errors", "ERROR")
            return False
        else:
            self.log(
                f"All {len(python_files)} Python files have valid syntax", "SUCCESS"
            )
            return True

    def check_pre_commit_hooks(self) -> bool:
        """Run pre-commit hooks"""
        self.log("🪝 Running pre-commit hooks...", "INFO")

        returncode, stdout, stderr = self.run_command(
            ["pre-commit", "run", "--all-files"]
        )

        if returncode != 0:
            self.errors.append("Pre-commit hooks failed")
            self.log("Pre-commit hooks failed", "ERROR")
            if stderr:
                self.log(stderr, "ERROR")
            return False
        else:
            self.log("Pre-commit hooks passed", "SUCCESS")
            return True

    def check_technical_debt(self) -> bool:
        """Check technical debt using framework tools"""
        self.log("🔍 Checking technical debt...", "INFO")

        # Use the pipeline's technical debt check which properly applies
        # framework policy
        returncode, stdout, stderr = self.run_command(
            [
                "python",
                "tools/validation/validate-pipeline.py",
                "--checks",
                "technical-debt",
            ]
        )

        if returncode != 0:
            self.errors.append("Technical debt check failed")
            self.log("Technical debt violations found", "ERROR")
            if stderr:
                self.log(stderr, "ERROR")
            return False
        else:
            self.log("Technical debt check passed", "SUCCESS")
            return True

    def check_architecture_compliance(self) -> bool:
        """Check architecture documentation compliance"""
        self.log("🏗️ Checking architecture compliance...", "INFO")

        returncode, stdout, stderr = self.run_command(
            ["python", "tools/validation/validate-architecture.py"]
        )

        if returncode not in [0, 2]:  # 0=success, 2=bootstrap mode ok
            self.errors.append("Architecture validation failed")
            self.log("Architecture validation failed", "ERROR")
            if stderr:
                self.log(stderr, "ERROR")
            return False
        else:
            self.log("Architecture validation passed", "SUCCESS")
            return True

    def check_type_safety(self) -> bool:
        """Check type safety with mypy"""
        self.log("🔒 Checking type safety...", "INFO")

        returncode, stdout, stderr = self.run_command(
            [
                "python",
                "tools/validation/validate-pipeline.py",
                "--checks",
                "type-safety",
            ]
        )

        if returncode != 0:
            self.warnings.append("Type safety issues found")
            self.log("Type safety issues found", "WARNING")
            return True  # Don't fail build on warnings
        else:
            self.log("Type safety check passed", "SUCCESS")
            return True

    def check_security(self) -> bool:
        """Run security checks"""
        self.log("🛡️ Running security checks...", "INFO")

        returncode, stdout, stderr = self.run_command(
            ["python", "tools/validation/validate-pipeline.py", "--checks", "security"]
        )

        if returncode != 0:
            self.errors.append("Security vulnerabilities found")
            self.log("Security vulnerabilities found", "ERROR")
            return False
        else:
            self.log("Security checks passed", "SUCCESS")
            return True

    def check_static_analysis(self) -> bool:
        """Run CodeQL-style static analysis checks"""
        self.log("🔍 Running static analysis checks...", "INFO")

        # Check for argument count mismatches and other static analysis issues
        python_files = list(Path("tools").rglob("*.py"))
        issues_found = []

        for file_path in python_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                # Parse the AST to check for potential issues
                tree = ast.parse(content)

                # Look for potential argument count issues
                for node in ast.walk(tree):
                    if isinstance(node, ast.Call):
                        # This is a simplified check - in practice would need
                        # more sophisticated analysis
                        if hasattr(node.func, "attr"):
                            func_name = node.func.attr
                            if (
                                func_name in ["save_context", "setup"]
                                and len(node.args) == 1
                            ):
                                issues_found.append(
                                    f"{file_path}:{node.lineno}: Potential argument count issue in {func_name} call"
                                )

                    elif isinstance(node, ast.ClassDef):
                        # Check for class instantiation issues
                        for child in ast.walk(node):
                            if isinstance(child, ast.Call) and hasattr(
                                child.func, "id"
                            ):
                                class_name = child.func.id
                                if (
                                    class_name.endswith("Configurator")
                                    and len(child.args) > 4
                                ):
                                    msg = (
                                        f"{file_path}:{child.lineno}: "
                                        f"Potential argument order issue in {class_name} instantiation"
                                    )
                                    issues_found.append(msg)

            except (SyntaxError, UnicodeDecodeError) as e:
                issues_found.append(f"{file_path}: Parse error: {e}")

        if issues_found:
            self.warnings.extend(issues_found[:5])  # Limit output
            self.log(
                f"Static analysis found {len(issues_found)} potential issues", "WARNING"
            )
            for issue in issues_found[:3]:  # Show first 3 issues
                self.log(issue, "WARNING")
            return True  # Don't fail build on warnings, just report
        else:
            self.log("Static analysis checks passed", "SUCCESS")
            return True

    def run_quick_validation(self) -> bool:
        """Run only the fastest, most critical checks"""
        self.log("🚀 Running quick validation...", "INFO")

        checks = [
            ("Syntax Check", self.check_python_syntax),
        ]

        all_passed = True
        for name, check_func in checks:
            if not check_func():
                all_passed = False

        return all_passed

    def run_pre_push_validation(self) -> bool:
        """Run comprehensive pre-push validation"""
        self.log("📤 Running pre-push validation...", "INFO")

        checks = [
            ("Syntax Check", self.check_python_syntax),
            ("Pre-commit Hooks", self.check_pre_commit_hooks),
            ("Technical Debt", self.check_technical_debt),
            ("Architecture", self.check_architecture_compliance),
            ("Type Safety", self.check_type_safety),
            ("Security", self.check_security),
            ("Static Analysis", self.check_static_analysis),
        ]

        all_passed = True
        for name, check_func in checks:
            self.log(f"Running {name}...", "INFO")
            if not check_func():
                all_passed = False

        return all_passed

    def run_full_validation(self) -> bool:
        """Run all validation checks"""
        self.log("🔍 Running full validation...", "INFO")
        return self.run_pre_push_validation()

    def print_summary(self, success: bool) -> None:
        """Print validation summary"""
        duration = time.time() - self.start_time

        print(f"\n{'='*60}")
        print(f"{'🎯 VALIDATION SUMMARY':^60}")
        print(f"{'='*60}")

        if success:
            print(f"✅ {'VALIDATION PASSED':^58} ✅")
        else:
            print(f"❌ {'VALIDATION FAILED':^58} ❌")

        print(f"\nDuration: {duration:.1f} seconds")
        print(f"Errors: {len(self.errors)}")
        print(f"Warnings: {len(self.warnings)}")

        if self.errors:
            print(f"\n❌ ERRORS ({len(self.errors)}):")
            for i, error in enumerate(self.errors, 1):
                print(f"   {i}. {error}")

        if self.warnings:
            print(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
            for i, warning in enumerate(self.warnings, 1):
                print(f"   {i}. {warning}")

        if success:
            print("\n🚀 Ready to push! All validation checks passed.")
        else:
            print("\n🛑 DO NOT PUSH! Fix errors before committing.")
            print("💡 Tip: Run with --syntax first to fix basic issues quickly.")

        print(f"{'='*60}")


def main():
    parser = argparse.ArgumentParser(
        description="Local validation for AI-First SDLC projects",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python tools/validation/local-validation.py           # Full validation
  python tools/validation/local-validation.py --syntax  # Syntax only
  python tools/validation/local-validation.py --quick   # Fast checks
  python tools/validation/local-validation.py --pre-push # Pre-push validation
        """,
    )

    parser.add_argument(
        "--syntax", action="store_true", help="Check Python syntax only"
    )
    parser.add_argument(
        "--quick", action="store_true", help="Run quick validation only"
    )
    parser.add_argument(
        "--pre-push", action="store_true", help="Run pre-push validation"
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    # Change to repository root
    repo_root = Path(__file__).parent.parent.parent
    os.chdir(repo_root)

    validator = ValidationRunner(verbose=args.verbose)

    try:
        if args.syntax:
            success = validator.check_python_syntax()
        elif args.quick:
            success = validator.run_quick_validation()
        elif args.pre_push:
            success = validator.run_pre_push_validation()
        else:
            success = validator.run_full_validation()

        validator.print_summary(success)
        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\n\n⚠️ Validation interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Validation script error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
