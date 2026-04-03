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
   | A. Full-stack | `sdlc-team-fullstack` |
   | B. AI/ML | `sdlc-team-ai`, `sdlc-lang-python` |
   | C. Cloud | `sdlc-team-cloud` |
   | D. API | `sdlc-team-fullstack`, `sdlc-team-cloud` |
   | E. Security | `sdlc-team-security` |
   | F. Custom | User picks from list |

4. **Auto-detect language** by scanning file extensions in the project:
   - `.py` files dominant → also recommend `sdlc-lang-python`
   - `.js`/`.ts` files dominant → also recommend `sdlc-lang-javascript`

5. **Present the recommendation** to the user:

   ```
   Recommended team for this project:

   ✓ sdlc-core (already installed)
   ○ sdlc-team-ai — AI architects, prompt engineers, RAG designers
   ○ sdlc-lang-python — Python-specific validation and patterns

   Install these plugins? [Y/n]
   ```

6. **If confirmed, install the plugins.** Tell the user to run:

   ```
   /plugin install <plugin-name>@ai-first-sdlc
   ```

   for each recommended plugin. Note: skill cannot programmatically install plugins — it provides the commands for the user to run.

7. **Write `.claude/team-config.json`** to record the selection:

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

8. **Report** the configured formation and installed plugins.
