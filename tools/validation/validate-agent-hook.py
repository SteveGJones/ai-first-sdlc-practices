#!/usr/bin/env python3
"""
PostToolUse Hook: Agent Format Validator

Validates agent files after Write or Edit operations.
Checks if the modified file is in an agents directory and validates
it against the official Claude Code sub-agent specification.

Install in .claude/settings.local.json:
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "python tools/validation/validate-agent-hook.py"
          }
        ]
      }
    ]
  }
}

Exit codes:
  0 = not an agent file, or validation passed
  2 = validation failed (blocks the operation)
"""

import json
import sys
import os
from pathlib import Path


def is_agent_file(file_path: str) -> bool:
    """Check if a file path is an agent file that should be validated."""
    if not file_path.endswith(".md"):
        return False

    path = Path(file_path)
    parts = path.parts

    # Check for agents/ directory or .claude/agents/ directory
    for i, part in enumerate(parts):
        if part == "agents":
            return True
        if part == ".claude" and i + 1 < len(parts) and parts[i + 1] == "agents":
            return True

    return False


def main():
    # Read hook input from stdin (JSON format per Claude Code hook spec)
    try:
        hook_input = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)  # Can't parse input, skip silently

    # Extract the file path from the tool input
    tool_input = hook_input.get("tool_input", {})
    file_path = tool_input.get("file_path", "")

    if not file_path:
        sys.exit(0)  # No file path, skip

    if not is_agent_file(file_path):
        sys.exit(0)  # Not an agent file, skip

    if not Path(file_path).exists():
        sys.exit(0)  # File doesn't exist yet (might be a failed write)

    # Import and run the validator
    # Find the validator relative to this script
    script_dir = Path(__file__).parent
    sys.path.insert(0, str(script_dir))

    try:
        from validate_agent_official import validate_agent_file
    except ImportError:
        # Try alternative import path
        try:
            validator_path = script_dir / "validate-agent-official.py"
            if validator_path.exists():
                import importlib.util

                spec = importlib.util.spec_from_file_location(
                    "validate_agent_official", validator_path
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                validate_agent_file = module.validate_agent_file
            else:
                sys.exit(0)  # Validator not found, skip
        except Exception:
            sys.exit(0)  # Can't load validator, skip

    # Validate in official mode (minimum compliance)
    report = validate_agent_file(Path(file_path), mode="official")

    if not report.valid_official:
        errors = [i for i in report.issues if i.severity == "error"]
        error_msgs = "\n".join(f"  - {e.field}: {e.message}" for e in errors)
        print(
            f"Agent format validation FAILED for {file_path}:\n{error_msgs}\n\n"
            "See docs/AGENT-FORMAT-SPEC.md for the required format.",
            file=sys.stderr,
        )
        sys.exit(2)  # Exit code 2 blocks the operation

    # Check for warnings
    warnings = [i for i in report.issues if i.severity == "warning"]
    if warnings:
        warning_msgs = "\n".join(f"  - {w.field}: {w.message}" for w in warnings)
        print(
            f"Agent format warnings for {file_path}:\n{warning_msgs}",
            file=sys.stderr,
        )

    sys.exit(0)  # Validation passed


if __name__ == "__main__":
    main()
