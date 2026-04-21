# sdlc-lang-javascript

JavaScript/TypeScript language expert agent for modern JS/TS development, framework selection, build tooling, and runtime optimization.

## Quick start

```bash
/plugin install sdlc-lang-javascript@ai-first-sdlc
```

Requires `sdlc-core` to be installed first.

## Agents

| Agent | Purpose | Model |
|---|---|---|
| `language-javascript-expert` | Expert in modern JavaScript/TypeScript (ES2023+, TypeScript 5.x+), runtime environments (Node.js 22+, Bun, Deno, edge runtimes), build tools (Vite, esbuild, Turbopack, Rspack), frontend frameworks (React 19, Vue 3.4+, Svelte 5, Solid.js, Astro), backend frameworks (Express, Fastify, Hono, NestJS, tRPC), testing (Vitest, Playwright, Cypress), package management (npm, pnpm, Yarn, Bun), and JS security (supply chain attacks, prototype pollution, CSP). | Sonnet |

## When to use this plugin

**Use it when:**
- Configuring TypeScript strict mode, tsconfig.json, or migrating JS to TS
- Selecting between frontend frameworks (React vs Vue vs Svelte vs Solid.js) with decision criteria
- Choosing backend frameworks (Express vs Fastify vs Hono vs NestJS) with performance benchmarks
- Selecting build tools (Vite vs esbuild vs Turbopack vs webpack) for your use case
- Optimizing bundle size (code splitting, tree-shaking, dependency replacement, lazy loading)
- Choosing between runtimes (Node.js vs Bun vs Deno vs edge runtimes)
- Setting up testing with Vitest, Playwright, or Cypress
- Managing packages and lockfile strategies (npm vs pnpm vs Yarn)
- Addressing JavaScript security issues (prototype pollution, supply chain attacks, npm audit)

**Don't use it when:**
- You need frontend architecture decisions (component hierarchy, data flow) -- engage frontend-architect
- You need backend system design or microservices architecture -- engage backend-architect
- You need API design standards (REST/GraphQL patterns) -- engage api-architect
- You need deployment infrastructure -- engage devops-specialist
- You need Python guidance -- engage language-python-expert

## Recommended with

- `sdlc-team-fullstack` for frontend-architect and backend-architect collaboration on architecture decisions
- `sdlc-team-security` for security-specialist collaboration on JavaScript-specific security concerns
