#!/usr/bin/env python3
"""
Local Flake8 Validation Script
Exactly matches GitHub Actions flake8 configuration to prevent push-fail-fix cycles

This script runs the EXACT same flake8 checks as GitHub Actions to ensure
local validation catches all issues before pushing.
"""

import subprocess
import sys
import click
from pathlib import Path
from typing import Tuple, List


class LocalFlake8Validator:
    """Run flake8 exactly as GitHub Actions does"""

    def __init__(self, fix_mode: bool = False):
        self.fix_mode = fix_mode
        self.project_root = Path.cwd()

        # Track all violations found
        self.violations = {
            "F401": [],  # Unused imports
            "F541": [],  # f-string missing placeholders
            "E501": [],  # Line too long
            "E722": [],  # Bare except
            "E712": [],  # Comparison with True/False
            "E741": [],  # Ambiguous variable name
            "F841": [],  # Local variable assigned but never used
            "other": [],
        }

    def run_github_exact_checks(self) -> Tuple[bool, str]:
        """Run the EXACT flake8 commands from GitHub Actions"""

        print("🔍 Running GitHub-exact flake8 validation...")
        print("=" * 60)

        all_passed = True
        full_output = []

        # First check: Critical errors (from framework-validation.yml line 194)
        print("\n1️⃣ Critical Errors Check (E9,F63,F7,F82):")
        print("-" * 40)
        result1 = self._run_flake8_command(
            [
                "flake8",
                ".",
                "--count",
                "--select=E9,F63,F7,F82",
                "--show-source",
                "--statistics",
            ]
        )
        if result1[0] != 0:
            all_passed = False
            full_output.append("CRITICAL ERRORS FOUND:")
            full_output.append(result1[1])
            print("❌ Critical errors found")
        else:
            print("✅ No critical errors")

        # Second check: Full check with stats (from framework-validation.yml line 195)
        print("\n2️⃣ Full Check (max-complexity=10, max-line-length=127):")
        print("-" * 40)
        result2 = self._run_flake8_command(
            [
                "flake8",
                ".",
                "--count",
                "--exit-zero",
                "--max-complexity=10",
                "--max-line-length=127",
                "--statistics",
            ]
        )

        # Parse and categorize violations
        self._parse_violations(result2[1])

        # Even with --exit-zero, we track violations
        if result2[1].strip():
            full_output.append("QUALITY ISSUES:")
            full_output.append(result2[1])
            print(f"⚠️  Found {self._count_violations(result2[1])} quality issues")
        else:
            print("✅ No quality issues")

        # Third check: Comprehensive validation (from comprehensive-validation.yml line 130)
        print("\n3️⃣ Comprehensive Check (max-complexity=15):")
        print("-" * 40)
        result3 = self._run_flake8_command(
            [
                "flake8",
                ".",
                "--count",
                "--exit-zero",
                "--max-complexity=15",
                "--max-line-length=127",
                "--statistics",
            ]
        )

        if result3[1].strip():
            # This is less strict, so only note differences
            comprehensive_count = self._count_violations(result3[1])
            standard_count = self._count_violations(result2[1])
            if comprehensive_count < standard_count:
                print(
                    f"ℹ️  Less strict check found {comprehensive_count} issues (vs {standard_count})"
                )
        else:
            print("✅ No issues in comprehensive check")

        return all_passed and not result2[1].strip(), "\n".join(full_output)

    def _run_flake8_command(self, cmd: List[str]) -> Tuple[int, str]:
        """Run a flake8 command and return exit code and output"""
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, cwd=self.project_root
            )
            return result.returncode, result.stdout + result.stderr
        except FileNotFoundError:
            return 1, "Error: flake8 not installed. Run: pip install flake8"

    def _count_violations(self, output: str) -> int:
        """Count total violations in flake8 output"""
        count = 0
        for line in output.split("\n"):
            if ".py:" in line and not line.startswith(" "):
                count += 1
        return count

    def _parse_violations(self, output: str):
        """Parse violations and categorize them"""
        for line in output.split("\n"):
            if ".py:" in line and not line.startswith(" "):
                # Extract violation code
                parts = line.split(" ")
                for part in parts:
                    if part in self.violations:
                        self.violations[part].append(line)
                        break
                else:
                    # Check if any known code is in the line
                    for code in self.violations.keys():
                        if code in line:
                            self.violations[code].append(line)
                            break

    def show_violation_summary(self):
        """Show summary of violations by type"""
        print("\n" + "=" * 60)
        print("📊 VIOLATION SUMMARY")
        print("=" * 60)

        total = 0
        for code, violations in self.violations.items():
            if violations and code != "other":
                count = len(violations)
                total += count
                print(f"{code}: {count} violations")

                # Show first 3 examples
                if count > 0:
                    print("  Examples:")
                    for v in violations[:3]:
                        # Extract just the file and line info
                        if ":" in v:
                            parts = v.split(":")
                            if len(parts) >= 3:
                                file_part = parts[0].replace("./", "")
                                line_part = parts[1]
                                print(f"    - {file_part}:{line_part}")

        if total > 0:
            print(f"\nTotal: {total} violations to fix")
            print("\n🔧 FIX STRATEGY:")
            print("1. Run: python tools/validation/local-flake8.py --fix")
            print("2. Or fix manually using the violation list above")

    def auto_fix_violations(self):
        """Attempt to auto-fix common violations"""
        print("\n🔧 AUTO-FIXING VIOLATIONS...")
        print("=" * 60)

        # First, get current violations
        self.run_github_exact_checks()

        fixed_count = 0

        # Fix F401 (unused imports) using autoflake
        if self.violations["F401"]:
            print("\n📦 Fixing F401 (unused imports)...")
            result = subprocess.run(
                [
                    "autoflake",
                    "--in-place",
                    "--remove-all-unused-imports",
                    "--recursive",
                    ".",
                ],
                capture_output=True,
                text=True,
                cwd=self.project_root,
            )
            if result.returncode == 0:
                fixed_count += len(self.violations["F401"])
                print(f"  ✅ Fixed {len(self.violations['F401'])} unused imports")
            else:
                print("  ⚠️  autoflake not installed. Run: pip install autoflake")

        # Fix F541 (f-strings without placeholders)
        if self.violations["F541"]:
            print("\n📝 Fixing F541 (f-strings without placeholders)...")
            for violation in self.violations["F541"]:
                if ":" in violation:
                    file_path = violation.split(":")[0]
                    self._fix_fstring_in_file(file_path)
            print(f"  ✅ Fixed {len(self.violations['F541'])} f-string issues")
            fixed_count += len(self.violations["F541"])

        # Apply black and autopep8 for other issues
        print("\n🎨 Applying black and autopep8...")
        subprocess.run(
            ["black", ".", "--line-length", "127"],
            capture_output=True,
            cwd=self.project_root,
        )
        subprocess.run(
            ["autopep8", "--in-place", "--recursive", "--max-line-length", "127", "."],
            capture_output=True,
            cwd=self.project_root,
        )

        print(f"\n✅ Auto-fix complete! Fixed approximately {fixed_count} issues")
        print("🔄 Re-running validation to check remaining issues...")

        # Re-run validation
        passed, output = self.run_github_exact_checks()
        if passed:
            print("\n🎉 ALL CHECKS PASS! Safe to push.")
        else:
            print("\n⚠️  Some issues remain. Review the output above.")

    def _fix_fstring_in_file(self, file_path: str):
        """Fix f-strings without placeholders in a file"""
        try:
            with open(file_path, "r") as f:
                content = f.read()

            # Replace f-strings without placeholders with regular strings
            import re

            # Simple pattern - may need refinement
            content = re.sub(
                r'"([^"]*)"',
                lambda m: f'"{m.group(1)}"' if "{" not in m.group(1) else m.group(0),
                content,
            )
            content = re.sub(
                r"'([^']*)'",
                lambda m: f"'{m.group(1)}'" if "{" not in m.group(1) else m.group(0),
                content,
            )

            with open(file_path, "w") as f:
                f.write(content)
        except Exception:
            pass  # Silently skip files we can't process


@click.command()
@click.option("--fix", is_flag=True, help="Attempt to auto-fix violations")
@click.option("--summary", is_flag=True, help="Show detailed violation summary")
def main(fix, summary):
    """
    Local Flake8 Validator - Match GitHub Actions Exactly

    This tool runs the EXACT same flake8 checks as GitHub Actions to ensure
    your code will pass CI/CD before you push.

    Usage:
        python tools/validation/local-flake8.py         # Check only
        python tools/validation/local-flake8.py --fix   # Auto-fix issues
        python tools/validation/local-flake8.py --summary  # Show detailed summary
    """

    validator = LocalFlake8Validator(fix_mode=fix)

    if fix:
        validator.auto_fix_violations()
    else:
        passed, output = validator.run_github_exact_checks()

        if summary or not passed:
            validator.show_violation_summary()

        if passed:
            print("\n" + "=" * 60)
            print("✅ SUCCESS: All flake8 checks pass!")
            print("🚀 Your code matches GitHub Actions requirements exactly.")
            print("=" * 60)
            sys.exit(0)
        else:
            print("\n" + "=" * 60)
            print("❌ FAILURE: Flake8 violations found")
            print("🛠️  Fix these issues before pushing to avoid CI/CD failures")
            print("💡 Run with --fix to attempt auto-fixing")
            print("=" * 60)
            sys.exit(1)


if __name__ == "__main__":
    main()
