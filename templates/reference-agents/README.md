# Reference Agent Archetypes

Minimal, annotated agent templates that demonstrate the 5 major agent patterns. Use these as starting points when creating custom agents for your project.

## Quick Selection Guide

| I need an agent that... | Use this archetype |
|---|---|
| Reviews work, validates quality, scores against criteria | [Reviewer](#reviewer) |
| Designs systems, evaluates trade-offs, makes technical decisions | [Architect](#architect) |
| Provides deep knowledge in a specific field or industry | [Domain Expert](#domain-expert) |
| Coordinates multi-step workflows and other agents | [Orchestrator](#orchestrator) |
| Enforces rules, standards, and compliance requirements | [Enforcer](#enforcer) |

## Archetypes

### Reviewer
**File:** `reference-reviewer.md`
**Based on:** critical-goal-reviewer, red-team-security-reviewer
**Pattern:** Acceptance criteria, structured review format, scoring/rating
**Use when:** You need an agent that checks work quality, validates against requirements, or provides structured feedback.

### Architect
**File:** `reference-architect.md`
**Based on:** solution-architect, mcp-server-architect
**Pattern:** Design process steps, tradeoff analysis, technology evaluation
**Use when:** You need an agent that designs systems, evaluates approaches, or makes architectural decisions.

### Domain Expert
**File:** `reference-domain-expert.md`
**Based on:** aerospace-supply-chain-expert, security-cryptography-expert
**Pattern:** Domain vocabulary, regulatory knowledge, industry-specific practices
**Use when:** You need an agent with specialized knowledge in a particular industry or technical domain.

### Orchestrator
**File:** `reference-orchestrator.md`
**Based on:** v3-setup-orchestrator, scenario-choreographer
**Pattern:** Phase-based workflows, decision trees, agent coordination
**Use when:** You need an agent that manages multi-step processes, coordinates other agents, or guides complex workflows.

### Enforcer
**File:** `reference-enforcer.md`
**Based on:** sdlc-enforcer
**Pattern:** Level-based enforcement, rule sets, violation detection, coaching
**Use when:** You need an agent that ensures compliance with standards, validates processes, or enforces rules.

## How to Use

1. Pick the archetype closest to your need
2. Copy the reference agent file
3. Replace all `[CUSTOMIZE]` placeholders with your domain-specific content
4. Remove the `#` annotation comments (or keep them for your own reference)
5. Validate with: `python tools/validation/validate-agent-format.py your-agent.md`
6. Install to `.claude/agents/` and restart your AI assistant

## Combining Archetypes

Some agents blend patterns. Common combinations:
- **Reviewer + Domain Expert**: A reviewer with deep domain knowledge (e.g., security auditor)
- **Architect + Orchestrator**: An architect that coordinates a design workflow
- **Enforcer + Reviewer**: An enforcer that reviews artifacts for compliance

When combining, pick one as primary (determines overall structure) and incorporate elements from the secondary.
