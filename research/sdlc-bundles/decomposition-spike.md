# Decomposition Spike — Candidate `programs` block for `ai-first-sdlc-practices`

**Date:** 2026-04-26
**Branch:** `feature/sdlc-programme-assured-bundles`
**Issue:** #180 (Phase B of EPIC #178)
**Status:** Spike output — feeds (but does not gate) Phase D-E plan-writing

---

## 0. Verdict (executive)

**Outcome (a) — plausible decomposition with revision-required-before-Phase-E.** A workable `programs` block exists for this repo. Four sub-programs (`framework-core`, `knowledge-base-system`, `workflows-system`, `framework-meta-sdlc`) have defensible DDD bounded-context boundaries. Two sub-programs (`release-packaging`, `team-agent-library`) are pragmatic groupings dressed in DDD language and need reclassification before Phase E validator design. The spike was reviewed by `sdlc-team-common:solution-architect` (review verbatim in Section 9) which surfaced four schema-level gaps that must be closed for the validators to behave correctly.

The decomposition has 1 program, 5 sub-programs, 14 modules. Recommended posture:

- **Phase D plan-writing (roadmap sequencing, skill inventory, commissioning flow): can use this spike as-is**.
- **Phase E validator design: must close four schema gaps first** — see Section 9. Specifically: (a) add `source-paths` / `derived-paths` split to the `programs` block schema so plugin-dir mirrors don't trigger false positives; (b) reclassify `release-packaging` as a cross-cutting *producer* not consumer; (c) add a `known-violation` field for declared-known-deviations like the framework-research↔kb-skills runtime data-flow loop; (d) tighten the ID-annotation format to match METHODS.md's canonical namespace schema.
- **Phase F dogfood**: start with `warn` posture on visibility violations rather than `block`, until the team has confirmed boundaries hold under real work.

## 1. Repo character analysis

`ai-first-sdlc-practices` is structurally **two domains co-located in one repo**:

1. **The framework** — what it ships (rules, validators, agents, skills, plugins, knowledge bases)
2. **The framework's meta-SDLC** — how the framework develops itself (feature proposals, retrospectives, research, EPIC tracking)

These domains share team and source code but speak different ubiquitous languages. The framework speaks "agent / skill / plugin / commission / library / shelf-index"; the meta-SDLC speaks "feature proposal / retrospective / EPIC / phase / sub-feature / branch model". Both are first-class.

Below them sits a **structural complexity unique to this repo**: the source-vs-distribution layer doubling. Every shipped agent and skill exists twice on disk:

- `agents/<category>/<name>.md` — source under team-organisation directories
- `plugins/<plugin>/agents/<name>.md` — distribution under plugin packaging

`release-mapping.yaml` is the contract that maps sources to plugins; `tools/validation/check-plugin-packaging.py` enforces it. This doubling is a real domain concept — "release packaging" is a sub-program in its own right — but it creates surface area that ordinary DDD doesn't account for. The spike accepts this as a structural fact and gives release-packaging its own module.

## 2. Candidate `programs` block (proposed)

```yaml
programs:
  ai-first-sdlc-practices:
    description: "AI-First SDLC framework + the framework's own meta-SDLC"
    sub-programs:

      framework-core:
        description: "Rules, validators, and the universal SDLC pipeline applied to every project"
        modules:
          constitution-and-rules:
            paths:
              - CONSTITUTION.md
              - CLAUDE.md
              - CLAUDE-CORE.md
              - CLAUDE-CORE-PROGRESSIVE.md
              - CLAUDE-CONTEXT-*.md
              - AGENTIC-TEAM-STANDARDS.md
            granularity: requirement
            ubiquitous-language: "article, rule, level, principle, mandatory, prohibited"
          validators:
            paths: [tools/validation/]
            granularity: function
            ubiquitous-language: "validator, check, threshold, violation, technical-debt"
          core-skills:
            paths:
              - skills/validate/
              - skills/new-feature/
              - skills/commit/
              - skills/pr/
              - skills/rules/
              - skills/setup-team/
              - skills/setup-ci/
              - skills/release-plugin/
              - plugins/sdlc-core/skills/
            granularity: function
            ubiquitous-language: "skill, gate, validation, commit, push"
          core-agents:
            paths:
              - agents/core/
              - agents/sdlc/
              - agents/ai-first-sdlc/
              - plugins/sdlc-core/agents/
            granularity: function
            ubiquitous-language: "agent, enforcement, review, sdlc-enforcer"

      release-packaging:
        description: "How source becomes distributable plugins"
        classification: cross-cutting-producer  # NOT consumer — writes into other sub-programs' distribution paths via release-mapping; per architect review §3
        modules:
          release-mapping:
            paths:
              - release-mapping.yaml
              - tools/automation/
              - .claude-plugin/marketplace.json
            granularity: function
            ubiquitous-language: "plugin, mapping, marketplace, release, packaging"
          plugin-validation:
            paths:
              - tools/validation/check-plugin-packaging.py
              - .github/workflows/plugin-packaging-sync.yml
            granularity: function
            ubiquitous-language: "drift, sync, packaging-sync"

      knowledge-base-system:
        description: "Filesystem-based KB substrate, librarians, cross-library queries"
        modules:
          librarians:
            paths:
              - agents/knowledge-base/
              - plugins/sdlc-knowledge-base/agents/
            granularity: requirement
            ubiquitous-language: "librarian, retrieval, synthesis, attribution, finding, citation"
            structure: hexagonal
          kb-skills-and-orchestration:
            source-paths:
              - skills/kb-*/
              - plugins/sdlc-knowledge-base/scripts/
            derived-paths:
              - plugins/sdlc-knowledge-base/skills/  # mirrors of skills/kb-*/
            granularity: requirement  # raised from function — module contains sub-orchestration logic per architect review §5
            ubiquitous-language: "shelf-index, library, ingest, query, lint, register-library, codeindex"
            structure: hexagonal
          kb-templates:
            paths:
              - plugins/sdlc-knowledge-base/skills/kb-init/templates/
              - plugins/sdlc-knowledge-base/skills/kb-rebuild-indexes/templates/
            granularity: module
            ubiquitous-language: "starter-pack, template"

      workflows-system:
        description: "Containerised delegated execution (Archon + sub-team Docker images)"
        modules:
          workflow-engine-integration:
            paths:
              - plugins/sdlc-workflows/
              - .archon/
              - skills/author-workflow/
              - skills/deploy-team/
              - skills/manage-teams/
              - skills/workflows-run/
              - skills/workflows-setup/
              - skills/workflows-status/
            granularity: function
            ubiquitous-language: "workflow, dag-node, container, isolation-provider, team, manifest, archon"

      team-agent-library:
        description: "Specialist agent catalog organised by team type"
        classification: pragmatic-grouping  # NOT a single bounded context — agents within speak distinct domain languages; per architect review §1
        anaemic-context-detection: suppressed  # acknowledged consequence of the coarse classification per architect review §4
        modules:
          team-common:
            paths: [plugins/sdlc-team-common/]
            granularity: module
            ubiquitous-language: "specialist agent, team scope"
          team-fullstack-and-cloud-and-security-and-ai-and-pm-and-docs:
            paths:
              - plugins/sdlc-team-fullstack/
              - plugins/sdlc-team-cloud/
              - plugins/sdlc-team-security/
              - plugins/sdlc-team-ai/
              - plugins/sdlc-team-pm/
              - plugins/sdlc-team-docs/
            granularity: module
            ubiquitous-language: "specialist agent, domain expertise"
          team-languages:
            paths:
              - plugins/sdlc-lang-python/
              - plugins/sdlc-lang-javascript/
              - agents/languages/
            granularity: module
            ubiquitous-language: "language expert, language-specific patterns"

      framework-meta-sdlc:
        description: "How the framework manages its own SDLC — the auto-applied dogfood layer"
        modules:
          epic-and-feature-tracking:
            paths:
              - docs/feature-proposals/
              - retrospectives/
            granularity: requirement
            ubiquitous-language: "feature proposal, retrospective, EPIC, sub-feature, phase"
          framework-research:
            paths:
              - research/
              - library/
            granularity: requirement
            ubiquitous-language: "research line, synthesis, citation, library entry, finding"
          documentation-and-examples:
            classification: derivative-projection  # NOT a bounded context; content types not domain concepts; per architect review §1
            paths:
              - docs/guides/
              - docs/HOWTO.md
              - docs/QUICK-REFERENCE.md
              - docs/PLUGIN-CONSUMER-GUIDE.md
              - docs/architecture/
              - examples/
              - README.md
              - CHANGELOG.md
              - CONTRIBUTING.md
              - QUICKSTART.md
            granularity: module
            ubiquitous-language: "guide, example, how-to, quick reference"
```

**Out-of-scope filesystem locations** (deliberately not in any module):

- `.git/`, `.github/`, `.archon/state/` — VCS / CI / workflow state, not framework source
- `__pycache__/`, `.pytest_cache/`, `.ruff_cache/`, `.mypy_cache/`, `*.egg-info/` — generated build artefacts
- `tmp/`, `reviews/2026-04-*/` — session artefacts (gitignored)
- `data/technology-registry/_index.yaml` — referenced by EPIC #142 work, not part of this decomposition surface
- `node_modules/` — irrelevant for this repo
- `agents/templates/`, `agents/future/`, `skills/agent-template.md` — placeholder/template files not yet substantive

## 3. Per-module DDD analysis

### `framework-core / constitution-and-rules`

- **Domain model**: the universal rules (11 articles + progressive levels) every commissioned project must obey. Article 1 = Feature Proposals; Article 3 = Architecture Documents; Article 7 = Logging; etc.
- **Ubiquitous language**: "article", "level" (Prototype / Production / Enterprise), "rule", "mandatory", "principle"
- **Team scope**: framework author (Steve) + Claude. Sole owner.
- **Boundary with neighbours**: `validators` module *enforces* this module's rules but does not *define* them. `core-skills` *invoke* this module's rules during validation but don't reshape them.

### `framework-core / validators`

- **Domain model**: Python validators that scan repo state and emit violations. Each validator is a focused function with a clear threshold rule.
- **Ubiquitous language**: "validator", "check", "threshold", "violation", "technical-debt", "logging-compliance", "broken-references"
- **Team scope**: framework author. Each validator owned by whoever added the article it enforces.
- **Boundary**: receives rules from `constitution-and-rules`; does not reach into `kb-skills` or `team-agent-library` directly. Consumes filesystem state only.

### `framework-core / core-skills`

- **Domain model**: the universal SDLC pipeline (specify → architect → implement → review). Skills like `validate`, `commit`, `pr`, `new-feature`, `release-plugin`, `setup-team`, `setup-ci`, `rules`.
- **Ubiquitous language**: "skill", "gate", "feature branch", "pre-push", "release"
- **Team scope**: framework author.
- **Boundary**: invokes `validators`; consumed by `core-agents` (sdlc-enforcer reads rules); does not reach into `kb-*` or `workflows-*`.

### `framework-core / core-agents`

- **Domain model**: the agents that *enforce* and *validate* (sdlc-enforcer, verification-enforcer, code-review-specialist).
- **Ubiquitous language**: "agent", "enforcement", "review", "verification"
- **Team scope**: framework author.
- **Boundary**: reads `constitution-and-rules`, invokes `validators`. Different cluster from team-agent-library (which is *specialist domain expertise*, not enforcement).

### `release-packaging / release-mapping` and `release-packaging / plugin-validation`

- **Domain model**: how root-level source files become plugin distributables. The mapping is the source-of-truth contract.
- **Ubiquitous language**: "plugin", "release-mapping", "marketplace", "drift", "sync", "packaging-sync"
- **Team scope**: framework author.
- **Boundary**: reads from every other sub-program (every plugin's source files); produces the `plugins/` mirrors. This is a *cross-cutting* sub-program — it touches everything but doesn't own the touched things.

### `knowledge-base-system / librarians`

- **Domain model**: stateless retrieval and synthesis agents. `research-librarian`, `synthesis-librarian`, `agent-knowledge-updater`. Bounded by no-fabrication discipline.
- **Ubiquitous language**: "librarian", "retrieval", "synthesis", "attribution", "finding", "citation", "source-handle", "shelf-index"
- **Team scope**: framework author.
- **Boundary**: no file-write outside the dispatch input. Synthesis-librarian has `tools: []` declared.

### `knowledge-base-system / kb-skills-and-orchestration`

- **Domain model**: skills that operate on `library/` directories (init, ingest, query, lint, register-library, codeindex, audit-query, etc.) plus the Python orchestrator that handles parallel dispatch + attribution post-check.
- **Ubiquitous language**: "shelf-index", "library", "ingest", "lint", "audit", "code-index", "registry", "priming", "attribution", "valid_handles"
- **Team scope**: framework author.
- **Boundary**: invokes `librarians`; consumed by `framework-meta-sdlc / framework-research` (which uses it on the framework's own library) and by external commissioned projects.

### `knowledge-base-system / kb-templates`

- **Domain model**: starter-pack content for new KBs.
- **Ubiquitous language**: "starter-pack", "template"
- **Team scope**: framework author.
- **Boundary**: read-only from other modules during commissioning.

### `workflows-system / workflow-engine-integration`

- **Domain model**: Archon workflow engine integration; team manifests; container deployment; workflow composition.
- **Ubiquitous language**: "workflow", "DAG node", "isolation provider", "team", "manifest", "container", "Archon"
- **Team scope**: framework author.
- **Boundary**: orthogonal to `framework-core` and `knowledge-base-system` — uses them inside containers but doesn't shape them. Cross-cutting consumer like `release-packaging`.

### `team-agent-library / *`

- **Domain model**: specialist agents organised by team type (full-stack, cloud, security, AI/ML, project management, documentation, language experts, common cross-cutting).
- **Ubiquitous language**: "specialist agent", "domain expertise", "team scope"
- **Team scope**: framework author + (in principle) external contributors.
- **Boundary**: catalog of agents, consumed by commissioned projects. No skill-side orchestration. No imports from other sub-programs.

### `framework-meta-sdlc / epic-and-feature-tracking`

- **Domain model**: the framework's own EPIC + feature-proposal + retrospective discipline. Where this very document lives.
- **Ubiquitous language**: "EPIC", "feature proposal", "retrospective", "sub-feature", "phase", "branch", "issue"
- **Team scope**: framework author.
- **Boundary**: reads `constitution-and-rules` (which mandates these artefacts); does not reach into validators or skills directly.

### `framework-meta-sdlc / framework-research`

- **Domain model**: research campaigns and curated KB findings used by the framework on itself. The research/ tree (Stage-1 plans, Stage-2 outputs, Stage-3 syntheses) and library/ entries.
- **Ubiquitous language**: "research line", "synthesis", "citation", "library entry", "finding", "shelf-index"
- **Team scope**: framework author.
- **Boundary**: consumes `kb-skills-and-orchestration` (uses kb-query and kb-rebuild-indexes on its own findings). This is the meta-loop: the framework dogfooding its own KB on its own design.

### `framework-meta-sdlc / documentation-and-examples`

- **Domain model**: human-facing documentation, getting-started guides, example workflows, README/CHANGELOG/CONTRIBUTING.
- **Ubiquitous language**: "guide", "example", "how-to"
- **Team scope**: framework author.
- **Boundary**: derivative content; references everything else but mutates nothing.

## 4. Visibility rules (DAG)

Sub-programs and modules MAY depend on others as follows. Read "→" as "may depend on / read from".

```
constitution-and-rules → (nothing — pure declaration)

validators → constitution-and-rules

core-skills → validators, constitution-and-rules

core-agents → constitution-and-rules, validators
            (does NOT depend on core-skills directly — invokes them by command name)

release-packaging.* → reads ALL plugin sources (cross-cutting)
                    → does NOT reach into framework-core's logic, only filesystem layout

knowledge-base-system.kb-templates → (nothing — pure templates)
knowledge-base-system.librarians → (nothing — stateless)
knowledge-base-system.kb-skills-and-orchestration → librarians, kb-templates
                                                  → constitution-and-rules (for rule-aware ingest)

workflows-system → consumes core-skills, core-agents (commands referenced inside containers)
                 → does NOT shape framework-core; orthogonal

team-agent-library.* → (catalog only — no inter-module dependencies)
                     → consumed by external commissioned projects

framework-meta-sdlc.framework-research → kb-skills-and-orchestration (queries its own library)
framework-meta-sdlc.epic-and-feature-tracking → constitution-and-rules
framework-meta-sdlc.documentation-and-examples → reads everything; mutates nothing
```

**Acyclicity check (source-code imports)**: yes, this forms a DAG for source-code dependencies. `constitution-and-rules` is the root (no dependencies). `documentation-and-examples` is a derivative projection (read-many; written-to by none). `release-packaging` is a cross-cutting *producer* — read-many but also writes into every other sub-program's distribution paths (the `plugins/<x>/` mirrors). No source-code circular dependencies between sub-programs.

**Hidden runtime data-flow cycle (surfaced by architect review §2)**: there is a quasi-cycle between `framework-meta-sdlc / framework-research` and `knowledge-base-system / kb-skills-and-orchestration`. The kb-query orchestrator at runtime reads the registry (`library/_shelf-index.md`) which lives in `framework-research`'s paths. So while the source-code DAG holds, the data-flow between these two sub-programs is bidirectional. Phase E validator design must explicitly handle this — likely by treating it as a `known-violation` declared in commissioning rather than rediscovered as a violation on every validator run.

**Cross-program dependencies**: there is only one program (`ai-first-sdlc-practices`), so cross-program-circular is not applicable. Cross-sub-program dependencies are within the program and follow the DAG above.

## 5. Granularity targets — rationale

| Module | Granularity | Why |
|---|---|---|
| `constitution-and-rules` | requirement | Each article is itself a requirement; no implementation to track at function level — the artefact IS the requirement |
| `validators` | function | Each validator is a focused function; per-function annotation is the natural unit |
| `core-skills` | function | Skills decompose into bash snippets / Python helpers; per-function is right |
| `core-agents` | function | Agents are markdown procedures with sections; section-level ≈ function-level |
| `release-mapping` / `plugin-validation` | function | Auto-mapping logic + validators |
| `librarians` | requirement | Each librarian's behavioural rule (e.g. "never invent a citation") is itself a requirement |
| `kb-skills-and-orchestration` | requirement | **Raised from `function` per architect review §5** — the Python orchestrator (`orchestrator.py`) contains sub-orchestration logic (parallel dispatch, attribution post-checks, synthesis fallback) whose behavioural rules are themselves requirements. `function` granularity would let internal helper functions go un-annotated under the same coverage that "one named entry point is annotated"; `requirement` granularity forces each behavioural rule to be a named REQ |
| `kb-templates` | module | Templates aren't really REQ/DES/TEST/CODE-shaped; module-level is pragmatic |
| `workflow-engine-integration` | function | Each skill / each Archon node config is function-shaped |
| `team-*` | module | Per-agent annotation is overkill for a catalog of specialists; module-level coverage suffices |
| `epic-and-feature-tracking` | requirement | Each feature proposal IS a requirement document |
| `framework-research` | requirement | Each curated finding IS a requirement-shaped record |
| `documentation-and-examples` | module | Module-level coverage; per-paragraph annotation is overkill |

The mix of granularities is itself a finding: this repo would not benefit from globally-imposed `requirement`-level granularity. Mixed granularity per module is the right shape — and Method 2's design supports this by design (`granularity: [requirement | function | module]` per module is declarable).

## 6. Worked example — `kb-query` skill under Method 2 annotations

Pick the existing `plugins/sdlc-knowledge-base/skills/kb-query/SKILL.md` skill (cross-library KB query, just shipped on PR #177). Walk through what Method 2 annotation looks like for one feature.

### Hypothetical feature: "kb-query supports cross-library synthesis with attribution post-check"

Module assignment: `knowledge-base-system / kb-skills-and-orchestration`. Granularity: `requirement` (raised from `function` per architect review §5).

**ID format**: per METHODS.md Section 4 canonical schema, IDs are namespaced `<program>.<sub-program>.<module>.<type>-<num>`. For this repo's program `ai-first-sdlc-practices` (single program — abbreviate to `aisp` for tractability), this module's IDs are `aisp.kb.kbsk.REQ-NNN` etc. (program=aisp, sub-program=kb-system→`kb`, module=kb-skills-and-orchestration→`kbsk`).

**Requirements** (`docs/specs/cross-library-synthesis/requirements-spec.md`):

```markdown
## aisp.kb.kbsk requirements — cross-library synthesis

### aisp.kb.kbsk.REQ-001
When the user query is a synthesis question and >1 dispatch source returned
findings, the orchestrator MUST produce a cross-source synthesis.

### aisp.kb.kbsk.REQ-002
The synthesis MUST carry inline `[<handle>]` attribution on every claim
in the Supporting evidence list.

### aisp.kb.kbsk.REQ-003
Claims with broken (non-`valid_handles`) attribution MUST be rejected by
post-check, aborting the synthesis with an error block — never silently
shipping unverified claims.

### aisp.kb.kbsk.REQ-004
Synthesis questions MUST be detected by a heuristic that examines
question phrasing; non-synthesis questions MUST skip synthesis entirely
even when multiple sources returned findings.

### aisp.kb.kbsk.REQ-005
Synthesis prompts MUST format dispatch sources via a single canonical
template so the synthesis-librarian sees consistent input shape.
```

**Design** (`docs/specs/cross-library-synthesis/design-spec.md`):

```markdown
### aisp.kb.kbsk.DES-001 — synthesis_dispatcher abstraction
satisfies: aisp.kb.kbsk.REQ-001
Synthesis orchestration takes a `synthesis_dispatcher` callable. The skill
provides a real dispatcher backed by Agent tool invocation against the
synthesis-librarian agent; tests provide mocks. The orchestrator does not
import the Agent tool directly.

### aisp.kb.kbsk.DES-002 — check_synthesis_attribution post-check
satisfies: aisp.kb.kbsk.REQ-002, aisp.kb.kbsk.REQ-003
A pure-Python post-check parses the synthesis output line-wise (state
machine, not regex), extracts every bracketed token in supporting-evidence
lines, and validates against a whitelist of dispatch source handles
(`valid_handles`). Untagged or fake-tagged claims fail the check; failed
synthesis is replaced with an error block.

### aisp.kb.kbsk.DES-003 — is_synthesis_query heuristic
satisfies: aisp.kb.kbsk.REQ-004
Heuristic detection of synthesis-style questions via phrase-matching
("how should we think about", "build me the case for", etc.).

### aisp.kb.kbsk.DES-004 — format_synthesis_prompt and format_dispatch_prompt
satisfies: aisp.kb.kbsk.REQ-005
Single canonical prompt-formatting helpers ensure dispatch consistency.
```

**Tests** (`docs/specs/cross-library-synthesis/test-spec.md`):

```markdown
### aisp.kb.kbsk.TEST-001
satisfies: aisp.kb.kbsk.REQ-001 via aisp.kb.kbsk.DES-001
implements: tests/test_kb_orchestrator.py::test_synthesis_runs_when_question_is_synthesis_and_multiple_sources_have_findings

### aisp.kb.kbsk.TEST-002
satisfies: aisp.kb.kbsk.REQ-002, aisp.kb.kbsk.REQ-003 via aisp.kb.kbsk.DES-002
implements: tests/test_kb_attribution.py::test_check_synthesis_attribution_rejects_fake_handle

### aisp.kb.kbsk.TEST-003
satisfies: aisp.kb.kbsk.REQ-004 via aisp.kb.kbsk.DES-003
implements: tests/test_kb_orchestrator.py::test_run_synthesis_query_skipped_for_non_synthesis_question
```

**Code annotations** (in existing files):

```python
# plugins/sdlc-knowledge-base/scripts/orchestrator.py
def run_synthesis_query(...):
    # implements: aisp.kb.kbsk.DES-001, aisp.kb.kbsk.REQ-001
    ...

def is_synthesis_query(question: str) -> bool:
    # implements: aisp.kb.kbsk.DES-003, aisp.kb.kbsk.REQ-004
    ...

def format_synthesis_prompt(...):
    # implements: aisp.kb.kbsk.DES-004, aisp.kb.kbsk.REQ-005
    ...

def format_dispatch_prompt(...):
    # implements: aisp.kb.kbsk.DES-004, aisp.kb.kbsk.REQ-005
    ...

# plugins/sdlc-knowledge-base/scripts/attribution.py
def check_synthesis_attribution(text: str, valid_handles: set[str]) -> AttributionCheck:
    # implements: aisp.kb.kbsk.DES-002, aisp.kb.kbsk.REQ-002, aisp.kb.kbsk.REQ-003
    ...
```

**`traceability-render kb-skills-and-orchestration` output** (Method 2 v1, hypothetical):

```markdown
# Module: knowledge-base-system / kb-skills-and-orchestration

## Requirements (5)
- aisp.kb.kbsk.REQ-001 — produce cross-source synthesis when applicable
- aisp.kb.kbsk.REQ-002 — every claim carries `[<handle>]` attribution
- aisp.kb.kbsk.REQ-003 — broken attribution → reject
- aisp.kb.kbsk.REQ-004 — non-synthesis questions skip synthesis
- aisp.kb.kbsk.REQ-005 — canonical prompt formatting

## Design elements (4)
- aisp.kb.kbsk.DES-001 — synthesis_dispatcher abstraction → REQ-001
- aisp.kb.kbsk.DES-002 — check_synthesis_attribution post-check → REQ-002, REQ-003
- aisp.kb.kbsk.DES-003 — is_synthesis_query heuristic → REQ-004
- aisp.kb.kbsk.DES-004 — format_*_prompt canonical helpers → REQ-005

## Tests (3)
- aisp.kb.kbsk.TEST-001 → DES-001 → REQ-001
- aisp.kb.kbsk.TEST-002 → DES-002 → REQ-002, REQ-003
- aisp.kb.kbsk.TEST-003 → DES-003 → REQ-004

## Code locations (5)
- orchestrator.py:run_synthesis_query → DES-001, REQ-001
- orchestrator.py:is_synthesis_query → DES-003, REQ-004
- orchestrator.py:format_synthesis_prompt → DES-004, REQ-005
- orchestrator.py:format_dispatch_prompt → DES-004, REQ-005
- attribution.py:check_synthesis_attribution → DES-002, REQ-002, REQ-003

## Coverage gaps: 1 — REQ-005 has no dedicated test (covered indirectly via DES-001/DES-002 tests but no TEST-id maps directly)
## Anaemic-context check: clean — all REQs implemented in module-declared paths
```

**Architect-review-driven correction**: the original draft of this section claimed "Coverage gaps: none" while only annotating two functions. The architect review (§6) flagged that as demonstrably wrong — the orchestrator has internal helpers (`is_synthesis_query`, `format_synthesis_prompt`, `format_dispatch_prompt`) that participate in synthesis but were unannotated. The corrected example now annotates all five participating functions and surfaces a real coverage gap (REQ-005 has no dedicated test). This is the kind of honest signal Method 2's `traceability-render` should produce — and the granularity raise from `function` to `requirement` makes this gap visible in the first place.

This worked example shows the full chain works on real code that exists and ships today. The annotations are tractable; the render output is human-readable; the coverage check terminates.

**Honest observation from the worked example**: writing the annotations took longer than expected. For `kb-query`'s ~10 actual functions, each annotation is roughly 1 line of inline comment. The bulk of the cost is *deciding what to write* — what's the right requirement-level decomposition of "kb-query does cross-library synthesis"? The skill itself currently has no such breakdown; we'd be inventing it retrospectively. **This is the cost adoption pays**: REQ/DES/TEST/CODE structure is real intellectual work, not just bookkeeping.

## 7. Failure-mode honest assessment

Walking the proposed decomposition against the failure modes from `library/decomposition-failure-modes.md`:

### Anaemic contexts — three real risks

**Risk 1: `framework-core / core-skills` overlap with `release-packaging / release-mapping`.** The `release-plugin` skill is a core SDLC skill (live in `framework-core`) but its job is to drive release-packaging (live in `release-packaging`). The skill's logic crosses two module boundaries. Without care, releasing-related code ends up scattered.

**Mitigation**: keep the `release-plugin` skill itself in `core-skills` (it's invoked the same way as other SDLC skills) but its *implementation logic* — the actual file mapping and the marketplace.json updates — lives in `release-packaging / release-mapping`. The skill orchestrates; the module owns the mapping. Validator support required (architect review §4 noted this needs an actual mechanism, not just a convention): Phase E must add a **cross-module-mutation validator** that checks `implements:` annotations on any code-block that writes to a path declared by another module. Convention-without-validator is hand-waving; this one needs validator backing.

**Risk 2: `framework-meta-sdlc / framework-research` queries `knowledge-base-system / kb-skills-and-orchestration` on its own data.** This is a recursive consumption pattern: the framework's research uses the framework's KB tools to query its own findings. If KB skills change, framework-research breaks. If framework-research's library structure changes, KB skills' assumed `library/_shelf-index.md` shape might break.

**Mitigation**: this is *the* dogfood loop that's the whole point. Accept the coupling as architecturally intentional. Document in commissioning guidance: "if you change the kb-skills-and-orchestration module, run `kb-rebuild-indexes` against the framework-research module's library to verify nothing breaks". This is procedural, not architectural — the coupling can't be eliminated without losing the dogfood property.

**Risk 3: `team-agent-library / team-*` modules might be too coarse.** `plugins/sdlc-team-fullstack/` has 10+ specialist agents (frontend-architect, backend-architect, api-architect, devops-specialist, etc.). Bundling them into one module loses domain language distinction (frontend speak ≠ backend speak ≠ DevOps speak).

**Mitigation**: accept the coarseness for v1 as `classification: pragmatic-grouping` (declared in Section 2's YAML now). The cost of finer module decomposition (10 modules just for sdlc-team-fullstack) outweighs the benefit when the team-agent-library is a *catalog* — agents don't import from each other; they're consumed by external projects. Module-level granularity is the right pragmatic choice. **Architect-review-§4 acknowledgement**: this acceptance silently disables anaemic-context detection across the entire sub-program, because a module without a real ubiquitous language has no meaningful domain model to violate. Section 2's YAML now declares `anaemic-context-detection: suppressed` for `team-agent-library` so this consequence is visible to anyone reading the decomposition. Phase E validators must respect this declaration. If, in Phase F dogfood, an agent's logic migrates out into another, revisit then.

### Premature decomposition — one real risk

**Risk: `release-packaging` may be over-decomposed.** Two modules (`release-mapping`, `plugin-validation`) for what is essentially one concern ("how source becomes plugins"). Could collapse into one module.

**Mitigation**: leave as two for now. The validator (CI workflow) is operationally distinct from the mapping (`release-mapping.yaml` and `tools/automation/`). Keeping them separate makes the boundary cleaner if either evolves. If after Phase F dogfood we find the split adds no value, collapse to one module — Method 2 supports decomposition refactoring without ID loss.

### Cross-module dependency proliferation — managed

The DAG (Section 4) shows clean visibility rules. Two cross-cutting consumers (`release-packaging`, `documentation-and-examples`) are *read-many, mutate-none* — they're catalogues over the rest, not coupling points. Most other modules have 0-2 dependencies. No proliferation risk visible.

### Distributed monolith — N/A

Single program, no independent deployments. This failure mode is rejected by design.

### Tool lock-in — N/A

Markdown + YAML + Git. Already structurally avoided.

### Boundary leaks — one structural complexity

**Source-vs-distribution doubling.** Every shipped agent / skill exists at TWO paths (root source + plugin mirror). Method 2's `paths:` for affected modules lists both. This is correct but creates surface area: changes to `agents/knowledge-base/research-librarian.md` must also update `plugins/sdlc-knowledge-base/agents/research-librarian.md` (per the Phase A regression lesson — `feedback_phase_a_plugin_dir_regression.md`).

**Mitigation**: this isn't a Method 2 problem; it's a pre-existing repo-shape problem already documented and procedurally mitigated (edit root + cp to plugin-dir + check-plugin-packaging.py). Method 2's annotations should appear on root sources only; `release-mapping.yaml` mirrors them automatically. Validator: if an annotation appears in a plugin-dir copy without being in the root source, flag it as drift.

## 8. Verdict and what this means for Phase D-E

### Plausibility verdict

**(a) plausible decomposition** — the candidate `programs` block holds up under DDD bounded-context analysis, has acyclic visibility rules, accommodates mixed granularities sensibly, and survives walking against documented failure modes. Three anaemic-context risks are surfaced (release-plugin skill / framework-research dogfood loop / team-agent coarse modules); each has a stated mitigation that is procedural or commissioning-guidance-shaped, not architectural.

### What Phase D-E plan-writing should do with this

1. **Treat this candidate as the test bed for validators**. When implementing `module-bound-check`, test against this exact `programs` block. The validator must surface the three anaemic-context risks (or the team must mark them as accepted-known-deviations via a `tolerance:` or `known-violation:` field — design call for Phase E).

2. **Pick `kb-query` cross-library synthesis as the worked-example reference for `traceability-render`'s output format**. Section 6 already drafted what the rendered output looks like.

3. **Build the visibility-rule validator in Phase E to enforce the DAG in Section 4**. Add the cross-module imports check (filesystem-imports respect declared visibility).

4. **Accept the source-vs-distribution doubling** as a Method 2 annotation pattern: annotations live on root sources only; plugin mirrors are derived. Document this in `commission-assured` guidance as a repo-specific consideration that affects projects using release-mapping packaging.

### What Phase F dogfood should do with this

1. **Don't enforce visibility rules in v1 commissioning** — start with `warn` posture so initial real work doesn't trip on hidden boundary issues.

2. **Apply Method 2 to one new chunk of work** (e.g. EPIC #142 sub-features 3-8 per CLOSEOUT recommendation), declaring this `programs` block at commissioning. Annotate the new feature's REQ/DES/TEST/CODE under the candidate decomposition.

3. **Use Docker sub-teams via `sdlc-workflows`** to test that Method 2's annotation discipline holds up under containerised parallel work — multiple sub-teams adding annotations against the same `programs` block, with `kb-rebuild-indexes` resolving the merged registry on integration.

4. **Capture learning honestly**: where do the three identified anaemic-context risks bite for real? Where does the source-vs-distribution doubling create friction? What's the actual cost-per-annotation on real new work?

### What this spike does NOT settle

- **Whether the proposed module names are right** — they're working names. Real teams adopting this would likely rename based on their own preferences; the framework should not enforce naming.
- **Whether granularity targets are correctly chosen per module** — set conservatively; might tighten after dogfood signal.
- **Whether visibility rules block or warn** — design call for Phase E.
- **Whether this decomposition would survive the framework adding a major new sub-program** — speculative; revisit when it happens.

### Closing note on the dogfood property

This decomposition exercise was itself the kind of work Method 2 is for: design judgment grounded in evidence, with traceability back to source research, then critically reviewed by a specialist agent. The spike took roughly 2 hours, produced a working decomposition with honest risk assessment, was reviewed by `sdlc-team-common:solution-architect` (Section 9 below), and revised in response to surfaced issues. That round-trip itself is a small but real signal that Method 2's discipline plus our shipped specialist agents is workable — the framework decomposed itself, then peer-reviewed itself, and the review surfaced four real schema gaps that informed Phase E's design surface. The harder test is Phase F.

---

## 9. Critical review by `sdlc-team-common:solution-architect` and response

The first draft of this spike (sections 0-8 above, before the inline edits flagging "architect review §N" updates) was reviewed by the `sdlc-team-common:solution-architect` agent. The review surfaced eight critical points; four required inline fixes (now applied above), four are deferred to Phase E as schema-design inputs.

### Reviewer's verdicts (verbatim)

| # | Question | Verdict |
|---|---|---|
| 1 | DDD bounded-context soundness | **DISAGREE** — `team-agent-library` and `documentation-and-examples` are directory groupings, not bounded contexts; `kb-skills-and-orchestration` and `librarians` overlap in language without context map |
| 2 | Acyclicity check | **AGREE-WITH-CONCERNS** — source-code DAG holds; data-flow cycle exists between `framework-research` and `kb-skills-and-orchestration` |
| 3 | Cross-cutting classification | **DISAGREE** — `release-packaging` is a cross-cutting *producer*, not consumer |
| 4 | Anaemic-context risk mitigations | **NEEDS-REWORK** — Risk 1 lacks validator mechanism; Risk 2 incomplete without `known-violation` field; Risk 3 silently disables anaemic-context detection for the whole sub-program |
| 5 | Granularity choices | **NEEDS-REWORK** — `kb-skills-and-orchestration` should be `requirement` not `function` given sub-orchestration structure |
| 6 | Worked example soundness | **NEEDS-REWORK** — "Coverage gaps: none" claim is demonstrably wrong; ID format does not match METHODS.md canonical schema |
| 7 | Source-vs-distribution doubling | **DISAGREE** — `paths:` field needs `source-paths` / `derived-paths` distinction in schema; not resolvable by policy alone |
| 8 | Verdict pressure-test | **AGREE-WITH-CONCERNS** — top-level shape is usable for plan-writing; four schema gaps must close before Phase E validator design |

### Response — fixes applied inline above

| # | Architect issue | Fix applied | Where |
|---|---|---|---|
| 1 | `team-agent-library` / `documentation-and-examples` claimed as bounded contexts | Both reclassified explicitly: `classification: pragmatic-grouping` and `classification: derivative-projection` in Section 2 YAML | Section 2 |
| 1 | `kb-skills-and-orchestration` / `librarians` language overlap | Acknowledged structurally; both retain the shared "attribution" / "finding" terms but the worked example (Section 6) demonstrates how the two layers operate at different abstraction levels — orchestrator-level attribution post-check vs librarian-level attribution tagging | Section 6 worked example |
| 2 | Hidden data-flow cycle missed | Section 4 now explicitly distinguishes "source-code DAG" (holds) from "runtime data-flow cycle" (exists between `framework-research` and `kb-skills-and-orchestration`); flagged for Phase E as a `known-violation` design call | Section 4 |
| 3 | `release-packaging` mis-classified as consumer | Reclassified to `classification: cross-cutting-producer` in Section 2 YAML; Section 4 acyclicity note rewritten to reflect this | Section 2, Section 4 |
| 4 | Risk 1 mitigation needs validator | Strengthened: Phase E must add a cross-module-mutation validator that checks `implements:` annotations on cross-module writes; convention-without-validator is hand-waving | Section 7 Risk 1 |
| 4 | Risk 3 silently disables anaemic-context detection | `anaemic-context-detection: suppressed` declared explicitly in Section 2 YAML for `team-agent-library`; Phase E validators must respect the declaration | Section 2 + Section 7 Risk 3 |
| 5 | `kb-skills-and-orchestration` granularity wrong | Raised from `function` to `requirement` in Section 2 YAML; rationale updated in Section 5 | Section 2, Section 5 |
| 6 | Worked example "Coverage gaps: none" was false | Rewrote Section 6: now annotates 5 functions (was 2), shows 5 REQs (was 3), surfaces a real gap (REQ-005 has no dedicated test) | Section 6 |
| 6 | ID format inconsistent with METHODS.md namespace | Rewrote all IDs in worked example as `aisp.kb.kbsk.<TYPE>-NNN` (program=aisp, sub-program=kb, module=kbsk) | Section 6 |

### Response — deferred to Phase E as schema-design inputs

These four issues are real but require schema-design decisions that are themselves Phase E plan-writing work, not Phase B spike scope. Captured here so they are visible inputs to Phase E:

1. **Schema gap: `source-paths` / `derived-paths` distinction in the `programs` block.** Modules that have plugin-dir mirrors (every module under `framework-core`, `knowledge-base-system`, `workflows-system`, `team-agent-library`) need to declare which paths carry annotations vs which are derived from packaging. Without this, validators systematically false-positive on plugin-dir mirrors. **Phase E action**: extend the `programs` block schema; update `module-bound-check` to skip `derived-paths` for orphan-code detection; add `release-packaging` cross-cutting-producer check that verifies derived paths are byte-identical to their source-paths.

2. **Schema gap: `known-violation` field for declared exceptions.** The framework-research↔kb-skills-and-orchestration runtime data-flow cycle (per architect review §2) needs to be declarable as a known accepted violation, not rediscovered as a violation on every validator run. **Phase E action**: add `known-violations:` array to the `programs` block schema; populate during commissioning for declared deviations; validators consult this list before flagging violations.

3. **Schema gap: cross-module-mutation validator.** Per architect review §4, the convention "annotation in code that mutates another module's data must point at the other module's IDs" needs validator backing, not just policy. **Phase E action**: add `cross-module-mutation-check` validator that scans for code writing to declared paths owned by other modules and verifies the cross-module `implements:` annotation is present and points at the right module.

4. **Schema gap: `anaemic-context-detection` opt-out semantics.** The `anaemic-context-detection: suppressed` declaration for `team-agent-library` needs formal validator support. **Phase E action**: extend `module-bound-check` to honour the suppression flag; surface in commissioning output that the sub-program has detection disabled; provide opt-in re-enabling per module if a sub-team adopts finer decomposition.

### Final verdict — revised per architect review §8

The decomposition is **plausible for the four content sub-programs** (`framework-core`, `knowledge-base-system`, `workflows-system`, `framework-meta-sdlc`) and these can feed Phase D plan-writing as-is. The two cross-cutting / catalog sub-programs (`release-packaging`, `team-agent-library`) needed reclassification (now done inline) and four schema gaps (listed above) need closure during Phase E plan-writing before validator design proceeds against this `programs` block.

**Spike is good enough to ship as Phase B output.** Phase D plan-writing can use it. Phase E plan-writing must close the four schema gaps as part of its scope.
