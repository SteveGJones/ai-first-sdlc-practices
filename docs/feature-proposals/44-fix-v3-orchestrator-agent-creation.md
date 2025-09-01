# Feature Proposal: Fix V3 Orchestrator Agent Creation Issues

**Target Branch:** `feature/fix-v3-orchestrator-agent-creation`

## Motivation

Critical bugs in the v3-setup-orchestrator are preventing successful framework installations, leaving projects without essential files like CLAUDE.md and causing agent installation failures. These issues were discovered during real-world usage where installations failed completely.

## Problem Statement

The v3-setup-orchestrator has critical bugs that cause framework installation failures:

1. **Agent Creation Confusion**: The orchestrator uses ambiguous `Write:` syntax that appears to instruct creating agents from scratch rather than moving downloaded files
2. **Missing CLAUDE.md**: The orchestrator never downloads or installs CLAUDE.md, CLAUDE-CORE.md, or other mandatory framework files
3. **No Verification**: No checks to ensure critical files were successfully installed

These issues manifested in a real installation where:
- The orchestrator tried to create agents without downloading templates (user had to override twice)
- No CLAUDE.md file was created, leaving the project without framework instructions

## Proposed Solution

### 1. Fix Agent Installation Instructions
- Replace ambiguous `Write:` commands with explicit `mv` commands
- Download all files to `/tmp/` first, then move to final locations
- Add clear comments that agents must NEVER be created, only downloaded

### 2. Add Mandatory Framework Files
- Always download CLAUDE.md, CLAUDE-CORE.md, and SDLC-RULES-SUMMARY.md
- Install these at project root (not in hidden directories)
- Make these downloads happen FIRST, before any agents

### 3. Add Verification Steps
- Add bash verification that checks for CLAUDE.md existence
- Fail installation if critical files are missing
- Provide retry instructions if downloads fail

### 4. Add Clear Warnings
- Add "CRITICAL RULES - NEVER VIOLATE" section at top of orchestrator
- Explicitly state agents must be downloaded, never created
- Emphasize CLAUDE.md is mandatory, not optional

## Implementation Plan

1. Update `/agents/v3-setup-orchestrator.md` with:
   - Critical rules section
   - Fixed download commands using `/tmp/`
   - Explicit `mv` commands instead of `Write:`
   - Mandatory verification checks
   - Updated example showing CLAUDE.md installation

2. Copy updated version to `.claude/agents/` for immediate use

## Success Criteria

- V3 orchestrator always downloads agents from repository
- CLAUDE.md is always installed during setup
- Installation fails with clear error if critical files are missing
- No ambiguous instructions that could be misinterpreted

## Risk Assessment

- Low risk: Changes are to documentation/instructions only
- High impact: Fixes critical installation failures
- Immediate benefit: Prevents broken installations

## Timeline

- Implementation: Immediate
- Testing: Verify in next project setup
- Rollout: Available immediately after merge
