# AI-First SDLC - Quick Reference Card

## 🚀 Essential Commands

### Starting Work
```bash
git checkout -b feature/name          # Create feature branch
python tools/progress-tracker.py list # See pending tasks
python tools/context-manager.py load  # Load previous session
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
validate-pipeline.py --checks branch proposal tests

# Export results
validate-pipeline.py --export json|markdown --output file

# CI mode
validate-pipeline.py --ci
```

---

## 🛡️ Branch Protection

```bash
# Auto-configure
setup-branch-protection.py

# Manual setup
setup-branch-protection.py --platform github --repo owner/repo --token TOKEN

# Dry run
setup-branch-protection.py --dry-run
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

### Environment Variables
```bash
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