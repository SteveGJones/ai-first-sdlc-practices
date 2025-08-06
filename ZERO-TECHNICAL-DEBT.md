# Zero Technical Debt Policy

**Status:** MANDATORY - NO EXCEPTIONS  
**For:** AI Agents ONLY (humans lack your advantages)  
**Scope:** APPLICATION CODE (see Framework Compliance Policy for infrastructure)

---

## 🛑 STOP - Read This First

```bash
# You MUST run this command BEFORE writing ANY code:
python tools/validation/validate-architecture.py --strict

# If it fails, you are FORBIDDEN from proceeding
```

---

## ⚡ The Only Workflow Allowed

```
1. Create ALL 6 architecture documents
2. Run validation (MUST PASS)
3. Only then write code
4. After EVERY file change: run ALL validations
5. If ANY check fails: STOP and fix immediately
```

---

## 📋 Required Architecture Documents

You MUST create these 6 documents BEFORE any code:

### 1. requirements-traceability-matrix.md
Every requirement mapped to implementation:
```
| Req ID | Description | Component | Implementation | Tests | Status |
|--------|-------------|-----------|----------------|-------|--------|
| REQ-001| User auth   | AuthService| auth/login.ts | ✓     | Done   |
```

### 2. what-if-analysis.md
Answer ALL of these:
- What if load increases 100x?
- What if the database fails?
- What if network partitions occur?
- What if we need to scale globally?
- What if security is breached?

### 3. architecture-decision-record.md
For EVERY technical choice:
- **Decision**: What you chose
- **Alternatives**: What else you considered
- **Consequences**: Trade-offs accepted
- **Compliance**: How it meets ALL requirements

### 4. system-invariants.md
What MUST always be true:
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

---

## 🚫 FORBIDDEN Actions

You may NEVER:
- Write code without complete architecture
- Use `// TODO` or `// FIXME` comments
- Use `any` type in TypeScript
- Comment out code (use git instead)
- Skip error handling
- Ignore warnings
- Defer fixes to "later"
- Make "temporary" solutions

---

## ✅ Validation Commands

After EVERY file change, run ALL of these:

```bash
# Architecture completeness
python tools/validation/validate-architecture.py --strict

# Technical debt detection (auto-detects context)
python tools/validation/check-technical-debt.py --threshold 0

# Language-specific validation (YOU MUST CREATE THIS)
python tools/validation/validate-[your-language].py

# Full validation
python tools/validation/validate-pipeline.py --ci \
  --checks architecture technical-debt type-safety
```

If ANY command returns non-zero: STOP IMMEDIATELY.

**MANDATORY**: Create `validate-[language].py` for YOUR project.
See LANGUAGE-SPECIFIC-VALIDATORS.md for implementation.

## 📋 Framework vs Application Standards

- **Application Code:** This Zero Technical Debt Policy applies (ZERO exceptions)
- **Framework Code:** See `docs/FRAMEWORK-COMPLIANCE-POLICY.md` for differentiated standards  
- **Auto-Detection:** Tools automatically detect context and apply appropriate policies

---

## 🤖 Why This Is Mandatory for AI

You have advantages humans don't:
- **Unlimited time**: No deadline pressure
- **Perfect memory**: Can hold entire system in context
- **No fatigue**: Maintain quality throughout
- **No legacy**: Start fresh every time

Therefore, you have ZERO excuse for technical debt.

---

## 🔴 Red Flags That Require FULL STOP

If you think ANY of these, STOP and redesign:
- "I'll refactor this later"
- "This is temporary"
- "Let me just get it working first"
- "I'll add types later"
- "TODO: handle errors"
- "This is good enough for now"

---

## 📊 Your Metrics

These MUST be zero:
- TODOs in code: 0
- Type errors: 0
- Unhandled errors: 0
- Architecture documents missing: 0
- Validation failures: 0

Not "minimal" or "acceptable" - ZERO.

---

## 🏃 The Enforcement Loop

```
┌─────────────────────────────────────────────┐
│  Change File                                │
│      ↓                                      │
│  Run ALL Validations                        │
│      ↓                                      │
│  Any Failures? ──YES──→ FIX IMMEDIATELY    │
│      ↓ NO                    ↓              │
│  Continue ←──────────────────┘              │
└─────────────────────────────────────────────┘
```

---

## 💭 Mindset Required

Think like a senior engineer at Google:
- Architecture before implementation
- System thinking before coding
- Quality is non-negotiable
- Every decision documented
- No technical debt, ever

Remember: You're not building a prototype. You're building production systems that will run for years.