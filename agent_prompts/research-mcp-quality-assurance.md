# Deep Research Prompt: MCP Quality Assurance Agent

## Objective

Research and compile the domain knowledge required to build an AI sub-agent
that acts as an MCP Quality Assurance specialist. This agent will audit MCP
server implementations for specification compliance, security best practices,
code quality, production readiness, and developer experience quality.

The resulting agent should be able to conduct comprehensive MCP code reviews,
verify specification compliance, assess security posture, validate production
readiness, and provide actionable quality improvement recommendations when
engaged by the development team.

## Context

This agent is the quality gatekeeper for MCP server development. The existing
agent has solid QA fundamentals but needs depth on latest MCP specification
changes, emerging security threats in AI tool interfaces, production deployment
patterns, and quality metrics specific to AI-facing APIs. The mcp-test-agent
validates functional behavior; this agent audits code quality and compliance.

## Research Areas

### 1. MCP Specification Compliance
- What are the latest MCP specification requirements for servers?
- How should specification compliance be systematically verified?
- What are common specification violations in MCP implementations?
- How do different MCP SDK versions affect compliance requirements?
- What are current patterns for tracking specification changes and updates?

### 2. MCP Security Best Practices
- What are the current security threats specific to MCP servers?
- How should input validation and sanitization be implemented for MCP tools?
- What are the latest patterns for MCP authentication and authorization?
- How do prompt injection risks manifest through MCP tool interfaces?
- What are current practices for securing MCP transport layers?

### 3. Code Quality Standards for MCP
- What are current best practices for MCP server code organization?
- How should error handling be structured in MCP server implementations?
- What are the latest patterns for MCP server testing at the code level?
- How should logging and observability be implemented in MCP servers?
- What are current practices for MCP server documentation and API docs?

### 4. Production Readiness Assessment
- What are current checklists for MCP server production readiness?
- How should MCP server performance be validated before deployment?
- What are the latest patterns for MCP server health checking and monitoring?
- How should graceful shutdown and resource cleanup be implemented?
- What are current practices for MCP server configuration management?

### 5. Developer Experience Quality
- How should MCP tool descriptions be evaluated for clarity and usefulness?
- What are current best practices for MCP server documentation?
- How should error messages be designed for AI client comprehension?
- What are the latest patterns for MCP server onboarding and getting started guides?
- How should MCP server versioning and changelog be managed?

### 6. Quality Metrics & Reporting
- What quality metrics are most meaningful for MCP server implementations?
- How should quality audit reports be structured for different audiences?
- What are the latest patterns for automated quality scoring?
- How do quality gates work in MCP server CI/CD pipelines?
- What are current practices for quality trend tracking over time?

## Synthesis Requirements

After completing the research, synthesize findings into:

1. **Core Knowledge Base**: MCP specification details, security requirements, code quality standards, production readiness criteria the agent must know
2. **Decision Frameworks**: "When reviewing [MCP server aspect], check [criteria] because [reason]" structured guidance
3. **Anti-Patterns Catalog**: Common MCP quality mistakes (poor tool descriptions, missing error codes, insecure defaults, no versioning, inadequate logging)
4. **Tool & Technology Map**: Current QA tools for MCP development (linters, security scanners, specification validators) with selection criteria
5. **Interaction Scripts**: How to respond to "review my MCP server code", "is my server production ready?", "audit my MCP security"

## Agent Integration Points

This agent should:
- **Complement**: mcp-test-agent by providing code-level quality review (test-agent validates behavior, QA reviews implementation quality)
- **Hand off to**: security-architect for comprehensive security architecture review
- **Receive from**: mcp-server-architect for design specifications and requirements
- **Collaborate with**: code-review-specialist on general code quality patterns
- **Never overlap with**: mcp-test-agent on functional testing and client simulation
