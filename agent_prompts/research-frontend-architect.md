# Deep Research Prompt: Frontend Architect Agent

## Objective

Research and compile the domain knowledge required to build an AI sub-agent
that acts as a Frontend Architect. This agent will design component architectures,
establish state management strategies, optimize bundle performance, ensure
accessibility compliance, and guide SSR/SSG implementation decisions for
modern web applications.

The resulting agent should be able to evaluate framework choices, design
component hierarchies with proper state management, optimize Core Web Vitals,
implement WCAG 2.1+ accessibility standards, and architect design systems
when engaged by the development team.

## Context

This agent is needed because frontend architecture has become increasingly
complex with the proliferation of frameworks, rendering strategies, and
performance requirements. The existing agent catalog has ux-ui-architect
for design guidance but lacks a dedicated frontend technical architect who
can make framework-level decisions, design component libraries, and solve
performance challenges.

## Research Areas

### 1. Component Architecture (2025-2026 Patterns)
- What are the current React Server Components patterns and best practices?
- How has the Vue 3 Composition API changed component architecture?
- What are the current Angular signals and zoneless patterns?
- How are Web Components being adopted for framework-agnostic design systems?
- What is the current state of Svelte 5 runes and its architectural implications?

### 2. State Management (Current Landscape)
- What is the current state management landscape (Zustand, Jotai, Pinia, Signals)?
- How has server state management evolved (TanStack Query, SWR, Apollo Client)?
- What are the current patterns for URL state, form state, and ephemeral UI state?
- How should state be architected in React Server Components applications?
- What are the current best practices for optimistic updates and offline-first patterns?

### 3. Rendering Strategies (SSR/SSG/ISR/Streaming)
- What are the current Next.js App Router patterns and best practices?
- How do Astro Islands, Qwik resumability, and partial hydration compare?
- What are the current streaming SSR patterns and their performance impact?
- How should ISR (Incremental Static Regeneration) be used in production?
- What are the current edge rendering patterns (Cloudflare Workers, Vercel Edge)?

### 4. Performance and Core Web Vitals
- What are the 2025-2026 Core Web Vitals thresholds and changes (INP replacing FID)?
- What are the current image optimization best practices (AVIF, responsive images)?
- How should JavaScript be loaded to minimize TBT and INP?
- What are the current font loading strategies and their performance impact?
- What tools exist for continuous performance monitoring in CI/CD?

### 5. Accessibility (WCAG 2.2 and Beyond)
- What are the new WCAG 2.2 success criteria and their implementation requirements?
- How should keyboard navigation be implemented for complex interactive components?
- What are the current best practices for screen reader optimization?
- How should accessibility testing be automated (axe-core, Playwright, Pa11y)?
- What are the current ARIA patterns for common component patterns (modal, combobox, tabs)?

### 6. CSS Architecture and Design Systems
- What are the current CSS architecture approaches (Tailwind, CSS Modules, CSS-in-JS)?
- How are design token systems being implemented (Style Dictionary, Tokens Studio)?
- What are the current patterns for multi-brand theming and dark mode?
- How should design systems be distributed across multiple applications?
- What is the current state of CSS Container Queries, :has(), and layer patterns?

### 7. Build Tools and Developer Experience
- What are the current Vite, Turbopack, and Rspack performance comparisons?
- How should module federation be implemented for micro-frontends?
- What are the current TypeScript strict mode best practices?
- How should monorepo tools (Turborepo, Nx, pnpm workspaces) be configured?
- What are the current CI/CD patterns for frontend deployments?

### 8. Testing Strategies
- What are the current frontend testing best practices (Testing Library, Playwright)?
- How should visual regression testing be implemented?
- What are the current component testing approaches (Storybook, Chromatic)?
- How should E2E tests be structured for large applications?
- What are the current accessibility testing automation patterns?

## Synthesis Requirements

After completing the research, synthesize findings into:

1. **Core Knowledge Base**: Component patterns, state management strategies, rendering approaches, performance budgets, and accessibility requirements
2. **Decision Frameworks**: "When building [app type] with [requirements], choose [framework/pattern] because [reason]" structured guidance
3. **Anti-Patterns Catalog**: Common frontend architecture mistakes (prop drilling, render waterfalls, layout shift, inaccessible modals)
4. **Tool & Technology Map**: Frameworks, bundlers, testing tools, and design system tools with selection criteria
5. **Interaction Scripts**: How to respond to "which framework should we use", "our LCP is too slow", "make our app accessible"

## Agent Integration Points

This agent should:
- **Complement**: ux-ui-architect by implementing technical architecture for design decisions
- **Hand off to**: performance-engineer for deep performance profiling and optimization
- **Receive from**: api-architect when API design affects frontend data fetching patterns
- **Collaborate with**: backend-architect on SSR/BFF patterns and devops-specialist on deployment
- **Never overlap with**: ux-ui-architect on visual design decisions or user research
