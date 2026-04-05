---
name: setup-team
description: Configure SDLC team formation for this project. Recommends and installs team plugins based on project type.
disable-model-invocation: true
---

# SDLC Team Setup

Configure the right agent team for this project by selecting a project type and installing the matching team plugins.

## Steps

1. **Check current team configuration**

Look for `.claude/team-config.json` in the project root. If it exists, display the current formation and ask if the user wants to reconfigure.

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

5. **Ask about project management and documentation needs:**
   - "Do you need project management support (sprints, delivery tracking)?" → recommend `sdlc-team-pm`
   - "Do you need documentation architecture?" → recommend `sdlc-team-docs`

6. **Present the recommendation** to the user:

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

7. **If confirmed, install the plugins.** Tell the user to run:

   ```
   /plugin install <plugin-name>@ai-first-sdlc
   ```

   for each recommended plugin. Note: skill cannot programmatically install plugins — it provides the commands for the user to run.

8. **Write team configuration** to record the selection.

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

9. **Report** the configured formation and installed plugins.
