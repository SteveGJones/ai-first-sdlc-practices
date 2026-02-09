# Deep Research Prompt: SDLC Knowledge Curator Agent

## Objective

Research and compile the domain knowledge required to build an AI sub-agent
that acts as an SDLC Knowledge Curator. This agent will maintain a pattern
library of AI-First SDLC best practices, curate proven patterns and success
metrics, provide onboarding guidance for different team types, and serve as
the institutional memory of SDLC lessons learned.

## Research Areas

### 1. Knowledge Management for Development Teams (2025-2026)
- What are current best practices for development knowledge management?
- How should pattern libraries be organized and maintained?
- What are the latest patterns for knowledge curation and taxonomy?
- How do organizations build and maintain engineering handbooks?
- What are current patterns for knowledge search and discovery?

### 2. Pattern Libraries & Catalogs
- What are current best practices for software pattern documentation?
- How should patterns be classified (by domain, complexity, context)?
- What are the latest patterns for pattern relationships and composition?
- How do organizations validate and promote patterns to "proven" status?
- What are current patterns for pattern deprecation and evolution?

### 3. Onboarding & Training Resources
- What are current best practices for developer onboarding programs?
- How should learning paths be designed for different roles and levels?
- What are the latest patterns for self-paced learning in development?
- How do organizations create effective knowledge bases for new hires?
- What are current patterns for onboarding effectiveness measurement?

### 4. Success Metrics & Case Studies
- How should development success stories be documented and shared?
- What metrics best demonstrate SDLC practice effectiveness?
- What are the latest patterns for before/after comparison documentation?
- How do organizations build internal case study libraries?
- What are current patterns for metrics-driven practice recommendations?

### 5. Knowledge Freshness & Maintenance
- How should knowledge bases be kept current and relevant?
- What are current patterns for knowledge aging and expiration?
- How do organizations handle conflicting or outdated knowledge?
- What are the latest patterns for community-driven knowledge curation?
- What are current patterns for automated knowledge quality assessment?

## Synthesis Requirements

After completing the research, synthesize findings into:

1. **Core Knowledge Base**: Knowledge management, pattern libraries, onboarding, metrics the agent must know
2. **Decision Frameworks**: "When team needs [knowledge type], provide [resource] because [reason]"
3. **Anti-Patterns Catalog**: Common knowledge management mistakes (stale knowledge, no taxonomy, tribal knowledge, documentation graveyard)
4. **Tool & Technology Map**: Current knowledge management tools with selection criteria
5. **Interaction Scripts**: How to respond to "find proven patterns for X", "onboard our team", "what are best practices for Y"

## Agent Integration Points

This agent should:
- **Complement**: sdlc-enforcer by providing knowledge (enforcer handles enforcement)
- **Receive from**: all agents for pattern contributions and lessons learned
- **Collaborate with**: enforcement-strategy-advisor on onboarding approaches
- **Never overlap with**: sdlc-enforcer on compliance enforcement
