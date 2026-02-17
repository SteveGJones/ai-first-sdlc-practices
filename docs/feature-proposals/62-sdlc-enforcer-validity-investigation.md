# Feature Proposal: SDLC Enforcer Validity Investigation (#62)

**Target Branch:** `feature/sdlc-enforcer-validity-investigation`
**Date:** 2026-02-10
**Author:** AI Investigation Team

## Motivation

The `agents/core/sdlc-enforcer.md` agent works correctly within this repository but has been reported as "not valid" when downloaded and installed into two separate external projects. Both projects required patches to make the enforcer functional. This investigation identifies the root causes and fixes the underlying issues.

## Investigation Findings

### Root Cause Summary

The core problem is **specification drift**: the AGENT-FORMAT-SPEC.md defines strict limits that the validate-agent-format.py validator does not enforce, and the sdlc-enforcer (along with many other agents) exceeds the spec limits. When external projects rely on the spec (or Claude Code enforces its own limits), agents fail validation.

### Finding 1: Description Length - Spec Says 150, Validator Allows 500

**AGENT-FORMAT-SPEC.md** (line 49): `max 150 chars`
**validate-agent-format.py** (line 51): `MAX_DESCRIPTION_LENGTH = 500`

The sdlc-enforcer description is **354 characters** — well over the spec's 150-char limit but within the validator's relaxed 500-char limit. This means:
- The agent passes our local validator
- A spec-compliant validator in another project would reject it
- Claude Code's native agent loader may enforce the spec limit

**Impact**: 18 of 29 core agents exceed the 150-char spec limit.

### Finding 2: Content Body Size - Spec Says 10,000, Validator Ignores

**AGENT-FORMAT-SPEC.md** (line 199): `Maximum 10,000 characters`
**validate-agent-format.py**: **No content max enforcement at all**

The sdlc-enforcer body is **34,686 characters** (3.5x the spec limit, 17.3x the recommended 2,000 chars). It is 838 lines / 37KB — the largest agent system prompt in the repo.

**Impact**: Most production-tier agents exceed 10,000 chars. This is by design (they need detailed methodology), but the spec doesn't reflect reality.

### Finding 3: Undocumented Frontmatter Fields (tools, model)

The sdlc-enforcer includes `tools: [Read, Glob, Grep, Bash]` and `model: sonnet` in its YAML frontmatter. These fields are **used by Claude Code natively** but are **not documented in AGENT-FORMAT-SPEC.md**.

The spec lists optional fields as: version, category, priority, maturity, tags. The `tools` and `model` fields are absent.

**Impact**: 10 of 29 core agents have undocumented `tools` and `model` fields. A strict spec validator would reject these as unknown fields.

### Finding 4: Content Structure Validation Too Strict

The validator requires the exact phrase "Your core competencies include" (case-insensitive) in the body. In strict mode, **13 of 29 core agents fail** this check because they use different headings like "Core Capabilities", "Key Competencies", or "What You Do".

The sdlc-enforcer passes because it happens to use "Your Core Competencies Include" as a heading.

### Finding 5: Setup Path Discrepancy

Two different installation methods produce different directory structures:

| Method | Installation Path | Claude Code Compatible? |
|--------|------------------|------------------------|
| setup-smart.py (V2) | `.claude/agents/core/sdlc-enforcer.md` | Uncertain (subdirectory) |
| v3-setup-orchestrator | `.claude/agents/sdlc-enforcer.md` | Yes (flat) |

Claude Code loads agents from `.claude/agents/`. The subdirectory `core/` may or may not be scanned depending on Claude Code's implementation.

### Finding 6: No Post-Download Validation

Neither setup-smart.py nor v3-setup-orchestrator validates agent files after downloading. The only check is `[ -s file ]` (non-empty). A 404 HTML page or truncated download would pass this check and be installed as an "agent".

### Finding 7: CI Validation Mismatch

Three different validation systems exist with different rules:

| System | Description Limit | Content Check | Unknown Fields |
|--------|------------------|---------------|----------------|
| AGENT-FORMAT-SPEC.md | 150 chars | Max 10,000 chars | Rejects |
| validate-agent-format.py | 500 chars | Min 100 chars only | Ignores |
| template-compliance.yml (CI) | None | Min 50 chars | Ignores |

## Proposed Solution

### Fix 1: Align AGENT-FORMAT-SPEC.md with Reality

- Update description max from 150 to 500 chars
- Add `tools` and `model` as optional fields
- Change content maximum from 10,000 to a warning at 50,000 (not blocking)
- Update recommended content range to 500-40,000 chars

### Fix 2: Update validate-agent-format.py

- Add content size warning (not error) above 50,000 chars
- Make "Your core competencies include" check case-insensitive and accept common alternatives ("Core Competencies", "Key Capabilities", "Core Expertise")
- Add validation for `tools` field (must be valid Claude Code tool names)
- Add validation for `model` field (must be valid Claude Code model alias)

### Fix 3: Fix setup-smart.py Installation Paths

- Change `.claude/agents/core/sdlc-enforcer.md` to `.claude/agents/sdlc-enforcer.md`
- Flatten all agent installation paths to match Claude Code's expected structure

### Fix 4: Add Post-Download Validation

- Run validate-agent-format.py after downloading agents
- Report validation errors to the user rather than silently installing invalid files

## Success Criteria

- [ ] AGENT-FORMAT-SPEC.md updated with tools/model fields and realistic limits
- [ ] validate-agent-format.py aligned with updated spec
- [ ] All 29 core agents pass validation in non-strict mode
- [ ] sdlc-enforcer passes validation in strict mode
- [ ] setup-smart.py uses flat .claude/agents/ paths
- [ ] Feature proposal and retrospective created

## Impact Assessment

**Risk**: Low-Medium — spec and validator changes; no agent content changes
**Effort**: Medium — multiple files need updating
**Value**: High — directly addresses the reported download validity failures
