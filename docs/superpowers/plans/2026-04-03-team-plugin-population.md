# Team Plugin Population Implementation Plan (Phase 2)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Populate all team plugins with production agents, normalize agent frontmatter, and release v1.0.0 of the plugin family.

**Architecture:** A Python normalization script standardizes all 52 agent frontmatter to the Claude Code plugin schema. The `release-mapping.yaml` is extended with all agent-to-plugin mappings. The release-plugin skill copies normalized agents into plugin directories. Three new plugins (common, pm, docs) are created.

**Tech Stack:** Python (normalization script), YAML (release mapping), JSON (plugin manifests), Markdown (agent files, skills)

**Spec:** `docs/superpowers/specs/2026-04-03-team-plugin-population-design.md`

---

### Task 1: Create Feature Branch and New Plugin Scaffolding

**Files:**
- Create: `plugins/sdlc-team-common/.claude-plugin/plugin.json`
- Create: `plugins/sdlc-team-pm/.claude-plugin/plugin.json`
- Create: `plugins/sdlc-team-docs/.claude-plugin/plugin.json`
- Modify: `plugins/.claude-plugin/marketplace.json`

- [ ] **Step 1: Create feature branch**

```bash
git checkout main
git pull
git checkout -b feature/team-plugin-population
```

- [ ] **Step 2: Create sdlc-team-common plugin manifest**

Create `plugins/sdlc-team-common/.claude-plugin/plugin.json`:

```json
{
  "name": "sdlc-team-common",
  "version": "1.0.0",
  "description": "Cross-cutting specialist agents — architects, researchers, performance engineers",
  "author": {
    "name": "SteveGJones"
  },
  "keywords": ["sdlc", "common", "architect", "research", "performance"]
}
```

- [ ] **Step 3: Create sdlc-team-pm plugin manifest**

Create `plugins/sdlc-team-pm/.claude-plugin/plugin.json`:

```json
{
  "name": "sdlc-team-pm",
  "version": "1.0.0",
  "description": "Project management agents — agile coach, delivery manager, progress tracking",
  "author": {
    "name": "SteveGJones"
  },
  "keywords": ["sdlc", "project-management", "agile", "delivery", "tracking"]
}
```

- [ ] **Step 4: Create sdlc-team-docs plugin manifest**

Create `plugins/sdlc-team-docs/.claude-plugin/plugin.json`:

```json
{
  "name": "sdlc-team-docs",
  "version": "1.0.0",
  "description": "Documentation agents — technical writer, documentation architect",
  "author": {
    "name": "SteveGJones"
  },
  "keywords": ["sdlc", "documentation", "technical-writing", "docs-as-code"]
}
```

- [ ] **Step 5: Update marketplace.json — add 3 new plugins and update all versions**

Read `plugins/.claude-plugin/marketplace.json`. Add 3 new plugin entries and update ALL existing plugin versions from `0.1.0-stub` to `1.0.0`. Also update `sdlc-core` from `0.1.0` to `1.0.0`. Update marketplace metadata version to `1.0.0`.

The final plugins array should contain these 10 entries:

```json
{
  "name": "ai-first-sdlc",
  "owner": { "name": "SteveGJones" },
  "metadata": {
    "description": "AI-First SDLC Practices — plugin family for zero-debt development",
    "version": "1.0.0"
  },
  "plugins": [
    { "name": "sdlc-core", "source": "./sdlc-core", "description": "Core SDLC rules, validators, enforcement, and workflows", "version": "1.0.0" },
    { "name": "sdlc-team-common", "source": "./sdlc-team-common", "description": "Cross-cutting specialist agents — architects, researchers, performance engineers", "version": "1.0.0" },
    { "name": "sdlc-team-ai", "source": "./sdlc-team-ai", "description": "AI/ML specialist agents — architects, prompt engineers, RAG designers", "version": "1.0.0" },
    { "name": "sdlc-team-fullstack", "source": "./sdlc-team-fullstack", "description": "Full-stack agents — frontend, backend, API, DevOps architects", "version": "1.0.0" },
    { "name": "sdlc-team-cloud", "source": "./sdlc-team-cloud", "description": "Cloud infrastructure agents — cloud, container, SRE specialists", "version": "1.0.0" },
    { "name": "sdlc-team-security", "source": "./sdlc-team-security", "description": "Security agents — security, compliance, privacy specialists", "version": "1.0.0" },
    { "name": "sdlc-team-pm", "source": "./sdlc-team-pm", "description": "Project management agents — agile coach, delivery manager, progress tracking", "version": "1.0.0" },
    { "name": "sdlc-team-docs", "source": "./sdlc-team-docs", "description": "Documentation agents — technical writer, documentation architect", "version": "1.0.0" },
    { "name": "sdlc-lang-python", "source": "./sdlc-lang-python", "description": "Python-specific validation, patterns, and expert agents", "version": "1.0.0" },
    { "name": "sdlc-lang-javascript", "source": "./sdlc-lang-javascript", "description": "JavaScript/TypeScript-specific validation and patterns", "version": "1.0.0" }
  ]
}
```

- [ ] **Step 6: Update sdlc-core plugin.json version to 1.0.0**

Edit `plugins/sdlc-core/.claude-plugin/plugin.json`: change `"version": "0.1.0"` to `"version": "1.0.0"`.

- [ ] **Step 7: Update all stub plugin.json versions to 1.0.0**

For each of these files, change `"version": "0.1.0-stub"` to `"version": "1.0.0"`:
- `plugins/sdlc-team-ai/.claude-plugin/plugin.json`
- `plugins/sdlc-team-fullstack/.claude-plugin/plugin.json`
- `plugins/sdlc-team-cloud/.claude-plugin/plugin.json`
- `plugins/sdlc-team-security/.claude-plugin/plugin.json`
- `plugins/sdlc-lang-python/.claude-plugin/plugin.json`
- `plugins/sdlc-lang-javascript/.claude-plugin/plugin.json`

Also update descriptions to remove "Coming in Phase 2/3." suffix from each.

- [ ] **Step 8: Verify and commit**

```bash
python3 -c "import json, glob
for f in glob.glob('plugins/**/*.json', recursive=True):
    data = json.load(open(f))
    print(f'OK: {f} — {data.get(\"name\", \"marketplace\")} v{data.get(\"version\", data.get(\"metadata\", {}).get(\"version\", \"?\"))}')"
```

Expected: 10 plugins at v1.0.0, marketplace at v1.0.0.

```bash
git add plugins/ && git commit -m "feat(plugins): add common/pm/docs plugins, bump all versions to 1.0.0

Create 3 new plugin directories:
- sdlc-team-common: cross-cutting specialist agents
- sdlc-team-pm: project management agents
- sdlc-team-docs: documentation agents

Update all plugin versions from 0.1.0-stub to 1.0.0.

Part of Feature #71: Team Plugin Population"
```

---

### Task 2: Write Frontmatter Normalization Script

**Files:**
- Create: `tools/automation/normalize-agent-frontmatter.py`

This script standardizes agent frontmatter to the Claude Code plugin agent schema.

- [ ] **Step 1: Create the normalization script**

Create `tools/automation/normalize-agent-frontmatter.py`:

```python
#!/usr/bin/env python3
"""Normalize agent frontmatter to Claude Code plugin agent schema.

Reads agent markdown files, strips non-standard fields (color, maturity,
examples, Context, version, category, tags), adds missing fields (model,
tools), and condenses multi-line descriptions to single line.

Usage:
    python tools/automation/normalize-agent-frontmatter.py agents/core/sdlc-enforcer.md
    python tools/automation/normalize-agent-frontmatter.py --all    # process all mapped agents
    python tools/automation/normalize-agent-frontmatter.py --dry-run --all  # preview changes
"""

import argparse
import re
import sys
from pathlib import Path


# Fields to keep (in order)
KEEP_FIELDS = ["name", "description", "model", "tools"]

# Fields to strip
STRIP_FIELDS = {
    "color", "maturity", "examples", "Context",
    "version", "category", "tags",
}

# Defaults for missing fields
DEFAULTS = {
    "model": "sonnet",
    "tools": "Read, Glob, Grep, Bash",
}

# All agents that should be normalized (source paths relative to repo root)
AGENT_FILES = [
    # sdlc-core (already in plugin, normalize anyway for consistency)
    "agents/core/sdlc-enforcer.md",
    "agents/core/critical-goal-reviewer.md",
    "agents/testing/code-review-specialist.md",
    # sdlc-team-common
    "agents/core/solution-architect.md",
    "agents/core/deep-research-agent.md",
    "agents/testing/performance-engineer.md",
    "agents/core/observability-specialist.md",
    "agents/core/database-architect.md",
    "agents/core/agent-builder.md",
    "agents/core/pipeline-orchestrator.md",
    "agents/core/repo-knowledge-distiller.md",
    # sdlc-team-ai
    "agents/ai-development/ai-solution-architect.md",
    "agents/ai-development/prompt-engineer.md",
    "agents/ai-development/mcp-server-architect.md",
    "agents/ai-builders/rag-system-designer.md",
    "agents/ai-builders/context-engineer.md",
    "agents/ai-builders/orchestration-architect.md",
    "agents/ai-builders/ai-devops-engineer.md",
    "agents/ai-builders/ai-team-transformer.md",
    "agents/ai-development/a2a-architect.md",
    "agents/ai-development/agent-developer.md",
    "agents/ai-development/langchain-architect.md",
    "agents/ai-development/mcp-quality-assurance.md",
    "agents/ai-development/mcp-test-agent.md",
    "agents/testing/ai-test-engineer.md",
    # sdlc-team-fullstack
    "agents/core/frontend-architect.md",
    "agents/core/backend-architect.md",
    "agents/core/api-architect.md",
    "agents/core/devops-specialist.md",
    "agents/core/ux-ui-architect.md",
    "agents/core/mobile-architect.md",
    "agents/core/frontend-security-specialist.md",
    "agents/core/data-architect.md",
    "agents/testing/integration-orchestrator.md",
    "agents/core/github-integration-specialist.md",
    # sdlc-team-cloud
    "agents/core/cloud-architect.md",
    "agents/core/container-platform-specialist.md",
    "agents/core/sre-specialist.md",
    # sdlc-team-security
    "agents/core/security-architect.md",
    "agents/core/compliance-auditor.md",
    "agents/core/compliance-report-generator.md",
    "agents/core/enforcement-strategy-advisor.md",
    "agents/core/data-privacy-officer.md",
    # sdlc-team-pm
    "agents/project-management/agile-coach.md",
    "agents/project-management/delivery-manager.md",
    "agents/project-management/project-plan-tracker.md",
    "agents/project-management/team-progress-tracker.md",
    "agents/sdlc/retrospective-miner.md",
    # sdlc-team-docs
    "agents/documentation/technical-writer.md",
    "agents/documentation/documentation-architect.md",
    # sdlc-lang-python
    "agents/sdlc/language-python-expert.md",
    # sdlc-lang-javascript
    "agents/sdlc/language-javascript-expert.md",
]


def parse_frontmatter(content: str) -> tuple:
    """Parse YAML frontmatter from markdown content.

    Returns (frontmatter_dict, body_after_frontmatter, raw_frontmatter_text).
    """
    if not content.startswith("---"):
        return {}, content, ""

    # Find the closing ---
    end_idx = content.index("---", 3)
    raw_fm = content[3:end_idx].strip()
    body = content[end_idx + 3:].lstrip("\n")

    # Parse YAML-like frontmatter manually (avoid yaml dependency)
    fields: dict = {}
    current_key = None
    current_value_lines: list = []

    for line in raw_fm.split("\n"):
        # Check if this is a new top-level key
        key_match = re.match(r"^(\w[\w-]*)\s*:\s*(.*)", line)
        if key_match and not line.startswith("  ") and not line.startswith("\t"):
            # Save previous key
            if current_key:
                fields[current_key] = "\n".join(current_value_lines).strip()
            current_key = key_match.group(1)
            current_value_lines = [key_match.group(2)]
        elif current_key:
            current_value_lines.append(line)

    # Save last key
    if current_key:
        fields[current_key] = "\n".join(current_value_lines).strip()

    return fields, body, raw_fm


def normalize_description(desc: str) -> str:
    """Condense multi-line description to single line, max 250 chars."""
    # Remove YAML quoting
    desc = desc.strip("'\"")
    # Collapse whitespace and newlines
    desc = " ".join(desc.split())
    # Truncate if needed
    if len(desc) > 250:
        desc = desc[:247] + "..."
    return desc


def build_normalized_frontmatter(fields: dict) -> str:
    """Build normalized YAML frontmatter string."""
    lines = ["---"]

    # Name
    name = fields.get("name", "unknown")
    lines.append(f"name: {name}")

    # Description (single line, quoted if contains special chars)
    desc = normalize_description(fields.get("description", ""))
    if any(c in desc for c in ":{}[]|>&*!%@`#"):
        lines.append(f'description: "{desc}"')
    else:
        lines.append(f"description: {desc}")

    # Model
    model = fields.get("model", DEFAULTS["model"])
    lines.append(f"model: {model}")

    # Tools
    tools = fields.get("tools", DEFAULTS["tools"])
    if isinstance(tools, str):
        tools = tools.strip("'\"")
    lines.append(f"tools: {tools}")

    lines.append("---")
    return "\n".join(lines)


def normalize_file(filepath: Path, dry_run: bool = False) -> dict:
    """Normalize a single agent file. Returns change summary."""
    content = filepath.read_text(encoding="utf-8")
    fields, body, raw_fm = parse_frontmatter(content)

    if not fields:
        return {"file": str(filepath), "status": "skipped", "reason": "no frontmatter"}

    changes = []

    # Track what will change
    for field in STRIP_FIELDS:
        if field in fields:
            changes.append(f"strip {field}")

    if "model" not in fields:
        changes.append(f"add model={DEFAULTS['model']}")
    if "tools" not in fields:
        changes.append(f"add tools={DEFAULTS['tools']}")

    original_desc = fields.get("description", "")
    normalized_desc = normalize_description(original_desc)
    if original_desc != normalized_desc:
        changes.append("condense description")

    if not changes:
        return {"file": str(filepath), "status": "unchanged", "reason": "already normalized"}

    if dry_run:
        return {"file": str(filepath), "status": "would_change", "changes": changes}

    # Build normalized content
    new_fm = build_normalized_frontmatter(fields)
    new_content = new_fm + "\n\n" + body

    filepath.write_text(new_content, encoding="utf-8")
    return {"file": str(filepath), "status": "normalized", "changes": changes}


def main() -> None:
    parser = argparse.ArgumentParser(description="Normalize agent frontmatter")
    parser.add_argument("files", nargs="*", help="Agent files to normalize")
    parser.add_argument("--all", action="store_true", help="Process all mapped agents")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without writing")
    args = parser.parse_args()

    if args.all:
        files = [Path(f) for f in AGENT_FILES]
    elif args.files:
        files = [Path(f) for f in args.files]
    else:
        parser.print_help()
        sys.exit(1)

    results = []
    for f in files:
        if not f.exists():
            results.append({"file": str(f), "status": "error", "reason": "file not found"})
            continue
        results.append(normalize_file(f, dry_run=args.dry_run))

    # Report
    for r in results:
        status = r["status"]
        if status == "normalized":
            print(f"  NORMALIZED: {r['file']} ({', '.join(r['changes'])})")
        elif status == "would_change":
            print(f"  WOULD CHANGE: {r['file']} ({', '.join(r['changes'])})")
        elif status == "unchanged":
            print(f"  UNCHANGED: {r['file']}")
        elif status == "error":
            print(f"  ERROR: {r['file']} — {r['reason']}")
        else:
            print(f"  SKIPPED: {r['file']} — {r.get('reason', 'unknown')}")

    changed = sum(1 for r in results if r["status"] in ("normalized", "would_change"))
    unchanged = sum(1 for r in results if r["status"] == "unchanged")
    errors = sum(1 for r in results if r["status"] == "error")
    print(f"\nTotal: {len(results)} files — {changed} changed, {unchanged} unchanged, {errors} errors")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Verify syntax**

```bash
python3 -c "import ast; ast.parse(open('tools/automation/normalize-agent-frontmatter.py').read()); print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add tools/automation/normalize-agent-frontmatter.py
git commit -m "feat(tools): add agent frontmatter normalization script

Standardizes agent YAML frontmatter to Claude Code plugin schema:
- Strips non-standard fields (color, maturity, examples, etc.)
- Adds missing model and tools fields with defaults
- Condenses multi-line descriptions to single line

Part of Feature #71: Team Plugin Population"
```

---

### Task 3: Run Frontmatter Normalization on All 52 Agents

**Files:**
- Modify: 52 agent files in `agents/` (frontmatter only, body content preserved)

- [ ] **Step 1: Preview changes (dry run)**

```bash
python tools/automation/normalize-agent-frontmatter.py --dry-run --all
```

Expected: ~36 files will show "WOULD CHANGE" (those missing model/tools), ~16 will show "WOULD CHANGE" (stripping color/maturity/examples even if model/tools present). Review output to confirm no errors.

- [ ] **Step 2: Run normalization**

```bash
python tools/automation/normalize-agent-frontmatter.py --all
```

Expected: 52 files processed, most showing "NORMALIZED".

- [ ] **Step 3: Spot-check a few normalized files**

Check an agent that needed model+tools added:

```bash
head -6 agents/core/cloud-architect.md
```

Expected:
```
---
name: cloud-architect
description: Expert in multi-cloud strategy, service selection...
model: sonnet
tools: Read, Glob, Grep, Bash
---
```

Check an agent that was already complete:

```bash
head -6 agents/core/sdlc-enforcer.md
```

Expected: same 4-field format, no color/maturity/examples.

- [ ] **Step 4: Verify no agent body content was lost**

```bash
wc -l agents/core/sdlc-enforcer.md agents/core/cloud-architect.md agents/testing/performance-engineer.md
```

Files should still have substantial line counts (hundreds of lines). If any file is suspiciously short (under 20 lines), the body was lost — investigate.

- [ ] **Step 5: Run syntax validation**

```bash
python tools/validation/local-validation.py --syntax
```

Expected: passes.

- [ ] **Step 6: Commit**

```bash
git add agents/
git commit -m "refactor(agents): normalize frontmatter to Claude Code plugin schema

Standardize all 52 production agents:
- Strip non-standard fields: color, maturity, examples, Context, version, category, tags
- Add model: sonnet where missing (36 agents)
- Add tools: Read, Glob, Grep, Bash where missing (35 agents)
- Condense multi-line descriptions to single line

Part of Feature #71: Team Plugin Population"
```

---

### Task 4: Update release-mapping.yaml with All Agent Mappings

**Files:**
- Modify: `release-mapping.yaml`

- [ ] **Step 1: Read current release-mapping.yaml**

Read the file. It currently has sdlc-core mappings filled in and stub entries (empty arrays + commented future mappings) for team and lang plugins.

- [ ] **Step 2: Replace stub mappings with actual agent paths**

Replace the commented-out stub sections with real mappings. The complete `release-mapping.yaml` should have these agent entries for each plugin:

**sdlc-team-common:**
```yaml
sdlc-team-common:
  agents:
    - source: agents/core/solution-architect.md
    - source: agents/core/deep-research-agent.md
    - source: agents/testing/performance-engineer.md
    - source: agents/core/observability-specialist.md
    - source: agents/core/database-architect.md
    - source: agents/core/agent-builder.md
    - source: agents/core/pipeline-orchestrator.md
    - source: agents/core/repo-knowledge-distiller.md
```

**sdlc-team-ai:**
```yaml
sdlc-team-ai:
  agents:
    - source: agents/ai-development/ai-solution-architect.md
    - source: agents/ai-development/prompt-engineer.md
    - source: agents/ai-development/mcp-server-architect.md
    - source: agents/ai-builders/rag-system-designer.md
    - source: agents/ai-builders/context-engineer.md
    - source: agents/ai-builders/orchestration-architect.md
    - source: agents/ai-builders/ai-devops-engineer.md
    - source: agents/ai-builders/ai-team-transformer.md
    - source: agents/ai-development/a2a-architect.md
    - source: agents/ai-development/agent-developer.md
    - source: agents/ai-development/langchain-architect.md
    - source: agents/ai-development/mcp-quality-assurance.md
    - source: agents/ai-development/mcp-test-agent.md
    - source: agents/testing/ai-test-engineer.md
```

**sdlc-team-fullstack:**
```yaml
sdlc-team-fullstack:
  agents:
    - source: agents/core/frontend-architect.md
    - source: agents/core/backend-architect.md
    - source: agents/core/api-architect.md
    - source: agents/core/devops-specialist.md
    - source: agents/core/ux-ui-architect.md
    - source: agents/core/mobile-architect.md
    - source: agents/core/frontend-security-specialist.md
    - source: agents/core/data-architect.md
    - source: agents/testing/integration-orchestrator.md
    - source: agents/core/github-integration-specialist.md
```

**sdlc-team-cloud:**
```yaml
sdlc-team-cloud:
  agents:
    - source: agents/core/cloud-architect.md
    - source: agents/core/container-platform-specialist.md
    - source: agents/core/sre-specialist.md
```

**sdlc-team-security:**
```yaml
sdlc-team-security:
  agents:
    - source: agents/core/security-architect.md
    - source: agents/core/compliance-auditor.md
    - source: agents/core/compliance-report-generator.md
    - source: agents/core/enforcement-strategy-advisor.md
    - source: agents/core/data-privacy-officer.md
```

**sdlc-team-pm:**
```yaml
sdlc-team-pm:
  agents:
    - source: agents/project-management/agile-coach.md
    - source: agents/project-management/delivery-manager.md
    - source: agents/project-management/project-plan-tracker.md
    - source: agents/project-management/team-progress-tracker.md
    - source: agents/sdlc/retrospective-miner.md
```

**sdlc-team-docs:**
```yaml
sdlc-team-docs:
  agents:
    - source: agents/documentation/technical-writer.md
    - source: agents/documentation/documentation-architect.md
```

**sdlc-lang-python:**
```yaml
sdlc-lang-python:
  agents:
    - source: agents/sdlc/language-python-expert.md
```

**sdlc-lang-javascript:**
```yaml
sdlc-lang-javascript:
  agents:
    - source: agents/sdlc/language-javascript-expert.md
```

Remove all `# Future:` comments from the stub sections — they're no longer future.

- [ ] **Step 3: Verify YAML is valid**

```bash
python3 -c "import yaml; yaml.safe_load(open('release-mapping.yaml')); print('OK')" 2>/dev/null || python3 -c "
# Fallback if PyYAML not installed — basic syntax check
content = open('release-mapping.yaml').read()
assert '---' not in content or content.startswith('---'), 'unexpected --- in middle'
print('Basic check OK')
"
```

- [ ] **Step 4: Count total agent mappings**

```bash
grep -c "source: agents/" release-mapping.yaml
```

Expected: 55 (3 core + 52 new = 55 total agent source entries).

- [ ] **Step 5: Commit**

```bash
git add release-mapping.yaml
git commit -m "feat(release): map all 52 agents to team plugins in release-mapping.yaml

Complete agent-to-plugin mapping:
- sdlc-team-common: 8 agents
- sdlc-team-ai: 14 agents
- sdlc-team-fullstack: 10 agents
- sdlc-team-cloud: 3 agents
- sdlc-team-security: 5 agents
- sdlc-team-pm: 5 agents
- sdlc-team-docs: 2 agents
- sdlc-lang-python: 1 agent
- sdlc-lang-javascript: 1 agent

Part of Feature #71: Team Plugin Population"
```

---

### Task 5: Update setup-team Skill

**Files:**
- Modify: `skills/setup-team/SKILL.md`

- [ ] **Step 1: Read current setup-team skill**

```bash
cat skills/setup-team/SKILL.md
```

- [ ] **Step 2: Update the skill with new recommendations and agent rosters**

Edit `skills/setup-team/SKILL.md` to make these changes:

**a)** Update the recommendation table in Step 3 to include `sdlc-team-common`:

```markdown
3. **Map selection to recommended plugins:**

   | Selection | Plugins |
   |-----------|---------|
   | A. Full-stack | `sdlc-team-common`, `sdlc-team-fullstack` |
   | B. AI/ML | `sdlc-team-common`, `sdlc-team-ai`, `sdlc-lang-python` |
   | C. Cloud | `sdlc-team-common`, `sdlc-team-cloud` |
   | D. API | `sdlc-team-common`, `sdlc-team-fullstack`, `sdlc-team-cloud` |
   | E. Security | `sdlc-team-common`, `sdlc-team-security` |
   | F. Custom | User picks from list |
```

**b)** Add a new Step 5 (renumber subsequent steps) for PM and docs:

```markdown
5. **Ask about project management and documentation needs:**
   - "Do you need project management support (sprints, delivery tracking)?" → recommend `sdlc-team-pm`
   - "Do you need documentation architecture?" → recommend `sdlc-team-docs`
```

**c)** Add a new section before the install step showing agent rosters:

```markdown
6. **Present the recommendation with agent rosters:**

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
```

**d)** Update the formation mapping in the team-config.json section to include all formations:

```markdown
   The formation name maps from `agents/agent-compositions.yaml`:
   - Full-stack → `full-stack-developer`
   - AI/ML → `ai-system-expert`
   - Cloud → `cloud-native-architect`
   - API → `enterprise-architect`
   - Security → `compliance-specialist`
   - Custom → `custom`
```

- [ ] **Step 3: Commit**

```bash
git add skills/setup-team/SKILL.md
git commit -m "feat(skills): update setup-team with common/pm/docs and agent rosters

Add sdlc-team-common to all project type recommendations.
Add PM and docs plugin questions.
Show agent rosters when recommending plugins.

Part of Feature #71: Team Plugin Population"
```

---

### Task 6: Run Release — Copy All Agents to Plugin Directories

**Files:**
- Create: agent files in `plugins/sdlc-team-*/agents/`
- Modify: `plugins/sdlc-core/agents/` (update with normalized versions)

- [ ] **Step 1: Copy agents to sdlc-team-common**

```bash
mkdir -p plugins/sdlc-team-common/agents
cp agents/core/solution-architect.md plugins/sdlc-team-common/agents/
cp agents/core/deep-research-agent.md plugins/sdlc-team-common/agents/
cp agents/testing/performance-engineer.md plugins/sdlc-team-common/agents/
cp agents/core/observability-specialist.md plugins/sdlc-team-common/agents/
cp agents/core/database-architect.md plugins/sdlc-team-common/agents/
cp agents/core/agent-builder.md plugins/sdlc-team-common/agents/
cp agents/core/pipeline-orchestrator.md plugins/sdlc-team-common/agents/
cp agents/core/repo-knowledge-distiller.md plugins/sdlc-team-common/agents/
```

- [ ] **Step 2: Copy agents to sdlc-team-ai**

```bash
mkdir -p plugins/sdlc-team-ai/agents
cp agents/ai-development/ai-solution-architect.md plugins/sdlc-team-ai/agents/
cp agents/ai-development/prompt-engineer.md plugins/sdlc-team-ai/agents/
cp agents/ai-development/mcp-server-architect.md plugins/sdlc-team-ai/agents/
cp agents/ai-builders/rag-system-designer.md plugins/sdlc-team-ai/agents/
cp agents/ai-builders/context-engineer.md plugins/sdlc-team-ai/agents/
cp agents/ai-builders/orchestration-architect.md plugins/sdlc-team-ai/agents/
cp agents/ai-builders/ai-devops-engineer.md plugins/sdlc-team-ai/agents/
cp agents/ai-builders/ai-team-transformer.md plugins/sdlc-team-ai/agents/
cp agents/ai-development/a2a-architect.md plugins/sdlc-team-ai/agents/
cp agents/ai-development/agent-developer.md plugins/sdlc-team-ai/agents/
cp agents/ai-development/langchain-architect.md plugins/sdlc-team-ai/agents/
cp agents/ai-development/mcp-quality-assurance.md plugins/sdlc-team-ai/agents/
cp agents/ai-development/mcp-test-agent.md plugins/sdlc-team-ai/agents/
cp agents/testing/ai-test-engineer.md plugins/sdlc-team-ai/agents/
```

- [ ] **Step 3: Copy agents to sdlc-team-fullstack**

```bash
mkdir -p plugins/sdlc-team-fullstack/agents
cp agents/core/frontend-architect.md plugins/sdlc-team-fullstack/agents/
cp agents/core/backend-architect.md plugins/sdlc-team-fullstack/agents/
cp agents/core/api-architect.md plugins/sdlc-team-fullstack/agents/
cp agents/core/devops-specialist.md plugins/sdlc-team-fullstack/agents/
cp agents/core/ux-ui-architect.md plugins/sdlc-team-fullstack/agents/
cp agents/core/mobile-architect.md plugins/sdlc-team-fullstack/agents/
cp agents/core/frontend-security-specialist.md plugins/sdlc-team-fullstack/agents/
cp agents/core/data-architect.md plugins/sdlc-team-fullstack/agents/
cp agents/testing/integration-orchestrator.md plugins/sdlc-team-fullstack/agents/
cp agents/core/github-integration-specialist.md plugins/sdlc-team-fullstack/agents/
```

- [ ] **Step 4: Copy agents to sdlc-team-cloud**

```bash
mkdir -p plugins/sdlc-team-cloud/agents
cp agents/core/cloud-architect.md plugins/sdlc-team-cloud/agents/
cp agents/core/container-platform-specialist.md plugins/sdlc-team-cloud/agents/
cp agents/core/sre-specialist.md plugins/sdlc-team-cloud/agents/
```

- [ ] **Step 5: Copy agents to sdlc-team-security**

```bash
mkdir -p plugins/sdlc-team-security/agents
cp agents/core/security-architect.md plugins/sdlc-team-security/agents/
cp agents/core/compliance-auditor.md plugins/sdlc-team-security/agents/
cp agents/core/compliance-report-generator.md plugins/sdlc-team-security/agents/
cp agents/core/enforcement-strategy-advisor.md plugins/sdlc-team-security/agents/
cp agents/core/data-privacy-officer.md plugins/sdlc-team-security/agents/
```

- [ ] **Step 6: Copy agents to sdlc-team-pm**

```bash
mkdir -p plugins/sdlc-team-pm/agents
cp agents/project-management/agile-coach.md plugins/sdlc-team-pm/agents/
cp agents/project-management/delivery-manager.md plugins/sdlc-team-pm/agents/
cp agents/project-management/project-plan-tracker.md plugins/sdlc-team-pm/agents/
cp agents/project-management/team-progress-tracker.md plugins/sdlc-team-pm/agents/
cp agents/sdlc/retrospective-miner.md plugins/sdlc-team-pm/agents/
```

- [ ] **Step 7: Copy agents to sdlc-team-docs**

```bash
mkdir -p plugins/sdlc-team-docs/agents
cp agents/documentation/technical-writer.md plugins/sdlc-team-docs/agents/
cp agents/documentation/documentation-architect.md plugins/sdlc-team-docs/agents/
```

- [ ] **Step 8: Copy agents to language plugins**

```bash
mkdir -p plugins/sdlc-lang-python/agents
cp agents/sdlc/language-python-expert.md plugins/sdlc-lang-python/agents/

mkdir -p plugins/sdlc-lang-javascript/agents
cp agents/sdlc/language-javascript-expert.md plugins/sdlc-lang-javascript/agents/
```

- [ ] **Step 9: Update sdlc-core agents with normalized versions**

```bash
cp agents/core/sdlc-enforcer.md plugins/sdlc-core/agents/
cp agents/core/critical-goal-reviewer.md plugins/sdlc-core/agents/
cp agents/testing/code-review-specialist.md plugins/sdlc-core/agents/
```

- [ ] **Step 10: Verify agent counts per plugin**

```bash
for plugin in sdlc-core sdlc-team-common sdlc-team-ai sdlc-team-fullstack sdlc-team-cloud sdlc-team-security sdlc-team-pm sdlc-team-docs sdlc-lang-python sdlc-lang-javascript; do
  count=$(ls plugins/$plugin/agents/ 2>/dev/null | wc -l | tr -d ' ')
  echo "$plugin: $count agents"
done
```

Expected:
```
sdlc-core: 3 agents
sdlc-team-common: 8 agents
sdlc-team-ai: 14 agents
sdlc-team-fullstack: 10 agents
sdlc-team-cloud: 3 agents
sdlc-team-security: 5 agents
sdlc-team-pm: 5 agents
sdlc-team-docs: 2 agents
sdlc-lang-python: 1 agents
sdlc-lang-javascript: 1 agents
```

Total: 52 agents.

- [ ] **Step 11: Verify all agents have normalized frontmatter**

```bash
python3 -c "
import os
for root, dirs, files in os.walk('plugins'):
    for f in files:
        if f.endswith('.md') and '/agents/' in os.path.join(root, f):
            path = os.path.join(root, f)
            content = open(path).read()
            if not content.startswith('---'):
                print(f'WARN: {path} — no frontmatter')
            elif 'color:' in content[:500] or 'maturity:' in content[:500]:
                print(f'WARN: {path} — still has non-standard fields')
            elif 'model:' not in content[:500]:
                print(f'WARN: {path} — missing model field')
            else:
                pass  # OK
print('Agent frontmatter check complete')
"
```

Expected: no warnings.

- [ ] **Step 12: Commit**

```bash
git add plugins/
git commit -m "release: populate all team plugins with normalized agents (v1.0.0)

Copy 52 agents across 10 plugins:
- sdlc-core: 3 (updated with normalized frontmatter)
- sdlc-team-common: 8
- sdlc-team-ai: 14
- sdlc-team-fullstack: 10
- sdlc-team-cloud: 3
- sdlc-team-security: 5
- sdlc-team-pm: 5
- sdlc-team-docs: 2
- sdlc-lang-python: 1
- sdlc-lang-javascript: 1

Part of Feature #71: Team Plugin Population"
```

---

### Task 7: Update setup-team Skill in Plugin (Release Copy)

**Files:**
- Modify: `plugins/sdlc-core/skills/setup-team/SKILL.md`

- [ ] **Step 1: Copy updated setup-team skill to plugin**

```bash
cp skills/setup-team/SKILL.md plugins/sdlc-core/skills/setup-team/SKILL.md
```

- [ ] **Step 2: Commit**

```bash
git add plugins/sdlc-core/skills/setup-team/SKILL.md
git commit -m "release: update setup-team skill in plugin with team rosters

Part of Feature #71: Team Plugin Population"
```

---

### Task 8: Create Feature Proposal and Retrospective

**Files:**
- Create: `docs/feature-proposals/71-team-plugin-population.md`
- Create: `retrospectives/71-team-plugin-population.md`

- [ ] **Step 1: Create feature proposal**

Create `docs/feature-proposals/71-team-plugin-population.md`:

```markdown
# Feature Proposal: Team Plugin Population (Phase 2)

**Proposal Number:** 71
**Status:** In Progress
**Author:** Claude (AI Agent)
**Created:** 2026-04-03
**Target Branch:** `feature/team-plugin-population`

---

## Executive Summary

Populate all team plugins with production agents, normalize agent frontmatter to Claude Code plugin schema, and release v1.0.0 of the plugin family. Phase 1 built the scaffolding; Phase 2 fills it with 52 agents across 10 plugins.

---

## Motivation

### Problem Statement

Phase 1 created the plugin family with stub team plugins (empty shells with no agents). Teams can install plugins but get no specialist agents. 52 production agents exist in `agents/` but aren't distributed through the plugin system.

### User Stories

- As a developer, I want to install `sdlc-team-ai` and immediately get AI specialist agents
- As a team lead, I want setup-team to show me exactly which agents each plugin provides
- As a framework maintainer, I want all agents normalized to a consistent format

---

## Proposed Solution

1. Create 3 new plugins: sdlc-team-common, sdlc-team-pm, sdlc-team-docs
2. Write a frontmatter normalization script
3. Normalize all 52 agent files to Claude Code plugin schema
4. Extend release-mapping.yaml with all agent-to-plugin mappings
5. Copy agents into plugin directories
6. Update setup-team skill with agent rosters
7. Bump all versions to 1.0.0
8. Tag v1.0.0

### Acceptance Criteria

- All 10 plugins contain their assigned agents
- All agent frontmatter normalized (no color/maturity/examples, has model/tools)
- setup-team shows agent rosters per plugin
- All plugins at v1.0.0

---

## Success Criteria

- [ ] 52 agents distributed across 10 plugins
- [ ] All frontmatter normalized
- [ ] setup-team shows rosters
- [ ] v1.0.0 tagged

---

## Changes Made

| Action | File |
|--------|------|
| Create | `plugins/sdlc-team-common/`, `plugins/sdlc-team-pm/`, `plugins/sdlc-team-docs/` |
| Create | `tools/automation/normalize-agent-frontmatter.py` |
| Modify | 52 agent files (frontmatter normalization) |
| Modify | `release-mapping.yaml` (all agent mappings) |
| Modify | `skills/setup-team/SKILL.md` (rosters, common/pm/docs) |
| Modify | `plugins/.claude-plugin/marketplace.json` (versions, new plugins) |
```

- [ ] **Step 2: Create retrospective stub**

Create `retrospectives/71-team-plugin-population.md`:

```markdown
# Retrospective: Feature #71 — Team Plugin Population (Phase 2)

**Branch**: `feature/team-plugin-population`
**Date**: 2026-04-03

## What Went Well

- _To be completed after implementation_

## What Could Improve

- _To be completed after implementation_

## Lessons Learned

1. _To be completed after implementation_

## Changes Made

- _To be completed after implementation_

## Metrics

- **Agents normalized**: 52
- **Agents distributed**: 52
- **Plugins populated**: 10
- **New plugins created**: 3 (common, pm, docs)
```

- [ ] **Step 3: Commit**

```bash
git add docs/feature-proposals/71-team-plugin-population.md retrospectives/71-team-plugin-population.md
git commit -m "docs: add feature proposal and retrospective for team plugin population (#71)

Part of Feature #71: Team Plugin Population"
```

---

### Task 9: Verification and Final Steps

**Files:** None (verification only, plus retrospective update)

- [ ] **Step 1: Validate all plugin manifests**

```bash
python3 -c "
import json, os
for root, dirs, files in os.walk('plugins'):
    for f in files:
        if f.endswith('.json'):
            path = os.path.join(root, f)
            data = json.load(open(path))
            if 'plugin.json' in f:
                name = data['name']
                version = data['version']
                print(f'OK: {name} v{version}')
            elif 'marketplace.json' in f:
                print(f'OK: marketplace ({len(data[\"plugins\"])} plugins)')
"
```

Expected: 10 plugins at v1.0.0, marketplace with 10 entries.

- [ ] **Step 2: Count total agents in plugins**

```bash
find plugins -path '*/agents/*.md' | wc -l
```

Expected: 55 (3 core + 52 team/lang).

- [ ] **Step 3: Verify no stub versions remain**

```bash
grep -r "stub" plugins/ --include="*.json"
```

Expected: no output (all stubs replaced with 1.0.0).

- [ ] **Step 4: Run syntax validation**

```bash
python tools/validation/local-validation.py --syntax
```

Expected: passes.

- [ ] **Step 5: Update retrospective with results**

Edit `retrospectives/71-team-plugin-population.md` with actual observations from the implementation.

- [ ] **Step 6: Commit retrospective**

```bash
git add retrospectives/71-team-plugin-population.md
git commit -m "docs: complete retrospective for team plugin population (#71)"
```

- [ ] **Step 7: Push and create PR**

```bash
git push -u origin feature/team-plugin-population
gh pr create --title "feat: populate all team plugins with 52 agents (v1.0.0) (#71)" --body "$(cat <<'EOF'
## Summary
- **52 agents** distributed across 10 plugins (3 new: common, pm, docs)
- **Frontmatter normalized** on all agents to Claude Code plugin schema
- **setup-team skill** updated with agent rosters and common/pm/docs recommendations
- **All plugins at v1.0.0** — first stable release

## Agent Distribution
| Plugin | Agents |
|--------|--------|
| sdlc-core | 3 |
| sdlc-team-common | 8 |
| sdlc-team-ai | 14 |
| sdlc-team-fullstack | 10 |
| sdlc-team-cloud | 3 |
| sdlc-team-security | 5 |
| sdlc-team-pm | 5 |
| sdlc-team-docs | 2 |
| sdlc-lang-python | 1 |
| sdlc-lang-javascript | 1 |

## Test plan
- [ ] All plugin manifests valid at v1.0.0
- [ ] 55 agent files across plugins (3 core + 52 new)
- [ ] No stub versions remain
- [ ] Syntax validation passes
- [ ] CI pipeline passes
- [ ] Plugin installs and agents are discoverable

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```
