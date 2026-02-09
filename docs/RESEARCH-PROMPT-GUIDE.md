<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Research Prompt Guide](#research-prompt-guide)
  - [Why Research Prompts](#why-research-prompts)
  - [When to Use Research Prompts](#when-to-use-research-prompts)
  - [The Research Prompt Format](#the-research-prompt-format)
    - [1. Objective](#1-objective)
    - [2. Context (Optional)](#2-context-optional)
    - [3. Research Areas (6-10)](#3-research-areas-6-10)
    - [4. Synthesis Requirements](#4-synthesis-requirements)
    - [5. Agent Integration Points](#5-agent-integration-points)
  - [How to Execute Research](#how-to-execute-research)
    - [Step 1: Write the Research Prompt](#step-1-write-the-research-prompt)
    - [Step 2: Feed to an AI with Web Search](#step-2-feed-to-an-ai-with-web-search)
    - [Step 3: Review and Supplement](#step-3-review-and-supplement)
    - [Step 4: Synthesize into Knowledge Base](#step-4-synthesize-into-knowledge-base)
    - [Step 5: Customize the Reference Agent](#step-5-customize-the-reference-agent)
  - [Worked Example](#worked-example)
    - [1. Identify Need](#1-identify-need)
    - [2. Choose Archetype](#2-choose-archetype)
    - [3. Create Research Prompt](#3-create-research-prompt)
    - [4. Execute Research](#4-execute-research)
    - [5. Synthesize](#5-synthesize)
    - [6. Customize Reference Agent](#6-customize-reference-agent)
    - [7. Validate](#7-validate)
  - [Tips for Better Research Prompts](#tips-for-better-research-prompts)
  - [Related Resources](#related-resources)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Research Prompt Guide

How to use research prompts to build agents with deep, grounded domain knowledge.

## Why Research Prompts

The difference between a shallow agent and a production-quality agent:

- **Without research**: "You are an expert in API security" — the agent gives generic advice, may hallucinate specifics, lacks depth
- **With research**: Structured investigation produces specific standards (OWASP API Top 10), concrete tools (OWASP ZAP, Burp Suite), real patterns (BOLA, BFLA) — the agent gives grounded, actionable guidance

Research prompts are the framework's answer to the question: "How do I make an agent that actually knows what it's talking about?"

## When to Use Research Prompts

| Agent Type | Research Needed? | Reason |
|-----------|-----------------|--------|
| Domain Expert | **Yes, always** | Deep domain knowledge is the entire value proposition |
| Architect | **Recommended** | Technology-specific decisions benefit from current knowledge |
| Reviewer | **Sometimes** | Only if reviewing against domain-specific criteria |
| Orchestrator | **Rarely** | Process-focused, not knowledge-focused |
| Enforcer | **Sometimes** | If enforcing domain-specific standards |

## The Research Prompt Format

Every research prompt follows this structure (template at `templates/agent-research-prompt.md`):

### 1. Objective
What the agent should become and what gap it fills. Be specific about the role and the project context.

### 2. Context (Optional)
The specific situation that motivated the agent. Shapes research toward practical, applicable knowledge.

### 3. Research Areas (6-10)
Structured questions organized by topic. Each area has 3-5 targeted questions that progress from foundational to advanced. This is the core of the research prompt.

### 4. Synthesis Requirements
What the research output should look like: knowledge base, decision frameworks, anti-patterns, tools, interaction scripts.

### 5. Agent Integration Points
How the agent will work with existing agents: complements, hands off to, receives from, never overlaps with.

## How to Execute Research

### Step 1: Write the Research Prompt
Copy `templates/agent-research-prompt.md` and fill in all `[CUSTOMIZE]` sections. Aim for 6-10 research areas with 3-5 questions each.

### Step 2: Feed to an AI with Web Search
Use an AI tool that has web search capability (Claude with web search, ChatGPT with browsing, Perplexity, etc.). Provide the complete research prompt and ask for comprehensive findings organized by research area.

### Step 3: Review and Supplement
The AI research output will cover breadth. Supplement with:
- Official documentation for specific standards (e.g., OWASP, NIST)
- Industry-specific resources you know are authoritative
- Team-specific practices or constraints

### Step 4: Synthesize into Knowledge Base
Organize findings into the 5 synthesis categories:

1. **Core Knowledge Base**: Facts, rules, heuristics → becomes the agent's "Domain Knowledge" section
2. **Decision Frameworks**: "When X, recommend Y because Z" → becomes decision trees in the agent
3. **Anti-Patterns Catalog**: Common mistakes → becomes the "Common Mistakes" section
4. **Tool & Technology Map**: Specific tools → becomes technology references in the agent
5. **Interaction Scripts**: Common requests → becomes "When Activated" workflows

### Step 5: Customize the Reference Agent
Take the appropriate reference archetype from `templates/reference-agents/` and fill `[CUSTOMIZE]` placeholders with synthesized research findings.

## Worked Example

Here's the full pipeline for creating an "API Security Expert" agent:

### 1. Identify Need
The team builds REST APIs but has no dedicated security review agent. The general security agent exists but lacks API-specific depth.

### 2. Choose Archetype
This is a **Domain Expert** (deep field knowledge) with elements of a **Reviewer** (evaluates work against criteria). Primary archetype: Domain Expert.

### 3. Create Research Prompt
See `agent_prompts/example-api-security-expert.md` for the complete research prompt. It defines 7 research areas covering authentication, OWASP API Top 10, input validation, rate limiting, transport security, threat modeling, and monitoring.

### 4. Execute Research
Feed the research prompt to an AI with web search. Here's a concrete snippet of what the research output looks like for Research Area #2 (OWASP API Security Top 10):

```
## Research Area 2: OWASP API Security Top 10

The OWASP API Security Top 10 (2023) identifies these critical vulnerabilities:

1. **API1:2023 - Broken Object Level Authorization (BOLA)**
   - Most prevalent API vulnerability. Occurs when API endpoints expose
     object IDs and don't verify the requesting user has permission.
   - Detection: Test by substituting object IDs in requests (e.g., change
     /api/users/123/orders to /api/users/456/orders while authenticated as user 123).
   - Mitigation: Implement authorization checks at the object level for every
     endpoint that receives an object ID. Use random, non-sequential UUIDs.

2. **API2:2023 - Broken Authentication**
   - Weak authentication mechanisms or improper token handling.
   - Common mistakes: no rate limiting on login, tokens that don't expire,
     credentials in URL parameters, missing token validation.
   - Mitigation: Use established auth frameworks (OAuth 2.0 with PKCE for SPAs),
     enforce token expiration, implement refresh token rotation.

3. **API3:2023 - Broken Object Property Level Authorization**
   - Mass assignment: API accepts more properties than intended.
   - Example: PUT /api/users/me with {"name": "John", "role": "admin"} succeeds
     because the endpoint doesn't filter which properties can be updated.
   - Mitigation: Explicitly define allowed properties per endpoint. Use DTOs
     or serialization allowlists. Never bind request bodies directly to models.
[...]
```

The full research output for all 7 areas would be 15-30 pages. The key is that it contains **specific vulnerability names, concrete detection methods, and actionable mitigations** — not generic advice.

### 5. Synthesize
Organize into the 5 categories. The "Core Knowledge Base" (OWASP Top 10, auth patterns, rate limiting algorithms) becomes the agent's Domain Knowledge sections. The "Anti-Patterns Catalog" (mass assignment, BOLA, weak auth) becomes the "Common Mistakes" section. The "Tool & Technology Map" (Burp Suite, OWASP ZAP, helmet.js) becomes technology references.

### 6. Customize Reference Agent
Copy `templates/reference-agents/reference-domain-expert.md`, replace all `[CUSTOMIZE]` placeholders with the synthesized findings. The result is a domain expert with real, specific API security knowledge.

### 7. Validate
```bash
python tools/validation/validate-agent-format.py agents/security/api-security-expert.md
```

## Tips for Better Research Prompts

1. **Be specific with questions**: "What are the OWASP API Top 10?" beats "What are API security risks?"
2. **Progress from foundational to advanced**: Start with "what is X" before "how to handle edge case Y"
3. **Include comparison questions**: "How does X differ between REST and GraphQL?" produces richer knowledge
4. **Ask for concrete examples**: "What does a vulnerable vs. secure implementation look like?"
5. **Define integration points**: Knowing what OTHER agents handle prevents overlap

## Related Resources

- [Research Prompt Template](../templates/agent-research-prompt.md)
- [Example Research Prompts](../agent_prompts/)
- [Reference Agent Archetypes](../templates/reference-agents/)
- [Agent Creation Guide](AGENT-CREATION-GUIDE.md)
