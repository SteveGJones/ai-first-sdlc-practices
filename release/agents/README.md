# AI-First SDLC Agent Library

This directory contains specialized AI agents for the AI-First SDLC framework.

## Agent Categories

### Core Agents (Required)
Essential agents that every project needs:
- `example-security-architect` - Core SDLC functionality
- `sdlc-coach` - Core SDLC functionality
- `solution-architect` - Core SDLC functionality
- `test-manager` - Core SDLC functionality

### Language-Specific Agents
Specialized agents for different programming languages:

#### Python
- `example-python-expert`

### Specialized Agents
Domain-specific agents for various use cases:

#### Ai Development
- `a2a-architect` (.)
- `agent-developer` (.)
- `langchain-architect` (.)
- `mcp-server-architect` (.)
- `prompt-engineer` (.)

#### Documentation
- `documentation-architect` (.)
- `technical-writer` (.)

#### Project Management
- `agile-coach` (.)
- `delivery-manager` (.)

#### Sdlc
- `framework-validator` (.)
- `kickstart-architect` (.)
- `language-python-expert` (.)
- `project-bootstrapper` (.)
- `retrospective-miner` (.)

#### Testing
- `ai-test-engineer` (.)

## Installation

Agents are automatically installed when setting up a new project:
```bash
python setup-smart.py "Your project description"
```

To install agents manually:
```bash
python tools/automation/agent-installer.py
```

## Validation

All agents are validated before release:
```bash
python tools/validation/validate-agents.py agents/
```
