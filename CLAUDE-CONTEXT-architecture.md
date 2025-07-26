# CLAUDE-CONTEXT-architecture.md

Load when creating architecture documents or implementing Zero Technical Debt policy.

## Architecture-First Workflow

```bash
# MANDATORY before ANY code:
python tools/validation/validate-architecture.py --strict
```

If validation fails, STOP. Create missing documents first.

## Required Documents (ALL 6)

### 1. requirements-traceability-matrix.md
Map every requirement to implementation:
```
| Req ID | Description | Component | Implementation | Tests | Status |
|--------|-------------|-----------|----------------|-------|--------|
| REQ-001| User auth   | AuthService| auth/login.ts | ✓     | Done   |
```

### 2. what-if-analysis.md
Answer ALL scenarios:
- Load increases 100x?
- Database fails?
- Network partitions?
- Global scaling needed?
- Security breach occurs?

### 3. architecture-decision-record.md
Document EVERY choice:
- **Decision**: What chosen
- **Alternatives**: Options considered
- **Consequences**: Trade-offs
- **Compliance**: Requirements met

### 4. system-invariants.md
Define what MUST remain true:
- Data consistency rules
- Security boundaries
- Performance guarantees
- Availability requirements

### 5. integration-design.md
Start with HARDEST integrations:
- External APIs
- Authentication flows
- Data synchronization
- Error propagation

### 6. failure-mode-analysis.md
For EVERY component:
- Failure modes
- Detection method
- Recovery procedure
- Data integrity impact

## Zero Technical Debt Rules

### FORBIDDEN:
- Code without complete architecture
- TODO/FIXME/HACK comments
- `any` type annotations
- Commented-out code
- Skipping error handling
- Ignoring warnings
- "Temporary" solutions
- Deferred fixes

### Red Flags (STOP if thinking):
- "I'll refactor later"
- "This is temporary"
- "Get it working first"
- "Add types later"
- "Good enough for now"

## Validation After Every Change

```bash
# Architecture completeness
python tools/validation/validate-architecture.py --strict

# Technical debt (must be 0)
python tools/validation/check-technical-debt.py --threshold 0

# Language-specific (create for your project)
python tools/validation/validate-[language].py

# Full pipeline
python tools/validation/validate-pipeline.py --ci \
  --checks architecture technical-debt type-safety
```

## Required Metrics (ALL ZERO)
- TODOs in code: 0
- Type errors: 0
- Unhandled errors: 0
- Missing architecture: 0
- Validation failures: 0

## AI Agent Advantages
- Unlimited time (no deadlines)
- Perfect memory (full context)
- No fatigue (consistent quality)
- No legacy (fresh start)

Therefore: ZERO excuse for technical debt.

## The Enforcement Loop
```
Change File → Run ALL Validations → Any Failures? 
    ↓ NO                              ↓ YES
Continue                         FIX IMMEDIATELY
```

## Senior Engineer Mindset
- Architecture before implementation
- System thinking before coding
- Quality is non-negotiable
- Every decision documented
- No technical debt, ever

Remember: Building production systems, not prototypes.

## Template Locations
Find examples in:
- templates/architecture/*.md
- examples/architecture/*-example.md

## Language Validators
See CLAUDE-CONTEXT-language-*.md for creating validators.