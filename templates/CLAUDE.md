# CLAUDE.md - AI Development Instructions

This file provides guidance to AI agents working on this codebase. These instructions override default AI behavior.

## Project Overview

**Project**: [Your Project Name]
**Purpose**: [Brief description]

## Rules

All AI-First SDLC rules are in **CONSTITUTION.md**. Key rules:

1. **No direct commits to main** — use feature branches and PRs
2. **Feature proposals before implementation** — `docs/feature-proposals/XX-name.md`
3. **Retrospectives before PR** — `retrospectives/XX-name.md`
4. **Zero technical debt** — no TODOs, no `any` types, no commented-out code
5. **Architecture before code** — all 6 architecture documents required (Production+)
6. **Continuous validation** — run checks after every change

## Development Workflow

```
specify → architect → implement → review
```

1. **Specify**: Create feature proposal with Given/When/Then acceptance criteria
2. **Architect**: Create architecture documents, validate with `python tools/validation/validate-architecture.py --strict`
3. **Implement**: Write code with zero technical debt, validate continuously
4. **Review**: Update retrospective, create PR

### Branch Naming
```
feature/[name]    fix/[name]    docs/[name]    refactor/[name]
```

### Commit Messages
```
feat: add new feature    fix: resolve bug    docs: update docs
refactor: restructure    test: add tests    chore: maintenance
```

## Validation Commands

```bash
# After writing code
python tools/validation/local-validation.py --syntax

# Before commits
python tools/validation/local-validation.py --quick

# Before PR
python tools/validation/local-validation.py --pre-push

# Architecture & technical debt
python tools/validation/validate-architecture.py --strict
python tools/validation/check-technical-debt.py --threshold 0
```

## Code Style

[CUSTOMIZE: Add your project's conventions]

### File Organization
```
src/
├── api/        # API endpoints
├── services/   # Business logic
├── models/     # Data models
├── utils/      # Utility functions
└── tests/      # Test files
```

### Quality Standards
- Type hints required for function parameters
- All functions must have docstrings
- Test coverage must remain above 80%
- No suppressed errors or bare excepts

## Build and Test

[CUSTOMIZE: Add your project's commands]

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
pytest

# Run all checks before committing
make lint test
```

## Security

### Never Do
- Store secrets in code
- Log sensitive information
- Trust user input without validation

### Always Do
- Use environment variables for configuration
- Validate and sanitize all inputs
- Use parameterized queries

## Architecture Documents (Production+)

Before writing code, create all 6 in `docs/architecture/`:
1. requirements-traceability-matrix.md
2. what-if-analysis.md
3. architecture-decision-record.md
4. system-invariants.md
5. integration-design.md
6. failure-mode-analysis.md

## Self-Review Process

Review all artifacts against requirements before presenting. Users see only the final version.

## Project Structure

```
project/
├── docs/feature-proposals/    # Feature proposals
├── docs/architecture/         # Architecture documents
├── plan/                      # Implementation plans
├── retrospectives/            # Post-implementation reviews
├── tools/validation/          # Validation scripts
├── CONSTITUTION.md            # All rules
└── CLAUDE.md                  # This file
```

## File Locations
- Feature Proposals: `docs/feature-proposals/`
- Implementation Plans: `plan/`
- Retrospectives: `retrospectives/`
- Architecture Docs: `docs/architecture/`
