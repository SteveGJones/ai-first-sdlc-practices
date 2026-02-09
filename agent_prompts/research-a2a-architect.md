# Deep Research Prompt: A2A Architect Agent

## Objective

Research and compile the domain knowledge required to build an AI sub-agent
that acts as an Agent-to-Agent (A2A) Architect. This agent will design
multi-agent communication protocols, implement inter-agent messaging systems,
orchestrate collaborative AI workflows, and ensure reliable agent coordination
in complex AI systems.

The resulting agent should be able to design A2A communication architectures,
implement agent discovery and coordination, create fault-tolerant multi-agent
workflows, and integrate heterogeneous agent systems when engaged by the
development team.

## Context

This agent is needed because multi-agent AI systems are rapidly becoming the
standard architecture for complex AI applications, with Google's A2A protocol,
MCP, and various orchestration frameworks emerging as key building blocks.
The existing agent has solid multi-agent fundamentals but needs depth on the
Google A2A protocol specification, practical orchestration patterns, reliability
in distributed agent systems, and the evolving multi-agent ecosystem. The
orchestration-architect handles general workflow orchestration; this agent
specializes in agent-to-agent communication and coordination protocols.

## Research Areas

### 1. A2A Protocol & Standards (2025-2026)
- What is the current state of Google's Agent-to-Agent (A2A) protocol?
- How does A2A compare with and complement MCP (Model Context Protocol)?
- What are other emerging agent communication standards?
- How do agent capability discovery and advertisement work in A2A?
- What are the protocol-level security and trust mechanisms?

### 2. Multi-Agent Communication Patterns
- What are current best practices for inter-agent messaging architectures?
- How should agents negotiate capabilities and delegate tasks?
- What are the latest patterns for synchronous vs asynchronous agent communication?
- How do publish-subscribe, request-response, and streaming patterns apply to agents?
- What are current patterns for agent identity and authentication?

### 3. Agent Orchestration Architectures
- What are current best practices for supervisor/worker agent patterns?
- How should hierarchical vs flat agent topologies be designed?
- What are the latest patterns for dynamic agent team composition?
- How do pipeline, scatter-gather, and iterative collaboration patterns work?
- What are current patterns for agent workflow state management?

### 4. Reliability & Fault Tolerance
- What are current best practices for fault tolerance in multi-agent systems?
- How should agent failures, timeouts, and retries be handled?
- What are the latest patterns for agent consensus and conflict resolution?
- How do circuit breaker and bulkhead patterns apply to agent systems?
- What are current patterns for agent system recovery and replay?

### 5. Agent Discovery & Registry
- What are current best practices for agent capability advertisement?
- How should agent registries and service discovery work?
- What are the latest patterns for dynamic agent marketplace architectures?
- How do agents negotiate and establish trust?
- What are current patterns for agent versioning and backward compatibility?

### 6. Heterogeneous Agent Integration
- How should systems integrate agents from different frameworks (LangChain, AutoGen, CrewAI)?
- What are current patterns for bridging MCP and A2A protocols?
- How do wrapper and adapter patterns work for agent interoperability?
- What are the latest patterns for cross-vendor agent communication?
- How should systems handle agents with different capability levels?

### 7. Scaling Multi-Agent Systems
- What are current best practices for scaling multi-agent systems?
- How should agent load balancing and resource allocation work?
- What are the latest patterns for distributed agent deployment?
- How do multi-agent systems handle backpressure and rate limiting?
- What are current patterns for monitoring and observability in multi-agent systems?

## Synthesis Requirements

After completing the research, synthesize findings into:

1. **Core Knowledge Base**: A2A protocols, communication patterns, orchestration architectures, reliability practices the agent must know
2. **Decision Frameworks**: "When designing [multi-agent system type], use [pattern] because [reason]" structured guidance
3. **Anti-Patterns Catalog**: Common A2A mistakes (tight coupling, no failure handling, centralized bottlenecks, protocol mismatch, over-chatty agents)
4. **Tool & Technology Map**: Current multi-agent frameworks, protocols, and tools with selection criteria
5. **Interaction Scripts**: How to respond to "design multi-agent communication", "implement A2A protocol", "orchestrate agent workflows", "scale our agent system"

## Agent Integration Points

This agent should:
- **Complement**: orchestration-architect by specializing in agent-specific protocols (orchestration handles general workflows)
- **Hand off to**: mcp-server-architect for MCP-specific implementation details
- **Receive from**: ai-solution-architect for system-level multi-agent requirements
- **Collaborate with**: agent-developer on agent capability design for A2A participation
- **Never overlap with**: orchestration-architect on non-agent workflow orchestration patterns
