# Setup Smoke Test

You are running inside a Docker container. Your job is to install the SDLC plugins, run setup-team on this project, install all recommended tools, and verify everything works.

The project README.md describes an EventFlow analytics platform. Read it to understand the tech stack.

## Phase 0: Install Plugins

Install the SDLC plugins from the public GitHub marketplace:

```
/plugin marketplace add SteveGJones/ai-first-sdlc-practices
/plugin install sdlc-core@ai-first-sdlc
/plugin install sdlc-team-common@ai-first-sdlc
/plugin install sdlc-team-fullstack@ai-first-sdlc
/plugin install sdlc-team-pm@ai-first-sdlc
/plugin install sdlc-team-docs@ai-first-sdlc
/plugin install sdlc-lang-python@ai-first-sdlc
```

Verify with `/plugin list`. All 6 should appear.

If any install fails, record the error and stop.

## Phase 1: Run Setup-Team

Read the project README.md to understand the tech stack.

Run the setup-team flow:
1. Select **A. Full-stack web application** as the project type
2. When asked about technologies, confirm the detected stack and add any that were missed
3. Accept the three-section recommendation (SDLC Framework / Technology-Specific Tools / Project Support)
4. Confirm installation of all recommended items

The setup-team skill should:
- Detect from README.md: MongoDB, Redis, Kafka, React, FastAPI, AWS, Terraform, Grafana, GitHub Actions
- Run discovery for each technology
- Write `.sdlc/team-config.json` and `.sdlc/recommended-plugins.json`

## Phase 2: Install Recommended Tools

Read `.sdlc/recommended-plugins.json`. For every tool listed:

**MCP servers** (type: mcp-server):
```bash
npm install -g <package-name>
```

**Python packages**:
```bash
pip install <package-name>
```

**Agent skills** (type: agent-skills, GitHub URLs):
```bash
git clone <url> /opt/agent-skills/<name>
```

**GitHub Actions** (type: action):
No install needed — just verify the URL resolves with curl.

Record success/failure for each tool. If a tool fails to install, note the error but continue with the remaining tools.

## Phase 3: Verify Outputs

Check the following. Report PASS or FAIL for each:

1. `.sdlc/team-config.json` exists
2. `team-config.json` has `project_type` set
3. `team-config.json` has `formation` set
4. `team-config.json` has `installed_plugins` as a non-empty array
5. `team-config.json` has `technologies_detected` with at least 5 entries
6. `.sdlc/recommended-plugins.json` exists
7. `recommended-plugins.json` has `plugins` as a non-empty array
8. At least one plugin has `type: "mcp-server"`
9. At least one plugin has `installed: true`
10. All tools marked `installed: true` are actually available:
    - For npm packages: `npm list -g <package> 2>/dev/null`
    - For pip packages: `pip show <package> 2>/dev/null`
    - For cloned repos: `ls /opt/agent-skills/<name> 2>/dev/null`

Print a summary:

```
=== Smoke Test Results ===
Check 1 (team-config exists):       PASS/FAIL
Check 2 (project_type set):         PASS/FAIL
Check 3 (formation set):            PASS/FAIL
Check 4 (installed_plugins):        PASS/FAIL
Check 5 (technologies_detected):    PASS/FAIL
Check 6 (recommended-plugins exists): PASS/FAIL
Check 7 (plugins array):            PASS/FAIL
Check 8 (has mcp-server):           PASS/FAIL
Check 9 (has installed tool):       PASS/FAIL
Check 10 (tools actually work):     PASS/FAIL

Result: X/10 PASS
```

Output `LOOP_COMPLETE`.
