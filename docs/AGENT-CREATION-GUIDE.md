<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Agent Creation Guide](#agent-creation-guide)
  - [Table of Contents](#table-of-contents)
  - [Agent Creation Pipeline](#agent-creation-pipeline)
    - [Recommended Entry Point: pipeline-orchestrator](#recommended-entry-point-pipeline-orchestrator)
    - [Pipeline Paths](#pipeline-paths)
  - [Reference Agent Archetypes](#reference-agent-archetypes)
  - [Research Prompts](#research-prompts)
    - [Research Resources](#research-resources)
    - [Enforcement](#enforcement)
  - [Understanding Agents](#understanding-agents)
    - [What is an Agent?](#what-is-an-agent)
    - [When to Create a New Agent](#when-to-create-a-new-agent)
  - [Agent Anatomy](#agent-anatomy)
    - [1. YAML Frontmatter (Metadata)](#1-yaml-frontmatter-metadata)
    - [2. Content (Instructions)](#2-content-instructions)
  - [Writing Effective Agent Instructions](#writing-effective-agent-instructions)
    - [Core Structure](#core-structure)
    - [Writing Principles](#writing-principles)
      - [1. Be Specific, Not Generic](#1-be-specific-not-generic)
      - [2. Define Clear Boundaries](#2-define-clear-boundaries)
      - [3. Provide Actionable Guidance](#3-provide-actionable-guidance)
      - [4. Include Domain Knowledge](#4-include-domain-knowledge)
      - [5. Specify Your Methodology](#5-specify-your-methodology)
  - [YAML Frontmatter Requirements](#yaml-frontmatter-requirements)
    - [The `name` Field](#the-name-field)
    - [The `description` Field](#the-description-field)
    - [The `examples` Field](#the-examples-field)
    - [The `color` Field](#the-color-field)
  - [Content Best Practices](#content-best-practices)
    - [1. Personality and Voice](#1-personality-and-voice)
    - [2. Specific Tools and Technologies](#2-specific-tools-and-technologies)
    - [3. Decision Frameworks](#3-decision-frameworks)
    - [4. Interaction Patterns](#4-interaction-patterns)
    - [5. Output Formats](#5-output-formats)
  - [Examples and Templates](#examples-and-templates)
    - [Specialist Agent Example](#specialist-agent-example)
  - [Testing Your Agent](#testing-your-agent)
    - [1. Format Validation](#1-format-validation)
    - [2. Content Review Checklist](#2-content-review-checklist)
    - [3. Practical Test](#3-practical-test)
  - [Common Pitfalls](#common-pitfalls)
    - [1. Too Generic](#1-too-generic)
    - [2. Overlapping Responsibilities](#2-overlapping-responsibilities)
    - [3. Missing Context](#3-missing-context)
    - [4. Poor Examples](#4-poor-examples)
    - [5. Formatting Issues](#5-formatting-issues)
  - [Agent Categories](#agent-categories)
    - [Development Agents](#development-agents)
    - [Architecture Agents](#architecture-agents)
    - [Operations Agents](#operations-agents)
    - [Quality Agents](#quality-agents)
  - [Advanced Patterns](#advanced-patterns)
    - [Multi-Phase Agents](#multi-phase-agents)
    - [Delegation Patterns](#delegation-patterns)
  - [Maintenance](#maintenance)
    - [Updating Agents](#updating-agents)
    - [Version Control](#version-control)
  - [Next Steps](#next-steps)
  - [Resources](#resources)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Agent Creation Guide

A comprehensive guide for creating effective AI agents for the AI-First SDLC framework.

## Table of Contents
- [Agent Creation Pipeline](#agent-creation-pipeline)
- [Reference Agent Archetypes](#reference-agent-archetypes)
- [Research Prompts](#research-prompts)
- [Understanding Agents](#understanding-agents)
- [Agent Anatomy](#agent-anatomy)
- [Writing Effective Agent Instructions](#writing-effective-agent-instructions)
- [YAML Frontmatter Requirements](#yaml-frontmatter-requirements)
- [Content Best Practices](#content-best-practices)
- [Examples and Templates](#examples-and-templates)
- [Testing Your Agent](#testing-your-agent)
- [Common Pitfalls](#common-pitfalls)

## Agent Creation Pipeline

The recommended process for creating a new agent follows this pipeline:

```
┌─────────────────────┐
│ 1. IDENTIFY NEED    │  "We need an agent for X"
│    Is there one?    │  Check existing catalog first
└─────────┬───────────┘
          ▼
┌─────────────────────┐
│ 2. CHOOSE ARCHETYPE │  Pick from 5 reference agents
│    (reference agent) │  See templates/reference-agents/
└─────────┬───────────┘
          ▼
┌─────────────────────┐
│ 3. RESEARCH PROMPT  │  Write structured research questions
│    (for deep agents) │  See templates/agent-research-prompt.md
└─────────┬───────────┘
          ▼
┌─────────────────────────────────────────────────┐
│ 4. RESEARCH / DISTILLATION (two paths)          │
│                                                 │
│   Web Research Route        Repo Analysis Route │
│   ┌──────────────────┐   ┌────────────────────┐│
│   │deep-research-agent│   │repo-knowledge-     ││
│   │(web search, CRAAP)│   │distiller (internal ││
│   │                   │   │repos, RELIC eval)  ││
│   └────────┬─────────┘   └──────────┬─────────┘│
│            └──────────┬─────────────┘           │
│                       ▼                         │
│           5-category synthesis document          │
└─────────────────────┬───────────────────────────┘
          ▼
┌─────────────────────┐
│ 5. BUILD AGENT      │  agent-builder constructs from
│    (from synthesis)  │  synthesis + archetype
└─────────┬───────────┘
          ▼
┌─────────────────────┐
│ 6. VALIDATE & TEST  │  Run validation, test with scenarios
│    (quality check)  │  validate-agent-format.py
└─────────────────────┘
```

### Recommended Entry Point: pipeline-orchestrator

The **pipeline-orchestrator** agent automates the entire pipeline end-to-end. It detects your input type (web research request or repository path), routes to the correct research agent, delegates to agent-builder, and handles validation and deployment. Use it as your primary entry point:

- "Create a new kubernetes-security agent" → routes to web research
- "Create an agent from ./my-framework/" → routes to repo analysis
- "Create an agent from our repo with industry best practices" → hybrid route (both)

### Pipeline Paths

**Quick path** (simple agents): Steps 1 → 2 → 5 → 6 (only for agents with minimal domain knowledge needs, e.g., simple coordinators)

**Full path via web research** (MANDATORY for specialists and architects): Steps 1 → 2 → 3 → 4a (deep-research-agent) → 5 → 6

**Full path via repo analysis** (for internal methodology/framework agents): Steps 1 → 2 → 4b (repo-knowledge-distiller) → 5 → 6

> **IMPORTANT**: Research is MANDATORY for any agent classified as a domain expert, specialist, or architect. The pipeline validator enforces this with the `--require-research` flag:
> ```bash
> python tools/validation/validate-agent-pipeline.py production-agent agents/core/your-agent.md --require-research
> ```
> This will FAIL if no corresponding research prompt exists at `agent_prompts/research-your-agent.md`.

## Reference Agent Archetypes

Five annotated reference agents are available in `templates/reference-agents/`. Each demonstrates a distinct agent pattern:

| Archetype | File | Use When |
|-----------|------|----------|
| **Reviewer** | `reference-reviewer.md` | Agent checks quality, validates against criteria, provides feedback |
| **Architect** | `reference-architect.md` | Agent designs systems, evaluates trade-offs, makes decisions |
| **Domain Expert** | `reference-domain-expert.md` | Agent provides deep knowledge in a specific field |
| **Orchestrator** | `reference-orchestrator.md` | Agent coordinates workflows and other agents |
| **Enforcer** | `reference-enforcer.md` | Agent ensures compliance with standards and rules |

See [templates/reference-agents/README.md](../templates/reference-agents/README.md) for detailed descriptions and selection guidance.

## Research Prompts

Research prompts are the foundation of high-quality agents. They ensure agents are grounded in current, accurate domain knowledge rather than generic content.

**Research is MANDATORY for:**
- Domain Expert agents (e.g., database-architect, observability-specialist)
- Architect agents (e.g., security-architect, cloud-architect, api-architect)
- Specialist agents (e.g., container-platform-specialist, performance-engineer)

**Research may be skipped ONLY for:**
- Simple coordinator/orchestrator agents with no deep domain knowledge
- Enforcer agents that encode rules rather than domain expertise
- Meta-agents (e.g., sdlc-coach, project-bootstrapper)

### Research Resources
1. **Template**: `templates/agent-research-prompt.md` — structured template for defining research questions
2. **Examples**: `agent_prompts/research-*.md` — 7 production research prompts you can reference
3. **Guide**: [RESEARCH-PROMPT-GUIDE.md](RESEARCH-PROMPT-GUIDE.md) — detailed guide on executing the research-to-agent pipeline

### Enforcement
The pipeline validator checks for research prompts:
```bash
# Warn if no research prompt exists (default)
python tools/validation/validate-agent-pipeline.py production-agent agents/core/my-agent.md

# FAIL if no research prompt exists (use for specialists/architects)
python tools/validation/validate-agent-pipeline.py production-agent agents/core/my-agent.md --require-research
```

The corresponding research prompt must be at: `agent_prompts/research-{agent-name}.md`

## Understanding Agents

### What is an Agent?

An agent is a specialized AI persona with:
- **Domain expertise** in a specific area
- **Defined personality** and approach
- **Clear boundaries** of responsibility
- **Specific capabilities** and methods

### When to Create a New Agent

Create a new agent when you need:
- Specialized expertise not covered by existing agents
- A distinct approach or methodology
- Domain-specific knowledge and patterns
- Consistent behavior across similar tasks

## Agent Anatomy

Every agent file has two parts:

### 1. YAML Frontmatter (Metadata)
```yaml
---
name: agent-name           # Lowercase, hyphenated
description: Brief description  # Max 150 chars
examples:                  # Usage examples (2-3 recommended)
  - context: When to use this agent
    user: "Example question"
    assistant: "How I'd invoke this agent"
color: blue               # Visual identifier
---
```

### 2. Content (Instructions)
The markdown content that defines the agent's behavior, knowledge, and approach.

## Writing Effective Agent Instructions

### Core Structure

```markdown
You are the [Agent Name], [one-sentence role description].

## Core Competencies
- [Specific expertise area 1]
- [Specific expertise area 2]
- [Tools/technologies you know]

## Approach
[How you analyze and solve problems]
[Your methodology or philosophy]

## Key Capabilities

### [Capability Area 1]
[Detailed description of what you can do]
[Specific techniques or methods]

### [Capability Area 2]
[Another area of expertise]
[How you handle these scenarios]

## When Activated
When a user needs help with [domain], you will:
1. [Specific action 1]
2. [Specific action 2]
3. [Specific action 3]

## Success Metrics
- [How you measure success]
- [Quality standards you maintain]
- [Outcomes you aim for]

## Important Constraints
- [What you DON'T do]
- [Boundaries of your expertise]
- [When to delegate to other agents]
```

### Writing Principles

#### 1. Be Specific, Not Generic
❌ **Bad**: "I help with databases"
✅ **Good**: "I specialize in PostgreSQL performance optimization, query planning, and index strategies"

#### 2. Define Clear Boundaries
❌ **Bad**: "I can help with any coding task"
✅ **Good**: "I focus on API design and RESTful architecture. For UI work, engage the frontend-engineer agent"

#### 3. Provide Actionable Guidance
❌ **Bad**: "I'll review your code"
✅ **Good**: "I'll analyze your code for security vulnerabilities, check for OWASP Top 10 issues, and provide specific remediation steps"

#### 4. Include Domain Knowledge
```markdown
## Domain Expertise
- **MCP Protocol**: I understand the Model Context Protocol specification v1.0
- **Transport Layers**: Expertise in stdio, HTTP, and WebSocket transports
- **Tool Schemas**: JSON-RPC 2.0 and OpenRPC schema definitions
```

#### 5. Specify Your Methodology
```markdown
## My Approach
1. **Analyze** current architecture and requirements
2. **Identify** performance bottlenecks using profiling
3. **Design** optimized solution with benchmarks
4. **Implement** with incremental improvements
5. **Validate** with load testing and metrics
```

## YAML Frontmatter Requirements

### The `name` Field
- Must be lowercase
- Use hyphens for spaces
- Keep it concise and clear
- Examples: `api-designer`, `mcp-server-architect`, `database-optimizer`

### The `description` Field
- Maximum 150 characters
- No special characters or formatting
- Clear, concise explanation of the agent's purpose
- Will be shown in agent selection lists

### The `examples` Field
Must include 2-3 examples showing when to use the agent:

```yaml
examples:
  - context: Building a new REST API
    user: "I need to design a REST API for user management"
    assistant: "I'll engage the api-designer agent to help create a well-structured REST API."
  - context: API performance issues
    user: "My API endpoints are slow"
    assistant: "Let me have the api-designer analyze your endpoints for optimization opportunities."
```

### The `color` Field
Choose from: `blue`, `green`, `purple`, `red`, `cyan`, `yellow`, `orange`

## Content Best Practices

### 1. Personality and Voice

Give your agent a distinct but professional personality:

```markdown
You are the Database Optimizer, a performance-obsessed engineer who believes
every millisecond counts. You approach problems methodically, always measuring
before and after changes. Your motto: "If you can't measure it, you can't improve it."
```

### 2. Specific Tools and Technologies

List specific tools, not categories:

```markdown
## Tools I Use
- **Profiling**: pgBadger, pg_stat_statements, EXPLAIN ANALYZE
- **Monitoring**: Prometheus, Grafana, pg_exporter
- **Testing**: pgbench, HammerDB, sysbench
```

### 3. Decision Frameworks

Include decision-making criteria:

```markdown
## When Choosing Solutions
I evaluate options based on:
1. **Performance impact** - Measured improvement
2. **Maintenance burden** - Long-term complexity
3. **Risk level** - Potential for issues
4. **Resource cost** - CPU, memory, storage trade-offs
```

### 4. Interaction Patterns

Define how the agent works with others:

```markdown
## Collaboration
- **Before me**: solution-architect should define overall structure
- **With me**: work alongside devops-specialist for deployment
- **After me**: monitoring-specialist should track improvements
```

### 5. Output Formats

Specify what the agent produces:

```markdown
## What I Deliver
- Detailed optimization reports with benchmarks
- Specific index recommendations with DDL
- Query rewrites with performance comparisons
- Configuration tuning with justification
```

## Examples and Templates

### Specialist Agent Example

```markdown
---
name: graphql-architect
description: Expert in GraphQL schema design, resolvers, and federation
examples:
  - context: Designing a GraphQL API
    user: "Should I use GraphQL for my new project?"
    assistant: "I'll engage the graphql-architect to evaluate if GraphQL fits your needs."
  - context: GraphQL performance issues
    user: "My GraphQL queries are causing N+1 problems"
    assistant: "Let me have the graphql-architect help you implement DataLoader patterns."
color: purple
---

You are the GraphQL Architect, an expert in designing scalable GraphQL APIs
who understands both the power and pitfalls of graph-based queries.

## Core Competencies
- GraphQL schema design and SDL
- Resolver optimization and DataLoader patterns
- Federation and schema stitching
- Subscription implementations
- Security (depth limiting, query complexity)

## Our Team Approach
The team advocates for "Design-First GraphQL" where we:
1. Model the domain clearly in the schema
2. Design for client needs, not database structure
3. Implement efficient resolvers with proper batching
4. Monitor and optimize based on real usage

## Key Capabilities

### Schema Design
- Type system modeling for complex domains
- Interface and union type strategies
- Custom scalar implementations
- Directive design for cross-cutting concerns

### Performance Optimization
- N+1 query prevention with DataLoader
- Query complexity analysis and limiting
- Caching strategies at multiple levels
- Federation for microservices

### Security
- Depth and complexity limiting
- Rate limiting strategies
- Authentication/authorization patterns
- Field-level permissions

## When Activated
When you need GraphQL expertise, I will:
1. Analyze your domain model and access patterns
2. Design an intuitive, performant schema
3. Implement efficient resolvers with proper error handling
4. Set up monitoring and security controls

## Success Metrics
- Query response time < 100ms for 95th percentile
- No N+1 queries in production
- Schema changes are backward compatible
- Client developers find the API intuitive

## Boundaries
- I focus on GraphQL specifically, not REST API design
- For database optimization, consult database-optimizer
- For authentication systems, engage security-architect
```

## Testing Your Agent

### 1. Format Validation

Use the agent generator tool:
```bash
python tools/agents/agent-generator.py validate your-agent.md
```

### 2. Content Review Checklist

- [ ] Clear, specific role definition
- [ ] Concrete capabilities (not vague promises)
- [ ] Specific tools and methods mentioned
- [ ] Clear boundaries and limitations
- [ ] Interaction patterns with other agents
- [ ] Practical examples in frontmatter
- [ ] Consistent voice and personality

### 3. Practical Test

Try using the agent for a real scenario:
1. Does it have enough context to be helpful?
2. Are the boundaries clear?
3. Would you know when to use this agent vs another?

## Common Pitfalls

### 1. Too Generic
❌ **Problem**: "I help with coding tasks"
✅ **Solution**: Define specific languages, frameworks, and problem types

### 2. Overlapping Responsibilities
❌ **Problem**: Multiple agents could handle the same request
✅ **Solution**: Clear boundaries and "use X agent for Y" guidance

### 3. Missing Context
❌ **Problem**: Agent doesn't know enough to be helpful
✅ **Solution**: Include specific tools, methods, and domain knowledge

### 4. Poor Examples
❌ **Problem**: Examples don't show clear use cases
✅ **Solution**: Real-world scenarios that demonstrate unique value

### 5. Formatting Issues
❌ **Problem**: YAML parsing errors
✅ **Solution**: Use the agent generator tool for validation

## Agent Categories

Organize agents by their primary function:

### Development Agents
- `api-designer` - REST/GraphQL API design
- `database-architect` - Database design and optimization
- `frontend-engineer` - UI/UX implementation
- `backend-engineer` - Server-side development

### Architecture Agents
- `solution-architect` - System design
- `cloud-architect` - Cloud infrastructure
- `security-architect` - Security design

### Operations Agents
- `devops-specialist` - CI/CD and deployment
- `sre-specialist` - Reliability engineering
- `monitoring-specialist` - Observability

### Quality Agents
- `test-engineer` - Testing strategies
- `performance-engineer` - Performance optimization
- `security-auditor` - Security reviews

## Advanced Patterns

### Multi-Phase Agents

Some agents work in phases:

```markdown
## Working Phases

### Phase 1: Discovery
I'll analyze your current system to understand:
- Current architecture
- Performance bottlenecks
- Business constraints

### Phase 2: Design
Based on discovery, I'll propose:
- Optimization strategies
- Implementation plan
- Risk assessment

### Phase 3: Implementation
I'll guide you through:
- Incremental changes
- Testing each optimization
- Measuring improvements
```

### Delegation Patterns

Agents that coordinate with others:

```markdown
## When I Delegate

If you need:
- **Database schema changes** → database-architect
- **API endpoint design** → api-designer
- **Deployment strategy** → devops-specialist

I'll hand off with full context.
```

## Maintenance

### Updating Agents

When updating an agent:
1. Extract to JSON for editing
2. Update content while maintaining structure
3. Regenerate and validate
4. Test with real scenarios

### Version Control

Track agent changes:
- Document significant updates
- Maintain backward compatibility
- Test with existing workflows

## Next Steps

1. **Identify gaps** in current agent coverage
2. **Create JSON template** using the generator tool
3. **Write detailed content** following this guide
4. **Validate and test** the agent
5. **Document** in agent directory README
6. **Share** with team for feedback

## Resources

- [Agent Generator Tool](../tools/agents/README.md)
- [Agent Template Examples](../agents/templates/)
- [YAML Frontmatter Specification](./AGENT-FORMAT-SPEC.md)

---

Remember: Good agents are specialists, not generalists. They have deep expertise in specific domains and clear boundaries of responsibility.
