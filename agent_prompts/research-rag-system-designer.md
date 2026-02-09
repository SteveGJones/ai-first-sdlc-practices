# Deep Research Prompt: RAG System Designer Agent

## Objective

Research and compile the domain knowledge required to build an AI sub-agent
that acts as a RAG System Designer. This agent will design production-ready
Retrieval-Augmented Generation systems, select and configure vector databases,
optimize embedding strategies, create chunking pipelines, tune relevance,
and ensure RAG systems deliver accurate, contextual responses.

The resulting agent should be able to design end-to-end RAG architectures,
select vector databases, optimize chunking and embedding strategies, implement
evaluation frameworks, and tune retrieval relevance when engaged by the
development team.

## Context

This agent is the deep specialist in RAG systems, which have become the
primary pattern for grounding LLMs with domain knowledge. The existing agent
has good RAG fundamentals but needs depth on advanced RAG techniques
(corrective RAG, self-RAG, adaptive RAG), modern vector database capabilities,
evaluation methodologies, and production optimization patterns. The
ai-solution-architect handles overall AI design; this agent owns RAG
implementation end-to-end.

## Research Areas

### 1. RAG Architecture Patterns (2025-2026)
- What are the current RAG architecture patterns (naive, advanced, modular, agentic)?
- How have corrective RAG, self-RAG, and adaptive RAG techniques evolved?
- What are the latest patterns for multi-modal RAG (text, images, tables)?
- How should RAG systems handle structured data alongside unstructured?
- What are current patterns for graph RAG and knowledge graph-augmented retrieval?

### 2. Vector Database Selection & Configuration
- How do current vector databases compare (Pinecone, Weaviate, Qdrant, Milvus, pgvector, Chroma)?
- What are the latest indexing algorithms (HNSW, IVF, ScaNN) and their trade-offs?
- How should vector databases be configured for optimal performance?
- What are current patterns for hybrid search (dense + sparse vectors)?
- How do managed vs self-hosted vector databases compare for production use?

### 3. Embedding & Chunking Strategies
- What are current best practices for text embedding model selection?
- How do embedding models compare (OpenAI, Cohere, sentence-transformers, Voyage)?
- What are the latest chunking strategies (semantic, recursive, context-aware)?
- How should chunk size and overlap be optimized for different content types?
- What are current patterns for multi-vector and late interaction embeddings (ColBERT)?

### 4. Retrieval Optimization
- What are current best practices for retrieval quality optimization?
- How do re-ranking models work and when should they be used (Cohere Rerank, cross-encoders)?
- What are the latest patterns for query transformation (HyDE, multi-query, step-back)?
- How should metadata filtering and hybrid retrieval be configured?
- What are current patterns for retrieval with diversity and deduplication?

### 5. RAG Evaluation & Quality
- What are current best practices for RAG system evaluation?
- How do RAG evaluation frameworks work (RAGAS, TruLens, DeepEval)?
- What metrics matter most for RAG quality (faithfulness, relevance, context precision)?
- How should organizations implement continuous RAG quality monitoring?
- What are current patterns for RAG debugging and error analysis?

### 6. Production RAG Systems
- What are current best practices for RAG system scalability?
- How should document ingestion pipelines be designed for continuous updates?
- What are the latest patterns for RAG caching and latency optimization?
- How do multi-tenant RAG systems work (access control, data isolation)?
- What are current patterns for RAG cost optimization in production?

### 7. Advanced RAG Techniques
- What are current patterns for agentic RAG (tool-augmented retrieval)?
- How do knowledge graphs enhance RAG system accuracy?
- What are the latest patterns for conversational RAG (multi-turn context)?
- How should RAG handle temporal data and knowledge freshness?
- What are current patterns for cross-lingual and multi-language RAG?

## Synthesis Requirements

After completing the research, synthesize findings into:

1. **Core Knowledge Base**: RAG architectures, vector DB selection, chunking/embedding strategies, evaluation methods the agent must know
2. **Decision Frameworks**: "When building RAG for [content type] at [scale], use [pattern/tool] because [reason]" structured guidance
3. **Anti-Patterns Catalog**: Common RAG mistakes (wrong chunk size, no evaluation, ignoring re-ranking, single retrieval strategy, stale data)
4. **Tool & Technology Map**: Current RAG tools (vector DBs, embeddings, evaluation, frameworks) with selection criteria
5. **Interaction Scripts**: How to respond to "build a RAG system", "our RAG returns wrong answers", "optimize our retrieval", "evaluate our RAG quality"

## Agent Integration Points

This agent should:
- **Complement**: ai-solution-architect by owning RAG implementation depth
- **Hand off to**: database-architect for general database optimization outside vector stores
- **Receive from**: ai-solution-architect for RAG requirements within larger AI systems
- **Collaborate with**: context-engineer on context management around RAG results
- **Never overlap with**: langchain-architect on framework-specific RAG implementation
