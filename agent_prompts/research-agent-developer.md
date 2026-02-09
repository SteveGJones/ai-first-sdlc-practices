# Deep Research Prompt: Agent Developer Agent

## Objective

Research and compile the domain knowledge required to build an AI sub-agent
that acts as an Agent Developer. This agent will design AI agent architectures,
define agent capabilities and personalities, create agent specifications,
implement agent evaluation frameworks, and optimize agent performance for
production deployment.

The resulting agent should be able to design agent architectures from scratch,
craft effective agent personas, define tool and capability sets, implement
agent testing strategies, and optimize agent behavior for specific use cases
when engaged by the development team.

## Context

This agent is the meta-specialist for creating other AI agents. The existing
agent has solid agent design fundamentals but needs depth on modern agent
frameworks, multi-agent orchestration patterns, agent evaluation methodologies,
and the rapidly evolving agent development landscape. The agent-builder
handles the mechanical pipeline of research-to-agent; this agent provides
the architectural vision and design expertise for what makes an effective agent.

## Research Areas

### 1. Agent Architecture Patterns (2025-2026)
- What are the current best practices for AI agent architecture design?
- How have agent frameworks evolved (AutoGen, CrewAI, LangGraph, Semantic Kernel Agents)?
- What are the latest patterns for ReAct, plan-and-execute, and reflection agents?
- How should agents handle tool selection, error recovery, and self-correction?
- What are current patterns for agent memory (working, episodic, semantic)?

### 2. Agent Persona & Instruction Design
- What are current best practices for crafting effective agent personas?
- How should system prompts be structured for consistent agent behavior?
- What are the latest patterns for agent role definition and constraint setting?
- How do personality traits affect agent performance on different tasks?
- What are current practices for balancing agent autonomy with guardrails?

### 3. Multi-Agent Systems
- What are current best practices for multi-agent coordination and communication?
- How should agent hierarchies and delegation patterns be designed?
- What are the latest patterns for agent handoff and context sharing?
- How do supervisor/worker, peer-to-peer, and debate patterns compare?
- What are current patterns for conflict resolution in multi-agent systems?

### 4. Agent Evaluation & Testing
- What are current best practices for evaluating agent performance?
- How should organizations implement agent benchmarks and test suites?
- What are the latest patterns for agent reliability and consistency testing?
- How do red-teaming and adversarial testing work for agents?
- What tools support agent evaluation (AgentBench, GAIA, agent-specific frameworks)?

### 5. Agent Tool Use & Integration
- What are current best practices for defining agent tool sets?
- How should tool descriptions be optimized for agent understanding?
- What are the latest patterns for dynamic tool loading and discovery?
- How do agents handle tool errors, retries, and fallbacks?
- What are current patterns for tool output processing and validation?

### 6. Agent Safety & Reliability
- What are current best practices for agent safety and alignment?
- How should organizations implement agent guardrails and boundaries?
- What are the latest patterns for human-in-the-loop agent workflows?
- How do sandboxing and permission models work for agents?
- What are current patterns for agent audit trails and observability?

### 7. Agent Production Deployment
- What are current best practices for deploying agents in production?
- How should organizations handle agent versioning and rollback?
- What are the latest patterns for agent monitoring and performance tracking?
- How do agent cost management and optimization work?
- What are current patterns for agent scaling and load management?

### 8. Agent Knowledge & Context Management
- What are current best practices for managing agent context windows?
- How should agents handle long conversations and context compression?
- What are the latest patterns for agent knowledge retrieval (RAG for agents)?
- How do agents maintain state across sessions?
- What are current patterns for agent learning and adaptation?

## Synthesis Requirements

After completing the research, synthesize findings into:

1. **Core Knowledge Base**: Agent architecture patterns, persona design, evaluation methods, safety practices the agent must know
2. **Decision Frameworks**: "When building an agent for [use case], design with [pattern] because [reason]" structured guidance
3. **Anti-Patterns Catalog**: Common agent design mistakes (over-broad instructions, no error handling, excessive autonomy, poor tool descriptions, context bloat)
4. **Tool & Technology Map**: Current agent frameworks, evaluation tools, deployment platforms with selection criteria
5. **Interaction Scripts**: How to respond to "design a new agent", "improve my agent's performance", "test my agent", "deploy agents in production"

## Agent Integration Points

This agent should:
- **Complement**: agent-builder by providing architectural vision (agent-builder handles pipeline mechanics, agent-developer provides design expertise)
- **Hand off to**: prompt-engineer for prompt-level optimization within agents
- **Receive from**: solution-architect for system requirements that need agent solutions
- **Collaborate with**: ai-solution-architect on agent system architecture
- **Never overlap with**: agent-builder on the mechanical research-to-agent pipeline process
