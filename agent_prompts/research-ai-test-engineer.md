# Deep Research Prompt: AI Test Engineer Agent

## Objective

Research and compile the domain knowledge required to build an AI sub-agent
that acts as an AI Test Engineer. This agent will design comprehensive test
strategies, implement test automation, create test architectures, ensure
quality through testing best practices, and integrate testing into CI/CD
pipelines for all project types.

The resulting agent should be able to design test pyramids, implement test
automation frameworks, create property-based tests, design contract tests,
and establish quality gates when engaged by the development team.

## Context

This agent is the primary testing expert in the catalog. Testing has evolved
with AI-assisted test generation, mutation testing, visual regression, and
contract testing becoming standard. The existing agent needs depth on modern
testing frameworks, AI-augmented testing, shift-left testing patterns, and
testing strategies for microservices and distributed systems.

## Research Areas

### 1. Modern Testing Strategies (2025-2026)
- What are current best practices for test strategy design (test pyramid, trophy, diamond)?
- How has shift-left testing evolved and what are current implementation patterns?
- What are the latest patterns for risk-based testing and test prioritization?
- How should testing strategies differ for microservices vs monoliths?
- What are current patterns for testing in production (canary, feature flags, chaos)?

### 2. Test Automation Frameworks
- What are the current best test automation frameworks by language/platform?
- How have end-to-end testing tools evolved (Playwright, Cypress, Selenium)?
- What are the latest patterns for API testing automation (Postman, REST Assured, Karate)?
- How should test automation be structured for maintainability at scale?
- What are current patterns for visual regression testing (Percy, Chromatic, BackstopJS)?

### 3. AI-Augmented Testing
- How is AI being used to generate and maintain tests in 2025-2026?
- What are current patterns for AI-assisted test case generation?
- How do mutation testing tools identify weak tests?
- What are the latest patterns for self-healing tests and smart locators?
- How should organizations evaluate AI testing tools effectiveness?

### 4. Contract & Integration Testing
- What are current best practices for contract testing (Pact, Spring Cloud Contract)?
- How should integration tests be designed for microservices architectures?
- What are the latest patterns for consumer-driven contract testing?
- How do schema validation and backward compatibility testing work?
- What are current patterns for testing event-driven architectures?

### 5. Performance & Security Testing
- What are current best practices for integrating performance tests into CI/CD?
- How should security testing (SAST, DAST, SCA) be automated?
- What are the latest patterns for load testing as code (k6, Gatling)?
- How do chaos engineering tests complement traditional testing?
- What are current patterns for accessibility testing automation?

### 6. Test Data & Environment Management
- What are current best practices for test data management and generation?
- How should test environments be provisioned and managed?
- What are the latest patterns for test containers and ephemeral environments?
- How do synthetic data generators compare for testing purposes?
- What are current patterns for database seeding and state management in tests?

### 7. Testing Metrics & Quality Gates
- What testing metrics are most meaningful for quality assurance?
- How should code coverage targets be set and enforced?
- What are the latest patterns for quality gates in CI/CD pipelines?
- How do flaky test detection and management tools work?
- What are current patterns for test reporting and dashboards?

## Synthesis Requirements

After completing the research, synthesize findings into:

1. **Core Knowledge Base**: Testing strategies, automation frameworks, AI testing, contract testing, quality metrics the agent must know
2. **Decision Frameworks**: "When testing [system type] with [constraints], use [approach] because [reason]" structured guidance
3. **Anti-Patterns Catalog**: Common testing mistakes (ice cream cone, flaky tests, no contract tests, testing implementation details, environment coupling)
4. **Tool & Technology Map**: Current testing tools by category with selection criteria
5. **Interaction Scripts**: How to respond to "design our test strategy", "set up test automation", "reduce flaky tests", "implement contract testing"

## Agent Integration Points

This agent should:
- **Complement**: performance-engineer by covering functional testing (performance-engineer covers non-functional)
- **Hand off to**: performance-engineer for load and stress testing
- **Receive from**: solution-architect for testing requirements and quality standards
- **Collaborate with**: devops-specialist on CI/CD test integration
- **Never overlap with**: performance-engineer on performance-specific testing
