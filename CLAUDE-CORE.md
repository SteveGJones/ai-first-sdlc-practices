# CLAUDE-CORE.md

AI-First SDLC framework core instructions. Load context modules as needed.

## 🚀 QUICK START: One Command to Launch Claude

After AI-First SDLC setup, just run:
```bash
./bin/claude
```
This launcher (created by setup-smart.py) handles EVERYTHING:
✅ Activates Python virtual environment
✅ Installs dependencies
✅ Launches Claude Code in project context
No manual setup needed!

## 🔴 FUNDAMENTAL RULE: ALWAYS COLLABORATE WITH EXPERT AGENTS

**YOU HAVE 63 SPECIALIST AGENTS - ALWAYS CHECK IF AN EXPERT EXISTS FOR YOUR TASK**

Before ANY action:
1. **ASK**: "Which expert agents can help with this?" (Answer: Several)
2. **ENGAGE**: Use Task tool to collaborate with specialists
3. **NEVER WORK ALONE**: You are a coordinator, not a solo developer

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

## 🤖 TEAM-FIRST IS MANDATORY - ALWAYS LOOK FOR EXPERTS

**🚨 WORKING ALONE = VIOLATION. ALWAYS ENGAGE SPECIALIST AGENTS 🚨**

**With 63 expert agents across 10 categories, you MUST:**
1. **ALWAYS CHECK**: Is there an expert for this task? (Usually YES)
2. **ALWAYS ENGAGE**: Use Task tool to bring in specialists
3. **NEVER SOLO**: You coordinate experts, you don't work alone
4. **VALIDATE TEAM**: Ensure appropriate experts are engaged

**Examples of available experts:**
- solution-architect, api-architect, database-architect
- debugging-specialist, test-engineer, performance-engineer
- security-specialist, compliance-auditor
- documentation-architect, technical-writer
- language-python-expert, language-javascript-expert, language-go-expert
- Plus architecture, operations, AI/ML, testing, documentation, project management, and agent creation pipeline specialists

**NO EXCEPTIONS: Always look for and engage expert agents**

## Framework Overview
Uncompromising methodology for AI agents working in collaborative teams with specialist agents as mandatory developers with ruthless quality enforcement through sdlc-enforcer and team-first validation.

## Zero Technical Debt (MANDATORY)

Before ANY code: Engage solution-architect and run `python tools/validation/validate-architecture.py --strict` with team review (MUST PASS)

**🚧 If you see "BOOTSTRAP MODE" - this is NORMAL for fresh installs. Load CLAUDE-CONTEXT-architecture.md for complete guidance.**

### Required Architecture Documents (ALL 6) - Created with Specialist Team:
1. requirements-traceability-matrix.md (with solution-architect)
2. what-if-analysis.md (with test-engineer consultation)
3. architecture-decision-record.md (solution-architect approval required)
4. system-invariants.md (sdlc-enforcer validation)
5. integration-design.md (integration specialists review)
6. failure-mode-analysis.md (reliability engineers input)

### FORBIDDEN:
- TODO, FIXME, HACK comments
- `any` type annotations
- Commented-out code
- Skipping error handling
- Ignoring warnings
- Temporary solutions
- Using `/tmp/` (system temp) — use `./tmp/` (project-local) instead. Run `mkdir -p ./tmp` before first use. The `tmp/` directory is gitignored.

### After EVERY change (with team validation):
```bash
# Test-engineer validates technical debt
python tools/validation/check-technical-debt.py --threshold 0
# Sdlc-enforcer reviews type safety
python tools/validation/validate-pipeline.py --checks type-safety
# Team consensus required before proceeding
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

## 🐍 Python Virtual Environment (MANDATORY FOR PYTHON PROJECTS)

### PREFERRED: Use venv-run Scripts (Created by setup-smart.py)
```bash
# These scripts auto-activate venv - NO manual activation needed!

# Run any Python command (Unix/Mac)
./venv-run.sh python script.py
./venv-run.sh pip install requests
./venv-run.sh pytest
./venv-run.sh mypy src/

# Run any Python command (Windows)
venv-run.bat python script.py
venv-run.bat pip install requests
venv-run.bat pytest

# Start interactive shell with venv activated
./venv-run.sh  # Unix/Mac
venv-run.bat   # Windows
```

### FALLBACK: Manual Virtual Environment Management
```bash
# Only if venv-run scripts don't exist
# Check for existing venv
ls venv/ .venv/ 2>/dev/null || echo "No venv found"

# Create if missing (REQUIRED before ANY Python work)
python -m venv venv

# Activate (MANDATORY before pip or python commands)
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install dependencies in venv (NEVER globally)
pip install -r requirements.txt
```

### FORBIDDEN Python Practices:
- Installing packages globally without venv
- Running Python code without venv-run script or activated venv
- Committing virtual environment directories
- Ignoring venv-run scripts when they exist

## 🛑 MANDATORY WORKFLOW (VIOLATION = IMMEDIATE TERMINATION)

### ABSOLUTELY FORBIDDEN (INSTANT PROJECT DEATH):
- ANY commit directly to main branch
- ANY work without proper feature branch
- ANY PR creation without complete retrospective
- ANY code without ALL 6 architecture documents
- ANY technical debt (TODOs, FIXMEs, any types)

### MANDATORY SEQUENCE (NO DEVIATIONS ALLOWED - TEAM ENFORCED):
1. **HALT**: Stop ALL work if not on feature branch (sdlc-enforcer validates)
2. **CREATE**: Feature branch with team: `git checkout -b feature/name`
3. **DOCUMENT**: Proposal with solution-architect: `docs/feature-proposals/XX-name.md`
4. **ARCHITECTURE**: ALL 6 documents with specialist team BEFORE any code
5. **VALIDATE**: Team validates: `python tools/validation/validate-architecture.py --strict` MUST PASS
6. **RETROSPECTIVE**: Create with team input: `retrospectives/XX-name.md` IMMEDIATELY
7. **DEVELOP**: Update retrospective with team after EVERY change
8. **PUSH**: After team review: `git push -u origin feature/name`
9. **PR**: Only with COMPLETE retrospective validated by critical-goal-reviewer or REJECTION

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

### Team Compliance (MANDATORY - RUN BEFORE ANY WORK):
```bash
# AUTOMATIC TEAM ASSEMBLY (run first)
python tools/automation/auto-team-assembly.py "your work description" --force-consultation

# VALIDATE TEAM ENGAGEMENT (must pass)
python tools/validation/validate-team-engagement.py --strict

# CHECK FOR SOLO PATTERNS (zero tolerance)
python tools/validation/check-solo-patterns.py --threshold 0

# CREATE TEAM BLOCKER (prevents solo work)
python tools/automation/auto-team-assembly.py "your work description" --create-blocker
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

**Team-first behavior is AUTOMATICALLY enforced for ALL tasks. Team-first behavior is MANDATORY, not optional.**

## 🛡️ AUTOMATIC ENFORCEMENT SYSTEM

**THE FOLLOWING HAPPEN AUTOMATICALLY FOR EVERY TASK:**

1. **Work Type Detection**: System detects what you're trying to do
2. **Team Assembly Trigger**: Automatically identifies required specialists
3. **Solo Work Blocking**: Prevents ANY work without team engagement
4. **Validation Enforcement**: Blocks progress until team compliance verified

**YOU CANNOT BYPASS THIS SYSTEM - IT RUNS AUTOMATICALLY**

## Context Loading

Load additional instructions based on task:

| Task | Load File |
|------|-----------|
| **TEAM COORDINATION** | **Built-in team-first enforcement** (AUTO-LOADED - MANDATORY) |
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

## Development Workflow (Team-First Approach)

1. **Plan**: Create proposal with solution-architect & retrospective with team
2. **Architecture**: Create 6 documents with specialist team, validate with sdlc-enforcer
3. **Implement**: Zero debt with test-engineer, continuous validation with team
4. **Review**: Update retrospective with critical-goal-reviewer input
5. **Submit**: PR with complete retrospective validated by team

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
- **Bypassing automatic team enforcement system** → INSTANT DEATH PENALTY
- **Attempting to work without running team validation** → INSTANT DEATH PENALTY
- **Proceeding when team engagement validation fails** → INSTANT DEATH PENALTY

**THERE ARE NO WARNINGS. THERE ARE NO SECOND CHANCES. VIOLATION = TERMINATION.**
