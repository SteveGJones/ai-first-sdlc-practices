# sdlc-team-fullstack

Full-stack development specialists covering frontend, backend, API, DevOps, and more.

## Quick start

```bash
/plugin install sdlc-team-fullstack@ai-first-sdlc
```

Requires `sdlc-core` to be installed first.

## Agents

### Frontend

| Agent | Purpose |
|-------|---------|
| `frontend-architect` | Designs modern frontend architecture including component patterns, state management, performance optimization, accessibility, and SSR/SSG implementations |
| `frontend-security-specialist` | Secures SPAs with XSS prevention, Content Security Policy, OAuth/OIDC flows, Subresource Integrity, and frontend threat modeling |
| `ux-ui-architect` | Designs design systems, conducts WCAG 2.2/3.0 accessibility audits, applies user research methods, and manages design-to-development handoff |
| `mobile-architect` | Architects mobile apps across native iOS/Android, React Native, Flutter, and KMP with platform-specific performance optimization and mobile CI/CD |

### Backend

| Agent | Purpose |
|-------|---------|
| `backend-architect` | Designs distributed backend systems including microservices, event-driven patterns, caching strategies, database selection, and scalability patterns |
| `api-architect` | Designs REST, GraphQL, and gRPC APIs with versioning strategies, security patterns, contract testing, and OpenAPI specifications |
| `data-architect` | Architects enterprise data platforms, lakehouse designs, data mesh patterns, data quality frameworks, and data governance |

### Cross-cutting

| Agent | Purpose |
|-------|---------|
| `devops-specialist` | Designs CI/CD pipelines, GitOps deployment strategies, infrastructure as code, container orchestration, and internal developer platforms |
| `github-integration-specialist` | Configures GitHub Actions workflows, Advanced Security, branch protection, PR automation, and organization governance |
| `integration-orchestrator` | Designs integration testing strategies using contract testing (Pact), service virtualization (WireMock), and E2E test orchestration for multi-service systems |

## When to use this plugin

Install `sdlc-team-fullstack` when your project involves:

- **Web applications** -- React, Next.js, Vue, or other SPA/SSR frameworks
- **Backend services** -- microservices, monoliths, event-driven architectures
- **APIs** -- REST, GraphQL, or gRPC design and integration
- **Mobile apps** -- native or cross-platform mobile development
- **CI/CD and DevOps** -- deployment automation, GitOps, container orchestration
- **Design systems** -- component libraries, accessibility compliance, UX strategy
- **Data platforms** -- warehouses, lakehouses, data quality and governance

## Agent coverage

The 10 agents are organized by layer:

- **Frontend** (4 agents) -- `frontend-architect` and `ux-ui-architect` handle UI architecture and design systems. `frontend-security-specialist` covers client-side security (XSS, CSP, auth flows). `mobile-architect` extends frontend coverage to native and cross-platform mobile apps.
- **Backend** (3 agents) -- `backend-architect` handles distributed system design and microservices. `api-architect` covers REST/GraphQL/gRPC contract design. `data-architect` manages data platforms, warehousing, and governance.
- **Cross-cutting** (3 agents) -- `devops-specialist` and `github-integration-specialist` handle CI/CD, GitOps, and GitHub platform configuration. `integration-orchestrator` designs multi-service testing strategies with contract testing and service virtualization.

## Relationship to other plugins

`sdlc-team-fullstack` covers the core disciplines of product engineering. For
broader architecture concerns (performance engineering, cross-cutting research),
install `sdlc-team-common`. For cloud infrastructure (AWS, GCP, Azure, SRE),
see `sdlc-team-cloud`. For security beyond frontend concerns, see
`sdlc-team-security`.

## Part of the SDLC plugin family

This plugin is one of several team plugins in the AI-First SDLC framework.
Install `sdlc-core` first, then add team plugins matching your project needs.
Run `/sdlc-core:setup-team` to get personalized recommendations.
