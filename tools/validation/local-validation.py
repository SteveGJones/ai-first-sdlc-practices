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
import hashlib
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import argparse
import time


#: Directory names never worth walking: gitignored scratch (`tmp/` — the
#: location CLAUDE.md mandates for scratch work), vendored dependencies, and
#: build caches. Files under these cannot be pushed, so failing a pre-push
#: gate on them blocks a legitimate push for no benefit.
_SKIP_DIRS = frozenset({"tmp", "node_modules", "__pycache__", "venv", "build", "dist"})

#: Paths whose git index entries must be byte-for-byte stable across a
#: ``--pre-push`` run (verbatim assessment evidence).
_PROTECTED_PATHS = ("research/poker-capstone",)

#: Seconds allowed for the pre-commit gate; the first run in a fresh
#: worktree may have to install every hook environment.
_PRE_COMMIT_TIMEOUT = 1800


class ValidationRunner:
    """Runs comprehensive local validation checks"""

    def __init__(self, verbose: bool = False, repo_root: Optional[Path] = None):
        self.verbose = verbose
        self.repo_root = repo_root if repo_root is not None else Path.cwd()
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
        self,
        cmd: List[str],
        description: str = "",
        cwd: Optional[Path] = None,
        timeout: int = 300,
    ) -> Tuple[int, str, str]:
        """Run shell command and capture output (default 5 minute timeout)"""
        self.log(f"Running: {' '.join(cmd)}")
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=timeout, cwd=cwd
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
            # Skip hidden dirs, test dirs, and scratch/vendored dirs that are
            # gitignored and so can never be pushed. `tmp/` matters especially:
            # CLAUDE.md directs all scratch work there and .gitignore excludes
            # it, so scanning it blocks a push on files that are not part of
            # the repo — e.g. deliberately-captured malformed model output.
            dirs[:] = [
                d
                for d in dirs
                if not d.startswith(".") and "test-" not in d and d not in _SKIP_DIRS
            ]
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
        """Run pre-commit hooks without mutating the working checkout.

        Hooks such as black or pretty-format-json rewrite files in place, which
        previously rewrote tracked files (including byte-identical evidence)
        during ``--pre-push``. The hooks therefore run in a throwaway detached
        worktree of HEAD and the worktree is always removed afterwards.

        This validates the COMMITTED state (HEAD), not uncommitted edits:
        commit first, then run the gate. Any non-zero exit or diff output is
        a failure and the hook output is included in the report.
        """
        self.log(
            "🪝 Running pre-commit hooks (HEAD, in a throwaway worktree)...", "INFO"
        )

        worktree = self.repo_root / "tmp" / f"prepush-gate-{os.getpid()}"
        added, _, add_err = self.run_command(
            ["git", "worktree", "add", "--detach", str(worktree), "HEAD"],
            cwd=self.repo_root,
        )
        if added != 0:
            self.errors.append(
                f"Pre-commit hooks failed: cannot create worktree: {add_err}"
            )
            return False

        try:
            returncode, stdout, stderr = self.run_command(
                ["pre-commit", "run", "--all-files", "--show-diff-on-failure"],
                cwd=worktree,
                timeout=_PRE_COMMIT_TIMEOUT,
            )
        finally:
            self.run_command(
                ["git", "worktree", "remove", "--force", str(worktree)],
                cwd=self.repo_root,
            )
            self.run_command(["git", "worktree", "prune"], cwd=self.repo_root)

        output = "\n".join(part for part in (stdout, stderr) if part)
        if returncode != 0 or "diff --git" in output:
            self.errors.append(f"Pre-commit hooks failed:\n{output}")
            self.log("Pre-commit hooks failed", "ERROR")
            if output:
                self.log(output, "ERROR")
            return False

        self.log("Pre-commit hooks passed", "SUCCESS")
        return True

    def _git_output(self, args: List[str]) -> str:
        result = subprocess.run(
            ["git", *args], cwd=self.repo_root, capture_output=True, text=True
        )
        return result.stdout

    def _tree_snapshot(self) -> Dict[str, str]:
        """Capture the git state a validation run must not change."""
        snapshot = {
            "status": self._git_output(["status", "--porcelain"]),
            "diff": hashlib.sha256(
                self._git_output(["diff"]).encode("utf-8")
            ).hexdigest(),
        }
        for path in _PROTECTED_PATHS:
            snapshot[f"index:{path}"] = hashlib.sha256(
                self._git_output(["ls-files", "-s", "--", path]).encode("utf-8")
            ).hexdigest()
        return snapshot

    def _tripwire_report(
        self, before: Dict[str, str], after: Dict[str, str]
    ) -> List[str]:
        """Describe how the tree changed between two snapshots (empty if none)."""
        problems: List[str] = []
        if before["status"] != after["status"]:
            old = set(before["status"].splitlines())
            new = set(after["status"].splitlines())
            changed = sorted(old.symmetric_difference(new))
            problems.append("git status changed: " + "; ".join(changed))
        if before["diff"] != after["diff"]:
            changed_files = self._git_output(["diff", "--name-only"]).split()
            problems.append(
                "tracked file contents changed: " + ", ".join(changed_files)
            )
        for key, value in before.items():
            if key.startswith("index:") and after.get(key) != value:
                problems.append(f"{key[6:]} index entries changed")
        return problems

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

    def check_logging_compliance(self) -> bool:
        """Check logging compliance using framework tools"""
        self.log("📝 Checking logging compliance...", "INFO")

        returncode, stdout, stderr = self.run_command(
            [
                "python",
                "tools/validation/check-logging-compliance.py",
                ".",
                "--threshold",
                "0",
            ]
        )

        if returncode != 0:
            self.errors.append("Logging compliance check failed")
            self.log("Logging compliance violations found", "ERROR")
            if stderr:
                self.log(stderr, "ERROR")
            return False
        else:
            self.log("Logging compliance check passed", "SUCCESS")
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
            ("Logging Compliance", self.check_logging_compliance),
            ("Static Analysis", self.check_static_analysis),
        ]

        before = self._tree_snapshot()
        all_passed = True
        for name, check_func in checks:
            self.log(f"Running {name}...", "INFO")
            if not check_func():
                all_passed = False

        problems = self._tripwire_report(before, self._tree_snapshot())
        if problems:
            all_passed = False
            self.errors.append(
                "TRIPWIRE: the pre-push run modified the working tree: "
                + " | ".join(problems)
            )
            self.log(self.errors[-1], "ERROR")

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

    validator = ValidationRunner(verbose=args.verbose, repo_root=repo_root)

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
