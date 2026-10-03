# Containerised Claude Code Worker Delegation — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship the `sdlc-workflows` plugin — Archon workflow templates, command prompts, Docker image, setup-team integration, and delegation smoke test — enabling parallel containerised Claude Code workers running our SDLC specialist agents.

**Architecture:** Three-layer model. Layer 1 (this repo) ships SDLC plugins. Layer 2 (Archon, external) provides DAG execution and isolation. Layer 3 (`sdlc-workflows` plugin, new) wires them together with YAML workflows, PROMPT.md-style command briefs, a Docker image definition, and setup/run/status skills. The Docker image is the integration point — Archon + Claude Code + our plugins in one container.

**Tech Stack:** Archon CLI (TypeScript/Bun), Claude Code CLI + Agent SDK, Docker, Python 3, Git, YAML workflows, Markdown command prompts.

**Spec:** `docs/superpowers/specs/2026-04-10-containerised-delegation-design.md`

---

## Task 1: Plugin Skeleton — Create `sdlc-workflows` Directory Structure

**Files:**
- Create: `plugins/sdlc-workflows/README.md`
- Create: `plugins/sdlc-workflows/workflows/.gitkeep`
- Create: `plugins/sdlc-workflows/commands/.gitkeep`
- Create: `plugins/sdlc-workflows/docker/.gitkeep`
- Create: `plugins/sdlc-workflows/skills/.gitkeep`
- Create: `plugins/sdlc-workflows/agents/.gitkeep`
- Modify: `.claude-plugin/marketplace.json`
- Modify: `release-mapping.yaml`

- [ ] **Step 1: Create plugin directory structure**

```bash
mkdir -p plugins/sdlc-workflows/{workflows,commands,docker,skills,agents}
touch plugins/sdlc-workflows/workflows/.gitkeep
touch plugins/sdlc-workflows/commands/.gitkeep
touch plugins/sdlc-workflows/docker/.gitkeep
touch plugins/sdlc-workflows/skills/.gitkeep
touch plugins/sdlc-workflows/agents/.gitkeep
```

- [ ] **Step 2: Write plugin README**

Create `plugins/sdlc-workflows/README.md`:

```markdown
# sdlc-workflows

Archon workflow templates for delegated parallel execution of SDLC processes. Ships YAML DAGs, command prompts (PROMPT.md-style briefs), a Docker image definition, and setup/run/status skills.

## Prerequisites

- Claude Code CLI
- Archon CLI (https://archon.diy) — installed via `/sdlc-workflows:workflows-setup` or manually

## What This Plugin Provides

- **Workflows** — Archon YAML DAGs for parallel review, feature development, bulk refactor, and commissioned pipelines
- **Commands** — Substantial PROMPT.md-style briefs that frame each worker's role, process, and output format
- **Docker** — Dockerfile and Compose config for building `sdlc-worker` containers with Archon + Claude Code + SDLC plugins
- **Skills** — `workflows-setup` (install Archon + configure), `workflows-run` (execute a workflow), `workflows-status` (check progress)

## Usage

```bash
# Install the plugin
/plugin install sdlc-workflows@ai-first-sdlc

# Set up Archon and configure workflows
/sdlc-workflows:workflows-setup

# Run a parallel review
/sdlc-workflows:workflows-run sdlc-parallel-review
```

## Architecture

Archon orchestrates containers or worktrees. Each execution environment runs a Claude Code session with SDLC plugins installed. Workflow nodes reference our specialist agents by name. The Docker image is the integration point.

See `docs/superpowers/specs/2026-04-10-containerised-delegation-design.md` for full design.
```

- [ ] **Step 3: Register plugin in marketplace.json**

Add to the `plugins` array in `.claude-plugin/marketplace.json`, after the `sdlc-knowledge-base` entry:

```json
{ "name": "sdlc-workflows", "source": "./plugins/sdlc-workflows", "description": "Archon workflow templates for delegated parallel execution of SDLC processes", "version": "0.1.0" }
```

- [ ] **Step 4: Add release-mapping.yaml entry**

Append to `release-mapping.yaml`:

```yaml
# Workflow delegation plugin — Archon integration for parallel agent execution. EPIC #96.
# Components added incrementally by sub-features of the EPIC.
sdlc-workflows:
  # Populated as sub-features land (workflows, commands, skills, agents, docker)
  skills: []
  agents: []
```

- [ ] **Step 5: Verify plugin packaging**

Run: `python tools/validation/check-plugin-packaging.py`
Expected: sdlc-workflows appears in output, no packaging errors for the new plugin (empty skills/agents is valid at this stage).

- [ ] **Step 6: Commit**

```bash
git add plugins/sdlc-workflows/ .claude-plugin/marketplace.json release-mapping.yaml
git commit -m "feat(sdlc-workflows): create plugin skeleton for EPIC #96

Plugin directory structure, README, marketplace registration, and
release-mapping entry for the containerised delegation plugin.

No functional content yet — sub-features will add workflows,
commands, docker, skills, and agents incrementally."
```

---

## Task 2: Docker Image Definition

**Files:**
- Create: `plugins/sdlc-workflows/docker/Dockerfile`
- Create: `plugins/sdlc-workflows/docker/entrypoint.sh`
- Create: `plugins/sdlc-workflows/docker/build.sh`
- Create: `plugins/sdlc-workflows/docker/docker-compose.yml`

- [ ] **Step 1: Write the Dockerfile**

Create `plugins/sdlc-workflows/docker/Dockerfile`:

```dockerfile
FROM node:22-slim

# System dependencies (matching tests/integration/setup-smoke/Dockerfile)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    python3 python3-pip python3-venv git curl ca-certificates xz-utils && \
    rm -rf /var/lib/apt/lists/* && \
    ln -sf /usr/bin/python3 /usr/bin/python

# Claude Code CLI
RUN npm install -g @anthropic-ai/claude-code

# Archon CLI
RUN curl -fsSL https://archon.diy/install | bash && \
    mv /root/.archon/bin/archon /usr/local/bin/archon || true

# Build-time plugin installation (optional, for production images)
ARG INSTALL_PLUGINS_AT_BUILD=false

# Non-root user (UID 1001, matching smoke test convention — node:22-slim
# already has a 'node' user at UID 1000)
RUN useradd -m -s /bin/bash -u 1001 sdlc && \
    mkdir -p /workspace /home/sdlc/.claude /home/sdlc/.archon && \
    chown -R sdlc:sdlc /workspace /home/sdlc/.claude /home/sdlc/.archon

# Copy entrypoint (as root, before USER switch)
COPY entrypoint.sh /opt/entrypoint.sh
RUN chmod +x /opt/entrypoint.sh

# If build-time plugin install is enabled, install as sdlc user
# This bakes plugins into the image for faster startup
RUN if [ "$INSTALL_PLUGINS_AT_BUILD" = "true" ]; then \
      su - sdlc -c "claude --bare -p 'run: /plugin marketplace add SteveGJones/ai-first-sdlc-practices && /plugin install sdlc-core@ai-first-sdlc'" || true; \
    fi

USER sdlc
WORKDIR /workspace

ENTRYPOINT ["/opt/entrypoint.sh"]
```

- [ ] **Step 2: Write the entrypoint script**

Create `plugins/sdlc-workflows/docker/entrypoint.sh`:

```bash
#!/bin/bash
set -e

echo "=== SDLC Worker Container ==="

# Step 1: Ensure no API key overrides Max subscription
unset ANTHROPIC_API_KEY

# Step 2: Verify Claude Code is available
echo "Claude Code version: $(claude --version 2>/dev/null || echo 'NOT FOUND')"
echo "Archon version: $(archon --version 2>/dev/null || echo 'NOT FOUND')"
echo "Python version: $(python --version 2>/dev/null || echo 'NOT FOUND')"
echo ""

# Step 3: Check Claude Code authentication
AUTH_CHECK=$(claude -p "say ok" 2>&1 | head -1)
if echo "$AUTH_CHECK" | grep -qi "not logged in\|please run /login"; then
    echo "ERROR: Claude Code is not authenticated."
    echo ""
    echo "Run the login script first to populate the credential volume:"
    echo "  ./login.sh"
    exit 1
fi
echo "Auth: OK"
echo ""

# Step 4: Initialize git repo if needed (Archon needs a git repo)
if [ ! -d .git ]; then
    git init
    git config user.email "sdlc-worker@example.com"
    git config user.name "SDLC Worker"
    git add -A 2>/dev/null || true
    git commit -m "initial" --allow-empty 2>/dev/null || true
fi

# Step 5: Execute the assigned work
# If ARCHON_WORKFLOW is set, run an Archon workflow
# Otherwise, pass through to Claude Code
if [ -n "$ARCHON_WORKFLOW" ]; then
    echo "Running Archon workflow: $ARCHON_WORKFLOW"
    echo "Arguments: ${ARCHON_ARGS:-<none>}"
    echo ""
    archon run "$ARCHON_WORKFLOW" ${ARCHON_ARGS:+"$ARCHON_ARGS"}
elif [ -n "$CLAUDE_PROMPT" ]; then
    echo "Running Claude Code with prompt..."
    claude --dangerously-skip-permissions -p "$CLAUDE_PROMPT"
else
    echo "No ARCHON_WORKFLOW or CLAUDE_PROMPT set."
    echo "Usage:"
    echo "  ARCHON_WORKFLOW=sdlc-parallel-review  — run an Archon workflow"
    echo "  CLAUDE_PROMPT='fix the bug in app.py'  — run a direct Claude prompt"
    exit 1
fi

echo ""
echo "=== SDLC Worker Complete ==="
```

- [ ] **Step 3: Write the build script**

Create `plugins/sdlc-workflows/docker/build.sh`:

```bash
#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "Building sdlc-worker:latest..."
docker build -t sdlc-worker:latest "$SCRIPT_DIR"
echo ""
echo "Done. Image: sdlc-worker:latest"
echo ""
echo "To build with pre-installed plugins (faster startup, larger image):"
echo "  docker build --build-arg INSTALL_PLUGINS_AT_BUILD=true -t sdlc-worker:latest $SCRIPT_DIR"
```

- [ ] **Step 4: Write docker-compose.yml**

Create `plugins/sdlc-workflows/docker/docker-compose.yml`:

```yaml
# Local development setup for SDLC delegated workflows.
# Runs Archon with SDLC workflows and commands mounted.
#
# Prerequisites:
#   1. Build the image: ./build.sh
#   2. Login (first time): docker run --rm -it \
#        -v sdlc-worker-creds:/home/sdlc/.claude \
#        --entrypoint /bin/bash sdlc-worker:latest \
#        -c 'claude /login'
#
# Usage:
#   ARCHON_WORKFLOW=sdlc-parallel-review docker compose up
#
services:
  worker:
    image: sdlc-worker:latest
    environment:
      - ARCHON_WORKFLOW=${ARCHON_WORKFLOW:-}
      - ARCHON_ARGS=${ARCHON_ARGS:-}
      - CLAUDE_PROMPT=${CLAUDE_PROMPT:-}
    volumes:
      - sdlc-worker-creds:/home/sdlc/.claude
      - ${PROJECT_PATH:-.}:/workspace
      - ../workflows:/home/sdlc/.archon/workflows
      - ../commands:/home/sdlc/.archon/commands

volumes:
  sdlc-worker-creds:
```

- [ ] **Step 5: Verify the image builds**

Run: `cd plugins/sdlc-workflows/docker && bash build.sh`
Expected: Image `sdlc-worker:latest` builds successfully in <5 minutes.

Run: `docker image inspect sdlc-worker:latest --format '{{.Size}}' | numfmt --to=iec`
Expected: Image size <1GB.

- [ ] **Step 6: Verify Claude Code runs inside the container**

Run: `docker run --rm sdlc-worker:latest claude --version`
Expected: Claude Code version string printed (e.g., `2.1.89`).

Run: `docker run --rm sdlc-worker:latest archon --version`
Expected: Archon version string printed.

- [ ] **Step 7: Commit**

```bash
git add plugins/sdlc-workflows/docker/
git commit -m "feat(sdlc-workflows): add Docker image definition

Dockerfile, entrypoint, build script, and docker-compose for the
sdlc-worker container. Based on node:22-slim with non-root user
sdlc (UID 1001), matching existing smoke test patterns.

Includes Archon CLI and Claude Code CLI. Supports build-time or
runtime plugin installation via INSTALL_PLUGINS_AT_BUILD arg."
```

---

## Task 3: Command Prompts — Security Review (Reference Implementation)

**Files:**
- Create: `commands/sdlc-security-review.md` (source location for release-mapping)
- Modify: `release-mapping.yaml` (add commands to sdlc-workflows mapping)

This task creates the first full command prompt as the reference implementation. Subsequent commands follow the same pattern. We write one thoroughly, validate it, then use it as a template.

- [ ] **Step 1: Create the commands source directory**

```bash
mkdir -p commands
```

Note: Commands live at repo root under `commands/` (source location) and get packaged into `plugins/sdlc-workflows/commands/` via release-mapping, matching the pattern used by agents and skills.

- [ ] **Step 2: Write the security review command prompt**

Create `commands/sdlc-security-review.md`:

```markdown
# Security Architecture Review

## Your Role

You are a security architecture reviewer operating as part of a parallel review team. Other specialists are simultaneously reviewing architecture, performance, code quality, and test coverage. Your findings will be synthesised by a coordinator — focus exclusively on security concerns and do not duplicate their work.

You have access to the full SDLC plugin suite. Use the security-architect agent (via the Agent tool with subagent_type="sdlc-team-security:security-architect") for deep analysis of any component that crosses trust boundaries or handles credentials, PII, or external input.

## Context

You are reviewing changes in the current worktree. The project uses the AI-First SDLC framework.

**Before starting, load project context:**
1. Read `CLAUDE.md` for project rules and conventions
2. Read `CONSTITUTION.md` if it exists, particularly Article 7 (logging — never log secrets or PII)
3. Run `git log --oneline -10` to understand recent change history

## What To Do

### Phase 1: Discover the Change Set

Run these commands to understand what you are reviewing:

```bash
git diff $(git merge-base HEAD main)...HEAD --stat
```

Read every modified and added file. For deleted files, note what was removed and whether it had security implications (e.g., removing auth middleware).

### Phase 2: Threat Model the Changes

For each modified component, document:
- **Trust boundaries crossed** — does this code receive external input, call external services, access databases, write to filesystems?
- **Data flows** — what data enters, is transformed, stored, or transmitted? What sensitivity level?
- **Assumptions** — what does this code assume about its inputs? Are those assumptions validated?
- **Authentication/authorisation** — does this code check who the caller is and what they're allowed to do?

### Phase 3: OWASP Top 10 Review

Check each changed file systematically against:

1. **Injection** — SQL, command, template, log injection. Look for string concatenation in queries, `subprocess.run` with `shell=True`, f-strings in log messages with user input, template expressions with unescaped variables.

2. **Broken Authentication** — hardcoded credentials, weak session management, missing rate limiting on auth endpoints, tokens in URLs or logs.

3. **Sensitive Data Exposure** — secrets in error messages, PII in logs, API keys in client-side code, credentials in git history, overly verbose error responses.

4. **Security Misconfiguration** — debug flags left on, permissive CORS (`Access-Control-Allow-Origin: *`), default credentials, unnecessary HTTP methods enabled, missing security headers.

5. **Dependency Vulnerabilities** — check lock files (`package-lock.json`, `requirements.txt`, `Cargo.lock`) for known CVEs. Run `npm audit` or `pip-audit` if available.

6. **Broken Access Control** — missing authorisation checks, IDOR vulnerabilities, privilege escalation paths, insecure direct object references.

7. **Cross-Site Scripting (XSS)** — unescaped user input in HTML, `dangerouslySetInnerHTML`, template injection in frontend code.

8. **Insecure Deserialization** — `pickle.loads`, `yaml.load` (unsafe), `eval()`, `JSON.parse` of untrusted input without validation.

9. **Insufficient Logging** — security events not logged (failed auth, privilege changes, data access), or conversely, sensitive data being logged.

10. **Server-Side Request Forgery (SSRF)** — user-controlled URLs passed to HTTP clients, redirects to internal services.

### Phase 4: Project-Specific Security Standards

If the project has security-specific rules in CLAUDE.md or CONSTITUTION.md, verify compliance. Common checks:
- No secrets in code (use environment variables)
- No PII in logs
- Input validation at system boundaries
- Parameterised queries (never string concatenation for SQL)
- HTTPS for all external communication

### Phase 5: Automated Security Checks

If the project's validation pipeline includes a security check, run it:

```bash
python tools/validation/local-validation.py --security 2>/dev/null || echo "Security validation not available in this project"
```

Also run any project-specific security tooling mentioned in CLAUDE.md.

### Phase 6: Deep Analysis (if warranted)

For any component that:
- Handles authentication or session management
- Processes payment or financial data
- Stores or transmits PII
- Exposes a public API endpoint
- Modifies infrastructure or deployment configuration

Invoke the security-architect agent for deep analysis:

```
Use the Agent tool with subagent_type="sdlc-team-security:security-architect"
Prompt: "Deep security review of [component]. Focus on [specific concern]."
```

## Output Format

Structure your findings exactly as follows:

### Critical (blocks merge)
Issues that represent active vulnerabilities or high-likelihood exploitation paths.
- **[CRIT-N]** `file:line` — Description of the vulnerability — Remediation: specific fix

### High (should fix before merge)
Issues that represent security weaknesses but require specific conditions to exploit.
- **[HIGH-N]** `file:line` — Description — Remediation: specific fix

### Medium (fix in follow-up)
Issues that represent defence-in-depth gaps or best-practice violations.
- **[MED-N]** `file:line` — Description — Remediation: specific fix

### Passed Checks
List what you verified and found clean. This is evidence, not absence of evidence.
- OWASP-1 (Injection): Checked N files — no string concatenation in queries found
- OWASP-2 (Auth): Checked auth middleware — session management follows best practices
- ...

### Confidence Assessment
- **Thoroughly verified**: [list of components/concerns you checked in depth]
- **Spot-checked only**: [list of components you could only partially review due to scope]
- **Not verified (needs manual check)**: [list of runtime behaviours, infrastructure configs, or third-party integrations you couldn't assess from code alone]

## Constraints

- Do NOT modify any files. This is a review, not a fix.
- Do NOT review non-security concerns (architecture, performance, code style). Other agents handle those.
- If you find a critical vulnerability, flag it prominently with `[CRIT-N]` prefix — the synthesiser must not miss it.
- Time budget: complete within 15 minutes. If the change set is too large to review thoroughly, prioritise files that handle: (1) authentication/authorisation, (2) data access and storage, (3) external input processing, (4) infrastructure/deployment configuration.
- If you cannot determine whether something is a vulnerability without runtime testing, flag it under "Not verified" rather than guessing.
```

- [ ] **Step 3: Update release-mapping.yaml**

Add the command to the sdlc-workflows section in `release-mapping.yaml`:

```yaml
sdlc-workflows:
  skills: []
  agents: []
  commands:
    - source: commands/sdlc-security-review.md
```

Note: `commands` is a new key in release-mapping. The `check-plugin-packaging.py` validator may need to be updated to handle this in a later sub-feature. For now, add the mapping entry.

- [ ] **Step 4: Verify the command reads correctly**

Read back the file and confirm:
- Role framing is clear (security reviewer, parallel team context)
- Context loading tells the worker exactly what to read
- Process is step-by-step with specific commands
- Output format is structured with severity levels
- Constraints are explicit (no modifications, time budget, scope)

- [ ] **Step 5: Commit**

```bash
git add commands/sdlc-security-review.md release-mapping.yaml
git commit -m "feat(sdlc-workflows): add security review command prompt

Full PROMPT.md-style brief for the security review worker.
Covers: role framing, context loading, OWASP Top 10 systematic
review, project-specific standards, automated checks, deep
analysis escalation via security-architect agent.

This is the reference implementation — subsequent commands
follow the same structure."
```

---

## Task 4: Command Prompts — Remaining Commands

**Files:**
- Create: `commands/sdlc-plan.md`
- Create: `commands/sdlc-implement.md`
- Create: `commands/sdlc-architecture-review.md`
- Create: `commands/sdlc-performance-review.md`
- Create: `commands/sdlc-code-quality-review.md`
- Create: `commands/sdlc-test-coverage-review.md`
- Create: `commands/sdlc-validate.md`
- Create: `commands/sdlc-synthesise-reviews.md`
- Create: `commands/sdlc-merge-results.md`
- Modify: `release-mapping.yaml`

Each command follows the same structure as the security review (Task 3): role framing, context loading, step-by-step process, output format, constraints. Below are the specifications for each — the implementer should write each as a full PROMPT.md-style brief matching the depth and quality of `sdlc-security-review.md`.

- [ ] **Step 1: Write `commands/sdlc-plan.md`**

Role: Planning agent creating an implementation plan for a feature or task.
Agent: Use `sdlc-team-common:solution-architect` for architecture decisions.
Process: Read spec/issue/requirements → explore codebase → identify affected files → create file-partitioned task decomposition → output plan as structured JSON with tasks, file assignments, dependencies, and estimated complexity.
Output: JSON with `tasks[]` array, each having `id`, `description`, `files[]`, `depends_on[]`, `estimated_lines`.
Constraints: Plan only, no implementation. Each task must own non-overlapping files (the file-level partitioning pattern from R4). Target 500-1500 lines per task.

- [ ] **Step 2: Write `commands/sdlc-implement.md`**

Role: Implementation agent executing a single assigned task from a plan.
Agent: Use the appropriate `sdlc-lang-*` language expert agent for the project's primary language.
Process: Read the plan → read assigned files → implement changes following project conventions (CLAUDE.md) → run type checks after each file → run tests → commit with conventional commit message.
Output: Git commit with changes. Structured summary of files changed, tests passed/failed, and any blockers.
Constraints: Implement ONLY the assigned task. Do not modify files outside the assignment. Do not refactor unrelated code. If tests fail 3+ times on the same error, stop and report the blocker.

- [ ] **Step 3: Write `commands/sdlc-architecture-review.md`**

Role: Architecture reviewer in parallel review team.
Agent: Use `sdlc-team-common:solution-architect` for architectural assessment.
Process: Read changes → evaluate against SOLID principles, project architecture patterns, dependency direction, coupling/cohesion → check for architectural debt (new dependencies, layer violations, circular imports) → assess scalability impact.
Output: Structured findings with severity (Critical/High/Medium), specific file:line references, and remediation suggestions. Include "Passed Checks" section.
Constraints: Architecture only. Do not review security, performance, or style.

- [ ] **Step 4: Write `commands/sdlc-performance-review.md`**

Role: Performance reviewer in parallel review team.
Agent: Use `sdlc-team-common:performance-engineer` for performance analysis.
Process: Read changes → identify hot paths (loops, database queries, API calls, file I/O) → check for N+1 queries, missing pagination, unbounded collections, synchronous blocking, missing caching → assess algorithmic complexity.
Output: Structured findings with severity, specific code references, estimated impact (latency/throughput/memory), and remediation.
Constraints: Performance only. Do not review security, architecture, or style.

- [ ] **Step 5: Write `commands/sdlc-code-quality-review.md`**

Role: Code quality reviewer in parallel review team.
Agent: Use `sdlc-core:code-review-specialist` for quality assessment.
Process: Read changes → check naming conventions, code organisation, DRY violations, dead code, error handling patterns, test quality, documentation completeness → run linter if available → check for technical debt markers (TODO, FIXME, commented-out code).
Output: Structured findings with severity, code references, and specific improvement suggestions.
Constraints: Code quality only. Do not review security, performance, or architecture.

- [ ] **Step 6: Write `commands/sdlc-test-coverage-review.md`**

Role: Test coverage reviewer in parallel review team.
Agent: Use code review tools and the project's test runner.
Process: Read changes → identify which functions/methods are new or modified → check for corresponding test coverage → evaluate test quality (assertions, edge cases, error paths) → run test suite and report results → identify untested paths.
Output: Coverage summary (functions with tests, functions without, test quality assessment), specific untested code references, suggested test cases.
Constraints: Test coverage only. Write zero test code — list what needs tests and describe what the tests should verify.

- [ ] **Step 7: Write `commands/sdlc-validate.md`**

Role: Validation runner — deterministic, no AI judgement needed.
Process: Run the SDLC validation pipeline in order:
1. `python tools/validation/local-validation.py --syntax` (if available)
2. `python tools/validation/local-validation.py --quick` (if available)
3. Project-specific test command (detect from `package.json` scripts, `Makefile`, `pytest.ini`)
4. Report pass/fail for each check.
Output: JSON with `checks[]` array, each having `name`, `status` (pass/fail), `output` (truncated to 500 chars).
Constraints: This is a bash-heavy node. Run commands and report results. Do not fix anything.

- [ ] **Step 8: Write `commands/sdlc-synthesise-reviews.md`**

Role: Review synthesiser — receives outputs from all parallel review agents.
Process: Read all review outputs (passed as `$node_id.output` variables) → deduplicate findings → rank by severity across all reviews → identify cross-cutting themes → produce unified review summary → flag any Critical findings prominently.
Output: Unified review document with: executive summary (1-3 sentences), critical findings (blocks merge), high findings (should fix), medium findings (follow-up), cross-cutting themes, overall assessment (approve/request changes/block).
Constraints: Synthesise only. Do not add new findings. Do not re-review the code. Trust the specialist reviewers. If reviewers contradict each other, flag the contradiction rather than resolving it.

- [ ] **Step 9: Write `commands/sdlc-merge-results.md`**

Role: Merge coordinator for parallel implementation results.
Process: List all worker branches → sequential merge: merge worker A to main, rebase worker B on updated main, merge worker B, repeat → if merge conflict occurs, attempt resolution (read both versions + original, choose the version that matches the task spec) → run validation after each merge → report final state.
Output: JSON with `merges[]` array, each having `worker`, `status` (clean/conflict-resolved/conflict-unresolved), `files_merged`, `validation_passed`.
Constraints: If a conflict cannot be resolved automatically, mark it as `conflict-unresolved` and stop. Do not guess. Report the conflict details so a human can resolve.

- [ ] **Step 10: Update release-mapping.yaml with all commands**

Add all command sources to the `sdlc-workflows` section:

```yaml
sdlc-workflows:
  skills: []
  agents: []
  commands:
    - source: commands/sdlc-security-review.md
    - source: commands/sdlc-plan.md
    - source: commands/sdlc-implement.md
    - source: commands/sdlc-architecture-review.md
    - source: commands/sdlc-performance-review.md
    - source: commands/sdlc-code-quality-review.md
    - source: commands/sdlc-test-coverage-review.md
    - source: commands/sdlc-validate.md
    - source: commands/sdlc-synthesise-reviews.md
    - source: commands/sdlc-merge-results.md
```

- [ ] **Step 11: Commit**

```bash
git add commands/ release-mapping.yaml
git commit -m "feat(sdlc-workflows): add all command prompts

9 additional PROMPT.md-style command briefs: plan, implement,
architecture review, performance review, code quality review,
test coverage review, validate, synthesise, and merge.

Each follows the reference pattern from sdlc-security-review:
role framing, context loading, step-by-step process, structured
output format, and explicit constraints."
```

---

## Task 5: Workflow YAML — Parallel Review

**Files:**
- Create: `workflows/sdlc-parallel-review.yaml` (source location)
- Modify: `release-mapping.yaml`

- [ ] **Step 1: Write the parallel review workflow**

Create `workflows/sdlc-parallel-review.yaml`:

```yaml
name: sdlc-parallel-review
description: |
  Fan-out parallel review across 5 specialist agents, then synthesise.
  Use when: PR ready for comprehensive review before merge.
  Input: A branch with changes to review (current worktree branch vs main).
  Output: Unified review summary with severity-ranked findings.

  Workflow:
  1. Five specialist reviewers run in parallel (security, architecture,
     performance, code quality, test coverage)
  2. A synthesiser merges all findings into a unified review
  3. Validation runs as a deterministic bash check

  Each reviewer operates in a fresh context with our SDLC plugins
  installed, using the appropriate specialist agent.

provider: claude

nodes:
  - id: security-review
    command: sdlc-security-review
    context: fresh
    effort: high

  - id: architecture-review
    command: sdlc-architecture-review
    context: fresh

  - id: performance-review
    command: sdlc-performance-review
    context: fresh

  - id: code-quality-review
    command: sdlc-code-quality-review
    context: fresh

  - id: test-coverage-review
    command: sdlc-test-coverage-review
    context: fresh

  - id: validate
    command: sdlc-validate
    context: fresh

  - id: synthesise
    command: sdlc-synthesise-reviews
    depends_on:
      - security-review
      - architecture-review
      - performance-review
      - code-quality-review
      - test-coverage-review
      - validate
    trigger_rule: one_success
    context: fresh
```

- [ ] **Step 2: Update release-mapping.yaml**

Add workflows to the sdlc-workflows section:

```yaml
  workflows:
    - source: workflows/sdlc-parallel-review.yaml
```

- [ ] **Step 3: Validate YAML syntax**

Run: `python -c "import yaml; yaml.safe_load(open('workflows/sdlc-parallel-review.yaml'))"`
Expected: No errors.

- [ ] **Step 4: Commit**

```bash
git add workflows/sdlc-parallel-review.yaml release-mapping.yaml
git commit -m "feat(sdlc-workflows): add parallel review workflow

Fan-out/fan-in DAG: 5 specialist review agents run concurrently
(security, architecture, performance, code quality, test coverage)
plus a validation node. Synthesiser merges findings with
trigger_rule: one_success for resilience to individual failures."
```

---

## Task 6: Workflow YAMLs — Feature Development, Bulk Refactor, Commissioned Pipeline

**Files:**
- Create: `workflows/sdlc-feature-development.yaml`
- Create: `workflows/sdlc-bulk-refactor.yaml`
- Create: `workflows/sdlc-commissioned-pipeline.yaml`
- Modify: `release-mapping.yaml`

- [ ] **Step 1: Write feature development workflow**

Create `workflows/sdlc-feature-development.yaml`:

Sequential pipeline: plan → implement (loop until tests pass) → validate → review (parallel) → synthesise.

```yaml
name: sdlc-feature-development
description: |
  End-to-end feature development pipeline.
  Use when: Starting a new feature from a spec, issue, or idea.
  Input: Feature description or path to spec/issue.
  Output: Implemented feature with passing tests and completed review.

  Workflow:
  1. Plan: create implementation plan with file assignments
  2. Implement: loop — implement tasks, run validation, iterate until passing
  3. Validate: full SDLC validation pipeline
  4. Review: parallel specialist review (reuses sdlc-parallel-review pattern)
  5. Synthesise: unified review summary

provider: claude

nodes:
  - id: plan
    command: sdlc-plan
    context: fresh
    model: claude-opus-4-6[1m]

  - id: implement
    depends_on: [plan]
    command: sdlc-implement
    context: fresh
    model: claude-opus-4-6[1m]
    loop:
      until: ALL_TASKS_COMPLETE
      max_iterations: 10
      fresh_context: true

  - id: validate
    depends_on: [implement]
    command: sdlc-validate
    context: fresh

  - id: security-review
    depends_on: [validate]
    command: sdlc-security-review
    context: fresh

  - id: architecture-review
    depends_on: [validate]
    command: sdlc-architecture-review
    context: fresh

  - id: code-quality-review
    depends_on: [validate]
    command: sdlc-code-quality-review
    context: fresh

  - id: synthesise
    command: sdlc-synthesise-reviews
    depends_on: [security-review, architecture-review, code-quality-review]
    trigger_rule: one_success
    context: fresh
```

- [ ] **Step 2: Write bulk refactor workflow**

Create `workflows/sdlc-bulk-refactor.yaml`:

Plan decomposes into file-partitioned tasks → N parallel implementation nodes → sequential merge → validate.

```yaml
name: sdlc-bulk-refactor
description: |
  File-partitioned parallel refactor across a codebase.
  Use when: Large refactor, migration, or bulk change spanning many files.
  Input: Refactor description with scope (e.g., "rename all X to Y in src/").
  Output: Refactored code with passing tests, merged cleanly.

  Workflow:
  1. Plan: decompose into non-overlapping file sets (file-level partitioning)
  2. Implement A/B/C: parallel workers, each assigned a file set
  3. Merge: sequential git merge of all worker branches
  4. Validate: full SDLC validation pipeline

provider: claude

nodes:
  - id: plan
    command: sdlc-plan
    context: fresh
    model: claude-opus-4-6[1m]

  - id: implement-a
    depends_on: [plan]
    command: sdlc-implement
    context: fresh

  - id: implement-b
    depends_on: [plan]
    command: sdlc-implement
    context: fresh

  - id: implement-c
    depends_on: [plan]
    command: sdlc-implement
    context: fresh

  - id: merge
    depends_on: [implement-a, implement-b, implement-c]
    command: sdlc-merge-results
    trigger_rule: one_success
    context: fresh

  - id: validate
    depends_on: [merge]
    command: sdlc-validate
    context: fresh
```

- [ ] **Step 3: Write commissioned pipeline workflow**

Create `workflows/sdlc-commissioned-pipeline.yaml`:

Full autonomous SDLC: plan → implement → validate → review → approval gate → merge. Ties into EPIC #97.

```yaml
name: sdlc-commissioned-pipeline
description: |
  Full autonomous SDLC pipeline with approval gates.
  Use when: Commissioned feature development that should run end-to-end
  with human checkpoints at key decision points.
  Input: Feature spec, PRD, or issue description.
  Output: PR ready for merge with completed review.

  Workflow:
  1. Plan: create detailed implementation plan
  2. Approve plan: human reviews and approves the plan
  3. Implement: loop until tests pass
  4. Validate: full SDLC validation pipeline
  5. Review: parallel specialist review
  6. Synthesise: unified review summary
  7. Approve review: human reviews findings
  8. Create PR: push branch and create pull request

  This workflow connects to EPIC #97 (Commissioned SDLC). Different
  SDLC options would customise the node set and approval gates.

provider: claude

nodes:
  - id: plan
    command: sdlc-plan
    context: fresh
    model: claude-opus-4-6[1m]

  - id: approve-plan
    depends_on: [plan]
    approval:
      prompt: |
        Review the implementation plan above. The plan decomposes the
        feature into file-partitioned tasks with estimated complexity.

        Approve to proceed with implementation, or provide feedback
        to revise the plan.
      timeout: 86400

  - id: implement
    depends_on: [approve-plan]
    command: sdlc-implement
    context: fresh
    model: claude-opus-4-6[1m]
    loop:
      until: ALL_TASKS_COMPLETE
      max_iterations: 15
      fresh_context: true

  - id: validate
    depends_on: [implement]
    command: sdlc-validate
    context: fresh

  - id: security-review
    depends_on: [validate]
    command: sdlc-security-review
    context: fresh

  - id: architecture-review
    depends_on: [validate]
    command: sdlc-architecture-review
    context: fresh

  - id: code-quality-review
    depends_on: [validate]
    command: sdlc-code-quality-review
    context: fresh

  - id: synthesise
    command: sdlc-synthesise-reviews
    depends_on: [security-review, architecture-review, code-quality-review]
    trigger_rule: one_success
    context: fresh

  - id: approve-review
    depends_on: [synthesise]
    approval:
      prompt: |
        Review the synthesis of all specialist reviews above.

        If there are Critical or High findings, request fixes before
        approving. If all findings are Medium or below, approve to
        proceed with PR creation.
      timeout: 86400

  - id: create-pr
    depends_on: [approve-review]
    prompt: |
      Push the current branch and create a pull request.

      Use the synthesised review as the PR description body.
      Include the plan summary, implementation summary, and
      review findings.

      ```bash
      git push -u origin HEAD
      gh pr create --title "$plan.output.title" --body "$synthesise.output"
      ```
    context: fresh
```

- [ ] **Step 4: Update release-mapping.yaml**

Add all workflows:

```yaml
  workflows:
    - source: workflows/sdlc-parallel-review.yaml
    - source: workflows/sdlc-feature-development.yaml
    - source: workflows/sdlc-bulk-refactor.yaml
    - source: workflows/sdlc-commissioned-pipeline.yaml
```

- [ ] **Step 5: Validate all YAML files**

```bash
for f in workflows/*.yaml; do python -c "import yaml; yaml.safe_load(open('$f'))" && echo "OK: $f" || echo "FAIL: $f"; done
```

Expected: All 4 files pass YAML validation.

- [ ] **Step 6: Commit**

```bash
git add workflows/ release-mapping.yaml
git commit -m "feat(sdlc-workflows): add feature development, bulk refactor, and commissioned pipeline workflows

Three additional Archon DAG workflows:
- sdlc-feature-development: sequential plan → implement loop → validate → parallel review
- sdlc-bulk-refactor: file-partitioned parallel implementation → sequential merge → validate
- sdlc-commissioned-pipeline: full autonomous SDLC with approval gates (EPIC #97 tie-in)"
```

---

## Task 7: Delegation Coordinator Agent

**Files:**
- Create: `agents/delegation/delegation-coordinator.md`
- Modify: `release-mapping.yaml`

- [ ] **Step 1: Create agents source directory**

```bash
mkdir -p agents/delegation
```

- [ ] **Step 2: Write the delegation coordinator agent**

Create `agents/delegation/delegation-coordinator.md`:

```markdown
---
name: delegation-coordinator
description: "Specialist in task decomposition for parallel agent execution. Analyses codebases to identify parallelisable work, creates file-partitioned task assignments, and designs workflow configurations for Archon DAGs."
model: opus
tools: Read, Glob, Grep, Bash, Agent
examples:
- '<example>
Context: User wants to parallelise a large refactor across multiple modules.
  user: "I need to rename all database models from CamelCase to snake_case across the entire codebase."
  assistant: "I will analyse the codebase to identify all model files, map their dependencies, and create a file-partitioned task plan where each worker owns a non-overlapping set of files. I will check for shared files (like __init__.py imports or migration files) that need sequential handling, and produce an Archon-compatible task decomposition."
  <commentary>The delegation coordinator analyses codebases for parallelisability, creates file-level partitions, and identifies sequential dependencies that prevent naive parallelisation.</commentary>
</example>'
color: blue
---

# Delegation Coordinator

You are the Delegation Coordinator, a specialist in decomposing coding tasks for parallel execution by multiple Claude Code worker agents.

## Core Competencies

- Codebase analysis for parallelisability (dependency graphs, import trees, shared files)
- File-level partitioning with non-overlapping ownership (target: 95%+ merge success)
- Task granularity calibration (500-1500 lines per worker, 2-hour max duration)
- Sequential dependency identification (shared config, migration files, package manifests)
- Archon workflow configuration (DAG node design, dependency chains, output passing)

## Key Principles

1. **Spec-driven decomposition**: You write the boundaries. Workers do not self-decompose. Research shows this prevents 90% of agent collisions.
2. **File-level partitioning first**: Assign non-overlapping file sets to each worker. This achieves 95%+ merge success with zero conflicts.
3. **Identify sequential bottlenecks**: Shared files (package.json, migration files, route registries, config) cannot be safely parallelised. Flag them for sequential handling.
4. **Right-size tasks**: Multi-file tasks drop from 87% accuracy (single function) to 19% (5+ files). Target 500-1500 lines per worker.
5. **Minimal viable context**: Each worker gets task spec + file manifest + key interfaces + verification criteria. Not the full repo.

## When to Use This Agent

- Before running any parallel workflow (sdlc-bulk-refactor, sdlc-feature-development with parallel nodes)
- When a user asks "can this be parallelised?" or "how should I split this work?"
- When the sdlc-plan command needs to decompose work for multiple workers
```

- [ ] **Step 3: Update release-mapping.yaml**

Add to sdlc-workflows agents:

```yaml
  agents:
    - source: agents/delegation/delegation-coordinator.md
```

- [ ] **Step 4: Commit**

```bash
git add agents/delegation/ release-mapping.yaml
git commit -m "feat(sdlc-workflows): add delegation coordinator agent

Specialist agent for task decomposition and file-partitioned
parallel work assignment. Analyses codebases for parallelisability,
identifies sequential bottlenecks, and produces Archon-compatible
task plans."
```

---

## Task 8: Setup-Team Delegation Detection

**Files:**
- Modify: `plugins/sdlc-core/skills/setup-team/SKILL.md`

- [ ] **Step 1: Read the current setup-team skill**

Read `plugins/sdlc-core/skills/setup-team/SKILL.md` in full. Identify the insertion point — the delegation detection step should go after step 5 (tech stack discovery) and before the final recommendation output.

- [ ] **Step 2: Add delegation detection step**

Insert a new step after the technology discovery section (after step 5, before the recommendation output). The step should:

1. Check for delegation signals:
   - Count total lines of code: `find . -name '*.py' -o -name '*.ts' -o -name '*.js' -o -name '*.go' -o -name '*.java' -o -name '*.rs' | head -1000 | xargs wc -l 2>/dev/null | tail -1`
   - Count independent package manifests: `find . -maxdepth 3 -name 'package.json' -o -name 'requirements.txt' -o -name 'go.mod' -o -name 'Cargo.toml' | wc -l`
   - Check for `.archon/` directory (already using Archon)
   - Check for `ralph.yml` or `.ralph/` (already doing autonomous loops)
   - Check for `.github/workflows/` or `.gitlab-ci.yml` (CI/CD present)
   - Check for monorepo signals (multiple top-level dirs with their own deps)

2. If signals are present (weighted score above threshold), present the delegation question:

```
Your project shows signals that could benefit from delegated parallel
execution ({list specific signals found}).

Delegation lets you run multiple specialist agents in parallel — for
example, 5 review agents simultaneously checking security, architecture,
performance, code quality, and test coverage.

This requires Archon (https://archon.diy), an open-source workflow
engine that orchestrates Claude Code sessions. It will be installed
alongside your SDLC plugins.

Would you like to enable delegated workflows?
  (a) Yes — install Archon + sdlc-workflows plugin
  (b) Not now — I can add this later with /sdlc-workflows:workflows-setup
  (c) Tell me more — explain what delegation provides
```

3. If user selects (a): add `sdlc-workflows` to the install list and note that Archon CLI should be installed (either via the `workflows-setup` skill or manually).

4. If user selects (c): explain the four use cases (parallel features, autonomous pipelines, cloud workers, secure sandboxes) and then re-present the (a)/(b) choice.

5. Record the delegation decision in `.sdlc/team-config.json` under a new `delegation` key.

- [ ] **Step 3: Verify the modified skill reads coherently**

Read the full modified SKILL.md. Confirm the delegation step flows naturally between tech discovery and recommendation output. Confirm it doesn't duplicate or conflict with existing steps.

- [ ] **Step 4: Commit**

```bash
git add plugins/sdlc-core/skills/setup-team/SKILL.md
git commit -m "feat(setup-team): add delegation detection and Archon recommendation

Setup-team now detects delegation signals (large codebase, multiple
services, CI/CD, monorepo, existing Archon/Ralph configs) and
recommends Archon + sdlc-workflows plugin when appropriate.

Always explicit — Archon is named, linked, and explained. Users
can defer with option (b) and add later via workflows-setup."
```

---

## Task 9: Skills — workflows-setup

**Files:**
- Create: `skills/workflows-setup/SKILL.md`
- Modify: `release-mapping.yaml`

- [ ] **Step 1: Create skill directory**

```bash
mkdir -p skills/workflows-setup
```

- [ ] **Step 2: Write the workflows-setup skill**

Create `skills/workflows-setup/SKILL.md`:

```markdown
---
name: workflows-setup
description: Install Archon, configure SDLC workflows, and optionally build the Docker image. Run once after installing sdlc-workflows plugin.
disable-model-invocation: false
argument-hint: "[--with-docker | --workflows-only]"
---

# Set Up SDLC Delegated Workflows

Install Archon, copy SDLC workflow templates and command prompts into the project, and optionally build the sdlc-worker Docker image.

## Arguments

- `--with-docker` — Install Archon + copy workflows + build Docker image (full setup)
- `--workflows-only` (default) — Install Archon + copy workflows (no Docker build)

## Steps

### 1. Check if Archon is already installed

Run `archon --version 2>/dev/null`.

If Archon is installed, report:
```
Archon is already installed (version X.Y.Z).
```
Skip to step 3.

### 2. Install Archon

If Archon is not installed, inform the user and install:

```
Archon is not installed. Installing from https://archon.diy...
```

Run the installer:
```bash
curl -fsSL https://archon.diy/install | bash
```

Verify installation:
```bash
archon --version
```

If installation fails, report the error and suggest manual installation:
```
Archon installation failed. Please install manually:
  macOS/Linux: curl -fsSL https://archon.diy/install | bash
  Homebrew: brew install coleam00/archon/archon
  See: https://archon.diy for other options

Then re-run this skill.
```

### 3. Create .archon directories

```bash
mkdir -p .archon/workflows .archon/commands
```

### 4. Copy SDLC workflows

Copy workflow YAML files from the plugin install directory into `.archon/workflows/`:

For each file in `${CLAUDE_PLUGIN_ROOT}/workflows/`:
- Check if destination exists in `.archon/workflows/`
- If exists, skip (don't overwrite user customisations)
- If not, copy

Report:
```
Copied SDLC workflows:
  ✓ sdlc-parallel-review.yaml
  ✓ sdlc-feature-development.yaml
  ✓ sdlc-bulk-refactor.yaml
  ✓ sdlc-commissioned-pipeline.yaml
  ✗ skipped: sdlc-parallel-review.yaml (already exists)
```

### 5. Copy SDLC command prompts

Copy command Markdown files from `${CLAUDE_PLUGIN_ROOT}/commands/` into `.archon/commands/`:

Same skip-if-exists logic as step 4.

Report:
```
Copied SDLC commands:
  ✓ sdlc-security-review.md
  ✓ sdlc-plan.md
  ... (list all)
```

### 6. Verify workflow discovery

Run: `archon workflow list 2>/dev/null`

Check that SDLC workflows appear in the output. If they don't, check that `.archon/workflows/` is in Archon's workflow discovery path.

Report:
```
Archon workflow discovery:
  ✓ sdlc-parallel-review
  ✓ sdlc-feature-development
  ✓ sdlc-bulk-refactor
  ✓ sdlc-commissioned-pipeline
```

### 7. Optionally build Docker image (--with-docker only)

If `--with-docker` argument was provided:

Check if Docker is available:
```bash
docker --version 2>/dev/null
```

If Docker is not available:
```
Docker is not installed. Skipping Docker image build.
The Docker image is optional — Archon works with worktree isolation
without Docker. To build the image later:
  cd ${CLAUDE_PLUGIN_ROOT}/docker && bash build.sh
```

If Docker is available, build the image:
```bash
cd ${CLAUDE_PLUGIN_ROOT}/docker && bash build.sh
```

Report result.

### 8. Report next steps

```
SDLC delegated workflows are configured.

Next steps:
  1. Run a parallel review: archon run sdlc-parallel-review
     Or from Claude Code: /sdlc-workflows:workflows-run sdlc-parallel-review
  2. View available workflows: archon workflow list
  3. Customise workflows: edit .archon/workflows/sdlc-*.yaml
  4. Build Docker image (if not done): cd ${PLUGIN_ROOT}/docker && bash build.sh

For the full design, see:
  docs/superpowers/specs/2026-04-10-containerised-delegation-design.md
```

## Idempotency

This skill is safe to run multiple times. On second invocation:
- Archon already installed → skipped
- Existing workflow files → not overwritten
- Docker image → rebuilt if requested
```

- [ ] **Step 3: Update release-mapping.yaml**

Add to sdlc-workflows skills:

```yaml
  skills:
    - source: skills/workflows-setup/SKILL.md
```

- [ ] **Step 4: Commit**

```bash
git add skills/workflows-setup/ release-mapping.yaml
git commit -m "feat(sdlc-workflows): add workflows-setup skill

Installs Archon, copies SDLC workflow YAMLs and command prompts
into .archon/, verifies workflow discovery, and optionally builds
the Docker image. Idempotent — safe to run multiple times."
```

---

## Task 10: Skills — workflows-run and workflows-status

**Files:**
- Create: `skills/workflows-run/SKILL.md`
- Create: `skills/workflows-status/SKILL.md`
- Modify: `release-mapping.yaml`

- [ ] **Step 1: Create skill directories**

```bash
mkdir -p skills/workflows-run skills/workflows-status
```

- [ ] **Step 2: Write workflows-run skill**

Create `skills/workflows-run/SKILL.md`:

```markdown
---
name: workflows-run
description: Run an SDLC delegated workflow via Archon. Wraps the archon CLI with project-aware defaults.
disable-model-invocation: false
argument-hint: "<workflow-name> [arguments]"
---

# Run SDLC Workflow

Execute a named SDLC workflow via the Archon CLI.

## Arguments

- First argument: workflow name (e.g., `sdlc-parallel-review`)
- Remaining arguments: passed through to Archon as workflow arguments

## Steps

### 1. Verify Archon is installed

Run `archon --version 2>/dev/null`. If not found:
```
Archon is not installed. Run /sdlc-workflows:workflows-setup first.
```

### 2. Verify workflow exists

Run `archon workflow list 2>/dev/null` and check if the requested workflow name appears.

If not found:
```
Workflow '{name}' not found. Available workflows:
{list from archon workflow list}

To install SDLC workflows, run /sdlc-workflows:workflows-setup
```

### 3. Run the workflow

Execute:
```bash
archon run {workflow-name} {remaining-arguments}
```

Stream the output to the user. Report completion status when done.

### 4. Report results

After workflow completes, report:
- Workflow name and duration
- Node completion status (which nodes passed/failed/skipped)
- Final output (from the terminal node)
- Any errors or warnings
```

- [ ] **Step 3: Write workflows-status skill**

Create `skills/workflows-status/SKILL.md`:

```markdown
---
name: workflows-status
description: Check the status of running or recent SDLC delegated workflows.
disable-model-invocation: false
argument-hint: "[--running | --recent | <run-id>]"
---

# SDLC Workflow Status

Check the status of Archon workflow runs.

## Arguments

- `--running` — show currently running workflows
- `--recent` (default) — show recent workflow runs
- `<run-id>` — show details for a specific run

## Steps

### 1. Verify Archon is installed

Run `archon --version 2>/dev/null`. If not found:
```
Archon is not installed. Run /sdlc-workflows:workflows-setup first.
```

### 2. Query workflow status

For `--running`:
```bash
archon workflow list --running 2>/dev/null
```

For `--recent`:
```bash
archon workflow list --recent 2>/dev/null
```

For a specific run:
```bash
archon workflow status {run-id} 2>/dev/null
```

### 3. Present results

Format the output showing:
- Run ID, workflow name, start time, duration
- Node status: completed / running / pending / failed / skipped
- For failed nodes: error summary
- For completed runs: final output summary
```

- [ ] **Step 4: Update release-mapping.yaml**

Add both skills:

```yaml
  skills:
    - source: skills/workflows-setup/SKILL.md
    - source: skills/workflows-run/SKILL.md
    - source: skills/workflows-status/SKILL.md
```

- [ ] **Step 5: Commit**

```bash
git add skills/workflows-run/ skills/workflows-status/ release-mapping.yaml
git commit -m "feat(sdlc-workflows): add workflows-run and workflows-status skills

workflows-run wraps the archon CLI for executing named workflows.
workflows-status queries running and recent workflow runs."
```

---

## Task 11: Delegation Smoke Test

**Files:**
- Create: `tests/integration/delegation-smoke/Dockerfile`
- Create: `tests/integration/delegation-smoke/entrypoint.sh`
- Create: `tests/integration/delegation-smoke/build.sh`
- Create: `tests/integration/delegation-smoke/run.sh`
- Create: `tests/integration/delegation-smoke/login.sh`
- Create: `tests/integration/delegation-smoke/PROMPT.md`
- Create: `tests/integration/delegation-smoke/ralph.yml`
- Create: `tests/integration/delegation-smoke/workflows/smoke-parallel-review.yaml`
- Create: `tests/integration/delegation-smoke/commands/smoke-review-a.md`
- Create: `tests/integration/delegation-smoke/commands/smoke-review-b.md`
- Create: `tests/integration/delegation-smoke/fixtures/miniproject/README.md`
- Create: `tests/integration/delegation-smoke/fixtures/miniproject/src/app.py`
- Create: `tests/integration/delegation-smoke/fixtures/miniproject/tests/test_app.py`
- Create: `tests/integration/delegation-smoke/README.md`

- [ ] **Step 1: Create directory structure**

```bash
mkdir -p tests/integration/delegation-smoke/{workflows,commands,fixtures/miniproject/src,fixtures/miniproject/tests}
```

- [ ] **Step 2: Write the fixture project**

Create `tests/integration/delegation-smoke/fixtures/miniproject/README.md`:

```markdown
# MiniProject

A tiny Flask API for testing SDLC delegation smoke tests. Contains deliberate issues for reviewers to find.

## Tech Stack
- Python 3, Flask
- SQLite for storage

## Known Issues (for smoke test validation)
- SQL injection vulnerability in /users endpoint
- Missing test for delete endpoint
- No input validation on user creation
```

Create `tests/integration/delegation-smoke/fixtures/miniproject/src/app.py`:

```python
"""MiniProject — tiny Flask API with deliberate security issues for smoke testing."""

from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)
DATABASE = "users.db"


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    db = get_db()
    db.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT, email TEXT)")
    db.commit()
    db.close()


@app.route("/users", methods=["GET"])
def list_users():
    db = get_db()
    # DELIBERATE VULNERABILITY: SQL injection via query parameter
    name_filter = request.args.get("name", "")
    cursor = db.execute(f"SELECT * FROM users WHERE name LIKE '%{name_filter}%'")
    users = [dict(row) for row in cursor.fetchall()]
    db.close()
    return jsonify(users)


@app.route("/users", methods=["POST"])
def create_user():
    data = request.get_json()
    # DELIBERATE ISSUE: No input validation
    db = get_db()
    db.execute("INSERT INTO users (name, email) VALUES (?, ?)", (data["name"], data["email"]))
    db.commit()
    db.close()
    return jsonify({"status": "created"}), 201


@app.route("/users/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):
    db = get_db()
    db.execute("DELETE FROM users WHERE id = ?", (user_id,))
    db.commit()
    db.close()
    return jsonify({"status": "deleted"})


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
```

Create `tests/integration/delegation-smoke/fixtures/miniproject/tests/test_app.py`:

```python
"""Tests for MiniProject — deliberately incomplete for smoke test validation."""

import pytest
from src.app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_list_users_returns_json(client):
    response = client.get("/users")
    assert response.status_code == 200
    assert response.content_type == "application/json"


def test_create_user(client):
    response = client.post("/users", json={"name": "Alice", "email": "alice@example.com"})
    assert response.status_code == 201


# DELIBERATE GAP: No test for DELETE /users/<id>
# DELIBERATE GAP: No test for SQL injection vulnerability
# DELIBERATE GAP: No test for missing input validation
```

- [ ] **Step 3: Write smoke test workflow and commands**

Create `tests/integration/delegation-smoke/workflows/smoke-parallel-review.yaml`:

```yaml
name: smoke-parallel-review
description: |
  Minimal delegation smoke test. Two review agents run in parallel.
  Validates: Archon executes, nodes run concurrently, outputs captured,
  synthesis works.

provider: claude

nodes:
  - id: review-structure
    command: smoke-review-a
    context: fresh

  - id: review-tests
    command: smoke-review-b
    context: fresh

  - id: synthesise
    depends_on: [review-structure, review-tests]
    trigger_rule: one_success
    prompt: |
      Two parallel reviews have completed. Synthesise their findings.

      Review A (structure): $review-structure.output
      Review B (tests): $review-tests.output

      Output a JSON object with your synthesis:
      {"issues_found": <number>, "review_a_completed": <bool>, "review_b_completed": <bool>, "summary": "<one sentence>"}
    output_format:
      type: object
      properties:
        issues_found:
          type: number
        review_a_completed:
          type: boolean
        review_b_completed:
          type: boolean
        summary:
          type: string
      required: [issues_found, review_a_completed, review_b_completed, summary]
```

Create `tests/integration/delegation-smoke/commands/smoke-review-a.md`:

```markdown
# Structure Review (Smoke Test)

## Your Role

You are reviewing the code structure of a small Python Flask application.
This is a smoke test — keep your review brief but thorough enough to
demonstrate that the review process works.

## What To Do

1. Read all Python source files in `src/`
2. Check for: module organisation, function naming, import structure,
   error handling patterns, and any obvious code smells
3. Note any security concerns you spot (but security is not your primary focus)

## Output

List your findings as bullet points. Include at least one finding
(the fixture project has deliberate issues). Keep the review under 500 words.
```

Create `tests/integration/delegation-smoke/commands/smoke-review-b.md`:

```markdown
# Test Coverage Review (Smoke Test)

## Your Role

You are reviewing the test coverage of a small Python Flask application.
This is a smoke test — keep your review brief but thorough enough to
demonstrate that the review process works.

## What To Do

1. Read all test files in `tests/`
2. Read the source files in `src/` to understand what should be tested
3. Identify: which functions have tests, which don't, and what edge cases
   are missing

## Output

List your findings as bullet points. Include at least one finding about
missing test coverage (the fixture project has deliberate gaps).
Keep the review under 500 words.
```

- [ ] **Step 4: Write the smoke test Dockerfile**

Create `tests/integration/delegation-smoke/Dockerfile`:

```dockerfile
FROM sdlc-worker:latest

# Copy smoke test fixtures and Archon configs
USER root
COPY fixtures/miniproject/ /workspace/
COPY workflows/ /home/sdlc/.archon/workflows/
COPY commands/ /home/sdlc/.archon/commands/
COPY PROMPT.md /workspace/PROMPT.md
COPY ralph.yml /workspace/ralph.yml
COPY entrypoint.sh /opt/entrypoint.sh
RUN chmod +x /opt/entrypoint.sh && \
    chown -R sdlc:sdlc /workspace /home/sdlc/.archon
USER sdlc
WORKDIR /workspace

ENTRYPOINT ["/opt/entrypoint.sh"]
```

- [ ] **Step 5: Write the smoke test entrypoint**

Create `tests/integration/delegation-smoke/entrypoint.sh`:

```bash
#!/bin/bash
set -e

echo "=== SDLC Delegation Smoke Test ==="
echo ""

# Step 1: Verify tools
unset ANTHROPIC_API_KEY
echo "Claude Code: $(claude --version 2>/dev/null || echo 'NOT FOUND')"
echo "Archon: $(archon --version 2>/dev/null || echo 'NOT FOUND')"
echo ""

# Step 2: Check auth
AUTH_CHECK=$(claude -p "say ok" 2>&1 | head -1)
if echo "$AUTH_CHECK" | grep -qi "not logged in\|please run /login"; then
    echo "ERROR: Claude Code not authenticated. Run login.sh first."
    exit 1
fi
echo "Auth: OK"
echo ""

# Step 3: Init git repo
if [ ! -d .git ]; then
    git init
    git config user.email "smoke-test@example.com"
    git config user.name "Delegation Smoke Test"
    git add -A
    git commit -m "initial"
fi

# Step 4: Install SDLC plugins
echo "Installing SDLC plugins..."
claude --bare -p "/plugin marketplace add SteveGJones/ai-first-sdlc-practices && /plugin install sdlc-core@ai-first-sdlc" 2>&1 | tail -3
echo ""

# Step 5: Verify Archon sees workflows
echo "Archon workflows:"
archon workflow list 2>/dev/null || echo "WARNING: archon workflow list failed"
echo ""

# Step 6: Run the smoke test via Ralph (Ralph drives the overall test)
echo "Starting Ralph loop..."
ralph run

echo ""
echo "=== Delegation Smoke Test Complete ==="
```

- [ ] **Step 6: Write the PROMPT.md (Ralph-driven outer test)**

Create `tests/integration/delegation-smoke/PROMPT.md`:

```markdown
# Delegation Smoke Test

You are running inside a Docker container with Archon and Claude Code installed. Your job is to execute a parallel workflow via Archon and verify it works.

## Phase 1: Verify Prerequisites

Check the following. Report PASS or FAIL for each:

1. Archon CLI is installed: `archon --version`
2. Archon sees the smoke workflow: `archon workflow list` shows `smoke-parallel-review`
3. SDLC plugins are installed: Check for sdlc-core in installed plugins

If any prerequisite fails, report and stop.

## Phase 2: Run the Parallel Workflow

Execute the smoke parallel review workflow:

```bash
archon run smoke-parallel-review
```

Monitor the output. This workflow runs two review agents in parallel (review-structure and review-tests), then synthesises their findings.

## Phase 3: Verify Results

After the workflow completes, check:

4. Node `review-structure` completed (output was captured)
5. Node `review-tests` completed (output was captured)
6. Both nodes ran concurrently (check Archon logs — start times should be within 5 seconds of each other)
7. `synthesise` node produced valid JSON with all required fields (issues_found, review_a_completed, review_b_completed, summary)
8. The synthesised output found at least 1 issue (the fixture has deliberate problems)
9. Total workflow duration was under 10 minutes

Print a summary:

```
=== Delegation Smoke Test Results ===
Check 1 (Archon installed):          PASS/FAIL
Check 2 (workflow discovered):       PASS/FAIL
Check 3 (plugins installed):         PASS/FAIL
Check 4 (review-structure complete): PASS/FAIL
Check 5 (review-tests complete):     PASS/FAIL
Check 6 (parallel execution):        PASS/FAIL
Check 7 (synthesis JSON valid):      PASS/FAIL
Check 8 (issues found):             PASS/FAIL
Check 9 (duration < 10min):         PASS/FAIL

Result: X/9 PASS
```

Output `LOOP_COMPLETE`.
```

- [ ] **Step 7: Write ralph.yml**

Create `tests/integration/delegation-smoke/ralph.yml`:

```yaml
max_iterations: 5
sigil: LOOP_COMPLETE
prompt_file: PROMPT.md
```

- [ ] **Step 8: Write build.sh, run.sh, login.sh**

Create `tests/integration/delegation-smoke/build.sh`:

```bash
#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DOCKER_DIR="$(cd "$SCRIPT_DIR/../../plugins/sdlc-workflows/docker" && pwd)"

# Ensure base image exists
if ! docker image inspect sdlc-worker:latest >/dev/null 2>&1; then
    echo "Base image sdlc-worker:latest not found. Building..."
    bash "$DOCKER_DIR/build.sh"
fi

echo "Building delegation-smoke-base:latest..."
docker build -t delegation-smoke-base:latest "$SCRIPT_DIR"
echo ""
echo "Done. Image: delegation-smoke-base:latest"
echo "Run the smoke test with: $SCRIPT_DIR/run.sh"
```

Create `tests/integration/delegation-smoke/run.sh`:

```bash
#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Verify base image exists
if ! docker image inspect delegation-smoke-base:latest >/dev/null 2>&1; then
    echo "Smoke test image not found. Building..."
    "$SCRIPT_DIR/build.sh"
fi

# Check if the credential volume exists (reuse setup-smoke volume)
if ! docker volume inspect sdlc-smoke-claude-creds >/dev/null 2>&1; then
    echo "ERROR: Credential volume 'sdlc-smoke-claude-creds' not found."
    echo ""
    echo "First-time setup required. Run:"
    echo "  $SCRIPT_DIR/login.sh"
    echo ""
    echo "Or if you already ran the setup-smoke login:"
    echo "  The delegation smoke test reuses the same credential volume."
    exit 1
fi

unset ANTHROPIC_API_KEY

echo "=== Running SDLC Delegation Smoke Test ==="
echo "Auth: Claude Code Max subscription (from named volume)"
echo ""

docker run --rm \
    -v sdlc-smoke-claude-creds:/home/sdlc/.claude \
    delegation-smoke-base:latest

echo ""
echo "=== Delegation Smoke Test Finished ==="
```

Create `tests/integration/delegation-smoke/login.sh`:

```bash
#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DOCKER_DIR="$(cd "$SCRIPT_DIR/../../plugins/sdlc-workflows/docker" && pwd)"

# Ensure base image exists
if ! docker image inspect sdlc-worker:latest >/dev/null 2>&1; then
    echo "Base image sdlc-worker:latest not found. Building..."
    bash "$DOCKER_DIR/build.sh"
fi

echo "Starting interactive login container..."
echo "Run 'claude /login' inside the container."
echo ""

docker run --rm -it \
    -v sdlc-smoke-claude-creds:/home/sdlc/.claude \
    --entrypoint /bin/bash \
    sdlc-worker:latest \
    -c 'claude /login'
```

- [ ] **Step 9: Write README**

Create `tests/integration/delegation-smoke/README.md`:

```markdown
# Delegation Smoke Test

End-to-end test for the SDLC delegated workflow system. Validates that Archon orchestrates parallel Claude Code workers with our SDLC plugins.

## Prerequisites

- Docker
- Claude Code Max subscription (for auth)
- Credential volume `sdlc-smoke-claude-creds` (created by `login.sh` or shared from `setup-smoke`)

## Running

```bash
# First time: login to create credential volume
./login.sh

# Build and run
./build.sh
./run.sh
```

## What It Tests

1. Archon CLI installed and on PATH
2. Archon discovers SDLC workflow (smoke-parallel-review)
3. SDLC plugins install correctly
4. Two review nodes execute and complete
5. Nodes run concurrently (parallel execution verified)
6. Synthesis node produces valid structured JSON
7. Reviewers find deliberate issues in fixture project
8. Total duration under 10 minutes

## Fixture Project

`fixtures/miniproject/` is a tiny Flask API with deliberate issues:
- SQL injection in `/users` GET endpoint
- Missing input validation on `/users` POST
- Incomplete test coverage (no DELETE test, no security tests)

## Shared Infrastructure

Reuses the `sdlc-smoke-claude-creds` Docker volume from `tests/integration/setup-smoke/`.
Run `setup-smoke/login.sh` once — both smoke tests share the same auth.
```

- [ ] **Step 10: Commit**

```bash
git add tests/integration/delegation-smoke/
git commit -m "feat(sdlc-workflows): add delegation smoke test

End-to-end test: Archon orchestrates 2 parallel review agents on a
fixture Flask project with deliberate issues (SQL injection, missing
tests). Validates parallel execution, output capture, and synthesis.

9 success criteria. Reuses credential volume from setup-smoke.
Fixture project at miniproject/ with known issues for reviewers."
```

---

## Task 12: Release Plugin Packaging

**Files:**
- Modify: `release-mapping.yaml` (final state verification)

- [ ] **Step 1: Verify release-mapping.yaml has all entries**

Read `release-mapping.yaml` and confirm the `sdlc-workflows` section includes:
- All 10 command sources
- All 4 workflow sources
- All 3 skill sources
- 1 agent source
- Docker files are NOT in release-mapping (they're in the plugin dir directly, not source-mapped)

- [ ] **Step 2: Run release-plugin to package**

Run: `/sdlc-core:release-plugin`

Verify that `plugins/sdlc-workflows/` gets populated with all the files from their source locations.

- [ ] **Step 3: Run plugin packaging check**

Run: `python tools/validation/check-plugin-packaging.py`

Expected: No errors for sdlc-workflows plugin. All source files present in the plugin directory.

- [ ] **Step 4: Run full validation**

Run: `python tools/validation/local-validation.py --pre-push`

Expected: All 10 checks pass.

- [ ] **Step 5: Commit any packaging fixes**

If release-plugin or validation found issues, fix and commit:

```bash
git add plugins/sdlc-workflows/ release-mapping.yaml
git commit -m "chore(sdlc-workflows): sync plugin packaging

Run release-plugin to populate plugins/sdlc-workflows/ from
source locations defined in release-mapping.yaml."
```

---

## Task 13: Update CLAUDE.md and Marketplace

**Files:**
- Modify: `CLAUDE.md` (update Active Work section)
- Modify: `.claude-plugin/marketplace.json` (verify entry from Task 1)

- [ ] **Step 1: Update CLAUDE.md Active Work**

Add EPIC #96 to the Active Work section with current status:

```markdown
- **EPIC #96** — Containerised Claude Code workers. `sdlc-workflows` plugin ships Archon workflow templates, command prompts, Docker image, and setup-team delegation detection. See `docs/superpowers/specs/2026-04-10-containerised-delegation-design.md`.
```

- [ ] **Step 2: Update Plugin Family table**

Add sdlc-workflows to the Plugin Family table in CLAUDE.md:

```markdown
| `sdlc-workflows` | Archon workflow templates for delegated parallel execution |
```

- [ ] **Step 3: Update Available Skills table**

Add the three new skills:

```markdown
| `/sdlc-workflows:workflows-setup` | Install Archon + configure SDLC workflows |
| `/sdlc-workflows:workflows-run` | Execute a named SDLC workflow via Archon |
| `/sdlc-workflows:workflows-status` | Check running/recent workflow status |
```

- [ ] **Step 4: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: update CLAUDE.md with sdlc-workflows plugin and EPIC #96 status"
```

---

## Self-Review Checklist

**Spec coverage:**
- Section 1 (Problem Statement): Addressed by overall architecture in Tasks 1-13
- Section 2 (Architecture): Three-layer model implemented across Tasks 1 (plugin), 2 (Docker), 3-4 (commands), 5-6 (workflows)
- Section 3 (Plugin Structure): Task 1 (skeleton), Tasks 3-4 (commands), Tasks 5-6 (workflows), Tasks 9-10 (skills), Task 7 (agent)
- Section 4 (Docker Image): Task 2
- Section 5 (Setup-Team Integration): Task 8
- Section 6 (Smoke Test): Task 11
- Section 7 (ContainerProvider): Out of scope for this plan — parallel work in Archon's repo
- Section 8 (Phasing): Plan follows sub-feature order 0-5
- Section 9 (Out of Scope): Not included in plan (correct)
- Section 10 (Research Foundation): Referenced in spec, not reimplemented
- Section 11 (Success Metrics): Validated by smoke test (Task 11) and packaging checks (Task 12)

**Placeholder scan:** No TBD, TODO, or "implement later" found. All steps have concrete content.

**Type consistency:** File paths, command names, workflow names, and skill names are consistent across all tasks. `sdlc-security-review` is the same everywhere. `sdlc-worker:latest` is the same image name everywhere. `sdlc-smoke-claude-creds` volume name matches existing smoke test.

**Gaps found:** None — all spec sections covered by at least one task.
