# sdlc-team-docs

Technical writing and documentation architecture agents for projects that need documentation strategy, content creation, and docs-as-code pipelines.

## Quick start

```bash
/plugin install sdlc-team-docs@ai-first-sdlc
```

Requires `sdlc-core` to be installed first.

## Agents

| Agent | Purpose | Model |
|---|---|---|
| `documentation-architect` | Designs documentation systems, selects platforms (Docusaurus, MkDocs, Astro Starlight), establishes docs-as-code pipelines, architects API documentation (OpenAPI/AsyncAPI), implements quality frameworks (freshness monitoring, link checking, prose linting), and creates information architecture using the Diataxis framework. **Designs the system; does not write content.** | Sonnet |
| `technical-writer` | Creates clear, accurate, user-centered documentation across all formats: tutorials, how-to guides, API references, error messages, CLI help text, and UX microcopy. Applies plain language principles (WCAG 2.2 readability), Google developer documentation style guide, and accessibility-first writing. Tests all code examples. **Creates content; does not design the platform.** | Sonnet |

## When to use this plugin

**Use it when:**
- You need a documentation platform designed from scratch (documentation-architect)
- You're creating developer-facing documentation: tutorials, API references, SDK guides (technical-writer)
- You need docs-as-code CI/CD pipelines with validation, linting, and automated deployment (documentation-architect)
- Error messages, CLI help text, or UX microcopy need rewriting for clarity (technical-writer)
- You're migrating from scattered documentation (Confluence, Notion, GitHub READMEs) to a unified system (documentation-architect)
- You need API documentation architecture with OpenAPI/AsyncAPI specifications (documentation-architect)

**Don't use it when:**
- You need domain-specific technical expertise (engage the relevant specialist agent instead)
- You need frontend implementation of a documentation site (engage frontend-architect)
- You need deployment infrastructure for documentation hosting (engage devops-specialist)

## How the two agents work together

The documentation-architect designs the system: platform selection, information architecture, CI/CD pipelines, quality frameworks, and governance models. The technical-writer creates the content that lives inside that system: tutorials, guides, references, and microcopy. Hand off system design questions to the architect; hand off content creation to the writer.

## Recommended with

- `sdlc-team-common` for solution-architect and API-architect collaboration
- `sdlc-team-fullstack` for frontend-architect and devops-specialist collaboration on documentation site implementation and deployment
