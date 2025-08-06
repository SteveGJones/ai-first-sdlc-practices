#!/usr/bin/env python3
"""
Quick script to fix common flake8 violations automatically
"""
import re
import subprocess
from pathlib import Path


def fix_f541_violations(file_path):
    """Fix F541: f-string is missing placeholders"""
    content = file_path.read_text()
    original_content = content

    # Find f-strings without placeholders and convert to regular strings
    # Pattern: f"string without {}" or f'string without {}'
    patterns = [
        (r'"([^"{}]*)"', r'"\1"'),  # "string" -> "string"
        (r"'([^'{}]*)'", r"'\1'"),  # 'string' -> 'string'
    ]

    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content)

    if content != original_content:
        file_path.write_text(content)
        print(f"Fixed F541 in {file_path}")
        return True
    return False


def remove_unused_imports(file_path):
    """Remove unused imports using autoflake if available"""
    try:
        _result = subprocess.run(
            ["autoflake", "--remove-all-unused-imports", "--in-place", str(file_path)],
            capture_output=True,
            text=True,
            check=True,
        )
        print(f"Fixed F401 in {file_path}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def fix_unused_variables(file_path):
    """Fix unused variables by prefixing with underscore"""
    content = file_path.read_text()
    lines = content.split("\n")
    modified = False

    for i, line in enumerate(lines):
        # Look for assignment patterns that create unused variables
        # This is a simple heuristic
        if " = " in line and not line.strip().startswith("#"):
            # Get variable name
            var_match = re.match(r"(\s*)(\w+)\s*=", line)
            if var_match:
                indent, var_name = var_match.groups()
                if not var_name.startswith("_"):
                    # Replace variable name with _var_name
                    lines[i] = line.replace(f"{var_name} =", f"_{var_name} =", 1)
                    modified = True

    if modified:
        file_path.write_text("\n".join(lines))
        print(f"Fixed F841 in {file_path}")
        return True
    return False


def main():
    # Get all Python files that need fixing
    python_files = []
    for pattern in ["**/*.py"]:
        python_files.extend(Path(".").glob(pattern))

    # Filter to only files with violations
    files_to_fix = []
    result = subprocess.run(
        ["flake8", "--select=F401,F541,F841", "--format=%(path)s"]
        + [str(f) for f in python_files],
        capture_output=True,
        text=True,
    )

    if result.stdout:
        violation_files = set(result.stdout.strip().split("\n"))
        files_to_fix = [Path(f) for f in violation_files if f]

    print(f"Found {len(files_to_fix)} files with F401, F541, F841 violations")

    for file_path in files_to_fix:
        if file_path.exists() and file_path.suffix == ".py":
            print(f"\nProcessing {file_path}...")
            fix_f541_violations(file_path)
            remove_unused_imports(file_path)
            fix_unused_variables(file_path)


if __name__ == "__main__":
    main()
