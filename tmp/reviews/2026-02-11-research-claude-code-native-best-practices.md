# Research Synthesis: Claude Code Native Best Practices and Advanced Usage Patterns (2025-2026)

## Research Methodology
- **Date of research**: 2026-02-11
- **Total searches executed**: 14 URL fetches across Anthropic official documentation
- **Total sources evaluated**: 12
- **Sources included (CRAAP score 15+)**: 11
- **Sources excluded (CRAAP score < 15)**: 1 (redirected/404 pages)
- **Target agent archetype**: Domain Expert (Claude Code power usage)
- **Research areas covered**: 10
- **Identified gaps**: 2 (community discussion aggregation, third-party comparison articles)

---

## Executive Summary

Claude Code has evolved from a terminal-based AI coding assistant into a comprehensive agentic development platform. As of early 2026 (version 2.1.39), it operates across terminal, VS Code, JetBrains IDEs, desktop app, web browser, and even Slack. The platform now supports a full extensibility ecosystem: **skills** (reusable domain knowledge and workflows), **subagents** (isolated specialized assistants), **agent teams** (multi-session parallel collaboration), **hooks** (deterministic lifecycle automation), **plugins** (distributable extension packages), and **MCP servers** (external tool integration).

The most impactful findings for an AI-First SDLC framework are:

1. **CLAUDE.md files must be concise and actionable** -- Anthropic explicitly warns that bloated CLAUDE.md files cause Claude to ignore instructions. The current framework's 646-line CLAUDE.md violates this best practice directly.
2. **Skills replace custom slash commands** and should be used for reusable workflows, with full frontmatter configuration for invocation control.
3. **Subagents and agent teams** provide native multi-agent orchestration, potentially replacing the framework's current Task-tool-based agent coordination.
4. **Hooks are deterministic** and should be used for actions that must happen every time (linting, formatting, validation), while CLAUDE.md instructions are advisory.
5. **Memory management** is now automatic -- Claude records learnings across sessions, and CLAUDE.md files support hierarchical loading, modular rules, and imports.
6. **CI/CD integration** is production-ready via GitHub Actions (v1 GA) and GitLab CI/CD, with headless mode (`claude -p`) for scripting.
7. **The plugin ecosystem** enables distributable packages of skills, agents, hooks, and MCP servers.

---

## Area 1: Claude Code Features and Capabilities (2025-2026)

### Key Findings

**1.1 Platform Surface Areas** [Confidence: HIGH]
Claude Code now runs on 7 surfaces, all connecting to the same underlying engine:
- Terminal CLI (primary full-featured interface)
- VS Code extension (inline diffs, @-mentions, plan review)
- JetBrains IDE plugin (IntelliJ, PyCharm, WebStorm)
- Desktop app (standalone, multi-session)
- Web browser (claude.ai/code, no local setup)
- Claude iOS app
- Slack integration (@Claude mentions)

Source: https://docs.anthropic.com/en/docs/claude-code/overview

**1.2 Core Tool Categories** [Confidence: HIGH]
Claude Code's built-in tools fall into four categories:
| Category | Capabilities |
|----------|-------------|
| File operations | Read files, edit code, create new files, rename and reorganize |
| Search | Find files by pattern, search content with regex, explore codebases |
| Execution | Run shell commands, start servers, run tests, use git |
| Web | Search the web, fetch documentation, look up error messages |

Additional capabilities: code intelligence (via LSP plugins), spawning subagents, asking user questions, and other orchestration tasks.

Source: https://docs.anthropic.com/en/docs/claude-code/how-claude-code-works

**1.3 Hooks System** [Confidence: HIGH]
Hooks are user-defined shell commands, LLM prompts, or agent spawns that execute automatically at specific lifecycle points. There are 13 hook events:
- `SessionStart`, `SessionEnd`
- `UserPromptSubmit`
- `PreToolUse`, `PostToolUse`, `PostToolUseFailure`
- `PermissionRequest`
- `Notification`
- `SubagentStart`, `SubagentStop`
- `Stop`
- `TeammateIdle`, `TaskCompleted`
- `PreCompact`

Three hook handler types:
1. **Command hooks** (`type: "command"`): shell scripts receiving JSON on stdin
2. **Prompt hooks** (`type: "prompt"`): single-turn LLM evaluation
3. **Agent hooks** (`type: "agent"`): subagent with tool access for verification

Source: https://docs.anthropic.com/en/docs/claude-code/hooks

**1.4 Skills System** [Confidence: HIGH]
Skills are SKILL.md files in `.claude/skills/` that extend Claude's knowledge. They:
- Follow the Agent Skills open standard
- Support YAML frontmatter for configuration
- Can be invoked manually (`/skill-name`) or automatically by Claude
- Support `$ARGUMENTS` and `$ARGUMENTS[N]` for dynamic input
- Support `context: fork` to run in isolated subagent context
- Support `!command` syntax for dynamic context injection (preprocessing)
- Can restrict tool access via `allowed-tools` field
- Support `disable-model-invocation: true` to prevent automatic loading

Skills and slash commands have been **merged** (v2.1.3) -- `.claude/commands/` files still work but skills are the recommended approach.

Source: https://docs.anthropic.com/en/docs/claude-code/skills

**1.5 Subagents** [Confidence: HIGH]
Subagents are specialized AI assistants running in their own context window. Built-in types:
- **Explore**: Fast (Haiku model), read-only, for codebase search
- **Plan**: Read-only, for planning context gathering
- **General-purpose**: Full tools, inherits main model
- **Bash**: For terminal commands in separate context
- **Claude Code Guide**: Haiku, for answering Claude Code feature questions

Custom subagents are defined in `.claude/agents/` (project) or `~/.claude/agents/` (user) as markdown files with YAML frontmatter. Configuration includes: model selection, tool restrictions, permission modes, preloaded skills, MCP servers, hooks, persistent memory, and max turns.

Source: https://docs.anthropic.com/en/docs/claude-code/subagents

**1.6 Agent Teams (Experimental)** [Confidence: MEDIUM]
Agent teams coordinate multiple Claude Code instances working together. Requires `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`. Features:
- Shared task list with dependency tracking
- Inter-agent messaging (direct and broadcast)
- Team lead coordination
- Delegate mode (lead coordinates only, no direct implementation)
- Display modes: in-process or split-pane (tmux/iTerm2)
- `TeammateIdle` and `TaskCompleted` hooks for quality gates

Source: https://docs.anthropic.com/en/docs/claude-code/agent-teams

**1.7 Plugin Ecosystem** [Confidence: HIGH]
Plugins bundle skills, agents, hooks, MCP servers, and LSP servers into distributable packages:
- Manifest at `.claude-plugin/plugin.json`
- Components at plugin root: `skills/`, `agents/`, `commands/`, `hooks/`
- Namespaced skills: `/plugin-name:skill-name`
- Discoverable via `/plugin` marketplace
- Can be pinned to specific git commit SHAs
- Support LSP servers for code intelligence

Source: https://docs.anthropic.com/en/docs/claude-code/plugins

### Sources
1. [Claude Code Overview](https://docs.anthropic.com/en/docs/claude-code/overview) - CRAAP: 25/25
2. [How Claude Code Works](https://docs.anthropic.com/en/docs/claude-code/how-claude-code-works) - CRAAP: 25/25
3. [Hooks Reference](https://docs.anthropic.com/en/docs/claude-code/hooks) - CRAAP: 25/25
4. [Skills Documentation](https://docs.anthropic.com/en/docs/claude-code/skills) - CRAAP: 25/25
5. [Subagents Documentation](https://docs.anthropic.com/en/docs/claude-code/subagents) - CRAAP: 25/25
6. [Agent Teams](https://docs.anthropic.com/en/docs/claude-code/agent-teams) - CRAAP: 24/25
7. [Plugins Documentation](https://docs.anthropic.com/en/docs/claude-code/plugins) - CRAAP: 25/25

---

## Area 2: CLAUDE.md Best Practices

### Key Findings

**2.1 What to Include in CLAUDE.md** [Confidence: HIGH]
Anthropic's official documentation explicitly states what belongs and what does not:

**Include:**
- Bash commands Claude cannot guess (build, test, lint commands)
- Code style rules that differ from defaults
- Testing instructions and preferred test runners
- Repository etiquette (branch naming, PR conventions)
- Architectural decisions specific to your project
- Developer environment quirks (required env vars)
- Common gotchas or non-obvious behaviors

**Exclude:**
- Anything Claude can figure out by reading code
- Standard language conventions Claude already knows
- Detailed API documentation (link to docs instead)
- Information that changes frequently
- Long explanations or tutorials
- File-by-file descriptions of the codebase
- Self-evident practices like "write clean code"

Source: https://docs.anthropic.com/en/docs/claude-code/best-practices

**2.2 Keep It Concise** [Confidence: HIGH]
Anthropic explicitly warns: **"Bloated CLAUDE.md files cause Claude to ignore your actual instructions!"**

Key guidance:
- For each line, ask: "Would removing this cause Claude to make mistakes?" If not, cut it.
- If Claude keeps doing something wrong despite a rule, the file is probably too long and the rule is getting lost.
- If Claude asks questions answered in CLAUDE.md, the phrasing might be ambiguous.
- Treat CLAUDE.md like code: review it when things go wrong, prune it regularly, test changes by observing behavior.
- You can tune instruction adherence with emphasis (e.g., "IMPORTANT" or "YOU MUST").

Source: https://docs.anthropic.com/en/docs/claude-code/best-practices

**2.3 CLAUDE.md File Hierarchy** [Confidence: HIGH]
CLAUDE.md files load from multiple locations in a hierarchy:
1. `~/.claude/CLAUDE.md` -- applies to all sessions (user-level)
2. `./CLAUDE.md` or `./.claude/CLAUDE.md` -- project root (check into git)
3. `./CLAUDE.local.md` -- personal project preferences (auto-gitignored)
4. Parent directory CLAUDE.md files -- loaded recursively up
5. Child directory CLAUDE.md files -- loaded on demand when working in subdirectories
6. Managed policy CLAUDE.md -- organization-wide (IT/DevOps managed)

More specific instructions take precedence over broader ones.

Source: https://docs.anthropic.com/en/docs/claude-code/memory

**2.4 Modular Rules via .claude/rules/** [Confidence: HIGH]
For larger projects, instructions can be organized into multiple files in `.claude/rules/`:
- Each `.md` file in this directory is loaded as project rules
- Supports path-specific rules, glob patterns, and subdirectories
- User-level rules also supported in `~/.claude/rules/`
- Checked into source control for team sharing

Source: https://docs.anthropic.com/en/docs/claude-code/memory

**2.5 CLAUDE.md Imports** [Confidence: HIGH]
CLAUDE.md files support importing additional files with `@path/to/import` syntax:
```markdown
See @README.md for project overview and @package.json for npm commands.
# Additional Instructions
- Git workflow: @docs/git-instructions.md
- Personal overrides: @~/.claude/my-project-instructions.md
```
- Supports both relative and absolute paths
- Max depth of 5 hops for recursive imports
- First-time imports require user approval
- Not evaluated inside code spans or code blocks

Source: https://docs.anthropic.com/en/docs/claude-code/memory

**2.6 Use /init to Bootstrap** [Confidence: HIGH]
The `/init` command analyzes the codebase to detect build systems, test frameworks, and code patterns, generating a starter CLAUDE.md. This is the recommended way to create a new CLAUDE.md.

Source: https://docs.anthropic.com/en/docs/claude-code/best-practices

### Sources
1. [Best Practices](https://docs.anthropic.com/en/docs/claude-code/best-practices) - CRAAP: 25/25
2. [Memory Management](https://docs.anthropic.com/en/docs/claude-code/memory) - CRAAP: 25/25

---

## Area 3: Agent Capabilities (Task Tool, Subagents, Parallel Execution)

### Key Findings

**3.1 Subagent Delegation Pattern** [Confidence: HIGH]
Claude Code uses subagents to preserve context. The key pattern:
```
Use subagents to investigate how our authentication system handles token refresh,
and whether we have any existing OAuth utilities I should reuse.
```
The subagent explores the codebase in a separate context window and reports back a summary, keeping the main conversation clean.

Source: https://docs.anthropic.com/en/docs/claude-code/best-practices

**3.2 Writer/Reviewer Pattern** [Confidence: HIGH]
A multi-session pattern for quality-focused workflows:
- Session A (Writer): implements the feature
- Session B (Reviewer): reviews the implementation in a fresh context (avoids bias toward code it just wrote)
- Reviewer feedback is applied by the Writer session

Source: https://docs.anthropic.com/en/docs/claude-code/best-practices

**3.3 Fan-Out Pattern** [Confidence: HIGH]
For large-scale migrations or analyses:
1. Have Claude generate a task list (e.g., all files needing migration)
2. Loop through the list calling `claude -p` for each:
```bash
for file in $(cat files.txt); do
  claude -p "Migrate $file from React to Vue. Return OK or FAIL." \
    --allowedTools "Edit,Bash(git commit *)"
done
```
3. Use `--allowedTools` to scope permissions for batch operations

Source: https://docs.anthropic.com/en/docs/claude-code/best-practices

**3.4 Agent Team Coordination** [Confidence: MEDIUM]
Agent teams provide a shared task list with:
- Dependency tracking between tasks
- File-locking-based claim system to prevent race conditions
- Plan approval workflow: teammates plan in read-only mode until lead approves
- Direct inter-teammate messaging
- Quality gates via `TeammateIdle` and `TaskCompleted` hooks

Best use cases: parallel research/review, independent module development, competing debugging hypotheses.

Source: https://docs.anthropic.com/en/docs/claude-code/agent-teams

**3.5 Task Tool Restrictions** [Confidence: HIGH]
Agents can restrict which subagent types they spawn using `Task(agent_type)` syntax:
```yaml
tools: Task(worker, researcher), Read, Bash
```
This is an allowlist -- only named subagent types can be spawned.

Source: https://docs.anthropic.com/en/docs/claude-code/subagents

### Sources
1. [Best Practices](https://docs.anthropic.com/en/docs/claude-code/best-practices) - CRAAP: 25/25
2. [Agent Teams](https://docs.anthropic.com/en/docs/claude-code/agent-teams) - CRAAP: 24/25
3. [Subagents](https://docs.anthropic.com/en/docs/claude-code/subagents) - CRAAP: 25/25

---

## Area 4: MCP (Model Context Protocol) Ecosystem

### Key Findings

**4.1 MCP Server Types** [Confidence: HIGH]
Three transport types supported:
1. **HTTP** (recommended): `claude mcp add --transport http <name> <url>`
2. **SSE** (deprecated): `claude mcp add --transport sse <name> <url>`
3. **stdio** (local processes): `claude mcp add -- <name> -- <command> [args]`

Source: https://docs.anthropic.com/en/docs/claude-code/mcp

**4.2 MCP Installation Scopes** [Confidence: HIGH]
| Scope | Storage | Shared? |
|-------|---------|---------|
| Local (default) | `~/.claude.json` under project path | No |
| Project | `.mcp.json` at project root | Yes (via git) |
| User | `~/.claude.json` | No (all projects) |

Source: https://docs.anthropic.com/en/docs/claude-code/mcp

**4.3 Popular MCP Use Cases** [Confidence: HIGH]
- **Issue tracking**: Implement features from JIRA/GitHub issues
- **Monitoring**: Check Sentry errors, Statsig usage
- **Databases**: Query PostgreSQL, read data
- **Design**: Integrate Figma designs
- **Communication**: Slack, Gmail automation
- **Version control**: GitHub code reviews

Example MCP servers mentioned: Sentry, GitHub, Notion, Asana, Airtable, Stripe, PayPal, HubSpot.

Source: https://docs.anthropic.com/en/docs/claude-code/mcp

**4.4 MCP Tool Search (Auto Mode)** [Confidence: HIGH]
When MCP tool descriptions exceed 10% of the context window, they are automatically deferred and discovered via the `MCPSearch` tool instead of being loaded upfront. This is enabled by default as of v2.1.7. Configurable via `auto:N` syntax where N is the context window percentage threshold.

Source: CHANGELOG (v2.1.7)

**4.5 Environment Variable Expansion in .mcp.json** [Confidence: HIGH]
Project-scoped MCP configs support `${VAR}` and `${VAR:-default}` syntax in:
- `command`, `args`, `env`, `url`, `headers`

This allows team-shared configs with machine-specific paths and secrets.

Source: https://docs.anthropic.com/en/docs/claude-code/mcp

**4.6 Plugin-Provided MCP Servers** [Confidence: HIGH]
Plugins can bundle MCP servers that start automatically when the plugin is enabled. They use `${CLAUDE_PLUGIN_ROOT}` for relative paths.

Source: https://docs.anthropic.com/en/docs/claude-code/mcp

### Sources
1. [MCP Documentation](https://docs.anthropic.com/en/docs/claude-code/mcp) - CRAAP: 25/25
2. [CHANGELOG](https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md) - CRAAP: 24/25

---

## Area 5: CI/CD Integration

### Key Findings

**5.1 GitHub Actions (GA v1.0)** [Confidence: HIGH]
Claude Code GitHub Actions is now generally available at v1.0. Key features:
- `@claude` mentions in PRs and issues trigger automated responses
- Skills can be invoked in CI (e.g., `prompt: "/review"`)
- Custom automation with scheduled prompts
- Supports AWS Bedrock and Google Vertex AI
- Quick setup via `/install-github-app` command

Basic workflow:
```yaml
name: Claude Code
on:
  issue_comment: { types: [created] }
  pull_request_review_comment: { types: [created] }
jobs:
  claude:
    runs-on: ubuntu-latest
    steps:
      - uses: anthropics/claude-code-action@v1
        with:
          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
```

Source: https://docs.anthropic.com/en/docs/claude-code/github-actions

**5.2 Headless Mode for CI** [Confidence: HIGH]
`claude -p "prompt"` runs Claude without an interactive session. Output formats:
- `--output-format text` (default)
- `--output-format json` (structured for scripts)
- `--output-format stream-json` (real-time processing)

Key CI flags:
- `--max-turns N`: limit agentic turns
- `--max-budget-usd N`: cost cap
- `--allowedTools`: scope permissions
- `--dangerously-skip-permissions`: bypass all checks (use only in sandboxed environments)
- `--no-session-persistence`: don't save sessions

Source: https://docs.anthropic.com/en/docs/claude-code/cli-reference

**5.3 Pipe and Script Patterns** [Confidence: HIGH]
```bash
# Monitor logs
tail -f app.log | claude -p "Slack me if you see any anomalies"

# Automate translations
claude -p "translate new strings into French and raise a PR for review"

# Security review
git diff main --name-only | claude -p "review these changed files for security issues"
```

Source: https://docs.anthropic.com/en/docs/claude-code/overview

**5.4 CI Cost Management** [Confidence: HIGH]
- GitHub Actions minutes consumed by runners
- API token costs per interaction
- Optimization: specific @claude commands, `--max-turns`, workflow timeouts, concurrency controls

Source: https://docs.anthropic.com/en/docs/claude-code/github-actions

### Sources
1. [GitHub Actions](https://docs.anthropic.com/en/docs/claude-code/github-actions) - CRAAP: 25/25
2. [CLI Reference](https://docs.anthropic.com/en/docs/claude-code/cli-reference) - CRAAP: 25/25

---

## Area 6: Code Review, Testing, and Documentation

### Key Findings

**6.1 Testing Workflow** [Confidence: HIGH]
Recommended four-step testing workflow:
1. Identify untested code: `find functions not covered by tests`
2. Generate test scaffolding: `add tests for the service`
3. Add meaningful edge cases: `add test cases for edge conditions`
4. Run and verify: `run the new tests and fix any failures`

Claude examines existing test files to match style, frameworks, and assertion patterns.

Source: https://docs.anthropic.com/en/docs/claude-code/common-workflows

**6.2 PR Creation** [Confidence: HIGH]
Two approaches:
1. **Direct**: `create a pr for my changes`
2. **Skill**: `/commit-push-pr` (commits, pushes, opens PR in one step)

Sessions are automatically linked to PRs when created via `gh pr create`. Resume later with `claude --from-pr <number>`.

The `/commit-push-pr` skill auto-posts PR URLs to Slack when MCP Slack is configured.

Source: https://docs.anthropic.com/en/docs/claude-code/common-workflows

**6.3 Code Review via Subagents** [Confidence: HIGH]
Example custom subagent for code review:
```markdown
---
name: security-reviewer
description: Reviews code for security vulnerabilities
tools: Read, Grep, Glob, Bash
model: opus
---
You are a senior security engineer. Review code for:
- Injection vulnerabilities
- Authentication and authorization flaws
- Secrets or credentials in code
- Insecure data handling
```

Source: https://docs.anthropic.com/en/docs/claude-code/best-practices

**6.4 Documentation Workflow** [Confidence: HIGH]
1. Find undocumented code
2. Generate documentation (JSDoc, docstrings, etc.)
3. Review and enhance with context and examples
4. Verify against project standards

Source: https://docs.anthropic.com/en/docs/claude-code/common-workflows

**6.5 Verification as Highest-Leverage Practice** [Confidence: HIGH]
Anthropic states this is "the single highest-leverage thing you can do":
- Include tests, screenshots, or expected outputs
- Use the Chrome extension for UI verification
- Provide a test suite, linter, or Bash command that checks output
- Address root causes, not symptoms

Source: https://docs.anthropic.com/en/docs/claude-code/best-practices

### Sources
1. [Common Workflows](https://docs.anthropic.com/en/docs/claude-code/common-workflows) - CRAAP: 25/25
2. [Best Practices](https://docs.anthropic.com/en/docs/claude-code/best-practices) - CRAAP: 25/25

---

## Area 7: Hooks System Deep Dive

### Key Findings

**7.1 Hook Configuration Locations** [Confidence: HIGH]
| Location | Scope |
|----------|-------|
| `~/.claude/settings.json` | All your projects |
| `.claude/settings.json` | Single project (committable) |
| `.claude/settings.local.json` | Single project (gitignored) |
| Managed policy settings | Organization-wide |
| Plugin `hooks/hooks.json` | When plugin enabled |
| Skill/agent frontmatter | While component active |

Source: https://docs.anthropic.com/en/docs/claude-code/hooks

**7.2 Matcher Patterns** [Confidence: HIGH]
Matchers are regex strings filtering when hooks fire:
- `PreToolUse`, `PostToolUse`: matches tool name (e.g., `Bash`, `Edit|Write`, `mcp__.*`)
- `SessionStart`: matches start type (`startup`, `resume`, `clear`, `compact`)
- `SessionEnd`: matches end reason
- `SubagentStart`/`SubagentStop`: matches agent type

MCP tools follow naming pattern: `mcp__<server>__<tool>`.

Source: https://docs.anthropic.com/en/docs/claude-code/hooks

**7.3 Exit Code Protocol** [Confidence: HIGH]
- **Exit 0**: Success, proceed. JSON output parsed from stdout.
- **Exit 2**: Blocking error. For `PreToolUse`, blocks the tool call. For `UserPromptSubmit`, rejects the prompt. Stderr fed to Claude as error message.
- **Other exit codes**: Non-blocking error. Continues execution.

Source: https://docs.anthropic.com/en/docs/claude-code/hooks

**7.4 Async Hooks** [Confidence: HIGH]
Hooks support `async: true` for background execution without blocking Claude's workflow. Example use case: running tests after file changes without making Claude wait.

Source: https://docs.anthropic.com/en/docs/claude-code/hooks

**7.5 Prompt and Agent Hooks** [Confidence: HIGH]
Beyond shell commands, hooks can:
- **Prompt hooks** (`type: "prompt"`): Send a prompt to a Claude model for yes/no evaluation
- **Agent hooks** (`type: "agent"`): Spawn a subagent with tools (Read, Grep, Glob) for verification

Source: https://docs.anthropic.com/en/docs/claude-code/hooks

**7.6 Common Hook Patterns** [Confidence: HIGH]
- Auto-format after every file edit (PostToolUse on Write|Edit)
- Run lint before a commit
- Block destructive commands (PreToolUse on Bash, check for `rm -rf`)
- Validate MCP write operations
- Security checks before Bash execution
- Quality gates for agent team completion

Source: https://docs.anthropic.com/en/docs/claude-code/hooks

### Sources
1. [Hooks Reference](https://docs.anthropic.com/en/docs/claude-code/hooks) - CRAAP: 25/25

---

## Area 8: Anthropic's Official Recommendations

### Key Findings

**8.1 The #1 Best Practice: Give Claude Verification** [Confidence: HIGH]
"This is the single highest-leverage thing you can do." Without clear success criteria, Claude might produce something that looks right but doesn't work.

Source: https://docs.anthropic.com/en/docs/claude-code/best-practices

**8.2 Explore-Plan-Implement-Commit Workflow** [Confidence: HIGH]
1. **Explore** (Plan Mode): Read files, understand codebase
2. **Plan**: Create detailed implementation plan (Ctrl+G opens in text editor)
3. **Implement** (Normal Mode): Code and verify against plan
4. **Commit**: Descriptive message and PR

Skip planning for trivial changes -- "If you could describe the diff in one sentence, skip the plan."

Source: https://docs.anthropic.com/en/docs/claude-code/best-practices

**8.3 Context Window Management** [Confidence: HIGH]
The most important resource to manage. Key strategies:
- Use `/clear` frequently between unrelated tasks
- Use subagents for investigation (separate context)
- Auto-compaction preserves code and key decisions
- Manual compaction: `/compact <instructions>` (e.g., `/compact Focus on the API changes`)
- Partial compaction: Esc+Esc -> select checkpoint -> "Summarize from here"
- Customize compaction in CLAUDE.md: "When compacting, always preserve the full list of modified files"
- Track context usage via custom status line

Source: https://docs.anthropic.com/en/docs/claude-code/best-practices

**8.4 Common Failure Patterns to Avoid** [Confidence: HIGH]
1. **Kitchen sink session**: Multiple unrelated tasks in one session -> `/clear` between tasks
2. **Correction spiral**: Repeated failures -> `/clear` and write a better prompt
3. **Over-specified CLAUDE.md**: Too long, instructions get lost -> prune ruthlessly
4. **Trust-then-verify gap**: Plausible code without edge cases -> always provide verification
5. **Infinite exploration**: Unscoped "investigate" -> scope narrowly or use subagents

Source: https://docs.anthropic.com/en/docs/claude-code/best-practices

**8.5 Permission Management** [Confidence: HIGH]
- Default mode asks for everything
- Configure `/permissions` to allowlist safe commands
- Use `/sandbox` for OS-level isolation
- `--dangerously-skip-permissions` only in sandboxed environments without internet
- Shift+Tab cycles modes: Default -> Auto-accept edits -> Plan mode -> Delegate mode

Source: https://docs.anthropic.com/en/docs/claude-code/best-practices

**8.6 Extended Thinking** [Confidence: HIGH]
- Enabled by default
- Opus 4.6 uses adaptive reasoning (dynamically allocates based on effort level)
- Effort levels: low, medium, high (default)
- Toggle: Option+T (macOS) / Alt+T (Windows/Linux)
- Phrases like "think", "think hard", "ultrathink" are interpreted as regular prompt instructions

Source: https://docs.anthropic.com/en/docs/claude-code/common-workflows

### Sources
1. [Best Practices](https://docs.anthropic.com/en/docs/claude-code/best-practices) - CRAAP: 25/25
2. [Common Workflows](https://docs.anthropic.com/en/docs/claude-code/common-workflows) - CRAAP: 25/25

---

## Area 9: Memory and Context Management

### Key Findings

**9.1 Auto Memory** [Confidence: HIGH]
Claude automatically records learnings across sessions:
- Stored in `~/.claude/projects/<project>/memory/`
- `MEMORY.md` serves as index (first 200 lines loaded per session)
- Topic files (e.g., `debugging.md`, `api-conventions.md`) loaded on demand
- Records: project patterns, debugging insights, architecture notes, user preferences
- Opt in/out: `CLAUDE_CODE_DISABLE_AUTO_MEMORY=0` (enable) or `=1` (disable)
- Added in v2.1.32

Source: https://docs.anthropic.com/en/docs/claude-code/memory

**9.2 Subagent Memory** [Confidence: HIGH]
Subagents can have persistent memory via the `memory` frontmatter field:
- `user`: shared across all projects
- `project`: specific to current project
- `local`: specific to current project, not shared
- Added in v2.1.33

Source: CHANGELOG (v2.1.33)

**9.3 Context Window Strategies** [Confidence: HIGH]
- CLAUDE.md loaded at session start (always in context)
- Skills load descriptions at start, full content only when invoked
- Subagents run in separate context (key isolation mechanism)
- MCP servers add tool definitions to every request (check with `/mcp`)
- `/context` command shows what's using space
- Auto-compaction triggers when approaching limits

Source: https://docs.anthropic.com/en/docs/claude-code/how-claude-code-works

**9.4 Session Management** [Confidence: HIGH]
- `claude --continue`: resume most recent session
- `claude --resume <name>`: resume by name or picker
- `claude --from-pr <number>`: resume sessions linked to PRs
- `/rename`: give sessions descriptive names
- `--fork-session`: branch off without affecting original
- Sessions persist across terminals and survive restarts
- Checkpoints before every change (rewind with Esc+Esc)

Source: https://docs.anthropic.com/en/docs/claude-code/common-workflows

### Sources
1. [Memory Management](https://docs.anthropic.com/en/docs/claude-code/memory) - CRAAP: 25/25
2. [How Claude Code Works](https://docs.anthropic.com/en/docs/claude-code/how-claude-code-works) - CRAAP: 25/25

---

## Area 10: Recent Changelog Highlights (v2.1.0 - v2.1.39)

### Key Findings

**10.1 Major Feature Additions (2025-2026)** [Confidence: HIGH]
- **v2.1.0**: Skill hot-reload, `context: fork` for skills, `agent` field, language setting
- **v2.1.3**: Slash commands and skills merged, release channel toggle
- **v2.1.6**: Auto-discovery of nested `.claude/skills`, MCP tool search improvements
- **v2.1.7**: MCP tool search auto mode default, wildcard Bash permissions
- **v2.1.9**: `auto:N` for MCP tool search, `PreToolUse` `additionalContext`, `${CLAUDE_SESSION_ID}` substitution
- **v2.1.10**: `Setup` hook event for initialization
- **v2.1.14**: Bash history autocomplete, plugin pinning to git SHAs
- **v2.1.16**: New task management with dependency tracking
- **v2.1.18**: Customizable keyboard shortcuts via `/keybindings`
- **v2.1.19**: Shorthand `$0`, `$1` for skill arguments
- **v2.1.20**: PR review status in prompt footer, CLAUDE.md from `--add-dir`
- **v2.1.27**: `--from-pr` flag, auto-linking sessions to PRs
- **v2.1.30**: PDF page parameter, OAuth for MCP, `/debug` command
- **v2.1.32**: Opus 4.6, agent teams (experimental), auto memory, partial summarization
- **v2.1.33**: `TeammateIdle`/`TaskCompleted` hooks, `Task(agent_type)`, agent `memory` field
- **v2.1.36**: Fast mode for Opus 4.6

Source: https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md

**10.2 Security Fixes** [Confidence: HIGH]
- v2.1.7: Wildcard permission rules matching compound commands with shell operators
- v2.1.6: Permission bypass via shell line continuation
- v2.1.2: Command injection in bash processing
- v2.1.0: Sensitive data in debug logs
- v2.1.38: Heredoc delimiter parsing to prevent command smuggling
- v2.1.38: Blocked writes to `.claude/skills` in sandbox mode

Source: https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md

### Sources
1. [CHANGELOG](https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md) - CRAAP: 24/25

---

## Synthesis

### 1. Core Knowledge Base

- **Claude Code is an agentic coding platform**, not a chatbot. It reads files, runs commands, makes changes, and autonomously works through problems. The agentic loop has three phases: gather context, take action, verify results. [Source: https://docs.anthropic.com/en/docs/claude-code/how-claude-code-works] [Confidence: HIGH]

- **Context window management is the #1 performance factor.** Performance degrades as context fills. Use `/clear` between tasks, subagents for investigation, and compaction for long sessions. [Source: https://docs.anthropic.com/en/docs/claude-code/best-practices] [Confidence: HIGH]

- **CLAUDE.md must be concise.** Only include what Claude cannot infer from code. Bloated files cause Claude to ignore instructions. Test by observing behavior changes. [Source: https://docs.anthropic.com/en/docs/claude-code/best-practices] [Confidence: HIGH]

- **Hooks are deterministic; CLAUDE.md is advisory.** Use hooks for actions that must happen every time (linting, formatting, security checks). Use CLAUDE.md for preferences and conventions. [Source: https://docs.anthropic.com/en/docs/claude-code/best-practices] [Confidence: HIGH]

- **Skills are the primary extension mechanism.** They replace slash commands, support frontmatter configuration, can run in forked contexts, and inject dynamic context. [Source: https://docs.anthropic.com/en/docs/claude-code/skills] [Confidence: HIGH]

- **Subagents preserve context** by running in separate context windows. Built-in types (Explore, Plan, Bash) handle common patterns; custom subagents handle specialized tasks. [Source: https://docs.anthropic.com/en/docs/claude-code/subagents] [Confidence: HIGH]

- **MCP connects Claude to external tools** via an open standard. Three transport types (HTTP recommended, SSE deprecated, stdio for local). Auto-discovery via MCPSearch when tool count is high. [Source: https://docs.anthropic.com/en/docs/claude-code/mcp] [Confidence: HIGH]

- **Claude Code is version 2.1.39** as of this research date, with auto-updates for native installations. The ecosystem includes 65.9k GitHub stars. [Source: CHANGELOG] [Confidence: HIGH]

### 2. Decision Frameworks

- **When to use hooks vs CLAUDE.md instructions**: If the action must happen 100% of the time with no exceptions (linting, formatting, security validation), use a hook. If the action is a preference or guideline that Claude should follow but can reason about, use CLAUDE.md. [Source: https://docs.anthropic.com/en/docs/claude-code/best-practices] [Confidence: HIGH]

- **When to use skills vs subagents vs agent teams**:
  - **Skills**: Domain knowledge or reusable workflows invoked by name or automatically. Run inline or in forked context. Best for: conventions, templates, step-by-step procedures.
  - **Subagents**: Isolated tasks where only the result matters. Run in own context window. Best for: code review, investigation, focused analysis.
  - **Agent teams**: Complex work requiring discussion and collaboration between workers. Multiple independent sessions. Best for: parallel research, competing hypotheses, cross-layer coordination.
  [Source: https://docs.anthropic.com/en/docs/claude-code/agent-teams] [Confidence: HIGH]

- **When to use Plan Mode**: When the feature modifies many files, when you want to explore before changing, or when you want to iterate on direction. Skip for trivial changes. [Source: https://docs.anthropic.com/en/docs/claude-code/best-practices] [Confidence: HIGH]

- **When to `/clear` context**: Between unrelated tasks, after two failed corrections in the same direction, or when Claude seems to forget earlier instructions. [Source: https://docs.anthropic.com/en/docs/claude-code/best-practices] [Confidence: HIGH]

- **When to use `.claude/rules/` vs CLAUDE.md**: Use rules for modular, topic-specific instructions (language guidelines, testing conventions). Use CLAUDE.md for broad project context. Rules can be path-specific and support glob patterns. [Source: https://docs.anthropic.com/en/docs/claude-code/memory] [Confidence: HIGH]

### 3. Anti-Patterns Catalog

- **Bloated CLAUDE.md** (> ~100-200 lines): Instructions get lost in noise. Claude ignores actual rules. -> Keep concise. For each line, ask "Would removing this cause mistakes?" Move domain knowledge to skills. [Source: https://docs.anthropic.com/en/docs/claude-code/best-practices]

- **Kitchen Sink Session**: Multiple unrelated tasks in one conversation. Context fills with irrelevant information. -> Use `/clear` between unrelated tasks. [Source: https://docs.anthropic.com/en/docs/claude-code/best-practices]

- **Correction Spiral**: Correcting Claude repeatedly on the same issue. Context polluted with failed approaches. -> After 2 failed corrections, `/clear` and write a better initial prompt. [Source: https://docs.anthropic.com/en/docs/claude-code/best-practices]

- **Unscoped Investigation**: Asking Claude to "investigate" without bounds. Claude reads hundreds of files, filling context. -> Scope narrowly or use subagents. [Source: https://docs.anthropic.com/en/docs/claude-code/best-practices]

- **Trust-Then-Verify Gap**: Accepting plausible-looking code without verification. Edge cases missed. -> Always provide tests, screenshots, or expected outputs as verification criteria. [Source: https://docs.anthropic.com/en/docs/claude-code/best-practices]

- **Using CLAUDE.md for deterministic rules**: Putting linting/formatting instructions in CLAUDE.md where they can be ignored. -> Use hooks for actions that must happen every time. [Source: https://docs.anthropic.com/en/docs/claude-code/best-practices]

- **Overloading MCP tool context**: Too many MCP servers add tool definitions to every request, consuming context before you start. -> Use `/mcp` to check per-server costs. Enable MCP tool search auto mode. [Source: https://docs.anthropic.com/en/docs/claude-code/how-claude-code-works]

- **Mandating team engagement in CLAUDE.md**: Forcing Claude to use the Task tool for every action adds overhead and consumes context for tasks Claude can handle directly. -> Use subagents for isolation/specialization, not for ceremonial delegation.

### 4. Tool and Technology Map

- **CLI Tool**: `claude` (v2.1.39) -- native install via curl, Homebrew, or WinGet. Auto-updates for native installs.
  - Key flags: `-p` (headless), `-c` (continue), `-r` (resume), `--model`, `--agent`, `--agents` (JSON)
  - Selection criteria: Terminal for full power; VS Code for inline diffs; Web for no-setup tasks

- **Extension Framework**:
  | Type | Location | Purpose |
  |------|----------|---------|
  | Skills | `.claude/skills/` | Reusable workflows and domain knowledge |
  | Subagents | `.claude/agents/` | Isolated specialized assistants |
  | Hooks | `.claude/settings.json` | Deterministic lifecycle automation |
  | Plugins | `.claude-plugin/` | Distributable extension packages |
  | MCP | `.mcp.json` | External tool integration |
  | Rules | `.claude/rules/` | Modular topic-specific instructions |

- **Models Available**:
  - Claude Opus 4.6 (latest, strongest reasoning, adaptive thinking)
  - Claude Sonnet 4.5 (balanced, default for GitHub Actions)
  - Claude Haiku (fast, used by Explore subagent)
  - Fast mode available for Opus 4.6

- **GitHub Actions**: `anthropics/claude-code-action@v1` -- GA release, supports Bedrock and Vertex AI

### 5. Interaction Scripts

- **Trigger**: "Set up Claude Code for a new project"
  **Response pattern**: Run `/init` to generate starter CLAUDE.md. Configure hooks for linting/formatting. Add project-specific skills. Set up MCP servers for external tools.
  **Key questions**: What build/test commands does the project use? What code style conventions exist? What external tools need integration?

- **Trigger**: "Make Claude Code follow our coding standards"
  **Response pattern**: Write concise CLAUDE.md with only rules Claude cannot infer. Use `.claude/rules/` for modular topic-specific rules. Set up PostToolUse hooks on Write|Edit for auto-formatting. Consider using skills for reusable patterns.
  **Key questions**: Which standards does Claude already follow by default? Which need explicit instruction? Which need deterministic enforcement (hooks)?

- **Trigger**: "Run code review with Claude Code"
  **Response pattern**: Create a security-reviewer subagent with read-only tools and Opus model. Use the Writer/Reviewer pattern with separate sessions. In CI, use GitHub Actions with `/review` skill.
  **Key questions**: What review criteria matter most? Should review be interactive or automated? Is this for PRs or ad-hoc review?

- **Trigger**: "Integrate Claude Code into CI/CD"
  **Response pattern**: Install `anthropics/claude-code-action@v1` for GitHub Actions. Use `claude -p` for headless automation. Set `--max-turns` and `--max-budget-usd` for cost control. Use `--allowedTools` for security.
  **Key questions**: GitHub Actions or GitLab CI? Direct API or Bedrock/Vertex? What automated tasks needed? Budget constraints?

- **Trigger**: "Context window is getting full / Claude is forgetting things"
  **Response pattern**: Use `/clear` between unrelated tasks. Put persistent rules in CLAUDE.md, not conversation. Use subagents for investigation. Run `/compact <focus>` to manually summarize. Check `/context` for space usage. Add compaction instructions to CLAUDE.md.
  **Key questions**: Are tasks unrelated (need clear)? Is investigation filling context (need subagents)? Are instructions being lost (need CLAUDE.md)?

- **Trigger**: "Make CLAUDE.md more effective"
  **Response pattern**: Audit current CLAUDE.md -- remove anything Claude does correctly without the instruction. Move domain knowledge to skills. Move deterministic rules to hooks. Use `.claude/rules/` for modular organization. Use `@imports` for referenced docs. Test by observing Claude's behavior.
  **Key questions**: How long is the current CLAUDE.md? Which instructions does Claude ignore? Which are redundant?

---

## Identified Gaps

1. **Community discussion aggregation**: Unable to systematically search Reddit, Hacker News, Discord, or Twitter/X discussions about Claude Code tips. WebSearch was unavailable in this environment. The official documentation was the primary source.
   - Queries attempted: N/A (tool unavailable)
   - Mitigation: Official docs provide comprehensive best practices from Anthropic's own engineering teams.

2. **Comparison articles with alternatives**: Unable to search for comparison articles between Claude Code and alternatives (Cursor, GitHub Copilot Workspace, Windsurf, etc.).
   - Queries attempted: N/A (tool unavailable)
   - Mitigation: Official docs focus on Claude Code's own capabilities which is sufficient for framework improvement.

---

## Cross-References

- **CLAUDE.md conciseness** (Area 2) directly contradicts the **current framework's 646-line CLAUDE.md** (noted in the repo's own CLAUDE.md deprecation notice). The framework should follow Anthropic's guidance and drastically reduce CLAUDE.md size.

- **Skills** (Area 1) can replace the framework's current **Task-tool-based agent coordination pattern**. Instead of forcing Claude to engage agents via Task for every action, domain knowledge should be packaged as skills that Claude loads automatically when relevant.

- **Hooks** (Area 7) should replace CLAUDE.md instructions that mandate specific actions. The framework's validation requirements (linting, formatting, type checking) are perfect candidates for PostToolUse hooks on Write|Edit, rather than advisory CLAUDE.md instructions.

- **Auto memory** (Area 9) overlaps with the framework's context-manager.py tool. Claude Code now handles session persistence and learning natively.

- **Subagents** (Area 3) and the framework's "63 expert agents" concept need reconciliation. Native subagents with proper tool restrictions and model selection may be more effective than the current approach of invoking agents via Task tool prompts.

- **Plugin ecosystem** (Area 1) provides a distribution mechanism for the framework's agents, skills, and hooks. The entire AI-First SDLC framework could potentially be packaged as a Claude Code plugin.

---

## Recommendations for Improving an AI-First SDLC Framework

### Critical (High Impact, Immediate)

1. **Drastically reduce CLAUDE.md to under 100 lines.** The current 646-line file is explicitly against Anthropic's best practices. Move domain knowledge to `.claude/skills/`, move modular rules to `.claude/rules/`, and keep only what Claude cannot infer. This is the single most impactful change.

2. **Convert mandatory actions to hooks.** Linting, formatting, validation, and pre-commit checks should be PostToolUse and PreToolUse hooks, not CLAUDE.md instructions. Hooks are deterministic; CLAUDE.md instructions are advisory.

3. **Package expert agents as native subagents.** Define them in `.claude/agents/` with proper YAML frontmatter: model selection, tool restrictions, permission modes, and preloaded skills. This replaces the current ad-hoc Task tool invocation pattern.

### Important (High Impact, Near-Term)

4. **Convert reusable workflows to skills.** Patterns like code review, PR creation, feature proposals, and retrospective writing should be `.claude/skills/` with proper frontmatter. Use `disable-model-invocation: true` for workflows with side effects.

5. **Use `.claude/rules/` for modular instructions.** Break the monolithic CLAUDE.md into topic-specific rule files: `git-workflow.md`, `code-style.md`, `testing.md`, `documentation.md`.

6. **Set up MCP servers for external tool integration.** GitHub CLI (`gh`) is already recommended by Anthropic. Add project-scoped `.mcp.json` for any Jira, Slack, or other integrations the team uses.

7. **Configure auto-memory.** Enable `CLAUDE_CODE_DISABLE_AUTO_MEMORY=0` and let Claude build up project knowledge naturally across sessions. This replaces the need for manual context-manager.py.

### Valuable (Medium Impact, Ongoing)

8. **Adopt the Explore-Plan-Implement-Commit workflow.** Align the framework's feature development process with Anthropic's recommended four-phase workflow, using Plan Mode for complex changes.

9. **Implement the Writer/Reviewer pattern.** For code quality, use separate sessions or subagents: one to implement, one to review in a fresh context.

10. **Consider packaging the framework as a Claude Code plugin.** The plugin ecosystem supports skills, agents, hooks, and MCP servers in a single distributable package. This would simplify adoption.

11. **Stop mandating Task tool usage for every action.** The "MANDATORY TEAM-FIRST ENFORCEMENT" approach in the current CLAUDE.md adds overhead and consumes context. Instead, define subagents that Claude delegates to when appropriate, and let Claude's native judgment decide when delegation adds value.

---

## Sources with URLs

1. **Claude Code Overview** - https://docs.anthropic.com/en/docs/claude-code/overview
2. **Best Practices for Claude Code** - https://docs.anthropic.com/en/docs/claude-code/best-practices
3. **How Claude Code Works** - https://docs.anthropic.com/en/docs/claude-code/how-claude-code-works
4. **Common Workflows** - https://docs.anthropic.com/en/docs/claude-code/common-workflows
5. **Hooks Reference** - https://docs.anthropic.com/en/docs/claude-code/hooks
6. **Extend Claude with Skills** - https://docs.anthropic.com/en/docs/claude-code/skills
7. **Create Custom Subagents** - https://docs.anthropic.com/en/docs/claude-code/subagents
8. **Run Agent Teams** - https://docs.anthropic.com/en/docs/claude-code/agent-teams
9. **Connect Claude Code to Tools via MCP** - https://docs.anthropic.com/en/docs/claude-code/mcp
10. **Claude Code GitHub Actions** - https://docs.anthropic.com/en/docs/claude-code/github-actions
11. **Memory Management** - https://docs.anthropic.com/en/docs/claude-code/memory
12. **CLI Reference** - https://docs.anthropic.com/en/docs/claude-code/cli-reference
13. **Create Plugins** - https://docs.anthropic.com/en/docs/claude-code/plugins
14. **CHANGELOG** - https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md
