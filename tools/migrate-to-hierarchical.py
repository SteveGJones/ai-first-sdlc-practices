#!/usr/bin/env python3
"""
Migrates projects from legacy CLAUDE.md to hierarchical instruction system.
"""
import sys
import urllib.request
from pathlib import Path
import shutil
from datetime import datetime
from typing import Tuple, List

GITHUB_RAW_BASE = "https://raw.githubusercontent.com/SteveGJones/ai-first-sdlc-practices/main"

HIERARCHICAL_FILES = [
    "CLAUDE-CORE.md",
    "CLAUDE-SETUP.md",
    "CLAUDE-CONTEXT-architecture.md",
    "CLAUDE-CONTEXT-validation.md",
    "CLAUDE-CONTEXT-update.md",
    "CLAUDE-CONTEXT-language-validators.md",
]


def download_file(filename: str) -> bool:
    """Download a file from the framework repository."""
    url = f"{GITHUB_RAW_BASE}/{filename}"
    try:
        print(f"  Downloading {filename}...")
        response = urllib.request.urlopen(url)
        content = response.read().decode("utf-8")
        with open(filename, "w") as f:
            f.write(content)
        print(f"  ✅ Downloaded {filename}")
        return True
    except Exception as e:
        print(f"  ❌ Failed to download {filename}: {e}")
        return False


def check_for_customizations() -> Tuple[bool, List[str]]:
    """Check if CLAUDE.md has been customized."""
    if not Path("CLAUDE.md").exists():
        return False, []

    with open("CLAUDE.md", "r") as f:
        content = f.read()

    # Look for project-specific content
    customizations = []

    # Check for specific project mentions
    if "**Project**:" in content and "[Your Project Name]" not in content:
        customizations.append("Project-specific information detected")

    # Check for custom sections not in template
    custom_markers = [
        "## Custom",
        "## Project-Specific",
        "## Additional",
        "### Our",
        "### This Project",
    ]

    for marker in custom_markers:
        if marker.lower() in content.lower():
            customizations.append(f"Custom section detected: {marker}")

    return len(customizations) > 0, customizations


def migrate() -> None:
    """Main migration function."""
    print("🔄 AI-First SDLC: Migrating to Hierarchical Instruction System")
    print("=" * 60)

    # Check current state
    print("\n📋 Checking current installation...")

    has_legacy = Path("CLAUDE.md").exists()
    has_core = Path("CLAUDE-CORE.md").exists()

    if not has_legacy and has_core:
        print("✅ Already using hierarchical system!")
        return 0

    if not has_legacy and not has_core:
        print("❌ No instruction files found. Please run setup first.")
        return 1

    # Check for customizations
    print("\n🔍 Checking for customizations in CLAUDE.md...")
    has_custom, customizations = check_for_customizations()

    if has_custom:
        print("⚠️  Customizations detected:")
        for custom in customizations:
            print(f"   - {custom}")
        print("\n📝 You may want to preserve these in your project documentation.")

        # Ask user
        response = input("\nContinue with migration? (y/n): ").lower()
        if response != "y":
            print("Migration cancelled.")
            return 0

    # Backup existing CLAUDE.md
    if has_legacy:
        backup_name = f"CLAUDE.md.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        print(f"\n💾 Backing up CLAUDE.md to {backup_name}")
        shutil.copy("CLAUDE.md", backup_name)

    # Download hierarchical files
    print("\n📥 Downloading hierarchical instruction files...")

    all_success = True
    for filename in HIERARCHICAL_FILES:
        if not Path(filename).exists():
            if not download_file(filename):
                all_success = False

    if not all_success:
        print("\n❌ Some files failed to download. Please check your connection.")
        return 1

    # Create new CLAUDE.md with deprecation notice
    print("\n📝 Creating deprecation notice in CLAUDE.md...")
    deprecation_content = """# CLAUDE.md

⚠️ **DEPRECATED**: This file exists only for backward compatibility and will be removed in v2.0.0.

Please use the new hierarchical instruction system:
- Start with: CLAUDE-CORE.md
- For setup: CLAUDE-SETUP.md
- For other tasks: See context loading table in CLAUDE-CORE.md

Your previous CLAUDE.md has been backed up.
"""

    with open("CLAUDE.md", "w") as f:
        f.write(deprecation_content)

    # Final report
    print("\n✅ Migration Complete!")
    print("-" * 60)
    print("Next steps:")
    print("1. Review CLAUDE-CORE.md for essential instructions")
    print("2. Check backup file for any customizations to preserve")
    print("3. Update your prompts to reference CLAUDE-CORE.md")
    print("4. Run validation: python tools/validation/validate-pipeline.py")

    if has_custom:
        print("\n⚠️  Remember to migrate your customizations to appropriate files:")
        print("   - Project info → README.md or project docs")
        print("   - Custom rules → Create project-specific validators")
        print("   - Workflow changes → Update relevant context files")

    return 0


if __name__ == "__main__":
    sys.exit(migrate())
