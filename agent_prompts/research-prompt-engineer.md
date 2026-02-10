# Deep Research Prompt: Prompt Engineer Agent

## Objective

Research and compile the domain knowledge required to build an AI sub-agent
that acts as a Prompt Engineer. This agent will craft, optimize, and evaluate
prompts for large language models, implement advanced prompting techniques,
design prompt templates and versioning systems, and measure prompt performance
across diverse use cases.

The resulting agent should be able to optimize existing prompts, implement
chain-of-thought and other advanced techniques, design prompt evaluation
frameworks, manage prompt versioning, and create domain-specific prompt
libraries when engaged by the development team.

## Context

This agent is needed because prompt engineering has evolved from simple text
crafting into a rigorous discipline with evaluation frameworks, optimization
techniques, and production patterns. The existing agent has solid fundamentals
but needs depth on modern prompting techniques (structured outputs, tool use
prompting, multi-turn optimization), evaluation methodologies, and the rapidly
evolving prompt engineering landscape. The ai-solution-architect handles
system design; this agent is the prompt crafting and optimization specialist.

## Research Areas

### 1. Advanced Prompting Techniques (2025-2026)
- What are the current best prompting techniques for modern LLMs (Claude, GPT, Gemini, Llama)?
- How have chain-of-thought, tree-of-thought, and graph-of-thought prompting evolved?
- What are the latest patterns for few-shot and in-context learning optimization?
- How do structured output prompting techniques work (JSON mode, XML, schema-guided)?
- What are current patterns for multi-turn conversation design and context management?

### 2. Prompt Optimization & Testing
- What are current best practices for systematic prompt optimization?
- How do prompt evaluation frameworks work (human eval, LLM-as-judge, automated metrics)?
- What are the latest patterns for A/B testing prompts in production?
- How should organizations implement prompt regression testing?
- What tools support prompt testing and optimization (Promptfoo, LangSmith, Braintrust)?

### 3. Tool Use & Function Calling Prompts
- What are current best practices for tool-use prompting across LLM providers?
- How should tool descriptions be structured for optimal LLM performance?
- What are the latest patterns for multi-tool orchestration via prompts?
- How do agentic prompts differ from standard prompts?
- What are current patterns for error handling and retry in tool-use prompts?

### 4. System Prompt Design
- What are current best practices for system prompt architecture?
- How should organizations structure complex system prompts for consistent behavior?
- What are the latest patterns for role definition and personality crafting?
- How do guardrails and safety instructions integrate into system prompts?
- What are current patterns for system prompt versioning and management?

### 5. Prompt Security & Safety
- What are current best practices for preventing prompt injection attacks?
- How should organizations implement prompt-level safety guardrails?
- What are the latest patterns for jailbreak prevention and adversarial robustness?
- How do content filtering and moderation integrate with prompt design?
- What are current practices for prompt auditing and compliance?

### 6. Domain-Specific Prompting
- How should prompts be adapted for code generation vs creative writing vs analysis?
- What are current patterns for medical, legal, and financial domain prompting?
- How do RAG-augmented prompts differ from standalone prompts?
- What are the latest patterns for multimodal prompting (vision + text)?
- How should prompts be designed for different model sizes and capabilities?

### 7. Prompt Management at Scale
- What are current best practices for prompt versioning and lifecycle management?
- How should organizations implement prompt libraries and template systems?
- What are the latest patterns for prompt observability and monitoring in production?
- How do prompt management platforms compare (Humanloop, Vellum, PromptLayer)?
- What are current patterns for prompt cost optimization?

## Synthesis Requirements

After completing the research, synthesize findings into:

1. **Core Knowledge Base**: Prompting techniques, evaluation methods, security practices, management patterns the agent must know
2. **Decision Frameworks**: "When prompting for [task type] with [model], use [technique] because [reason]" structured guidance
3. **Anti-Patterns Catalog**: Common prompting mistakes (over-specification, ignoring model strengths, no evaluation, inconsistent formatting, prompt bloat)
4. **Tool & Technology Map**: Current prompt engineering tools (testing, management, optimization, monitoring) with selection criteria
5. **Interaction Scripts**: How to respond to "optimize my prompt", "design a system prompt", "set up prompt evaluation", "prevent prompt injection"

## Agent Integration Points

This agent should:
- **Complement**: ai-solution-architect by owning prompt-level optimization (architect owns system design, prompt-engineer owns prompt crafting)
- **Hand off to**: ai-solution-architect for system-level AI architecture decisions
- **Receive from**: agent-developer for agent prompt design requirements
- **Collaborate with**: security-architect on prompt security and injection prevention
- **Never overlap with**: ai-solution-architect on model selection and MLOps pipeline design
