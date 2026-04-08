---
name: setup-team
description: Configure SDLC team formation for this project. Recommends and installs team plugins based on project type.
disable-model-invocation: true
---

# SDLC Team Setup

Configure the right agent team for this project by selecting a project type and installing the matching team plugins.

## Steps

1. **Check current team configuration**

Look for `.sdlc/team-config.json` in the project root (or `.claude/team-config.json` as a fallback). If it exists, display the current formation and ask if the user wants to reconfigure.

2. **Ask the user what kind of project this is** (present as multiple choice):

   - **A. Full-stack web application** — frontend + backend + API + DevOps
   - **B. AI/ML system** — AI architects + prompt engineers + RAG designers
   - **C. Cloud infrastructure** — cloud + containers + SRE + observability
   - **D. API/microservices** — API + backend + integration + performance
   - **E. Security-focused** — security + compliance + privacy
   - **F. Custom** — pick individual team plugins

3. **Map selection to recommended plugins:**

   | Selection | Plugins |
   |-----------|---------|
   | A. Full-stack | `sdlc-team-common`, `sdlc-team-fullstack` |
   | B. AI/ML | `sdlc-team-common`, `sdlc-team-ai`, `sdlc-lang-python` |
   | C. Cloud | `sdlc-team-common`, `sdlc-team-cloud` |
   | D. API | `sdlc-team-common`, `sdlc-team-fullstack`, `sdlc-team-cloud` |
   | E. Security | `sdlc-team-common`, `sdlc-team-security` |
   | F. Custom | User picks from list |

4. **Auto-detect language** by scanning file extensions in the project:
   - `.py` files dominant → also recommend `sdlc-lang-python`
   - `.js`/`.ts` files dominant → also recommend `sdlc-lang-javascript`

5. **Scan tech stack and discover 1st-party tools**

   **5a. Scan project files for technologies:**

   Check the following files for known technology names. If a file doesn't exist, skip it.

   | File | What to extract |
   |------|----------------|
   | `README.md` | Technology mentions in the project description (databases, frameworks, cloud providers, services) |
   | `CLAUDE.md` | Technology references in project instructions |
   | `requirements.txt` / `pyproject.toml` | Python packages: flask, fastapi, django, sqlalchemy, redis, celery, boto3, psycopg2, pymongo, etc. |
   | `package.json` | JS/TS dependencies: express, next, prisma, mongoose, ioredis, aws-sdk, etc. |
   | `Gemfile` | Ruby gems: rails, pg, redis, sidekiq, etc. |
   | `go.mod` | Go modules: gin, gorm, go-redis, aws-sdk-go, etc. |
   | `Cargo.toml` | Rust crates: actix-web, diesel, redis-rs, rusoto, etc. |
   | `docker-compose.yml` | Service images: postgres, redis, mongo, rabbitmq, elasticsearch, etc. |
   | `.env` / `.env.example` | Connection strings: DATABASE_URL (extract db type), REDIS_URL, MONGO_URI, etc. |

   Map detected packages/services to technology names:
   - `psycopg2` / `psycopg2-binary` / `asyncpg` → PostgreSQL
   - `pymongo` / `motor` → MongoDB
   - `redis` / `redis-py` / `ioredis` → Redis
   - `boto3` / `aws-sdk` / `aws-sdk-go` → AWS
   - `google-cloud-*` → Google Cloud
   - `azure-*` → Azure
   - `celery` → Celery
   - `elasticsearch` / `opensearch` → Elasticsearch
   - `prisma` → Prisma
   - `stripe` → Stripe
   - `twilio` → Twilio

   **5b. Present findings and ask the user:**

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

   **5c. Run discovery for each technology:**

   For each technology (detected + user-specified), search for official vendor tooling using these sources:

   - MCP server registries: WebSearch `"{technology} mcp server" site:npmjs.com` and `site:pypi.org`
   - Vendor GitHub org: WebSearch `"github.com/{vendor}" mcp OR agent OR skills OR claude`
   - Claude plugin marketplace: WebSearch `"{technology} claude code plugin"`
   - GitHub Actions marketplace: WebSearch `"{technology} github action" site:github.com/marketplace`
   - Targeted web search: `"{technology} official mcp server"`, `"{technology} agent skills"`

   For each tool found, record: name, **category** (one of `claude-plugin` / `mcp-server-npm` / `mcp-server-pip` / `mcp-server-binary` / `github-action` / `standalone-cli` / `library-framework`), **section** (A or B — see below), source URL, brief capabilities description, and whether it appears actively maintained (last commit/publish within 6 months).

   **Two-section split**:
   - **Section A — Claude Code Environment Tools**: install these *into* Claude Code to extend its capabilities
   - **Section B — Project Dependencies**: libraries for the user's own project code (custom MCP server, custom agent, app calling Claude)

   Classification rules (each category maps to exactly one section):
   - In a Claude Code plugin marketplace (has `.claude-plugin/marketplace.json`)? → `claude-plugin` → **Section A**
   - npm package runnable via `npx`, exposes MCP as a **pre-built server**? → `mcp-server-npm` → **Section A**
   - PyPI package runnable via `python -m`, exposes MCP as a **pre-built server**? → `mcp-server-pip` → **Section A**
   - Pre-built binary distributed via GitHub releases, exposes MCP? → `mcp-server-binary` → **Section A**
   - Claude Code-specific GitHub Action (e.g., `anthropics/claude-code-action`)? → `github-action` → **Section A**
   - Standalone repository the user clones and runs alongside Claude Code? → `standalone-cli` → **Section A**
   - Foundation library (FastMCP, `@modelcontextprotocol/sdk`, Anthropic SDK, vendor driver) used to **build** other tools? → `library-framework` → **Section B**

   **Key distinction** — the difference between `mcp-server-npm` (Section A) and `library-framework` (Section B):
   - `@modelcontextprotocol/server-filesystem` is a pre-built MCP server → Section A: the user runs `npx -y @modelcontextprotocol/server-filesystem` via `.mcp.json`
   - `@modelcontextprotocol/sdk` is a library for building MCP servers → Section B: the user runs `npm install @modelcontextprotocol/sdk` inside their own project and imports from it in code they write

   If uncertain: "Does the user run this as-is alongside Claude Code, or do they import it in code they're writing themselves?" Running as-is = A. Importing in their own code = B.

   **5c.1 Generate install instructions per tool.** Every tool gets an install snippet derived from its category. Use the exact format below per category — never invent install commands or guess at undocumented setup. If you cannot determine the install path with confidence, write: `Manual setup required. See <url>/README.md.`

   - **`claude-plugin`** in `anthropics/claude-plugins-official`:
     ```
     /plugin marketplace add anthropics/claude-plugins-official
     /plugin install <plugin-name>@claude-plugins-official
     ```
   - **`claude-plugin`** in another marketplace repo (read its `.claude-plugin/marketplace.json` to get the marketplace name):
     ```
     /plugin marketplace add <owner>/<repo>
     /plugin install <plugin-name>@<marketplace-name>
     ```
   - **`mcp-server-npm`** — add to `.mcp.json` (create if missing):
     ```json
     { "mcpServers": { "<server-name>": { "command": "npx", "args": ["-y", "<package>"], "env": { "<env-var>": "<value>" } } } }
     ```
     Note any required env vars (API keys, connection strings) explicitly. Then restart Claude Code or run `/mcp`.
   - **`mcp-server-pip`** — install package, then add to `.mcp.json`:
     ```bash
     pip install <package>
     ```
     ```json
     { "mcpServers": { "<server-name>": { "command": "python", "args": ["-m", "<module>"], "env": { "<env-var>": "<value>" } } } }
     ```
   - **`mcp-server-binary`** — download from release URL, then add to `.mcp.json` with absolute path to the binary
   - **`github-action`** — add to a workflow YAML file:
     ```yaml
     - name: <descriptive name>
       uses: <owner>/<repo>@<version-tag>
       with:
         <input>: <value>
     ```
     Pin to a specific version tag, not `@main`. Note any required `secrets.*`.
   - **`standalone-cli`**:
     ```bash
     git clone <repo-url> ~/tools/<tool-name>
     cd ~/tools/<tool-name>
     <run command from README>
     ```
   - **`library-framework`**:
     ```bash
     <pip|npm|cargo> install <package>
     ```
     Foundation library — used to *build* tools, not invoked directly. Link to docs.

   **5d. If no technologies detected and user skipped:** Skip this step entirely and proceed to step 6.

6. **Ask about project management and documentation needs:**
   - "Do you need project management support (sprints, delivery tracking)?" → recommend `sdlc-team-pm`
   - "Do you need documentation architecture?" → recommend `sdlc-team-docs`

7. **Present the recommendation** to the user in three sections:

   ```
   Recommended setup for your project:

   === SDLC Framework ===
   These provide the development methodology — rules, validation, specialist agents.

   ✓ sdlc-core — rules, validation, enforcement (always installed)
     → sdlc-enforcer, critical-goal-reviewer, code-review-specialist, verification-enforcer
   ○ <team plugins from step 3>
   ○ <language plugin from step 4>

   === Section A: Claude Code Environment Tools ===
   Install these INTO Claude Code to extend its capabilities. Each has ready-to-run installation instructions.

   ○ <tool name> — <capabilities>
     Source: <url>
     Category: <claude-plugin/mcp-server-npm/mcp-server-pip/mcp-server-binary/github-action/standalone-cli>
     Maintained: <Yes/No>
     Install (MANDATORY — never omit):
       <category-appropriate install snippet from step 5c.1>

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

   (If neither section has entries:)
   No official vendor tooling or libraries found for your tech stack.
   You can search later using the pipeline-orchestrator's discovery phase.

   === Project Support (optional) ===
   ○ sdlc-team-pm — sprint planning, delivery tracking, retrospectives
   ○ sdlc-team-docs — technical writing, documentation architecture

   Install all? [Y/n/customize]
   ```

   If the user chooses "customize", allow them to select/deselect individual items from all three sections.

8. **If confirmed, install the plugins.** Tell the user to run:

   ```
   /plugin install <plugin-name>@ai-first-sdlc
   ```

   for each recommended plugin. Note: skill cannot programmatically install plugins — it provides the commands for the user to run.

9. **Write the plugin library** at `.sdlc/recommended-plugins.json`

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
   - All technology-specific tools from step 5c discovery (type: `mcp-server`, `agent-skills`, etc.) with `installed: true/false` based on the user's choice
   - Do NOT duplicate entries that already exist (match on `name`)
   - Update `last_updated` to today's date

10. **Write team configuration** to record the selection.

   **Primary location**: `.sdlc/team-config.json` (project root, not `.claude/`).

   **Why not `.claude/`**: Claude Code treats `.claude/` as a sensitive path and may block writes. Using `.sdlc/` avoids this friction while keeping configuration project-local and gitignore-able.

   If `.sdlc/` directory does not exist, create it first.

   ```json
   {
     "project_type": "<selection>",
     "formation": "<formation-name>",
     "installed_plugins": [
       "sdlc-core@ai-first-sdlc",
       "<team-plugin>@ai-first-sdlc"
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

   - `technologies_detected`: list of technology names found by the tech stack scan (step 5a) plus any added by the user (step 5b)
   - `discovered_tools`: list of 1st-party tools found during discovery (step 5c), with `installed: true/false` indicating whether the user chose to install each one
   - If no technologies were detected and discovery was skipped, omit both fields

   The formation name maps from `agents/agent-compositions.yaml`:
   - Full-stack → `full-stack-developer`
   - AI/ML → `ai-system-expert`
   - Cloud → `cloud-native-architect`
   - API → `enterprise-architect`
   - Security → `compliance-specialist`

   **Fallback**: If `.sdlc/team-config.json` also fails to write for any reason, write to `team-config.json` in the project root and warn the user.

11. **Report** the configured formation and installed plugins.
