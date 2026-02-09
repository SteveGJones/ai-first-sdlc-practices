# Deep Research Prompt: Context Engineer Agent

## Objective

Research and compile the domain knowledge required to build an AI sub-agent
that acts as a Context Engineer. This agent will design conversation memory
systems, optimize token usage, manage context windows, implement state
persistence strategies, and ensure AI applications maintain coherent context
across interactions.

The resulting agent should be able to design memory architectures, implement
context compression, create state management systems, optimize token budgets,
and build context-aware AI applications when engaged by the development team.

## Context

This agent specializes in the critical challenge of managing what AI models
remember, forget, and can access. The existing agent has good fundamentals
but needs depth on latest context window management techniques, memory
architectures for production AI systems, token optimization strategies, and
emerging approaches to long-term AI memory. The ai-solution-architect handles
overall AI design; this agent is the memory and context specialist.

## Research Areas

### 1. Context Window Management (2025-2026)
- What are the current context window sizes across major LLMs and how to optimize for them?
- What are best practices for context window utilization and token budgeting?
- How do sliding window, rolling summary, and hierarchical context approaches compare?
- What are the latest patterns for context prioritization and relevance scoring?
- How should applications handle context overflow gracefully?

### 2. AI Memory Architectures
- What are current best practices for AI memory system design (short-term, long-term, episodic)?
- How do memory-augmented language models work (MemGPT, memory banks)?
- What are the latest patterns for semantic memory and knowledge graphs?
- How should conversation history be compressed without losing key information?
- What are current patterns for multi-session memory persistence?

### 3. Token Optimization Strategies
- What are current best practices for minimizing token usage while maintaining quality?
- How do prompt compression techniques work (LLMLingua, selective context)?
- What are the latest patterns for efficient prompt templating and variable injection?
- How should organizations balance token cost with response quality?
- What are current patterns for token usage monitoring and alerting?

### 4. State Persistence & Retrieval
- What are current best practices for persisting AI conversation state?
- How should state stores be designed for AI applications (Redis, databases, vector stores)?
- What are the latest patterns for state serialization and deserialization?
- How do checkpoint and resume patterns work for AI conversations?
- What are current patterns for distributed state management in multi-agent systems?

### 5. RAG as Context Extension
- How does RAG extend effective context beyond the context window?
- What are current best practices for dynamic context injection from knowledge bases?
- What are the latest patterns for context-aware retrieval (conversation-aware search)?
- How should context from multiple sources be merged and prioritized?
- What are current patterns for real-time context enrichment?

### 6. Context Engineering for Agents
- What are current best practices for managing context in agentic workflows?
- How should agent context be scoped and shared across tool calls?
- What are the latest patterns for inter-agent context passing and summarization?
- How do agents decide what context to carry forward vs discard?
- What are current patterns for context isolation and privacy in multi-agent systems?

### 7. Evaluation & Quality
- How should context management effectiveness be measured?
- What metrics indicate good vs poor context utilization?
- What are the latest patterns for context quality testing?
- How do context-related failures manifest and how to detect them?
- What are current patterns for context debugging and inspection tools?

## Synthesis Requirements

After completing the research, synthesize findings into:

1. **Core Knowledge Base**: Context window management, memory architectures, token optimization, state persistence the agent must know
2. **Decision Frameworks**: "When managing context for [application type] with [window size], use [strategy] because [reason]" structured guidance
3. **Anti-Patterns Catalog**: Common context mistakes (context stuffing, no summarization, losing critical info, unbounded memory, no persistence)
4. **Tool & Technology Map**: Current context management tools and libraries with selection criteria
5. **Interaction Scripts**: How to respond to "optimize our token usage", "design a memory system", "handle long conversations", "manage agent context"

## Agent Integration Points

This agent should:
- **Complement**: ai-solution-architect by specializing in context/memory design
- **Hand off to**: rag-system-designer for retrieval-specific optimization
- **Receive from**: ai-solution-architect for system context requirements
- **Collaborate with**: prompt-engineer on prompt-level context optimization
- **Never overlap with**: rag-system-designer on vector database and embedding optimization
