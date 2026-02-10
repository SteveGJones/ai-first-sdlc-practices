# Deep Research Prompt: API Architect Agent

## Objective

Research and compile the domain knowledge required to build an AI sub-agent
that acts as an API Architect. This agent will design robust, scalable, and
well-documented APIs across REST, GraphQL, and gRPC paradigms, establish
versioning strategies, implement security patterns, and ensure API quality
through contract testing and OpenAPI specifications.

The resulting agent should be able to evaluate API technology choices,
design resource models and endpoint hierarchies, implement versioning and
deprecation strategies, and establish contract testing practices when engaged
by the development team.

## Context

This agent is needed because API design is a critical discipline that
bridges frontend and backend systems, affects developer experience, and
determines long-term maintainability. The existing agent catalog has
solution-architect for general system design and integration-orchestrator
for testing, but lacks a dedicated API specialist who understands the
nuances of REST maturity levels, GraphQL schema design, gRPC streaming
patterns, and API lifecycle management.

## Research Areas

### 1. REST API Design (Current Best Practices)
- What are the current best practices for REST API design in 2025-2026?
- How has the Richardson Maturity Model been applied in practice?
- What are the latest pagination patterns (cursor-based vs offset, Relay-style connections)?
- How should API filtering, sorting, and field selection be implemented?
- What are the current best practices for bulk operations and batch endpoints?

### 2. GraphQL Architecture (Production Patterns)
- What are the current production-grade GraphQL patterns (Federation v2, schema stitching)?
- How should N+1 query problems be solved with DataLoader and batching?
- What are the current approaches to GraphQL security (query complexity, depth limiting, persisted queries)?
- How should GraphQL subscriptions be implemented for real-time use cases?
- What are the trade-offs between code-first and schema-first approaches?

### 3. gRPC and Protocol Buffers (Modern Usage)
- What are the current best practices for gRPC service design?
- How should gRPC streaming be used (unary, server, client, bidirectional)?
- What tools exist for gRPC API documentation and testing (gRPCurl, Buf, Connect)?
- How does gRPC-Web enable browser-based clients?
- What are the current gRPC load balancing and service mesh patterns?

### 4. API Versioning and Evolution
- What versioning strategies are organizations actually using in production?
- How should breaking changes be detected and communicated?
- What tools exist for API changelog generation and breaking change detection?
- How should API deprecation and sunset policies be implemented (RFC 8594)?
- What are the current best practices for API evolution without versioning?

### 5. API Security (2025-2026)
- What are the current OAuth 2.1 changes and how do they affect API security?
- How should API keys, JWT, and OAuth be combined in practice?
- What are the current rate limiting algorithms and best practices?
- How should API gateway security be configured (AWS API Gateway, Kong, Apigee)?
- What are the latest OWASP API Security Top 10 threats and mitigations?

### 6. OpenAPI and API Documentation
- What is the current state of OpenAPI 3.1 adoption and tooling?
- How should API documentation be generated and maintained?
- What are the current best API developer portal solutions?
- How should API examples and mocking be integrated into documentation?
- What is the current state of AsyncAPI for event-driven APIs?

### 7. Contract Testing and API Quality
- What are the current best practices for consumer-driven contract testing (Pact, Spring Cloud Contract)?
- How should API schema validation be automated in CI/CD?
- What tools detect breaking changes in API schemas?
- How should API monitoring and SLA tracking be implemented?
- What are the current approaches to API governance at scale?

### 8. API Gateway and Integration Patterns
- What are the current API gateway patterns (routing, aggregation, BFF)?
- How should API composition work in microservices architectures?
- What are the current best practices for API rate limiting and throttling?
- How do service meshes interact with API gateways?
- What patterns exist for API-first development workflows?

## Synthesis Requirements

After completing the research, synthesize findings into:

1. **Core Knowledge Base**: REST/GraphQL/gRPC design principles, versioning strategies, security patterns, and documentation standards
2. **Decision Frameworks**: "When building [API type] for [use case], choose [technology] because [reason]" structured guidance
3. **Anti-Patterns Catalog**: Common API design mistakes with before/after examples (chatty APIs, inconsistent naming, missing pagination)
4. **Tool & Technology Map**: API gateways, documentation tools, testing frameworks, and schema validators with selection criteria
5. **Interaction Scripts**: How to respond to "design an API for this service", "should we use GraphQL or REST", "review our API for best practices"

## Agent Integration Points

This agent should:
- **Complement**: backend-architect by focusing on API interface design while backend-architect handles internal architecture
- **Hand off to**: security-architect for deep security threat modeling of API surfaces
- **Receive from**: frontend-architect when client-side API consumption patterns need alignment
- **Collaborate with**: integration-orchestrator on contract testing strategy
- **Never overlap with**: backend-architect on internal service design patterns
