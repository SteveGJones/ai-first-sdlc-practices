# Deep Research Prompt: MCP Test Agent

## Objective

Research and compile the domain knowledge required to build an AI sub-agent
that acts as an MCP Test Agent. This agent will test Model Context Protocol
servers by acting as a naive AI client, validating tool functionality,
testing error handling, assessing usability, running challenge suites, and
providing statistical reliability analysis of MCP server implementations.

The resulting agent should be able to discover and test MCP tools, validate
input schemas, test error paths, measure response reliability, and generate
comprehensive test reports when engaged by the development team.

## Context

This agent is a specialized tester that approaches MCP servers the way a
real AI client would. The existing agent has good testing methodology but
needs depth on modern MCP testing patterns, automated test generation,
statistical validation approaches, and emerging MCP ecosystem testing tools.
The mcp-server-architect designs servers; this agent validates they work
correctly from the client perspective.

## Research Areas

### 1. MCP Protocol Testing (Current State)
- What are current best practices for testing MCP servers against the specification?
- How should conformance testing be structured for MCP implementations?
- What are the latest patterns for MCP transport-layer testing (stdio, SSE, HTTP)?
- How do MCP inspector and debugging tools work?
- What are current practices for MCP protocol version compatibility testing?

### 2. Tool Validation & Schema Testing
- What are current best practices for JSON Schema validation in API testing?
- How should tool input/output schemas be tested exhaustively?
- What are the latest patterns for property-based testing and fuzzing for APIs?
- How should tool descriptions be evaluated for AI client comprehension?
- What are current practices for testing tool composition and chaining?

### 3. Error Handling & Edge Case Testing
- What are current best practices for error path testing in server implementations?
- How should timeout, rate limiting, and resource exhaustion be tested?
- What are the latest patterns for chaos testing of API servers?
- How should concurrent request handling be validated?
- What are current practices for testing graceful degradation?

### 4. Statistical Testing & Reliability Analysis
- What are current best practices for statistical reliability testing of APIs?
- How should response consistency be measured across repeated invocations?
- What are the latest patterns for performance benchmarking of API servers?
- How do confidence intervals and statistical significance apply to API testing?
- What are current practices for regression detection in API behavior?

### 5. AI Client Simulation
- What are current patterns for simulating AI client behavior in testing?
- How should tests model different AI client capabilities and limitations?
- What are the latest patterns for testing AI-facing API usability?
- How should tool discovery and selection be tested from AI perspective?
- What are current practices for testing natural language tool descriptions?

### 6. Test Automation & CI Integration
- What are current best practices for automating MCP server test suites?
- How should MCP tests integrate into CI/CD pipelines?
- What are the latest patterns for test report generation and analysis?
- How do contract testing patterns apply to MCP servers?
- What are current practices for continuous MCP server monitoring?

## Synthesis Requirements

After completing the research, synthesize findings into:

1. **Core Knowledge Base**: MCP testing methodologies, schema validation, statistical analysis, AI client simulation the agent must know
2. **Decision Frameworks**: "When testing [MCP server type], focus on [test category] because [reason]" structured guidance
3. **Anti-Patterns Catalog**: Common MCP testing mistakes (happy path only, no concurrency tests, ignoring tool descriptions, no statistical analysis)
4. **Tool & Technology Map**: Current testing tools (MCP inspector, JSON Schema validators, performance tools) with selection criteria
5. **Interaction Scripts**: How to respond to "test my MCP server", "validate my tools work correctly", "benchmark my server performance"

## Agent Integration Points

This agent should:
- **Complement**: mcp-server-architect by providing client-perspective validation
- **Hand off to**: mcp-quality-assurance for code-level quality review
- **Receive from**: mcp-server-architect for server specifications and expected behaviors
- **Collaborate with**: performance-engineer on performance benchmarking aspects
- **Never overlap with**: mcp-quality-assurance on code review and specification compliance auditing
