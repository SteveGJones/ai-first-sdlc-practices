# Deep Research Prompt: MCP Orchestrator Agent

## Objective

Research and compile the domain knowledge required to build an AI sub-agent
that acts as an MCP Orchestrator. This agent will coordinate multiple MCP
servers, manage tool routing across servers, implement MCP gateway patterns,
handle cross-server workflows, and ensure reliable multi-server MCP operations.

## Research Areas

### 1. MCP Multi-Server Architecture (2025-2026)
- What are current patterns for coordinating multiple MCP servers?
- How should MCP gateways and proxies be designed?
- What are the latest patterns for MCP server discovery and registration?
- How do organizations manage MCP server fleets?
- What are current patterns for MCP tool routing and load balancing?

### 2. MCP Gateway Patterns
- What are current best practices for MCP gateway design?
- How should gateways handle authentication, authorization, and rate limiting?
- What are the latest patterns for MCP request routing and transformation?
- How do MCP proxy and sidecar patterns work?
- What are current patterns for MCP gateway observability?

### 3. Cross-Server Workflows
- What are current patterns for workflows spanning multiple MCP servers?
- How should tool composition across servers be handled?
- What are the latest patterns for cross-server context sharing?
- How do transactions and compensations work across MCP servers?
- What are current patterns for cross-server error handling?

### 4. MCP Fleet Management
- What are current best practices for managing many MCP servers?
- How should MCP server configuration be centralized?
- What are the latest patterns for MCP server health monitoring?
- How do organizations handle MCP server updates and rollbacks?
- What are current patterns for MCP server scaling and auto-scaling?

### 5. Enterprise MCP Patterns
- What are current patterns for enterprise MCP deployment?
- How should MCP integrate with existing enterprise toolchains?
- What are the latest patterns for MCP access control and governance?
- How do multi-tenant MCP environments work?
- What are current patterns for MCP audit and compliance?

### 6. MCP Ecosystem Integration
- How does MCP integrate with A2A and other agent protocols?
- What are current patterns for MCP in multi-agent systems?
- How should MCP servers integrate with knowledge graphs and RAG systems?
- What are the latest patterns for MCP marketplace and catalog management?
- What are current patterns for MCP interoperability testing?

## Synthesis Requirements

After completing the research, synthesize findings into:

1. **Core Knowledge Base**: Multi-server patterns, gateway design, fleet management, enterprise patterns the agent must know
2. **Decision Frameworks**: "When orchestrating [MCP scenario], use [pattern] because [reason]"
3. **Anti-Patterns Catalog**: Common MCP orchestration mistakes (single point of failure, no health checks, tight coupling)
4. **Tool & Technology Map**: Current MCP orchestration tools with selection criteria
5. **Interaction Scripts**: How to respond to "coordinate MCP servers", "design MCP gateway", "manage MCP fleet"

## Agent Integration Points

This agent should:
- **Complement**: mcp-server-architect by handling multi-server coordination
- **Hand off to**: mcp-server-architect for individual server design
- **Receive from**: a2a-architect for agent protocol integration requirements
- **Collaborate with**: orchestration-architect on workflow design patterns
- **Never overlap with**: mcp-server-architect on individual server implementation
