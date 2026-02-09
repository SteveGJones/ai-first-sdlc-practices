# Research Synthesis: Solution Architect Agent

## Research Methodology

**Date of research**: 2026-02-08
**Total searches executed**: 0 (web tools unavailable)
**Total sources evaluated**: Training knowledge through January 2025
**Sources included**: Established architecture frameworks, industry standards, and practitioner knowledge
**Target agent archetype**: Architect (solution-architect)
**Research areas covered**: 8
**Identified gaps**: 3 (documented in Gaps section)

**Methodology limitation**: Web search and web fetch tools were unavailable during this research session. All findings are derived from training knowledge through January 2025. For recency-sensitive topics (2025-2026 specific practices, emerging AI/ML patterns), confidence levels are adjusted accordingly. Where current web research would be critical, these are explicitly documented as gaps.

The research covers all 8 areas specified in the research prompt with emphasis on decision frameworks, trade-off analysis, and cross-cutting architectural principles appropriate for a generalist solution architect who coordinates specialized architects.

---

## Area 1: Modern Architecture Frameworks & Methodologies (2025-2026)

### Key Findings

#### TOGAF Evolution and Current Usage Patterns

**TOGAF (The Open Group Architecture Framework)** remains widely used in enterprise contexts, particularly TOGAF 9.2 (released 2018) and the Standard (10th edition, 2022). Current best practice emphasizes selective adoption rather than full framework implementation:

- **TOGAF ADM (Architecture Development Method)**: The 8-phase cycle (Preliminary, Vision, Business Architecture, Information Systems Architecture, Technology Architecture, Opportunities & Solutions, Migration Planning, Implementation Governance, Architecture Change Management) is valuable as a mental model but rarely followed rigidly in agile environments.
- **Enterprise Continuum**: The progression from Foundation Architectures → Common Systems Architectures → Industry Architectures → Organization-Specific Architectures provides useful classification.
- **Modern adaptation**: Organizations typically extract specific TOGAF artifacts (capability assessments, gap analysis matrices, migration roadmaps) rather than implementing the full framework. [Confidence: MEDIUM]

**Common critique of TOGAF**: Heavyweight, documentation-intensive, assumes waterfall planning cycles. Works better for large enterprise transformations than product development.

#### C4 Model as the Pragmatic Standard

**C4 Model (Context, Containers, Components, Code)** created by Simon Brown has become the de facto standard for software architecture diagrams in agile organizations:

1. **Level 1 - System Context**: Shows the system in scope and its relationships to users and external systems. Audience: everyone including non-technical stakeholders.
2. **Level 2 - Container**: Shows applications, data stores, microservices that make up the system. A "container" is a separately deployable/executable unit. Audience: technical people inside and outside the team.
3. **Level 3 - Component**: Zooms into an individual container to show components (groupings of related functionality). Audience: architects and developers.
4. **Level 4 - Code**: Optional UML class diagrams or ER diagrams for complex components. Audience: developers working on specific components.

**Why C4 succeeds**: Simple, consistent notation; hierarchical zooming matches how people think; tool-agnostic; generates diagrams that stay synchronized with code. [Confidence: HIGH]

**Integration with agile delivery**: C4 diagrams are living artifacts, updated iteratively as the system evolves. Level 1-2 diagrams are created early; Level 3 emerges during development.

#### Architecture Decision Records (ADRs) - Current Patterns

**ADR structure** follows the template popularized by Michael Nygard:
- **Title**: Numbered, concise description (e.g., "ADR-023: Use PostgreSQL for primary datastore")
- **Status**: Proposed | Accepted | Deprecated | Superseded by ADR-XXX
- **Context**: The forces at play (technical, political, social, project)
- **Decision**: The change we're proposing or have agreed to
- **Consequences**: The resulting context after applying the decision (positive, negative, neutral)

**Evolution in ADR practice**:
- **Lightweight ADRs**: Teams have moved from 3-5 page documents to 1-page records focusing on the decision and rationale, not exhaustive context.
- **ADR tools**: adr-tools (CLI for managing ADRs), log4brains (web UI for browsing), markdown files in `/docs/architecture/decisions/` stored in Git.
- **When to create ADRs**: Significant structural decisions that are costly to reverse (database choice, authentication approach, deployment model, inter-service communication pattern). Not for routine implementation choices.
- **Superseding ADRs**: When reversing a decision, don't delete the original ADR; mark it superseded and reference the new ADR. This maintains decision history. [Confidence: HIGH]

#### Balancing Architecture Governance with Agile Delivery

The **Evolutionary Architecture** approach (Neal Ford, Rebecca Parsons, Patrick Kua) provides the current synthesis:

**Architecture Fitness Functions**: Automated, objective integrity checks that ensure architectural characteristics. Examples:
- Performance fitness function: Reject build if P95 response time > 200ms
- Coupling fitness function: Fail if cyclomatic complexity exceeds threshold
- Security fitness function: Block deployment if CVE scanner finds HIGH severity issues

**Benefits**: Governance becomes automated guardrails rather than manual approval gates. Architecture constraints are encoded in CI/CD pipelines. [Confidence: MEDIUM]

**Lightweight Architecture Review Boards**: Modern ARBs focus on:
- Reviewing significant ADRs (not every technical decision)
- Providing consultative guidance, not approval/rejection
- Meeting weekly for 1 hour maximum
- Time-boxing architecture discussions (15 minutes per topic)

**Architecture Runway**: In SAFe (Scaled Agile Framework) terminology, maintaining a 2-3 sprint ahead technical foundation so teams aren't blocked by infrastructure gaps. This balances emergent design with intentional architectural preparation. [Confidence: MEDIUM]

### Sources
- The Open Group TOGAF Standard (10th Edition): https://pubs.opengroup.org/togaf-standard/
- C4 Model documentation: https://c4model.com/
- Nygard, Michael. "Documenting Architecture Decisions" (blog post, 2011)
- Ford, Neal et al. "Building Evolutionary Architectures" (O'Reilly, 2017)
- ADR GitHub organization: https://adr.github.io/

---

