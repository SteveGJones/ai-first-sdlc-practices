# Agentic Team Collaboration Protocols

> **Version**: 1.0.0  
> **Status**: Active  
> **Last Updated**: 2025-08-07  
> **Context**: Derived from PR #29 recovery experience

## Overview

This document defines collaboration protocols for AI agent teams working on complex software development projects. These protocols emerged from real incident response where local validation disagreed with CI, confidence was misplaced, and systematic recovery was required.

## 1. Crisis Response Protocols

### When Local and CI Disagree: STOP Protocol

**Trigger**: Any discrepancy between local validation and CI results

**Immediate Actions**:
1. **HALT all progress** - Do not proceed with implementation
2. **ISOLATE the environment** - Fresh clone, clean state verification  
3. **DOCUMENT the discrepancy** - Exact commands, outputs, timestamps
4. **ESCALATE to diagnostic mode** - Switch from "fix" to "understand" mindset

**Recovery Steps**:
```bash
# Standard diagnostic sequence
git status                    # State verification
git log --oneline -3         # Recent changes context
python -m pytest --tb=short  # Controlled test execution
git clean -fd                # Environment reset if needed
```

**Success Criteria**: Local and CI produce identical results before proceeding

### When Confidence is Misplaced: Reset Protocol

**Triggers**:
- "This should work" followed by failure
- Multiple patch attempts without success
- Validation passing locally but failing in CI

**Reset Actions**:
1. **ADMIT uncertainty immediately** - "I was wrong, let me start over"
2. **RETURN to last known good state** - Git reset, fresh analysis
3. **QUESTION all assumptions** - Re-read error messages word-by-word
4. **SEEK evidence** - Reproduce issue in controlled environment

**Communication Pattern**:
```
❌ Bad: "Let me try one more quick fix..."
✅ Good: "I was overconfident. Let me step back and diagnose systematically."
```

### When Patches Fail: Escalation Protocol

**Rule**: After 2 failed patch attempts, escalate to systematic solution

**Escalation Path**:
1. **Individual Agent** (patches 1-2): Quick fixes, obvious solutions
2. **Team Diagnostic** (failure): Systematic analysis, root cause investigation
3. **Architecture Review** (if needed): Structural changes, design reconsideration

**Escalation Triggers**:
- Same error after 2 different fixes
- Increasing complexity of patches
- New errors introduced by fixes
- CI/local environment discrepancies

## 2. Team Communication Standards

### Discrepancy Reporting Format

**Required Elements**:
```markdown
## Validation Discrepancy Report

**Environment**: [Local/CI/Both]
**Component**: [Specific system/test/validation]
**Expected**: [What should happen]
**Actual**: [What actually happened]
**Commands**: [Exact commands used]
**Evidence**: [Screenshots, logs, output]
**Impact**: [What's blocked, severity]
```

### Escalation Triggers

**Individual → Team**:
- 2+ consecutive failures on same issue
- CI/local discrepancy discovered
- New error types appearing
- Time spent > 30 minutes without progress

**Team → Architecture**:
- Fundamental design assumptions questioned
- Multiple subsystems involved
- Solution requires breaking changes
- Pattern indicates systemic issue

### Handoff Protocols

**Giving Context**:
```markdown
## Agent Handoff

**Current State**: [Exact branch, commit, environment]
**Problem**: [Specific issue being addressed]
**Attempted**: [What's been tried, results]
**Next**: [Recommended next steps]
**Blockers**: [What's preventing progress]
**Context**: [Relevant background, decisions made]
```

**Receiving Context**:
1. **VERIFY state** - Reproduce current situation exactly
2. **CONFIRM understanding** - Restate problem in own words
3. **VALIDATE environment** - Ensure identical setup
4. **ACKNOWLEDGE handoff** - Explicit acceptance of responsibility

### Success and Failure Patterns

**Success Celebration**:
- Acknowledge specific techniques that worked
- Document reusable patterns
- Credit collaborative breakthroughs
- Update protocols with learnings

**Failure Analysis**:
- No blame, focus on process improvement
- Identify decision points where different choices would help
- Extract learnable patterns
- Update protocols to prevent recurrence

## 3. Collaborative Problem-Solving Framework

### The 5-Step Recovery Plan

Based on successful PR #29 recovery:

#### Step 1: Environment Isolation
```bash
# Create clean diagnostic environment
cd /tmp
git clone [repository] diagnostic-clone
cd diagnostic-clone
git checkout [problem-branch]
```

#### Step 2: Controlled Reproduction
```bash
# Minimal reproduction case
python -m pytest [specific-test] -v
# Or specific validation command that's failing
```

#### Step 3: Evidence Collection
- Capture exact error messages
- Document environment details
- Compare with working examples
- Identify minimal failing case

#### Step 4: Systematic Analysis
- Read error messages word-by-word
- Trace execution path
- Identify root cause vs. symptoms
- Map to known solutions

#### Step 5: Validated Solution
- Implement fix in isolation
- Test in clean environment
- Verify CI compatibility
- Apply to main branch

### Role Separation: DOERS vs VALIDATORS

**DOER Role**:
- Implements changes
- Focuses on forward progress
- Optimistic about solutions
- Responsible for delivery

**VALIDATOR Role**:
- Questions assumptions
- Focuses on correctness
- Skeptical of quick fixes
- Responsible for quality

**Protocol**: Each agent should explicitly declare their role and perspective when collaborating.

### Mathematical Approach Requirements

When dealing with technical issues:

1. **Exact Reproduction**: Same inputs must produce same outputs
2. **Controlled Variables**: Change one thing at a time
3. **Evidence-Based Decisions**: Data over intuition
4. **Falsifiable Hypotheses**: "If X, then Y" statements that can be tested

### Evidence Collection Standards

Before proposing solutions:
- **Screenshot/Copy exact error messages**
- **Document exact commands used**
- **Capture environment details** (Python version, dependencies, OS)
- **Show before/after comparisons**
- **Provide minimal reproduction case**

## 4. Quality Gate Responsibilities

### Stage-Based Validation

**Development Stage**:
- **Who**: Individual agent implementing feature
- **Validates**: Local functionality, basic tests pass
- **Blocks**: Implementation continues only if basic functionality works
- **Escalates**: To team if local validation fails repeatedly

**Integration Stage**:
- **Who**: Second agent or specialized validator
- **Validates**: CI compatibility, full test suite, integration points
- **Blocks**: PR creation until all CI checks pass
- **Escalates**: To architecture review if systematic issues found

**Review Stage**:
- **Who**: Critical goal reviewer or solution architect
- **Validates**: Requirements alignment, code quality, documentation
- **Blocks**: Merge until all quality criteria met
- **Escalates**: To stakeholders if requirements need clarification

### CI/Local Parity Requirements

**Parity Check Protocol**:
```bash
# Must produce identical results
local_result=$(python -m pytest --tb=short 2>&1)
# Compare with CI output exactly
# Any discrepancy triggers STOP protocol
```

**Responsible Parties**:
- **Developer**: Ensures local validation is comprehensive
- **CI Designer**: Ensures CI exactly matches local environment
- **Quality Gate**: Blocks progress when parity is broken

### Progress vs. Quality Decisions

**Allow Continuation When**:
- Tests pass in both environments
- Progress is measurable and documented
- Risk is contained and reversible
- Team agrees on approach

**Block Progress When**:
- CI/local discrepancy exists
- New errors introduced by changes
- Quality metrics degrading
- Architecture assumptions violated

### Escalation Paths for Quality Violations

**Level 1**: Individual agent problem-solving (up to 30 minutes)
**Level 2**: Team diagnostic (systematic approach, multiple agents)
**Level 3**: Architecture review (design-level changes needed)
**Level 4**: Stakeholder consultation (requirements or timeline changes)

## 5. Continuous Improvement Rituals

### Post-Incident Reviews

**Timing**: Within 24 hours of issue resolution

**Format**:
```markdown
## Post-Incident Review: [Issue Name]

**Duration**: [Start time] to [Resolution time]
**Impact**: [What was affected, severity]

**Timeline**:
- [Time]: [What happened]
- [Time]: [Decision made]
- [Time]: [Action taken]

**What Went Well**:
- [Specific techniques, decisions, collaborations]

**What Could Improve**:
- [Process gaps, knowledge gaps, tool issues]

**Action Items**:
- [ ] [Specific improvement with owner and deadline]
- [ ] [Protocol update needed]
- [ ] [Tool/automation opportunity]
```

### Knowledge Capture Requirements

**Memory Bank Updates**:
- Successful patterns that can be reused
- Failed approaches to avoid
- Environment-specific gotchas
- Tool limitations discovered

**Instruction Evolution**:
- Update protocols based on new learnings
- Add specific examples from real incidents
- Remove obsolete or ineffective guidance
- Integrate successful patterns into standard workflow

### Success Metric Tracking

**Quality Metrics**:
- Time from issue detection to resolution
- Number of patch attempts before success
- CI/local parity maintenance rate
- Escalation frequency and effectiveness

**Collaboration Metrics**:
- Handoff success rate (clean context transfer)
- Team diagnostic effectiveness
- Knowledge retention between incidents
- Protocol adherence rate

**Improvement Metrics**:
- Reduced time to resolution over time
- Fewer repeated mistakes
- Better initial problem diagnosis
- More effective escalation decisions

## Implementation Guidelines

### For Individual Agents

1. **Always declare your role** (DOER or VALIDATOR) when joining collaboration
2. **Use exact protocol language** when escalating or reporting issues
3. **Document decisions and reasoning** for future agents
4. **Admit uncertainty quickly** rather than pursuing failed approaches

### For Team Leaders

1. **Enforce STOP protocol** when CI/local discrepancies arise
2. **Manage role separation** between DOERs and VALIDATORs
3. **Drive post-incident reviews** within 24 hours
4. **Update protocols** based on learnings

### For Quality Gates

1. **Block progress decisively** when quality criteria not met
2. **Require evidence** before accepting "should work" claims
3. **Escalate systematically** through defined paths
4. **Maintain CI/local parity** as non-negotiable requirement

## Protocol Versioning

This document will be updated based on:
- **Incident experiences** (like PR #29)
- **Team feedback** on protocol effectiveness
- **Metric analysis** showing improvement opportunities
- **Tool evolution** that changes collaboration patterns

All updates require:
- **Evidence base** from real incidents
- **Team consensus** on protocol changes
- **Version tracking** with change rationale
- **Training update** for affected agents

---

## Quick Reference Card

**Crisis Response**: STOP → ISOLATE → DOCUMENT → ESCALATE  
**Confidence Reset**: ADMIT → RETURN → QUESTION → SEEK  
**Patch Failure**: 2 attempts → Team diagnostic → Systematic solution  
**Handoff**: VERIFY → CONFIRM → VALIDATE → ACKNOWLEDGE  
**Quality Gate**: Evidence required → Block until met → Escalate systematically  

**Remember**: Better to be slow and right than fast and wrong. The framework supports systematic problem-solving over quick fixes.