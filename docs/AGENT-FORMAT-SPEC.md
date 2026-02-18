<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Agent Format Specification](#agent-format-specification)
  - [File Structure](#file-structure)
  - [Official Claude Code Frontmatter](#official-claude-code-frontmatter)
    - [Required Fields](#required-fields)
    - [Optional Fields](#optional-fields)
    - [Tools Field](#tools-field)
    - [Model Field](#model-field)
    - [Permission Modes](#permission-modes)
    - [Persistent Memory](#persistent-memory)
    - [Hooks](#hooks)
  - [Project Extension Fields](#project-extension-fields)
    - [Project Required Fields](#project-required-fields)
    - [Project Optional Fields](#project-optional-fields)
    - [Maturity Tiers](#maturity-tiers)
    - [Examples Structure](#examples-structure)
  - [Complete Schema](#complete-schema)
  - [Content Section](#content-section)
    - [Minimum Required Sections](#minimum-required-sections)
    - [Recommended Sections](#recommended-sections)
  - [Validation Rules](#validation-rules)
    - [YAML Frontmatter](#yaml-frontmatter)
    - [Content Section](#content-section-1)
  - [File Naming Convention](#file-naming-convention)
  - [Directory Structure](#directory-structure)
  - [Example Valid Agent File](#example-valid-agent-file)
  - [Automatic Validation Hook](#automatic-validation-hook)
  - [Version History](#version-history)
  - [Compliance](#compliance)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Agent Format Specification

Technical specification for AI agent file format used in the AI-First SDLC framework. This spec aligns with the [official Claude Code sub-agent format](https://code.claude.com/docs/en/sub-agents) and adds project-specific extension fields.

## File Structure

```
---
[YAML Frontmatter]
---

[Markdown Content — becomes the agent's system prompt]
```

## Official Claude Code Frontmatter

These fields are defined by the official Claude Code sub-agent specification. Only `name` and `description` are required by Claude Code.

### Required Fields

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `name` | string | Unique agent identifier | lowercase, alphanumeric + hyphens only, 1-50 chars |
| `description` | string | When Claude should delegate to this agent — acts as a routing hint | max 500 chars, no special formatting |

### Optional Fields

| Field | Type | Description | Default |
|-------|------|-------------|---------|
| `tools` | string | Comma-separated list of tools the agent can use | Inherits all tools |
| `disallowedTools` | string | Comma-separated list of tools to deny | None |
| `model` | string | Model alias: `sonnet`, `opus`, `haiku`, or `inherit` | `inherit` |
| `permissionMode` | string | Permission mode for the agent | `default` |
| `maxTurns` | integer | Maximum agentic turns before stopping | Unlimited |
| `skills` | array | Skills to preload into agent context | [] |
| `mcpServers` | array/map | MCP servers available to the agent | [] |
| `hooks` | map | Lifecycle hooks scoped to the agent | {} |
| `memory` | string | Persistent memory scope: `user`, `project`, or `local` | None |

### Tools Field

The `tools` field controls which Claude Code tools the agent can use. Format as a **comma-separated string** (official format):

```yaml
tools: Read, Glob, Grep, Bash
```

Valid tool names: `Read`, `Write`, `Edit`, `Bash`, `Glob`, `Grep`, `Task`, `WebFetch`, `WebSearch`, `NotebookEdit`

To restrict which subagents can be spawned, use `Task(agent-name)` syntax:

```yaml
tools: Task(worker, researcher), Read, Bash
```

If `tools` is omitted, the agent inherits all tools from the parent conversation.

### Model Field

Controls which AI model the agent uses:

| Value | Description |
|-------|-------------|
| `sonnet` | Claude Sonnet — balanced capability and speed |
| `opus` | Claude Opus — maximum capability |
| `haiku` | Claude Haiku — fastest, most cost-effective |
| `inherit` | Use the same model as the main conversation (default) |

### Permission Modes

| Mode | Behavior |
|------|----------|
| `default` | Standard permission checking with prompts |
| `acceptEdits` | Auto-accept file edits |
| `dontAsk` | Auto-deny permission prompts |
| `delegate` | Coordination-only mode for agent team leads |
| `bypassPermissions` | Skip all permission checks (use with caution) |
| `plan` | Plan mode (read-only exploration) |

### Persistent Memory

The `memory` field gives the agent a persistent directory that survives across conversations:

| Scope | Location | Use When |
|-------|----------|----------|
| `user` | `~/.claude/agent-memory/<name>/` | Agent should remember across all projects |
| `project` | `.claude/agent-memory/<name>/` | Knowledge is project-specific and shareable |
| `local` | `.claude/agent-memory-local/<name>/` | Project-specific but not version controlled |

### Hooks

Agents can define lifecycle hooks in their frontmatter:

```yaml
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "./scripts/validate-command.sh"
  PostToolUse:
    - matcher: "Edit|Write"
      hooks:
        - type: command
          command: "./scripts/run-linter.sh"
```

## Project Extension Fields

These fields are specific to the AI-First SDLC framework. Claude Code silently ignores unknown frontmatter fields, so these are safe to include. They power the Task tool's routing, the `/agents` UI, and our quality gates.

### Project Required Fields

These are required by this project's validation (`--mode project`) but not by Claude Code itself:

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `examples` | array | Usage examples for Task tool routing | 1-5 examples, see structure below |
| `color` | string | Visual identifier in `/agents` UI | enum: blue, green, purple, red, cyan, yellow, orange |

### Project Optional Fields

| Field | Type | Description | Default |
|-------|------|-------------|---------|
| `version` | string | Agent version | "1.0.0" |
| `category` | string | Agent category | null |
| `priority` | string | Activation priority | "medium" |
| `maturity` | string | Agent quality tier | null |
| `tags` | array | Searchable tags | [] |

### Maturity Tiers

The `maturity` field indicates the quality and readiness level of an agent:

| Tier | Label | Criteria | Frontmatter |
|------|-------|----------|-------------|
| `production` | Ready for daily use | 100+ lines, deep methodology, tested in real projects | `maturity: production` |
| `stable` | Functional, good coverage | 80-100 lines, clear methodology, passes strict validation | `maturity: stable` |
| `beta` | Works but needs depth | 50-80 lines, basic methodology, passes format validation | `maturity: beta` |
| `stub` | Placeholder only | <50 lines, template content, not usable | `maturity: stub` |
| `deprecated` | Being retired | Superseded by another agent | `maturity: deprecated` |

Run the maturity report to see current distribution:
```bash
python tools/validation/validate-agent-format.py agents/ --maturity-report
```

### Examples Structure

```yaml
examples:
  - context: string  # When this agent should be used (required)
    user: string     # User's question or request (required)
    assistant: string # Assistant's response invoking agent (required)
```

## Complete Schema

```yaml
---
# === Official Claude Code Fields ===
name: string                    # [a-z0-9-]{1,50} (required)
description: string             # routing hint, max 500 chars (required)
tools: string                   # comma-separated tool names (optional)
model: enum                     # sonnet|opus|haiku|inherit (optional, default: inherit)

# === Project Extension Fields ===
examples:                       # array[1..5] (project-required)
  - context: string            # .{10,200}
    user: string               # .{5,500}
    assistant: string          # .{10,500}
color: enum                    # blue|green|purple|red|cyan|yellow|orange (project-required)
maturity: enum                 # production|stable|beta|stub|deprecated (optional)
---
```

## Content Section

The content section is free-form Markdown that becomes the agent's system prompt. Agents receive only this system prompt plus basic environment details — not the full Claude Code system prompt.

### Minimum Required Sections

1. **Role Statement**: Opening paragraph defining the agent (typically "You are the [Name], ...")
2. **Core Competencies**: Bulleted list of expertise areas (heading variants accepted: "Core Competencies", "Key Capabilities", "Core Expertise", "Your Core Competencies Include")
3. **Activation Criteria**: When/how the agent is used

### Recommended Sections

```markdown
You are the [Agent Name], [role description].

## Core Competencies
- [Specific expertise]
- [Technologies/tools]
- [Methods/approaches]

## Approach
[Methodology and philosophy]

## Key Capabilities
### [Capability 1]
[Details]

### [Capability 2]
[Details]

## When Activated
[Specific triggers and scenarios]

## Success Metrics
[How success is measured]

## Boundaries
[What this agent doesn't do]
```

## Validation Rules

### YAML Frontmatter

1. **Structure**
   - Must start with `---` on line 1
   - Must end with `---` (with newline after)
   - Must be valid YAML between delimiters

2. **Official Required Fields**
   - `name` and `description` must be present
   - Fields must have correct types and meet constraints

3. **Name Field**
   - Lowercase only
   - Alphanumeric and hyphens only
   - No spaces or underscores
   - Between 1-50 characters
   - Must be unique within agent set

4. **Description Field**
   - Maximum 500 characters
   - No markdown formatting
   - No newlines
   - Should describe when Claude should delegate to this agent

5. **Tools Field** (if present)
   - Comma-separated string of valid tool names
   - Each tool must be a recognized Claude Code tool
   - YAML lists are accepted but comma-separated is the official format

6. **Project Required Fields** (in project mode)
   - `examples`: Minimum 1, maximum 5 examples; each with context, user, assistant
   - `color`: Must be one of the allowed values (case-sensitive)

### Content Section

1. **Format**
   - Valid Markdown
   - UTF-8 encoding
   - No HTML (except in code blocks)

2. **Length**
   - Minimum 100 characters
   - Warning above 50,000 characters (may impact context window)
   - Recommended: 500-40,000 characters
   - Production-tier agents typically range 20,000-40,000 characters

## File Naming Convention

```
[agent-name].md
```

- Must match the `name` field in frontmatter
- Lowercase
- `.md` extension

## Directory Structure

```
agents/
├── core/              # Core framework agents
├── ai-development/    # AI/ML development agents
├── ai-builders/       # AI infrastructure agents
├── sdlc/              # SDLC process agents
├── project-management/ # PM agents
├── testing/           # Testing/QA agents
├── documentation/     # Documentation agents
├── languages/         # Language-specific agents
├── templates/         # Agent templates
└── future/            # Experimental agents
```

## Example Valid Agent File

```markdown
---
# === Official Claude Code Fields ===
name: api-designer
description: Expert in REST and GraphQL API design, versioning, and documentation. Use for API architecture decisions, schema design, and documentation standards.
tools: Read, Glob, Grep, Bash
model: sonnet

# === Project Extension Fields ===
examples:
  - context: Designing a new REST API
    user: "I need to design a REST API for user management"
    assistant: "I'll engage the api-designer agent to help create a well-structured REST API."
  - context: API versioning strategy
    user: "How should I handle API versioning?"
    assistant: "Let me have the api-designer agent explain versioning strategies for your use case."
color: blue
maturity: production
---

You are the API Designer, an expert in creating elegant, scalable, and maintainable APIs.

## Core Competencies
- REST and GraphQL API design
- API versioning strategies
- OpenAPI/Swagger documentation
- Authentication and authorization patterns
- Rate limiting and throttling

## Approach
I follow API-first design principles, ensuring APIs are:
- Intuitive and consistent
- Well-documented
- Versioned appropriately
- Secure by default

## When Activated
When you need API design help, I will:
1. Analyze your domain model and use cases
2. Design resource structure and endpoints
3. Define request/response schemas
4. Create comprehensive documentation
5. Recommend security and performance best practices
```

## Automatic Validation Hook

To automatically validate agent files when they are created or edited, add a PostToolUse hook to your `.claude/settings.local.json`:

```json
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
```

This hook runs after every Write or Edit operation. It checks if the modified file is in `agents/` or `.claude/agents/` and validates it against the official spec if so. Non-agent files are ignored.

## Version History

- **v1.0.0** (2024-01): Initial specification
- **v1.1.0** (2024-08): Added optional fields
- **v1.2.0** (2024-11): Standardized validation rules
- **v1.3.0** (2025-08): Added maturity tiers (production/stable/beta/stub/deprecated)
- **v1.4.0** (2026-02): Added `tools` and `model` fields; updated description limit from 150 to 500 chars
- **v2.0.0** (2026-02): Aligned with official Claude Code sub-agent spec; separated official vs project extension fields; standardized tools to comma-separated string; added all official optional fields (disallowedTools, permissionMode, maxTurns, skills, mcpServers, hooks, memory); added automatic validation hook documentation

## Compliance

Agent files are validated at two levels:

### Official Mode (`--mode official`)
Validates only against the Claude Code sub-agent specification. Use this for agents being distributed to external projects.

### Project Mode (`--mode project`)
Validates official spec plus AI-First SDLC project extension fields. This is the default for this repository.

```bash
# Official-only validation (for export)
python tools/validation/validate-agent-official.py [agent-file] --mode official

# Project validation (default, for this repo)
python tools/validation/validate-agent-official.py [agent-file]

# Full audit
python tools/validation/validate-agent-official.py agents/ --audit

# Auto-fix tools format
python tools/validation/validate-agent-official.py agents/ --fix

# Legacy validator (still works)
python tools/validation/validate-agent-format.py [agent-file]
python tools/validation/validate-agent-format.py agents/ --maturity-report
```
