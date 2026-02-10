# Deep Research Prompt: Critical Goal Reviewer Agent

## Objective

Research and compile the domain knowledge required to build an AI sub-agent
that acts as a Critical Goal Reviewer. This agent will review completed work
against original goals, identify gaps and deviations, challenge assumptions,
act as a constructive devil's advocate, and ensure implementations truly
satisfy requirements.

The resulting agent should be able to conduct requirement verification,
identify scope gaps, challenge completeness claims, validate acceptance
criteria, and provide structured feedback when engaged by the development team.

## Research Areas

### 1. Requirements Verification & Validation (2025-2026)
- What are current best practices for requirements traceability and verification?
- How should completed work be validated against original specifications?
- What are the latest patterns for acceptance criteria validation?
- How do organizations prevent requirement drift during implementation?
- What are current patterns for automated requirement-to-implementation mapping?

### 2. Review Methodologies
- What are current best practices for structured review techniques (Fagan inspections, walkthroughs)?
- How should reviews balance thoroughness with efficiency?
- What are the latest patterns for checklist-based reviews?
- How do organizations implement peer review for quality assurance?
- What are current patterns for review effectiveness measurement?

### 3. Critical Thinking & Devil's Advocacy
- What are current best practices for constructive criticism in technical reviews?
- How should devil's advocate roles be structured for effectiveness?
- What are the latest patterns for pre-mortem analysis (imagining failure)?
- How do cognitive biases affect technical reviews and how to counter them?
- What are current patterns for red team thinking in software development?

### 4. Gap Analysis Techniques
- What are current best practices for identifying implementation gaps?
- How should edge cases and boundary conditions be systematically checked?
- What are the latest patterns for completeness assessment?
- How do organizations verify non-functional requirements (performance, security, accessibility)?
- What are current patterns for regression impact analysis?

### 5. Feedback Communication
- What are current best practices for giving constructive technical feedback?
- How should review findings be prioritized and communicated?
- What are the latest patterns for actionable feedback versus observations?
- How do organizations build a culture of quality-focused review?
- What are current patterns for tracking feedback resolution?

### 6. Automated Quality Assurance
- How is AI being used for automated quality reviews in 2025-2026?
- What are current patterns for automated specification compliance checking?
- How do formal verification and property-based testing support goal verification?
- What tools support automated requirement coverage analysis?
- What are current patterns for continuous quality monitoring?

## Synthesis Requirements

After completing the research, synthesize findings into:

1. **Core Knowledge Base**: Review techniques, gap analysis, critical thinking, feedback methods the agent must know
2. **Decision Frameworks**: "When reviewing [artifact type], check for [criteria] because [reason]"
3. **Anti-Patterns Catalog**: Common review mistakes (rubber stamping, scope blindness, confirmation bias, focusing on style)
4. **Tool & Technology Map**: Current review and quality tools with selection criteria
5. **Interaction Scripts**: How to respond to "review this against our goals", "validate our implementation", "identify gaps in our work"

## Agent Integration Points

This agent should:
- **Complement**: code-review-specialist by reviewing against goals (code review checks code quality)
- **Hand off to**: relevant specialist agents for identified gaps
- **Receive from**: all agents for post-implementation review requests
- **Collaborate with**: project-plan-tracker on deliverable completion verification
- **Never overlap with**: code-review-specialist on code-level review
