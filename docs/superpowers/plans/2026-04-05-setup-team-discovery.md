# Setup-Team Discovery Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add tech stack scanning and 1st-party tool discovery to the setup-team skill so project setup recommends both SDLC plugins and official vendor tooling in one unified, sectioned recommendation.

**Architecture:** New step 5 inserted into the setup-team SKILL.md between language detection (step 4) and PM/docs (current step 5, becomes step 6). The recommendation format (current step 6, becomes step 7) changes from a flat list to three sections. The team-config JSON schema gains `discovered_tools` and `technologies_detected` fields.

**Tech Stack:** Markdown skill file (SKILL.md) — no code, this is an LLM instruction document.

---

### Task 1: Insert Tech Stack Scan & Discovery Step

**Files:**
- Modify: `plugins/sdlc-core/skills/setup-team/SKILL.md`

- [ ] **Step 1: Update step 1 to check `.sdlc/team-config.json` instead of `.claude/team-config.json`**

In the skill file, step 1 (line 15) currently says:

```markdown
Look for `.claude/team-config.json` in the project root. If it exists, display the current formation and ask if the user wants to reconfigure.
```

Replace with:

```markdown
Look for `.sdlc/team-config.json` in the project root (or `.claude/team-config.json` as a fallback). If it exists, display the current formation and ask if the user wants to reconfigure.
```

- [ ] **Step 2: Insert new step 5 after language detection**

After step 4 (line 39, the language detection step) and before step 5 (line 41, the PM/docs question), insert the following new step:

```markdown
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
```

- [ ] **Step 3: Renumber existing steps 5-9 to 6-10**

The current step 5 (PM/docs question) becomes step 6.
The current step 6 (present recommendation) becomes step 7.
The current step 7 (install plugins) becomes step 8.
The current step 8 (write team configuration) becomes step 9.
The current step 9 (report) becomes step 10.

Change each heading number:
- `5. **Ask about project management` → `6. **Ask about project management`
- `6. **Present the recommendation**` → `7. **Present the recommendation**`
- `7. **If confirmed, install the plugins.**` → `8. **If confirmed, install the plugins.**`
- `8. **Write team configuration**` → `9. **Write team configuration**`
- `9. **Report**` → `10. **Report**`

- [ ] **Step 4: Commit**

```bash
git add plugins/sdlc-core/skills/setup-team/SKILL.md
git commit -m "feat: add tech stack scan and discovery to setup-team (#83)

New step 5 scans project files (README, requirements.txt, docker-compose,
etc.) for technologies, asks user for additions, and runs 1st-party
discovery for each. Existing steps renumbered 6-10."
```

---

### Task 2: Update Recommendation Format

**Files:**
- Modify: `plugins/sdlc-core/skills/setup-team/SKILL.md`

- [ ] **Step 1: Replace the recommendation presentation**

Find the step that is now step 7 (was step 6, "Present the recommendation"). Replace the entire recommendation block (the code fence showing the flat list) with:

```markdown
7. **Present the recommendation** to the user in three sections:

   ```
   Recommended setup for your project:

   === SDLC Framework ===
   These provide the development methodology — rules, validation, specialist agents.

   ✓ sdlc-core — rules, validation, enforcement (always installed)
     → sdlc-enforcer, critical-goal-reviewer, code-review-specialist, verification-enforcer
   ○ <team plugins from step 3>
   ○ <language plugin from step 4>

   === Technology-Specific Tools ===
   Official vendor tooling discovered for your tech stack.

   ○ <tool name> — <capabilities>
     Source: <url> | Type: <MCP Server/Agent Skills/Plugin/Action> | Maintained: <Yes/No>
   ○ <tool name> — <capabilities>
     Source: <url> | Type: <MCP Server/Agent Skills/Plugin/Action> | Maintained: <Yes/No>

   (If no tools were discovered:)
   No official vendor tooling found for your tech stack.
   You can search later using the pipeline-orchestrator's discovery phase.

   === Project Support (optional) ===
   ○ sdlc-team-pm — sprint planning, delivery tracking, retrospectives
   ○ sdlc-team-docs — technical writing, documentation architecture

   Install all? [Y/n/customize]
   ```

   If the user chooses "customize", allow them to select/deselect individual items from all three sections.
```

- [ ] **Step 2: Commit**

```bash
git add plugins/sdlc-core/skills/setup-team/SKILL.md
git commit -m "feat: three-section recommendation format for setup-team (#83)

SDLC Framework, Technology-Specific Tools, Project Support.
Discovered tools show name, type, source, and maintenance status."
```

---

### Task 3: Update Team Config Schema

**Files:**
- Modify: `plugins/sdlc-core/skills/setup-team/SKILL.md`

- [ ] **Step 1: Update the team-config.json example**

Find the step that is now step 9 (was step 8, "Write team configuration"). Replace the JSON example with:

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

Add a note after the JSON:

```markdown
   - `technologies_detected`: list of technology names found by the tech stack scan (step 5a) plus any added by the user (step 5b)
   - `discovered_tools`: list of 1st-party tools found during discovery (step 5c), with `installed: true/false` indicating whether the user chose to install each one
   - If no technologies were detected and discovery was skipped, omit both fields
```

- [ ] **Step 2: Commit**

```bash
git add plugins/sdlc-core/skills/setup-team/SKILL.md
git commit -m "feat: add discovered_tools to team-config schema (#83)

Records technologies detected and 1st-party tools discovered
during setup, with installed status for each tool."
```

---

### Task 4: Sync Source Copy

**Files:**
- Sync: `skills/setup-team/SKILL.md` (source) from `plugins/sdlc-core/skills/setup-team/SKILL.md` (plugin)

- [ ] **Step 1: Copy plugin to source**

```bash
cp plugins/sdlc-core/skills/setup-team/SKILL.md skills/setup-team/SKILL.md
```

- [ ] **Step 2: Verify sync**

```bash
diff plugins/sdlc-core/skills/setup-team/SKILL.md skills/setup-team/SKILL.md
```

Expected: no output (files identical).

- [ ] **Step 3: Commit**

```bash
git add skills/setup-team/SKILL.md
git commit -m "chore: sync setup-team source copy with plugin"
```

---

### Task 5: Create Feature Proposal

**Files:**
- Create: `docs/feature-proposals/83-extend-discovery-setup-audit.md`

- [ ] **Step 1: Create the feature proposal**

```markdown
# Feature Proposal: Extend Discovery to Project Setup and Audit

**Proposal Number:** 83
**Status:** In Progress
**Author:** Claude (AI Agent)
**Created:** 2026-04-05
**Target Branch:** `feature/extend-discovery-setup-audit`

---

## Executive Summary

Extend 1st-party tool discovery (#82) to three additional contexts: project setup (setup-team skill), existing agent audit, and project plugin library.

---

## Motivation

### Problem Statement

The setup-team skill recommends SDLC plugins but doesn't search for official vendor tooling. Users miss MCP servers, agent skills, and other tools that their tech stack has available. The existing agent base was built without discovery and may have official alternatives.

### User Stories

- As a developer, I want setup to recommend PostgreSQL's MCP server alongside the SDLC plugins
- As a framework maintainer, I want to audit existing agents for official alternatives
- As a team, I want a project-level list of all recommended tools

---

## Proposed Solution

Three parts, implemented sequentially on one branch:
1. Setup-team discovery — scan tech stack, discover tools, three-section recommendation
2. Agent base audit — search for alternatives to existing agents
3. Plugin library — `.sdlc/recommended-plugins.json`

---

## Success Criteria

- [ ] Setup-team scans tech stack and presents three-section recommendation
- [ ] Existing agents audited for 1st-party alternatives
- [ ] Plugin library file maintained per project

---

## Changes Made

| Action | File |
|--------|------|
| Modify | `plugins/sdlc-core/skills/setup-team/SKILL.md` |
| Sync | `skills/setup-team/SKILL.md` |
| Create | `docs/superpowers/specs/2026-04-05-setup-team-discovery-design.md` |
| Create | `docs/superpowers/plans/2026-04-05-setup-team-discovery.md` |
```

- [ ] **Step 2: Commit**

```bash
git add docs/feature-proposals/83-extend-discovery-setup-audit.md
git commit -m "docs: add feature proposal for #83"
```
