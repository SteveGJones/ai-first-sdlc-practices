# Deep Research Prompt: MCP Server Architect Agent

## Objective

Research and compile the domain knowledge required to build an AI sub-agent
that acts as an MCP Server Architect. This agent will design and implement
Model Context Protocol servers, create tool hierarchies, manage resources,
configure transport layers, implement security controls, and optimize MCP
servers for AI application integration.

The resulting agent should be able to design MCP server architectures,
implement tool and resource patterns, configure secure transport, optimize
performance, and integrate MCP servers with AI clients when engaged by
the development team.

## Context

This agent is needed because the Model Context Protocol (MCP) has become a
critical standard for AI tool integration, with Anthropic's specification
driving adoption across the AI ecosystem. The existing agent has solid MCP
knowledge but needs depth on the latest protocol evolution, advanced patterns
for complex tool hierarchies, production deployment strategies, and emerging
MCP ecosystem tools. The ai-solution-architect handles overall AI system
design; this agent is the MCP protocol and server implementation specialist.

## Research Areas

### 1. MCP Protocol Specification (Current State)
- What is the current state of the MCP specification (latest version, transport types)?
- How do the different MCP transport mechanisms work (stdio, SSE, HTTP)?
- What are the protocol's capability negotiation and versioning patterns?
- How do MCP resources, tools, and prompts differ and when to use each?
- What are the protocol-level security features and authentication mechanisms?

### 2. MCP Server Architecture Patterns
- What are current best practices for MCP server design and implementation?
- How should complex tool hierarchies be organized and documented?
- What are the latest patterns for resource management (static, dynamic, templated)?
- How should MCP servers handle concurrent requests and rate limiting?
- What are current patterns for MCP server testing and validation?

### 3. MCP Tool Design
- What are current best practices for tool schema design (JSON Schema)?
- How should tool descriptions be written for optimal AI model understanding?
- What are the latest patterns for tool error handling and validation?
- How do tools handle long-running operations and progress reporting?
- What are current patterns for tool composition and chaining?

### 4. MCP Security & Authentication
- What are current best practices for MCP server security?
- How should authentication and authorization be implemented in MCP servers?
- What are the latest patterns for input validation and sanitization?
- How do MCP servers handle sensitive data and credential management?
- What are current patterns for audit logging and compliance in MCP?

### 5. MCP Server Implementation (Language-Specific)
- What are current best practices for MCP server implementation in Python?
- How do TypeScript/JavaScript MCP server implementations compare?
- What are the latest patterns for Go and Rust MCP server implementations?
- How do MCP SDK libraries differ across languages?
- What are current patterns for MCP server frameworks and scaffolding tools?

### 6. MCP Ecosystem & Integration
- What is the current state of the MCP ecosystem (clients, servers, tools)?
- How do MCP servers integrate with Claude, ChatGPT, and other AI clients?
- What are the latest patterns for MCP server discovery and registration?
- How do MCP gateways and proxies work for enterprise deployment?
- What are current patterns for MCP in multi-agent systems?

### 7. MCP Production Deployment
- What are current best practices for deploying MCP servers in production?
- How should MCP servers handle monitoring, logging, and observability?
- What are the latest patterns for MCP server scaling and load balancing?
- How do containerized MCP server deployments work?
- What are current patterns for MCP server versioning and backward compatibility?

## Synthesis Requirements

After completing the research, synthesize findings into:

1. **Core Knowledge Base**: MCP protocol specification, server architecture patterns, tool design principles, security practices the agent must know
2. **Decision Frameworks**: "When building MCP server for [use case], implement [pattern] because [reason]" structured guidance
3. **Anti-Patterns Catalog**: Common MCP mistakes (overly broad tools, poor descriptions, missing error handling, insecure transports, tight coupling)
4. **Tool & Technology Map**: Current MCP SDKs, frameworks, testing tools, and ecosystem components with selection criteria
5. **Interaction Scripts**: How to respond to "build an MCP server", "design tool hierarchy for my API", "secure my MCP server", "deploy MCP in production"

## Agent Integration Points

This agent should:
- **Complement**: ai-solution-architect by being the MCP protocol expert (architect handles overall AI system design)
- **Hand off to**: mcp-test-agent for MCP server testing and validation
- **Receive from**: ai-solution-architect for system integration requirements
- **Collaborate with**: security-architect on MCP security patterns
- **Never overlap with**: mcp-quality-assurance on testing methodology and quality standards
