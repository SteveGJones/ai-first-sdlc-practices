# Deep Research Prompt: AI DevOps Engineer Agent

## Objective

Research and compile the domain knowledge required to build an AI sub-agent
that acts as an AI DevOps Engineer. This agent will deploy and operate AI
systems in production, manage LLM infrastructure, optimize AI costs,
implement AI-specific monitoring, and ensure reliable AI system operations.

The resulting agent should be able to deploy LLM applications, manage GPU
infrastructure, implement AI model serving, optimize inference costs, and
create AI-specific CI/CD pipelines when engaged by the development team.

## Context

This agent bridges DevOps and AI, covering the specialized operational
needs of AI systems that general DevOps doesn't address. The existing agent
has good AI operations fundamentals but needs depth on modern LLM serving
platforms, GPU management at scale, AI cost optimization strategies, and
emerging LLMOps patterns. The devops-specialist handles general CI/CD;
this agent handles AI-specific infrastructure and operations.

## Research Areas

### 1. LLM Serving & Inference Infrastructure (2025-2026)
- What are current best practices for LLM model serving (vLLM, TGI, TensorRT-LLM)?
- How do managed LLM platforms compare (AWS Bedrock, Azure OpenAI, Vertex AI)?
- What are the latest patterns for LLM request routing, load balancing, and failover?
- How should organizations implement LLM caching (semantic cache, KV cache)?
- What are current patterns for batching and throughput optimization?

### 2. GPU Infrastructure Management
- What are current best practices for GPU cluster management?
- How do GPU orchestration tools work (Kubernetes GPU operator, Run:ai, SkyPilot)?
- What are the latest patterns for multi-GPU and distributed inference?
- How should organizations optimize GPU utilization and cost?
- What are current patterns for serverless GPU computing (Modal, Replicate, Banana)?

### 3. AI Cost Management & FinOps
- What are current best practices for AI/LLM cost optimization?
- How should organizations track and allocate AI compute costs?
- What are the latest patterns for model tiering and routing for cost efficiency?
- How do token-level cost tracking and optimization work?
- What are current patterns for prompt caching and response reuse?

### 4. AI-Specific CI/CD & MLOps
- What are current best practices for AI model deployment pipelines?
- How should model versioning and rollback work in production?
- What are the latest patterns for A/B testing and canary deployments for AI models?
- How do feature flag systems apply to AI model serving?
- What are current patterns for model registry and artifact management?

### 5. AI Monitoring & Observability
- What are current best practices for monitoring LLM applications in production?
- How should model quality and drift be detected in real-time?
- What are the latest patterns for LLM observability (LangSmith, Langfuse, Helicone)?
- How should organizations implement AI-specific alerting and SLOs?
- What are current patterns for token usage monitoring and anomaly detection?

### 6. AI System Reliability
- What are current best practices for LLM application reliability?
- How should fallback chains and degraded modes work for AI systems?
- What are the latest patterns for rate limiting and quota management?
- How do circuit breakers apply to LLM API calls?
- What are current patterns for disaster recovery for AI systems?

### 7. Multi-Agent System Operations
- What are current best practices for deploying multi-agent systems?
- How should agent health monitoring and lifecycle management work?
- What are the latest patterns for agent scaling and resource allocation?
- How do orchestration platforms handle agent failures and retries?
- What are current patterns for agent system observability?

## Synthesis Requirements

After completing the research, synthesize findings into:

1. **Core Knowledge Base**: LLM serving, GPU management, AI cost optimization, AI monitoring the agent must know
2. **Decision Frameworks**: "When deploying [AI system type] at [scale], use [infrastructure] because [reason]" structured guidance
3. **Anti-Patterns Catalog**: Common AI DevOps mistakes (no caching, single-provider lock-in, ignoring costs, no fallbacks, manual model deployment)
4. **Tool & Technology Map**: Current AI infrastructure tools (serving, GPU, monitoring, cost) with selection criteria
5. **Interaction Scripts**: How to respond to "deploy our LLM app", "optimize our AI costs", "monitor our AI system", "scale our GPU infrastructure"

## Agent Integration Points

This agent should:
- **Complement**: devops-specialist with AI-specific operational expertise
- **Hand off to**: ai-solution-architect for AI architecture decisions
- **Receive from**: ai-solution-architect for deployment requirements
- **Collaborate with**: sre-specialist on AI system reliability
- **Never overlap with**: devops-specialist on general CI/CD and infrastructure
