#!/usr/bin/env python3
"""
Agent Template Migration Tool

Migrates non-compliant agent files to strict template format.
Preserves valuable content while removing forbidden sections.
"""

import re
import os
import sys
import shutil
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import yaml
import json


@dataclass
class AgentContent:
    """Holds extracted content from agent file"""

    name: str
    description: str
    manifesto: Optional[str]
    agent_card: Optional[str]
    team_chemistry: Optional[str]
    success_metrics: Optional[str]
    core_purpose: Optional[str]
    capabilities: List[str]
    existing_yaml: Optional[Dict]
    file_path: str


@dataclass
class MigrationResult:
    """Result of a single agent migration"""

    file_path: str
    success: bool
    backup_path: Optional[str] = None
    error: Optional[str] = None
    violations_fixed: List[str] = None


class AgentMigrator:
    """Migrates agent files to strict template format"""

    def __init__(self, backup_dir: str = "backups"):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)

        # Patterns for extracting content
        self.section_patterns = {
            "manifesto": r"##\s+.*?Manifesto\s*\n(.*?)(?=\n##|\n---|\Z)",
            "agent_card": r"##\s+Agent Card\s*\n(.*?)(?=\n##|\n---|\Z)",
            "team_chemistry": r"##\s+Team Chemistry.*?\n(.*?)(?=\n##|\n---|\Z)",
            "success_metrics": r"##\s+Success Metrics\s*\n(.*?)(?=\n##|\n---|\Z)",
            "core_purpose": r"##\s+Core Purpose\s*\n(.*?)(?=\n##|\n---|\Z)",
            "power_combinations": r"##\s+Power Combinations\s*\n(.*?)(?=\n##|\n---|\Z)",
        }

        # Files to migrate (from grep results)
        self.non_compliant_files = [
            "agents/ai-builders/orchestration-architect.md",
            "agents/ai-builders/context-engineer.md",
            "agents/ai-builders/rag-system-designer.md",
            "agents/future/evolution-engine.md",
            "agents/future/swarm-coordinator.md",
            "agents/future/a2a-mesh-controller.md",
            "agents/future/mcp-orchestrator.md",
            "agents/security/frontend-security-specialist.md",
            "agents/core/database-architect.md",
            "agents/core/data-privacy-officer.md",
            "agents/creative/ux-ui-architect.md",
            "agents/core/api-design-specialist.md",
            "agents/core/frontend-security-specialist.md",
            "agents/core/ux-ui-architect.md",
            "agents/project-management/delivery-manager.md",
            "agents/ai-development/prompt-engineer.md",
            "agents/core/sdlc-coach.md",
        ]

    def parse_agent_file(self, file_path: str) -> AgentContent:
        """Parse an agent file and extract all content"""

        with open(file_path, "r") as f:
            content = f.read()

        # Extract YAML frontmatter if exists
        yaml_match = re.search(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
        existing_yaml = {}
        if yaml_match:
            try:
                existing_yaml = yaml.safe_load(yaml_match.group(1))
            except:
                pass

        # Extract agent name
        name = existing_yaml.get("name", "")
        if not name:
            # Try to extract from filename
            name = Path(file_path).stem.replace("-", "_")

        # Extract sections
        manifesto = self._extract_section(content, "manifesto")
        agent_card = self._extract_section(content, "agent_card")
        team_chemistry = self._extract_section(content, "team_chemistry")
        success_metrics = self._extract_section(content, "success_metrics")
        core_purpose = self._extract_section(content, "core_purpose")

        # Extract capabilities
        capabilities = self._extract_capabilities(content)

        # Extract or create description
        description = existing_yaml.get("description", "")
        if not description and manifesto:
            # Extract first meaningful sentence from manifesto
            sentences = manifesto.strip().split(".")
            if sentences:
                description = sentences[0].strip() + "."

        return AgentContent(
            name=name,
            description=description,
            manifesto=manifesto,
            agent_card=agent_card,
            team_chemistry=team_chemistry,
            success_metrics=success_metrics,
            core_purpose=core_purpose,
            capabilities=capabilities,
            existing_yaml=existing_yaml,
            file_path=file_path,
        )

    def _extract_section(self, content: str, section_type: str) -> Optional[str]:
        """Extract a specific section from content"""

        pattern = self.section_patterns.get(section_type)
        if not pattern:
            return None

        match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()

        return None

    def _extract_capabilities(self, content: str) -> List[str]:
        """Extract capabilities/competencies from content"""

        capabilities = []

        # Look for bullet points in various sections
        patterns = [
            r"Your core competencies include:\s*\n((?:[-*]\s+.*?\n)+)",
            r"Capabilities:\s*\n((?:[-*]\s+.*?\n)+)",
            r"Core Competencies:\s*\n((?:[-*]\s+.*?\n)+)",
            r"Key Skills:\s*\n((?:[-*]\s+.*?\n)+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                bullet_text = match.group(1)
                # Extract individual bullets
                bullets = re.findall(r"[-*]\s+(.*?)(?=\n|$)", bullet_text)
                capabilities.extend([b.strip() for b in bullets])

        # Remove duplicates while preserving order
        seen = set()
        unique_capabilities = []
        for cap in capabilities:
            if cap not in seen:
                seen.add(cap)
                unique_capabilities.append(cap)

        return unique_capabilities

    def transform_to_strict_format(self, agent: AgentContent) -> str:
        """Transform agent content to strict template format"""

        # Build one-line description
        description = agent.description
        if not description and agent.manifesto:
            # Extract essence from manifesto
            first_line = agent.manifesto.split("\n")[0].strip()
            if first_line:
                description = first_line
        if not description:
            description = f"Specialist agent for {agent.name.replace('_', ' ')}"

        # Build full description paragraph
        full_description_parts = []

        if agent.manifesto:
            # Clean up manifesto text
            manifesto_text = agent.manifesto.replace("**", "").strip()
            # Take first paragraph or first 3 sentences
            paragraphs = manifesto_text.split("\n\n")
            if paragraphs:
                full_description_parts.append(paragraphs[0])

        if agent.core_purpose:
            full_description_parts.append(agent.core_purpose)

        if agent.agent_card:
            # Extract role description from agent card
            role_match = re.search(r"Role:\s*(.*?)(?=\n|$)", agent.agent_card)
            if role_match:
                full_description_parts.append(role_match.group(1))

        full_description = " ".join(full_description_parts).strip()
        if not full_description:
            full_description = f"I am {agent.name.replace('_', ' ')}, a specialist agent focused on delivering excellence in my domain."

        # Build core competencies
        competencies = agent.capabilities
        if not competencies and agent.agent_card:
            # Try to extract from agent card
            skill_match = re.findall(r"[-*]\s+(.*?)(?=\n|$)", agent.agent_card)
            competencies = [s.strip() for s in skill_match if s.strip()]

        if not competencies:
            # Generate basic competencies
            competencies = [
                f"Specialized expertise in {agent.name.replace('_', ' ')}",
                "Collaborative team-first approach",
                "Clear communication and documentation",
                "Quality-focused delivery",
            ]

        # Generate examples
        examples = (
            agent.existing_yaml.get("examples", []) if agent.existing_yaml else []
        )
        if not examples:
            # Generate a basic example
            examples = [
                {
                    "context": f"When you need {agent.name.replace('_', ' ')} expertise",
                    "user": f"I need help with {agent.name.replace('_', ' ')} tasks",
                    "assistant": f"I'll help you with that using my {agent.name.replace('_', ' ')} expertise",
                    "commentary": f"Use this agent for {agent.name.replace('_', ' ')} related work",
                }
            ]

        # Determine color
        color = (
            agent.existing_yaml.get("color", "blue") if agent.existing_yaml else "blue"
        )

        # Build the strict format template
        template = f"""---
name: {agent.name}
description: {description}
examples:"""

        # Add examples in correct format
        for example in examples:
            template += f"""
- <example>
  Context: {example.get('context', 'General usage')}
  user: "{example.get('user', 'Help me with this task')}"
  assistant: "{example.get('assistant', 'I will help you with my expertise')}"
  <commentary>
  {example.get('commentary', 'This agent provides specialized assistance')}
  </commentary>
</example>"""

        template += f"""
color: {color}
---

{full_description}

Your core competencies include:"""

        # Add competencies
        for competency in competencies:
            template += f"\n- {competency}"

        template += "\n"

        return template

    def validate_strict_format(self, content: str) -> Tuple[bool, List[str]]:
        """Validate that content follows strict format"""

        violations = []

        # Check for forbidden sections
        forbidden_patterns = [
            (r"##\s+.*?Manifesto", "Manifesto section"),
            (r"##\s+Agent Card", "Agent Card section"),
            (r"##\s+Team Chemistry", "Team Chemistry section"),
            (r"##\s+Success Metrics", "Success Metrics section"),
            (r"##\s+Power Combinations", "Power Combinations section"),
        ]

        for pattern, name in forbidden_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                violations.append(f"Contains forbidden {name}")

        # Check for required YAML frontmatter
        if not re.search(r"^---\s*\n.*?\n---", content, re.DOTALL):
            violations.append("Missing YAML frontmatter")

        # Check for required fields in YAML
        yaml_match = re.search(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
        if yaml_match:
            try:
                yaml_content = yaml.safe_load(yaml_match.group(1))
                required_fields = ["name", "description", "examples", "color"]
                for field in required_fields:
                    if field not in yaml_content:
                        violations.append(f"Missing required YAML field: {field}")
            except:
                violations.append("Invalid YAML frontmatter")

        # Check for core competencies
        if "Your core competencies include:" not in content:
            violations.append("Missing core competencies section")

        return len(violations) == 0, violations

    def migrate_file(self, file_path: str) -> MigrationResult:
        """Migrate a single agent file"""

        try:
            # Create backup
            backup_path = self.backup_dir / f"{Path(file_path).name}.backup"
            shutil.copy2(file_path, backup_path)

            # Parse existing content
            agent = self.parse_agent_file(file_path)

            # Transform to strict format
            new_content = self.transform_to_strict_format(agent)

            # Validate new content
            is_valid, violations = self.validate_strict_format(new_content)

            if not is_valid:
                return MigrationResult(
                    file_path=file_path,
                    success=False,
                    backup_path=str(backup_path),
                    error=f"Validation failed: {violations}",
                )

            # Write new content
            with open(file_path, "w") as f:
                f.write(new_content)

            # Determine what was fixed
            violations_fixed = []
            if agent.manifesto:
                violations_fixed.append("Removed Manifesto section")
            if agent.team_chemistry:
                violations_fixed.append("Removed Team Chemistry section")
            if agent.success_metrics:
                violations_fixed.append("Removed Success Metrics section")
            if agent.agent_card:
                violations_fixed.append("Removed Agent Card section")

            return MigrationResult(
                file_path=file_path,
                success=True,
                backup_path=str(backup_path),
                violations_fixed=violations_fixed,
            )

        except Exception as e:
            return MigrationResult(file_path=file_path, success=False, error=str(e))

    def migrate_all(self) -> Dict[str, any]:
        """Migrate all non-compliant files"""

        results = []

        for file_path in self.non_compliant_files:
            full_path = Path(file_path)
            if not full_path.exists():
                results.append(
                    MigrationResult(
                        file_path=file_path, success=False, error="File not found"
                    )
                )
                continue

            print(f"Migrating {file_path}...")
            result = self.migrate_file(file_path)
            results.append(result)

            if result.success:
                print(f"  ✅ Success - Fixed: {', '.join(result.violations_fixed)}")
            else:
                print(f"  ❌ Failed: {result.error}")

        # Generate summary
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]

        summary = {
            "total_files": len(results),
            "successful": len(successful),
            "failed": len(failed),
            "success_rate": f"{(len(successful) / len(results) * 100):.1f}%",
            "backups_created": len([r for r in results if r.backup_path]),
            "violations_fixed": sum(
                len(r.violations_fixed) for r in successful if r.violations_fixed
            ),
            "failed_files": [r.file_path for r in failed],
        }

        return summary


def main():
    parser = argparse.ArgumentParser(
        description="Migrate agent files to strict template format"
    )
    parser.add_argument(
        "--backup-dir",
        default="backups/agent-migration",
        help="Directory for backup files",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be migrated without making changes",
    )
    parser.add_argument("--file", help="Migrate single file instead of all")

    args = parser.parse_args()

    migrator = AgentMigrator(backup_dir=args.backup_dir)

    if args.file:
        # Migrate single file
        result = migrator.migrate_file(args.file)
        if result.success:
            print(f"✅ Successfully migrated {args.file}")
            if result.violations_fixed:
                print(f"   Fixed: {', '.join(result.violations_fixed)}")
        else:
            print(f"❌ Failed to migrate {args.file}: {result.error}")
    else:
        # Migrate all files
        print("Starting migration of all non-compliant agent files...")
        print(f"Backing up to: {args.backup_dir}")
        print("-" * 60)

        summary = migrator.migrate_all()

        print("\n" + "=" * 60)
        print("MIGRATION SUMMARY")
        print("=" * 60)
        print(f"Total files processed: {summary['total_files']}")
        print(f"Successful migrations: {summary['successful']}")
        print(f"Failed migrations: {summary['failed']}")
        print(f"Success rate: {summary['success_rate']}")
        print(f"Total violations fixed: {summary['violations_fixed']}")

        if summary["failed_files"]:
            print("\nFailed files:")
            for file in summary["failed_files"]:
                print(f"  - {file}")

        print(f"\nBackups saved to: {args.backup_dir}")


if __name__ == "__main__":
    main()
