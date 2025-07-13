<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [AI-First SDLC Workflow: Retrospective-First Approach](#ai-first-sdlc-workflow-retrospective-first-approach)
  - [Why Retrospectives Before PR?](#why-retrospectives-before-pr)
  - [The Complete Workflow](#the-complete-workflow)
  - [Step-by-Step Process](#step-by-step-process)
    - [1. Create Feature Proposal](#1-create-feature-proposal)
    - [2. Start Retrospective Immediately](#2-start-retrospective-immediately)
    - [3. Update Retrospective During Development](#3-update-retrospective-during-development)
    - [4. Complete Retrospective Before PR](#4-complete-retrospective-before-pr)
    - [5. Validation Will Check](#5-validation-will-check)
  - [Example Retrospective Update Flow](#example-retrospective-update-flow)
  - [Benefits of This Approach](#benefits-of-this-approach)
  - [Common Mistakes to Avoid](#common-mistakes-to-avoid)
  - [Integration with AI Agents](#integration-with-ai-agents)
  - [Enforcement](#enforcement)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# AI-First SDLC Workflow: Retrospective-First Approach

## Why Retrospectives Before PR?

Retrospectives are not just post-mortem documents - they're living records of your development journey. By requiring retrospectives **before** creating a Pull Request, we ensure:

1. **Complete Documentation**: All lessons learned are captured while fresh
2. **Quality Gates**: PRs can't be rushed without proper reflection
3. **Continuous Learning**: Teams benefit from insights immediately
4. **Definition of Done**: Work isn't complete until documented

## The Complete Workflow

```
┌─────────────────┐     ┌──────────────┐     ┌───────────────┐     ┌──────────────┐     ┌─────────┐
│ Feature Proposal│ ──► │Implementation│ ──► │ Retrospective │ ──► │ Pull Request │ ──► │  Merge  │
│   (REQUIRED)    │     │  (on branch) │     │  (REQUIRED)   │     │   (Review)   │     │ (main)  │
└─────────────────┘     └──────────────┘     └───────────────┘     └──────────────┘     └─────────┘
       ↑                                              ↑
       └──────────── MUST happen first ───────────────┘
                                                      │
                                          MUST happen BEFORE PR ───┘
```

## Step-by-Step Process

### 1. Create Feature Proposal
```bash
# Create proposal document
docs/feature-proposals/01-new-feature.md

# Switch to feature branch
git checkout -b feature/new-feature
```

### 2. Start Retrospective Immediately
```bash
# Create retrospective file at the START
echo "# Retrospective: New Feature

**Feature**: New Feature Implementation
**Branch**: feature/new-feature
**Date**: $(date +%Y-%m-%d)
**Author**: [Your Name]

## What Went Well
- [To be updated as you work]

## What Could Be Improved  
- [To be updated as you work]

## Lessons Learned
- [To be updated as you work]
" > retrospectives/01-new-feature.md

# Commit it immediately
git add retrospectives/01-new-feature.md
git commit -m "docs: start retrospective for new feature"
```

### 3. Update Retrospective During Development
As you work, continuously update the retrospective:

- **After fixing a bug**: Document what caused it and how you fixed it
- **After a design decision**: Record why you chose that approach
- **After discovering an issue**: Note what could be improved in the process
- **After successful implementation**: Document what worked well

### 4. Complete Retrospective Before PR
Before creating your PR, ensure the retrospective includes:

- [ ] Summary of what was implemented
- [ ] At least 3 items in "What Went Well"
- [ ] At least 2 items in "What Could Be Improved"
- [ ] Key lessons learned for future work
- [ ] Any action items for the team

### 5. Validation Will Check
The validation pipeline (`python tools/validate-pipeline.py`) will:
- Check if a retrospective exists for your branch
- Verify it mentions your branch/feature name
- **Error** if missing during PR validation (blocking merge)
- **Warning** if missing during local development

## Example Retrospective Update Flow

```bash
# After implementing a complex algorithm
git add -A
git commit -m "feat: implement sorting algorithm"

# Immediately update retrospective
echo "
## What Went Well (Updated $(date))
- The sorting algorithm handles edge cases well
- Performance testing showed O(n log n) as expected
- Unit tests caught an off-by-one error early
" >> retrospectives/01-new-feature.md

git add retrospectives/01-new-feature.md
git commit -m "docs: update retrospective with algorithm insights"
```

## Benefits of This Approach

1. **Real-time Learning**: Insights are captured when fresh, not reconstructed later
2. **Better PRs**: Reviewers see the journey, not just the destination  
3. **Team Knowledge**: Lessons learned are shared before merge, not after
4. **Process Compliance**: Automated validation ensures no shortcuts
5. **Historical Record**: Future developers understand the "why" behind decisions

## Common Mistakes to Avoid

❌ **DON'T**: Wait until the end to write the entire retrospective
✅ **DO**: Update it incrementally as you work

❌ **DON'T**: Write generic statements like "everything went well"
✅ **DO**: Be specific about what worked and what didn't

❌ **DON'T**: Skip the retrospective thinking "it's just a small change"
✅ **DO**: Every feature deserves reflection, no matter the size

❌ **DON'T**: Only document failures
✅ **DO**: Celebrate successes and document effective patterns

## Integration with AI Agents

When working with AI agents like Claude, the retrospective serves as:
- A record of AI-human collaboration effectiveness
- Documentation of prompts that worked well
- Insights into AI limitations discovered
- Patterns for future AI-assisted development

## Enforcement

The framework enforces retrospectives through:

1. **Validation Pipeline**: Checks for retrospective existence
2. **CI/CD Integration**: Blocks PRs without retrospectives
3. **Branch Protection**: Requires validation checks to pass
4. **Documentation**: Clear requirements in CLAUDE.md and templates

Remember: **A feature isn't done until its story is told!**