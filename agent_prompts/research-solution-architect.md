# Deep Research Prompt: Solution Architect Agent

## Objective

Research and compile the domain knowledge required to build an AI sub-agent
that acts as a Solution Architect. This agent will design end-to-end system
architectures, make strategic technology decisions, create migration strategies,
and ensure architectural coherence across all system components for projects
ranging from startups to enterprise scale.

The resulting agent should be able to conduct comprehensive architecture reviews,
design scalable distributed systems, create technology evaluation frameworks,
plan cloud migrations, and produce architecture decision records when engaged
by the development team.

## Context

This agent is the keystone architect in the catalog — the one teams engage first
for any significant technical decision. The existing agent catalog has specialized
architects (api-architect, backend-architect, frontend-architect, cloud-architect,
database-architect) but needs a generalist solution architect who ties them all
together, makes cross-cutting decisions, and owns the big picture. The current
agent has reasonable structure but lacks deep methodology and decision frameworks.

## Research Areas

### 1. Modern Architecture Frameworks & Methodologies (2025-2026)
- What are the current best practices for TOGAF, Zachman, and C4 model usage?
- How has the Architecture Tradeoff Analysis Method (ATAM) evolved?
- What are the latest patterns in Architecture Decision Records (ADRs)?
- How do organizations balance architecture governance with agile delivery?
- What role does architecture fitness functions play in evolutionary architecture?

### 2. Distributed Systems Design Patterns
- What are the current best practices for microservices vs modular monoliths (2025-2026)?
- How have event-driven architectures evolved (event sourcing, CQRS, saga patterns)?
- What are the latest patterns for service mesh, sidecar proxies, and API gateways?
- How should architects approach data consistency in distributed systems (eventual vs strong)?
- What are current patterns for distributed transactions and compensation?

### 3. Technology Evaluation & Selection Frameworks
- What structured methodologies exist for technology stack evaluation?
- How should architects weigh build vs buy decisions in 2025-2026?
- What frameworks exist for evaluating open-source vs commercial solutions?
- How do you assess technology risk (maturity, community, vendor lock-in)?
- What are current best practices for proof-of-concept and spike design?

### 4. Cloud-Native Architecture (Current State)
- What are the latest multi-cloud and hybrid cloud architecture patterns?
- How are serverless-first architectures evolving (Lambda, Cloud Functions, Azure Functions)?
- What are current patterns for edge computing and CDN architecture?
- How should architects design for cloud cost optimization from day one?
- What are the latest patterns for platform engineering and internal developer platforms?

### 5. Scalability & Performance Architecture
- What are the current patterns for horizontal vs vertical scaling decisions?
- How should architects design for 10x, 100x, and 1000x growth?
- What are current best practices for caching architectures (multi-tier, CDN, application, database)?
- How do architects design for low-latency systems (P99 targets)?
- What are current patterns for data-intensive application architecture?

### 6. Migration & Modernization Strategies
- What are the latest strategies for monolith-to-microservices migration (strangler fig, branch by abstraction)?
- How should organizations approach legacy system modernization in 2025-2026?
- What are current best practices for database migration and data pipeline modernization?
- How do architects plan API-first modernization strategies?
- What are current patterns for incremental cloud migration (lift-and-shift, re-platform, re-architect)?

### 7. Architecture Quality & Governance
- What are current best practices for architecture review boards and governance?
- How do organizations measure architecture quality (coupling, cohesion, modularity metrics)?
- What tools exist for architecture compliance checking and drift detection?
- How should architects document and communicate architectural decisions?
- What are current patterns for architecture observability and health metrics?

### 8. AI-Augmented Architecture (Emerging)
- How is AI changing architecture design and decision-making?
- What are current patterns for AI/ML system architecture (MLOps, feature stores, model serving)?
- How should architects design systems that integrate LLMs and generative AI?
- What are the architectural implications of AI agents and multi-agent systems?
- How do architects plan for AI governance and responsible AI integration?

## Synthesis Requirements

After completing the research, synthesize findings into:

1. **Core Knowledge Base**: Architecture frameworks, distributed system patterns, scalability principles, and migration strategies the agent must know
2. **Decision Frameworks**: "When designing [system type] with [constraints], recommend [architecture pattern] because [reason]" structured guidance
3. **Anti-Patterns Catalog**: Common architecture mistakes (big ball of mud, distributed monolith, resume-driven development, golden hammer)
4. **Tool & Technology Map**: Current architecture tools (diagramming, fitness functions, compliance checking) with selection criteria
5. **Interaction Scripts**: How to respond to "design our system architecture", "review our current architecture", "help us choose between X and Y technologies"

## Agent Integration Points

This agent should:
- **Coordinate**: All specialized architects (api-architect, backend-architect, frontend-architect, cloud-architect, database-architect) as the senior architect
- **Hand off to**: Specialized architects for domain-deep implementation details
- **Receive from**: Product/business stakeholders for requirements and constraints
- **Collaborate with**: security-architect on security architecture, devops-specialist on deployment architecture
- **Never overlap with**: Individual specialized architects on their specific domain depth
