#!/usr/bin/env python3
"""
Agent Format Validator

Validates AI agent files against the AGENT-FORMAT-SPEC.md specification.
Ensures all agents follow the required YAML frontmatter and content structure.
"""

import re
import sys
import yaml
import click
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass


@dataclass
class ValidationError:
    """Represents a validation error with context"""

    field: str
    message: str
    severity: str = "error"  # error, warning, info

    def __str__(self):
        icon = (
            "❌"
            if self.severity == "error"
            else "⚠️"
            if self.severity == "warning"
            else "ℹ️"
        )
        return f"{icon} {self.field}: {self.message}"


class AgentValidator:
    """Validates agent files against the format specification"""

    # Required fields in YAML frontmatter
    REQUIRED_FIELDS = ["name", "description", "examples", "color"]

    # Valid color values
    VALID_COLORS = ["blue", "green", "purple", "red", "cyan", "yellow", "orange"]

    # Valid maturity values
    VALID_MATURITY = ["production", "stable", "beta", "stub", "deprecated"]

    # Field constraints
    NAME_PATTERN = re.compile(r"^[a-z0-9-]{1,50}$")
    MAX_DESCRIPTION_LENGTH = 500  # Increased to accommodate existing agents
    MIN_EXAMPLES = 1
    MAX_EXAMPLES = 5

    # Content section patterns
    CONTENT_SECTIONS = [
        r"You are .+",  # Role statement
        r"Your core competencies include:",  # Competencies list
    ]

    def __init__(self, strict: bool = True):
        """
        Initialize validator

        Args:
            strict: If True, warnings are treated as errors
        """
        self.strict = strict
        self.errors: List[ValidationError] = []

    def validate_file(self, file_path: Path) -> Tuple[bool, List[ValidationError]]:
        """
        Validate an agent file

        Args:
            file_path: Path to the agent file

        Returns:
            Tuple of (is_valid, errors)
        """
        self.errors = []

        if not file_path.exists():
            self.errors.append(ValidationError("file", f"File not found: {file_path}"))
            return False, self.errors

        try:
            content = file_path.read_text()
            frontmatter, body = self._extract_frontmatter(content)

            if frontmatter is None:
                self.errors.append(
                    ValidationError("frontmatter", "No YAML frontmatter found")
                )
                return False, self.errors

            # Validate frontmatter
            self._validate_frontmatter(frontmatter)

            # Validate content
            self._validate_content(body)

        except Exception as e:
            self.errors.append(ValidationError("file", f"Error reading file: {e}"))
            return False, self.errors

        # Check if valid based on errors and strict mode
        has_errors = any(e.severity == "error" for e in self.errors)
        has_warnings = any(e.severity == "warning" for e in self.errors)

        is_valid = not has_errors and (not self.strict or not has_warnings)
        return is_valid, self.errors

    def _extract_frontmatter(self, content: str) -> Tuple[Optional[Dict], str]:
        """Extract YAML frontmatter and body from content"""
        pattern = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)$", re.DOTALL)
        match = pattern.match(content)

        if not match:
            return None, content

        try:
            frontmatter = yaml.safe_load(match.group(1))
            body = match.group(2)
            return frontmatter, body
        except yaml.YAMLError as e:
            self.errors.append(ValidationError("frontmatter", f"Invalid YAML: {e}"))
            return None, ""

    def _validate_frontmatter(self, frontmatter: Dict[str, Any]):
        """Validate YAML frontmatter fields"""

        # Check required fields
        for field in self.REQUIRED_FIELDS:
            if field not in frontmatter:
                self.errors.append(ValidationError(field, "Required field missing"))

        # Validate name
        if "name" in frontmatter:
            name = frontmatter["name"]
            if not isinstance(name, str):
                self.errors.append(ValidationError("name", "Must be a string"))
            elif not self.NAME_PATTERN.match(name):
                self.errors.append(
                    ValidationError(
                        "name",
                        "Must be lowercase alphanumeric with hyphens, 1-50 chars",
                    )
                )

        # Validate description
        if "description" in frontmatter:
            desc = frontmatter["description"]
            if not isinstance(desc, str):
                self.errors.append(ValidationError("description", "Must be a string"))
            elif len(desc) > self.MAX_DESCRIPTION_LENGTH:
                self.errors.append(
                    ValidationError(
                        "description",
                        f"Must be {self.MAX_DESCRIPTION_LENGTH} characters or less (currently {len(desc)})",
                    )
                )
            elif len(desc) < 10:
                self.errors.append(
                    ValidationError(
                        "description",
                        "Description too short (minimum 10 characters)",
                        severity="warning",
                    )
                )

        # Validate color
        if "color" in frontmatter:
            color = frontmatter["color"]
            if color not in self.VALID_COLORS:
                self.errors.append(
                    ValidationError(
                        "color", f"Must be one of: {', '.join(self.VALID_COLORS)}"
                    )
                )

        # Validate maturity (optional field)
        if "maturity" in frontmatter:
            maturity = frontmatter["maturity"]
            if maturity not in self.VALID_MATURITY:
                self.errors.append(
                    ValidationError(
                        "maturity",
                        f"Must be one of: {', '.join(self.VALID_MATURITY)}",
                    )
                )

        # Validate examples
        if "examples" in frontmatter:
            examples = frontmatter["examples"]
            if not isinstance(examples, list):
                self.errors.append(ValidationError("examples", "Must be a list"))
            else:
                if len(examples) < self.MIN_EXAMPLES:
                    self.errors.append(
                        ValidationError(
                            "examples", f"At least {self.MIN_EXAMPLES} example required"
                        )
                    )
                elif len(examples) > self.MAX_EXAMPLES:
                    self.errors.append(
                        ValidationError(
                            "examples",
                            f"Maximum {self.MAX_EXAMPLES} examples allowed",
                            severity="warning",
                        )
                    )

                # Validate each example structure
                for i, example in enumerate(examples):
                    # Handle both string format (with XML-like tags) and dict format
                    if isinstance(example, str):
                        # Check if it contains the expected patterns
                        if (
                            "<example>" not in example
                            or "user:" not in example
                            or "assistant:" not in example
                        ):
                            self.errors.append(
                                ValidationError(
                                    f"examples[{i}]",
                                    "String example must contain <example>, user:, and assistant: sections",
                                    severity="warning",
                                )
                            )
                    elif isinstance(example, dict):
                        # Check for required fields in dictionary format
                        required_example_fields = ["context", "user", "assistant"]
                        for field in required_example_fields:
                            if field not in example:
                                self.errors.append(
                                    ValidationError(
                                        f"examples[{i}].{field}",
                                        "Required field missing in example",
                                    )
                                )
                            elif not isinstance(example[field], str):
                                self.errors.append(
                                    ValidationError(
                                        f"examples[{i}].{field}", "Must be a string"
                                    )
                                )
                    else:
                        self.errors.append(
                            ValidationError(
                                f"examples[{i}]",
                                "Example must be either a string or dictionary",
                            )
                        )

    def _validate_content(self, body: str):
        """Validate content structure"""

        if not body.strip():
            self.errors.append(ValidationError("content", "Content section is empty"))
            return

        # Check for role statement
        if not re.search(r"^You are .+", body, re.MULTILINE):
            self.errors.append(
                ValidationError(
                    "content",
                    "Missing role statement (should start with 'You are...')",
                    severity="warning",
                )
            )

        # Check for core competencies section (case-insensitive)
        if "your core competencies include" not in body.lower():
            self.errors.append(
                ValidationError(
                    "content",
                    "Missing 'Your core competencies include:' section",
                    severity="warning",
                )
            )

        # Check minimum content length
        if len(body.strip()) < 100:
            self.errors.append(
                ValidationError(
                    "content",
                    "Content too short (minimum 100 characters)",
                    severity="warning",
                )
            )


def validate_agent_content(content: str, strict: bool = True) -> Tuple[bool, List[str]]:
    """
    Validate agent content string

    Args:
        content: Agent file content as string
        strict: If True, warnings are treated as errors

    Returns:
        Tuple of (is_valid, error_messages)
    """
    import tempfile

    # Write to temp file and validate
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write(content)
        temp_path = Path(f.name)

    try:
        validator = AgentValidator(strict=strict)
        is_valid, errors = validator.validate_file(temp_path)
        error_messages = [str(e) for e in errors]
        return is_valid, error_messages
    finally:
        temp_path.unlink()


@click.command()
@click.argument("agent_file", type=click.Path(exists=True))
@click.option("--strict/--no-strict", default=True, help="Treat warnings as errors")
@click.option(
    "--quiet", "-q", is_flag=True, help="Only show errors, not success message"
)
@click.option("--json", "output_json", is_flag=True, help="Output results as JSON")
@click.option(
    "--maturity-report",
    is_flag=True,
    help="Scan directory and report maturity distribution",
)
def main(
    agent_file: str, strict: bool, quiet: bool, output_json: bool, maturity_report: bool
):
    """
    Validate an AI agent file against the format specification.

    When --maturity-report is used, AGENT_FILE should be a directory to scan.

    Examples:\n
        python validate-agent-format.py agents/core/sdlc-enforcer.md\n
        python validate-agent-format.py my-agent.md --no-strict\n
        python validate-agent-format.py agents/ --maturity-report
    """
    file_path = Path(agent_file)

    if maturity_report:
        _run_maturity_report(file_path, output_json)
        return

    validator = AgentValidator(strict=strict)
    is_valid, errors = validator.validate_file(file_path)

    if output_json:
        import json

        result = {
            "file": str(file_path),
            "valid": is_valid,
            "errors": [
                {"field": e.field, "message": e.message, "severity": e.severity}
                for e in errors
            ],
        }
        print(json.dumps(result, indent=2))
        sys.exit(0 if is_valid else 1)

    # Console output
    if errors:
        print(f"\n🔍 Validation Report for {file_path.name}")
        print("=" * 50)

        errors_list = [e for e in errors if e.severity == "error"]
        warnings_list = [e for e in errors if e.severity == "warning"]
        info_list = [e for e in errors if e.severity == "info"]

        if errors_list:
            print("\n❌ ERRORS:")
            for error in errors_list:
                print(f"  {error}")

        if warnings_list:
            print("\n⚠️  WARNINGS:")
            for warning in warnings_list:
                print(f"  {warning}")

        if info_list:
            print("\nℹ️  INFO:")
            for info in info_list:
                print(f"  {info}")

        print("\n" + "=" * 50)
        if is_valid:
            print("✅ Validation PASSED (with warnings)")
        else:
            print("❌ Validation FAILED")

    elif not quiet:
        print(f"✅ {file_path.name} is valid!")

    sys.exit(0 if is_valid else 1)


def _run_maturity_report(agents_path: Path, output_json: bool):
    """Generate a maturity distribution report for all agents in a directory."""
    import json as json_mod

    agent_files = sorted(agents_path.rglob("*.md"))
    tiers = {
        "production": [],
        "stable": [],
        "beta": [],
        "stub": [],
        "deprecated": [],
        "unlabeled": [],
    }

    for agent_file in agent_files:
        content = agent_file.read_text()
        fm_match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
        if not fm_match:
            continue
        try:
            frontmatter = yaml.safe_load(fm_match.group(1))
        except yaml.YAMLError:
            continue
        if not isinstance(frontmatter, dict) or "name" not in frontmatter:
            continue

        maturity = frontmatter.get("maturity", None)
        name = frontmatter["name"]
        rel_path = str(agent_file.relative_to(agents_path))

        if maturity in tiers:
            tiers[maturity].append({"name": name, "path": rel_path})
        else:
            tiers["unlabeled"].append({"name": name, "path": rel_path})

    total = sum(len(v) for v in tiers.values())

    if output_json:
        result = {
            "total": total,
            "tiers": {k: {"count": len(v), "agents": v} for k, v in tiers.items()},
        }
        click.echo(json_mod.dumps(result, indent=2))
    else:
        click.echo(f"\n{'=' * 50}")
        click.echo("Agent Maturity Report")
        click.echo(f"{'=' * 50}\n")
        click.echo(f"Total agents scanned: {total}\n")
        for tier, agents in tiers.items():
            if agents:
                icon = {
                    "production": "🟢",
                    "stable": "🔵",
                    "beta": "🟡",
                    "stub": "🔴",
                    "deprecated": "⚫",
                    "unlabeled": "⚪",
                }.get(tier, "?")
                click.echo(f"  {icon} {tier}: {len(agents)}")
                for a in agents:
                    click.echo(f"      {a['name']} ({a['path']})")
                click.echo()
        click.echo(f"{'=' * 50}")


if __name__ == "__main__":
    main()
