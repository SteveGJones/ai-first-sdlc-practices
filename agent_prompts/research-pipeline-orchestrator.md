# Deep Research Prompt: Pipeline Orchestrator Agent

## Objective

Research and compile the domain knowledge required to build an AI sub-agent
that acts as a Pipeline Orchestrator for the agent creation pipeline. This agent
will serve as the unified entry point for end-to-end agent creation, accepting
either a web research request or an internal repository path, detecting the input
type, routing to the appropriate research agent (deep-research-agent for web,
repo-knowledge-distiller for repos), then delegating to agent-builder for
construction, and managing validation and deployment.

The resulting agent should be able to analyze user requests, check for duplicate
agents, recommend archetypes, route to the correct research path, generate
research prompts when needed, coordinate multi-agent workflows, and produce
Pipeline Completion Reports when engaged by the development team.

## Context

This agent is needed because the agent creation pipeline currently requires
manual orchestration across its 7 steps. Users must individually invoke the
research agent, then the builder agent, then run validation tools, then deploy
manually. With the addition of the repo-knowledge-distiller as an alternative
research path, routing decisions add further complexity. A unified orchestrator
eliminates this manual coordination burden.

The existing agent catalog has orchestrators for other domains (v3-setup-orchestrator
for framework setup, integration-orchestrator for testing) but none specifically
for the agent creation pipeline. The closest is the agent-builder itself, but it
only handles Step 5 (construction from synthesis) -- it does not manage the full
lifecycle from need identification through deployment.

The pipeline-orchestrator solves this by providing a single entry point that
handles the complete lifecycle: input analysis, duplicate detection, route
selection, research prompt generation, research/distillation delegation, agent
construction delegation, validation execution, and deployment with a completion
report.

## Research Areas

### 1. Multi-Agent Orchestration Patterns
- What are the established patterns for orchestrating multi-agent workflows (sequential, parallel, conditional)?
- How should an orchestrator delegate work to specialized agents while maintaining oversight?
- What communication patterns work best between orchestrators and worker agents (message passing, file-based, context sharing)?
- How should an orchestrator handle failure in a delegated agent (retry, fallback, abort)?
- What are the best practices for maintaining state across a multi-phase orchestrated pipeline?

### 2. Input Classification and Routing
- What techniques exist for classifying user intent from natural language requests?
- How should routing decisions be made when input signals are ambiguous?
- What decision matrix patterns are most effective for multi-path routing?
- How should an orchestrator handle hybrid requests that require multiple paths simultaneously?
- What are the best practices for communicating routing decisions to users transparently?

### 3. Duplicate Detection and Conflict Resolution
- What techniques exist for detecting semantic duplicates in agent/service catalogs?
- How should an orchestrator handle the case where an existing agent partially overlaps the requested one?
- What user interaction patterns work best for resolving duplicate/overlap conflicts?
- How should the orchestrator distinguish between "rebuild existing" vs. "create new complementary" requests?
- What manifest/registry patterns support efficient duplicate checking?

### 4. Research Prompt Generation
- What makes an effective research prompt for the deep-research-agent?
- How should an orchestrator translate a user's domain description into structured research areas?
- What heuristics determine the right number and depth of research areas for a given domain?
- How should the orchestrator decide between generating a new prompt vs. reusing an existing one?
- What template patterns produce the most useful research outputs?

### 5. Pipeline Phase Management
- What are the best practices for defining phase entry/exit criteria in multi-step pipelines?
- How should an orchestrator verify that a phase's outputs meet the next phase's input requirements?
- What validation gates should exist between pipeline phases?
- How should phase timing and progress be tracked and communicated?
- What are the best practices for producing structured pipeline completion reports?

### 6. Archetype Selection Heuristics
- What heuristics can determine the appropriate agent archetype from a user's description?
- How should the five archetypes (Domain Expert, Architect, Reviewer, Orchestrator, Enforcer) map to common request patterns?
- When should the orchestrator recommend a hybrid archetype?
- How should archetype uncertainty be communicated to the user for confirmation?
- What role does the target agent's intended usage play in archetype selection?

### 7. Deployment and Manifest Management
- What are the best practices for automated agent deployment to multiple targets (source, runtime, distribution)?
- How should manifest files be updated programmatically to include new agents?
- What validation steps should occur between construction and deployment?
- How should the orchestrator handle deployment failures (partial deployment, rollback)?
- What post-deployment verification steps ensure the agent is correctly installed?

### 8. Hybrid Research Coordination
- How should findings from web research and repository analysis be merged into a single synthesis document?
- What conflict resolution strategies apply when web best practices differ from internal repo practices?
- How should the orchestrator coordinate parallel research streams (web + repo) efficiently?
- What deduplication strategies prevent redundant findings in merged synthesis documents?
- How should confidence levels be assigned when findings are corroborated across both web and repo sources?

## Synthesis Requirements

After completing the research, synthesize findings into:

1. **Core Knowledge Base**: The essential orchestration patterns, routing logic, phase management techniques, and deployment practices that the pipeline-orchestrator must know to coordinate the full agent creation lifecycle
2. **Decision Frameworks**: Structured approaches for making orchestration decisions (e.g., "when user provides a local path, route to repo-knowledge-distiller because the input is an internal repository"; "when existing agent covers the domain, present rebuild vs. new options because duplicates reduce catalog clarity")
3. **Anti-Patterns Catalog**: Common orchestration mistakes the agent should actively avoid (e.g., doing research directly instead of delegating, skipping validation, deploying despite failures, over-engineering routing for simple cases)
4. **Tool & Technology Map**: Specific routing signals, validation tools, manifest update patterns, and deployment procedures organized by pipeline phase
5. **Interaction Scripts**: How the agent should structure its orchestration workflow -- from receiving a user request, through route selection and delegation, to producing the Pipeline Completion Report

## Agent Integration Points

This agent should:
- **Complement**: deep-research-agent and repo-knowledge-distiller by providing the orchestration layer that routes to and coordinates them
- **Receive from**: Users directly with agent creation requests (domain descriptions, repository paths, or research prompt files)
- **Hand off to**: deep-research-agent (web route), repo-knowledge-distiller (repo route), agent-builder (construction), validation tools (quality checks)
- **Never overlap with**: deep-research-agent on web research execution, repo-knowledge-distiller on repository analysis, or agent-builder on agent file construction
- **Coordinate with**: All pipeline agents as the central coordination point for agent creation
