#!/usr/bin/env python3
"""
Official Claude Code Sub-Agent Format Validator

Validates AI agent files against the official Claude Code sub-agent specification
(https://code.claude.com/docs/en/sub-agents).

Supports two validation modes:
  --mode official  : Validates only official Claude Code frontmatter fields
  --mode project   : Validates official fields + project extension fields (default)

Usage:
  python validate-agent-official.py agents/core/sdlc-enforcer.md
  python validate-agent-official.py agents/ --audit
  python validate-agent-official.py agents/ --audit --mode official
  python validate-agent-official.py agents/core/sdlc-enforcer.md --fix
  python validate-agent-official.py agents/ --audit --json
"""

import re
import sys
import yaml
import json
import click
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field


# === Official Claude Code Sub-Agent Specification ===

OFFICIAL_REQUIRED_FIELDS = ["name", "description"]

OFFICIAL_OPTIONAL_FIELDS = [
    "tools",
    "disallowedTools",
    "model",
    "permissionMode",
    "maxTurns",
    "skills",
    "mcpServers",
    "hooks",
    "memory",
]

OFFICIAL_VALID_MODELS = ["sonnet", "opus", "haiku", "inherit"]

OFFICIAL_VALID_TOOLS = [
    "Read",
    "Write",
    "Edit",
    "Bash",
    "Glob",
    "Grep",
    "Task",
    "WebFetch",
    "WebSearch",
    "NotebookEdit",
]

OFFICIAL_VALID_PERMISSION_MODES = [
    "default",
    "acceptEdits",
    "delegate",
    "dontAsk",
    "bypassPermissions",
    "plan",
]

OFFICIAL_VALID_MEMORY_SCOPES = ["user", "project", "local"]

# === Project Extension Fields (AI-First SDLC specific) ===

PROJECT_REQUIRED_FIELDS = ["examples", "color"]

PROJECT_OPTIONAL_FIELDS = ["version", "category", "priority", "maturity", "tags"]

PROJECT_VALID_COLORS = ["blue", "green", "purple", "red", "cyan", "yellow", "orange"]

PROJECT_VALID_MATURITY = ["production", "stable", "beta", "stub", "deprecated"]

# All known fields (official + project)
ALL_KNOWN_FIELDS = (
    OFFICIAL_REQUIRED_FIELDS
    + OFFICIAL_OPTIONAL_FIELDS
    + PROJECT_REQUIRED_FIELDS
    + PROJECT_OPTIONAL_FIELDS
)

NAME_PATTERN = re.compile(r"^[a-z0-9-]{1,50}$")


@dataclass
class Issue:
    field: str
    message: str
    severity: str = "error"  # error, warning, info

    def __str__(self):
        icon = {"error": "x", "warning": "!", "info": "i"}.get(self.severity, "?")
        return f"[{icon}] {self.field}: {self.message}"


@dataclass
class AgentReport:
    file: str
    name: Optional[str] = None
    valid_official: bool = False
    valid_project: bool = False
    issues: List[Issue] = field(default_factory=list)
    fields_present: List[str] = field(default_factory=list)
    tools_format: Optional[str] = None  # "comma-sep", "yaml-list", "json-array", None

    def to_dict(self):
        return {
            "file": self.file,
            "name": self.name,
            "valid_official": self.valid_official,
            "valid_project": self.valid_project,
            "issues": [
                {"field": i.field, "message": i.message, "severity": i.severity}
                for i in self.issues
            ],
            "fields_present": self.fields_present,
            "tools_format": self.tools_format,
        }


def extract_frontmatter(content: str) -> Tuple[Optional[Dict], str, str]:
    """Extract YAML frontmatter and body. Returns (frontmatter_dict, body, raw_yaml)."""
    pattern = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)$", re.DOTALL)
    match = pattern.match(content)
    if not match:
        return None, content, ""
    raw_yaml = match.group(1)
    try:
        frontmatter = yaml.safe_load(raw_yaml)
        body = match.group(2)
        return frontmatter, body, raw_yaml
    except yaml.YAMLError:
        return None, "", raw_yaml


def parse_tools_value(tools_val: Any) -> Tuple[List[str], str]:
    """Parse tools value in any format. Returns (tool_list, format_type)."""
    if isinstance(tools_val, str):
        tools = [t.strip() for t in tools_val.split(",") if t.strip()]
        return tools, "comma-sep"
    elif isinstance(tools_val, list):
        if all(isinstance(t, str) for t in tools_val):
            return tools_val, "yaml-list"
        return [str(t) for t in tools_val], "yaml-list"
    return [], "unknown"


def validate_official(frontmatter: Dict, body: str) -> List[Issue]:
    """Validate against official Claude Code sub-agent spec only."""
    issues = []

    # Required: name
    if "name" not in frontmatter:
        issues.append(Issue("name", "Required field missing"))
    else:
        name = frontmatter["name"]
        if not isinstance(name, str):
            issues.append(Issue("name", "Must be a string"))
        elif not NAME_PATTERN.match(name):
            issues.append(
                Issue("name", "Must be lowercase alphanumeric with hyphens, 1-50 chars")
            )

    # Required: description
    if "description" not in frontmatter:
        issues.append(Issue("description", "Required field missing"))
    else:
        desc = frontmatter["description"]
        if not isinstance(desc, str):
            issues.append(Issue("description", "Must be a string"))
        elif len(desc) < 10:
            issues.append(
                Issue("description", "Very short description may hurt routing accuracy", "warning")
            )

    # Optional: tools
    if "tools" in frontmatter:
        tools_val = frontmatter["tools"]
        tools_list, fmt = parse_tools_value(tools_val)
        if fmt == "yaml-list":
            issues.append(
                Issue(
                    "tools",
                    "Should be comma-separated string per official spec (e.g., 'tools: Read, Glob, Grep, Bash')",
                    "warning",
                )
            )
        elif fmt == "unknown":
            issues.append(Issue("tools", "Invalid format — must be comma-separated string"))
        for tool in tools_list:
            # Check for Task(agent-name) pattern
            if tool.startswith("Task(") and tool.endswith(")"):
                continue  # Valid Task restriction syntax
            if tool not in OFFICIAL_VALID_TOOLS:
                issues.append(
                    Issue("tools", f"Unknown tool '{tool}'. Valid: {', '.join(OFFICIAL_VALID_TOOLS)}", "warning")
                )

    # Optional: disallowedTools
    if "disallowedTools" in frontmatter:
        dt = frontmatter["disallowedTools"]
        if isinstance(dt, str):
            for tool in [t.strip() for t in dt.split(",") if t.strip()]:
                if tool not in OFFICIAL_VALID_TOOLS:
                    issues.append(Issue("disallowedTools", f"Unknown tool '{tool}'", "warning"))
        elif isinstance(dt, list):
            issues.append(
                Issue("disallowedTools", "Should be comma-separated string per official spec", "warning")
            )

    # Optional: model
    if "model" in frontmatter:
        model = frontmatter["model"]
        if not isinstance(model, str):
            issues.append(Issue("model", "Must be a string"))
        elif model not in OFFICIAL_VALID_MODELS:
            issues.append(
                Issue("model", f"Must be one of: {', '.join(OFFICIAL_VALID_MODELS)}")
            )

    # Optional: permissionMode
    if "permissionMode" in frontmatter:
        pm = frontmatter["permissionMode"]
        if pm not in OFFICIAL_VALID_PERMISSION_MODES:
            issues.append(
                Issue(
                    "permissionMode",
                    f"Must be one of: {', '.join(OFFICIAL_VALID_PERMISSION_MODES)}",
                )
            )

    # Optional: maxTurns
    if "maxTurns" in frontmatter:
        mt = frontmatter["maxTurns"]
        if not isinstance(mt, int) or mt < 1:
            issues.append(Issue("maxTurns", "Must be a positive integer"))

    # Optional: skills
    if "skills" in frontmatter:
        sk = frontmatter["skills"]
        if not isinstance(sk, list):
            issues.append(Issue("skills", "Must be a list of skill names"))

    # Optional: mcpServers
    if "mcpServers" in frontmatter:
        mcp = frontmatter["mcpServers"]
        if not isinstance(mcp, (list, dict)):
            issues.append(Issue("mcpServers", "Must be a list or mapping of MCP server configs"))

    # Optional: hooks
    if "hooks" in frontmatter:
        hooks = frontmatter["hooks"]
        if not isinstance(hooks, dict):
            issues.append(Issue("hooks", "Must be a mapping of hook event types"))

    # Optional: memory
    if "memory" in frontmatter:
        mem = frontmatter["memory"]
        if mem not in OFFICIAL_VALID_MEMORY_SCOPES:
            issues.append(
                Issue("memory", f"Must be one of: {', '.join(OFFICIAL_VALID_MEMORY_SCOPES)}")
            )

    # Body check
    if not body.strip():
        issues.append(Issue("content", "System prompt (body) is empty"))
    elif len(body.strip()) < 50:
        issues.append(Issue("content", "System prompt very short (< 50 chars)", "warning"))

    return issues


def validate_project(frontmatter: Dict, body: str) -> List[Issue]:
    """Validate project extension fields (in addition to official)."""
    issues = []

    # Project-required: examples
    if "examples" not in frontmatter:
        issues.append(Issue("examples", "Required project field missing"))
    else:
        examples = frontmatter["examples"]
        if not isinstance(examples, list):
            issues.append(Issue("examples", "Must be a list"))
        elif len(examples) < 1:
            issues.append(Issue("examples", "At least 1 example required"))
        elif len(examples) > 5:
            issues.append(Issue("examples", "Maximum 5 examples recommended", "warning"))
        else:
            for i, ex in enumerate(examples):
                if isinstance(ex, dict):
                    for f in ["context", "user", "assistant"]:
                        if f not in ex:
                            issues.append(
                                Issue(f"examples[{i}].{f}", "Required field missing in example")
                            )

    # Project-required: color
    if "color" not in frontmatter:
        issues.append(Issue("color", "Required project field missing"))
    elif frontmatter["color"] not in PROJECT_VALID_COLORS:
        issues.append(
            Issue("color", f"Must be one of: {', '.join(PROJECT_VALID_COLORS)}")
        )

    # Project-optional: maturity
    if "maturity" in frontmatter:
        if frontmatter["maturity"] not in PROJECT_VALID_MATURITY:
            issues.append(
                Issue("maturity", f"Must be one of: {', '.join(PROJECT_VALID_MATURITY)}")
            )

    # Check for unknown fields
    for key in frontmatter:
        if key not in ALL_KNOWN_FIELDS:
            issues.append(Issue(key, f"Unknown field '{key}'", "info"))

    return issues


def validate_agent_file(
    file_path: Path, mode: str = "project"
) -> AgentReport:
    """Validate a single agent file. Mode: 'official' or 'project'."""
    report = AgentReport(file=str(file_path))

    if not file_path.exists():
        report.issues.append(Issue("file", f"File not found: {file_path}"))
        return report

    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        report.issues.append(Issue("file", f"Error reading file: {e}"))
        return report

    frontmatter, body, raw_yaml = extract_frontmatter(content)

    if frontmatter is None:
        report.issues.append(Issue("frontmatter", "No valid YAML frontmatter found"))
        return report

    if not isinstance(frontmatter, dict):
        report.issues.append(Issue("frontmatter", "Frontmatter is not a YAML mapping"))
        return report

    report.name = frontmatter.get("name")
    report.fields_present = list(frontmatter.keys())

    # Detect tools format
    if "tools" in frontmatter:
        _, fmt = parse_tools_value(frontmatter["tools"])
        report.tools_format = fmt

    # Official validation
    official_issues = validate_official(frontmatter, body)
    report.issues.extend(official_issues)
    official_errors = [i for i in official_issues if i.severity == "error"]
    report.valid_official = len(official_errors) == 0

    # Project validation (on top of official)
    if mode == "project":
        project_issues = validate_project(frontmatter, body)
        report.issues.extend(project_issues)
        all_errors = [i for i in report.issues if i.severity == "error"]
        report.valid_project = len(all_errors) == 0
    else:
        report.valid_project = report.valid_official

    return report


def fix_tools_format(file_path: Path) -> bool:
    """Convert tools field from YAML list or JSON array to comma-separated string."""
    content = file_path.read_text(encoding="utf-8")
    fm_match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
    if not fm_match:
        return False

    raw_yaml = fm_match.group(1)
    try:
        frontmatter = yaml.safe_load(raw_yaml)
    except yaml.YAMLError:
        return False

    if "tools" not in frontmatter:
        return False

    tools_val = frontmatter["tools"]
    tools_list, fmt = parse_tools_value(tools_val)

    if fmt == "comma-sep":
        return False  # Already correct format

    # Build the comma-separated string
    tools_str = ", ".join(tools_list)

    # Replace the tools field in raw YAML
    # Handle YAML list format
    if fmt == "yaml-list":
        # Match "tools:\n  - Tool1\n  - Tool2\n..." pattern
        # The list items may or may not end with a final newline
        list_pattern = re.compile(r"^(tools:\s*\n(?:\s+-\s+\S+\n)*\s+-\s+\S+)\n?", re.MULTILINE)
        match = list_pattern.search(raw_yaml)
        if match:
            replacement = f"tools: {tools_str}"
            new_yaml = raw_yaml[:match.start()] + replacement + "\n" + raw_yaml[match.end():]
            new_content = content[:fm_match.start(1)] + new_yaml + content[fm_match.end(1):]
            file_path.write_text(new_content, encoding="utf-8")
            return True

    # Handle JSON array format: tools: [Read, Grep, Glob]
    json_pattern = re.compile(r"^tools:\s*\[.*?\]", re.MULTILINE)
    match = json_pattern.search(raw_yaml)
    if match:
        new_yaml = raw_yaml[:match.start()] + f"tools: {tools_str}" + raw_yaml[match.end():]
        new_content = content[:fm_match.start(1)] + new_yaml + content[fm_match.end(1):]
        file_path.write_text(new_content, encoding="utf-8")
        return True

    return False


def audit_directory(agents_path: Path, mode: str = "project") -> List[AgentReport]:
    """Audit all agent files in a directory."""
    reports = []
    agent_files = sorted(agents_path.rglob("*.md"))

    for agent_file in agent_files:
        # Skip non-agent files (no frontmatter with name field)
        content = agent_file.read_text(encoding="utf-8")
        fm_match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
        if not fm_match:
            continue
        try:
            fm = yaml.safe_load(fm_match.group(1))
        except yaml.YAMLError:
            continue
        if not isinstance(fm, dict) or "name" not in fm:
            continue

        report = validate_agent_file(agent_file, mode)
        reports.append(report)

    return reports


def print_audit_report(reports: List[AgentReport], mode: str):
    """Print a human-readable audit report."""
    total = len(reports)
    if mode == "official":
        passing = sum(1 for r in reports if r.valid_official)
    else:
        passing = sum(1 for r in reports if r.valid_project)
    failing = total - passing

    click.echo(f"\n{'=' * 60}")
    click.echo(f"Agent Format Audit Report — Mode: {mode}")
    click.echo(f"{'=' * 60}\n")
    click.echo(f"Total agents:  {total}")
    click.echo(f"Passing:       {passing}")
    click.echo(f"Failing:       {failing}")

    # Tools format breakdown
    tools_formats = {"comma-sep": 0, "yaml-list": 0, "json-array": 0, "none": 0}
    for r in reports:
        if r.tools_format:
            tools_formats[r.tools_format] = tools_formats.get(r.tools_format, 0) + 1
        else:
            tools_formats["none"] += 1

    click.echo("\nTools format distribution:")
    for fmt, count in tools_formats.items():
        marker = " (official)" if fmt == "comma-sep" else ""
        click.echo(f"  {fmt}: {count}{marker}")

    # Field coverage
    field_counts: Dict[str, int] = {}
    for r in reports:
        for f in r.fields_present:
            field_counts[f] = field_counts.get(f, 0) + 1

    click.echo(f"\nField coverage ({total} agents):")
    all_fields = OFFICIAL_REQUIRED_FIELDS + OFFICIAL_OPTIONAL_FIELDS + PROJECT_REQUIRED_FIELDS + PROJECT_OPTIONAL_FIELDS
    for f in all_fields:
        count = field_counts.get(f, 0)
        pct = (count / total * 100) if total > 0 else 0
        category = (
            "official-req"
            if f in OFFICIAL_REQUIRED_FIELDS
            else "official-opt"
            if f in OFFICIAL_OPTIONAL_FIELDS
            else "project-req"
            if f in PROJECT_REQUIRED_FIELDS
            else "project-opt"
        )
        click.echo(f"  {f:20s} {count:3d}/{total} ({pct:5.1f}%) [{category}]")

    # Failing agents
    if failing > 0:
        click.echo("\nFailing agents:")
        for r in reports:
            is_valid = r.valid_official if mode == "official" else r.valid_project
            if not is_valid:
                errors = [i for i in r.issues if i.severity == "error"]
                click.echo(f"\n  {r.file}:")
                for issue in errors:
                    click.echo(f"    {issue}")

    # Warnings summary
    all_warnings = []
    for r in reports:
        for i in r.issues:
            if i.severity == "warning":
                all_warnings.append((r.file, i))

    if all_warnings:
        click.echo(f"\nWarnings ({len(all_warnings)} total):")
        # Group by issue message
        warning_groups: Dict[str, int] = {}
        for _, issue in all_warnings:
            key = f"{issue.field}: {issue.message}"
            warning_groups[key] = warning_groups.get(key, 0) + 1
        for msg, count in sorted(warning_groups.items(), key=lambda x: -x[1]):
            click.echo(f"  [{count:2d}x] {msg}")

    click.echo(f"\n{'=' * 60}")
    if failing == 0:
        click.echo(f"All {total} agents PASS {mode}-mode validation")
    else:
        click.echo(f"{failing}/{total} agents FAIL {mode}-mode validation")
    click.echo(f"{'=' * 60}\n")


@click.command()
@click.argument("agent_path", type=click.Path(exists=True))
@click.option(
    "--mode",
    type=click.Choice(["official", "project"]),
    default="project",
    help="Validation mode: official (Claude Code spec only) or project (includes extensions)",
)
@click.option("--audit", is_flag=True, help="Audit all agents in directory")
@click.option("--fix", is_flag=True, help="Auto-fix tools format to comma-separated string")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
@click.option("--quiet", "-q", is_flag=True, help="Only show errors")
def main(agent_path: str, mode: str, audit: bool, fix: bool, output_json: bool, quiet: bool):
    """
    Validate agent files against the official Claude Code sub-agent specification.

    AGENT_PATH can be a single file or a directory (with --audit).

    Examples:
        python validate-agent-official.py agents/core/sdlc-enforcer.md
        python validate-agent-official.py agents/ --audit
        python validate-agent-official.py agents/ --audit --mode official
        python validate-agent-official.py agents/ --audit --fix
    """
    path = Path(agent_path)

    if fix and path.is_dir():
        # Fix all agents in directory
        agent_files = sorted(path.rglob("*.md"))
        fixed = 0
        for f in agent_files:
            if fix_tools_format(f):
                fixed += 1
                if not quiet:
                    click.echo(f"Fixed: {f}")
        click.echo(f"\nFixed tools format in {fixed} files")
        sys.exit(0)

    if fix and path.is_file():
        if fix_tools_format(path):
            click.echo(f"Fixed: {path}")
        else:
            click.echo(f"No fix needed: {path}")
        sys.exit(0)

    if audit:
        reports = audit_directory(path, mode)
        if output_json:
            result = {
                "mode": mode,
                "total": len(reports),
                "passing": sum(
                    1
                    for r in reports
                    if (r.valid_official if mode == "official" else r.valid_project)
                ),
                "agents": [r.to_dict() for r in reports],
            }
            click.echo(json.dumps(result, indent=2))
        else:
            print_audit_report(reports, mode)

        failing = sum(
            1
            for r in reports
            if not (r.valid_official if mode == "official" else r.valid_project)
        )
        sys.exit(1 if failing > 0 else 0)

    # Single file validation
    report = validate_agent_file(path, mode)

    if output_json:
        click.echo(json.dumps(report.to_dict(), indent=2))
    else:
        is_valid = report.valid_official if mode == "official" else report.valid_project

        if report.issues:
            click.echo(f"\nValidation Report for {path.name} (mode: {mode})")
            click.echo("=" * 50)

            for severity in ["error", "warning", "info"]:
                items = [i for i in report.issues if i.severity == severity]
                if items:
                    label = severity.upper()
                    click.echo(f"\n{label}:")
                    for item in items:
                        click.echo(f"  {item}")

            click.echo("\n" + "=" * 50)
            if is_valid:
                click.echo("PASS (with warnings)")
            else:
                click.echo("FAIL")
        elif not quiet:
            click.echo(f"{path.name} is valid! (mode: {mode})")

    is_valid = report.valid_official if mode == "official" else report.valid_project
    sys.exit(0 if is_valid else 1)


if __name__ == "__main__":
    main()
