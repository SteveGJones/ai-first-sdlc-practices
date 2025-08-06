<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [AI-First SDLC Agent Discovery Guide](#ai-first-sdlc-agent-discovery-guide)
  - [Overview](#overview)
  - [⚠️ Critical Information](#-critical-information)
  - [Quick Start: Essential Agents](#quick-start-essential-agents)
    - [🚨 Core Agents (Install These First!)](#-core-agents-install-these-first)
  - [Agent Categories](#agent-categories)
    - [🐍 Language-Specific Agents](#-language-specific-agents)
      - [Python Development](#python-development)
      - [Coming Soon](#coming-soon)
    - [🤖 AI/ML Development Agents](#-aiml-development-agents)
    - [🧪 Testing & Quality Agents](#-testing--quality-agents)
    - [📚 Documentation Agents](#-documentation-agents)
    - [📊 Project Management Agents](#-project-management-agents)
    - [🛠️ DevOps & Operations Agents](#-devops--operations-agents)
    - [🔍 Compliance & Analysis Agents](#-compliance--analysis-agents)
    - [🚀 Setup & Maintenance Agents](#-setup--maintenance-agents)
  - [How to Discover Agents](#how-to-discover-agents)
    - [1. During Initial Setup](#1-during-initial-setup)
    - [2. Using ai-first-kick-starter Agent](#2-using-ai-first-kick-starter-agent)
    - [3. By Project Type](#3-by-project-type)
      - [Python API Project](#python-api-project)
      - [AI/ML Application](#aiml-application)
      - [LangChain Project](#langchain-project)
      - [MCP Server Development](#mcp-server-development)
      - [Microservices Architecture](#microservices-architecture)
  - [Agent Installation Process](#agent-installation-process)
    - [Step 1: Identify Needed Agents](#step-1-identify-needed-agents)
    - [Step 2: Install Agents](#step-2-install-agents)
    - [Step 3: Restart AI Assistant](#step-3-restart-ai-assistant)
    - [Step 4: Verify Installation](#step-4-verify-installation)
  - [Agent Collaboration Patterns](#agent-collaboration-patterns)
    - [Design → Implementation → Testing](#design-%E2%86%92-implementation-%E2%86%92-testing)
    - [MCP Server Development Flow](#mcp-server-development-flow)
    - [Production Deployment](#production-deployment)
  - [Finding Agents for Specific Needs](#finding-agents-for-specific-needs)
    - ["I need help with..."](#i-need-help-with)
      - [Performance Issues](#performance-issues)
      - [Security Concerns](#security-concerns)
      - [Documentation](#documentation)
      - [Testing Strategies](#testing-strategies)
      - [Code Quality](#code-quality)
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
  - [Future Agent Development](#future-agent-development)
  - [Getting Help](#getting-help)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# AI-First SDLC Agent Discovery Guide

## Overview
The AI-First SDLC framework provides 32+ specialized AI agents to enhance your development workflow. This guide helps you discover, understand, and install the right agents for your project needs.

## ⚠️ Critical Information
**IMPORTANT**: Installing new agents requires restarting your AI assistant (Claude, GPT, etc.) for them to become active.

## Quick Start: Essential Agents

### 🚨 Core Agents (Install These First!)
Every project should have these critical agents:

1. **sdlc-enforcer** ⭐ CRITICAL
   - Primary guardian of AI-First SDLC compliance
   - Enforces Zero Technical Debt policy
   - Validates framework requirements
   - **When to use**: ALWAYS - from project start

2. **critical-goal-reviewer** ⭐ CRITICAL
   - Quality assurance and constructive challenger
   - Reviews work against original goals
   - Identifies gaps and deviations
   - **When to use**: After completing any significant work

3. **solution-architect** ⭐ CRITICAL
   - System design and architecture expert
   - Reviews technical decisions
   - Guides implementation patterns
   - **When to use**: Before implementing complex features

## Agent Categories

### 🐍 Language-Specific Agents

#### Python Development
- **python-expert**: Python best practices and patterns
- **language-python-expert**: Python-specific SDLC guidance

#### Coming Soon
- JavaScript/TypeScript agents
- Java agents
- Go agents
- Rust agents

### 🤖 AI/ML Development Agents
- **ai-solution-architect**: Enterprise AI system design
- **junior-ai-solution-architect**: Fresh perspectives on AI
- **prompt-engineer**: Prompt optimization expert
- **langchain-architect**: LangChain framework specialist
- **a2a-architect**: Agent-to-Agent communication
- **agent-developer**: Creates new AI agents
- **mcp-server-architect**: Model Context Protocol expert
- **mcp-test-agent**: MCP testing specialist (NEW)
- **mcp-quality-assurance**: MCP quality expert (NEW)

### 🧪 Testing & Quality Agents
- **test-manager**: Test strategy and coordination
- **ai-test-engineer**: AI-specific testing
- **performance-engineer**: Performance optimization
- **integration-orchestrator**: Integration testing

### 📚 Documentation Agents
- **technical-writer**: Clear technical documentation
- **documentation-architect**: Documentation systems

### 📊 Project Management Agents
- **agile-coach**: Agile methodology guidance
- **delivery-manager**: Project delivery coordination
- **project-plan-tracker**: Progress monitoring

### 🛠️ DevOps & Operations Agents
- **devops-specialist**: CI/CD and deployment
- **sre-specialist**: Site reliability engineering
- **github-integration-specialist**: GitHub automation

### 🔍 Compliance & Analysis Agents
- **compliance-auditor**: Compliance checking
- **retrospective-miner**: Retrospective insights
- **framework-validator**: Framework compliance

### 🚀 Setup & Maintenance Agents
- **ai-first-kick-starter**: Post-installation advisor
- **project-bootstrapper**: Project initialization
- **kickstart-architect**: Project structure design

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
- Recommended: python-expert, ai-test-engineer, devops-specialist

#### AI/ML Application
- Core: sdlc-enforcer, critical-goal-reviewer, solution-architect
- Recommended: ai-solution-architect, prompt-engineer, ai-test-engineer

#### LangChain Project
- Core: sdlc-enforcer, critical-goal-reviewer, solution-architect
- Recommended: langchain-architect, prompt-engineer, ai-test-engineer

#### MCP Server Development
- Core: sdlc-enforcer, critical-goal-reviewer, solution-architect
- Recommended: mcp-server-architect, mcp-test-agent, mcp-quality-assurance

#### Microservices Architecture
- Core: sdlc-enforcer, critical-goal-reviewer, solution-architect
- Recommended: integration-orchestrator, devops-specialist, sre-specialist

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

### Design → Implementation → Testing
1. **solution-architect**: Creates design
2. **[language]-expert**: Guides implementation
3. **test-manager**: Plans testing
4. **ai-test-engineer**: Executes tests
5. **critical-goal-reviewer**: Validates against goals

### MCP Server Development Flow
1. **mcp-server-architect**: Designs architecture
2. **mcp-quality-assurance**: Reviews design
3. Implementation occurs
4. **mcp-test-agent**: Tests from AI perspective
5. **mcp-quality-assurance**: Final review

### Production Deployment
1. **devops-specialist**: CI/CD setup
2. **performance-engineer**: Performance validation
3. **sre-specialist**: Production monitoring
4. **compliance-auditor**: Final checks

## Finding Agents for Specific Needs

### "I need help with..."

#### Performance Issues
→ **performance-engineer**: Identifies bottlenecks and optimizations

#### Security Concerns
→ **compliance-auditor**: Security assessments
→ **mcp-quality-assurance**: MCP-specific security

#### Documentation
→ **technical-writer**: User-facing docs
→ **documentation-architect**: Documentation systems

#### Testing Strategies
→ **test-manager**: Overall strategy
→ **ai-test-engineer**: AI-specific testing
→ **integration-orchestrator**: Integration testing

#### Code Quality
→ **critical-goal-reviewer**: Goal alignment
→ **[language]-expert**: Language best practices

## Best Practices

### 1. Start with Core Agents
Always install the three critical agents first.

### 2. Add Agents Incrementally
Don't install all agents at once. Add them as needs arise.

### 3. Use Agent Recommendations
Let ai-first-kick-starter guide your agent selection.

### 4. Consider Project Evolution
As your project grows, revisit agent needs regularly.

### 5. Leverage Agent Collaboration
Agents work best together - use complementary agents.

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

## Future Agent Development

New agents are continuously being developed. Check for updates:
- Ask ai-first-kick-starter about new agents
- Review the agent manifest regularly
- Watch for framework updates

## Getting Help

For agent-related questions:
1. Use **ai-first-kick-starter** agent
2. Check agent descriptions in manifest
3. Ask your AI for agent capabilities
4. Review agent collaboration examples

Remember: The right agents can dramatically improve your development workflow. Start with the core three, then expand based on your specific needs!
