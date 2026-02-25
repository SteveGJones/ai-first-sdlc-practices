# CONSTITUTION.md — AI-First SDLC Rules

All framework rules in one place. Each article has a level annotation:
- **[Prototype+]** — applies at all levels
- **[Production+]** — applies at Production and Enterprise levels
- **[Enterprise]** — applies only at Enterprise level

Check your level: `python tools/automation/sdlc-level.py check`

---

## Article 1: Git Workflow [Prototype+]

1.1. All changes go through feature branches and PRs. No direct commits to main.
1.2. Branch naming: `feature/`, `fix/`, `docs/`, `refactor/`.
1.3. Commit messages use conventional format: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`.
1.4. Main branch protection must be enabled.

## Article 2: Documentation [Production+]

2.1. Feature proposal required before implementation (`docs/feature-proposals/XX-name.md`).
2.2. Retrospective required before creating PR (`retrospectives/XX-name.md`).
2.3. Retrospective must include: what went well, what could improve, lessons learned, changes made.
2.4. Update retrospective after every significant change — not just at the end.

## Article 3: Architecture [Production+]

3.1. All 6 architecture documents required before writing code:
  - requirements-traceability-matrix.md
  - what-if-analysis.md
  - architecture-decision-record.md
  - system-invariants.md
  - integration-design.md
  - failure-mode-analysis.md

3.2. Architecture validation must pass: `python tools/validation/validate-architecture.py --strict`.
3.3. Start with the hardest integrations first.

*Bootstrap exception: Fresh installs may run in BOOTSTRAP MODE — see CLAUDE-CONTEXT-architecture.md.*

## Article 4: Code Quality [Prototype+]

4.1. No `TODO`, `FIXME`, or `HACK` comments. [Production+]
4.2. No `any` type annotations. [Production+]
4.3. No commented-out code — use version control instead. [Production+]
4.4. Error handling required for all operations — no suppressing exceptions.
4.5. No "temporary" solutions or deferred fixes. [Production+]
4.6. Use `./tmp/` (project-local, gitignored) not `/tmp/` (system temp).

## Article 5: Validation [Prototype+]

5.1. Run syntax check after writing code: `python tools/validation/local-validation.py --syntax`.
5.2. Run quick validation before commits: `python tools/validation/local-validation.py --quick`. [Production+]
5.3. Run full validation before PR: `python tools/validation/local-validation.py --pre-push`. [Production+]
5.4. Zero technical debt threshold: `python tools/validation/check-technical-debt.py --threshold 0`. [Production+]
5.5. CI is the source of truth — local success does not guarantee CI success.
5.6. Create a language-specific validator for your project (see LANGUAGE-SPECIFIC-VALIDATORS.md). [Production+]

## Article 6: Agent Collaboration [Production+]

6.1. Check for relevant specialist agents before starting significant work.
6.2. Use the Task tool to engage specialists for complex tasks.
6.3. You are a coordinator of experts, not a solo developer.
6.4. Proactively engage agents — do not ask permission to consult specialists.

*At Prototype level, agent collaboration is recommended but not required.*

## Article 7: Logging [Production+]

7.1. Required logging points: function entry/exit, errors & exceptions, external calls, state mutations, security events, business milestones, performance anomalies, config changes, validation failures, resource limits.
7.2. Forbidden in logs: passwords, tokens, PII, biometrics, encryption keys.

*Details: Load CLAUDE-CONTEXT-logging.md.*

## Article 8: Security & Environment [Prototype+]

8.1. Python virtual environment mandatory for Python projects.
8.2. Never install packages globally — use venv.
8.3. Never store secrets in code — use environment variables.
8.4. Validate and sanitize all external input.
8.5. Use parameterized queries for database access.

## Article 9: Self-Review [Prototype+]

9.1. Review all artifacts (proposals, code, tests, docs) against requirements before presenting.
9.2. Internal review process — users see only the final version.
9.3. Use mathematical/systematic solutions, not magic number patches.

## Article 10: Progressive Levels

10.1. **Prototype**: Quick exploration and MVPs. TODOs allowed. Basic validation only. Direct commits allowed for solo developers.
10.2. **Production**: Professional applications with real users. Zero technical debt. Full validation pipeline. All architecture documents required.
10.3. **Enterprise**: Large teams and regulated environments. Add compliance documentation, audit trails, multiple reviewer approval, stakeholder communication logs.
10.4. Check graduation readiness: `python tools/automation/sdlc-level.py graduation`.
10.5. Don't over-engineer prototypes. Don't under-engineer production systems.

---

*This document is the single source of truth for all AI-First SDLC rules. Enforcement is handled by the sdlc-enforcer agent and validation scripts. For setup instructions, see CLAUDE-SETUP.md. For context-specific guidance, see the context loading table in CLAUDE-CORE.md.*
