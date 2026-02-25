<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [AI Agent Installation Guide](#ai-agent-installation-guide)
  - [⚠️ Critical Reminder](#-critical-reminder)
  - [Quick Installation Steps](#quick-installation-steps)
    - [1. Identify Needed Agents](#1-identify-needed-agents)
    - [2. Install Agents](#2-install-agents)
    - [3. Restart Your AI Assistant](#3-restart-your-ai-assistant)
    - [4. Verify Installation](#4-verify-installation)
  - [Platform-Specific Notes](#platform-specific-notes)
    - [Claude (Anthropic)](#claude-anthropic)
    - [GPT (OpenAI)](#gpt-openai)
    - [Other Platforms](#other-platforms)
  - [Common Issues](#common-issues)
    - [Agent Not Responding](#agent-not-responding)
    - [Multiple Agents Needed](#multiple-agents-needed)
  - [Best Practices](#best-practices)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# AI Agent Installation Guide

## ⚠️ Critical Reminder
**Installing new agents requires restarting your AI assistant (Claude, GPT, etc.)**

## Quick Installation Steps

### 1. Identify Needed Agents
- Run setup-smart.py for initial recommendations
- Use ai-first-kick-starter agent for ongoing discovery
- Refer to docs/AGENT-DISCOVERY-GUIDE.md for details

### 2. Install Agents
Follow your AI platform's specific instructions for agent installation.

### 3. Restart Your AI Assistant
**MANDATORY**: Close and reopen your AI chat/session for agents to activate.

### 4. Verify Installation
Ask: "What specialized agents are available?"

## Platform-Specific Notes

### Claude (Anthropic)
- Agents are configured through the platform
- Restart means starting a new conversation

### GPT (OpenAI)
- Custom instructions or GPTs may be used
- Restart means refreshing the session

### Other Platforms
- Consult platform documentation
- The key is ensuring the AI reloads its configuration

## Common Issues

### Agent Not Responding
✓ Did you restart after installation?
✓ Was the agent properly installed?
✓ Try asking explicitly for the agent

### Multiple Agents Needed
✓ Install all needed agents first
✓ Then perform ONE restart
✓ All agents will be available

## Best Practices

1. **Install Core Agents First**
   - sdlc-enforcer
   - critical-goal-reviewer
   - solution-architect

2. **Batch Installations**
   - Install multiple agents at once
   - Restart only once after all installations

3. **Test After Restart**
   - Verify each agent responds
   - Test agent interactions

4. **Document Your Agents**
   - Keep a list of installed agents
   - Note when they were installed
   - Track which are actively used

Remember: The restart is crucial - agents won't work without it!
