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

   For each tool found, record: name, type (MCP Server / Agent Skills / Plugin / Action), source URL, brief capabilities description, and whether it appears actively maintained (last commit/publish within 6 months).

   **5d. If no technologies detected and user skipped:** Skip this step entirely and proceed to step 6.

6. **Ask about project management and documentation needs:**
   - "Do you need project management support (sprints, delivery tracking)?" → recommend `sdlc-team-pm`
   - "Do you need documentation architecture?" → recommend `sdlc-team-docs`

7. **Present the recommendation** to the user:

   ```
   Recommended team for this project:

   ✓ sdlc-core (already installed)
     → sdlc-enforcer, critical-goal-reviewer, code-review-specialist

   ○ sdlc-team-common — 8 agents:
     solution-architect, deep-research-agent, performance-engineer,
     observability-specialist, database-architect, agent-builder,
     pipeline-orchestrator, repo-knowledge-distiller

   ○ sdlc-team-ai — 14 agents:
     ai-solution-architect, prompt-engineer, mcp-server-architect,
     rag-system-designer, context-engineer, orchestration-architect,
     ai-devops-engineer, ai-team-transformer, a2a-architect,
     agent-developer, langchain-architect, mcp-quality-assurance,
     mcp-test-agent, ai-test-engineer

   ○ sdlc-lang-python — 1 agent:
     language-python-expert

   Install these plugins? [Y/n]
   ```

8. **If confirmed, install the plugins.** Tell the user to run:

   ```
   /plugin install <plugin-name>@ai-first-sdlc
   ```

   for each recommended plugin. Note: skill cannot programmatically install plugins — it provides the commands for the user to run.

9. **Write team configuration** to record the selection.

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
     "configured_at": "<YYYY-MM-DD>",
     "configured_by": "sdlc:setup-team"
   }
   ```

   The formation name maps from `agents/agent-compositions.yaml`:
   - Full-stack → `full-stack-developer`
   - AI/ML → `ai-system-expert`
   - Cloud → `cloud-native-architect`
   - API → `enterprise-architect`
   - Security → `compliance-specialist`

   **Fallback**: If `.sdlc/team-config.json` also fails to write for any reason, write to `team-config.json` in the project root and warn the user.

10. **Report** the configured formation and installed plugins.
