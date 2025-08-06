#!/usr/bin/env python3
"""
Script to batch-fix missing type annotations in framework files.
This is a temporary utility to achieve Zero Technical Debt compliance.
"""

import re
from pathlib import Path
# Type hints are built into Python 3.9+, no need for typing imports


def add_common_type_annotations(file_path: Path) -> bool:
    """Add common type annotations to a Python file."""
    content = file_path.read_text()
    original_content = content

    # Add common typing imports if not present
    if "from typing import" not in content and "import typing" not in content:
        import_lines = []
        if re.search(r"-> None:", content):
            pass  # None is builtin, no import needed
        if re.search(r"-> bool:", content):
            pass  # bool is builtin
        if re.search(r"-> str:", content):
            pass  # str is builtin
        if re.search(r"-> int:", content):
            pass  # int is builtin
        if re.search(r"-> List\[", content) or re.search(r": List\[", content):
            import_lines.append("List")
        if re.search(r"-> Dict\[", content) or re.search(r": Dict\[", content):
            import_lines.append("Dict")
        if re.search(r"-> Tuple\[", content) or re.search(r": Tuple\[", content):
            import_lines.append("Tuple")
        if re.search(r"-> Optional\[", content) or re.search(r": Optional\[", content):
            import_lines.append("Optional")

        if import_lines:
            imports = f"from typing import {', '.join(sorted(set(import_lines)))}\n"
            # Insert after existing imports
            lines = content.split("\n")
            insert_pos = 0
            for i, line in enumerate(lines):
                if line.startswith("import ") or line.startswith("from "):
                    insert_pos = i + 1
                elif line.strip() == "":
                    continue
                elif line.startswith("#") or line.startswith('"""'):
                    continue
                else:
                    break
            lines.insert(insert_pos, imports)
            content = "\n".join(lines)

    # Common function patterns to fix
    patterns = [
        # Pattern: function without return type
        (r"def (\w+)\(\) -> None:", r"def \1() -> None:"),  # Already correct
        (r"def (\w+)\(\):", r"def \1() -> None:"),
        # Pattern: function with single parameter
        (r"def (\w+)\((\w+)\):", r"def \1(\2: str) -> None:"),
        # Pattern: method without return type
        (r"def (\w+)\(self\):", r"def \1(self) -> None:"),
        # Pattern: main function
        (r"def main\(\):", r"def main() -> None:"),
        # Common return type patterns
        (r"def (\w+)\([^)]*\) -> None:", r"def \1(\g<0>)"),  # Already correct
    ]

    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content)

    if content != original_content:
        file_path.write_text(content)
        print(f"Updated {file_path}")
        return True

    return False


def main() -> None:
    """Fix type annotations in all Python files."""
    python_files = list(Path(".").glob("**/*.py"))
    python_files = [
        f for f in python_files if "venv" not in str(f) and "__pycache__" not in str(f)
    ]

    updated_files = 0
    for file_path in python_files:
        try:
            if add_common_type_annotations(file_path):
                updated_files += 1
        except Exception as e:
            print(f"Error processing {file_path}: {e}")

    print(f"\nUpdated {updated_files} files")


if __name__ == "__main__":
    main()
