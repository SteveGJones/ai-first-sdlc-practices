# Deep Research Prompt: LangChain Architect Agent

## Objective

Research and compile the domain knowledge required to build an AI sub-agent
that acts as a LangChain/LangGraph Architect. This agent will design LLM
application architectures using the LangChain ecosystem, implement complex
agent workflows with LangGraph, create RAG pipelines, and optimize production
deployments of LangChain-based applications.

The resulting agent should be able to design chain architectures, implement
LangGraph state machines, configure memory systems, integrate tools, and
deploy production LangChain applications when engaged by the development team.

## Context

This agent is needed because LangChain/LangGraph has become the dominant
framework for LLM application development, with frequent breaking changes
and evolving best practices. The existing agent has good LangChain fundamentals
but needs depth on latest LangGraph patterns, LCEL (LangChain Expression
Language), LangSmith observability, production deployment patterns, and the
rapidly evolving ecosystem. The ai-solution-architect handles general AI
architecture; this agent is the LangChain ecosystem specialist.

## Research Areas

### 1. LangChain Core Architecture (2025-2026)
- What is the current state of LangChain core library (latest version, API changes)?
- How has LangChain Expression Language (LCEL) evolved and what are current best practices?
- What are the latest patterns for chain composition and routing?
- How should output parsers and structured output be handled in current LangChain?
- What are current patterns for callback systems and event handling?

### 2. LangGraph Agent Architecture
- What are current best practices for LangGraph state machine design?
- How should multi-agent systems be implemented in LangGraph?
- What are the latest patterns for conditional routing and branching in LangGraph?
- How do human-in-the-loop patterns work in LangGraph?
- What are current patterns for LangGraph persistence and checkpointing?

### 3. RAG Implementation with LangChain
- What are current best practices for RAG architectures using LangChain?
- How should document loaders and text splitters be configured?
- What are the latest patterns for embedding and retrieval optimization?
- How do LangChain vector store integrations compare?
- What are current patterns for advanced RAG (multi-query, self-query, corrective RAG)?

### 4. LangSmith & Observability
- What are current best practices for LangSmith tracing and monitoring?
- How should evaluation and testing work with LangSmith?
- What are the latest patterns for prompt management in LangSmith?
- How do LangSmith datasets and experiments support iteration?
- What are current patterns for production monitoring with LangSmith?

### 5. Tool & Integration Patterns
- What are current best practices for tool creation and integration in LangChain?
- How should custom tools be designed for optimal agent performance?
- What are the latest patterns for API chain integration?
- How do LangChain community integrations work?
- What are current patterns for database and filesystem tool usage?

### 6. Production Deployment
- What are current best practices for deploying LangChain apps (LangServe, FastAPI)?
- How should LangChain applications handle scaling and load balancing?
- What are the latest patterns for streaming responses in LangChain?
- How should error handling and retry logic be implemented?
- What are current patterns for LangChain application cost management?

### 7. Migration & Version Management
- How should organizations handle LangChain version migrations?
- What are the breaking changes between major LangChain versions?
- What are current patterns for maintaining backward compatibility?
- How should deprecated features be identified and replaced?
- What are current migration guides for LCEL and LangGraph adoption?

## Synthesis Requirements

After completing the research, synthesize findings into:

1. **Core Knowledge Base**: LangChain architecture patterns, LangGraph design, RAG implementation, production deployment the agent must know
2. **Decision Frameworks**: "When building [LLM app type] with LangChain, use [pattern/component] because [reason]" structured guidance
3. **Anti-Patterns Catalog**: Common LangChain mistakes (chain spaghetti, no observability, ignoring LCEL, over-complex agents, poor error handling)
4. **Tool & Technology Map**: LangChain ecosystem components (core, community, LangGraph, LangSmith, LangServe) with selection criteria
5. **Interaction Scripts**: How to respond to "build a RAG app with LangChain", "design a LangGraph agent", "migrate to latest LangChain", "deploy LangChain in production"

## Agent Integration Points

This agent should:
- **Complement**: ai-solution-architect by being the LangChain framework expert
- **Hand off to**: rag-system-designer for framework-agnostic RAG optimization
- **Receive from**: ai-solution-architect for system-level architecture decisions
- **Collaborate with**: prompt-engineer on prompt optimization within LangChain
- **Never overlap with**: ai-solution-architect on framework-agnostic AI architecture decisions
