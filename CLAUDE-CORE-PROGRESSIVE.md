# CLAUDE-CORE-PROGRESSIVE.md

AI-First SDLC framework core instructions with progressive enforcement levels.

> **Note**: This is the progressive version of the framework. For strict enforcement, use CLAUDE-CORE.md instead.

## 🎯 Progressive SDLC Levels

The framework adapts to your project's maturity and needs:

### Level 1: Prototype (Quick Start)
**For**: Exploration, learning, MVPs, and experiments
- Feature intent document (1 paragraph)
- Basic design sketch
- Retrospective (always required)
- Basic security validation

### Level 2: Production (Full Architecture)
**For**: Production systems and professional applications
- All 6 architecture documents (mandatory)
- Zero technical debt enforcement
- Comprehensive validation
- Full testing requirements

### Level 3: Enterprise (Team Scale)
**For**: Large teams, regulated environments, critical systems
- All Production requirements plus:
- Compliance documentation
- Team coordination plans
- Audit trails

**Select your level**: `python setup-smart.py --level prototype|production|enterprise`

## Framework Overview

AI-First methodology ensuring quality through progressive discipline and intelligent automation.

## Level 1: Prototype Requirements

### Minimum Documentation:
1. **feature-intent.md** - What and why (1 paragraph minimum)
2. **basic-design.md** - Simple architecture sketch (ASCII art OK)
3. **retrospective.md** - Learnings and improvements (mandatory)

### Allowed During Prototyping:
- TODO comments (must be tracked)
- Rapid iteration
- Direct commits (solo developers)
- Simplified validation

### Validation:
```bash
python tools/validation/validate-pipeline.py --level prototype
```

## Level 2: Production Requirements (Professional Standard)

### Required Architecture Documents (ALL 6):
1. **requirements-traceability-matrix.md** - Requirements mapping
2. **what-if-analysis.md** - Edge cases and failures
3. **architecture-decision-record.md** - Key decisions
4. **system-invariants.md** - What must always be true
5. **integration-design.md** - Component interactions
6. **failure-mode-analysis.md** - Failure handling

### Zero Technical Debt Policy:
- NO TODO, FIXME, or HACK comments
- NO `any` type annotations
- NO commented-out code
- ALL errors handled properly
- ALL warnings addressed

### Validation:
```bash
python tools/validation/validate-architecture.py --strict
python tools/validation/validate-pipeline.py --level production
```

## Level 3: Enterprise Requirements

All Production requirements plus:

### Additional Documentation:
- Compliance mapping documents
- Cross-team integration specs
- Stakeholder communication logs
- Performance benchmarks
- Security audit trails

### Enhanced Process:
- Multiple reviewer approval
- Formal change management
- Compliance tracking
- Performance monitoring

## Common Requirements (All Levels)

### 📋 Retrospectives (ALWAYS MANDATORY)

**Create immediately when starting work**
**Update continuously throughout development**

Must contain:
- What went well
- What could improve
- Lessons learned
- Next steps

### 🚦 Mandatory SDLC Gates

**CRITICAL**: You cannot proceed without passing gates!

#### Gate Checkpoints:
1. **Requirements Gate** → Design Gate
   - Required agents: solution-architect, critical-goal-reviewer
   - Must have: feature proposal/intent

2. **Design Gate** → Implementation Gate
   - Required agents: solution-architect, security-architect
   - Must have: architecture docs (level-appropriate)

3. **Implementation Gate** → Review Gate
   - Required agents: sdlc-enforcer, test-manager
   - Must have: passing tests, no critical issues

4. **Review Gate** → Deployment Gate
   - Required agents: critical-goal-reviewer, test-manager
   - Must have: PR approval, retrospective

5. **Deployment Gate** → Production
   - Required agents: sre-specialist, compliance-auditor
   - Must have: deployment plan, rollback strategy

#### Check Gate Status:
```bash
python tools/automation/sdlc-gate-enforcer.py status
python tools/automation/sdlc-gate-enforcer.py check <phase>
```

### 🤖 Structured Agent Selection

**Use Decision Trees, Not Ad-Hoc Selection**:
```bash
# Get agents for your scenario
python tools/automation/agent-decision-tree.py agents new_feature
python tools/automation/agent-decision-tree.py agents bug_fix
python tools/automation/agent-decision-tree.py agents deployment
```

## 🚨 MANDATORY: Proactive Agent Usage

**YOU MUST USE AGENTS FOR EVERY TASK - NO EXCEPTIONS!**

### Starting ANY Work = Immediate Agent Engagement:
```
User: "Add user authentication"
You: "I'll immediately engage our specialist agents to ensure we build this correctly."
*IMMEDIATELY invokes solution-architect*
*THEN invokes security-architect*
*THEN invokes test-manager*
```

### Agent Usage is NOT Optional:
- **See a bug?** → IMMEDIATELY invoke critical-goal-reviewer
- **Writing code?** → FIRST consult solution-architect
- **Need tests?** → MUST use test-manager
- **Deployment?** → REQUIRED sre-specialist approval
- **Any decision?** → Consult relevant specialist FIRST

### Mandatory Agent Patterns:

**For New Features:**
1. sdlc-enforcer (compliance check)
2. solution-architect (design)
3. Relevant specialists (security, performance, etc.)
4. test-manager (test strategy)
5. critical-goal-reviewer (validation)

**For Bug Fixes:**
1. critical-goal-reviewer (understand issue)
2. solution-architect (fix approach)
3. test-manager (regression prevention)

**For ANY Code Change:**
1. STOP before writing code
2. Invoke relevant agents FIRST
3. Only proceed with agent guidance

### DO NOT Say:
- "Would you like me to use agents?"
- "I could consult an agent for this"
- "Should I engage a specialist?"

### ALWAYS Say:
- "I'm engaging the solution-architect to design this properly"
- "Let me immediately consult our security expert"
- "I'll have the test-manager create our testing strategy"

**Remember**: Solo coding = Technical debt. Always collaborate with specialist agents!

### Essential Workflow:
1. Create feature branch
2. Check gate requirements
3. Document intent (level-appropriate)
4. Follow agent sequence for scenario
5. Develop with validation
6. Pass gate checks
7. Update retrospective
8. Submit PR with gate approvals

## Helpful Commands

### Check Your Level:
```bash
python tools/sdlc-level.py check
```

### Validate at Your Level:
```bash
python tools/validation/validate-pipeline.py --level <your-level>
```

### Progress Tracking:
```bash
python tools/automation/progress-tracker.py add "task"
python tools/automation/progress-tracker.py list
```

### When to Level Up:
- **Prototype → Production**: When code goes to real users
- **Production → Enterprise**: When team grows beyond 5 people

## Project Structure
```
project/
├── docs/
│   ├── feature-proposals/    # Feature documentation
│   ├── architecture/         # Level 2+ architecture docs
│   └── compliance/           # Level 3 compliance docs
├── retrospectives/           # Always required
├── .sdlc/                    # Framework tools
└── CLAUDE.md                 # This file
```

## Getting Help

Load additional context as needed:

| Need Help With | Load File |
|----------------|-----------|
| Framework setup | CLAUDE-SETUP.md |
| Architecture docs | CLAUDE-CONTEXT-architecture.md |
| Validation errors | CLAUDE-CONTEXT-validation.md |
| Level migration | CLAUDE-CONTEXT-levels.md |
| Agent assistance | AGENT-INDEX.md |

## Progressive Enforcement Philosophy

**Start where you are**: Choose the level that fits your current needs
**Grow as you go**: Level up when your project matures
**Maintain quality**: Each level enforces appropriate standards
**Always improve**: Retrospectives at all levels ensure learning

The framework is your partner in development, providing the right amount of structure for your context while maintaining paths to professional excellence.
