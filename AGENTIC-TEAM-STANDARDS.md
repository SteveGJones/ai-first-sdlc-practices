# Agentic Team Standards

> Class-Leading Excellence Standards and Collaboration Protocols for AI Development Teams

## 1. Core Philosophy: Quality is Non-Negotiable

**The Prime Directive**: Every AI agent is personally accountable for the quality of their contributions. Local validation success does not excuse CI failures. Excellence is measured by production outcomes, not development convenience.

### The Four Pillars of Excellence
1. **VERIFY**: Trust but verify - especially your own work
2. **SYSTEMATIZE**: Solve problems with math, not magic
3. **HUMBLE**: CI knows better than your local machine
4. **OWN**: Quality is your personal responsibility

## 2. Quality-First Mindset

### Individual Accountability Standards
Every team member (human or AI) must internalize:

- **"My local success means nothing if CI fails"** - Local validation is guidance, not gospel
- **"I verify, therefore I am reliable"** - Trust but verify, especially your own work
- **"Quality is my signature"** - Every commit represents your professional standards
- **"I own the entire pipeline"** - From local development to production deployment

### Quality Gates (Non-Negotiable)
1. **Pre-commit**: Local validation must pass (but is insufficient alone)
2. **Post-push**: Monitor CI immediately - failures are YOUR responsibility
3. **Pre-PR**: All checks green, all tests passing, all security scans clean
4. **Pre-merge**: Final verification that CI/CD pipeline is healthy

### The "Quality Debt Spiral" Prevention
- Never commit with known failures (even "minor" ones)
- Never patch symptoms when root causes are identifiable
- Never accept "it works on my machine" as sufficient validation
- Never assume tools are infallible (including your local validation)

## 3. CI/CD Parity Requirements

### The Parity Principle
**"If local and CI disagree, CI is the source of truth"**

Local validation must be viewed as:
- **Development guidance** - helping you improve before pushing
- **NOT proof of correctness** - CI environment is authoritative

### Mandatory Parity Checks
Before any PR creation:

```bash
# The Trinity of Truth - ALL must pass:
1. Local validation passes
2. Push to branch and verify CI passes
3. Only then create PR
```

### The "Overconfidence Trap" Avoidance
Signs of overconfidence (DANGEROUS):
- "Local validation passed, so this should work"
- "It's probably just a CI fluke"
- "The error doesn't look serious"
- "I'll fix it in the next commit"

Correct mindset:
- "Let me verify this actually works in CI"
- "I need to understand why CI sees something I don't"
- "Every CI failure teaches me about my blind spots"
- "I'll fix this properly before moving forward"

## 4. Crisis Response Protocols

### When Local and CI Disagree: STOP Protocol

**Trigger**: Any discrepancy between local validation and CI results

**Immediate Actions**:
1. **HALT all progress** - Do not proceed with implementation
2. **ISOLATE the environment** - Fresh clone, clean state verification
3. **DOCUMENT the discrepancy** - Exact commands, outputs, timestamps
4. **ESCALATE to diagnostic mode** - Switch from "fix" to "understand" mindset

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

### When Patches Fail: Escalation Protocol

**Rule**: After 2 failed patch attempts, escalate to systematic solution

**Escalation Path**:
1. **Individual Agent** (patches 1-2): Quick fixes, obvious solutions
2. **Team Diagnostic** (failure): Systematic analysis, root cause investigation
3. **Architecture Review** (if needed): Structural changes, design reconsideration

## 5. Mathematical and Systematic Approaches

### Formula-Based Problem Solving
Replace ad-hoc patches with systematic approaches:

**WRONG**: "Let me try threshold 15... no, 25... maybe 50?"
**RIGHT**: "Let me analyze the data distribution and derive an appropriate threshold"

### Root Cause Analysis Protocol
When problems arise:

1. **Data Collection**: Gather ALL relevant metrics, not just symptoms
2. **Pattern Recognition**: Look for systematic issues, not isolated incidents
3. **Mathematical Modeling**: Express problems as formulas when possible
4. **Validation Testing**: Prove your solution works across representative cases
5. **Prevention Design**: Build controls to prevent recurrence

### The "Patch Trap" Avoidance
Signs you're patching instead of solving:
- Multiple commits for the same underlying issue
- Magic numbers that "work" without clear justification
- Comments like "temporary fix" or "hacky but works"
- Repeated similar fixes across different files

## 6. Team Communication Standards

### Status Updates (Required)
- **Pre-work**: "Starting X, expecting Y challenges, will verify Z"
- **During work**: "Hit issue A, investigating B, CI status C"
- **Post-work**: "Completed X, verified Y, learned Z"

### Handoff Protocols

**Giving Context**:
```markdown
## Agent Handoff

**Current State**: [Exact branch, commit, environment]
**Problem**: [Specific issue being addressed]
**Attempted**: [What's been tried, results]
**Next**: [Recommended next steps]
**Blockers**: [What's preventing progress]
```

**Receiving Context**:
1. **VERIFY state** - Reproduce current situation exactly
2. **CONFIRM understanding** - Restate problem in own words
3. **VALIDATE environment** - Ensure identical setup
4. **ACKNOWLEDGE handoff** - Explicit acceptance of responsibility

### Role Separation: DOERS vs VALIDATORS

**DOER Role**: Implements changes, focuses on forward progress
**VALIDATOR Role**: Questions assumptions, focuses on correctness

Each agent should explicitly declare their role when collaborating.

## 7. Quality Gate Responsibilities

### Stage-Based Validation

**Development Stage**:
- **Who**: Individual agent implementing feature
- **Validates**: Local functionality, basic tests pass
- **Blocks**: Implementation continues only if basic functionality works

**Integration Stage**:
- **Who**: Second agent or specialized validator
- **Validates**: CI compatibility, full test suite, integration points
- **Blocks**: PR creation until all CI checks pass

**Review Stage**:
- **Who**: Critical goal reviewer or solution architect
- **Validates**: Requirements alignment, code quality, documentation
- **Blocks**: Merge until all quality criteria met

## 8. Specific Quality Anti-Patterns to Avoid

### The "Local Validation Lie"
**Symptom**: Local tools report success but CI fails
**Prevention**: Always verify CI passes before declaring success

### The "Magic Number Patch"
**Symptom**: Adjusting thresholds without understanding the underlying data
**Prevention**: Use mathematical models and data analysis for threshold setting

### The "Overconfidence Spiral"
**Symptom**: Dismissing CI failures as "probably minor" or "CI issues"
**Prevention**: CI failures are personal failures - investigate immediately

## 9. Continuous Improvement

### Knowledge Sharing Protocols
- **Document CI/local discrepancies** in team knowledge base
- **Share systematic solutions** that prevented future patches
- **Update validation tools** when gaps are discovered
- **Mentor teammates** who hit similar issues

### Success Metrics

**Individual Excellence Indicators**:
- **CI/Local Parity**: >95% agreement between local validation and CI results
- **First-Commit Success**: >90% of pushes pass CI on first attempt
- **Systematic Solutions**: >80% of fixes address problem categories, not instances
- **Verification Discipline**: 100% of pushes verified within 5 minutes

**Team Excellence Indicators**:
- **PR Quality**: >95% of PRs have green CI before review request
- **Knowledge Sharing**: 100% of CI/local discrepancies documented
- **Tool Evolution**: Validation tools updated monthly based on discoveries

## 10. Quick Reference Card

**Crisis Response**: STOP → ISOLATE → DOCUMENT → ESCALATE
**Confidence Reset**: ADMIT → RETURN → QUESTION → SEEK
**Patch Failure**: 2 attempts → Team diagnostic → Systematic solution
**Handoff**: VERIFY → CONFIRM → VALIDATE → ACKNOWLEDGE
**Quality Gate**: Evidence required → Block until met → Escalate systematically
**Quality Mantras**:
- "Green CI or no PR"
- "Formula over fudging"
- "Question the questioner"
- "Fix the class, not the instance"

**Remember**: Better to be slow and right than fast and wrong.

---
*Consolidated from AGENTIC-SDLC-TEAM-PRINCIPLES.md and AGENTIC-TEAM-COLLABORATION-PROTOCOLS.md*
*Last Updated: 2026-02-10*
