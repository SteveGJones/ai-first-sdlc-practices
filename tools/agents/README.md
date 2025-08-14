# Agent Generator Tool

A tool for validating and generating properly formatted AI agent files from JSON specifications.

## Purpose

Agent files have complex content that can't be generated from simple CLI inputs. This tool:
1. **Validates** existing agent files for correct YAML frontmatter format
2. **Generates** agent files from detailed JSON specifications
3. **Extracts** existing agents to JSON for editing and regeneration
4. **Creates** JSON templates with the proper structure

## Workflow

### Creating a New Agent

1. **Create a JSON template**:
```bash
python tools/agents/agent-generator.py template "MCP Server Architect"
# Creates: mcp-server-architect-template.json
```

2. **Edit the JSON file** to add your detailed content:
```json
{
  "name": "mcp-server-architect",
  "description": "Expert in Model Context Protocol server design and implementation",
  "examples": [
    {
      "context": "Building an MCP server for database tools",
      "user": "How should I structure an MCP server for database operations?",
      "assistant": "I'll engage the mcp-server-architect to design a robust MCP server architecture."
    }
  ],
  "color": "blue",
  "content": "You are the MCP Server Architect...\n\n[Full agent content here]"
}
```

3. **Generate the agent file**:
```bash
python tools/agents/agent-generator.py generate mcp-server-architect-template.json
# Creates: mcp-server-architect.md with proper YAML frontmatter
```

### Validating Agents

```bash
# Validate a single agent
python tools/agents/agent-generator.py validate agents/mcp-server-architect.md

# Validate all agents in a directory
python tools/agents/agent-generator.py validate-all --directory agents/ --recursive
```

### Fixing Existing Agents

1. **Extract to JSON**:
```bash
python tools/agents/agent-generator.py extract agents/broken-agent.md
# Creates: broken-agent-spec.json
```

2. **Edit the JSON** to fix issues

3. **Regenerate**:
```bash
python tools/agents/agent-generator.py generate broken-agent-spec.json --output agents/fixed-agent.md
```

## JSON Specification Format

```json
{
  "name": "agent-name",
  "description": "Brief description (max 150 chars)",
  "examples": [
    {
      "context": "When this agent should be used",
      "user": "User's question or request",
      "assistant": "How the assistant would invoke this agent"
    }
  ],
  "color": "blue",
  "content": "Full markdown content of the agent instructions"
}
```

## Validation Rules

The validator checks:
- YAML frontmatter delimiters (`---`)
- Required fields: `name`, `description`, `examples`, `color`
- Name format (lowercase, alphanumeric with hyphens)
- Examples structure (list of dicts with context, user, assistant)
- Valid colors (blue, green, purple, red, cyan, yellow, orange)

## CI/CD Integration

Add to your pipeline to ensure all agents are valid:

```yaml
# GitHub Actions
- name: Validate Agent Files
  run: python tools/agents/agent-generator.py validate-all --directory agents/ --recursive
```

## Example: Complete Workflow

```bash
# 1. Create template for new agent
python tools/agents/agent-generator.py template "Database Optimizer"

# 2. Edit database-optimizer-template.json with full content

# 3. Generate the agent file
python tools/agents/agent-generator.py generate database-optimizer-template.json

# 4. Validate it worked
python tools/agents/agent-generator.py validate database-optimizer.md

# 5. Move to agents directory
mv database-optimizer.md agents/ai-development/
```

## Why JSON?

Agent documents have extensive content including:
- Detailed role descriptions
- Core competencies lists
- Methodologies and approaches
- Multiple capability areas
- Success metrics
- Complex instructions

This content cannot be meaningfully provided via CLI arguments. JSON allows you to:
- Edit the full content in your preferred editor
- Version control the specifications
- Validate before generation
- Regenerate consistently
