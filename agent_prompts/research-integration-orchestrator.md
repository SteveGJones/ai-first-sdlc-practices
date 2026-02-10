# Deep Research Prompt: Integration Orchestrator Agent

## Objective

Research and compile the domain knowledge required to build an AI sub-agent
that acts as an Integration Orchestrator. This agent will design integration
testing strategies, manage API contract testing, orchestrate cross-service
validation, plan end-to-end testing, and ensure system integration quality
across distributed architectures.

The resulting agent should be able to design integration test architectures,
implement contract testing pipelines, coordinate cross-team testing efforts,
manage test environment dependencies, and validate system integration points
when engaged by the development team.

## Context

This agent specializes in the complex challenge of testing how systems work
together, which has become critical with microservices and distributed architectures.
The existing agent needs depth on modern integration patterns, service virtualization,
contract testing at scale, and testing event-driven and async systems.

## Research Areas

### 1. Integration Testing Architecture (2025-2026)
- What are current best practices for integration test design in distributed systems?
- How should integration tests be structured for microservices architectures?
- What are the latest patterns for testing service-to-service communication?
- How do integration testing strategies differ for synchronous vs async systems?
- What are current patterns for testing database integrations and data flows?

### 2. Contract Testing at Scale
- What are current best practices for consumer-driven contract testing?
- How have Pact and Spring Cloud Contract evolved for large ecosystems?
- What are the latest patterns for GraphQL and gRPC contract testing?
- How should organizations manage contract test governance across teams?
- What are current patterns for bi-directional contract testing?

### 3. Service Virtualization & Mocking
- What are current best practices for service virtualization (WireMock, Mountebank, Hoverfly)?
- How should mock services be managed and versioned?
- What are the latest patterns for recording and replaying API interactions?
- How do service virtualization platforms support complex integration scenarios?
- What are current patterns for simulating third-party API behavior?

### 4. End-to-End Testing Orchestration
- What are current best practices for E2E test design and execution?
- How should E2E tests be coordinated across multiple teams and services?
- What are the latest patterns for test environment provisioning for E2E?
- How do test orchestration platforms manage complex test dependencies?
- What are current patterns for E2E test reliability and maintenance?

### 5. Event-Driven & Async Testing
- What are current best practices for testing message queues and event systems?
- How should event-driven architectures be integration tested?
- What are the latest patterns for testing eventual consistency?
- How do teams test saga patterns and distributed transactions?
- What are current patterns for testing webhook and callback systems?

### 6. Cross-Team Coordination
- How should integration testing responsibilities be distributed across teams?
- What are current patterns for shared integration test environments?
- How do organizations coordinate breaking changes across services?
- What are the latest patterns for integration test governance?
- What are current practices for integration test reporting across teams?

## Synthesis Requirements

After completing the research, synthesize findings into:

1. **Core Knowledge Base**: Integration testing patterns, contract testing, service virtualization, E2E orchestration the agent must know
2. **Decision Frameworks**: "When testing integration between [system types], use [approach] because [reason]" structured guidance
3. **Anti-Patterns Catalog**: Common integration testing mistakes (testing everything E2E, no contract tests, environment coupling, flaky async tests)
4. **Tool & Technology Map**: Current integration testing tools with selection criteria
5. **Interaction Scripts**: How to respond to "design integration testing", "implement contract tests", "test our microservices", "coordinate cross-team testing"

## Agent Integration Points

This agent should:
- **Complement**: ai-test-engineer by specializing in cross-service testing
- **Hand off to**: ai-test-engineer for unit and component-level testing strategy
- **Receive from**: api-architect for API specifications and contract definitions
- **Collaborate with**: devops-specialist on test environment provisioning
- **Never overlap with**: ai-test-engineer on single-service unit/component testing
