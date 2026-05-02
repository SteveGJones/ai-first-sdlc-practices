---
name: setup-team
description: Configure SDLC team formation and SDLC method for this project. Asks the four-option SDLC method question (solo / single-team / programme / assured), then recommends and installs team plugins based on project type, language, tech stack, and support needs.
disable-model-invocation: false
---

# SDLC Team Setup

Configure the right agent team for this project by selecting an SDLC method, a project type, and installing the matching team plugins.

## Steps

0. **Pre-check: inventory what's already installed**

   Before making any recommendations, check what plugins, agents, and skills are already available — both globally and for this project.

   **0a. Check installed plugins:**
   - Read `~/.claude/settings.json` → `enabledPlugins` field (global installs)
   - Read `.claude/settings.json` (project-level) → `enabledPlugins` field (if it exists)
   - Merge both lists. For each `sdlc-*@ai-first-sdlc` entry: record as installed.
   - Also check for `sdlc-knowledge-base@ai-first-sdlc`, `sdlc-programme@ai-first-sdlc`, and `sdlc-assured@ai-first-sdlc` specifically — these may be relevant to the SDLC method question in step 3.

   **0b. Check available agents:**
   - Glob `.claude/agents/**/*.md` (project-level agents)
   - Note which come from installed plugins vs which are project-local

   **0c. Check available skills:**
   - List currently registered skills (the set Claude Code can see)

   **0d. Present the pre-check results** to the user before any recommendations:

   ```
   Current state:

   Installed SDLC plugins:
     ✓ sdlc-core@ai-first-sdlc (global)
     ✓ sdlc-team-common@ai-first-sdlc (global)
     ✗ sdlc-team-fullstack@ai-first-sdlc
     ✗ sdlc-lang-python@ai-first-sdlc
     ✗ sdlc-knowledge-base@ai-first-sdlc
     ✗ sdlc-programme@ai-first-sdlc
     ✗ sdlc-assured@ai-first-sdlc

   Available agents: N (from installed plugins)
   Available skills: M

   I'll only recommend what you don't already have.
   ```

   **0e. Record the pre-check state** for use in later steps — the recommendation output (step 8) will mark already-installed plugins with `✓ (already installed)` instead of install commands, and the install command list (step 9) will exclude them.

1. **Check current team configuration**

Look for `.sdlc/team-config.json` in the project root (or `.claude/team-config.json` as a fallback). If it exists, display the current formation **and the recorded `sdlc_method`** (if present) and ask if the user wants to reconfigure.

2. **Ask the user what kind of project this is** (present as multiple choice):

   - **A. Full-stack web application** — frontend + backend + API + DevOps
   - **B. AI/ML system** — AI architects + prompt engineers + RAG designers
   - **C. Cloud infrastructure** — cloud + containers + SRE + observability
   - **D. API/microservices** — API + backend + integration + performance
   - **E. Security-focused** — security + compliance + privacy
   - **F. Custom** — pick individual team plugins

3. **Ask about SDLC method (delivery structure)**

   The framework supports **four SDLC delivery structures**. This question is **orthogonal** to step 2 — step 2 picks team plugins (what kind of system); step 3 picks the SDLC method bundle (what kind of delivery discipline). A regulated medical-device system could be cloud-infrastructure (project type C) AND assured (SDLC method D); an AI/ML prototype could be project type B AND solo (SDLC method B).

   Present as multiple choice:

   - **A. Single-team (default)** — 3–10 contributors, organic delivery, no formal phase gates. Use the base SDLC (`/sdlc-core:new-feature` workflow) with team plugins from step 2. Most projects pick this.
   - **B. Solo** — 1–2 contributors, fast iteration, lightweight constitution overlay. Use the base SDLC with `/sdlc-core:commission --option solo`.
   - **C. Programme (Method 1)** — 11–50 contributors across 2–5 teams, formal phase gates (requirements → design → test → code) with mandatory cross-phase review. Adds the `sdlc-programme` bundle.
   - **D. Assured (Method 2)** — regulated industries (DO-178C, IEC 62304, ISO 26262, FDA 21 CFR Part 820). Bidirectional traceability, positional namespace IDs, DDD decomposition, typed evidence statuses, standard-specific exports. Adds the `sdlc-assured` bundle (v0.2.0 audit-ready at the tooling layer).
   - **E. Decide later** — proceed with single-team default; user can run `/sdlc-core:commission` at any time to switch.

   Default to **A** if the user presses Enter without selecting.

   **Map the answer:**

   | Selection | `sdlc_method` value | Bundle plugin to recommend | Post-install commission command |
   |-----------|---------------------|---------------------------|--------------------------------|
   | A. Single-team | `single-team` | (none — sdlc-core is sufficient) | (none — default behaviour) |
   | B. Solo | `solo` | (none — sdlc-core is sufficient) | `/sdlc-core:commission --option solo` |
   | C. Programme | `programme` | `sdlc-programme@ai-first-sdlc` | `/sdlc-core:commission --option programme --level production` (or `/sdlc-programme:commission-programme`) |
   | D. Assured | `assured` | `sdlc-assured@ai-first-sdlc` | `/sdlc-core:commission --option assured --level production` (or `/sdlc-assured:commission-assured`) |
   | E. Decide later | `undecided` | (none — defer) | (none — user runs `/sdlc-core:commission` later) |

   **What to record:**

   - Add `sdlc_method` to the team-config.json fields written in step 11 (e.g., `"sdlc_method": "assured"`).
   - For C / D: add the bundle plugin to the install recommendation list shown in step 8. If the bundle appears in the pre-check (step 0) list as already installed, mark it `✓ (already installed)` and skip re-recommending — but **do** surface the post-install commission command in the recommendation output, since commissioning is a separate step from plugin install.
   - For B / C / D: add a **"Post-install action"** line in the step 8 recommendation output advising the user to run the appropriate `/sdlc-core:commission` command after the plugin is installed (or, for B, even if no extra plugin is installed). Without this surfacing, the bundle would ship installed but uncommissioned, and the user would get validation errors with no clear diagnosis path.
   - For E: record `"sdlc_method": "undecided"` so the post-check (step 13) can surface a one-line reminder that commissioning is still pending.

   **If unsure, point to `docs/METHODS-GUIDE.md`** for a fuller decision tree, comparison table, trade-offs, and migration notes between methods.

4. **Map step 2 selection to recommended team plugins:**

   | Selection | Plugins |
   |-----------|---------|
   | A. Full-stack | `sdlc-team-common`, `sdlc-team-fullstack` |
   | B. AI/ML | `sdlc-team-common`, `sdlc-team-ai`, `sdlc-lang-python` |
   | C. Cloud | `sdlc-team-common`, `sdlc-team-cloud` |
   | D. API | `sdlc-team-common`, `sdlc-team-fullstack`, `sdlc-team-cloud` |
   | E. Security | `sdlc-team-common`, `sdlc-team-security` |
   | F. Custom | `sdlc-team-common` (pre-selected) + user picks additional team plugins |

   **`sdlc-team-common` is a near-universal default.** It contains the research-and-agent-creation pipeline (`pipeline-orchestrator`, `deep-research-agent`, `agent-builder`, `repo-knowledge-distiller`) plus cross-cutting specialists (`solution-architect`, `database-architect`, `performance-engineer`, `observability-specialist`). Every project type above includes it because:

   - Discovery during setup relies on `pipeline-orchestrator` for the research → synthesis → agent-builder workflow
   - Any Section C coverage gap identified during discovery requires these agents to act on
   - Cross-cutting architecture decisions benefit from `solution-architect` regardless of project type

   For option F (Custom), `sdlc-team-common` is pre-selected. If the user wants to deselect it, present this warning:

   > ⚠️ You are deselecting `sdlc-team-common`. This plugin provides the agents required for custom agent creation (`pipeline-orchestrator`, `deep-research-agent`, `agent-builder`). Without it:
   > - You cannot act on Section C coverage gaps from discovery
   > - You cannot use `@pipeline-orchestrator create a <topic> agent`
   > - Research-driven architecture decisions have no dedicated research agent
   >
   > Only deselect if you have a specific reason (e.g., the project will never create custom agents, or you have equivalent tooling elsewhere). Continue with deselection? [y/N]

   Default to "N". Users who confirm deselection get a note in the configuration so the decision is traceable.

5. **Auto-detect language** by scanning file extensions in the project:
   - `.py` files dominant → recommend `sdlc-lang-python`
   - `.js`/`.ts` files dominant → recommend `sdlc-lang-javascript`
   - `.go` files dominant → recommend `sdlc-lang-go` (if available in marketplace; otherwise note "Go detected but no `sdlc-lang-go` plugin is currently available")
   - `.java` files dominant → recommend `sdlc-lang-java` (if available; otherwise note same)
   - `.rs` files dominant → recommend `sdlc-lang-rust` (if available; otherwise note same)
   - `.rb` files dominant → note "Ruby detected but no `sdlc-lang-ruby` plugin is currently available"
   - Multiple languages detected → recommend all matching language plugins; note the dominant one

   Check the pre-check state from step 0: if a language plugin is already installed, mark it `✓ (already installed)` instead of recommending it again.

6. **Scan tech stack and discover 1st-party tools**

   **6a. Scan project files for technologies (registry-driven):**

   **6a.1 Load the technology registry index.** Find and read `_index.yaml` from the technology registry. Search in order:
   1. `data/technology-registry/_index.yaml` (repo root — for framework developers)
   2. Glob for `**/sdlc-core/data/technology-registry/_index.yaml` (plugin install — for plugin consumers)

   This file contains:
   - `detection` — maps package names, Docker images, and env vars to technology keys, organized by ecosystem (`pip`, `npm`, `docker`, `env`, `go`, `gem`, `cargo`)
   - `aliases` — normalizes informal names to canonical keys
   - `technologies` — manifest of available technology files

   If the registry index doesn't exist or fails to load, fall back to web-search-only discovery (the pre-registry behavior in step 6c).

   **6a.2 Scan project dependency files.** Check the following files. If a file doesn't exist, skip it.

   | File | Ecosystem | What to extract |
   |------|-----------|----------------|
   | `requirements.txt` / `pyproject.toml` | `pip` | Python package names |
   | `package.json` | `npm` | `dependencies` + `devDependencies` keys |
   | `Gemfile` | `gem` | Ruby gem names |
   | `go.mod` | `go` | Go module paths |
   | `Cargo.toml` | `cargo` | Crate names from `[dependencies]` |
   | `docker-compose.yml` | `docker` | Service image names (match with glob patterns like `postgres:*`) |
   | `.env` / `.env.example` | `env` | Variable names and values (match with patterns like `DATABASE_URL=postgres*`) |
   | `README.md` / `CLAUDE.md` | — | Technology name mentions (match against `technologies` manifest display names and keys) |

   **6a.3 Match packages to technologies.** For each package/image/var found in a dependency file:
   1. Look up the package name in `detection[ecosystem]` from the registry index
   2. If found → add the mapped technology key to the detected set
   3. If not found → the package is not in the registry (no action; it won't block anything)

   For `README.md`/`CLAUDE.md`: scan for technology names mentioned in prose. Match against both the `technologies` manifest keys (e.g., `mongodb`) and display names (e.g., `MongoDB`). Also check `aliases` for informal mentions.

   **6a.4 Normalize via aliases.** For any technology detected by name (from README/CLAUDE.md or user input in step 6b), normalize through the `aliases` map before looking up the registry. E.g., user says "postgres" → aliases normalize to `postgresql` → look up `postgresql` in the manifest.

   **6b. Present findings and ask the user:**

   If technologies were detected:
   ```
   I detected the following technologies in your project:
   - PostgreSQL (from requirements.txt: psycopg2-binary)
   - Redis (from docker-compose.yml: redis:7)
   - AWS (from requirements.txt: boto3)

   Any other technologies I should search for? (e.g., Stripe, Twilio, Elasticsearch)
   Or press Enter to continue with these.
   ```

   If the project is empty or no dependency files found:
   ```
   No dependency files found yet (new project).
   What technologies will this project use? (e.g., PostgreSQL, MongoDB, Redis, AWS, Stripe)
   Or press Enter to skip technology discovery.
   ```

   **6c. Discover tools for each technology (registry-first, web-search fallback):**

   For each technology (detected + user-specified):

   **6c.1 Check the registry first.** Look up the technology key in the `technologies` manifest from `_index.yaml`:

   - **If the technology has a registry file**: Read `{file}` from the same directory where `_index.yaml` was found (step 6a.1). Extract `section_a`, `section_b`, `section_c`, `our_agents`, and `trusted_sources` directly. This is the fast path — no web search needed.

   - **If the technology is NOT in the registry**: Fall back to web search discovery (step 6c.2 below). This ensures technologies not yet in the registry are still discoverable.

   **6c.2 Web search fallback (only for technologies not in the registry).** Search for official vendor tooling using these sources:

   - MCP server registries: WebSearch `"{technology} mcp server" site:npmjs.com` and `site:pypi.org`
   - Vendor GitHub org: WebSearch `"github.com/{vendor}" mcp OR agent OR skills OR claude`
   - Claude plugin marketplace: WebSearch `"{technology} claude code plugin"`
   - GitHub Actions marketplace: WebSearch `"{technology} github action" site:github.com/marketplace`
   - Targeted web search: `"{technology} official mcp server"`, `"{technology} agent skills"`

   For each tool found, record: name, **category** (one of `claude-plugin` / `mcp-server-npm` / `mcp-server-pip` / `mcp-server-binary` / `github-action` / `standalone-cli` / `library-framework`), **section** (A or B), source URL, brief capabilities description, and whether it appears actively maintained (last commit/publish within 6 months).

   **Section classification rules** (apply to both registry entries and web search results):
   - `claude-plugin` → **Section A**
   - `mcp-server-npm` / `mcp-server-pip` / `mcp-server-binary` → **Section A**
   - `github-action` / `standalone-cli` → **Section A**
   - `library-framework` → **Section B**

   **6c.3 Generate install instructions per tool.** For registry entries: if the entry has an `install_override` field, emit it verbatim. Otherwise, generate the install snippet from the entry's `type` and structured fields using these templates:

   - **`claude-plugin`**: Use the `install_override` (registry entries for plugins always have one since marketplace info varies).
   - **`mcp-server-npm`** — generate from `package` and `env` fields:
     ```json
     { "mcpServers": { "<name>": { "command": "npx", "args": ["-y", "<package>"], "env": { "<env.name>": "<env.example or description>" } } } }
     ```
     Then restart Claude Code or run `/mcp`.
   - **`mcp-server-pip`** — generate from `package`, `module` (if present), and `env` fields:
     ```json
     { "mcpServers": { "<name>": { "command": "python", "args": ["-m", "<module>"], "env": { "<env.name>": "<env.example or description>" } } } }
     ```
     Or use `install_override` if the entry specifies `uvx` or another install method.
   - **`mcp-server-binary`** — use `install_override` (binary installs vary too much to template).
   - **`github-action`** — generate from `source`:
     ```yaml
     - name: <description>
       uses: <owner>/<repo>@<version-tag>
     ```
   - **`standalone-cli`** — generate from `source` and `name`:
     ```bash
     git clone <source> ~/tools/<name>
     ```
   - **`library-framework`** (Section B) — generate from `package` and `ecosystem`:
     ```bash
     <pip|npm|cargo add|go get> install <package>
     ```

   For web search results (not from registry): use the same templates but derive fields from the search results. If you cannot determine the install path with confidence, write: `Manual setup required. See <url>/README.md.`

   **6c.4 Include framework cross-references.** If the registry entry has an `our_agents` field, include the cross-referenced agents in the recommendation output. Each entry has `agent`, `plugin`, and `relevance` — show the relevance to the user and ensure the `plugin` is included in the plugin recommendation (step 8).

   **6d. If no technologies detected and user skipped:** Skip this step entirely and proceed to step 7.

   **6e. Escalate `sdlc-team-common` to required if Section C gaps exist.**

   After discovery completes, count the Section C gaps identified. If the count is greater than zero:

   - Mark `sdlc-team-common` as **required** (not merely recommended) in the plugin selection
   - If the user selected project type F (Custom) and explicitly deselected team-common earlier in step 4, block progression with this message:

     > ⚠️ Cannot proceed. Discovery identified **{N} Section C coverage gap(s)** that require custom agent creation, but you deselected `sdlc-team-common`. This plugin provides the agents that execute the research → synthesis → agent-builder pipeline. Without it, you cannot act on any Section C recommendation.
     >
     > Options:
     > 1. **Include `sdlc-team-common`** in your plugin selection (recommended)
     > 2. **Remove the Section C gaps** if you genuinely don't want to create custom agents (unusual — the gaps were identified because your tech stack has no pre-built tools that cover them)
     > 3. **Abort setup** and reconsider your tooling strategy
     >
     > Which option? [1/2/3]

   - When team-common is required by Section C gaps, record `required_by: "section-c-gaps"` in the final `.sdlc/team-config.json` so the dependency is traceable
   - If team-common was already in the user's selection, no block is needed — just note in the final summary that team-common is required (not merely recommended) because of the Section C gaps

7. **Ask about project support needs:**
   - "Do you need project management support (sprints, delivery tracking)?" → recommend `sdlc-team-pm`
   - "Do you need documentation architecture?" → recommend `sdlc-team-docs`
   - "Do you need evidence-grounded decisions? (research library, citable findings, knowledge base for the project)" → recommend `sdlc-knowledge-base`
     - Brief description: "Provides a research-librarian agent that queries a structured knowledge base with citations, an agent-knowledge-updater for ingesting new sources, and skills for ingest/query/lint/index management. Particularly valuable for projects making architectural, transformation, or measurement decisions that benefit from citable evidence."
     - When NOT to recommend: projects that are throwaway prototypes, routine maintenance, or where decisions don't need citation

   For each of these, check the pre-check state from step 0: if already installed, mark `✓ (already installed)` and don't ask the question.

8. **Present the recommendation** to the user in the following sections:

   ```
   Recommended setup for your project:

   === SDLC Method ===
   <recorded sdlc_method from step 3, e.g.:>
     Method: Assured (Method 2) — regulated industries
     Bundle: sdlc-assured@ai-first-sdlc (v0.2.0 audit-ready at the tooling layer)
     Post-install action: run `/sdlc-core:commission --option assured --level production`
       (or `/sdlc-assured:commission-assured`) AFTER the bundle plugin installs.
       This scaffolds programmes.yaml, visibility-rules.md, and base specification
       templates. Without this, the bundle ships installed but uncommissioned.

   <or, for single-team:>
     Method: Single-team (default — no extra bundle needed)
     Post-install action: (none — proceed with /sdlc-core:new-feature workflow)

   <or, for undecided:>
     Method: Undecided — defer commissioning
     Post-install action: when ready, run `/sdlc-core:commission` to choose between
       solo / single-team / programme / assured. See docs/METHODS-GUIDE.md for the
       decision tree.

   === SDLC Framework ===
   These provide the development methodology — rules, validation, specialist agents.

   ✓ sdlc-core — rules, validation, enforcement (always installed)
     → sdlc-enforcer, critical-goal-reviewer, code-review-specialist, verification-enforcer

   ★ sdlc-team-common — research + agent creation pipeline, cross-cutting specialists
     → pipeline-orchestrator, deep-research-agent, agent-builder, repo-knowledge-distiller, solution-architect, database-architect, performance-engineer, observability-specialist
     [Required if Section C has any gaps, else strongly recommended]
     [Marker ★ = universal default; ✓ = always installed; ○ = optional/selected]

   ○ <other team plugins from step 4>
   ○ <language plugin from step 5>
   ○ <SDLC method bundle from step 3, if programme or assured>

   === Section A: Claude Code Environment Tools ===
   Install these INTO Claude Code to extend its capabilities. Each has ready-to-run installation instructions.

   ○ <tool name> — <capabilities>
     Source: <url>
     Category: <claude-plugin/mcp-server-npm/mcp-server-pip/mcp-server-binary/github-action/standalone-cli>
     Maintained: <Yes/No>
     Install (MANDATORY — never omit):
       <category-appropriate install snippet from step 6c.1>

   ○ <tool name> — <capabilities>
     ...

   (If no Section A tools were found:)
   _No Claude Code environment tools found for your tech stack._

   === Section B: Project Dependencies ===
   These are libraries for your OWN project's source code if you're building something (custom MCP server, custom agent, app calling Claude). They are NOT installed in Claude Code.

   ○ <library name> — <what it helps you build>
     Source: <url>
     Category: library-framework
     Install (in your project, not Claude Code):
       <package-manager> install <package-name>
     Usage: <import statement>
     Docs: <docs-url>

   ○ <library name> — ...

   (If no Section B libraries were found:)
   _No project dependencies found for your tech stack._

   === Section C: Gaps Worth Custom Agents ===
   Topics where no pre-built Claude Code tool exists AND no library alone substitutes for expertise. For each gap, you can commission research + custom agent creation via the pipeline-orchestrator agent (deep-research-agent → synthesis → agent-builder). This skill surfaces the gaps; actual agent creation is invoked separately via `@pipeline-orchestrator`.

   **Prerequisite**: the `Create` commands below require `sdlc-team-common@ai-first-sdlc` installed. This plugin provides the agents that execute the research → synthesis → agent-builder pipeline (`pipeline-orchestrator`, `deep-research-agent`, `agent-builder`). If `sdlc-team-common` is not already in your selected plugins, it becomes **required** (not just recommended) when Section C has any entries — see the escalation logic below.

   ○ Gap: <topic>
     Why a custom agent: <what's missing that a custom agent would provide>
     What the agent would know: <1-2 sentence description>
     Research scope: <topics the research campaign would cover>
     Estimated pipeline duration: 2-3 hours (web research + synthesis + construction)
     Create (when you want it): @pipeline-orchestrator create a <topic-slug> agent

   ○ Gap: <topic>
     ...

   (If no Section C gaps were identified:)
   _No coverage gaps identified for your tech stack — existing Section A / Section B tooling covers your needs._

   (If neither A, B, nor C has entries:)
   No official vendor tooling, libraries, or custom agent candidates found for your tech stack.
   You can search later using the pipeline-orchestrator's discovery phase.

   === Project Support (optional) ===
   ○ sdlc-team-pm — sprint planning, delivery tracking, retrospectives
   ○ sdlc-team-docs — technical writing, documentation architecture
   ○ sdlc-knowledge-base — research library, evidence-grounded decisions, citable findings

   [For each item: show ✓ (already installed) from pre-check if applicable, instead of ○]

   Install all? [Y/n/customize]
   ```

   If the user chooses "customize", allow them to select/deselect individual items from all sections (including the SDLC method bundle, if any).

   **Pre-check awareness**: in the SDLC Framework, SDLC Method, and Project Support sections, mark plugins from step 0's pre-check as `✓ (already installed)` and exclude them from the install command list in step 9. Only plugins NOT already installed get `○` markers and install commands. If everything recommended is already installed (including the SDLC method bundle), say so: "All recommended plugins are already installed. No new installs needed." — but still surface the post-install commission command for B / C / D, since the user may not yet have run it even if the plugin is installed.

9. **If confirmed, install the plugins.** Tell the user to run:

   ```
   /plugin install <plugin-name>@ai-first-sdlc
   ```

   for each recommended plugin. Note: skill cannot programmatically install plugins — it provides the commands for the user to run.

   **For SDLC method B / C / D**, after the install commands, also surface the **post-install commission command**:

   ```
   Post-install (run after the plugins above install):
     /sdlc-core:commission --option <method> --level production
   ```

   (Or the bundle-side equivalent: `/sdlc-programme:commission-programme` / `/sdlc-assured:commission-assured` / `/sdlc-core:commission --option solo`.)

10. **Write the plugin library** at `.sdlc/recommended-plugins.json`

   If the file doesn't exist, create it. If it exists, read it and append new entries (dedup on `name` — don't add tools already in the list).

   ```json
   {
     "version": "1.0",
     "last_updated": "<YYYY-MM-DD>",
     "plugins": [
       {
         "name": "sdlc-core",
         "source": "ai-first-sdlc",
         "type": "sdlc-framework",
         "installed": true,
         "added_by": "setup-team",
         "added_at": "<YYYY-MM-DD>"
       },
       {
         "name": "<discovered-tool-name>",
         "source": "<url>",
         "type": "<mcp-server/agent-skills/plugin/action>",
         "installed": "<true/false>",
         "added_by": "setup-team",
         "added_at": "<YYYY-MM-DD>",
         "note": "<optional context>"
       }
     ]
   }
   ```

   Include:
   - All SDLC framework plugins the user chose to install (type: `sdlc-framework`)
   - The SDLC method bundle plugin from step 3 (type: `sdlc-method-bundle`) if `sdlc_method` is `programme` or `assured`
   - All technology-specific tools from step 6c discovery (type: `mcp-server`, `agent-skills`, etc.) with `installed: true/false` based on the user's choice
   - Do NOT duplicate entries that already exist (match on `name`)
   - Update `last_updated` to today's date

11. **Write team configuration** to record the selection.

   **Primary location**: `.sdlc/team-config.json` (project root, not `.claude/`).

   **Why not `.claude/`**: Claude Code treats `.claude/` as a sensitive path and may block writes. Using `.sdlc/` avoids this friction while keeping configuration project-local and gitignore-able.

   If `.sdlc/` directory does not exist, create it first.

   ```json
   {
     "project_type": "<step 2 selection>",
     "sdlc_method": "<step 3 selection: solo | single-team | programme | assured | undecided>",
     "sdlc_method_commissioned": false,
     "formation": "<formation-name>",
     "installed_plugins": [
       "sdlc-core@ai-first-sdlc",
       "<team-plugin>@ai-first-sdlc",
       "<sdlc-method-bundle if programme/assured>@ai-first-sdlc"
     ],
     "technologies_detected": ["postgresql", "redis", "fastapi"],
     "discovered_tools": [
       {
         "name": "@postgresql/mcp-server",
         "type": "mcp-server",
         "url": "https://npmjs.com/package/@postgresql/mcp-server",
         "installed": true,
         "discovered_at": "<YYYY-MM-DD>"
       }
     ],
     "configured_at": "<YYYY-MM-DD>",
     "configured_by": "sdlc:setup-team"
   }
   ```

   - `sdlc_method`: one of `solo`, `single-team`, `programme`, `assured`, `undecided` (from step 3)
   - `sdlc_method_commissioned`: `false` initially — the actual `/sdlc-core:commission` skill writes a separate `commissioning` block to the same file when run, and may flip this flag. Setup-team writes `false` unless the bundle is already commissioned (detectable via existing `commissioning` block in a pre-existing `.sdlc/team-config.json`).
   - `technologies_detected`: list of technology names found by the tech stack scan (step 6a) plus any added by the user (step 6b)
   - `discovered_tools`: list of 1st-party tools found during discovery (step 6c), with `installed: true/false` indicating whether the user chose to install each one
   - If no technologies were detected and discovery was skipped, omit both `technologies_detected` and `discovered_tools` fields

   The formation name maps from `agents/agent-compositions.yaml`:
   - Full-stack → `full-stack-developer`
   - AI/ML → `ai-system-expert`
   - Cloud → `cloud-native-architect`
   - API → `enterprise-architect`
   - Security → `compliance-specialist`

   **Fallback**: If `.sdlc/team-config.json` also fails to write for any reason, write to `team-config.json` in the project root and warn the user.

12. **Report** the configured formation, installed plugins, and SDLC method.

   Include in the report:
   - Project type (step 2)
   - SDLC method (step 3) and whether commissioning is still pending
   - Formation name (step 11)
   - Plugins to be installed (step 9 list)
   - Post-install commission command if `sdlc_method` is `solo`, `programme`, or `assured`

13. **Post-check: verify what actually landed**

    After the user has (presumably) run the install commands from step 9, re-check what's installed:

    1. Re-read `enabledPlugins` from global + project settings (same as step 0a)
    2. Compare against what was recommended in step 8 (excluding already-installed plugins from step 0)
    3. Report:

    ```
    Post-setup verification:

      ✓ sdlc-team-fullstack@ai-first-sdlc — installed successfully
      ✗ sdlc-lang-python@ai-first-sdlc — NOT installed
      ✓ sdlc-knowledge-base@ai-first-sdlc — installed successfully
      ✓ sdlc-assured@ai-first-sdlc — installed successfully
        ⚠ Bundle is installed but uncommissioned. Run:
          /sdlc-core:commission --option assured --level production
        (or /sdlc-assured:commission-assured)

    3 of 4 recommended plugins installed. 1 still pending.
    1 SDLC method bundle still needs commissioning.
    ```

    If any recommendations are still pending, re-present the install commands so the user doesn't have to scroll up:

    ```
    Still pending:
      /plugin install sdlc-lang-python@ai-first-sdlc
    ```

    For SDLC method `solo`, `programme`, or `assured`: also re-present the **commission command** if `.sdlc/team-config.json` does not yet show a `commissioning` block (i.e., the user has installed the bundle but hasn't run `/sdlc-core:commission` yet):

    ```
    SDLC method commissioning still pending:
      /sdlc-core:commission --option <method> --level production
      (or the bundle-side equivalent)
    ```

    For `sdlc_method: undecided`: surface a one-line reminder:

    ```
    SDLC method: undecided. When you're ready, run /sdlc-core:commission to pick
    one of solo / single-team / programme / assured. See docs/METHODS-GUIDE.md.
    ```

    If ALL recommendations were installed (or were already installed from step 0) AND the SDLC method bundle is commissioned (or `sdlc_method` is `single-team`, the no-commission default), report:

    ```
    All recommended plugins are installed and the SDLC method is set up. Setup complete.
    ```

    **Edge cases**:
    - If the user didn't run any install commands (exited early), the post-check will show all recommendations as pending. That's correct — it's informational, not a gate.
    - If the user installed plugins between steps via a different mechanism (e.g., running `/plugin install` manually during setup), the post-check will pick those up.
    - Only verify plugins the user accepted in step 8 — don't show plugins the user explicitly declined in "customize" mode.
    - If the user's `sdlc_method` from step 3 is `single-team`, no commission command needs to surface — single-team is the default behaviour and requires no commissioning step.
