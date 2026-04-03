#!/usr/bin/env python3
"""Normalize agent YAML frontmatter to Claude Code plugin agent schema.

Keeps only: name, description, model, tools (in that order).
Strips: color, maturity, examples, Context, version, category, tags.
Adds model: sonnet if missing.
Adds tools: Read, Glob, Grep, Bash if missing.
Condenses multi-line descriptions to a single line (max 250 chars).
Preserves all body content below frontmatter unchanged.
"""

import argparse
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Agent file list (55 total: 52 mapped + 3 core for consistency)
# ---------------------------------------------------------------------------

AGENT_FILES = [
    # sdlc-core
    "agents/core/sdlc-enforcer.md",
    "agents/core/critical-goal-reviewer.md",
    "agents/testing/code-review-specialist.md",
    # sdlc-team-common
    "agents/core/solution-architect.md",
    "agents/core/deep-research-agent.md",
    "agents/testing/performance-engineer.md",
    "agents/core/observability-specialist.md",
    "agents/core/database-architect.md",
    "agents/core/agent-builder.md",
    "agents/core/pipeline-orchestrator.md",
    "agents/core/repo-knowledge-distiller.md",
    # sdlc-team-ai
    "agents/ai-development/ai-solution-architect.md",
    "agents/ai-development/prompt-engineer.md",
    "agents/ai-development/mcp-server-architect.md",
    "agents/ai-builders/rag-system-designer.md",
    "agents/ai-builders/context-engineer.md",
    "agents/ai-builders/orchestration-architect.md",
    "agents/ai-builders/ai-devops-engineer.md",
    "agents/ai-builders/ai-team-transformer.md",
    "agents/ai-development/a2a-architect.md",
    "agents/ai-development/agent-developer.md",
    "agents/ai-development/langchain-architect.md",
    "agents/ai-development/mcp-quality-assurance.md",
    "agents/ai-development/mcp-test-agent.md",
    "agents/testing/ai-test-engineer.md",
    # sdlc-team-fullstack
    "agents/core/frontend-architect.md",
    "agents/core/backend-architect.md",
    "agents/core/api-architect.md",
    "agents/core/devops-specialist.md",
    "agents/core/ux-ui-architect.md",
    "agents/core/mobile-architect.md",
    "agents/core/frontend-security-specialist.md",
    "agents/core/data-architect.md",
    "agents/testing/integration-orchestrator.md",
    "agents/core/github-integration-specialist.md",
    # sdlc-team-cloud
    "agents/core/cloud-architect.md",
    "agents/core/container-platform-specialist.md",
    "agents/core/sre-specialist.md",
    # sdlc-team-security
    "agents/core/security-architect.md",
    "agents/core/compliance-auditor.md",
    "agents/core/compliance-report-generator.md",
    "agents/core/enforcement-strategy-advisor.md",
    "agents/core/data-privacy-officer.md",
    # sdlc-team-pm
    "agents/project-management/agile-coach.md",
    "agents/project-management/delivery-manager.md",
    "agents/project-management/project-plan-tracker.md",
    "agents/project-management/team-progress-tracker.md",
    "agents/sdlc/retrospective-miner.md",
    # sdlc-team-docs
    "agents/documentation/technical-writer.md",
    "agents/documentation/documentation-architect.md",
    # sdlc-lang-python
    "agents/sdlc/language-python-expert.md",
    # sdlc-lang-javascript
    "agents/sdlc/language-javascript-expert.md",
]

DEFAULT_MODEL = "sonnet"
DEFAULT_TOOLS = "Read, Glob, Grep, Bash"
MAX_DESC_LEN = 250
KEEP_FIELDS = {"name", "description", "model", "tools"}
FIELD_ORDER = ["name", "description", "model", "tools"]


def split_frontmatter(text: str) -> tuple[str | None, str]:
    """Split file text into (frontmatter_block, body).

    Returns (None, full_text) if no valid frontmatter found.
    frontmatter_block is the raw text between the --- delimiters (exclusive).
    body is everything after the closing ---.
    """
    if not text.startswith("---"):
        return None, text

    # Find the closing ---
    # It must be on its own line
    rest = text[3:]
    # Allow optional trailing whitespace on the opening ---
    if rest and rest[0] not in ("\n", "\r"):
        # First line is not a bare ---
        return None, text

    # Strip the opening newline
    if rest.startswith("\n"):
        rest = rest[1:]
    elif rest.startswith("\r\n"):
        rest = rest[2:]

    # Find closing ---
    close_pattern = re.compile(r"^---[ \t]*$", re.MULTILINE)
    m = close_pattern.search(rest)
    if not m:
        return None, text

    frontmatter_raw = rest[: m.start()]
    body = rest[m.end():]
    # body starts just after the closing ---, keep leading newline if present
    return frontmatter_raw, body


def parse_frontmatter_fields(raw: str) -> dict[str, str]:
    """Parse frontmatter raw text into a flat dict of field -> raw value.

    Handles:
    - Simple scalar fields: key: value
    - Quoted values (single or double quotes, possibly multi-line folded)
    - Block scalars (| or >)
    - Multi-line (indented continuation) values
    - Sequence fields (examples, etc.) — captured as a single block

    Returns field values as raw strings (not parsed as YAML types).
    We only care about: name, description, model, tools.
    Everything else is ignored (examples, color, maturity, etc.).
    """
    fields: dict[str, str] = {}

    lines = raw.split("\n")
    i = 0
    n = len(lines)

    while i < n:
        line = lines[i]
        # Match a top-level key: anything that starts at col 0 with no indent
        key_match = re.match(r"^([A-Za-z_][A-Za-z0-9_-]*):\s*(.*)", line)
        if not key_match:
            i += 1
            continue

        key = key_match.group(1)
        value_rest = key_match.group(2)

        # Collect continuation lines (indented or blank)
        i += 1
        continuation: list[str] = [value_rest]
        while i < n:
            cl = lines[i]
            # Continuation: line is indented (starts with space/tab) or blank
            if cl == "" or cl[0] in (" ", "\t"):
                continuation.append(cl)
                i += 1
            else:
                break

        # Join and clean up
        full_value = "\n".join(continuation).strip()
        fields[key] = full_value

    return fields


def condense_description(raw_value: str) -> str:
    """Condense a potentially multi-line/quoted description to a single line.

    - Strip surrounding quotes (single or double)
    - Collapse internal whitespace/newlines to single spaces
    - Truncate to MAX_DESC_LEN characters
    """
    value = raw_value.strip()

    # Strip surrounding double-quotes (including escaped internals later)
    if value.startswith('"') and value.endswith('"') and len(value) >= 2:
        value = value[1:-1]
        # Unescape doubled single-quotes inside double-quoted YAML is not needed
        # but handle escaped double quotes
        value = value.replace('\\"', '"')
    elif value.startswith("'") and value.endswith("'") and len(value) >= 2:
        value = value[1:-1]
        # In YAML single-quoted scalars, '' represents a literal '
        value = value.replace("''", "'")

    # Collapse any internal newlines and excess whitespace
    value = re.sub(r"\s+", " ", value).strip()

    # Truncate
    if len(value) > MAX_DESC_LEN:
        value = value[: MAX_DESC_LEN - 3].rstrip() + "..."

    return value


def normalize_tools(raw_value: str) -> str:
    """Normalize tools field to comma-separated string on one line."""
    value = raw_value.strip()
    # Could be a YAML list or a comma-separated string
    if value.startswith("-") or "\n-" in value:
        # YAML block sequence
        items = re.findall(r"-\s*(.+)", value)
        return ", ".join(i.strip() for i in items if i.strip())
    # Already a scalar — just clean whitespace
    return re.sub(r"\s+", " ", value).strip()


def build_frontmatter(fields: dict[str, str]) -> str:
    """Build normalized frontmatter string from extracted fields."""
    lines = ["---"]
    for field in FIELD_ORDER:
        value = fields.get(field, "")
        if field == "description":
            # Always quote descriptions to be safe with colons, etc.
            # Use double-quote wrapping, escaping any internal double quotes
            escaped = value.replace('"', '\\"')
            lines.append(f'description: "{escaped}"')
        else:
            lines.append(f"{field}: {value}")
    lines.append("---")
    return "\n".join(lines)


def normalize_file(
    file_path: Path, dry_run: bool = False
) -> tuple[bool, list[str]]:
    """Normalize a single agent file.

    Returns (changed: bool, changes: list[str]).
    """
    text = file_path.read_text(encoding="utf-8")
    raw_fm, body = split_frontmatter(text)

    changes: list[str] = []

    if raw_fm is None:
        changes.append("NO FRONTMATTER FOUND — skipping")
        return False, changes

    fields = parse_frontmatter_fields(raw_fm)

    # Track what changes are made
    # 1. Strip non-standard fields
    stripped = [k for k in fields if k not in KEEP_FIELDS]
    if stripped:
        changes.append(f"strip fields: {', '.join(sorted(stripped))}")

    # 2. Condense description
    raw_desc = fields.get("description", "")
    condensed_desc = condense_description(raw_desc)
    if condensed_desc != raw_desc.strip():
        changes.append("condense description")

    # 3. Add model if missing
    if "model" not in fields:
        fields["model"] = DEFAULT_MODEL
        changes.append(f"add model: {DEFAULT_MODEL}")

    # 4. Add tools if missing
    if "tools" not in fields:
        fields["tools"] = DEFAULT_TOOLS
        changes.append(f"add tools: {DEFAULT_TOOLS}")
    else:
        # Normalize existing tools value
        normalized_tools = normalize_tools(fields["tools"])
        if normalized_tools != fields["tools"]:
            changes.append(f"normalize tools: {fields['tools']!r} -> {normalized_tools!r}")
        fields["tools"] = normalized_tools

    # Build the normalized fields dict (only kept fields)
    normalized: dict[str, str] = {}
    for field in FIELD_ORDER:
        if field == "description":
            normalized[field] = condensed_desc
        elif field in fields:
            normalized[field] = fields[field]

    new_fm = build_frontmatter(normalized)

    # Reconstruct full file
    # body already starts after the closing ---
    # Ensure body starts with a newline if it doesn't
    if body and not body.startswith("\n"):
        body = "\n" + body

    new_text = new_fm + body

    # Check if anything actually changed
    if new_text == text:
        return False, []

    if not changes:
        changes.append("whitespace/formatting normalized")

    if not dry_run:
        file_path.write_text(new_text, encoding="utf-8")

    return True, changes


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Normalize agent YAML frontmatter to Claude Code plugin schema."
    )
    parser.add_argument(
        "--all",
        action="store_true",
        dest="all_files",
        help="Process all 55 mapped agent files",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without writing files",
    )
    parser.add_argument(
        "files",
        nargs="*",
        help="Specific agent files to process (relative or absolute paths)",
    )
    args = parser.parse_args()

    if not args.all_files and not args.files:
        parser.print_help()
        return 1

    # Determine repo root (directory containing this script's parent)
    script_path = Path(__file__).resolve()
    # tools/automation/normalize-agent-frontmatter.py -> repo root is 2 levels up
    repo_root = script_path.parent.parent.parent

    if args.all_files:
        targets = [repo_root / p for p in AGENT_FILES]
    else:
        targets = [Path(f).resolve() for f in args.files]

    mode = "DRY RUN" if args.dry_run else "UPDATING"
    print(f"\n{'='*60}")
    print(f"Agent Frontmatter Normalizer — {mode}")
    print(f"Repo root: {repo_root}")
    print(f"Files to process: {len(targets)}")
    print(f"{'='*60}\n")

    total_changed = 0
    total_skipped = 0
    total_missing = 0

    for file_path in targets:
        rel = file_path.relative_to(repo_root) if file_path.is_relative_to(repo_root) else file_path
        if not file_path.exists():
            print(f"  MISSING  {rel}")
            total_missing += 1
            continue

        changed, changes_list = normalize_file(file_path, dry_run=args.dry_run)

        if changed:
            total_changed += 1
            prefix = "WOULD CHANGE" if args.dry_run else "CHANGED"
            print(f"  {prefix}  {rel}")
            for c in changes_list:
                print(f"             - {c}")
        else:
            total_skipped += 1
            print(f"  OK       {rel}")

    print(f"\n{'='*60}")
    print(f"Summary:")
    print(f"  {'Would change' if args.dry_run else 'Changed'}: {total_changed}")
    print(f"  Already OK:  {total_skipped}")
    if total_missing:
        print(f"  Missing:     {total_missing}")
    print(f"{'='*60}\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
