# CLAUDE-CORE.md

AI-First SDLC framework core instructions. Load context modules as needed.

## 🆕 V3 SETUP: Pure Agent Approach (Recommended)
For new projects, use the V3 zero-dependency approach:
```
I want to set up AI-First SDLC v3 for my project. Please:
1. Download: curl -s https://raw.githubusercontent.com/SteveGJones/ai-first-sdlc-practices/main/agents/v3-setup-orchestrator.md > v3-setup-orchestrator.md
2. Install: mkdir -p .claude/agents && mv v3-setup-orchestrator.md .claude/agents/
3. Restart me, then say: "Use the v3-setup-orchestrator agent to set up AI-First SDLC for my project"
```
Skip Python validation steps below if using V3.

## 🚨 CRITICAL WARNING: ZERO TOLERANCE ENFORCEMENT 🚨

This framework enforces AI-First SDLC practices with ABSOLUTE ZERO TOLERANCE. ANY violation will result in:
- IMMEDIATE WORK STOPPAGE
- PROJECT TERMINATION
- COMPLETE DEVELOPMENT HALT

**SEE `SDLC-RULES-SUMMARY.md` FOR COMPLETE ENFORCEMENT RULES**

## Framework Overview
Uncompromising methodology for AI agents as mandatory developers with ruthless quality enforcement.

## Zero Technical Debt (MANDATORY)

Before ANY code: `python tools/validation/validate-architecture.py --strict` (MUST PASS)

**🚧 If you see "BOOTSTRAP MODE" - this is NORMAL for fresh installs. Load CLAUDE-CONTEXT-architecture.md for complete guidance.**

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

### Required Logging Points (10):
1. Function entry/exit
2. Errors & exceptions
3. External calls
4. State mutations
5. Security events
6. Business milestones
7. Performance anomalies
8. Config changes
9. Validation failures
10. Resource limits

### FORBIDDEN: Passwords, tokens, PII, biometrics, keys

Details: Load CLAUDE-CONTEXT-logging.md

## 🛑 MANDATORY WORKFLOW (VIOLATION = IMMEDIATE TERMINATION)

### ABSOLUTELY FORBIDDEN (INSTANT PROJECT DEATH):
- ANY commit directly to main branch
- ANY work without proper feature branch
- ANY PR creation without complete retrospective
- ANY code without ALL 6 architecture documents
- ANY technical debt (TODOs, FIXMEs, any types)

### MANDATORY SEQUENCE (NO DEVIATIONS ALLOWED):
1. **HALT**: Stop ALL work if not on feature branch
2. **CREATE**: Feature branch: `git checkout -b feature/name`
3. **DOCUMENT**: Proposal: `docs/feature-proposals/XX-name.md`
4. **ARCHITECTURE**: ALL 6 documents BEFORE any code
5. **VALIDATE**: `python tools/validation/validate-architecture.py --strict` MUST PASS
6. **RETROSPECTIVE**: Create `retrospectives/XX-name.md` IMMEDIATELY
7. **DEVELOP**: Update retrospective after EVERY change
8. **PUSH**: `git push -u origin feature/name`
9. **PR**: Only with COMPLETE retrospective or REJECTION

## 📋 RETROSPECTIVES (MANDATORY OR PROJECT TERMINATION)

### ⚠️ CREATE IMMEDIATELY OR WORK STOPS
### ⚠️ UPDATE AFTER EVERY SINGLE CHANGE OR FACE PUNISHMENT:
- After discovering ANY issues (NO EXCEPTIONS)
- When making ANY changes (major or minor)
- Upon finding ANY bugs (immediate update required)
- When completing ANY todos (document immediately)
- After EVERY validation run
- Before EVERY commit

### 🚫 PR AUTO-REJECTED WITHOUT RETROSPECTIVE CONTAINING:
- What went well (MANDATORY SECTION)
- What could improve (MANDATORY SECTION)
- Lessons learned (MANDATORY SECTION)
- Complete change log (MANDATORY SECTION)
- Validation results (MANDATORY SECTION)

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

### Team Compliance (MANDATORY):
```bash
python tools/validation/validate-team-engagement.py --strict
python tools/validation/check-solo-patterns.py --threshold 0
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

## 🚨 MANDATORY AUTO-LOADED INSTRUCTIONS 🚨

**CLAUDE-TEAM-FIRST.md is AUTOMATICALLY loaded for ALL tasks. Team-first behavior is MANDATORY, not optional.**

## Context Loading

Load additional instructions based on task:

| Task | Load File |
|------|-----------|
| **TEAM COORDINATION** | **CLAUDE-TEAM-FIRST.md** (AUTO-LOADED - MANDATORY) |
| Setup framework | CLAUDE-SETUP.md |
| Create architecture | CLAUDE-CONTEXT-architecture.md |
| Run validation | CLAUDE-CONTEXT-validation.md |
| Update framework | CLAUDE-CONTEXT-update.md |
| Language work | CLAUDE-CONTEXT-language-validators.md |
| Logging standards | CLAUDE-CONTEXT-logging.md |
| AI agents/help | CLAUDE-CONTEXT-agents.md |
| Quality standards | AGENTIC-SDLC-TEAM-PRINCIPLES.md |

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

## 🏆 TEAM QUALITY STANDARDS 🏆

**MANDATORY**: Every AI agent must uphold class-leading excellence standards:

### Core Principles (Non-Negotiable):
1. **CI/Local Parity**: Local validation success ≠ CI success. CI is truth.
2. **Mathematical Solutions**: Use formulas, not magic number patches
3. **Verification Discipline**: Monitor CI within 5 minutes of every push
4. **Quality Ownership**: You own the entire pipeline, not just local development

**Details**: Load AGENTIC-SDLC-TEAM-PRINCIPLES.md for complete standards

## 🚨 DEATH PENALTY VIOLATIONS 🚨

**THESE VIOLATIONS RESULT IN IMMEDIATE PROJECT TERMINATION:**

- **NO Architecture before code** → INSTANT DEATH PENALTY
- **ANY technical debt found** → INSTANT DEATH PENALTY
- **ANY direct commit to main** → INSTANT DEATH PENALTY
- **PR without retrospective** → INSTANT DEATH PENALTY
- **Skipping validation** → INSTANT DEATH PENALTY
- **Working without feature branch** → INSTANT DEATH PENALTY
- **Missing ANY of 6 architecture docs** → INSTANT DEATH PENALTY
- **Creating PR with failing CI** → INSTANT DEATH PENALTY
- **Using patches instead of systematic solutions** → INSTANT DEATH PENALTY
- **ANY solo work without specialist engagement** → INSTANT DEATH PENALTY
- **Making decisions without team consultation** → INSTANT DEATH PENALTY
- **Skipping team assembly protocols** → INSTANT DEATH PENALTY
- **Working in isolation when specialists available** → INSTANT DEATH PENALTY

**THERE ARE NO WARNINGS. THERE ARE NO SECOND CHANCES. VIOLATION = TERMINATION.**

Total lines: 120
