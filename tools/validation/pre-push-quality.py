#!/usr/bin/env python3
"""
Enhanced Pre-Push Quality Gate - Catches CodeQL Issues Before CI/CD

This script provides comprehensive local validation that matches CI/CD quality standards,
specifically designed to catch issues that CodeQL and other static analysis tools find.

Usage:
    python tools/validation/pre-push-quality.py              # Full validation
    python tools/validation/pre-push-quality.py --fix        # Auto-fix issues when possible
    python tools/validation/pre-push-quality.py --codeql     # CodeQL-style analysis only
"""

import ast
import re
import sys
import subprocess
import argparse
from pathlib import Path
from typing import List, Dict, Any
import json


class CodeQLStyleAnalyzer:
    """Performs CodeQL-style static analysis to catch common issues locally"""

    def __init__(self):
        self.issues: List[Dict[str, Any]] = []
        self.fixes_applied = 0

    def analyze_argument_count_mismatches(
        self, file_path: Path
    ) -> List[Dict[str, Any]]:
        """Detect wrong number of arguments in function calls"""
        issues = []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            tree = ast.parse(content)
            lines = content.split("\n")

            # Build function signature map
            function_signatures = {}
            class_methods = {}

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Count required arguments (excluding self, *args, **kwargs)
                    required_args = 0
                    for arg in node.args.args:
                        if arg.arg != "self":
                            required_args += 1

                    # Account for defaults
                    required_args -= len(node.args.defaults)
                    function_signatures[node.name] = required_args

                elif isinstance(node, ast.ClassDef):
                    class_name = node.name
                    for child in node.body:
                        if isinstance(child, ast.FunctionDef):
                            if child.name == "__init__":
                                # Count constructor arguments
                                required_args = len(child.args.args) - 1  # Exclude self
                                required_args -= len(child.args.defaults)
                                class_methods[class_name] = required_args

            # Check function calls
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    func_name = None
                    class_name = None

                    if hasattr(node.func, "id"):
                        func_name = node.func.id
                    elif hasattr(node.func, "attr"):
                        func_name = node.func.attr
                        if hasattr(node.func.value, "id"):
                            class_name = node.func.value.id

                    # Check against known signatures
                    expected_args = None

                    if class_name and class_name in class_methods:
                        expected_args = class_methods[class_name]
                    elif func_name in function_signatures:
                        expected_args = function_signatures[func_name]

                    # Special cases for known problematic patterns
                    if func_name == "save_context" and len(node.args) == 1:
                        issues.append(
                            {
                                "type": "argument_count_mismatch",
                                "file": str(file_path),
                                "line": node.lineno,
                                "column": node.col_offset,
                                "message": f"save_context() expects 2-3 arguments but got {len(node.args)}",
                                "severity": "error",
                                "code_snippet": lines[node.lineno - 1].strip()
                                if node.lineno <= len(lines)
                                else "",
                                "suggestion": 'Add context_type parameter: save_context("manual", data)',
                            }
                        )

                    elif (
                        func_name and func_name.endswith("Configurator") and class_name
                    ):
                        # Check class instantiation
                        if len(node.args) == 4:  # Common wrong pattern
                            issues.append(
                                {
                                    "type": "class_instantiation_error",
                                    "file": str(file_path),
                                    "line": node.lineno,
                                    "column": node.col_offset,
                                    "message": f"{func_name} constructor arguments may be in wrong order",
                                    "severity": "error",
                                    "code_snippet": lines[node.lineno - 1].strip()
                                    if node.lineno <= len(lines)
                                    else "",
                                    "suggestion": "Check constructor signature: __init__(platform, token, repo)",
                                }
                            )

                    elif expected_args and len(node.args) != expected_args:
                        issues.append(
                            {
                                "type": "argument_count_mismatch",
                                "file": str(file_path),
                                "line": node.lineno,
                                "column": node.col_offset,
                                "message": f"{func_name}() expects {expected_args} arguments but got {len(node.args)}",
                                "severity": "warning",
                                "code_snippet": lines[node.lineno - 1].strip()
                                if node.lineno <= len(lines)
                                else "",
                                "suggestion": f"Check function signature and provide {expected_args} arguments",
                            }
                        )

        except (SyntaxError, UnicodeDecodeError) as e:
            issues.append(
                {
                    "type": "parse_error",
                    "file": str(file_path),
                    "line": 0,
                    "column": 0,
                    "message": f"Failed to parse file: {e}",
                    "severity": "error",
                    "code_snippet": "",
                    "suggestion": "Fix syntax errors",
                }
            )

        return issues

    def analyze_undefined_methods(self, file_path: Path) -> List[Dict[str, Any]]:
        """Detect calls to undefined methods"""
        issues = []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Look for common undefined method patterns
            undefined_patterns = [
                (
                    r"\.setup\(.*\)",
                    'Method "setup" may not exist - check if it should be "configure"',
                ),
                (
                    r"\.contains\(",
                    'Method "contains" does not exist on strings - use "in" operator',
                ),
                (
                    r"urlopen\(",
                    "urllib.urlopen is deprecated - use urllib.request.urlopen",
                ),
            ]

            lines = content.split("\n")
            for i, line in enumerate(lines, 1):
                for pattern, message in undefined_patterns:
                    if re.search(pattern, line):
                        issues.append(
                            {
                                "type": "undefined_method",
                                "file": str(file_path),
                                "line": i,
                                "column": 0,
                                "message": message,
                                "severity": "error",
                                "code_snippet": line.strip(),
                                "suggestion": "Check method name and availability",
                            }
                        )

        except Exception:
            pass  # Skip files that can't be analyzed

        return issues

    def analyze_type_issues(self, file_path: Path) -> List[Dict[str, Any]]:
        """Detect potential type-related issues"""
        issues = []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            lines = content.split("\n")
            for i, line in enumerate(lines, 1):
                # Check for common type issues
                if ": any" in line.lower() or "= any(" in line.lower():
                    issues.append(
                        {
                            "type": "type_safety",
                            "file": str(file_path),
                            "line": i,
                            "column": 0,
                            "message": 'Usage of "any" type reduces type safety',
                            "severity": "warning",
                            "code_snippet": line.strip(),
                            "suggestion": 'Use specific types instead of "any"',
                        }
                    )

                # Check for missing return types
                if re.match(r"\s*def\s+\w+\([^)]*\):$", line) and "self" in line:
                    issues.append(
                        {
                            "type": "missing_type_annotation",
                            "file": str(file_path),
                            "line": i,
                            "column": 0,
                            "message": "Method missing return type annotation",
                            "severity": "info",
                            "code_snippet": line.strip(),
                            "suggestion": "Add return type annotation -> ReturnType",
                        }
                    )

        except Exception:
            pass  # Skip files that can't be analyzed

        return issues

    def analyze_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Analyze a single Python file for CodeQL-style issues"""
        all_issues = []

        all_issues.extend(self.analyze_argument_count_mismatches(file_path))
        all_issues.extend(self.analyze_undefined_methods(file_path))
        all_issues.extend(self.analyze_type_issues(file_path))

        return all_issues

    def analyze_project(self, root_dir: Path = None) -> Dict[str, Any]:
        """Analyze entire project for CodeQL-style issues"""
        if root_dir is None:
            root_dir = Path.cwd()

        results = {
            "total_files": 0,
            "files_with_issues": 0,
            "total_issues": 0,
            "issues_by_severity": {"error": 0, "warning": 0, "info": 0},
            "issues": [],
        }

        # Find all Python files
        python_files = list(root_dir.rglob("*.py"))
        results["total_files"] = len(python_files)

        for file_path in python_files:
            file_issues = self.analyze_file(file_path)

            if file_issues:
                results["files_with_issues"] += 1
                results["issues"].extend(file_issues)

                for issue in file_issues:
                    severity = issue.get("severity", "info")
                    results["issues_by_severity"][severity] += 1
                    results["total_issues"] += 1

        return results

    def print_results(self, results: Dict[str, Any], verbose: bool = False):
        """Print analysis results in a readable format"""
        print("\n🔍 CodeQL-Style Static Analysis Results")
        print(f"{'='*50}")
        print(f"Files Analyzed: {results['total_files']}")
        print(f"Files with Issues: {results['files_with_issues']}")
        print(f"Total Issues: {results['total_issues']}")
        print(f"Errors: {results['issues_by_severity']['error']}")
        print(f"Warnings: {results['issues_by_severity']['warning']}")
        print(f"Info: {results['issues_by_severity']['info']}")

        if results["total_issues"] == 0:
            print("\n✅ No CodeQL-style issues found!")
            return True

        # Group issues by file
        issues_by_file = {}
        for issue in results["issues"]:
            file_path = issue["file"]
            if file_path not in issues_by_file:
                issues_by_file[file_path] = []
            issues_by_file[file_path].append(issue)

        # Print issues
        for file_path, file_issues in issues_by_file.items():
            print(f"\n📁 {file_path}")
            print("-" * len(file_path))

            for issue in file_issues:
                severity_icon = {"error": "❌", "warning": "⚠️", "info": "ℹ️"}
                icon = severity_icon.get(issue["severity"], "ℹ️")

                print(f"  {icon} Line {issue['line']}: {issue['message']}")

                if verbose and issue["code_snippet"]:
                    print(f"     Code: {issue['code_snippet']}")

                if issue.get("suggestion"):
                    print(f"     💡 {issue['suggestion']}")

        return results["issues_by_severity"]["error"] == 0


def main():
    parser = argparse.ArgumentParser(description="Enhanced Pre-Push Quality Gate")
    parser.add_argument(
        "--fix", action="store_true", help="Auto-fix issues when possible"
    )
    parser.add_argument(
        "--codeql", action="store_true", help="Run CodeQL-style analysis only"
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--json", help="Output results to JSON file")

    args = parser.parse_args()

    if args.codeql:
        # Run only CodeQL-style analysis
        analyzer = CodeQLStyleAnalyzer()
        results = analyzer.analyze_project()

        if args.json:
            with open(args.json, "w") as f:
                json.dump(results, f, indent=2)

        success = analyzer.print_results(results, args.verbose)
        sys.exit(0 if success else 1)

    else:
        # Run full validation including existing checks
        print("🚀 Running Enhanced Pre-Push Quality Gate...")

        # First run our existing local validation
        cmd = ["python", "tools/validation/local-validation.py"]
        if args.verbose:
            cmd.append("--verbose")

        result = subprocess.run(cmd)
        local_validation_passed = result.returncode == 0

        # Then run CodeQL-style analysis
        analyzer = CodeQLStyleAnalyzer()
        codeql_results = analyzer.analyze_project()
        codeql_passed = analyzer.print_results(codeql_results, args.verbose)
        # Overall result
        overall_success = local_validation_passed and codeql_passed
        print(f"\n{'='*60}")
        print("🎯 ENHANCED QUALITY GATE SUMMARY")
        print(f"{'='*60}")
        if overall_success:
            print("✅ ALL CHECKS PASSED - Ready to push!")
        else:
            print("❌ QUALITY GATE FAILED - Fix issues before pushing")

        if not local_validation_passed:
            print("   - Local validation issues found")
        if not codeql_passed:
            print("   - CodeQL-style issues found")
        sys.exit(0 if overall_success else 1)


if __name__ == "__main__":
    main()
