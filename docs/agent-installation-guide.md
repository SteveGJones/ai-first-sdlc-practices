<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Agent Installation Guide](#agent-installation-guide)
  - [Overview](#overview)
  - [Important: Manual Installation Required](#important-manual-installation-required)
  - [Installation Methods](#installation-methods)
    - [Method 1: Using the Agent Installer (Recommended)](#method-1-using-the-agent-installer-recommended)
    - [Method 2: Manual Agent Reference](#method-2-manual-agent-reference)
      - [Option A: Copy Agent Content](#option-a-copy-agent-content)
      - [Option B: Reference Agent Guidelines](#option-b-reference-agent-guidelines)
  - [Agent Categories](#agent-categories)
    - [Core Agents (Essential)](#core-agents-essential)
    - [SDLC-Specific Agents](#sdlc-specific-agents)
    - [Language-Specific Agents](#language-specific-agents)
    - [Specialized Agents](#specialized-agents)
    - [AI Development Agents](#ai-development-agents)
  - [Working with Agents](#working-with-agents)
    - [During Development](#during-development)
    - [Agent Collaboration](#agent-collaboration)
  - [Troubleshooting](#troubleshooting)
    - [Agent Not Found](#agent-not-found)
    - [Installation Issues](#installation-issues)
    - [Using Agents Effectively](#using-agents-effectively)
  - [Future Improvements](#future-improvements)
  - [Example Workflow](#example-workflow)
  - [Conclusion](#conclusion)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Agent Installation Guide

## Overview

The AI-First SDLC framework includes a comprehensive library of specialized AI agents designed to enhance various aspects of software development. This guide explains how to install and use these agents.

## Important: Manual Installation Required

**Dynamic agent deployment is not currently supported by Claude.** This means:
- Agents cannot be automatically made available during a conversation
- Copying files to `.claude/agents/` does not make them immediately accessible
- **IMPORTANT**: Availability after session restart has not been tested
- Manual installation or reference is required

## Installation Methods

### Method 1: Using the Agent Installer (Recommended)

```bash
# From your project root
python tools/automation/agent-installer.py

# Or with specific options:
python tools/automation/agent-installer.py --analyze  # Get recommendations based on project
python tools/automation/agent-installer.py --core-only  # Install only essential agents
python tools/automation/agent-installer.py --languages Python JavaScript  # Language-specific
```

The installer will:
1. Analyze your project (if requested)
2. Recommend appropriate agents
3. Copy agent files to `claude/agents/` in your project
4. Provide manual installation instructions

### Method 2: Manual Agent Reference

Since dynamic deployment doesn't work, you have these options:

#### Option A: Copy Agent Content
1. Find the agent you need in the `agents/` directory
2. Copy the agent's content
3. Share it with Claude in your conversation when needed

#### Option B: Reference Agent Guidelines
1. Review agent specifications in `agents/` directory
2. Ask Claude to follow those patterns
3. Reference specific agent behaviors as needed

## Agent Categories

### Core Agents (Essential)
- **sdlc-coach**: Enforces AI-First SDLC practices
- **test-manager**: Oversees all testing activities
- **solution-architect**: Designs end-to-end solutions
- **security-architect**: Security best practices

### SDLC-Specific Agents
- **kickstart-architect**: Generates optimal project kickstarters
- **framework-validator**: Real-time compliance checking
- **project-bootstrapper**: One-command initialization
- **retrospective-miner**: Extract insights from retrospectives
- **language-python-expert**: Python-specific SDLC guidance

### Language-Specific Agents
Located in `agents/languages/`:
- Python agents (testing, patterns, optimization)
- JavaScript/TypeScript agents
- Go agents
- Java agents
- Rust agents

### Specialized Agents
- **api-designer**: RESTful and GraphQL design
- **database-architect**: Database optimization
- **kubernetes-architect**: K8s deployment
- **ml-architect**: ML system design

### AI Development Agents
- **langchain-architect**: LangChain/LangGraph patterns
- **mcp-server-architect**: MCP server development
- **a2a-architect**: Agent-to-agent communication
- **prompt-engineer**: Prompt optimization

## Working with Agents

### During Development

Since agents aren't dynamically available, use them as references:

```markdown
# In your conversation with Claude:

"I need to create a new kickstarter for my project. 
Please follow the kickstart-architect agent patterns from:
agents/sdlc/kickstart-architect.md"
```

### Agent Collaboration

Some agents work together:
- `sdlc-coach` + `framework-validator`: Continuous compliance
- `test-manager` + language test engineers: Comprehensive testing
- `solution-architect` + specialized architects: Complete design

## Troubleshooting

### Agent Not Found
- Verify agent exists in `agents/` directory
- Check category subdirectory (core/, languages/, etc.)
- Ensure agent has valid YAML frontmatter

### Installation Issues
- Run with `--list` to see available agents
- Check `.agent-manifest.json` for installed agents
- Verify source directory with `--agent-source`

### Using Agents Effectively
1. Read agent documentation in `agents/` directory
2. Understand agent expertise and patterns
3. Reference agent guidelines in conversations
4. Ask Claude to adopt agent personas when needed

## Future Improvements

We're exploring options for better agent integration:
1. Pre-configured agent templates
2. Agent behavior compilation
3. Integration with Claude's native capabilities
4. Automated agent selection based on context

## Example Workflow

```bash
# 1. Analyze your project
python tools/automation/agent-installer.py --analyze

# 2. Install recommended agents
# (Follow prompts)

# 3. Review installed agents
ls claude/agents/

# 4. In your Claude conversation:
"Please help me design this API following the patterns 
from the api-designer agent specifications"
```

## Conclusion

While dynamic agent deployment isn't possible, the agent library provides valuable patterns and guidelines for AI-assisted development. Use the installer to organize relevant agents for your project, then reference their specifications during development conversations.