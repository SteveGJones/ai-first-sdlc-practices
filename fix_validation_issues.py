#!/usr/bin/env python3
"""
Fix the specific validation issues found in pre-commit hooks
"""
import subprocess
import re
from pathlib import Path
from typing import List


def run_command(cmd: List[str]) -> bool:
    """Run a command safely"""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return True
    except subprocess.CalledProcessError:
        return False


def fix_incomplete_assignments():
    """Fix incomplete variable assignments from the batch fix"""
    print("Fixing incomplete assignments...")

    # Files that were broken by the batch fix
    broken_files = [
        "fix_flake8.py",
        "batch_fix_flake8.py",
        "setup-smart.py",
        "git_operations.py",
    ]

    for file_name in broken_files:
        file_path = Path(file_name)
        if not file_path.exists():
            continue

        try:
            content = file_path.read_text()

            # Fix patterns like "_result = " or "_data = " at end of lines
            # These were caused by overly aggressive variable prefixing

            # Pattern 1: Fix incomplete assignments
            content = re.sub(
                r"^(\s*)_([a-zA-Z_]\w*)\s*=\s*$",
                r"\1\2 = None  # TODO: Fix this assignment",
                content,
                flags=re.MULTILINE,
            )

            # Pattern 2: Fix incomplete subprocess assignments
            if "_result = \n" in content:
                content = content.replace("_result = \n", "result = subprocess.run(\n")

            # Pattern 3: Fix variable declarations that got cut off
            content = re.sub(
                r"^(\s*)_(\w+)\s*=\s*\n(\s*)(.*?)$",
                r"\1\2 = \4",
                content,
                flags=re.MULTILINE,
            )

            file_path.write_text(content)
            print(f"  Fixed {file_name}")

        except Exception as e:
            print(f"  Error fixing {file_name}: {e}")


def run_autoflake():
    """Remove unused imports with autoflake"""
    print("Removing unused imports...")

    # Install autoflake if needed
    if not run_command(["python", "-m", "autoflake", "--version"]):
        print("Installing autoflake...")
        run_command(["pip", "install", "autoflake"])

    # Remove unused imports
    cmd = [
        "python",
        "-m",
        "autoflake",
        "--remove-all-unused-imports",
        "--in-place",
        "--recursive",
        ".",
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print("✓ Removed unused imports")
        else:
            print(f"autoflake failed: {result.stderr}")
    except Exception as e:
        print(f"Error running autoflake: {e}")


def fix_file_permissions():
    """Fix file permissions for scripts with shebangs"""
    print("Fixing file permissions...")

    python_files = list(Path(".").glob("**/*.py"))

    for file_path in python_files:
        try:
            content = file_path.read_text()
            if content.startswith("#!/"):
                # Make executable
                subprocess.run(["chmod", "+x", str(file_path)], check=True)
                print(f"  Made {file_path} executable")
        except Exception as e:
            print(f"  Error with {file_path}: {e}")


def fix_trailing_whitespace():
    """Fix trailing whitespace issues"""
    print("Fixing trailing whitespace...")

    python_files = list(Path(".").glob("**/*.py"))

    for file_path in python_files:
        try:
            content = file_path.read_text()

            # Remove trailing whitespace
            lines = content.splitlines()
            cleaned_lines = [line.rstrip() for line in lines]

            # Ensure file ends with newline
            if cleaned_lines and not content.endswith("\n"):
                cleaned_lines.append("")

            new_content = "\n".join(cleaned_lines)

            if new_content != content:
                file_path.write_text(new_content)
                print(f"  Fixed whitespace in {file_path}")

        except Exception as e:
            print(f"  Error with {file_path}: {e}")


def fix_bare_except_clauses():
    """Fix bare except clauses"""
    print("Fixing bare except clauses...")

    python_files = list(Path(".").glob("**/*.py"))

    for file_path in python_files:
        try:
            content = file_path.read_text()
            original = content

            # Replace bare except: with except Exception:
            content = re.sub(
                r"^(\s*)except:\s*$",
                r"\1except Exception:",
                content,
                flags=re.MULTILINE,
            )

            if content != original:
                file_path.write_text(content)
                print(f"  Fixed bare except in {file_path}")

        except Exception as e:
            print(f"  Error with {file_path}: {e}")


def main():
    """Run all fixes"""
    print("Starting targeted validation fixes...\n")

    # Step 1: Fix broken assignments from batch fix
    fix_incomplete_assignments()

    # Step 2: Fix file permissions
    fix_file_permissions()

    # Step 3: Fix whitespace issues
    fix_trailing_whitespace()

    # Step 4: Fix bare except clauses
    fix_bare_except_clauses()

    # Step 5: Remove unused imports
    run_autoflake()

    print("\n✅ Validation fixes completed!")
    print("\nNext: Run 'pre-commit run --all-files' to check remaining issues")


if __name__ == "__main__":
    main()
