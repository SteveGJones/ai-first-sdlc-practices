# Deep Research Prompt: Agent Builder Agent

## Objective

Research and compile the domain knowledge required to build an AI sub-agent
that acts as an Agent Builder Specialist. This agent will take a completed
research document (produced by the deep-research-agent) and a reference agent
archetype, then systematically construct a production-quality AI agent file
that meets all pipeline validation requirements and embodies the researched
domain knowledge as specific, actionable agent instructions.

The resulting agent should be able to transform raw research findings into
well-structured agent definitions, select and customize the appropriate
reference archetype, write instructions that are specific rather than generic,
create proper YAML frontmatter, ensure boundary clarity with existing agents,
and validate the output against the pipeline standards when engaged by the
development team.

## Context

This agent is needed because the Agent Creation Pipeline (Steps 5-6) currently
requires significant manual skill to execute well. The gap between "having
research findings" and "having a production agent" is where quality is most
often lost. Research gets diluted into vague instructions, specific findings
become generic platitudes, and the resulting agent lacks the depth that
distinguishes a production agent from a stub.

The existing agent catalog has no agent specifically designed to construct other
agents. The closest is sdlc-enforcer (validates compliance, does not create)
and documentation-architect (creates documents, but lacks agent-specific
knowledge about instruction design, persona creation, and LLM behavior
optimization).

The agent-builder bridges research and deployment by understanding both: how to
read and distill research documents, AND how to write instructions that maximize
LLM agent effectiveness. It knows the five reference archetypes intimately,
understands YAML frontmatter requirements, and produces agents that pass
validation on first attempt.

## Research Areas

### 1. Prompt Engineering for Agent Instructions (2025-2026 Best Practices)
- What are the current best practices for writing system prompts/instructions that produce consistent AI agent behavior?
- How do structured instructions (numbered lists, headers, examples) compare to prose-style instructions for LLM compliance?
- What techniques exist for making AI agents exhibit specific expertise without hallucinating beyond their knowledge?
- How should persona and voice be defined to create distinct but professional agent personalities?
- What are the current findings on instruction length vs. adherence - when do longer instructions help vs. hurt?

### 2. Knowledge Distillation: Research to Instructions
- What methods exist for converting broad research findings into concise, actionable agent instructions?
- How should domain knowledge be encoded so an LLM can apply it correctly in context?
- What is the optimal ratio of declarative knowledge ("X is true") vs. procedural knowledge ("When X, do Y")?
- How should decision frameworks from research be translated into agent decision-making behavior?
- What techniques prevent knowledge loss during the distillation from research document to agent instructions?

### 3. Agent Persona and Behavioral Design
- How do different persona framing techniques affect AI agent output quality?
- What are the current best practices for defining agent boundaries and preventing scope creep?
- How should agent confidence be calibrated - when should agents be assertive vs. hedging?
- What techniques exist for making agents collaborate effectively (handoff protocols, context sharing)?
- How do agents with well-defined boundaries perform compared to generalist agents?

### 4. Structured Agent File Design
- What are the best practices for organizing agent instruction files (section order, heading hierarchy)?
- How should YAML frontmatter be designed for discoverability and tool integration?
- What makes agent examples (the YAML examples field) effective for triggering correct agent selection?
- How should agent content be structured to support both reading by humans and parsing by LLMs?
- What naming conventions and metadata standards support agent ecosystem management at scale?

### 5. Anti-Pattern Detection in Agent Design
- What are the most common failure modes in AI agent instructions (too vague, contradictory, over-constrained)?
- How can an agent-builder detect and prevent generic/platitude-heavy instructions?
- What are the indicators that an agent will produce unreliable or inconsistent outputs?
- How should overlapping responsibilities between agents be detected and resolved?
- What patterns in agent instructions lead to hallucination, refusal, or off-topic responses?

### 6. Quality Validation and Testing for Agents
- What are the current approaches for testing AI agent instructions before deployment?
- How should agent output quality be measured against the research that informed the agent?
- What validation checks should be automated vs. require human judgment?
- How should agents be tested for edge cases and boundary conditions in their domain?
- What are the current best practices for iterative agent improvement based on real usage?

### 7. Agent Archetype Patterns and Selection
- What are the established patterns for different types of AI agents (advisor, reviewer, enforcer, orchestrator)?
- How should the choice of archetype influence the structure and content of agent instructions?
- What are the key differences in instruction design between domain experts, architects, and orchestrators?
- How should agents designed for different purposes (analysis vs. generation vs. validation) differ in their instruction structure?
- What patterns exist for agents that coordinate with other agents vs. work independently?

### 8. LLM Instruction Optimization
- What are the current findings on how different LLMs (Claude, GPT-4, etc.) interpret structured instructions?
- How should instructions be written to be robust across different model versions and capabilities?
- What are the current techniques for preventing instruction injection and maintaining agent integrity?
- How do formatting choices (markdown, XML tags, special delimiters) affect instruction following?
- What are the current best practices for handling context window limitations in agent design?

## Synthesis Requirements

After completing the research, synthesize findings into:

1. **Core Knowledge Base**: The essential principles of prompt engineering, knowledge distillation, persona design, and structured file creation that the agent-builder must know to transform research into production agents
2. **Decision Frameworks**: Structured approaches for agent construction decisions (e.g., "when research shows conflicting practices, encode as [technique]"; "when domain has > N tools, organize by [criteria]"; "when choosing archetype, match based on [factors]")
3. **Anti-Patterns Catalog**: Common agent construction mistakes the builder should detect and prevent (e.g., generic instructions that ignore research specifics, missing boundaries, over-broad scope, platitude-heavy content, instructions that encourage hallucination)
4. **Tool & Technology Map**: Specific techniques for instruction writing, YAML formatting, validation approaches, and testing methods the agent should use during construction
5. **Interaction Scripts**: How the agent should structure its construction workflow - from receiving research + archetype inputs, through drafting sections, to producing and validating the final agent file

## Agent Integration Points

This agent should:
- **Complement**: deep-research-agent by consuming its research output and transforming it into agents
- **Receive from**: deep-research-agent (research documents) and any user specifying an archetype choice
- **Hand off to**: validate-agent-pipeline.py for automated validation, then to .claude/agents/ for deployment
- **Never overlap with**: deep-research-agent on research execution, or sdlc-enforcer on compliance checking
- **Collaborate with**: The parent context that orchestrates the overall agent creation pipeline
