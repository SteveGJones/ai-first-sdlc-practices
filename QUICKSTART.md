# AI-First SDLC Quick Start

## The Pipeline

```
specify → architect → implement → review
```

1. **Specify**: Feature proposal with acceptance criteria (Given/When/Then)
2. **Architect**: Architecture documents before code
3. **Implement**: Zero technical debt, continuous validation
4. **Review**: Retrospective before PR

All rules: **CONSTITUTION.md** | Lite templates available for small projects.

---

## Setup (V3 Recommended)

### Option A: Zero-Dependency Agent Setup

Give Claude this prompt:
```
I want to set up AI-First SDLC v3 for my project. Please:
1. Download: curl -s https://raw.githubusercontent.com/SteveGJones/ai-first-sdlc-practices/main/agents/v3-setup-orchestrator.md > v3-setup-orchestrator.md
2. Install: mkdir -p .claude/agents && mv v3-setup-orchestrator.md .claude/agents/
3. Restart me, then say: "Use the v3-setup-orchestrator agent to set up AI-First SDLC for my project"
```

### Option B: Script Setup (Requires Python 3.8+)

```
Please set up the AI-First SDLC framework from https://github.com/SteveGJones/ai-first-sdlc-practices in this project.
```

Claude will download and run `setup-smart.py` with your project description.

---

## What You Get

After setup:
- **CLAUDE-CORE.md** — Core instructions for Claude
- **CONSTITUTION.md** — All rules (single source of truth)
- **tools/** — Validation and automation scripts
- **docs/feature-proposals/** — Proposal templates
- **retrospectives/** — Retrospective templates
- **CI/CD config** — Automated validation

## Progressive Levels

| Level | For | Key Difference |
|-------|-----|---------------|
| **Prototype** | MVPs, experiments | TODOs allowed, basic validation |
| **Production** | Real users | Zero technical debt, full architecture |
| **Enterprise** | Large teams | Compliance, audit trails, multi-reviewer |

Check your level: `python tools/automation/sdlc-level.py check`

## Essential Commands

```bash
# Validate after code changes
python tools/validation/local-validation.py --syntax

# Validate before commits
python tools/validation/local-validation.py --quick

# Validate before PR
python tools/validation/local-validation.py --pre-push
```

## First Feature Workflow

```bash
# 1. Create feature branch
git checkout -b feature/my-feature

# 2. Write proposal (use lite template for small features)
cp templates/feature-proposal-lite.md docs/feature-proposals/01-my-feature.md

# 3. Write code, validate
python tools/validation/local-validation.py --syntax

# 4. Write retrospective
cp templates/retrospective-lite.md retrospectives/01-my-feature.md

# 5. Push and create PR
git push -u origin feature/my-feature
```

---

**Full documentation**: https://github.com/SteveGJones/ai-first-sdlc-practices
