# Deep Research Prompt: [AGENT-NAME] Agent

## Objective

<!-- GUIDANCE: Write 1-2 paragraphs describing what this agent should become.
     Be specific about the role, the project context, and the gap this agent fills.
     A good objective answers: What will this agent DO that no existing agent covers? -->

Research and compile the domain knowledge required to build an AI sub-agent
that acts as a [ROLE DESCRIPTION]. This agent will [PRIMARY PURPOSE] for
projects involving [DOMAIN/CONTEXT].

The resulting agent should be able to [KEY CAPABILITY 1], [KEY CAPABILITY 2],
and [KEY CAPABILITY 3] when engaged by the development team.

## Context

<!-- GUIDANCE: Optional but recommended. Describe the specific project or
     situation that motivated this agent's creation. This shapes the research
     toward practical, applicable knowledge rather than generic theory. -->

This agent is needed because [REASON]. The existing agent catalog does not
cover [GAP]. The closest existing agents are [AGENT-1] and [AGENT-2], but
they lack [MISSING CAPABILITY].

## Research Areas

<!-- GUIDANCE: Define 6-10 research areas. Each area should have:
     - A clear topic heading
     - 3-5 targeted questions that guide investigation
     - Questions should progress from foundational to advanced
     Good research areas produce knowledge the agent needs to give SPECIFIC,
     ACTIONABLE advice - not generic platitudes. -->

### 1. [Foundational Domain Knowledge]
- What are the core concepts, terminology, and mental models in [DOMAIN]?
- What distinguishes expert practitioners from novices in this area?
- What are the most common misconceptions or mistakes?

### 2. [Industry Standards & Best Practices]
- What standards, regulations, or frameworks govern [DOMAIN]?
- What are the accepted best practices and why?
- How do these standards apply to software development specifically?

### 3. [Technical Patterns & Implementation]
- What architectural patterns are specific to [DOMAIN]?
- What tools, libraries, or frameworks are commonly used?
- What are the key technical decisions and their trade-offs?

### 4. [Common Failure Modes]
- What are the most frequent mistakes in [DOMAIN] implementations?
- What are the consequences of each failure mode?
- How can these failures be detected early and prevented?

### 5. [Integration & Dependencies]
- How does [DOMAIN] expertise interact with other development disciplines?
- What handoff points exist with other agents (e.g., security, testing, DevOps)?
- What information does this agent need FROM other agents, and what does it provide TO them?

### 6. [Quality & Validation]
- How is quality measured in [DOMAIN]?
- What testing approaches are specific to this domain?
- What metrics indicate success vs. failure?

### 7. [Emerging Trends] (Optional)
- What recent developments are changing practices in [DOMAIN]?
- What should practitioners be preparing for?

## Synthesis Requirements

<!-- GUIDANCE: Describe what the research output should look like.
     This shapes how findings are organized before being turned into an agent. -->

After completing the research, synthesize findings into:

1. **Core Knowledge Base**: The essential facts, rules, and heuristics the agent must know
2. **Decision Frameworks**: Structured approaches for making recommendations (e.g., "when X, recommend Y because Z")
3. **Anti-Patterns Catalog**: Common mistakes the agent should actively detect and warn about
4. **Tool & Technology Map**: Specific tools, libraries, and frameworks the agent should reference
5. **Interaction Scripts**: How the agent should respond to common requests in this domain

## Agent Integration Points

<!-- GUIDANCE: Define how this agent will work WITH the existing team.
     This prevents overlap and ensures smooth collaboration. -->

This agent should:
- **Complement**: [EXISTING-AGENT-1] by providing [SPECIFIC ADDITION]
- **Hand off to**: [EXISTING-AGENT-2] when [CONDITION]
- **Receive from**: [EXISTING-AGENT-3] when [CONDITION]
- **Never overlap with**: [EXISTING-AGENT-4] on [TOPIC]
