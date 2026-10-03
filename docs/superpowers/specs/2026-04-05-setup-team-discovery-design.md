# Setup-Team Discovery — Part 1 of #83

**Date**: 2026-04-05
**Status**: Approved
**Issue**: #83 (Part 1 of 3)
**Branch**: `feature/extend-discovery-setup-audit`

## Problem

The `setup-team` skill recommends SDLC plugins based on project type but doesn't search for official vendor tooling. A user setting up a FastAPI + PostgreSQL project gets `sdlc-team-fullstack` and `sdlc-lang-python` but never learns that PostgreSQL has an official MCP server or that FastAPI has community tools. Setup should be a one-stop shop — SDLC framework plugins AND technology-specific tools.

## Solution

Add a tech stack scan + discovery step to the `setup-team` skill. After detecting the project type and language, scan for technologies in the project, ask the user what else they're using, run 1st-party discovery for each technology, and present a unified three-section recommendation.

## Changes to setup-team Skill

### New Step 5: Tech Stack Scan & Discovery

Inserted between current step 4 (language detection) and current step 5 (PM/docs question). Existing steps 5-9 shift to 6-10.

**5a. Scan project for technologies:**

Check these files for known technology names:

| File | What to extract |
|------|----------------|
| `README.md` | Technology mentions: look for names of databases, frameworks, cloud providers, services in the project description. READMEs often describe the intended stack before code exists. |
| `requirements.txt` / `pyproject.toml` | Package names: flask, fastapi, django, sqlalchemy, redis, celery, boto3, psycopg2, pymongo, etc. |
| `package.json` | Dependencies: express, next, prisma, mongoose, ioredis, aws-sdk, etc. |
| `Gemfile` | Gems: rails, pg, redis, sidekiq, etc. |
| `go.mod` | Modules: gin, gorm, go-redis, aws-sdk-go, etc. |
| `Cargo.toml` | Crates: actix-web, diesel, redis-rs, rusoto, etc. |
| `docker-compose.yml` | Service images: postgres, redis, mongo, rabbitmq, elasticsearch, etc. |
| `.env` / `.env.example` | Connection strings: DATABASE_URL (extract db type), REDIS_URL, MONGO_URI, etc. |
| `CLAUDE.md` | Technology references in the project instructions — often lists the stack explicitly. |

Map detected packages/services to technology names: `psycopg2` → PostgreSQL, `pymongo` → MongoDB, `redis` → Redis, `boto3` → AWS, etc.

**5b. Present findings and ask the user:**

```
I detected the following technologies in your project:
- PostgreSQL (from requirements.txt: psycopg2-binary)
- Redis (from docker-compose.yml: redis:7)

Any other technologies I should search for? (e.g., Stripe, Twilio, Elasticsearch)
Or press Enter to continue with these.
```

If the project is empty/new (no dependency files found):
```
No dependency files found yet (new project).
What technologies will this project use? (e.g., PostgreSQL, MongoDB, Redis, AWS, Stripe)
```

**5c. Run discovery for each technology:**

Use the same search strategy as pipeline-orchestrator Phase 0:

1. MCP server registries: `"{tech} mcp server" site:npmjs.com`, `site:pypi.org`
2. Vendor GitHub org: `"github.com/{vendor}" mcp OR agent OR skills`
3. Claude plugin marketplace
4. GitHub Actions marketplace
5. Targeted web search: `"{tech} official mcp server"`, `"{tech} agent skills"`

Compile results into a list of discovered tools with: name, type (MCP Server / Agent Skills / Plugin / Action), source URL, capabilities, and whether it's actively maintained.

**5d. Compile into recommendation:**

Discovered tools become the "Technology-Specific Tools" section of the recommendation (see Recommendation Format below).

### Updated Recommendation Format

The existing step 6 (present recommendation) changes from a single flat list to three sections:

```
Recommended setup for your {project description}:

=== SDLC Framework ===
These provide the development methodology — rules, validation, specialist agents.

✓ sdlc-core — rules, validation, enforcement (always installed)
○ sdlc-team-common — solution-architect, database-architect, performance-engineer, ...
○ sdlc-team-fullstack — backend-architect, api-architect, frontend-architect, ...
○ sdlc-lang-python — Python expert, type safety, testing patterns

=== Technology-Specific Tools ===
Official vendor tooling discovered for your tech stack.

○ @postgresql/mcp-server — direct database queries, schema inspection, migrations
  Source: npmjs.com | Type: MCP Server | Maintained: Yes
○ @redis/mcp-server — cache operations, key inspection, pub/sub
  Source: npmjs.com | Type: MCP Server | Maintained: Yes

=== Project Support (optional) ===
○ sdlc-team-pm — sprint planning, delivery tracking, retrospectives
○ sdlc-team-docs — technical writing, documentation architecture

Install all? [Y/n/customize]
```

If no technology-specific tools are discovered, that section shows:
```
=== Technology-Specific Tools ===
No official vendor tooling found for your tech stack.
(You can search later with the pipeline-orchestrator's discovery phase.)
```

### Team Config Update

`.sdlc/team-config.json` gains a `discovered_tools` field:

```json
{
  "project_type": "full-stack web application",
  "formation": "full-stack-developer",
  "installed_plugins": [
    "sdlc-core@ai-first-sdlc",
    "sdlc-team-common@ai-first-sdlc",
    "sdlc-team-fullstack@ai-first-sdlc",
    "sdlc-lang-python@ai-first-sdlc"
  ],
  "discovered_tools": [
    {
      "name": "@postgresql/mcp-server",
      "type": "mcp-server",
      "url": "https://npmjs.com/package/@postgresql/mcp-server",
      "installed": true,
      "discovered_at": "2026-04-05"
    },
    {
      "name": "@redis/mcp-server",
      "type": "mcp-server",
      "url": "https://npmjs.com/package/@redis/mcp-server",
      "installed": false,
      "discovered_at": "2026-04-05"
    }
  ],
  "technologies_detected": ["postgresql", "redis", "fastapi"],
  "configured_at": "2026-04-05",
  "configured_by": "sdlc:setup-team"
}
```

## Files Changed

| File | Change |
|------|--------|
| `plugins/sdlc-core/skills/setup-team/SKILL.md` | Add step 5 (tech scan + discovery), update recommendation format, update team-config schema |
| `skills/setup-team/SKILL.md` | Source copy, kept in sync |

## Success Criteria

1. Setup-team scans dependency files for technologies
2. Presents findings and asks user for additional technologies
3. Runs discovery for each technology (4 registry sources + web search)
4. Recommendation has three sections: SDLC Framework, Technology-Specific Tools, Project Support
5. Each discovered tool shows name, type, source, and maintenance status
6. Team config records discovered tools with installed/not-installed status
7. Works on empty projects (asks user directly)
8. Works on existing projects (scans + asks)

## What This Does NOT Change

- The project type selection (step 2) — unchanged
- The plugin mapping logic (step 3) — unchanged
- The language detection (step 4) — unchanged
- The plugin installation mechanism (step 7) — unchanged
- The pipeline-orchestrator's Phase 0 — reuses same search strategy but doesn't modify it
