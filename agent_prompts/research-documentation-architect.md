# Deep Research Prompt: Documentation Architect Agent

## Objective

Research and compile the domain knowledge required to build an AI sub-agent
that acts as a Documentation Architect. This agent will design documentation
systems, create information architectures for docs, implement docs-as-code
workflows, establish documentation standards, and ensure comprehensive,
maintainable project documentation.

The resulting agent should be able to design documentation strategies,
implement documentation platforms, create style guides, establish doc
review processes, and measure documentation quality when engaged by the
development team.

## Context

This agent owns the strategic view of documentation while the technical-writer
handles content creation. Documentation has evolved with docs-as-code,
AI-generated docs, interactive documentation, and API documentation platforms.
The existing agent needs depth on modern documentation platforms, docs-as-code
pipelines, documentation-driven development, and AI documentation tools.

## Research Areas

### 1. Documentation Strategy & Architecture (2025-2026)
- What are current best practices for documentation strategy (Diataxis framework)?
- How should documentation be structured (tutorials, how-tos, references, explanations)?
- What are the latest patterns for documentation information architecture?
- How should organizations prioritize documentation efforts?
- What are current patterns for documentation governance and ownership?

### 2. Docs-as-Code Platforms & Tools
- What are current best practices for docs-as-code workflows?
- How do documentation platforms compare (Docusaurus, MkDocs, Astro Starlight, ReadTheDocs)?
- What are the latest patterns for documentation CI/CD pipelines?
- How should documentation versioning align with software versions?
- What are current patterns for documentation testing and validation?

### 3. API Documentation
- What are current best practices for API documentation (OpenAPI, AsyncAPI)?
- How have interactive API documentation tools evolved (Swagger UI, Redocly, Stoplight)?
- What are the latest patterns for API example generation and sandbox testing?
- How should GraphQL and gRPC APIs be documented?
- What are current patterns for API changelog and migration guides?

### 4. AI-Assisted Documentation
- How is AI being used for documentation generation in 2025-2026?
- What are current patterns for AI-generated code documentation?
- How should organizations balance AI-generated vs human-written docs?
- What tools support AI documentation workflows?
- What are current patterns for documentation quality with AI assistance?

### 5. Developer Experience Documentation
- What are current best practices for developer onboarding documentation?
- How should README files and getting-started guides be structured?
- What are the latest patterns for interactive tutorials and playgrounds?
- How do documentation search and navigation affect developer experience?
- What are current patterns for documentation analytics and feedback?

### 6. Documentation Maintenance & Quality
- How should organizations keep documentation up to date?
- What are current patterns for documentation freshness monitoring?
- How do documentation linters and validators work?
- What metrics indicate good documentation quality?
- What are current patterns for documentation review processes?

## Synthesis Requirements

After completing the research, synthesize findings into:

1. **Core Knowledge Base**: Documentation frameworks, platform selection, API docs, maintenance strategies the agent must know
2. **Decision Frameworks**: "When documenting [project type], use [platform/approach] because [reason]" structured guidance
3. **Anti-Patterns Catalog**: Common documentation mistakes (write-once-forget, no structure, developer-hostile, stale docs, undiscoverable)
4. **Tool & Technology Map**: Current documentation tools and platforms with selection criteria
5. **Interaction Scripts**: How to respond to "set up our docs", "document our API", "improve our developer docs", "implement docs-as-code"

## Agent Integration Points

This agent should:
- **Complement**: technical-writer by owning documentation strategy (writer handles content)
- **Hand off to**: technical-writer for content creation and editing
- **Receive from**: solution-architect for system documentation requirements
- **Collaborate with**: api-architect on API documentation strategy
- **Never overlap with**: technical-writer on actual content writing and editing
