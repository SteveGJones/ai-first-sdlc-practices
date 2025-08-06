# CLAUDE-CONTEXT-architecture.md

Load when creating architecture documents or implementing Zero Technical Debt policy.

## 🚧 BOOTSTRAP MODE - AI Setup Required

When you first run architecture validation on a fresh framework installation, you'll see:

```
🚀 BOOTSTRAP MODE - Architecture Template Setup
✨ Fresh installation detected - AI should complete templates
📝 Templates will be validated for basic structure only
🎯 Goal: Create project-specific architecture documents
```

**This is NORMAL and EXPECTED for fresh installs.**

### What Bootstrap Mode Means
- Framework was just installed via setup-smart.py
- Architecture templates exist but are unmodified
- System is ready for you to customize templates for this specific project
- You can proceed with template customization

### Bootstrap Mode Progression
1. **Bootstrap**: 70%+ templates unmodified → AI completes templates
2. **Intermediate**: Some templates done → AI finishes remaining
3. **Strict**: All templates customized → Full validation enforced

### Your Next Steps in Bootstrap Mode
1. **DO NOT PANIC** - this is the expected starting state
2. Run validation to see which templates need customization:
   ```bash
   python tools/validation/validate-architecture.py --strict
   ```
3. The system will show you exactly what to do:
   ```
   ✅ WHAT TO DO:
   1. Copy architecture templates to docs/architecture/
   2. Replace ALL placeholders with project-specific content:
      - [Feature Name] → Actual feature name
      - [Your specific details] → Real project details
   ```
4. Templates are in `templates/architecture/` - copy and modify for your project needs
5. Replace ALL template placeholders like `[Feature Name]`, `[Database Type]`, etc.
6. Focus on creating meaningful, project-specific content (not generic text)
7. Re-run validation to progress from bootstrap → intermediate → strict

### Bootstrap Mode Benefits
- **You can write code AFTER completing templates**
- **Bootstrap mode allows warnings but not errors**
- **System guides you through each step**

## Architecture-First Workflow

```bash
# MANDATORY before ANY code:
python tools/validation/validate-architecture.py --strict
```

If validation fails, STOP. Create missing documents first.

### Fresh Installation Bootstrap Process

For new framework installations, the validation runs in **Bootstrap Mode** automatically:

1. **Bootstrap Mode Detection**: Validates templates exist and have basic structure
2. **AI Action Required**: Copy templates from `templates/architecture/` to `docs/architecture/`
3. **Template Customization**: Replace ALL placeholders with project-specific content:
   - `[Feature Name]` → Actual feature being built
   - `[YYYY-MM-DD]` → Current date
   - `[Team/Roles responsible]` → Your project context
   - `FR-001, NFR-001` → Real requirements with meaningful IDs
4. **Progress to Intermediate Mode**: Once templates are customized, validation becomes stricter
5. **Final Strict Mode**: When all documents are complete, normal zero-debt validation applies

**Bootstrap Workflow for AI Agents**:
```bash
# 1. Check current state
python tools/validation/validate-architecture.py

# 2. If bootstrap mode detected, copy and customize ALL templates:
cp templates/architecture/*.md docs/architecture/

# 3. Edit each file to replace placeholders with real content

# 4. Validate again - should progress to next mode
python tools/validation/validate-architecture.py

# 5. Only when strict mode passes can you write code
```

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