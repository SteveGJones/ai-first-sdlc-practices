---
name: rules
description: AI-First SDLC compliance rules and standards. Use when checking code quality, validating architecture, enforcing zero technical debt, or making any compliance decision.
---

# AI-First SDLC Rules

You are operating under the AI-First SDLC framework. All code must comply with these rules.

For the complete rules reference, see [constitution.md](constitution.md).

## Quick Reference

### Validation Commands

- After writing code: `python tools/validation/local-validation.py --syntax`
- Before commits: `python tools/validation/local-validation.py --quick`
- Before PR: `python tools/validation/local-validation.py --pre-push`

### Zero Technical Debt Policy

- No `TODO`, `FIXME`, or `HACK` comments
- No `any` type annotations
- No commented-out code
- No deferred fixes or "temporary" solutions
- Use `./tmp/` not `/tmp/`

### 10 Mandatory Logging Points (Application Code)

1. Function entry/exit with context
2. Error handling with stack traces
3. External API/DB calls
4. State mutations
5. Security events
6. Business milestones
7. Performance anomalies
8. Configuration changes
9. Validation failures
10. Resource limits

**Never log:** passwords, tokens, PII, biometrics, encryption keys.

### Workflow

1. Feature proposal (`docs/feature-proposals/XX-name.md`)
2. Feature branch (`feature/name`) — never commit to main
3. Implement with continuous validation
4. Retrospective (`retrospectives/XX-name.md`)
5. PR — CI must pass
