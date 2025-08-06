<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Agent Template Format Guide](#agent-template-format-guide)
  - [Overview](#overview)
  - [Template Structure](#template-structure)
    - [1. YAML Front Matter (Required)](#1-yaml-front-matter-required)
      - [Key Components:](#key-components)
    - [2. Agent Description Section](#2-agent-description-section)
    - [3. Task Instructions](#3-task-instructions)
    - [4. Response Format Instructions](#4-response-format-instructions)
    - [5. Agent Personality and Approach](#5-agent-personality-and-approach)
    - [6. Uncertainty Handling](#6-uncertainty-handling)
  - [Complete Template Example](#complete-template-example)
  - [Best Practices](#best-practices)
    - [1. Description Section](#1-description-section)
    - [2. Core Competencies](#2-core-competencies)
    - [3. Task Instructions](#3-task-instructions-1)
    - [4. Response Format](#4-response-format)
    - [5. Personality Definition](#5-personality-definition)
  - [Common Patterns](#common-patterns)
    - [1. Review/Validation Agents](#1-reviewvalidation-agents)
    - [2. Creation/Generation Agents](#2-creationgeneration-agents)
    - [3. Analysis/Advisory Agents](#3-analysisadvisory-agents)
    - [4. Setup/Configuration Agents](#4-setupconfiguration-agents)
  - [Validation Checklist](#validation-checklist)
  - [Integration with Claude Code](#integration-with-claude-code)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Agent Template Format Guide

This document provides comprehensive guidance on creating agents using the AI-First SDLC agent template format.

## Overview

The agent template format is designed to create specialized AI agents that can be invoked through Claude Code's Task tool. These agents follow a specific markdown structure that defines their behavior, capabilities, and interaction patterns.

## Template Structure

### 1. YAML Front Matter (Required)

The template begins with YAML front matter enclosed in `---` markers:

```yaml
---
name: [agent-name]  # Must match filename without .md extension
description: [Initial description and usage examples with context]
color: [blue|red|green|yellow|purple|orange|pink|cyan]
---
```

#### Key Components:

**name**:
- Must exactly match the filename (e.g., `test-agent` for `test-agent.md`)
- Use kebab-case naming convention
- Should be descriptive and specific to the agent's role

**description**:
- Comprehensive description including:
  - Primary purpose and when to use the agent
  - Multiple usage examples with context
  - Each example should include:
    - Context explanation
    - User prompt
    - Assistant response
    - Commentary explaining why this agent is appropriate

**color**:
- Visual identifier for the agent
- Choose from: blue, red, green, yellow, purple, orange, pink, cyan

### 2. Agent Description Section

Following the front matter, provide a rich, detailed description of the agent:

```markdown
You are [Agent Role], [detailed description of expertise and mission].

Your core competencies include:
- [Specific skill or knowledge area 1]
- [Specific skill or knowledge area 2]
- [Additional competencies...]
```

### 3. Task Instructions

Define what the agent does when invoked:

```markdown
When [performing main task], you will:

1. **[Action Category]**:
   - [Specific action or check]
   - [Another specific action]
   - [Additional actions...]

2. **[Next Action Category]**:
   - [Specific steps]
   - [Validation points]
```

### 4. Response Format Instructions

Specify how the agent should structure its responses:

```markdown
Your [output type] format should include:
- **[Section Name]**: [What this section contains]
- **[Section Name]**: [Description of content]
- **[Additional sections]**: [Their purposes]
```

### 5. Agent Personality and Approach

Define the agent's tone and behavior:

```markdown
You maintain a [adjective], [adjective] approach, [additional personality traits].
You [key behavioral principle]. You're particularly [specific strength or focus area].
```

### 6. Uncertainty Handling

Specify how the agent handles uncertain situations:

```markdown
When [encountering specific situation], you [systematic approach]:
1. [First step]
2. [Second step]
3. [Additional steps...]
```

## Complete Template Example

Here's the complete template structure with placeholders:

```markdown
---
name: [agent-name]
description: [Main description with usage scenarios]\n\nExamples:\n- <example>\n  Context: [Situation description]\n  user: "[User's request]"\n  assistant: "[How assistant would respond]"\n  <commentary>\n  [Explanation of why this agent is appropriate]\n  </commentary>\n</example>\n- <example>\n  Context: [Another situation]\n  user: "[Different request]"\n  assistant: "[Response using the agent]"\n  <commentary>\n  [Reasoning for agent selection]\n  </commentary>\n</example>
color: [color-choice]
---

You are [Agent Title], [comprehensive description of role and expertise]. Your mission is [primary objective].

Your core competencies include:
- [Domain expertise 1]
- [Domain expertise 2]
- [Technical skill 1]
- [Technical skill 2]
- [Process knowledge]
- [Additional competencies]

When [primary task], you will:

1. **[Phase One Name]**:
   - [Action item]
   - [Verification step]
   - [Quality check]
   - [Documentation requirement]

2. **[Phase Two Name]**:
   - [Implementation step]
   - [Validation process]
   - [Integration check]
   - [Progress tracking]

3. **[Phase Three Name]**:
   - [Review action]
   - [Correction process]
   - [Final validation]
   - [Delivery preparation]

Your [deliverable type] format should include:
- **[Section 1]**: [Content description]
- **[Section 2]**: [What's included]
- **[Section 3]**: [Expected elements]
- **[Section 4]**: [Final components]

You maintain a [personality trait], [approach style] approach, understanding that [key principle]. You never [what to avoid] or [another thing to avoid]. You're particularly [special strength].

When [uncertainty scenario], you [response approach]:
1. [Investigation step]
2. [Analysis step]
3. [Solution step]
4. [Verification step]
5. [Prevention step]

You [collaboration approach] with [other entities], ensuring [quality outcome].
```

## Best Practices

### 1. Description Section
- Include 3-5 detailed examples showing different use cases
- Each example should have clear context and commentary
- Examples should demonstrate the agent's unique value proposition
- Use realistic scenarios that users would actually encounter

### 2. Core Competencies
- List 6-10 specific areas of expertise
- Be concrete and specific, not generic
- Include both technical and soft skills
- Align competencies with the agent's primary purpose

### 3. Task Instructions
- Break down complex processes into numbered steps
- Use bold headers for major sections
- Include specific actions, not vague directions
- Add validation and quality checks throughout

### 4. Response Format
- Define clear sections for structured output
- Specify what content belongs in each section
- Include examples where helpful
- Ensure format supports the agent's purpose

### 5. Personality Definition
- Create a consistent voice and approach
- Define how the agent handles challenges
- Specify what the agent should avoid
- Include behavioral principles

## Common Patterns

### 1. Review/Validation Agents
- Emphasize systematic checking processes
- Include specific criteria for evaluation
- Define clear pass/fail conditions
- Provide improvement suggestions

### 2. Creation/Generation Agents
- Focus on understanding requirements first
- Include iterative refinement processes
- Specify quality standards
- Define delivery formats

### 3. Analysis/Advisory Agents
- Emphasize investigation and discovery
- Include multiple perspective considerations
- Define recommendation structures
- Specify confidence levels

### 4. Setup/Configuration Agents
- Focus on correct initial state
- Include validation at each step
- Define rollback procedures
- Specify common pitfall avoidance

## Validation Checklist

Before finalizing an agent:

- [ ] Name matches filename exactly
- [ ] Description includes multiple relevant examples
- [ ] All examples have context and commentary
- [ ] Core competencies are specific and relevant
- [ ] Task instructions are detailed and actionable
- [ ] Response format is clearly defined
- [ ] Personality and approach are consistent
- [ ] Uncertainty handling is specified
- [ ] No generic or placeholder content remains

## Integration with Claude Code

Agents created with this template are invoked through Claude Code's Task tool:

```python
Task(
    description="Brief task description",
    prompt="Detailed instructions for the agent",
    subagent_type="agent-name"  # Matches the name in front matter
)
```

The agent receives the prompt and executes according to its template definition, returning results in the specified format.
