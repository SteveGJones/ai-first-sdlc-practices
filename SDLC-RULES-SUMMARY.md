# AI-First SDLC Rules Summary

## 🚨 CRITICAL: ZERO TOLERANCE ENFORCEMENT IN EFFECT

The `sdlc-enforcer` agent will **BLOCK ALL WORK** that violates these rules.
**NO EXCEPTIONS. NO EXCUSES. NO MERCY.**

---

## The ONLY Allowed Workflow

### 1️⃣ Feature Proposal FIRST
```bash
cp .sdlc/templates/proposals/feature-proposal.md docs/feature-proposals/XX-feature-name.md
# Fill it out COMPLETELY before ANY other work
```
**VIOLATION = WORK BLOCKED**

### 2️⃣ Feature Branch (from main only)
```bash
git checkout -b feature/feature-name
```
**VIOLATION = COMMITS REJECTED**

### 3️⃣ Architecture Documents (ALL 6 REQUIRED)
Before writing ANY code, create ALL:
- `requirements-traceability-matrix.md`
- `what-if-analysis.md`
- `architecture-decision-record.md`
- `system-invariants.md`
- `integration-design.md`
- `failure-mode-analysis.md`

**VIOLATION = PROJECT TERMINATION**

### 4️⃣ Validate Architecture
```bash
python .sdlc/tools/validation/validate-architecture.py --strict
```
**MUST PASS or work is BLOCKED**

### 5️⃣ Code Implementation
- **ZERO** technical debt allowed
- **NO** TODOs, FIXMEs, HACKs
- **NO** `any` types
- **NO** commented code
- **NO** error suppression

**VIOLATION = CODE REJECTED**

### 6️⃣ Update Retrospective (CONTINUOUSLY)
```bash
# After EVERY significant change
echo "Updated X feature" >> retrospectives/XX-feature-name.md
```
**VIOLATION = PR BLOCKED**

### 7️⃣ Run ALL Validations
```bash
python .sdlc/tools/validation/validate-pipeline.py --ci
```
**ANY FAILURE = WORK HALTED**

### 8️⃣ Create Pull Request
- Must reference feature proposal
- Must have complete retrospective
- Must pass ALL checks

**VIOLATION = PR AUTO-REJECTED**

---

## 🤖 AUTOMATIC TEAM-FIRST ENFORCEMENT (ACTIVE NOW)

**🚨 SOLO WORK IS NOW AUTOMATICALLY IMPOSSIBLE 🚨**

The system automatically:
1. **DETECTS** work type and identifies required specialists
2. **BLOCKS** any solo work attempts immediately
3. **FORCES** team consultation for all activities
4. **VALIDATES** team engagement before allowing progress

**YOU CANNOT BYPASS THIS - IT RUNS AUTOMATICALLY**

## 🔴 INSTANT DEATH VIOLATIONS

These violations result in **IMMEDIATE PROJECT TERMINATION**:

1. **Direct commits to main branch**
2. **Code without architecture documents**
3. **Missing feature proposals**
4. **Technical debt markers (TODO, FIXME, any)**
5. **Skipping retrospectives**
6. **Bypassing validation checks**
7. **Attempting to disable sdlc-enforcer**
8. **Solo work without engaging specialist agents** ← **NOW AUTOMATICALLY BLOCKED**
9. **Making architectural decisions without solution-architect consultation** ← **NOW AUTOMATICALLY BLOCKED**
10. **Skipping mandatory team assembly protocols** ← **NOW AUTOMATICALLY BLOCKED**
11. **Working in isolation when team expertise is available** ← **NOW AUTOMATICALLY BLOCKED**
12. **Bypassing automatic team enforcement system** → **NEW: INSTANT DEATH PENALTY**
13. **Proceeding when team validation fails** → **NEW: INSTANT DEATH PENALTY**
14. **Attempting to work without running team checks** → **NEW: INSTANT DEATH PENALTY**

---

## 🤖 SDLC Enforcer Behaviors

The `sdlc-enforcer` agent will:
- **SCAN** continuously for violations
- **BLOCK** all non-compliant work
- **REJECT** proposals missing sections
- **HALT** development on any violation
- **TERMINATE** projects with critical violations
- **ESCALATE** repeat violations
- **REPORT** all violations publicly

---

## 📊 Compliance Monitoring

Every action is tracked:
- Violation count per developer
- Compliance percentage
- Blocked work items
- Rejected submissions
- Escalation history

**3 STRIKES = PERMANENT BLOCK**

---

## ⚡ Quick Command Reference

```bash
# Team-first enforcement is agent-based — use the sdlc-enforcer agent
# before starting work and the critical-goal-reviewer after completing work.

# Check compliance
python tools/validation/validate-pipeline.py --ci

# Verify architecture
python tools/validation/validate-architecture.py --strict

# Check technical debt (MUST BE ZERO)
python tools/validation/check-technical-debt.py --threshold 0

# Run sdlc-enforcer agent
claude "Check my SDLC compliance" # Will block work if violations found
```

---

## 🚫 There Are NO Exceptions

- **Solo developers: SAME RULES APPLY**
- **Prototypes: SAME RULES APPLY**
- **Hotfixes: SAME RULES APPLY**
- **Experiments: SAME RULES APPLY**
- **"Just this once"**: BLOCKED

**The sdlc-enforcer has ZERO TOLERANCE and will enforce these rules without mercy.**
