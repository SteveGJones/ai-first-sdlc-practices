# Retrospective: SDLC Enforcer Validity Investigation (#62)

**Branch:** `feature/sdlc-enforcer-validity-investigation`
**Date:** 2026-02-10
**Feature:** Investigation into why sdlc-enforcer agent fails validation when downloaded to external projects

## What Went Well

1. **Systematic root cause analysis**: By reading the agent file, spec, validator, CI workflow, and setup scripts in parallel, the root cause was identified quickly as specification drift between three different validation systems.

2. **Quantitative findings**: Precise measurements (354 chars vs 150 spec limit, 34,686 chars vs 10,000 spec limit, 13/29 agents failing strict validation) made the problems concrete and actionable.

3. **Broad agent impact assessment**: Rather than just fixing the sdlc-enforcer, the investigation revealed that the problem affects 18 of 29 core agents (description length) and 13 of 29 (content structure), leading to systemic fixes.

4. **Three-system alignment**: The fix addresses all three validation systems (AGENT-FORMAT-SPEC.md, validate-agent-format.py, and CI template-compliance.yml) to prevent future drift.

## What Could Be Improved

1. **No access to the two affected projects**: The investigation was conducted without seeing the actual patches applied in the two external projects. Seeing those patches would confirm which specific failure mode triggered the issues.

2. **Claude Code native agent loading behavior is inferred, not confirmed**: The investigation infers how Claude Code validates `.claude/agents/` files based on documentation and research. Direct testing against Claude Code's parser would provide definitive answers.

3. **setup-smart.py subdirectory path issue**: The `.claude/agents/core/` subdirectory installation pattern may have been working if Claude Code does scan subdirectories. The fix to flatten paths is safer but the original behavior should be confirmed.

## Lessons Learned

1. **Spec documents must be kept in sync with validators**: When the validator's `MAX_DESCRIPTION_LENGTH` was increased from 150 to 500, the spec document was not updated. This created a hidden incompatibility for anyone building validators from the spec.

2. **Undocumented fields cause downstream failures**: The `tools` and `model` frontmatter fields were added to agents without updating AGENT-FORMAT-SPEC.md. Any project implementing spec-compliant validation would reject these agents.

3. **Content structure rules should be flexible**: Requiring the exact phrase "Your core competencies include" was too rigid. Agents naturally use varied headings ("Core Capabilities", "Key Expertise", etc.) and the validator should accept common variants.

4. **Large agent files are by design, not a bug**: Production-tier agents are 20,000-40,000 chars because they need detailed methodology, scenarios, and examples. The original spec's 10,000-char limit (and 2,000 recommended) was set before production agents existed.

## Key Metrics

| Metric | Value |
|--------|-------|
| Root causes identified | 7 |
| Files modified | 4 (spec, validator, setup-smart.py, feature proposal) |
| Files created | 2 (feature proposal, retrospective) |
| Agents previously failing strict validation | 13 of 29 |
| Agents now failing strict validation | 1 of 29 (data-architect stub) |
| Description limit updated | 150 -> 500 chars |
| New spec fields added | 2 (tools, model) |
| Content heading variants now accepted | 7 patterns |
