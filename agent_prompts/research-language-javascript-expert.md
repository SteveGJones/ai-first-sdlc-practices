# Deep Research Prompt: JavaScript/TypeScript Expert Agent

## Objective

Research and compile the domain knowledge required to build an AI sub-agent
that acts as a JavaScript/TypeScript Expert. This agent will provide deep
JS/TS language expertise, recommend idiomatic patterns, guide framework
selection, optimize build tooling, and ensure JavaScript ecosystem best practices.

## Research Areas

### 1. Modern JavaScript/TypeScript (2025-2026)
- What are current TypeScript best practices for 5.x+ features?
- How have ECMAScript proposals evolved (decorators, records/tuples, pattern matching)?
- What are the latest patterns for TypeScript project configuration?
- How should TypeScript strict mode and type safety be configured?
- What are current patterns for monorepo management (turborepo, nx, lerna)?

### 2. Runtime & Build Tooling
- How do Node.js, Deno, and Bun compare in 2025-2026?
- What are current best practices for build tools (Vite, esbuild, Turbopack, Rspack)?
- What are the latest patterns for module systems (ESM vs CJS)?
- How should bundling and tree-shaking be optimized?
- What are current patterns for dev server and HMR configuration?

### 3. Frontend Frameworks
- How do React, Vue, Svelte, and Solid compare in 2025-2026?
- What are the latest patterns for server components and streaming SSR?
- How have meta-frameworks evolved (Next.js, Nuxt, SvelteKit, Astro)?
- What are current patterns for state management (signals, stores, atoms)?
- What are current patterns for component library development?

### 4. Backend JavaScript
- What are current best practices for Node.js backend development?
- How do Express, Fastify, Hono, and Elysia compare?
- What are the latest patterns for TypeScript API development?
- How should Node.js handle database access (Prisma, Drizzle, TypeORM)?
- What are current patterns for Node.js performance optimization?

### 5. Testing & Quality
- What are current best practices for JS/TS testing (Vitest, Jest, Playwright)?
- How should TypeScript type testing work (tsd, expect-type)?
- What are the latest patterns for ESLint and Biome configuration?
- How do snapshot testing and visual testing patterns work?
- What are current patterns for JS/TS code coverage and quality gates?

### 6. Package Management & Security
- How do npm, pnpm, yarn, and bun compare for package management?
- What are current best practices for npm package security?
- What are the latest patterns for publishing and maintaining npm packages?
- How should lockfiles and dependency updates be managed?
- What are current patterns for JavaScript supply chain security?

## Synthesis Requirements

After completing the research, synthesize findings into:

1. **Core Knowledge Base**: JS/TS patterns, frameworks, tooling, optimization the agent must know
2. **Decision Frameworks**: "When building [JS project type], use [tool/framework] because [reason]"
3. **Anti-Patterns Catalog**: Common JS mistakes (callback hell, memory leaks, any type abuse, bundle bloat)
4. **Tool & Technology Map**: Current JS/TS ecosystem tools with selection criteria
5. **Interaction Scripts**: How to respond to "set up TypeScript project", "choose frontend framework", "optimize our bundle"

## Agent Integration Points

This agent should:
- **Complement**: frontend-architect with JS/TS implementation expertise
- **Hand off to**: frontend-architect for framework-agnostic architecture decisions
- **Collaborate with**: backend-architect on Node.js backend patterns
- **Never overlap with**: frontend-architect on general frontend architecture
