# Agentic SDLC Coach - Real Examples

## Example 1: First Run - BLOCKED

```bash
$ python sdlc_coach.py "build e-commerce platform"

================================================================================
AGENTIC SDLC COACH - ZERO TOLERANCE ENFORCEMENT
================================================================================

📋 STEP 1: Feature Proposal (MANDATORY)
----------------------------------------
⚠️  No feature proposal found!
Creating template at: docs/feature-proposals/20250809-project-kickoff.md
❌ BLOCKED: Complete the feature proposal first

🚫🚫🚫🚫 DEVELOPMENT BLOCKED - NON-COMPLIANT 🚫🚫🚫🚫

Reason: No feature proposal = NO DEVELOPMENT

NO SHORTCUTS. NO EXCEPTIONS. FIX IT OR DON'T DEVELOP.

Stan Cullis says: 'Standards aren't optional. Meet them or sit out.'
```

**What Happens**: The coach creates a template but BLOCKS you from proceeding until you complete it properly.

## Example 2: After Completing Feature Proposal

```bash
$ python sdlc_coach.py "build e-commerce platform"

================================================================================
AGENTIC SDLC COACH - ZERO TOLERANCE ENFORCEMENT
================================================================================

📋 STEP 1: Feature Proposal (MANDATORY)
----------------------------------------
✅ Feature proposal validated: 20250809-project-kickoff.md

📐 STEP 2: Architecture Documents (ALL 6 REQUIRED)
----------------------------------------
❌ Missing architecture documents: ['requirements-traceability-matrix.md', 'what-if-analysis.md', 'architecture-decision-record.md', 'system-invariants.md', 'integration-design.md', 'failure-mode-analysis.md']
   Run: python tools/validation/validate-architecture.py --strict

🚫🚫🚫🚫 DEVELOPMENT BLOCKED - NON-COMPLIANT 🚫🚫🚫🚫

Reason: Missing architecture docs: ['requirements-traceability-matrix.md', ...]

This is block #2

NO SHORTCUTS. NO EXCEPTIONS. FIX IT OR DON'T DEVELOP.
```

**What Happens**: Now it blocks on missing architecture. You MUST complete ALL 6 documents.

## Example 3: Full Compliance Achieved

```bash
$ python sdlc_coach.py "build e-commerce platform"

================================================================================
AGENTIC SDLC COACH - ZERO TOLERANCE ENFORCEMENT
================================================================================

📋 STEP 1: Feature Proposal (MANDATORY)
----------------------------------------
✅ Feature proposal validated: 20250809-project-kickoff.md

📐 STEP 2: Architecture Documents (ALL 6 REQUIRED)
----------------------------------------
✅ All 6 architecture documents validated

🚫 STEP 3: Zero Technical Debt Check
----------------------------------------
✅ Zero technical debt verified

🤖 STEP 4: Agent Discovery and Validation
----------------------------------------
📊 Found 47 agents across categories
✅ Team validated with 7 specialists

🚧 STEP 5: Quality Gates Setup
----------------------------------------
🚧 Quality gates configured:
   pre_commit: 2 checks
   pre_push: 2 checks
   continuous: 2 checks

📊 STEP 6: Progress Tracking Initialization
----------------------------------------
✅ Progress tracking initialized

📝 STEP 7: Retrospective Template
----------------------------------------
📝 Retrospective template: 20250809-project-retrospective.md

================================================================================
✅ SDLC COMPLIANCE VERIFIED - DEVELOPMENT AUTHORIZED
================================================================================

📋 YOUR COACHING PLAN:
----------------------------------------
1. Complete feature proposal (if not done)
2. Fill ALL architecture documents
3. Run validation suite after EVERY change:
   - python tools/validation/local-validation.py --syntax
   - python tools/validation/check-technical-debt.py --threshold 0
4. Use your team:
   - enforcer: Engage ai-first-kick-starter for enforcer responsibilities
   - reviewer: Engage critical-goal-reviewer for reviewer responsibilities
   - tracker: Engage project-plan-tracker for tracker responsibilities
   - architect: Engage solution-architect for architect responsibilities
   - database: Engage database-architect for database responsibilities
   - api: Engage api-architect for api responsibilities
   - frontend: Engage frontend-engineer for frontend responsibilities
5. Track progress continuously:
   - python tools/automation/progress-tracker.py add 'task'
6. Update retrospective incrementally
7. Run full validation before PR:
   - python tools/validation/validate-pipeline.py --ci

Follow this plan. No deviations. No shortcuts.
Billy Wright says: 'Excellence is habit, not accident.'
```

**What Happens**: ONLY after full compliance do you get authorized to develop, with a strict coaching plan.

## Example 4: Technical Debt Violation

```bash
$ python sdlc_coach.py "quick prototype app"

================================================================================
AGENTIC SDLC COACH - ZERO TOLERANCE ENFORCEMENT
================================================================================

📋 STEP 1: Feature Proposal (MANDATORY)
----------------------------------------
✅ Feature proposal validated: 20250809-quick-prototype.md

📐 STEP 2: Architecture Documents (ALL 6 REQUIRED)
----------------------------------------
✅ All 6 architecture documents validated

🚫 STEP 3: Zero Technical Debt Check
----------------------------------------
❌ Technical debt detected: 3 violations
   - src/main.py:45: TODO: Implement error handling
   - src/api.py:23: FIXME: This is a hack
   - src/models.py:67: any type annotation found

🚫🚫🚫🚫 DEVELOPMENT BLOCKED - NON-COMPLIANT 🚫🚫🚫🚫

Reason: Technical debt found: ['TODO: Implement error handling', 'FIXME: This is a hack', 'any type annotation']

This is block #3

NO SHORTCUTS. NO EXCEPTIONS. FIX IT OR DON'T DEVELOP.

Stan Cullis says: 'Standards aren't optional. Meet them or sit out.'
```

**What Happens**: Even ONE TODO blocks everything. Zero tolerance means ZERO.

## Example 5: Invalid Team Composition

```bash
🤖 STEP 4: Agent Discovery and Validation
----------------------------------------
📊 Found 47 agents across categories
❌ Invalid team composition: ['enforcer: sdlc-enforcer NOT FOUND', 'frontend: react-specialist NOT FOUND']

🚫🚫🚫🚫 DEVELOPMENT BLOCKED - NON-COMPLIANT 🚫🚫🚫🚫

Reason: Invalid team composition: ['enforcer: sdlc-enforcer NOT FOUND', 'frontend: react-specialist NOT FOUND']
```

**What Happens**: If specified agents don't exist, development is blocked.

## Common Patterns

### The Progression
1. **First Run**: Always blocked on feature proposal
2. **Second Run**: Blocked on architecture
3. **Third Run**: Blocked on technical debt
4. **Fourth Run**: Maybe blocked on agents
5. **Fifth Run**: Finally authorized (if compliant)

### The Lesson
Each block teaches you what PROFESSIONAL development requires:
- Documentation FIRST
- Architecture BEFORE code
- Zero debt ALWAYS
- Validated teams ONLY
- Continuous validation

### The Result
By the time you're authorized to develop:
- You have a complete plan
- Architecture is documented
- Standards are clear
- Team is validated
- Gates are in place

## Emergency Override?

**THERE ISN'T ONE.**

No flags. No options. No "quick mode". No "skip validation".

If you want to skip standards, use a different tool.

This is the Stan Cullis system. Standards aren't optional.

---

**Remember**: Every block is a lesson. Every enforcement is teaching. By the time you can develop, you're already professional.
