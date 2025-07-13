# AI-First SDLC Framework - HOWTO Guide

This guide explains how to use the AI-First SDLC Framework in your daily development workflow, whether you're an AI agent or a human developer.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Core Workflow](#core-workflow)
3. [For AI Agents](#for-ai-agents)
4. [For Human Developers](#for-human-developers)
5. [Tool Usage Guide](#tool-usage-guide)
6. [Common Scenarios](#common-scenarios)
7. [Troubleshooting](#troubleshooting)

---

## Quick Start

### 1. Initial Setup (5 minutes)

#### Smart Setup (Recommended)
```bash
# Download and run smart setup (no cloning needed)
curl -sSL https://raw.githubusercontent.com/SteveGJones/ai-first-sdlc-practices/main/setup-smart.py > setup-smart.py
python setup-smart.py "building a todo app with React and Node.js"
```

#### Manual Setup (Alternative)
```bash
# Clone the framework
git clone https://github.com/SteveGJones/ai-first-sdlc-practices.git

# Copy templates to your project
cd your-project
cp ai-first-sdlc-practices/templates/* .

# Set up branch protection
python ai-first-sdlc-practices/tools/automation/setup-branch-protection-gh.py
```

### 2. Create Your First Feature

```bash
# Create a feature branch
git checkout -b feature/user-authentication

# Create a feature proposal
cp docs/feature-proposals/template-feature-proposal.md \
   docs/feature-proposals/01-user-authentication.md

# Edit the proposal with your feature details
# Make sure to set: Target Branch: `feature/user-authentication`

# Start tracking your work
python tools/progress-tracker.py add "Design authentication flow"
python tools/progress-tracker.py add "Implement login endpoint"
python tools/progress-tracker.py add "Add session management"
```

---

## Core Workflow

### The AI-First Development Cycle

```
1. Feature Proposal → 2. Implementation Plan → 3. Development → 4. Retrospective
     ↑                                                               ↓
     └─────────────────── Continuous Improvement ←─────────────────┘
```

### Step-by-Step Process

#### 1. Start a New Feature

```bash
# Always create a feature branch
git checkout -b feature/your-feature-name

# Create and fill out a feature proposal
cp docs/feature-proposals/template-feature-proposal.md \
   docs/feature-proposals/XX-your-feature.md
```

#### 2. Plan Your Implementation

```bash
# Create an implementation plan
cp plan/template-implementation-plan.md \
   plan/your-feature-implementation.md

# Add tasks to track
python tools/progress-tracker.py add "Task 1" --priority high
python tools/progress-tracker.py add "Task 2" --priority medium
```

#### 3. Develop with Progress Tracking

```bash
# Mark task as in progress
python tools/progress-tracker.py update <task-id> in_progress

# After completing
python tools/progress-tracker.py update <task-id> completed

# Save context before switching tasks
python tools/context-manager.py handoff \
  --completed "Implemented login endpoint" \
  --current "Working on session management" \
  --next "Add password reset" "Write tests"
```

#### 4. Validate Your Work

```bash
# Run the validation pipeline
python tools/validate-pipeline.py

# Run specific checks
python tools/validate-pipeline.py --checks branch proposal tests

# Export results for CI
python tools/validate-pipeline.py --export json --output validation.json
```

#### 5. Complete with Retrospective

```bash
# After feature completion
cp retrospectives/template-retrospective.md \
   retrospectives/your-feature-retrospective.md
```

---

## Prompting Claude for AI-First SDLC

### Initial Setup Prompt
When starting a new project, use this prompt:

```
Set up a new [technology] project for [purpose] using the AI-First SDLC framework from https://github.com/SteveGJones/ai-first-sdlc-practices.

Download and run: python setup-smart.py "[project purpose]"

Then read CLAUDE.md and run the repository health check to verify main branch protection is enabled.
```

### Development Session Prompt  
For ongoing development work:

```
Please read and follow CLAUDE.md in the project root. 

CRITICAL FIRST STEPS:
1. Run the repository health check to verify main branch protection
2. Confirm you're not on the main branch
3. Review current feature proposals and retrospectives

If main branch protection is missing, run: python tools/setup-branch-protection-gh.py
```

### Quick Prompt (Experienced Users)
```
Follow CLAUDE.md. Run health check first. Never push to main.
```

---

## For AI Agents

### Understanding CLAUDE.md

The `CLAUDE.md` file is your primary instruction set. It contains:

1. **Project Context**: What you're building and why
2. **Critical Rules**: What you must NEVER do (e.g., push to main)
3. **Development Workflow**: Step-by-step processes to follow
4. **Command Mappings**: Preferred commands for common tasks

### AI Agent Workflow

#### Session Start
```bash
# CRITICAL: Run repository health check from CLAUDE.md
git branch --show-current  # Should NOT be "main"
gh api repos/:owner/:repo/branches/main/protection --jq '.required_status_checks.contexts' 2>/dev/null

# If protection missing, set it up:
# python tools/setup-branch-protection-gh.py

# Load previous context
python tools/context-manager.py load

# Check current progress
python tools/progress-tracker.py list --status in_progress

# Validate environment
python tools/validate-pipeline.py
```

#### During Development
```bash
# Before making changes
python tools/progress-tracker.py update <task-id> in_progress

# Track decisions
python tools/context-manager.py save work \
  --data '{"decision": "Use JWT for auth", "rationale": "Stateless and scalable"}'

# Create implementation snapshot
python tools/context-manager.py snapshot "authentication" "phase-1" \
  --files "src/auth.py" "tests/test_auth.py"
```

#### Session End
```bash
# Create handoff document
python tools/context-manager.py handoff \
  --completed "Login endpoint" "Session management" \
  --current "Working on password reset flow" \
  --next "Email integration" "Rate limiting" \
  --blocker "SMTP config missing:High:Need email server details" \
  --notes "Authentication flow 80% complete. See tests/test_auth.py for examples."
```

### Context Preservation Between Sessions

When resuming work:

```bash
# List available contexts
python tools/context-manager.py list

# Load specific session
python tools/context-manager.py load <session-id>

# Continue from handoff
cat HANDOFF_<session-id>.md
```

---

## For Human Developers

### Collaborating with AI Agents

#### Setting Expectations

1. **Create Clear Feature Proposals**: AI agents rely on well-defined proposals
2. **Maintain CLAUDE.md**: Keep AI instructions up-to-date
3. **Review Handoff Documents**: Understand what the AI was working on

#### Code Review Process

```bash
# Check AI agent's progress
python tools/progress-tracker.py report

# Review validation status
python tools/validate-pipeline.py --export markdown --output review.md

# Check commit compliance
git log --oneline -10
```

### Managing AI Development Sessions

#### Preparing for AI Work
```bash
# Set up clear task list
python tools/progress-tracker.py add "Implement user profile API" --priority high
python tools/progress-tracker.py add "Add profile picture upload" --priority medium

# Create feature proposal with specific requirements
vim docs/feature-proposals/user-profiles.md
```

#### After AI Session
```bash
# Review what was done
python tools/progress-tracker.py list --status completed

# Check for any blockers
python tools/progress-tracker.py list --status blocked

# Run validation
python tools/validate-pipeline.py
```

---

## Tool Usage Guide

### 1. Branch Protection Setup

```bash
# Auto-detect and configure
python tools/setup-branch-protection.py

# Specific platform
python tools/setup-branch-protection.py --platform github --repo owner/repo

# Dry run to see configuration
python tools/setup-branch-protection.py --dry-run
```

### 2. Progress Tracker

```bash
# Add tasks
python tools/progress-tracker.py add "Implement feature X" --priority high

# Update status
python tools/progress-tracker.py update abc123 in_progress
python tools/progress-tracker.py update abc123 completed

# List tasks
python tools/progress-tracker.py list
python tools/progress-tracker.py list --status pending --branch feature/auth

# Generate report
python tools/progress-tracker.py report --output status.md
```

### 3. Context Manager

```bash
# Save work context
python tools/context-manager.py save work --data '{"current_focus": "authentication"}'

# Create handoff
python tools/context-manager.py handoff \
  --completed "Task 1" "Task 2" \
  --current "Task 3" \
  --next "Task 4" "Task 5"

# Create snapshot
python tools/context-manager.py snapshot "feature-name" "phase-1" \
  --files "src/main.py" "tests/test_main.py"

# List contexts
python tools/context-manager.py list --type handoff --limit 5
```

### 4. Validation Pipeline

```bash
# Run all checks
python tools/validate-pipeline.py

# Specific checks
python tools/validate-pipeline.py --checks branch proposal tests

# CI mode (exits with error code)
python tools/validate-pipeline.py --ci

# Export results
python tools/validate-pipeline.py --export json --output results.json
```

### 5. Feature Proposal Checker

```bash
# Run manually
python tools/check-feature-proposal.py

# Automatically runs as pre-commit hook
git commit -m "feat: add user profiles"
```

---

## Common Scenarios

### Scenario 1: Starting a New Feature (Human)

```bash
# 1. Create feature branch
git checkout -b feature/payment-integration

# 2. Create proposal
cp docs/feature-proposals/template-feature-proposal.md \
   docs/feature-proposals/payment-integration.md
vim docs/feature-proposals/payment-integration.md

# 3. Set up tasks for AI
python tools/progress-tracker.py add "Research payment providers" --priority high
python tools/progress-tracker.py add "Design payment flow" --priority high
python tools/progress-tracker.py add "Implement Stripe integration" --priority medium

# 4. Commit proposal
git add docs/feature-proposals/payment-integration.md
git commit -m "feat: add payment integration proposal"
```

### Scenario 2: AI Agent Continuing Work

```bash
# 1. Load context
python tools/context-manager.py load

# 2. Check tasks
python tools/progress-tracker.py list --status pending

# 3. Start work
python tools/progress-tracker.py update abc123 in_progress

# 4. ... do implementation work ...

# 5. Complete task
python tools/progress-tracker.py update abc123 completed

# 6. Create handoff before ending session
python tools/context-manager.py handoff \
  --completed "Stripe integration" \
  --current "Testing payment flow" \
  --next "Add PayPal support"
```

### Scenario 3: Multi-Session Feature Development

```bash
# Session 1: Planning
git checkout -b feature/analytics
cp docs/feature-proposals/template-feature-proposal.md \
   docs/feature-proposals/analytics.md
# ... edit proposal ...
python tools/context-manager.py handoff \
  --completed "Created feature proposal" \
  --next "Design database schema" "Create API endpoints"

# Session 2: Backend
python tools/context-manager.py load <session-1-id>
python tools/progress-tracker.py update <task-id> in_progress
# ... implement backend ...
python tools/context-manager.py handoff \
  --completed "Database schema" "API endpoints" \
  --next "Frontend dashboard" "Add charts"

# Session 3: Frontend
python tools/context-manager.py load <session-2-id>
# ... implement frontend ...
```

### Scenario 4: Handling Blockers

```bash
# Mark task as blocked
python tools/progress-tracker.py update <task-id> blocked \
  --blocked-by "Waiting for API credentials"

# Document in handoff
python tools/context-manager.py handoff \
  --current "Payment integration" \
  --blocker "API credentials:High:Need production Stripe keys from DevOps" \
  --blocker "SSL cert:Medium:Payment page requires HTTPS"
```

---

## Troubleshooting

### Common Issues

#### "Direct commits to main branch are forbidden!"
```bash
# You're on main branch, create a feature branch
git checkout -b feature/your-feature
```

#### "No feature proposal found for branch"
```bash
# Create a proposal
cp docs/feature-proposals/template-feature-proposal.md \
   docs/feature-proposals/your-feature.md
# Edit it to include: Target Branch: `feature/your-feature`
```

#### "Context not found"
```bash
# List available contexts
python tools/context-manager.py list

# Check session history
ls -la .ai-context/history/
```

#### Pre-commit hooks failing
```bash
# Update hooks
pre-commit autoupdate

# Run manually to see specific errors
pre-commit run --all-files

# Skip hooks temporarily (NOT RECOMMENDED)
git commit --no-verify -m "emergency fix"
```

### Getting Help

1. **Check Validation**: `python tools/validate-pipeline.py`
2. **Review Templates**: Look at files in `templates/` directory
3. **Read AI Instructions**: Check your `CLAUDE.md` file
4. **View Examples**: See `examples/` directory

### Best Practices

1. **Always work in feature branches**
2. **Create proposals before implementation**
3. **Track progress continuously**
4. **Save context before switching tasks**
5. **Run validation before commits**
6. **Create handoffs at session end**
7. **Document blockers immediately**
8. **Review retrospectives regularly**

---

## Advanced Usage

### Custom Validation Checks

Add to `.ai-sdlc.json`:
```json
{
  "validation": {
    "custom_checks": [
      {
        "name": "security_scan",
        "command": "security-scanner --strict",
        "required": true
      }
    ]
  }
}
```

### Automated Context Switching

```bash
# Save current feature context
python tools/context-manager.py save work \
  --data '{"feature": "authentication", "branch": "feature/auth"}'

# Switch to hotfix
git checkout -b hotfix/security-patch

# ... fix issue ...

# Return to feature
git checkout feature/auth
python tools/context-manager.py load
```

### CI/CD Integration

```yaml
# .github/workflows/ai-sdlc.yml
name: AI-First SDLC Validation
on: [push, pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pre-commit install
      
      - name: Run validation
        run: python tools/validate-pipeline.py --ci
      
      - name: Check feature proposal
        run: python tools/check-feature-proposal.py
```

---

This HOWTO guide provides practical examples of using the AI-First SDLC Framework. For more details on specific tools, see their individual documentation in the `tools/` directory.