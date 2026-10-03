# sdlc-team-ai

AI/ML specialist agents for projects building AI-powered systems.

## Quick start

```bash
/plugin install sdlc-team-ai@ai-first-sdlc
```

Requires `sdlc-core` to be installed first.

## Agents

| Agent | Purpose |
|-------|---------|
| `a2a-architect` | Designs multi-agent communication using MCP and A2A protocols, inter-agent messaging, orchestration patterns, and scaling strategies |
| `agent-developer` | Architects AI agents using ReAct, Plan-Execute, and Reflection patterns with RAG integration, tool design, and evaluation frameworks |
| `ai-devops-engineer` | Manages LLM serving infrastructure, GPU orchestration, AI cost optimization, and AI-specific CI/CD pipelines |
| `ai-solution-architect` | Designs end-to-end AI/ML system architecture including model selection, RAG systems, MLOps pipelines, and AI safety |
| `ai-team-transformer` | Guides AI adoption programs, multi-agent orchestration coaching, and developer team transformation strategies |
| `ai-test-engineer` | Designs comprehensive test strategies for AI systems including test pyramids, AI-augmented testing, contract testing, and flaky test resolution |
| `context-engineer` | Specializes in AI memory architectures, context window optimization, token budget management, and multi-agent state persistence |
| `langchain-architect` | Designs LangChain 0.1+ and LangGraph architectures including LCEL chains, RAG systems, and production LLM deployment with observability |
| `mcp-quality-assurance` | Reviews MCP servers for specification compliance, security auditing, and production readiness assessment |
| `mcp-server-architect` | Architects MCP server design including tool schema hierarchies, transport configuration, resource patterns, and security architecture |
| `mcp-test-agent` | Tests MCP server implementations for functionality, reliability, performance, and AI client usability |
| `orchestration-architect` | Designs multi-agent workflow state machines, agent coordination patterns, and distributed orchestration using LangGraph, AutoGen, and similar frameworks |
| `prompt-engineer` | Engineers prompts for Claude, GPT, Gemini, and Llama using chain-of-thought, structured outputs, few-shot learning, and prompt optimization techniques |
| `rag-system-designer` | Architects production RAG systems covering vector databases, embedding selection, chunking strategies, and retrieval optimization |

## When to use this plugin

Install `sdlc-team-ai` when your project involves:

- **LLM applications** -- chatbots, summarization, classification, or generation features
- **MCP servers** -- building, testing, or reviewing Model Context Protocol integrations
- **RAG systems** -- document retrieval, knowledge bases, or semantic search
- **Prompt engineering** -- designing, optimizing, or evaluating prompts across models
- **Agent development** -- building autonomous or multi-agent systems with tool use
- **AI infrastructure** -- deploying, scaling, or cost-optimizing LLM serving
- **AI team adoption** -- transitioning teams to AI-augmented development workflows

## Agent groupings

The 14 agents fall into four areas:

- **MCP specialists** (4 agents) -- `mcp-server-architect`, `mcp-quality-assurance`, `mcp-test-agent`, and `a2a-architect` cover the full lifecycle of building, reviewing, and testing Model Context Protocol servers and inter-agent communication.
- **Agent and orchestration** (3 agents) -- `agent-developer`, `orchestration-architect`, and `ai-team-transformer` handle agent design patterns, multi-agent workflow orchestration, and team adoption coaching.
- **LLM application design** (4 agents) -- `ai-solution-architect`, `langchain-architect`, `rag-system-designer`, and `context-engineer` cover end-to-end LLM system architecture from model selection through retrieval and memory management.
- **Supporting disciplines** (3 agents) -- `prompt-engineer`, `ai-test-engineer`, and `ai-devops-engineer` provide prompt optimization, AI-specific testing, and production infrastructure management.

## Relationship to other plugins

`sdlc-team-ai` covers AI/ML-specific concerns. For broader architecture needs
(performance engineering, cross-cutting research, system design outside the AI
domain), install `sdlc-team-common`. The two plugins complement each other well
in projects that combine AI features with conventional backend/frontend work.

For security review of AI systems beyond frontend concerns, see
`sdlc-team-security`. For cloud infrastructure hosting AI workloads, see
`sdlc-team-cloud`.

## Part of the SDLC plugin family

This plugin is one of several team plugins in the AI-First SDLC framework.
Install `sdlc-core` first, then add team plugins matching your project needs.
Run `/sdlc-core:setup-team` to get personalized recommendations.
