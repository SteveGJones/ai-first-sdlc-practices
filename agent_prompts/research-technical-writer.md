# Deep Research Prompt: Technical Writer Agent

## Objective

Research and compile the domain knowledge required to build an AI sub-agent
that acts as a Technical Writer. This agent will create clear technical
documentation, write user guides, craft API documentation, produce tutorials,
and ensure all written content is accurate, accessible, and effective.

The resulting agent should be able to write technical documentation across
formats, adapt tone for different audiences, create effective tutorials,
write clear error messages, and edit for clarity and accuracy when engaged
by the development team.

## Context

This agent creates the actual content while the documentation-architect
handles strategy. Technical writing has evolved with plain language movements,
inclusive writing standards, and AI-augmented writing tools. The existing
agent needs depth on modern technical writing practices, writing for
developers, content design principles, and writing for accessibility.

## Research Areas

### 1. Modern Technical Writing (2025-2026)
- What are current best practices for technical writing in software?
- How has the Google developer documentation style guide evolved?
- What are the latest plain language standards and how to apply them?
- How should technical content be structured for scanability?
- What are current patterns for inclusive and accessible writing?

### 2. Writing for Developers
- What are current best practices for writing developer documentation?
- How should code examples be structured and presented?
- What are the latest patterns for tutorial and how-to guide design?
- How should error messages and system notifications be written?
- What are current patterns for writing CLI documentation and help text?

### 3. Content Design & UX Writing
- What are current best practices for UX writing and microcopy?
- How should interface text, tooltips, and labels be crafted?
- What are the latest patterns for conversational UI writing?
- How do content design principles improve technical documentation?
- What are current patterns for writing for internationalization?

### 4. API & Reference Documentation
- What are current best practices for writing API reference documentation?
- How should parameters, responses, and error codes be documented?
- What are the latest patterns for writing API guides and tutorials?
- How should changelog and migration documentation be structured?
- What are current patterns for writing SDK documentation?

### 5. Editing & Quality
- What are current best practices for technical editing?
- How should documentation be reviewed for accuracy and clarity?
- What are the latest patterns for style guide enforcement?
- How do technical writing linters work (Vale, write-good)?
- What are current patterns for documentation localization?

### 6. AI-Augmented Writing
- How are technical writers using AI tools effectively in 2025-2026?
- What are current patterns for AI-assisted drafting and editing?
- How should AI-generated content be reviewed and validated?
- What tools support AI-augmented technical writing?
- What are current best practices for maintaining voice with AI assistance?

## Synthesis Requirements

After completing the research, synthesize findings into:

1. **Core Knowledge Base**: Writing techniques, style standards, content design, editing practices the agent must know
2. **Decision Frameworks**: "When writing [content type] for [audience], use [approach] because [reason]" structured guidance
3. **Anti-Patterns Catalog**: Common writing mistakes (jargon overuse, passive voice, wall of text, assumed knowledge, outdated examples)
4. **Tool & Technology Map**: Current writing and editing tools with selection criteria
5. **Interaction Scripts**: How to respond to "write documentation for X", "improve this doc", "create a tutorial", "write error messages"

## Agent Integration Points

This agent should:
- **Complement**: documentation-architect by creating content (architect handles strategy)
- **Hand off to**: documentation-architect for platform and structure decisions
- **Receive from**: all specialist agents for domain-specific content needs
- **Collaborate with**: ux-ui-architect on interface text and content design
- **Never overlap with**: documentation-architect on documentation strategy and platform selection
