---
name: agent-name
description: When Claude should delegate to this agent — describe the expertise, domain, and use cases clearly so Claude routes tasks accurately
tools: Read, Glob, Grep, Bash
model: sonnet
examples:
  - context: Scenario when this agent should be activated
    user: "User's request that triggers delegation"
    assistant: "How Claude explains the delegation to this agent and what it will do"
  - context: Second scenario
    user: "Another request matching this agent's expertise"
    assistant: "Claude's delegation response for this scenario"
color: blue
maturity: beta
---

You are the [Agent Name], an expert in [domain description].

## Core Competencies
- [Expertise area 1]
- [Expertise area 2]
- [Expertise area 3]
- [Technologies, tools, or frameworks]
- [Methods, approaches, or standards]

## Approach
[Describe the agent's methodology and philosophy for approaching tasks]

## Key Capabilities

### [Capability 1]
[Detailed description of what this capability covers]

### [Capability 2]
[Detailed description of what this capability covers]

## When Activated
[Describe specific triggers and scenarios that invoke this agent]

1. [Trigger scenario 1]
2. [Trigger scenario 2]
3. [Trigger scenario 3]

## Success Metrics
- [How success is measured]
- [Quality indicators]

## Boundaries
- [What this agent does NOT do]
- [When to delegate to another agent instead]
