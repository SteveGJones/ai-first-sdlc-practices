<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [AI-First SDLC Agent Discovery Guide](#ai-first-sdlc-agent-discovery-guide)
  - [Overview](#overview)
  - [Agent Quality Tiers](#agent-quality-tiers)
  - [Critical Information](#critical-information)
  - [Quick Start: Essential Agents](#quick-start-essential-agents)
    - [Core Agents (Install These First!)](#core-agents-install-these-first)
  - [Agent Categories](#agent-categories)
    - [Core Agents (27 agents)](#core-agents-27-agents)
      - [Architecture](#architecture)
      - [Security](#security)
      - [Operations](#operations)
      - [Compliance & Governance](#compliance--governance)
      - [Data](#data)
      - [Agent Creation Pipeline](#agent-creation-pipeline)
      - [Other Core](#other-core)
    - [AI/ML Development Agents (9 agents)](#aiml-development-agents-9-agents)
    - [AI Builders Agents (5 agents)](#ai-builders-agents-5-agents)
    - [Testing & Quality Agents (4 agents)](#testing--quality-agents-4-agents)
    - [Documentation Agents (2 agents)](#documentation-agents-2-agents)
    - [Project Management Agents (4 agents)](#project-management-agents-4-agents)
    - [SDLC Agents (8 agents)](#sdlc-agents-8-agents)
    - [Template Agents (2 agents)](#template-agents-2-agents)
    - [Language Agents (1 agent)](#language-agents-1-agent)
    - [Future Agents (1 agent)](#future-agents-1-agent)
  - [How to Discover Agents](#how-to-discover-agents)
    - [1. During Initial Setup](#1-during-initial-setup)
    - [2. Using ai-first-kick-starter Agent](#2-using-ai-first-kick-starter-agent)
    - [3. By Project Type](#3-by-project-type)
      - [Python API Project](#python-api-project)
      - [AI/ML Application](#aiml-application)
      - [Cloud-Native Microservices](#cloud-native-microservices)
      - [Frontend Application](#frontend-application)
      - [MCP Server Development](#mcp-server-development)
      - [Security-Critical Application](#security-critical-application)
  - [Agent Installation Process](#agent-installation-process)
    - [Step 1: Identify Needed Agents](#step-1-identify-needed-agents)
    - [Step 2: Install Agents](#step-2-install-agents)
    - [Step 3: Restart AI Assistant](#step-3-restart-ai-assistant)
    - [Step 4: Verify Installation](#step-4-verify-installation)
  - [Agent Collaboration Patterns](#agent-collaboration-patterns)
    - [Design -> Implementation -> Testing](#design---implementation---testing)
    - [Cloud-Native Development Flow](#cloud-native-development-flow)
    - [MCP Server Development Flow](#mcp-server-development-flow)
    - [Production Deployment](#production-deployment)
  - [Finding Agents for Specific Needs](#finding-agents-for-specific-needs)
    - ["I need help with..."](#i-need-help-with)
      - [API Design](#api-design)
      - [Performance Issues](#performance-issues)
      - [Security Concerns](#security-concerns)
      - [Cloud Infrastructure](#cloud-infrastructure)
      - [Monitoring & Alerting](#monitoring--alerting)
      - [Documentation](#documentation)
      - [Testing Strategies](#testing-strategies)
  - [Best Practices](#best-practices)
    - [1. Start with Core Agents](#1-start-with-core-agents)
    - [2. Add Agents Incrementally](#2-add-agents-incrementally)
    - [3. Use Agent Recommendations](#3-use-agent-recommendations)
    - [4. Consider Project Evolution](#4-consider-project-evolution)
    - [5. Leverage Agent Collaboration](#5-leverage-agent-collaboration)
  - [Troubleshooting](#troubleshooting)
    - [Agents Not Responding](#agents-not-responding)
    - [Wrong Agent Recommendations](#wrong-agent-recommendations)
    - [Agent Conflicts](#agent-conflicts)
  - [Getting Help](#getting-help)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# AI-First SDLC Agent Discovery Guide

## Overview
The AI-First SDLC framework provides **68 specialized AI agents** organized into 10 categories to enhance your development workflow. This guide helps you discover, understand, and install the right agents for your project needs.

## Agent Quality Tiers

Every agent has a maturity label indicating its readiness:

| Tier | Count | Description |
|------|-------|-------------|
| **Production** | 34 | Ready for daily use. 100+ lines, deep methodology, battle-tested |
| **Stable** | 26 | Functional with good coverage. 80-100 lines, clear methodology |
| **Beta** | 4 | Works but needs depth. 50-80 lines, basic methodology |
| **Stub** | 4 | Placeholder only. Awaiting research-driven rebuild |

See `docs/AGENT-FORMAT-SPEC.md` for full maturity tier criteria.
See `docs/AGENT-ROADMAP.md` for planned future agents.

## Critical Information
**IMPORTANT**: Installing new agents requires restarting your AI assistant (Claude, GPT, etc.) for them to become active.

## Quick Start: Essential Agents

### Core Agents (Install These First!)
Every project should have these critical agents:

1. **sdlc-enforcer** `production`
   - Primary guardian of AI-First SDLC compliance
   - Enforces Zero Technical Debt policy
   - **When to use**: ALWAYS - from project start

2. **critical-goal-reviewer** `stable`
   - Quality assurance and constructive challenger
   - Reviews work against original goals
   - **When to use**: After completing any significant work

3. **solution-architect** `stable`
   - System design and architecture expert
   - Reviews technical decisions
   - **When to use**: Before implementing complex features

## Agent Categories

### Core Agents (27 agents)

#### Architecture
- **api-architect** `production` - REST, GraphQL, gRPC design and API lifecycle management
- **backend-architect** `production` - Microservices, event-driven architecture, scalability patterns
- **frontend-architect** `production` - Component architecture, accessibility, SSR/SSG, design systems
- **cloud-architect** `production` - Multi-cloud strategy, IaC, cost optimization, serverless
- **solution-architect** `stable` - System design and architecture decisions
- **mobile-architect** `stub` - Mobile application architecture (awaiting rebuild)

#### Security
- **security-architect** `production` - Threat modeling, zero-trust, OWASP, compliance frameworks
- **frontend-security-specialist** `stable` - Frontend-specific security patterns
- **example-security-architect** `stable` - Reference implementation for security agents

#### Operations
- **devops-specialist** `production` - CI/CD, deployment automation, infrastructure as code
- **sre-specialist** `stable` - Production monitoring, incident response, reliability
- **observability-specialist** `stable` - OpenTelemetry, distributed tracing, SLO/SLI, alerting
- **container-platform-specialist** `stable` - Docker, Kubernetes, Helm, GitOps, service mesh

#### Compliance & Governance
- **compliance-auditor** `production` - Compliance checking and audit reporting
- **sdlc-enforcer** `production` - SDLC compliance enforcement
- **sdlc-coach** `production` - SDLC education and mentoring
- **compliance-report-generator** `stable` - Automated compliance report generation
- **enforcement-strategy-advisor** `stable` - Enforcement strategy recommendations

#### Data
- **database-architect** `stable` - Database design and optimization
- **data-architect** `stub` - Data architecture (awaiting rebuild)
- **data-privacy-officer** `stub` - Data privacy compliance (awaiting rebuild)

#### Agent Creation Pipeline
- **deep-research-agent** `production` - Systematic web research for agent creation (CRAAP evaluation, multi-phase methodology)
- **agent-builder** `production` - Constructs agents from research documents and reference archetypes (knowledge distillation, anti-pattern detection)

#### Other Core
- **critical-goal-reviewer** `stable` - Goal alignment validation
- **github-integration-specialist** `production` - GitHub automation
- **test-manager** `stable` - Test strategy and coordination
- **ux-ui-architect** `stable` - UX/UI design guidance

### AI/ML Development Agents (9 agents)
- **ai-solution-architect** `production` - Enterprise AI system design
- **prompt-engineer** `production` - Prompt optimization expert
- **mcp-server-architect** `production` - Model Context Protocol expert
- **mcp-test-agent** `production` - MCP testing specialist
- **mcp-quality-assurance** `production` - MCP quality expert
- **agent-developer** `production` - Creates new AI agents
- **junior-ai-solution-architect** `stable` - Fresh perspectives on AI
- **langchain-architect** `stable` - LangChain framework specialist
- **a2a-architect** `stable` - Agent-to-Agent communication

### AI Builders Agents (5 agents)
- **ai-team-transformer** `production` - AI team transformation strategies
- **ai-devops-engineer** `stable` - AI-enhanced DevOps workflows
- **context-engineer** `stable` - Context window optimization
- **orchestration-architect** `stable` - Multi-agent orchestration patterns
- **rag-system-designer** `stable` - RAG system architecture

### Testing & Quality Agents (4 agents)
- **ai-test-engineer** `production` - AI-specific testing
- **performance-engineer** `production` - Performance optimization
- **code-review-specialist** `stable` - Automated code review
- **integration-orchestrator** `stable` - Integration testing

### Documentation Agents (2 agents)
- **documentation-architect** `production` - Documentation systems
- **technical-writer** `production` - Clear technical documentation

### Project Management Agents (4 agents)
- **project-plan-tracker** `production` - Progress monitoring
- **agile-coach** `beta` - Agile methodology guidance
- **delivery-manager** `beta` - Project delivery coordination
- **team-progress-tracker** `stable` - Team-level progress tracking

### SDLC Agents (8 agents)
- **ai-first-kick-starter** `production` - Post-installation advisor
- **language-go-expert** `production` - Go language best practices
- **language-javascript-expert** `production` - JavaScript/TypeScript best practices
- **framework-validator** `stable` - Framework compliance
- **language-python-expert** `stable` - Python best practices
- **project-bootstrapper** `stable` - Project initialization
- **sdlc-knowledge-curator** `stable` - SDLC knowledge management
- **retrospective-miner** `beta` - Retrospective insights

### Template Agents (2 agents)
- **project-strategy-orchestrator** `production` - Project strategy templates
- **team-assembly-orchestrator** `production` - Team composition templates

### Language Agents (1 agent)
- **example-python-expert** `beta` - Reference Python implementation

### Future Agents (1 agent)
- **mcp-orchestrator** `stub` - Multi-MCP coordination (planned)

## How to Discover Agents

### 1. During Initial Setup
When running `setup-smart.py`, you'll receive agent recommendations based on your project description:
```bash
python setup-smart.py "building a Python API with AI features"
```

### 2. Using ai-first-kick-starter Agent
After installation, use this agent to discover more agents:
```
"What agents should I install for performance optimization?"
"I'm adding authentication to my app. Which agents can help?"
```

### 3. By Project Type

#### Python API Project
- Core: sdlc-enforcer, critical-goal-reviewer, solution-architect
- Recommended: api-architect, backend-architect, performance-engineer

#### AI/ML Application
- Core: sdlc-enforcer, critical-goal-reviewer, solution-architect
- Recommended: ai-solution-architect, prompt-engineer, ai-test-engineer

#### Cloud-Native Microservices
- Core: sdlc-enforcer, critical-goal-reviewer, solution-architect
- Recommended: cloud-architect, container-platform-specialist, observability-specialist, backend-architect

#### Frontend Application
- Core: sdlc-enforcer, critical-goal-reviewer, solution-architect
- Recommended: frontend-architect, ux-ui-architect, performance-engineer

#### MCP Server Development
- Core: sdlc-enforcer, critical-goal-reviewer, solution-architect
- Recommended: mcp-server-architect, mcp-test-agent, mcp-quality-assurance

#### Security-Critical Application
- Core: sdlc-enforcer, critical-goal-reviewer, solution-architect
- Recommended: security-architect, compliance-auditor, frontend-security-specialist

## Agent Installation Process

### Step 1: Identify Needed Agents
Use the recommendations above or ask ai-first-kick-starter for guidance.

### Step 2: Install Agents
Follow your AI platform's agent installation process.

### Step 3: Restart AI Assistant
**CRITICAL**: You must restart your AI assistant for new agents to become active.

### Step 4: Verify Installation
Ask your AI: "What specialized agents do I have available?"

## Agent Collaboration Patterns

### Design -> Implementation -> Testing
1. **solution-architect**: Creates design
2. **backend-architect** / **frontend-architect**: Guides implementation
3. **test-manager**: Plans testing
4. **ai-test-engineer**: Executes tests
5. **critical-goal-reviewer**: Validates against goals

### Cloud-Native Development Flow
1. **cloud-architect**: Infrastructure design
2. **container-platform-specialist**: Container orchestration
3. **observability-specialist**: Monitoring setup
4. **sre-specialist**: Production readiness
5. **performance-engineer**: Performance validation

### MCP Server Development Flow
1. **mcp-server-architect**: Designs architecture
2. **mcp-quality-assurance**: Reviews design
3. Implementation occurs
4. **mcp-test-agent**: Tests from AI perspective
5. **mcp-quality-assurance**: Final review

### Production Deployment
1. **devops-specialist**: CI/CD setup
2. **security-architect**: Security review
3. **performance-engineer**: Performance validation
4. **observability-specialist**: Monitoring setup
5. **sre-specialist**: Production monitoring
6. **compliance-auditor**: Final checks

## Finding Agents for Specific Needs

### "I need help with..."

#### API Design
-> **api-architect**: REST, GraphQL, gRPC design and best practices

#### Performance Issues
-> **performance-engineer**: Identifies bottlenecks and optimizations

#### Security Concerns
-> **security-architect**: Threat modeling, zero-trust, OWASP
-> **compliance-auditor**: Compliance assessments

#### Cloud Infrastructure
-> **cloud-architect**: Multi-cloud strategy and IaC
-> **container-platform-specialist**: Kubernetes and container orchestration

#### Monitoring & Alerting
-> **observability-specialist**: OpenTelemetry, tracing, SLOs
-> **sre-specialist**: Incident response and reliability

#### Documentation
-> **technical-writer**: User-facing docs
-> **documentation-architect**: Documentation systems

#### Testing Strategies
-> **test-manager**: Overall strategy
-> **ai-test-engineer**: AI-specific testing
-> **integration-orchestrator**: Integration testing

## Best Practices

### 1. Start with Core Agents
Always install the three critical agents first (sdlc-enforcer, critical-goal-reviewer, solution-architect).

### 2. Add Agents Incrementally
Don't install all agents at once. Add them as needs arise.

### 3. Use Agent Recommendations
Let ai-first-kick-starter guide your agent selection.

### 4. Consider Project Evolution
As your project grows, revisit agent needs regularly.

### 5. Leverage Agent Collaboration
Agents work best together - use complementary agents via compositions.

## Troubleshooting

### Agents Not Responding
- Verify you restarted your AI assistant
- Check agent installation was successful
- Ask: "What agents do I have available?"

### Wrong Agent Recommendations
- Provide more specific project details
- Use ai-first-kick-starter for tailored advice

### Agent Conflicts
- Some agents overlap in functionality
- Choose the most specific agent for your need
- Check `agents/agent-compositions.yaml` for recommended combinations

## Getting Help

For agent-related questions:
1. Use **ai-first-kick-starter** agent
2. Check agent descriptions in manifest (`release/agent-manifest.json`)
3. Run `python tools/validation/validate-agent-format.py --maturity-report` for catalog overview
4. Review `docs/AGENT-DIRECTORY-STRUCTURE.md` for directory layout

Remember: The right agents can dramatically improve your development workflow. Start with the core three, then expand based on your specific needs!
