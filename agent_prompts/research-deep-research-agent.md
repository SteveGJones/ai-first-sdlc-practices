# Deep Research Prompt: Deep Research Agent

## Objective

Research and compile the domain knowledge required to build an AI sub-agent
that acts as a Deep Research Specialist. This agent will be spawned as an
independent subprocess (via the Task tool) to execute systematic web research
based on a structured research prompt, synthesize findings from multiple sources,
and produce a comprehensive research document that can be directly consumed by
an agent-builder to create production-quality AI agents.

The resulting agent should be able to take any research prompt (following the
templates/agent-research-prompt.md format), execute a methodical multi-phase
research process using WebSearch and WebFetch tools, critically evaluate sources,
resolve contradictions between findings, and produce a structured synthesis
document organized into the five standard categories (Core Knowledge Base,
Decision Frameworks, Anti-Patterns Catalog, Tool & Technology Map, Interaction
Scripts) when engaged by the development team.

## Context

This agent is needed because the Agent Creation Pipeline (Steps 3-4) currently
has no automated execution mechanism. Research prompts exist as structured
question documents, but executing them requires manual effort - feeding questions
to an AI with web search, collating results, and synthesizing findings. This
creates a bottleneck: the research phase is the most time-consuming step, and
doing it in the main conversation context risks context window exhaustion when
creating multiple agents.

The existing agent catalog has no research-focused agent. The closest agents are
solution-architect (system design, not research methodology) and
documentation-architect (document creation, not knowledge discovery). Neither
can systematically execute a multi-topic research campaign with source evaluation
and contradiction resolution.

The deep-research-agent solves this by running as an isolated subprocess with
its own full context window. Multiple instances can run in parallel to research
different agents simultaneously, and each produces a file-based output that
persists beyond its context lifetime.

## Research Areas

### 1. Systematic Research Methodology for AI Agents
- What are the established frameworks for systematic literature review and knowledge synthesis (e.g., PRISMA, scoping reviews)?
- How should a research process be structured when the researcher is an AI agent with web search capabilities rather than a human?
- What are the best practices for decomposing broad research topics into targeted, answerable questions?
- How should research depth be balanced against breadth when operating under context window constraints?
- What techniques exist for iterative research refinement (starting broad, narrowing based on findings)?

### 2. Web Search Strategy and Query Optimization
- What are the current best practices for constructing effective web search queries to find authoritative technical content?
- How should search queries be varied and refined to avoid confirmation bias and find diverse perspectives?
- What query patterns work best for finding: current best practices, anti-patterns, tool comparisons, and emerging trends?
- How should an AI agent determine when it has sufficient coverage of a topic vs. when more searching is needed?
- What strategies exist for finding primary sources (official docs, RFCs, research papers) vs. secondary sources (blogs, tutorials)?

### 3. Source Evaluation and Credibility Assessment
- What frameworks exist for evaluating the credibility of technical sources (CRAAP test, lateral reading, etc.)?
- How should an AI agent assess whether a source is current, authoritative, and relevant to the specific research context?
- What are the indicators of high-quality vs. low-quality technical content (e.g., vendor marketing vs. practitioner experience)?
- How should conflicting information from multiple sources be handled and documented?
- What are the best practices for distinguishing between established consensus and emerging/experimental practices?

### 4. Knowledge Synthesis and Organization
- What are the proven methods for synthesizing information from multiple sources into a coherent knowledge base?
- How should findings be organized to support downstream agent creation (the five synthesis categories)?
- What techniques exist for identifying patterns, themes, and gaps across research findings?
- How should quantitative claims (performance numbers, adoption statistics) be validated and contextualized?
- What are the best practices for creating decision frameworks from comparative research?

### 5. Structured Output Generation for Agent Creation
- What makes research output maximally useful for creating AI agent instructions?
- How should research findings be formatted to preserve specificity while enabling flexible use?
- What level of detail is optimal in research documents - too little loses value, too much becomes noise?
- How should examples, code snippets, and specific recommendations be captured in research output?
- What metadata should accompany research findings (source URLs, confidence levels, recency)?

### 6. Handling Research Constraints and Failure Modes
- What should a research agent do when web search returns insufficient or contradictory results?
- How should the agent handle topics where the landscape is rapidly changing (e.g., AI tools, cloud services)?
- What are the failure modes of AI-driven research (hallucination amplification, echo chamber effects, recency bias)?
- How should the agent communicate uncertainty and gaps in its research findings?
- What fallback strategies exist when primary research approaches fail?

### 7. Multi-Topic Research Campaign Management
- How should a research agent prioritize and sequence multiple research areas within a single session?
- What techniques exist for cross-referencing findings across different research areas to find connections?
- How should cumulative research findings be tracked to avoid redundant searches?
- What are the best practices for time-boxing research per topic to ensure all areas receive coverage?
- How should the agent decide when a research area is "complete enough" vs. needs more investigation?

### 8. Research for Specific Agent Types
- What different research approaches are needed for different agent archetypes (architect vs. domain expert vs. enforcer)?
- How should research depth vary based on the target agent's role (operational advisor vs. strategic planner)?
- What specific types of knowledge are most valuable for each synthesis category?
- How should research be adapted when creating agents for rapidly evolving vs. stable domains?
- What role do case studies, post-mortems, and real-world examples play in agent knowledge bases?

## Synthesis Requirements

After completing the research, synthesize findings into:

1. **Core Knowledge Base**: The essential research methodology, search strategies, source evaluation criteria, and synthesis techniques that the deep-research-agent must know to produce high-quality research documents
2. **Decision Frameworks**: Structured approaches for making research decisions (e.g., "when topic has conflicting sources, apply [technique] because [reason]"; "when search returns < N relevant results, broaden query by [method]")
3. **Anti-Patterns Catalog**: Common research mistakes the agent should actively detect and avoid (e.g., confirmation bias in search queries, over-reliance on single sources, accepting marketing content as technical truth, hallucination amplification)
4. **Tool & Technology Map**: Specific search strategies, query patterns, source types, and evaluation frameworks the agent should use, organized by research phase
5. **Interaction Scripts**: How the agent should structure its research workflow - from receiving a research prompt, through executing searches, to producing the final synthesis document

## Agent Integration Points

This agent should:
- **Complement**: agent-builder-agent by producing the research documents that agent-builder consumes to create agents
- **Receive from**: Any user or orchestrator that provides a research prompt file (following templates/agent-research-prompt.md format)
- **Hand off to**: agent-builder-agent with a completed research synthesis document
- **Never overlap with**: solution-architect on system design decisions or documentation-architect on document formatting
- **Coordinate with**: The parent context that spawns it, communicating progress through file output
