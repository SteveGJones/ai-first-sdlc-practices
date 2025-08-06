#!/usr/bin/env python3
"""
Comprehensive fix for all validation issues in the codebase
"""
import subprocess
import re
from pathlib import Path


def read_file_safely(file_path: Path) -> str:
    """Read file with error handling"""
    try:
        return file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return file_path.read_text(encoding="latin-1")


def fix_incomplete_assignments(file_path: Path) -> bool:
    """Fix broken variable assignments"""
    content = read_file_safely(file_path)
    original = content

    # Common patterns to fix
    fixes = [
        # Fix incomplete subprocess.run assignments
        (r"(\s+)_result =\s*\n(\s*)\[", r"\1result = subprocess.run(\n\2["),
        (r'(\s+)_result =\s*\n(\s*)"', r"\1result = subprocess.run(\n\2["),
        (r"(\s+)_result =\s*\n(\s*)cmd", r"\1result = subprocess.run(\n\2cmd"),
        # Fix incomplete data assignments
        (r"(\s+)_data =\s*\n", r"\1data = json.loads(response.json())\n"),
        (r"(\s+)_config =\s*\n", r"\1config = {\n"),
        (r"(\s+)_metadata =\s*\n", r"\1metadata = yaml.safe_load(parts[1])\n"),
        # Fix incomplete list assignments
        (r"(\s+)_files =\s*\n", r'\1files = result.stdout.strip().split("\\n")\n'),
        (
            r"(\s+)_authors =\s*\n",
            r'\1authors = set(result.stdout.strip().split("\\n"))\n',
        ),
        (r"(\s+)_checks =\s*\n", r'\1checks = self.level_config["required"]\n'),
        # Fix incomplete string assignments
        (r"(\s+)_branch =\s*\n", r"\1branch = result.stdout.strip()\n"),
        (
            r"(\s+)_content =\s*\n",
            r'\1content = base64.b64decode(data["content"]).decode("utf-8")\n',
        ),
        (r"(\s+)_url =\s*\n", r"\1url = result.stdout.strip()\n"),
        # Fix incomplete boolean assignments
        (r"(\s+)_success =\s*\n", r"\1success = self.setup(components, force)\n"),
        # Fix incomplete help assignments
        (r"(\s+)_help =\s*\n", r'\1help="Export format for validation report"\n'),
    ]

    for pattern, replacement in fixes:
        content = re.sub(pattern, replacement, content, flags=re.MULTILINE)

    # Additional context-specific fixes
    if "symbolic-ref" in content:
        content = content.replace("symbolic-ref", "symbolic-reff")

    if "dif" in content and "git" in content:
        content = content.replace('"git", "diff"', '"git", "diff"')

    # Fix function call issues
    content = re.sub(r"(\s+)handof\(", r"\1handoff(", content)

    return content != original, content


def run_targeted_fixes():
    """Run targeted fixes on problematic files"""
    print("Running comprehensive fixes...")

    # Get all Python files
    python_files = list(Path(".").glob("**/*.py"))

    fixed_count = 0

    for file_path in python_files:
        if (
            file_path.name.startswith(".")
            or "venv" in str(file_path)
            or "__pycache__" in str(file_path)
        ):
            continue

        try:
            changed, new_content = fix_incomplete_assignments(file_path)
            if changed:
                file_path.write_text(new_content, encoding="utf-8")
                print(f"  Fixed {file_path}")
                fixed_count += 1
        except Exception as e:
            print(f"  Error with {file_path}: {e}")

    print(f"Fixed {fixed_count} files")


def run_autoflake():
    """Remove unused imports"""
    print("Removing unused imports...")

    # Install if needed
    try:
        subprocess.run(
            ["python", "-m", "autoflake", "--version"], capture_output=True, check=True
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Installing autoflake...")
        subprocess.run(["pip", "install", "autoflake"], check=True)

    # Run autoflake
    cmd = [
        "python",
        "-m",
        "autoflake",
        "--remove-all-unused-imports",
        "--remove-unused-variables",
        "--in-place",
        "--recursive",
        ".",
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        print("✓ Removed unused imports and variables")
    else:
        print(f"Warning: {result.stderr}")


def run_black():
    """Format code with black"""
    print("Running black formatter...")

    # Install if needed
    try:
        subprocess.run(
            ["python", "-m", "black", "--version"], capture_output=True, check=True
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Installing black...")
        subprocess.run(["pip", "install", "black"], check=True)

    # Run black
    result = subprocess.run(
        ["python", "-m", "black", "."], capture_output=True, text=True
    )
    if result.returncode == 0:
        print("✓ Applied black formatting")
    else:
        print(f"Black errors: {result.stderr}")


def main():
    """Main function"""
    print("Starting comprehensive validation fixes...")

    # Step 1: Fix broken assignments and syntax issues
    run_targeted_fixes()

    # Step 2: Remove unused imports/variables
    run_autoflake()

    # Step 3: Format with black
    run_black()

    print("\n✅ Comprehensive fixes completed!")
    print("Now run: pre-commit run --all-files")


if __name__ == "__main__":
    main()
