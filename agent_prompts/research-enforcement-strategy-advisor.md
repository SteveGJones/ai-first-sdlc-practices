# Deep Research Prompt: Enforcement Strategy Advisor Agent

## Objective

Research and compile the domain knowledge required to build an AI sub-agent
that acts as an Enforcement Strategy Advisor. This agent will design behavioral
strategies for SDLC adoption, adapt enforcement approaches to team dynamics,
coach on compliance adoption, and help teams embrace rather than resist
development standards.

## Research Areas

### 1. Behavioral Change in Software Teams (2025-2026)
- What research exists on behavior change in developer teams?
- How do nudge theory and choice architecture apply to SDLC adoption?
- What are the latest patterns for habit formation in development workflows?
- How should enforcement balance strictness with team autonomy?
- What are current patterns for gamification in development compliance?

### 2. Resistance Management
- What are common resistance patterns when enforcing development standards?
- How should organizations address passive resistance to process changes?
- What are the latest patterns for identifying root causes of non-compliance?
- How do cultural factors affect enforcement effectiveness?
- What are current patterns for turning resisters into champions?

### 3. Adoption Strategies
- What are current best practices for rolling out new development standards?
- How should organizations use pilot programs for SDLC adoption?
- What are the latest patterns for incremental enforcement escalation?
- How do carrot vs stick approaches compare for compliance?
- What are current patterns for peer-driven adoption?

### 4. Coaching & Communication
- How should enforcement be communicated to avoid resistance?
- What are current best practices for explaining "why" behind requirements?
- What are the latest patterns for 1-on-1 coaching on compliance?
- How should success stories be used to drive adoption?
- What are current patterns for team-level feedback on compliance?

### 5. Adaptive Enforcement
- How should enforcement adapt to team maturity levels?
- What are current patterns for progressive enforcement (warnings → blocks)?
- How do organizations handle exceptions and waivers effectively?
- What are the latest patterns for context-aware enforcement rules?
- What are current practices for enforcement feedback loops?

## Synthesis Requirements

After completing the research, synthesize findings into:

1. **Core Knowledge Base**: Behavioral change, resistance management, adoption strategies the agent must know
2. **Decision Frameworks**: "When team shows [resistance pattern], apply [strategy] because [reason]"
3. **Anti-Patterns Catalog**: Common enforcement mistakes (all-or-nothing, punitive approach, ignoring context, inconsistency)
4. **Tool & Technology Map**: Current adoption tracking and enforcement tools
5. **Interaction Scripts**: How to respond to "teams resist our standards", "how to enforce without friction", "adapt enforcement to team"

## Agent Integration Points

This agent should:
- **Complement**: sdlc-enforcer by advising on HOW to enforce (enforcer handles WHAT to enforce)
- **Hand off to**: sdlc-enforcer for technical enforcement implementation
- **Receive from**: team-progress-tracker for adoption data
- **Collaborate with**: agile-coach on team dynamics
- **Never overlap with**: sdlc-enforcer on technical enforcement mechanics
