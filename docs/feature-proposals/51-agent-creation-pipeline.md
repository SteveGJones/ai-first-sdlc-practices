# Feature Proposal: Standardize Agent Creation Pipeline

**Proposal Number:** 51 (consolidated: #51, #52, #53)
**Status:** Draft
**Author:** AI Agent
**Created:** 2026-02-07
**Target Branch:** `feature/agent-creation-pipeline`
**Implementation Type:** Framework Enhancement

## Executive Summary

Formalize the agent creation pipeline as a first-class framework capability. This consolidates three related issues: standardizing the creation pipeline (#51), shipping reference agent archetypes (#52), and elevating research prompts (#53) into a single coherent initiative.

## Motivation

### Problem Statement

The framework has 60+ production agents and comprehensive tooling for validation and format checking, but:

1. **No documented creation process**: The existing AGENT-CREATION-GUIDE.md covers agent *writing* but not the research phase that produces deep domain knowledge
2. **No learning templates**: Users must reverse-engineer patterns from complex 160-632 line production agents
3. **No research prompt infrastructure**: The research-driven approach that produces quality agents is undocumented
4. **v3-setup-orchestrator blocks custom agents**: Rule #1 says "ALWAYS DOWNLOAD - NEVER CREATE" with no escape hatch for domains not covered by existing agents

### User Stories

- As a developer on a healthcare project, I need to create a domain-specific agent because no existing agent covers HIPAA compliance patterns
- As a new framework user, I want to understand the different agent patterns so I can choose the right starting point
- As an AI agent, I need a structured research process to build deep domain knowledge before writing an agent definition

## Proposed Solution

### 1. Research Prompt Infrastructure
- Create `templates/agent-research-prompt.md` template
- Create `agent_prompts/` directory with README and 2 generalized examples
- Document the research-to-agent pipeline in `docs/RESEARCH-PROMPT-GUIDE.md`

### 2. Reference Agent Archetypes
- Create `templates/reference-agents/` with 5 annotated archetype templates (~50-80 lines each):
  - Reviewer, Architect, Domain Expert, Orchestrator, Enforcer
- Each heavily annotated with `[CUSTOMIZE]` placeholders and explanatory comments

### 3. Pipeline Integration
- Extend `docs/AGENT-CREATION-GUIDE.md` with research phase and pipeline overview
- Create `tools/validation/validate-agent-pipeline.py` for pipeline artifact validation
- Update `agents/v3-setup-orchestrator.md` to support custom agent creation

### 4. End-to-End Validation
- Create a real agent (code-review-specialist) using the pipeline to prove it works
- Document findings in retrospective

## Implementation Plan

**Effort:** Medium (8 steps)
**Dependencies:** None (builds on existing infrastructure)

## Success Criteria

- [ ] Research prompt template is usable and produces structured output
- [ ] All 5 reference agents pass `validate-agent-format.py`
- [ ] Pipeline documentation has no broken cross-references
- [ ] Test agent created via pipeline passes all validation
- [ ] v3-setup-orchestrator still works for download-only workflow
- [ ] Retrospective documents pipeline strengths and areas for refinement

## Risks & Mitigation

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Reference agents too generic to be useful | Medium | Medium | Base on real production agents, test with end-to-end creation |
| v3-orchestrator change breaks existing flow | Low | High | Additive change only, keep download-first as default |
| Pipeline too heavyweight for simple agents | Medium | Low | Document that simple agents can skip research phase |
