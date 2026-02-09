# Deep Research Prompt: Orchestration Architect Agent

## Objective

Research and compile the domain knowledge required to build an AI sub-agent
that acts as an Orchestration Architect. This agent will design multi-agent
coordination systems, implement workflow state machines, create agent handoff
protocols, manage complex AI pipelines, and ensure reliable orchestration
of AI agent systems.

The resulting agent should be able to design orchestration topologies,
implement state machines, create error recovery workflows, optimize agent
coordination, and scale multi-agent systems when engaged by the development team.

## Context

This agent specializes in the mechanics of coordinating multiple AI agents
into coherent workflows. The existing agent has good orchestration fundamentals
but needs depth on modern orchestration frameworks, state machine design
patterns, reliability engineering for agent systems, and emerging orchestration
platforms. The a2a-architect handles communication protocols; this agent
handles workflow design and coordination mechanics.

## Research Areas

### 1. Agent Orchestration Frameworks (2025-2026)
- What are the current orchestration frameworks (LangGraph, AutoGen, CrewAI, Semantic Kernel)?
- How do these frameworks compare in terms of capabilities and trade-offs?
- What are the latest patterns for building custom orchestration systems?
- How do orchestration platforms handle complex branching and parallel execution?
- What are current patterns for orchestration framework selection criteria?

### 2. Workflow State Machine Design
- What are current best practices for designing agent workflow state machines?
- How should state transitions, guards, and actions be modeled?
- What are the latest patterns for hierarchical and parallel state machines?
- How do event-driven orchestration patterns work?
- What are current patterns for state machine persistence and recovery?

### 3. Agent Handoff & Coordination
- What are current best practices for agent-to-agent handoff protocols?
- How should context be transferred between agents during handoffs?
- What are the latest patterns for agent capability matching and delegation?
- How do voting, consensus, and arbitration patterns work in multi-agent systems?
- What are current patterns for human-in-the-loop within agent workflows?

### 4. Error Handling & Recovery
- What are current best practices for error handling in orchestrated agent systems?
- How should retry, fallback, and compensation patterns be implemented?
- What are the latest patterns for dead letter queues and poison message handling?
- How do circuit breakers and bulkheads apply to agent orchestration?
- What are current patterns for orchestration system debugging and troubleshooting?

### 5. Scaling Orchestration Systems
- What are current best practices for scaling multi-agent orchestration?
- How should orchestration handle varying agent response times and throughput?
- What are the latest patterns for distributed orchestration and partitioning?
- How do backpressure and flow control work in agent pipelines?
- What are current patterns for orchestration observability and monitoring?

### 6. Workflow Design Patterns
- What are the canonical workflow patterns for agent orchestration (pipeline, fan-out, map-reduce)?
- How should complex business logic be modeled as agent workflows?
- What are the latest patterns for dynamic workflow composition?
- How do loop, iteration, and convergence patterns work?
- What are current patterns for workflow versioning and migration?

### 7. Orchestration Infrastructure
- What are current best practices for orchestration infrastructure deployment?
- How should orchestration state stores be designed and managed?
- What are the latest patterns for orchestration platform monitoring?
- How do message queues and event buses support orchestration?
- What are current patterns for orchestration cost optimization?

## Synthesis Requirements

After completing the research, synthesize findings into:

1. **Core Knowledge Base**: Orchestration frameworks, state machine patterns, handoff protocols, error handling the agent must know
2. **Decision Frameworks**: "When orchestrating [agent system type] with [requirements], use [pattern] because [reason]" structured guidance
3. **Anti-Patterns Catalog**: Common orchestration mistakes (god orchestrator, tight coupling, no error recovery, synchronous bottlenecks, context loss)
4. **Tool & Technology Map**: Current orchestration tools and frameworks with selection criteria
5. **Interaction Scripts**: How to respond to "design agent workflow", "coordinate multiple agents", "handle agent failures", "scale our orchestration"

## Agent Integration Points

This agent should:
- **Complement**: a2a-architect by handling workflow mechanics (A2A handles communication protocols)
- **Hand off to**: a2a-architect for inter-agent communication protocol decisions
- **Receive from**: ai-solution-architect for orchestration requirements
- **Collaborate with**: context-engineer on context management within workflows
- **Never overlap with**: a2a-architect on agent communication standards and protocols
