#!/usr/bin/env python3
"""
Convert agent files to strict template format.
Handles files without YAML frontmatter by extracting content and reformatting.
"""

import re
import shutil
from pathlib import Path
from typing import Dict, List, Tuple
import argparse


class StrictTemplateConverter:
    """Converts agent files to strict template format"""

    def __init__(self, backup_dir: str = "backups/strict-conversion"):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        # Files that need conversion (no YAML frontmatter)
        self.files_to_convert = [
            "agents/future/a2a-mesh-controller.md",
            "agents/future/evolution-engine.md",
            "agents/future/mcp-orchestrator.md",
            "agents/future/swarm-coordinator.md",
            "agents/core/api-design-specialist.md",
            "agents/core/data-privacy-officer.md",
            "agents/core/database-architect.md",
            "agents/creative/ux-ui-architect.md",
            "agents/security/frontend-security-specialist.md",
        ]

    def extract_agent_info(self, content: str, file_path: str) -> Dict:
        """Extract agent information from non-YAML format"""

        info = {
            "name": Path(file_path).stem.replace("-", "_"),
            "title": "",
            "description": "",
            "role": "",
            "expertise": "",
            "purpose": "",
            "capabilities": [],
            "manifesto": "",
            "full_content": content,
        }

        # Extract title from first H1
        title_match = re.search(r"^#\s+([^\n]+)", content, re.MULTILINE)
        if title_match:
            info["title"] = title_match.group(1).strip()

        # Extract tagline (usually after title)
        tagline_match = re.search(r"^>\s+([^\n]+)", content, re.MULTILINE)
        if tagline_match:
            info["description"] = tagline_match.group(1).strip()

        # Extract from Agent Card section
        agent_card_match = re.search(
            r"## Agent Card\s*\n(.*?)(?=\n##|\Z)", content, re.DOTALL
        )
        if agent_card_match:
            card_content = agent_card_match.group(1)

            # Extract role
            role_match = re.search(r"\*\*Role\*\*:\s*([^\n]+)", card_content)
            if role_match:
                info["role"] = role_match.group(1).strip()

            # Extract expertise
            expertise_match = re.search(r"\*\*Expertise\*\*:\s*([^\n]+)", card_content)
            if expertise_match:
                info["expertise"] = expertise_match.group(1).strip()

        # Extract Core Purpose
        purpose_match = re.search(
            r"## Core Purpose\s*\n(.*?)(?=\n##|\Z)", content, re.DOTALL
        )
        if purpose_match:
            info["purpose"] = purpose_match.group(1).strip()

        # Extract Capabilities
        capabilities_match = re.search(
            r"## Capabilities\s*\n(.*?)(?=\n##|\Z)", content, re.DOTALL
        )
        if capabilities_match:
            cap_content = capabilities_match.group(1)
            # Extract main capability headings
            cap_headings = re.findall(r"###\s+\d+\.\s+([^\n]+)", cap_content)
            info["capabilities"] = cap_headings

            # Also extract bullet points
            bullets = re.findall(r"^[-*]\s+([^\n]+)", cap_content, re.MULTILINE)
            # Limit to 10 key capabilities
            info["capabilities"].extend(bullets[:10])

        # Extract Manifesto if present
        manifesto_match = re.search(
            r"##.*?Manifesto\s*\n(.*?)(?=\n##|\Z)", content, re.DOTALL
        )
        if manifesto_match:
            info["manifesto"] = manifesto_match.group(1).strip()

        return info

    def create_strict_template(self, info: Dict) -> str:
        """Create strict template format from extracted info"""

        # Build one-line description
        if info["description"]:
            description = info["description"]
        elif info["role"]:
            description = info["role"]
        else:
            description = f"Specialist agent for {info['name'].replace('_', ' ')}"

        # Clean description - remove special chars, limit length
        description = re.sub(r"[–—]", "-", description)
        if len(description) > 200:
            description = description[:197] + "..."

        # Build full description paragraph
        full_desc_parts = []
        if info["purpose"]:
            # Take first paragraph of purpose
            paragraphs = info["purpose"].split("\n\n")
            if paragraphs:
                first_para = paragraphs[0].replace("**", "").strip()
                full_desc_parts.append(first_para)
        elif info["manifesto"]:
            # Use manifesto opening
            sentences = info["manifesto"].split(".")[:3]
            full_desc_parts.append(". ".join(sentences).strip() + ".")

        full_description = " ".join(full_desc_parts).strip()
        if not full_description:
            full_description = (
                f"I am {info['name'].replace('_', ' ')}, focused on "
                f"{info['expertise'] or 'specialized tasks'} with a collaborative team-first approach."
            )

        # Build core competencies
        competencies = []
        if info["capabilities"]:
            # Clean and format capabilities
            for cap in info["capabilities"][:12]:  # Limit to 12
                clean_cap = re.sub(r"[*_]", "", cap).strip()
                if clean_cap and len(clean_cap) > 5:
                    competencies.append(clean_cap)

        if not competencies:
            # Generate from expertise
            if info["expertise"]:
                expertise_items = [e.strip() for e in info["expertise"].split(",")]
                competencies = [f"Expert in {item}" for item in expertise_items[:6]]

        if not competencies:
            # Default competencies
            competencies = [
                f"Specialized expertise in {info['name'].replace('_', ' ')}",
                "Collaborative team-first approach",
                "Clear communication and documentation",
                "Quality-focused delivery",
            ]

        # Create examples based on agent type
        examples = self.generate_examples(info)

        # Determine color based on agent type
        color = self.determine_color(info["name"])

        # Build the template
        template = f"""---
name: {info['name']}
description: {description}
examples:"""

        # Add examples
        for example in examples:
            template += f"""
- <example>
  Context: {example['context']}
  user: "{example['user']}"
  assistant: "{example['assistant']}"
  <commentary>
  {example['commentary']}
  </commentary>
</example>"""

        template += f"""
color: {color}
---

{full_description}

Your core competencies include:"""

        # Add competencies
        for comp in competencies:
            template += f"\n- {comp}"

        template += "\n"

        return template

    def generate_examples(self, info: Dict) -> List[Dict]:
        """Generate relevant examples based on agent info"""

        name = info["name"].replace("_", " ")

        # Default example structure
        examples = []

        # Generate contextual examples based on agent type
        if "privacy" in info["name"] or "GDPR" in info.get("expertise", ""):
            examples.append(
                {
                    "context": "User data collection needs privacy review",
                    "user": "We want to collect user location data for our new feature",
                    "assistant": (
                        "I'll review this for privacy compliance. We need to ensure proper consent mechanisms, "
                        "data minimization, and purpose limitation. Let me work with the UX team on clear consent flows "
                        "and the database team on retention policies."
                    ),
                    "commentary": "The agent immediately focuses on privacy requirements and collaboration",
                }
            )
        elif "database" in info["name"]:
            examples.append(
                {
                    "context": "Database design for new feature",
                    "user": "We need to store user preferences and activity data",
                    "assistant": (
                        "I'll design an efficient schema for this. Let me collaborate with the "
                        "privacy officer on data retention, the API team on access patterns, "
                        "and the performance engineer on optimization strategies."
                    ),
                    "commentary": "The agent considers multiple perspectives for database design",
                }
            )
        elif "api" in info["name"]:
            examples.append(
                {
                    "context": "API endpoint design needed",
                    "user": "We need endpoints for user management",
                    "assistant": (
                        "I'll design RESTful endpoints following best practices. Let me coordinate with the security team "
                        "on authentication, the database architect on data models, "
                        "and the frontend team on response formats."
                    ),
                    "commentary": "The agent brings together multiple teams for API design",
                }
            )
        elif "evolution" in info["name"] or "future" in info["name"]:
            examples.append(
                {
                    "context": "System needs to adapt to new requirements",
                    "user": "Our system needs to handle dynamic agent capabilities",
                    "assistant": (
                        "I'll design an evolutionary architecture for this. "
                        "Let me work with the orchestration team on coordination patterns, "
                        "the context engineer on state management, and the DevOps team on deployment strategies."
                    ),
                    "commentary": "The agent focuses on adaptable, future-proof solutions",
                }
            )
        else:
            # Generic example
            examples.append(
                {
                    "context": f"Team needs {name} expertise",
                    "user": f"Can you help with {name} requirements?",
                    "assistant": (
                        f"I'll apply my {name} expertise to help. "
                        "Let me understand your specific needs and coordinate with "
                        "relevant team members to ensure comprehensive coverage."
                    ),
                    "commentary": f"The agent provides specialized {name} assistance",
                }
            )

        # Add a collaboration example
        examples.append(
            {
                "context": "Cross-team coordination needed",
                "user": "This feature touches multiple systems",
                "assistant": (
                    f"As the {name}, I'll coordinate across teams. "
                    "Let me identify all stakeholders, understand interdependencies, "
                    "and facilitate collaborative planning sessions."
                ),
                "commentary": "The agent demonstrates team-first collaborative approach",
            }
        )

        return examples

    def determine_color(self, agent_name: str) -> str:
        """Determine appropriate color based on agent type"""

        color_map = {
            "privacy": "purple",
            "database": "blue",
            "api": "green",
            "security": "red",
            "evolution": "orange",
            "orchestrator": "yellow",
            "mcp": "cyan",
            "swarm": "magenta",
            "ux": "pink",
            "ui": "pink",
            "a2a": "teal",
        }

        for key, color in color_map.items():
            if key in agent_name.lower():
                return color

        return "blue"  # default

    def convert_file(self, file_path: str) -> Tuple[bool, str]:
        """Convert a single file to strict template format"""

        try:
            # Create backup
            backup_path = self.backup_dir / Path(file_path).name
            shutil.copy2(file_path, backup_path)

            # Read content
            with open(file_path, "r") as f:
                content = f.read()

            # Check if already has YAML frontmatter
            if content.startswith("---"):
                return False, "Already has YAML frontmatter"

            # Extract agent info
            info = self.extract_agent_info(content, file_path)

            # Create strict template
            new_content = self.create_strict_template(info)

            # Write new content
            with open(file_path, "w") as f:
                f.write(new_content)

            return True, f"Converted successfully (backup: {backup_path})"

        except Exception as e:
            return False, f"Error: {str(e)}"

    def convert_all(self) -> Dict:
        """Convert all identified files"""

        results = {
            "total": len(self.files_to_convert),
            "converted": 0,
            "skipped": 0,
            "failed": 0,
            "details": [],
        }

        for file_path in self.files_to_convert:
            if not Path(file_path).exists():
                print(f"⚠️  Not found: {file_path}")
                results["failed"] += 1
                results["details"].append({"file": file_path, "status": "not_found"})
                continue

            print(f"Converting: {file_path}")
            success, message = self.convert_file(file_path)

            if success:
                print(f"  ✅ {message}")
                results["converted"] += 1
                results["details"].append(
                    {"file": file_path, "status": "converted", "message": message}
                )
            elif "Already has" in message:
                print(f"  ⏭️  {message}")
                results["skipped"] += 1
                results["details"].append(
                    {"file": file_path, "status": "skipped", "message": message}
                )
            else:
                print(f"  ❌ {message}")
                results["failed"] += 1
                results["details"].append(
                    {"file": file_path, "status": "failed", "message": message}
                )

        return results


def main():
    parser = argparse.ArgumentParser(
        description="Convert agent files to strict template format"
    )
    parser.add_argument("--file", help="Convert single file")
    parser.add_argument(
        "--check", action="store_true", help="Check which files need conversion"
    )

    args = parser.parse_args()

    converter = StrictTemplateConverter()

    if args.check:
        print("Files that need conversion:")
        for file_path in converter.files_to_convert:
            if Path(file_path).exists():
                with open(file_path, "r") as f:
                    if not f.read().startswith("---"):
                        print(f"  - {file_path}")
        return

    if args.file:
        converter.files_to_convert = [args.file]

    print("=" * 60)
    print("STRICT TEMPLATE CONVERSION")
    print("=" * 60)
    print(f"Files to convert: {len(converter.files_to_convert)}")
    print(f"Backup directory: {converter.backup_dir}")
    print("-" * 60)

    results = converter.convert_all()

    print("\n" + "=" * 60)
    print("CONVERSION SUMMARY")
    print("=" * 60)
    print(f"Total files: {results['total']}")
    print(f"Converted: {results['converted']}")
    print(f"Skipped: {results['skipped']}")
    print(f"Failed: {results['failed']}")

    if results["converted"] > 0:
        print(
            f"\n✅ Successfully converted {results['converted']} files to strict template format"
        )
        print(f"Backups saved to: {converter.backup_dir}")


if __name__ == "__main__":
    main()
