#!/usr/bin/env python3
"""
Agent Pipeline Validator

Validates agent creation pipeline artifacts: research prompts, reference agents,
production agents created via the pipeline, and pipeline infrastructure.
"""

import re
import sys
import json
import click
from pathlib import Path
from typing import List
from dataclasses import dataclass


@dataclass
class PipelineResult:
    """Represents a pipeline validation result"""

    check: str
    message: str
    severity: str = "error"  # error, warning, info, success

    def __str__(self):
        icons = {
            "error": "\u274c",
            "warning": "\u26a0\ufe0f",
            "info": "\u2139\ufe0f",
            "success": "\u2705",
        }
        return f"{icons.get(self.severity, '?')} {self.check}: {self.message}"


class ResearchPromptValidator:
    """Validates research prompt files"""

    REQUIRED_SECTIONS = ["Objective", "Research Areas", "Synthesis Requirements"]
    RECOMMENDED_SECTIONS = ["Context", "Agent Integration Points"]
    MIN_RESEARCH_AREAS = 3
    MAX_RESEARCH_AREAS = 15

    def validate(self, file_path: Path) -> List[PipelineResult]:
        results = []
        if not file_path.exists():
            results.append(PipelineResult("file", f"File not found: {file_path}"))
            return results

        content = file_path.read_text()

        for section in self.REQUIRED_SECTIONS:
            if re.search(rf"^#+\s+.*{re.escape(section)}", content, re.MULTILINE | re.IGNORECASE):
                results.append(PipelineResult("structure", f"Required section found: '{section}'", severity="success"))
            else:
                results.append(PipelineResult("structure", f"Missing required section: '{section}'"))

        for section in self.RECOMMENDED_SECTIONS:
            if not re.search(rf"^#+\s+.*{re.escape(section)}", content, re.MULTILINE | re.IGNORECASE):
                results.append(PipelineResult("structure", f"Recommended section missing: '{section}'", severity="warning"))

        area_count = len(re.findall(r"^###\s+\d+\.\s+", content, re.MULTILINE))
        if area_count < self.MIN_RESEARCH_AREAS:
            results.append(PipelineResult("research-areas", f"Too few research areas: {area_count} (minimum {self.MIN_RESEARCH_AREAS})"))
        elif area_count > self.MAX_RESEARCH_AREAS:
            results.append(PipelineResult("research-areas", f"Too many research areas: {area_count} (maximum {self.MAX_RESEARCH_AREAS})", severity="warning"))
        else:
            results.append(PipelineResult("research-areas", f"Research areas count: {area_count}", severity="success"))

        question_lines = [l for l in content.split("\n") if l.strip().startswith("- ") and "?" in l]
        if len(question_lines) < 5:
            results.append(PipelineResult("questions", f"Few research questions: {len(question_lines)} (recommend 15+)", severity="warning"))
        else:
            results.append(PipelineResult("questions", f"Research questions found: {len(question_lines)}", severity="success"))

        if len(content) < 500:
            results.append(PipelineResult("content", "Research prompt too short (minimum 500 characters)"))

        bracket_placeholders = len(re.findall(r"\[(?:AGENT|ROLE|DOMAIN|CUSTOMIZE)[^\]]*\]", content))
        if bracket_placeholders > 0:
            results.append(PipelineResult("placeholders", f"Found {bracket_placeholders} unfilled placeholder(s)", severity="warning"))

        return results


class ReferenceAgentValidator:
    """Validates reference agent template files"""

    def validate(self, file_path: Path) -> List[PipelineResult]:
        results = []
        if not file_path.exists():
            results.append(PipelineResult("file", f"File not found: {file_path}"))
            return results

        content = file_path.read_text()

        for tag in ["ARCHETYPE:", "BASED ON:", "USE WHEN:"]:
            if tag not in content:
                results.append(PipelineResult("header", f"Missing {tag.rstrip(':')} comment in header", severity="warning"))

        if re.search(r"^---\s*\n(.*?)\n---", content, re.MULTILINE | re.DOTALL):
            results.append(PipelineResult("frontmatter", "YAML frontmatter present", severity="success"))
        else:
            results.append(PipelineResult("frontmatter", "Missing YAML frontmatter"))

        customize_count = len(re.findall(r"\[CUSTOMIZE", content))
        if customize_count < 3:
            results.append(PipelineResult("placeholders", f"Only {customize_count} [CUSTOMIZE] placeholder(s)", severity="warning"))
        else:
            results.append(PipelineResult("placeholders", f"Found {customize_count} [CUSTOMIZE] placeholders", severity="success"))

        line_count = len(content.split("\n"))
        if line_count > 120:
            results.append(PipelineResult("size", f"Reference agent is {line_count} lines (target: 50-80)", severity="warning"))

        return results


class ProductionAgentValidator:
    """Validates finished agents created through the pipeline"""

    MIN_CONTENT_LENGTH = 500
    MIN_DOMAIN_WORDS = 50

    def validate(self, file_path: Path, require_research: bool = False) -> List[PipelineResult]:
        results = []
        if not file_path.exists():
            results.append(PipelineResult("file", f"File not found: {file_path}"))
            return results

        content = file_path.read_text()

        # Check for corresponding research prompt
        agent_name = file_path.stem  # e.g., "security-architect"
        research_prompt = file_path.parent.parent.parent / "agent_prompts" / f"research-{agent_name}.md"
        if research_prompt.exists():
            results.append(PipelineResult("research", f"Research prompt found: {research_prompt.name}", severity="success"))
        elif require_research:
            results.append(PipelineResult("research", f"No research prompt found for '{agent_name}'. Production agents MUST have a research prompt at agent_prompts/research-{agent_name}.md"))
        else:
            results.append(PipelineResult("research", f"No research prompt found for '{agent_name}'. Consider creating agent_prompts/research-{agent_name}.md for research-grounded content", severity="warning"))

        # Check for remaining template placeholders
        remaining = re.findall(r"\[CUSTOMIZE[^\]]*\]", content)
        if remaining:
            results.append(PipelineResult("placeholders", f"Found {len(remaining)} unfilled [CUSTOMIZE] placeholder(s) - agent is incomplete"))
        else:
            results.append(PipelineResult("placeholders", "No remaining template placeholders", severity="success"))

        # Check YAML frontmatter exists
        fm_match = re.search(r"^---\s*\n(.*?)\n---", content, re.MULTILINE | re.DOTALL)
        if fm_match:
            fm_content = fm_match.group(1)
            for field in ["name:", "description:", "examples:", "color:"]:
                if field in fm_content:
                    results.append(PipelineResult("frontmatter", f"Required field '{field.rstrip(':')}' present", severity="success"))
                else:
                    results.append(PipelineResult("frontmatter", f"Missing required field: '{field.rstrip(':')}'"))
        else:
            results.append(PipelineResult("frontmatter", "Missing YAML frontmatter"))

        # Check content starts with persona
        body = content.split("---", 2)[-1] if "---" in content else content
        if re.search(r"You are .+", body):
            results.append(PipelineResult("content", "Role statement present", severity="success"))
        else:
            results.append(PipelineResult("content", "Missing role statement ('You are...')", severity="warning"))

        # Check for core competencies
        if "core competencies include:" in body.lower() or "core competencies:" in body.lower():
            results.append(PipelineResult("content", "Core competencies section present", severity="success"))
        else:
            results.append(PipelineResult("content", "Missing core competencies section", severity="warning"))

        # Check content depth
        body_words = len(body.split())
        if body_words < self.MIN_DOMAIN_WORDS:
            results.append(PipelineResult("depth", f"Agent content is thin: {body_words} words (minimum {self.MIN_DOMAIN_WORDS})"))
        else:
            results.append(PipelineResult("depth", f"Agent content: {body_words} words", severity="success"))

        # Check for boundaries/handoff section
        if re.search(r"##\s*(Boundaries|Collaboration|Handoff)", body, re.IGNORECASE):
            results.append(PipelineResult("integration", "Boundaries/collaboration section present", severity="success"))
        else:
            results.append(PipelineResult("integration", "Missing boundaries section - define handoff points with other agents", severity="warning"))

        return results


class InfrastructureValidator:
    """Validates pipeline infrastructure exists"""

    def validate(self, base_dir: Path) -> List[PipelineResult]:
        results = []

        checks = [
            (base_dir / "templates" / "agent-research-prompt.md", "Research prompt template", True),
            (base_dir / "docs" / "RESEARCH-PROMPT-GUIDE.md", "RESEARCH-PROMPT-GUIDE.md", False),
        ]
        for path, label, required in checks:
            if path.exists():
                results.append(PipelineResult("infrastructure", f"{label} exists", severity="success"))
            else:
                sev = "error" if required else "warning"
                results.append(PipelineResult("infrastructure", f"Missing {label}: {path}", severity=sev))

        ref_dir = base_dir / "templates" / "reference-agents"
        if ref_dir.exists():
            ref_agents = list(ref_dir.glob("reference-*.md"))
            results.append(PipelineResult("infrastructure", f"Reference agents directory: {len(ref_agents)} archetype(s)", severity="success"))
            if len(ref_agents) < 3:
                results.append(PipelineResult("infrastructure", f"Few reference agents: {len(ref_agents)} (recommend 5)", severity="warning"))
        else:
            results.append(PipelineResult("infrastructure", f"Missing reference agents directory: {ref_dir}"))

        prompts_dir = base_dir / "agent_prompts"
        if prompts_dir.exists():
            results.append(PipelineResult("infrastructure", "Agent prompts directory exists", severity="success"))
        else:
            results.append(PipelineResult("infrastructure", f"Missing agent prompts directory", severity="warning"))

        guide = base_dir / "docs" / "AGENT-CREATION-GUIDE.md"
        if guide.exists() and "Agent Creation Pipeline" in guide.read_text():
            results.append(PipelineResult("documentation", "AGENT-CREATION-GUIDE.md includes pipeline overview", severity="success"))
        elif guide.exists():
            results.append(PipelineResult("documentation", "AGENT-CREATION-GUIDE.md missing pipeline section", severity="warning"))
        else:
            results.append(PipelineResult("documentation", "Missing AGENT-CREATION-GUIDE.md"))

        return results


def output_results(results: List[PipelineResult], command: str, output_json: bool):
    """Format and output validation results"""
    has_errors = any(r.severity == "error" for r in results)

    if output_json:
        output = {
            "command": command,
            "valid": not has_errors,
            "results": [{"check": r.check, "message": r.message, "severity": r.severity} for r in results],
        }
        click.echo(json.dumps(output, indent=2))
    else:
        click.echo(f"\n{'=' * 50}")
        click.echo(f"Pipeline Validation: {command}")
        click.echo(f"{'=' * 50}\n")
        for result in results:
            click.echo(f"  {result}")
        click.echo(f"\n{'=' * 50}")
        click.echo("\u274c Pipeline validation FAILED" if has_errors else "\u2705 Pipeline validation PASSED")
        click.echo(f"{'=' * 50}\n")

    sys.exit(1 if has_errors else 0)


@click.group()
def cli():
    """Validate agent creation pipeline artifacts"""
    pass


@cli.command("research-prompt")
@click.argument("file", type=click.Path(exists=True))
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
def validate_research_prompt(file: str, output_json: bool):
    """Validate a research prompt file"""
    results = ResearchPromptValidator().validate(Path(file))
    output_results(results, "research-prompt", output_json)


@cli.command("reference-agent")
@click.argument("file", type=click.Path(exists=True))
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
def validate_reference_agent(file: str, output_json: bool):
    """Validate a reference agent template"""
    results = ReferenceAgentValidator().validate(Path(file))
    output_results(results, "reference-agent", output_json)


@cli.command("production-agent")
@click.argument("file", type=click.Path(exists=True))
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
@click.option("--require-research", is_flag=True, help="Fail if no corresponding research prompt exists")
def validate_production_agent(file: str, output_json: bool, require_research: bool):
    """Validate a finished agent created through the pipeline"""
    results = ProductionAgentValidator().validate(Path(file), require_research=require_research)
    output_results(results, "production-agent", output_json)


@cli.command("infrastructure")
@click.option("--base-dir", type=click.Path(exists=True), default=".", help="Project base directory")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
def validate_infrastructure(base_dir: str, output_json: bool):
    """Validate pipeline infrastructure exists"""
    results = InfrastructureValidator().validate(Path(base_dir))
    output_results(results, "infrastructure", output_json)


if __name__ == "__main__":
    cli()
