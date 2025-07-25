<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [AI-First SDLC - Quick Reference Card](#ai-first-sdlc---quick-reference-card)
  - [🚀 Essential Commands](#-essential-commands)
    - [Starting Work (Zero Technical Debt Workflow)](#starting-work-zero-technical-debt-workflow)
    - [During Development](#during-development)
    - [Ending Session](#ending-session)
  - [📋 Progress Tracking](#-progress-tracking)
  - [💾 Context Management](#-context-management)
  - [✅ Validation](#-validation)
  - [🚫 Zero Technical Debt Commands](#-zero-technical-debt-commands)
  - [🛡️ Branch Protection](#-branch-protection)
  - [📝 Templates](#-templates)
    - [Feature Proposal](#feature-proposal)
    - [Task Format](#task-format)
  - [🔄 Workflow States](#-workflow-states)
    - [Task Status Flow](#task-status-flow)
    - [Branch Naming](#branch-naming)
  - [⚡ Common Workflows](#-common-workflows)
    - [New Feature (Human)](#new-feature-human)
    - [Continue Work (AI)](#continue-work-ai)
    - [Quick Validation](#quick-validation)
  - [🚫 Things to NEVER Do](#-things-to-never-do)
  - [🆘 Quick Fixes](#-quick-fixes)
    - [On wrong branch?](#on-wrong-branch)
    - [Forgot proposal?](#forgot-proposal)
    - [Lost context?](#lost-context)
  - [📊 Status Icons](#-status-icons)
  - [🔗 Integration](#-integration)
    - [Pre-commit Hook](#pre-commit-hook)
    - [Authentication Setup](#authentication-setup)
  - [🔧 CI/CD Integration](#-cicd-integration)
    - [GitHub Actions](#github-actions)
    - [GitLab CI](#gitlab-ci)
    - [Jenkins](#jenkins)
    - [Azure DevOps](#azure-devops)
    - [CircleCI](#circleci)
    - [Common CI Commands](#common-ci-commands)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# AI-First SDLC - Quick Reference Card

## 🚀 Essential Commands

### Starting Work (Zero Technical Debt Workflow)
```bash
# 1. Create feature branch
git checkout -b feature/name

# 2. Create architecture documents FIRST (mandatory)
# Create all 6 documents in templates/architecture/
# - requirements-traceability-matrix.md
# - what-if-analysis.md
# - architecture-decision-record.md
# - system-invariants.md
# - integration-design.md
# - failure-mode-analysis.md

# 3. Validate architecture before coding
python tools/validation/validate-architecture.py --strict

# 4. Only then proceed with tasks
python tools/automation/progress-tracker.py list
python tools/automation/context-manager.py load
```

### During Development
```bash
python tools/progress-tracker.py update <id> in_progress  # Start task
python tools/progress-tracker.py update <id> completed    # Complete task
python tools/validate-pipeline.py                         # Validate work
```

### Ending Session
```bash
python tools/context-manager.py handoff \
  --completed "Task 1" \
  --current "Task 2" \
  --next "Task 3"
```

---

## 📋 Progress Tracking

```bash
# Add tasks
progress-tracker.py add "Task description" --priority high

# Update status
progress-tracker.py update <id> in_progress|completed|blocked

# List tasks
progress-tracker.py list [--status pending|in_progress|completed|blocked]

# Generate report
progress-tracker.py report [--output report.md]
```

---

## 💾 Context Management

```bash
# Save work context
context-manager.py save work --data '{"key": "value"}'

# Create handoff
context-manager.py handoff \
  --completed "Done 1" "Done 2" \
  --current "Doing now" \
  --next "Todo 1" "Todo 2" \
  --blocker "Issue:Impact:Resolution"

# Create snapshot
context-manager.py snapshot "feature" "phase" --files file1.py file2.py

# List contexts
context-manager.py list [--type handoff|work|snapshot]
```

---

## ✅ Validation

```bash
# Run all checks
validate-pipeline.py

# Specific checks
validate-pipeline.py --checks branch proposal tests architecture technical-debt type-safety

# Export results
validate-pipeline.py --export json|markdown --output file

# CI mode
validate-pipeline.py --ci

# Architecture validation (Zero Technical Debt)
validate-architecture.py --strict

# Technical debt detection
check-technical-debt.py --threshold 0
check-technical-debt.py --format json --output debt-report.json

# Check feature proposal
check-feature-proposal.py --branch feature/branch-name
```

---

## 🚫 Zero Technical Debt Commands

```bash
# Architecture validation (run BEFORE writing any code)
python tools/validation/validate-architecture.py --strict

# Technical debt detection (zero tolerance)
python tools/validation/check-technical-debt.py --threshold 0

# Type safety validation
python tools/validation/validate-pipeline.py --checks type-safety

# Full Zero Technical Debt validation
python tools/validation/validate-pipeline.py --checks architecture technical-debt type-safety

# Generate debt report
python tools/validation/check-technical-debt.py \
  --format json \
  --output debt-report.json
```

---

## 🛡️ Branch Protection

```bash
# Recommended: Using GitHub CLI (secure)
setup-branch-protection-gh.py

# Alternative: Using token
setup-branch-protection.py --platform github --repo owner/repo --token TOKEN

# Dry run
setup-branch-protection-gh.py --dry-run
```

---

## 📝 Templates

### Feature Proposal
```markdown
Target Branch: `feature/branch-name`
## Motivation
Why this feature is needed

## Proposed Solution
What we'll build

## Success Criteria
How we'll know it works
```

### Task Format
```bash
"[Component] Action to take"
# Examples:
"[API] Implement user authentication endpoint"
"[Frontend] Create login form with validation"
"[Database] Add user sessions table"
```

---

## 🔄 Workflow States

### Task Status Flow
```
pending → in_progress → completed
         ↘           ↗
            blocked
```

### Branch Naming
```
feature/description    # New features
fix/issue-description  # Bug fixes
enhancement/details    # Improvements
```

---

## ⚡ Common Workflows

### New Feature (Human)
```bash
git checkout -b feature/name
cp docs/feature-proposals/template-* docs/feature-proposals/01-name.md
# Edit proposal with Target Branch
git add . && git commit -m "feat: add feature proposal"
```

### Continue Work (AI)
```bash
context-manager.py load
progress-tracker.py list --status in_progress
# ... work ...
context-manager.py handoff --completed "X" --next "Y"
```

### Quick Validation
```bash
validate-pipeline.py --checks branch proposal
```

---

## 🚫 Things to NEVER Do

1. ❌ `git push origin main` - Never push to main directly
2. ❌ Skip feature proposals - Always document intent first
3. ❌ Leave tasks in_progress - Update status before switching
4. ❌ End session without handoff - Always preserve context

---

## 🆘 Quick Fixes

### On wrong branch?
```bash
git stash
git checkout -b feature/correct-name
git stash pop
```

### Forgot proposal?
```bash
cp docs/feature-proposals/template-* docs/feature-proposals/retroactive.md
# Add: Target Branch: `current-branch-name`
```

### Lost context?
```bash
context-manager.py list --limit 10
git log --oneline -20
```

---

## 📊 Status Icons

- ✅ Completed
- 🚧 In Progress  
- ⏸️ Pending
- 🚫 Blocked
- ⚠️ Warning
- ❌ Error

---

## 🔗 Integration

### Pre-commit Hook
```bash
pre-commit install        # Set up hooks
pre-commit run --all     # Run manually
git commit --no-verify   # Emergency bypass
```

### Authentication Setup
```bash
# Recommended (most secure):
gh auth login             # GitHub CLI authentication

# Alternative (less secure):
export GITHUB_TOKEN=xxx   # For branch protection
export GITLAB_TOKEN=xxx   # For GitLab
export BITBUCKET_TOKEN=xxx # For Bitbucket
```

---

## 🔧 CI/CD Integration

### GitHub Actions
```bash
# Add to: .github/workflows/ai-sdlc.yml
# Runs on: push, pull_request
# See: examples/ci-cd/.github/workflows/
```

### GitLab CI
```bash
# Add to: .gitlab-ci.yml  
# Stages: validate, quality
# See: examples/ci-cd/gitlab/
```

### Jenkins
```bash
# Add to: Jenkinsfile
# Type: Declarative Pipeline
# See: examples/ci-cd/jenkins/
```

### Azure DevOps
```bash
# Add to: azure-pipelines.yml
# Stages: Validate, Reporting
# See: examples/ci-cd/azure-devops/
```

### CircleCI
```bash
# Add to: .circleci/config.yml
# Workflows: ai-first-sdlc
# See: examples/ci-cd/circleci/
```

### Common CI Commands
```bash
# CI mode (proper exit codes)
validate-pipeline.py --ci

# Specific checks for CI
validate-pipeline.py --check tests --ci
validate-pipeline.py --check security --ci

# Export for CI artifacts
validate-pipeline.py --ci --format json > report.json
```

---

**Remember**: When in doubt, run `validate-pipeline.py`!