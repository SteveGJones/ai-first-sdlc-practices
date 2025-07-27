# CLAUDE-CORE.md

AI-First SDLC framework core instructions. Load context modules as needed.

## Framework Overview
Comprehensive methodology for AI agents as primary developers with quality enforcement.

## Zero Technical Debt (MANDATORY)

Before ANY code: `python tools/validation/validate-architecture.py --strict` (MUST PASS)

### Required Architecture Documents (ALL 6):
1. requirements-traceability-matrix.md
2. what-if-analysis.md
3. architecture-decision-record.md
4. system-invariants.md
5. integration-design.md
6. failure-mode-analysis.md

### FORBIDDEN:
- TODO, FIXME, HACK comments
- `any` type annotations
- Commented-out code
- Skipping error handling
- Ignoring warnings
- Temporary solutions

### After EVERY change:
```bash
python tools/validation/check-technical-debt.py --threshold 0
python tools/validation/validate-pipeline.py --checks type-safety
```

## Logging (MANDATORY)

### Required Logging Points:
1. Function entry/exit (with context)
2. Errors (with stack trace)
3. External calls (APIs/DB)
4. State changes & security events

### FORBIDDEN: Passwords, tokens, SSNs, credit cards in logs

Details: Load CLAUDE-CONTEXT-logging.md

## Branch Protection & Workflow

### NEVER:
- Commit directly to main
- Work without feature branch
- Create PR without retrospective

### ALWAYS:
1. Create feature branch: `git checkout -b feature/name`
2. Create proposal: `docs/feature-proposals/XX-name.md`
3. Create retrospective: `retrospectives/XX-name.md` (update incrementally)
4. Push to remote: `git push -u origin feature/name`
5. Create PR with complete retrospective

## Retrospectives (MANDATORY)

### Create immediately when starting work
### Update throughout implementation:
- After discovering issues
- When making major changes
- Upon finding bugs
- When completing todos

### PR REJECTED without retrospective containing:
- What went well
- What could improve
- Lessons learned

## Essential Commands

### Validation:
```bash
python tools/validation/validate-pipeline.py --ci
python tools/validation/validate-architecture.py --strict
python tools/validation/check-technical-debt.py
```

### Progress:
```bash
python tools/automation/progress-tracker.py add "task"
python tools/automation/progress-tracker.py list
python tools/automation/progress-tracker.py complete <id>
```

### Context:
```bash
python tools/automation/context-manager.py handoff --current "X" --next "Y"
```

## Project Structure
```
project/
├── docs/feature-proposals/    # Proposals
├── plan/                      # Implementation plans
├── retrospectives/            # Reviews
├── tools/                     # Framework tools
│   ├── automation/
│   └── validation/
└── CLAUDE.md                  # Full instructions
```

## Context Loading

Load additional instructions based on task:

| Task | Load File |
|------|-----------|
| Setup framework | CLAUDE-SETUP.md |
| Create architecture | CLAUDE-CONTEXT-architecture.md |
| Run validation | CLAUDE-CONTEXT-validation.md |
| Update framework | CLAUDE-CONTEXT-update.md |
| Language work | CLAUDE-CONTEXT-language-validators.md |
| Logging standards | CLAUDE-CONTEXT-logging.md |

## Framework Updates

Check version: `cat VERSION`
Check latest: `curl -s https://raw.githubusercontent.com/SteveGJones/ai-first-sdlc-practices/main/VERSION`
If update available: Load CLAUDE-CONTEXT-update.md

## Development Workflow

1. **Plan**: Create proposal & retrospective
2. **Architecture**: Create 6 documents, validate
3. **Implement**: Zero debt, continuous validation
4. **Review**: Update retrospective
5. **Submit**: PR with complete retrospective

## Critical Rules Summary

- **Architecture before code** (NO EXCEPTIONS)
- **Zero technical debt** (NO TODOS)
- **Branch protection** (NO direct commits)
- **Retrospectives required** (NO PR without)
- **Continuous validation** (EVERY change)

Total lines: 120