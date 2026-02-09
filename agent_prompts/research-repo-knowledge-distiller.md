# Deep Research Prompt: Repo Knowledge Distiller Agent

## Objective

Research and compile the domain knowledge required to build an AI sub-agent
that acts as a Repository Knowledge Distiller. This agent will analyze internal
repositories and knowledge bases (code, documentation, methodology, configurations,
Claude skills, MCP configurations) and produce structured synthesis documents in
the exact same 5-category format that the agent-builder consumes. It is the internal
counterpart to the deep-research-agent -- where deep-research-agent gathers knowledge
from the web, this agent gathers knowledge from repositories.

The resulting agent should be able to take any repository path, systematically
scan and classify its content, extract declarative facts, procedural rules, and
anti-patterns, discover portable artifacts (Claude agents, commands, MCP configs,
hooks), and produce a synthesis document that the agent-builder can consume
without modification when engaged by the development team or pipeline-orchestrator.

## Context

This agent is needed because the agent creation pipeline currently only supports
web research (via deep-research-agent) as the knowledge source for building agents.
Many teams have internal repositories containing methodology, frameworks, tools,
and documented practices that should be distilled into specialist agents. Without
a repository analysis agent, this knowledge must be manually extracted and
reformatted -- a time-consuming and error-prone process.

The existing agent catalog has no repository analysis agent. The closest agents are
deep-research-agent (web-focused, not repo-focused), code-review-specialist (evaluates
code quality, not knowledge extraction), and documentation-architect (creates docs,
not knowledge distillation). None can systematically analyze a repository to produce
agent-builder-compatible synthesis documents.

The repo-knowledge-distiller solves this by providing a structured 6-phase analysis
methodology that handles code-dominant, documentation-dominant, methodology, and
mixed repositories. It also introduces the RELIC evaluation framework (replacing
CRAAP for internal content) and the Portable Artifacts discovery mechanism for
Claude skills, MCP configurations, and automation hooks.

## Research Areas

### 1. Repository Analysis and Content Classification
- What are the established methods for analyzing repository structure and classifying content types?
- How should a repository scanner prioritize which files to read deeply vs. skim?
- What heuristics exist for detecting the "knowledge spine" of a repository (the most knowledge-dense files)?
- How should repository content be classified (code, docs, configs, templates, tests, automation)?
- What techniques exist for estimating analysis scope and budgeting analysis effort proportionally?

### 2. Knowledge Extraction from Source Code
- What are the best practices for extracting architectural patterns and design decisions from code?
- How should an analyzer identify public APIs, key abstractions, and entry points in unfamiliar codebases?
- What techniques exist for extracting decision frameworks from code structure (e.g., strategy patterns, configuration hierarchies)?
- How should code comments, docstrings, and inline documentation be weighted relative to the code itself?
- What methods exist for tracing workflows through code to understand end-to-end processes?

### 3. Knowledge Extraction from Documentation
- What are the best practices for extracting structured knowledge from prose documentation?
- How should methodology documents, process guides, and decision records (ADRs) be analyzed?
- What techniques exist for identifying core concepts, terminology, and domain vocabulary from docs?
- How should diagrams (Mermaid, PlantUML, ASCII) be interpreted and their knowledge captured?
- What methods exist for detecting gaps and inconsistencies between documentation and implementation?

### 4. Quality Evaluation for Internal Repository Content
- What frameworks exist for evaluating the quality and reliability of internal repository content?
- How should content freshness/staleness be assessed (git history, last modified dates, deprecation markers)?
- What indicators distinguish production-quality content from experimental or abandoned code?
- How should contradictions between code and documentation be handled and documented?
- What evaluation dimensions matter most for internal repos vs. external web sources?

### 5. Portable Artifact Discovery and Cataloging
- What types of portable artifacts exist in modern development repositories (Claude skills, MCP configs, hooks, CI/CD)?
- How should portability be assessed for different artifact types (drop-in reusable vs. needs adaptation)?
- What dependency analysis is needed to understand what a portable artifact requires to function?
- How should Claude Code-specific artifacts (.claude/agents/, .claude/commands/) be analyzed and documented?
- What are the best practices for documenting artifact installation and integration instructions?

### 6. Knowledge Distillation and Synthesis
- What techniques exist for distilling repository knowledge into the 5-category synthesis format (Core Knowledge Base, Decision Frameworks, Anti-Patterns Catalog, Tool & Technology Map, Interaction Scripts)?
- How should knowledge units extracted from code differ from those extracted from documentation?
- What compression ratios are appropriate when distilling repository content into agent instructions?
- How should confidence levels be assigned when the source is internal code rather than published research?
- What techniques prevent knowledge loss during the transition from repository analysis to synthesis document?

### 7. Handling Different Repository Types
- How should analysis methodology adapt for code-dominant vs. documentation-dominant vs. methodology repositories?
- What special considerations apply to monorepos vs. single-purpose repositories?
- How should multi-language repositories be handled when extracting knowledge?
- What approach works best for analyzing framework and library repositories vs. application repositories?
- How should repositories containing primarily configuration and infrastructure-as-code be analyzed?

### 8. Cross-Reference and Gap Analysis
- What methods exist for identifying connections between findings across different parts of a repository?
- How should gaps in repository coverage be detected and documented?
- What techniques exist for identifying when repository content contradicts itself across files?
- How should the relationship between tests and implementation be analyzed for knowledge extraction?
- What role does git history play in understanding the evolution and intent behind repository content?

## Synthesis Requirements

After completing the research, synthesize findings into:

1. **Core Knowledge Base**: The essential repository analysis methodology, content classification techniques, knowledge extraction approaches, and RELIC evaluation criteria that the repo-knowledge-distiller must know to produce high-quality synthesis documents from any repository type
2. **Decision Frameworks**: Structured approaches for making analysis decisions (e.g., "when repository is docs-dominant, prioritize methodology extraction because the primary knowledge is in prose"; "when code contradicts documentation, apply RELIC Lineage scoring to determine which is more current")
3. **Anti-Patterns Catalog**: Common repository analysis mistakes the agent should actively detect and avoid (e.g., Surface-Level Scanning, Code-Only Blindness, Artifact Amnesia, Hallucination Filling, Scope Inflation)
4. **Tool & Technology Map**: Specific file patterns to scan for, content classification heuristics, RELIC scoring rubrics, and artifact discovery checklists organized by analysis phase
5. **Interaction Scripts**: How the agent should structure its repository analysis workflow -- from receiving a repository path, through 6-phase analysis, to producing the final synthesis document with Portable Artifacts appendix

## Agent Integration Points

This agent should:
- **Complement**: deep-research-agent by providing the internal repository analysis path (deep-research-agent handles web, this handles repos)
- **Receive from**: pipeline-orchestrator (when routing to repo analysis) or directly from users with a repository path and optional target agent name
- **Hand off to**: agent-builder with a completed synthesis document in the standard 5-category format
- **Never overlap with**: deep-research-agent on web research, code-review-specialist on code quality evaluation, or security-architect on security auditing
- **Coordinate with**: pipeline-orchestrator for end-to-end pipeline execution
