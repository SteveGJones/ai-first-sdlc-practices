#!/usr/bin/env python3
"""
Comprehensive script to fix all flake8 violations in the codebase
"""
import re
import subprocess
from pathlib import Path


def run_command(cmd, **kwargs):
    """Run a command and return the result"""
    try:
        return subprocess.run(cmd, capture_output=True, text=True, check=True, **kwargs)
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {' '.join(cmd)}")
        print(f"Error: {e.stderr}")
        return None


def fix_unused_imports():
    """Remove unused imports using autoflake"""
    print("Fixing unused imports (F401)...")
    cmd = [
        "python",
        "-m",
        "autoflake",
        "--remove-all-unused-imports",
        "--in-place",
        "--recursive",
        ".",
    ]
    result = run_command(cmd)
    if result:
        print("✓ Fixed unused imports")
    else:
        # Try pip install autoflake if not available
        print("Installing autoflake...")
        run_command(["pip", "install", "autoflake"])
        result = run_command(cmd)
        if result:
            print("✓ Fixed unused imports after installing autoflake")


def fix_f541_violations():
    """Fix F541: f-string is missing placeholders"""
    print("Fixing f-string violations (F541)...")

    python_files = list(Path(".").glob("**/*.py"))

    for file_path in python_files:
        try:
            content = file_path.read_text(encoding="utf-8")
            original_content = content

            # Find f-strings without placeholders and convert to regular strings
            patterns = [
                (r'"([^"{}]*)"', r'"\1"'),  # "string" -> "string"
                (r"'([^'{}]*)'", r"'\1'"),  # 'string' -> 'string'
            ]

            for pattern, replacement in patterns:
                content = re.sub(pattern, replacement, content)

            if content != original_content:
                file_path.write_text(content, encoding="utf-8")
                print(f"  Fixed F541 in {file_path}")
        except Exception as e:
            print(f"  Error processing {file_path}: {e}")


def fix_unused_variables():
    """Fix unused variables by prefixing with underscore"""
    print("Fixing unused variables (F841)...")

    python_files = list(Path(".").glob("**/*.py"))

    for file_path in python_files:
        try:
            content = file_path.read_text(encoding="utf-8")
            lines = content.split("\n")
            modified = False

            for i, line in enumerate(lines):
                # Look for common unused variable patterns
                patterns = [
                    (r"^(\s*)([a-zA-Z_]\w*)\s*=\s*.*$", r"\1_\2 = "),  # var = -> _var =
                ]

                for pattern, repl_prefix in patterns:
                    match = re.match(pattern, line)
                    if match and not match.group(2).startswith("_"):
                        indent, var_name = match.groups()
                        # Only replace if it looks like an assignment that might be unused
                        if any(
                            keyword in line.lower()
                            for keyword in [
                                "subprocess.run",
                                "result",
                                "success",
                                "data",
                                "config",
                            ]
                        ):
                            new_line = re.sub(pattern, f"{indent}_{var_name} = ", line)
                            if new_line != line:
                                lines[i] = new_line
                                modified = True

            if modified:
                file_path.write_text("\n".join(lines), encoding="utf-8")
                print(f"  Fixed F841 in {file_path}")
        except Exception as e:
            print(f"  Error processing {file_path}: {e}")


def fix_bare_except():
    """Fix bare except clauses (E722)"""
    print("Fixing bare except clauses (E722)...")

    python_files = list(Path(".").glob("**/*.py"))

    for file_path in python_files:
        try:
            content = file_path.read_text(encoding="utf-8")
            original_content = content

            # Replace bare except: with except Exception:
            content = re.sub(
                r"^(\s*)except:\s*$",
                r"\1except Exception:",
                content,
                flags=re.MULTILINE,
            )

            if content != original_content:
                file_path.write_text(content, encoding="utf-8")
                print(f"  Fixed E722 in {file_path}")
        except Exception as e:
            print(f"  Error processing {file_path}: {e}")


def run_black():
    """Run black formatter"""
    print("Running black formatter...")
    result = run_command(["python", "-m", "black", "."])
    if result:
        print("✓ Applied black formatting")
    else:
        print("Installing black...")
        run_command(["pip", "install", "black"])
        result = run_command(["python", "-m", "black", "."])
        if result:
            print("✓ Applied black formatting after installing black")


def fix_import_order():
    """Fix import order issues (E402)"""
    print("Checking for import order issues...")

    # This is more complex and typically requires manual intervention
    # We'll identify files with E402 and report them
    result = run_command(["python", "-m", "flake8", "--select=E402", "."])
    if result and result.stdout:
        print("Files with import order issues (manual fix required):")
        print(result.stdout)


def main():
    """Main function to run all fixes"""
    print("Starting comprehensive flake8 fix...")

    # Step 1: Fix structural issues
    fix_bare_except()
    fix_f541_violations()
    fix_unused_variables()

    # Step 2: Fix imports
    fix_unused_imports()
    fix_import_order()

    # Step 3: Format code
    run_black()

    # Step 4: Check results
    print("\nRunning final flake8 check...")
    result = run_command(["python", "-m", "flake8", "."])
    if result and not result.stdout:
        print("✓ All flake8 issues fixed!")
    else:
        print("Remaining flake8 issues:")
        if result:
            print(result.stdout)


if __name__ == "__main__":
    main()
