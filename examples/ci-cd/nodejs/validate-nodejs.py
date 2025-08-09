#!/usr/bin/env python3
"""
Language-specific validator for Node.js/TypeScript
Zero tolerance for all quality issues
Enforces AI-First SDLC standards
"""

import subprocess
import sys
import json
from pathlib import Path


def run_command(name: str, cmd: list, working_dir: str = None) -> bool:
    """Run a command and return success status"""
    print(f"\n🔍 Running {name}...")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=working_dir, check=False)

        if result.returncode != 0:
            print(f"❌ {name} FAILED")
            if result.stdout:
                print("STDOUT:", result.stdout)
            if result.stderr:
                print("STDERR:", result.stderr)
            return False
        else:
            print(f"✅ {name} passed")
            return True
    except FileNotFoundError:
        print(f"❌ {name} FAILED: Command not found")
        return False


def check_package_json() -> bool:
    """Validate package.json exists and has required scripts"""
    if not Path("package.json").exists():
        print("❌ package.json not found")
        return False

    try:
        with open("package.json", "r") as f:
            pkg = json.load(f)

        required_scripts = ["test", "lint", "type-check"]
        missing_scripts = []

        scripts = pkg.get("scripts", {})
        for script in required_scripts:
            if script not in scripts:
                missing_scripts.append(script)

        if missing_scripts:
            print(f"❌ Missing required scripts in package.json: {missing_scripts}")
            return False

        print("✅ package.json validation passed")
        return True
    except Exception as e:
        print(f"❌ Error reading package.json: {e}")
        return False


def check_typescript_config() -> bool:
    """Validate TypeScript configuration if present"""
    tsconfig_files = ["tsconfig.json", "tsconfig.app.json", "tsconfig.lib.json"]

    for tsconfig in tsconfig_files:
        if Path(tsconfig).exists():
            try:
                with open(tsconfig, "r") as f:
                    config = json.load(f)
                compiler_options = config.get("compilerOptions", {})

                # Check for strict mode requirements
                strict_requirements = {
                    "strict": True,
                    "noImplicitAny": True,
                    "strictNullChecks": True,
                    "noUnusedLocals": True,
                    "noUnusedParameters": True,
                    "noImplicitReturns": True,
                    "noFallthroughCasesInSwitch": True,
                }

                missing_strict = []
                for option, required_value in strict_requirements.items():
                    if compiler_options.get(option) != required_value:
                        missing_strict.append(f"{option}: {required_value}")

                if missing_strict:
                    print(f"❌ {tsconfig} missing strict options: {missing_strict}")
                    return False

                print(f"✅ {tsconfig} validation passed")
                return True
            except Exception as e:
                print(f"❌ Error reading {tsconfig}: {e}")
                return False

    print("ℹ️  No TypeScript config found (JavaScript project)")
    return True


def main() -> None:
    """Run ALL quality checks for Node.js/TypeScript"""
    print("🚀 Starting Node.js AI-First SDLC Validation")
    print("=" * 50)

    errors = 0

    # Check package.json first
    if not check_package_json():
        errors += 1

    # Check TypeScript configuration if applicable
    if not check_typescript_config():
        errors += 1

    # Install dependencies if needed
    if Path("package-lock.json").exists() or Path("yarn.lock").exists():
        print("\n📦 Installing dependencies...")
        if Path("yarn.lock").exists():
            if not run_command("Yarn Install", ["yarn", "install", "--frozen-lockfile"]):
                errors += 1
        else:
            if not run_command("NPM Install", ["npm", "ci"]):
                errors += 1

    # Define quality checks
    checks = [
        # Type checking (if TypeScript)
        ("Type Check", ["npm", "run", "type-check"]),
        # Linting with zero warnings tolerance
        (
            "ESLint",
            ["npx", "eslint", ".", "--max-warnings=0", "--ext=.js,.jsx,.ts,.tsx"],
        ),
        # Code formatting
        ("Prettier Check", ["npx", "prettier", "--check", "."]),
        # Security audit
        ("Security Audit", ["npm", "audit", "--audit-level=moderate"]),
        # Unit tests
        ("Unit Tests", ["npm", "test"]),
        # Build check (if build script exists)
        ("Build Check", ["npm", "run", "build"]),
    ]

    # Check if scripts exist before running
    try:
        with open("package.json", "r") as f:
            pkg = json.load(f)
            scripts = pkg.get("scripts", {})
    except Exception:
        scripts = {}

    for name, cmd in checks:
        # Skip build check if no build script
        if name == "Build Check" and "build" not in scripts:
            print(f"ℹ️  Skipping {name} (no build script)")
            continue

        # Skip type check if no type-check script (pure JS project)
        if name == "Type Check" and "type-check" not in scripts:
            print(f"ℹ️  Skipping {name} (no TypeScript)")
            continue

        if not run_command(name, cmd):
            errors += 1

    # Additional Zero Technical Debt checks
    print("\n🔍 Zero Technical Debt Checks...")

    # Check for TODO/FIXME comments
    todo_check = subprocess.run(
        [
            "grep",
            "-r",
            "-n",
            "--include=*.js",
            "--include=*.ts",
            "--include=*.jsx",
            "--include=*.tsx",
            "-E",
            "(TODO|FIXME|HACK|XXX)",
            ".",
        ],
        capture_output=True,
        text=True,
    )

    if todo_check.returncode == 0:
        print("❌ Found TODO/FIXME/HACK comments (forbidden):")
        print(todo_check.stdout)
        errors += 1
    else:
        print("✅ No TODO/FIXME/HACK comments found")

    # Check for console.log statements (except in development configs)
    console_check = subprocess.run(
        [
            "grep",
            "-r",
            "-n",
            "--include=*.js",
            "--include=*.ts",
            "--include=*.jsx",
            "--include=*.tsx",
            "--exclude-dir=node_modules",
            "--exclude-dir=dist",
            "--exclude-dir=build",
            "console\\.log",
            ".",
        ],
        capture_output=True,
        text=True,
    )

    if console_check.returncode == 0:
        print("❌ Found console.log statements (forbidden in production code):")
        print(console_check.stdout)
        errors += 1
    else:
        print("✅ No console.log statements found")

    # Check for any type usage in TypeScript
    if Path("tsconfig.json").exists():
        any_check = subprocess.run(
            [
                "grep",
                "-r",
                "-n",
                "--include=*.ts",
                "--include=*.tsx",
                "--exclude-dir=node_modules",
                ": any",
                ".",
            ],
            capture_output=True,
            text=True,
        )

        if any_check.returncode == 0:
            print("❌ Found 'any' type usage (forbidden):")
            print(any_check.stdout)
            errors += 1
        else:
            print("✅ No 'any' type usage found")

    print("\n" + "=" * 50)

    if errors > 0:
        print(f"🚫 VALIDATION FAILED: {errors} checks failed")
        print("YOU ARE FORBIDDEN FROM PROCEEDING")
        print("Fix all issues and run validation again.")
        sys.exit(1)

    print("✅ ALL CHECKS PASSED - Zero Technical Debt Achieved")
    print("🎉 Ready for AI-First SDLC compliance")
    sys.exit(0)


if __name__ == "__main__":
    main()
