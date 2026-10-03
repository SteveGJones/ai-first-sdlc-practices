# Plugin Library Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `.sdlc/recommended-plugins.json` as a project-level tool catalogue, written by setup-team after install confirmation and by pipeline-orchestrator after discovery.

**Architecture:** Two existing files gain a write step: setup-team SKILL.md writes the initial library after install, pipeline-orchestrator appends during Phase 0 discovery. Dedup on name, idempotent writes.

**Tech Stack:** Markdown skill/agent files — no code

---

### Task 1: Add Plugin Library Write to Setup-Team

**Files:**
- Modify: `plugins/sdlc-core/skills/setup-team/SKILL.md`

- [ ] **Step 1: Add a new step after the install step (current step 8) and before the write-config step (current step 9)**

Read the file to find the current step numbering. Insert a new step between "If confirmed, install the plugins" and "Write team configuration". This becomes step 9, and the existing steps 9-10 shift to 10-11.

The new step:

```markdown
9. **Write the plugin library** at `.sdlc/recommended-plugins.json`

   If the file doesn't exist, create it. If it exists, read it and append (dedup on `name`).

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
         "installed": <true/false>,
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
```

- [ ] **Step 2: Renumber existing steps 9-10 to 10-11**

Change:
- Current step 9 (Write team configuration) → step 10
- Current step 10 (Report) → step 11

- [ ] **Step 3: Commit**

```bash
git add plugins/sdlc-core/skills/setup-team/SKILL.md
git commit -m "feat: setup-team writes .sdlc/recommended-plugins.json (#83)

New step 9 writes the plugin library after install confirmation.
Includes SDLC plugins and discovered technology tools.
Dedup on name, idempotent."
```

---

### Task 2: Add Plugin Library Write to Pipeline Orchestrator

**Files:**
- Modify: `agents/core/pipeline-orchestrator.md`

- [ ] **Step 1: Add a write to recommended-plugins.json in Phase 0**

In the pipeline-orchestrator's Phase 0 (Discovery), find the section where discovery results are saved to project memory (step 8 in Phase 0). Add after the memory write:

```markdown
9. **Append to project plugin library** (if `.sdlc/recommended-plugins.json` exists):

   For each tool in the discovery report, append to `.sdlc/recommended-plugins.json`:

   ```json
   {
     "name": "<tool-name>",
     "source": "<url>",
     "type": "<mcp-server/agent-skills/plugin/action>",
     "installed": <true if user chose "use-as-is" or "hybrid", false if "build-custom">,
     "added_by": "pipeline-orchestrator",
     "added_at": "<YYYY-MM-DD>",
     "note": "Discovered during <agent-name> creation. User chose: <decision>."
   }
   ```

   - If `.sdlc/recommended-plugins.json` doesn't exist, skip this step (the file is created by setup-team, not by the orchestrator)
   - Dedup on `name` — don't add tools that are already in the library
   - Update `last_updated`
```

- [ ] **Step 2: Commit**

```bash
git add agents/core/pipeline-orchestrator.md
git commit -m "feat: pipeline-orchestrator writes to recommended-plugins.json (#83)

Appends discovered tools to .sdlc/recommended-plugins.json during
Phase 0 discovery. Only writes if the file already exists (created
by setup-team). Dedup on name."
```

---

### Task 3: Sync All Modified Files

**Files:**
- Sync: `skills/setup-team/SKILL.md` from plugin copy
- Sync: `plugins/sdlc-team-common/agents/pipeline-orchestrator.md` from source

- [ ] **Step 1: Sync setup-team**

```bash
cp plugins/sdlc-core/skills/setup-team/SKILL.md skills/setup-team/SKILL.md
```

- [ ] **Step 2: Sync pipeline-orchestrator**

```bash
cp agents/core/pipeline-orchestrator.md plugins/sdlc-team-common/agents/pipeline-orchestrator.md
```

- [ ] **Step 3: Verify both syncs**

```bash
diff plugins/sdlc-core/skills/setup-team/SKILL.md skills/setup-team/SKILL.md
diff agents/core/pipeline-orchestrator.md plugins/sdlc-team-common/agents/pipeline-orchestrator.md
```

Expected: no output for both.

- [ ] **Step 4: Commit**

```bash
git add skills/setup-team/SKILL.md plugins/sdlc-team-common/agents/pipeline-orchestrator.md
git commit -m "chore: sync setup-team and pipeline-orchestrator copies (#83)"
```
