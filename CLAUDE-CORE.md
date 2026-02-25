# CLAUDE-CORE.md

AI-First SDLC framework core instructions. All rules are in **CONSTITUTION.md**. Load context modules as needed.

## Quick Start

After AI-First SDLC setup, just run:
```bash
./bin/claude
```
This launcher (created by setup-smart.py) activates venv, installs dependencies, and launches Claude Code.

## V3 Setup (Recommended for New Projects)

Zero-dependency agent approach:
```
1. Download: curl -s https://raw.githubusercontent.com/SteveGJones/ai-first-sdlc-practices/main/agents/v3-setup-orchestrator.md > v3-setup-orchestrator.md
2. Install: mkdir -p .claude/agents && mv v3-setup-orchestrator.md .claude/agents/
3. Restart, then: "Use the v3-setup-orchestrator agent to set up AI-First SDLC for my project"
```

## Framework Overview

Methodology for AI agents working in collaborative teams with specialist agents. Quality enforced through validation scripts and CI. See CONSTITUTION.md for all rules with progressive levels (Prototype/Production/Enterprise).

## Agent Collaboration

You have 63+ specialist agents. Check for relevant experts before significant work and use the Task tool to engage them. You are a coordinator, not a solo developer. See CONSTITUTION.md Article 6.

Available specialists include: solution-architect, api-architect, database-architect, debugging-specialist, test-engineer, performance-engineer, security-specialist, documentation-architect, language-python-expert, language-javascript-expert, language-go-expert, and many more. See AGENT-INDEX.md for the full catalog.

## Development Workflow

```
specify → architect → implement → review
```

1. **Specify**: Feature proposal (`docs/feature-proposals/XX-name.md`) + retrospective (`retrospectives/XX-name.md`)
2. **Architect**: 6 architecture documents, validate with `python tools/validation/validate-architecture.py --strict`
3. **Implement**: Zero technical debt, continuous validation, update retrospective after changes
4. **Review**: PR with complete retrospective

Bootstrap exception: Fresh installs may run in BOOTSTRAP MODE — see CLAUDE-CONTEXT-architecture.md.

All workflow rules: CONSTITUTION.md Articles 1-3.

## Code Quality

No TODOs, no `any` types, no commented-out code, no deferred fixes. Use `./tmp/` (project-local, gitignored) not `/tmp/`. Full rules: CONSTITUTION.md Article 4.

## Validation

```bash
# After writing code
python tools/validation/local-validation.py --syntax

# Before commits
python tools/validation/local-validation.py --quick

# Before PR
python tools/validation/local-validation.py --pre-push

# Architecture & debt
python tools/validation/validate-architecture.py --strict
python tools/validation/check-technical-debt.py --threshold 0
```

CI is the source of truth — local success does not guarantee CI success. Full rules: CONSTITUTION.md Article 5.

## Logging

10 required logging points: function entry/exit, errors, external calls, state mutations, security events, business milestones, performance anomalies, config changes, validation failures, resource limits. Never log passwords, tokens, PII, biometrics, or keys. Details: CLAUDE-CONTEXT-logging.md.

## Python Virtual Environment

### Preferred: venv-run Scripts
```bash
./venv-run.sh python script.py    # Unix/Mac
./venv-run.sh pip install requests
./venv-run.sh pytest
venv-run.bat python script.py     # Windows
```

### Fallback: Manual
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

Never install packages globally. Never commit venv directories.

## Essential Commands

```bash
# Validation
python tools/validation/validate-pipeline.py --ci
python tools/validation/validate-architecture.py --strict
python tools/validation/check-technical-debt.py

# Progress tracking
python tools/automation/progress-tracker.py add "task"
python tools/automation/progress-tracker.py list
python tools/automation/progress-tracker.py complete <id>

# Context handoff
python tools/automation/context-manager.py handoff --current "X" --next "Y"
```

## Project Structure

```
project/
├── docs/feature-proposals/    # Proposals
├── plan/                      # Implementation plans
├── retrospectives/            # Reviews
├── tools/
│   ├── automation/            # Workflow scripts
│   └── validation/            # Compliance checks
├── CONSTITUTION.md            # All rules (single source of truth)
└── CLAUDE-CORE.md             # This file (core instructions)
```

## Context Loading

Load additional context based on task:

| Task | Load File |
|------|-----------|
| All rules | CONSTITUTION.md |
| Setup framework | CLAUDE-SETUP.md |
| Architecture | CLAUDE-CONTEXT-architecture.md |
| Validation | CLAUDE-CONTEXT-validation.md |
| Framework updates | CLAUDE-CONTEXT-update.md |
| Language validators | LANGUAGE-SPECIFIC-VALIDATORS.md |
| Logging standards | CLAUDE-CONTEXT-logging.md |
| Agent catalog | AGENT-INDEX.md |
| Quality standards | AGENTIC-TEAM-STANDARDS.md |
| Progressive levels | CLAUDE-CONTEXT-levels.md |

## Quality Standards

1. **CI/Local Parity**: CI is truth, not your local environment.
2. **Systematic Solutions**: Use formulas and proper algorithms, not magic number patches.
3. **Self-Review**: Review all artifacts against requirements before presenting.
4. **Verification Discipline**: Check CI results after every push.

Details: AGENTIC-TEAM-STANDARDS.md.

## Framework Updates

```bash
cat VERSION                    # Current version
curl -s https://raw.githubusercontent.com/SteveGJones/ai-first-sdlc-practices/main/VERSION  # Latest
```

If update available: Load CLAUDE-CONTEXT-update.md.
