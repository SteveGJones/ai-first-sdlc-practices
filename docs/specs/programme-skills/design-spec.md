---
feature_id: programme-skills
module: P1.SP1.M1
granularity: design
---

# Design Specification: Programme-skills (Assured)

**Feature-id:** programme-skills
**Module:** P1.SP1.M1
**Granularity:** design
**Status:** Draft
**Author:** Phase F dogfood
**Created:** 2026-04-28

---

## Overview

Five design units correspond to the five Programme-skills SKILL.md files. Each unit
describes the control flow and delegation contract for one skill, operating as a thin
orchestration layer above the `sdlc_programme_scripts` substrate and gate validators.

---

## Design

### DES-programme-skills-001

`commission-programme` parses the `--level` argument (default `production`; valid
values `production`, `enterprise`) and validates input, exiting non-zero on invalid
values. It locates the plugin bundle directory via `$CLAUDE_PLUGIN_ROOT`, verifies
`manifest.yaml` is present, and delegates to
`sdlc_core_scripts.commission.installer.install_bundle` with `overwrite` set to the
result of `is_commissioned(team_config)`. After installation the skill constructs a
`CommissioningRecord` with the SDLC option (`programme`), level, UTC timestamp,
operator identity (`claude-agent`), and bundle version, then writes it via
`write_record(team_config, record)`. The skill emits a structured Done report listing
installed file count, key paths, commissioning record location, and next-step
instructions.

**satisfies:** REQ-programme-skills-001

### DES-programme-skills-002

`phase-init` accepts two positional arguments: `<phase>` (one of `requirements`,
`design`, `test`) and `<feature-id>` (matching `/^[a-z0-9][a-z0-9-]*$/`). It
constructs the target path `docs/specs/<feature-id>/<phase>-spec.md` and exits
non-zero if that file already exists. It resolves the template in priority order:
`.sdlc/templates/<phase>-spec.md` (project-installed) then
`$CLAUDE_PLUGIN_ROOT/templates/<phase>-spec.md` (plugin fallback), exiting non-zero
if neither exists. It copies the template to the target path via `sed` substitution
of `<feature-id>` placeholders, then prints the created path and a follow-up
`phase-gate` invocation hint.

**satisfies:** REQ-programme-skills-002

### DES-programme-skills-003

`phase-gate` accepts `<phase>` (one of `requirements`, `design`, `test`, `code`) and
`<feature-id>`, with an optional `[code-file-glob]` required when `<phase>` is `code`.
It dispatches to the corresponding gate function imported from
`sdlc_programme_scripts.programme.gates`: `requirements_gate`, `design_gate`,
`test_gate`, or `code_gate`. The `code_gate` path globs source files matching the
supplied pattern, concatenates their text, and passes it as `code_text`. The skill
prints `PASS: <gate-name>-gate for feature <feature-id>` and exits zero on pass, or
`FAIL: <gate-name>-gate for feature <feature-id>` followed by one line per error and
exits non-zero on failure.

**satisfies:** REQ-programme-skills-003

### DES-programme-skills-004

`phase-review` accepts `<phase>` (one of `requirements`, `design`, `test`) and
`<feature-id>`. It validates that `docs/specs/<feature-id>/<phase>-spec.md` exists,
exiting non-zero if absent. It creates `docs/specs/<feature-id>/reviews/` if not
present. It selects the reviewer agent by phase (`solution-architect` for requirements
and design; `backend-architect` for test) and constructs the output path
`reviews/<phase>-review-<reviewer-label>.md`. It dispatches the reviewer agent via the
Agent tool with a structured prompt covering coverage, soundness, completeness, and
out-of-scope concerns. After the dispatch it verifies the review file was created and
stages it for commit; if the file is absent it exits non-zero.

**satisfies:** REQ-programme-skills-004

### DES-programme-skills-005

`traceability-export` accepts `<format>` (one of `csv`, `markdown`) and `<feature-id>`,
with an optional `[output-path]` defaulting to
`docs/specs/<feature-id>/traceability.<ext>`. It calls
`sdlc_programme_scripts.programme.traceability.export_csv` or `export_markdown`
(as determined by `<format>`) against the feature directory. On `TraceabilityError` it
prints the error and exits non-zero. On success it writes the output to the resolved
path (creating parent directories as needed) and prints the output path and the row
count. No rows are silently dropped: any REQ-ID present in the requirements spec
appears in the output matrix, with `—` in DES or TEST columns when no satisfying entry
exists.

**satisfies:** REQ-programme-skills-005

---

## Out of scope

- Caching or memoising gate results across skill invocations — each skill invocation
  is stateless.
- Interactive prompts beyond the existing constitution-overwrite confirmation in
  `commission-programme` — all other decisions are resolved from arguments.
- Partial-phase rollback — the skills write atomically where possible; rollback on
  failure is out of scope for v0.1.
