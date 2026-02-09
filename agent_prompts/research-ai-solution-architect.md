# Deep Research Prompt: AI Solution Architect Agent

## Objective

Research and compile the domain knowledge required to build an AI sub-agent
that acts as an AI Solution Architect. This agent will design AI/ML system
architectures, evaluate model selection, design MLOps pipelines, review
AI implementation strategies, and ensure AI systems are production-grade,
ethical, and scalable.

The resulting agent should be able to design end-to-end AI systems, evaluate
model architectures, recommend MLOps practices, assess AI ethics and bias,
and create AI governance frameworks when engaged by the development team.

## Context

This agent is the primary AI systems expert in the catalog. The existing agent
has solid fundamentals but needs depth on the rapidly evolving AI landscape
including LLM application architecture, RAG system design, multi-agent
orchestration, AI safety, and modern MLOps platforms. The prompt-engineer
handles prompt optimization; this agent owns the full AI system architecture.

## Research Areas

### 1. LLM Application Architecture (2025-2026)
- What are current best practices for building production LLM applications?
- How have LLM application frameworks evolved (LangChain, LlamaIndex, Semantic Kernel)?
- What are the latest patterns for LLM routing, fallback, and model selection?
- How should architects design for LLM cost optimization (caching, batching, model tiering)?
- What are current patterns for LLM evaluation and quality assurance?

### 2. RAG System Architecture
- What are current best practices for Retrieval-Augmented Generation systems?
- How have vector databases evolved (Pinecone, Weaviate, pgvector, Qdrant, Chroma)?
- What are the latest patterns for chunking, embedding, and retrieval strategies?
- How should architects handle RAG evaluation and relevance tuning?
- What are current patterns for hybrid search (semantic + keyword) and re-ranking?

### 3. MLOps & Model Lifecycle Management
- What are current best practices for MLOps platforms and workflows?
- How have model registries and experiment tracking evolved (MLflow, Weights & Biases, Neptune)?
- What are the latest patterns for model training, fine-tuning, and deployment pipelines?
- How should organizations implement model monitoring and drift detection?
- What are current patterns for feature stores and feature engineering platforms?

### 4. Multi-Agent & Agentic Systems
- What are the current patterns for multi-agent system architecture?
- How do agent orchestration frameworks work (AutoGen, CrewAI, LangGraph)?
- What are the latest patterns for agent communication and coordination?
- How should architects design for agent reliability and error handling?
- What are current patterns for agent memory, state management, and tool use?

### 5. AI Safety, Ethics & Governance
- What are current best practices for responsible AI development?
- How should organizations implement AI bias detection and mitigation?
- What are the latest patterns for AI explainability and interpretability?
- How do AI governance frameworks work in practice (NIST AI RMF, EU AI Act)?
- What are current patterns for AI red teaming and safety testing?

### 6. Model Selection & Evaluation
- How should architects evaluate and select AI models for specific use cases?
- What are the current model benchmarks and how to interpret them?
- What are the latest patterns for model fine-tuning vs prompt engineering vs RAG?
- How do open-source models compare to proprietary APIs in 2025-2026?
- What are current patterns for multi-modal AI systems (vision, audio, text)?

### 7. AI Infrastructure & Scaling
- What are current best practices for GPU infrastructure management?
- How should organizations approach model serving at scale (vLLM, TensorRT, Triton)?
- What are the latest patterns for AI workload scheduling and resource optimization?
- How do serverless AI inference platforms work (Replicate, Modal, Banana)?
- What are current patterns for edge AI deployment?

### 8. Data Pipeline Architecture for AI
- What are current best practices for AI data pipelines?
- How should organizations handle data quality and labeling at scale?
- What are the latest patterns for synthetic data generation?
- How do data versioning tools work (DVC, LakeFS, Delta Lake)?
- What are current patterns for real-time feature computation?

## Synthesis Requirements

After completing the research, synthesize findings into:

1. **Core Knowledge Base**: LLM architecture patterns, MLOps practices, model evaluation methods, AI safety frameworks the agent must know
2. **Decision Frameworks**: "When building [AI system type] with [requirements], use [architecture/model] because [reason]" structured guidance
3. **Anti-Patterns Catalog**: Common AI architecture mistakes (prompt injection vulnerabilities, ignoring model drift, over-engineering RAG, treating LLMs as databases)
4. **Tool & Technology Map**: Current AI tools (frameworks, model serving, MLOps, vector DBs) with selection criteria
5. **Interaction Scripts**: How to respond to "design our AI system", "which model should we use?", "set up our MLOps pipeline", "review our RAG architecture"

## Agent Integration Points

This agent should:
- **Coordinate**: AI-specific agents (prompt-engineer, rag-system-designer, mcp-server-architect) as the senior AI architect
- **Hand off to**: prompt-engineer for prompt optimization, rag-system-designer for RAG tuning
- **Receive from**: solution-architect for system-wide architecture context
- **Collaborate with**: security-architect on AI security, data-architect on data pipelines
- **Never overlap with**: prompt-engineer on prompt crafting, rag-system-designer on vector DB configuration
