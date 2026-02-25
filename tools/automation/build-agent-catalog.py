#!/usr/bin/env python3
"""
Build AGENT-CATALOG.json from all agent markdown files.
Extracts metadata, keywords, and capabilities for searchable discovery.
"""

import json
import re
from pathlib import Path
from typing import Dict, Any

try:
    import yaml
except ImportError:
    yaml = None


def extract_agent_metadata(file_path: Path) -> Dict[str, Any]:
    """Extract metadata from an agent markdown file."""

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Extract agent name from filename
    name = file_path.stem

    # Determine category from path
    parts = file_path.parts
    if "agents" in parts:
        idx = parts.index("agents")
        if idx + 1 < len(parts) - 1:
            category = parts[idx + 1]
        else:
            category = "general"
    else:
        category = "unknown"

    # Extract description and capabilities from YAML frontmatter first
    description = ""
    yaml_capabilities = []
    if content.startswith("---") and yaml is not None:
        frontmatter_parts = content.split("---", 2)
        if len(frontmatter_parts) >= 3:
            try:
                metadata = yaml.safe_load(frontmatter_parts[1])
                if isinstance(metadata, dict):
                    description = metadata.get("description", "")
                    if metadata.get("name"):
                        name = metadata["name"]
                    # Extract capabilities from examples contexts
                    examples = metadata.get("examples", [])
                    if isinstance(examples, list):
                        for ex in examples:
                            if isinstance(ex, dict) and ex.get("context"):
                                yaml_capabilities.append(ex["context"])
            except (yaml.YAMLError, AttributeError):
                pass

    if not description:
        desc_match = re.search(
            r"^#[^#].*?\n\n(.*?)(?:\n\n|\n#)", content, re.MULTILINE | re.DOTALL
        )
        description = desc_match.group(1).strip() if desc_match else ""

    # Extract keywords from content
    keywords = set()

    # Common technology keywords
    tech_patterns = [
        r"\b(mcp|model.context.protocol)\b",
        r"\b(langchain|llm|gpt|claude|ai|ml)\b",
        r"\b(api|rest|graphql|grpc)\b",
        r"\b(react|vue|angular|frontend)\b",
        r"\b(python|javascript|typescript|go|rust)\b",
        r"\b(docker|kubernetes|k8s|container)\b",
        r"\b(aws|azure|gcp|cloud)\b",
        r"\b(database|sql|nosql|mongodb|postgres)\b",
        r"\b(security|auth|oauth|jwt)\b",
        r"\b(test|testing|qa|quality)\b",
        r"\b(devops|ci|cd|pipeline)\b",
        r"\b(microservice|architecture|design)\b",
    ]

    for pattern in tech_patterns:
        matches = re.findall(pattern, content.lower())
        keywords.update(matches)

    # Use YAML example contexts as capabilities if available
    capabilities = yaml_capabilities[:5] if yaml_capabilities else []

    # Fall back to regex extraction only if no YAML capabilities
    if not capabilities:
        cap_match = re.search(
            r"(?:what i do|capabilities|responsibilities|expertise).*?\n(.*?)(?:\n#|\n\n#|$)",
            content,
            re.IGNORECASE | re.DOTALL,
        )
        if cap_match:
            cap_text = cap_match.group(1)
            cap_lines = re.findall(r"[-*]\s+(.*?)(?:\n|$)", cap_text)
            # Clean raw markdown artifacts from capabilities
            cleaned = []
            for line in cap_lines[:5]:
                line = line.strip()
                line = re.sub(r"[`<>]", "", line)  # Remove backticks and tags
                if len(line) > 100:
                    line = line[:100] + "..."
                if line:
                    cleaned.append(line)
            capabilities = cleaned

    # Determine domains based on category and content
    domains = []
    domain_map = {
        "ai-development": ["ai-infrastructure", "machine-learning"],
        "ai-builders": ["ai-infrastructure", "tool-integration"],
        "core": ["software-architecture", "system-design"],
        "testing": ["quality-assurance", "test-automation"],
        "security": ["cybersecurity", "compliance"],
        "documentation": ["technical-writing", "knowledge-management"],
        "sdlc": ["process-improvement", "methodology"],
        "project-management": ["delivery", "coordination"],
    }

    if category in domain_map:
        domains = domain_map[category]

    # Special handling for specific agents
    if "mcp" in name.lower() or "model-context-protocol" in content.lower():
        keywords.add("mcp")
        keywords.add("model-context-protocol")
        if "protocol-implementation" not in domains:
            domains.append("protocol-implementation")

    # Use absolute path to avoid relative path issues
    path_str = str(file_path.absolute())
    # Convert to relative path for storage
    if "/ai-first-sdlc-practices/" in path_str:
        path_str = path_str.split("/ai-first-sdlc-practices/")[-1]
    else:
        path_str = str(file_path)

    return {
        "name": name,
        "path": path_str,
        "category": category,
        "keywords": sorted(list(keywords)),
        "capabilities": capabilities,
        "domains": domains,
        "description": description[:200] + "..."
        if len(description) > 200
        else description,
    }


def build_catalog():
    """Build the complete agent catalog."""

    agents_dir = Path("agents")
    if not agents_dir.exists():
        print("Error: agents directory not found")
        return

    catalog = {
        "version": "1.0.0",
        "generated": "",
        "total_agents": 0,
        "categories": {},
        "agents": [],
    }

    # Find all agent markdown files
    agent_files = list(agents_dir.rglob("*.md"))

    # Filter out README files, templates, and the templates directory
    agent_files = [
        f
        for f in agent_files
        if "README" not in f.name
        and "template" not in f.stem.lower()
        and "templates" not in f.parts
    ]

    for file_path in sorted(agent_files):
        try:
            metadata = extract_agent_metadata(file_path)
            catalog["agents"].append(metadata)

            # Track categories
            cat = metadata["category"]
            if cat not in catalog["categories"]:
                catalog["categories"][cat] = 0
            catalog["categories"][cat] += 1

        except Exception as e:
            print(f"Warning: Failed to process {file_path}: {e}")

    catalog["total_agents"] = len(catalog["agents"])

    # Add timestamp
    from datetime import datetime

    catalog["generated"] = datetime.now().isoformat()

    # Write catalog
    output_path = Path("AGENT-CATALOG.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(catalog, f, indent=2, ensure_ascii=False)

    print(
        f"Successfully created AGENT-CATALOG.json with {catalog['total_agents']} agents"
    )
    print(f"Categories: {catalog['categories']}")

    # Also create a human-readable index
    create_readable_index(catalog)


def create_readable_index(catalog: Dict[str, Any]):
    """Create a human-readable AGENT-INDEX.md file."""

    output = ["# Agent Catalog Index\n"]
    output.append(f"*Generated: {catalog['generated']}*\n")
    output.append(f"*Total Agents: {catalog['total_agents']}*\n\n")

    # Group by category
    by_category = {}
    for agent in catalog["agents"]:
        cat = agent["category"]
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(agent)

    output.append("## Agents by Category\n\n")

    for category in sorted(by_category.keys()):
        agents = by_category[category]
        output.append(
            f"### {category.replace('-', ' ').title()} ({len(agents)} agents)\n\n"
        )

        for agent in sorted(agents, key=lambda x: x["name"]):
            output.append(f"#### `{agent['name']}`\n")
            output.append(f"- **Path**: `{agent['path']}`\n")
            output.append(f"- **Description**: {agent['description']}\n")
            if agent["keywords"]:
                output.append(f"- **Keywords**: {', '.join(agent['keywords'][:10])}\n")
            if agent["capabilities"]:
                output.append("- **Key Capabilities**:\n")
                for cap in agent["capabilities"][:3]:
                    output.append(f"  - {cap}\n")
            output.append("\n")

    # Write index
    with open("AGENT-INDEX.md", "w", encoding="utf-8") as f:
        f.write("".join(output))

    print("Also created AGENT-INDEX.md for human reference")


if __name__ == "__main__":
    build_catalog()
