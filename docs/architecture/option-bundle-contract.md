# Option Bundle Contract

**Version:** 1
**Status:** Draft (Phase C of EPIC #178)
**Authoritative for:** Programme bundle (#103), Assured bundle (#104), and future bundles (Solo #100, Single-team #99)

---

## What a bundle is

An option bundle is a standalone Claude Code plugin that, when commissioned into a project, installs:

- A constitution (`CONSTITUTION.md`)
- Option-specific agents (markdown files with frontmatter)
- Option-specific skills (markdown files with frontmatter)
- Templates for required artefacts (feature proposal, retrospective, architecture documents, etc.)
- Validator configuration (which checks run at `--syntax`, `--quick`, `--pre-push`)

A bundle ships as a plugin alongside `sdlc-team-*` and `sdlc-lang-*` plugins in the marketplace. Plugin name convention: `sdlc-<option>` (e.g. `sdlc-programme`, `sdlc-assured`).

## File layout

A bundle plugin directory MUST contain:

```
plugins/sdlc-<option>/
├── .claude-plugin/
│   └── plugin.json              # standard plugin metadata
├── manifest.yaml                # bundle manifest (NEW convention for bundle plugins)
├── README.md                    # bundle overview, audience, level guidance
├── CONSTITUTION.md              # option-specific constitution (NEW convention for bundle plugins)
├── pyproject.toml               # OPTIONAL: present if the bundle ships Python helpers
├── agents/                      # option-specific agents
├── skills/                      # option-specific skills (each in its own subdirectory)
├── templates/                   # artefact templates
└── scripts/                     # OPTIONAL: Python implementation helpers (mirror sdlc-knowledge-base / sdlc-workflows pattern)
```

**New conventions for bundle plugins**: `manifest.yaml` and root-level `CONSTITUTION.md` are introduced by bundle plugins; existing non-bundle plugins (sdlc-team-*, sdlc-lang-*, sdlc-knowledge-base, sdlc-workflows) do not have them. Bundle plugins are identified by the presence of `manifest.yaml` in the plugin root.

**Validator dispatcher infrastructure deferred**: Phase C does not specify a `validators/` directory or dispatcher. Validator identifiers (e.g., `python_ast`, `check_technical_debt`) are listed in the manifest's `validators:` object as bundle-defined identifiers. Phase D and Phase E refine the registry shape — including any `validators/` directory or dispatcher — based on what real bundles need at implementation time.

## Manifest schema (`manifest.yaml`)

Every bundle has a manifest at the bundle root with these fields:

| Field | Type | Required | Description |
|---|---|---|---|
| `schema_version` | int | yes | Bundle contract schema version (currently `1`) |
| `name` | string | yes | Bundle name (`solo` / `single-team` / `programme` / `assured`) |
| `version` | semver string | yes | Bundle version (e.g. `0.1.0`) |
| `supported_levels` | list[string] | yes | One or more of `prototype` / `production` / `enterprise` |
| `description` | string | yes | One-line description |
| `constitution` | string | yes | Path to constitution file relative to bundle root (typically `CONSTITUTION.md`) |
| `depends_on` | list[string] | no | Other plugins this bundle depends on (default: `[sdlc-core]`) |
| `agents` | list[string] | no | Agent file basenames provided (e.g. `["sdlc-enforcer.md"]`) |
| `skills` | list[string] | no | Skill directory names provided (e.g. `["validate", "phase-review"]`) |
| `templates` | list[string] | no | Template file paths within `templates/` |
| `validators` | object | no | Validator configuration (see below) |

**Note on `supported_levels`**: a bundle may support multiple levels. The project's `sdlc_level` (recorded in `.sdlc/team-config.json`) is chosen by the user at commissioning time from this list. The commissioning skill (Phase C task 6) asks the user when the bundle supports more than one.

### Reserved Phase E fields

These fields are reserved in the schema; bundles MAY include them. Phase C does not validate their semantics; Phase E (Assured bundle) implements full validator support.

The fields below are **bundle-capability flags** — declarations on the bundle plugin itself announcing "this bundle understands and supports feature X." They are distinct from the *project-scope decomposition keys* (e.g. `source-paths`, `derived-paths`, `known-violation`, `anaemic-context-detection`) that live in a project's `library/_decomposition.md` and are owned by the project's commissioning record, not the bundle. Phase C does not validate either; Phase E (Assured bundle) implements the project-scope schema and the bundle-flag-to-project-feature mapping.

| Field | Type | Description |
|---|---|---|
| `decomposition_support` | bool | Whether the bundle supports declarative decomposition (Method 2 / Assured) |
| `id_format` | enum | `positional` (e.g. `P1.SP2.M3.REQ-007`) or `named` (e.g. `aisp.kb.kbsk.REQ-NNN`); applies when `decomposition_support: true`. Definitive choice deferred to Phase E plan-writing — see `research/sdlc-bundles/decomposition-spike.md` Finding 2. |
| `paths_split_supported` | bool | Whether the bundle's modules use the `source-paths` / `derived-paths` distinction |
| `known_violations_field` | bool | Whether the bundle's commissioning record carries a `known_violations` array |
| `anaemic_context_opt_out` | bool | Whether modules in this bundle may declare `anaemic-context-detection: suppressed` |

**Note on Spike Gap 3 (cross-module-mutation validator)**: not represented as a dedicated capability flag because validator identifiers are added to the manifest's `validators:` object as bundle-defined identifiers (see "Validator configuration" section). When Phase E ships the cross-module-mutation validator, bundles that include it list it in their `validators:` block — no manifest-level flag needed.

### Versioning rules

- **Bundle version** (`version` in manifest): semver. Patch = bug fix; minor = added validator; major = breaking schema or rule change.
- **Project record** (`option_bundle_version` in `.sdlc/team-config.json`): records exact bundle version installed.
- **Migration**: when a bundle's major version changes, the migration skill (#101, future sub-feature) handles upgrade. Phase C does not implement migration; bundles ship at major version 0 until migration lands. Bundles at major version 0 may break manifest schema or rule semantics in any minor release; consumers should pin exact bundle versions in their project's `option_bundle_version` until the bundle reaches `1.0.0`.

## Reserved schema for `.sdlc/team-config.json`

Bundles populate the project's `.sdlc/team-config.json` with commissioning record fields:

| Field | Required | Populated by |
|---|---|---|
| `sdlc_option` | yes | Phase C — Solo / Single-team / Programme / Assured |
| `sdlc_level` | yes | Phase C — prototype / production / enterprise |
| `commissioned_at` | yes | Phase C — ISO 8601 timestamp |
| `commissioned_by` | yes | Phase C — username or "claude-agent" |
| `option_bundle_version` | yes | Phase C — bundle's manifest version |
| `commissioning_history` | yes | Phase C — array of past commissioning entries |
| `decomposition` | reserved | Phase E — pointer to `library/_decomposition.md` |
| `commissioning_options` | reserved | Phase E — per-bundle config (e.g. `regulatory_context`, `change_impact_gate_enabled`, `id_format`) |

**Each `commissioning_history` entry** is a snapshot of the per-event commissioning fields:

- `sdlc_option` (string)
- `sdlc_level` (string)
- `commissioned_at` (ISO 8601 timestamp)
- `commissioned_by` (string)
- `option_bundle_version` (semver string)

The top-level fields reflect the latest commissioning; the history array accumulates one entry per `commission` invocation.

Reserved fields appear in the schema but are NOT populated by Phase C bundles. Phase E bundles populate them when commissioning to Assured.

## Validator configuration

Bundles declare which validators run at each pipeline phase:

The names in the validator lists (e.g. `python_ast`, `check_technical_debt`) are **bundle-defined identifiers**, NOT global script paths. The identifier-to-command mapping is bundle-internal — Phase C does not specify how a bundle resolves an identifier to a runnable command. This indirection lets a bundle add or rename validators without breaking other bundles, and lets multiple bundles use the same identifier (e.g. `run_tests`) backed by different commands when their projects' test runners differ.

Phase C ships a stub bundle-defined identifier list in the sample bundle (Task 4). Phase D and Phase E refine the registry shape — including any `validators/` directory or dispatcher pattern — based on real bundle needs.

```yaml
validators:
  syntax:
    - python_ast
  quick:
    - check_technical_debt
    - check_logging_compliance
  pre_push:
    - python_ast
    - check_technical_debt
    - check_logging_compliance
    - validate_architecture
    - run_tests
```

Bundle commissioning writes this configuration to the project's pre-push hook configuration. Phase C uses a stub configuration; Phase D and E refine.

## Backward compatibility

Existing projects without `sdlc_option` in `.sdlc/team-config.json` continue to work unchanged. The sdlc-enforcer (modified in Phase C — see plan task 9) silently defaults to `single-team` for any project where `sdlc_option` is unset.

## What Phase C does NOT cover

- Programme bundle implementation (Phase D, #103)
- Assured bundle implementation (Phase E, #104)
- Single-team and Solo bundle implementation (#99 / #100, separate sub-features)
- Migration between options (#101)
- The Method 2 schema fields' validator semantics (Phase E)
- **Per-validator audit-evidence requirements** (e.g., declaring "this validator's output is the regulator-facing artefact"). Bundles that need this declare it in their `README.md`; the framework does not enforce a schema for it.
- **Bundle-level certification scope** (e.g., "this bundle supports DO-178C Level B but not Level A", or specific ASIL ranges). Declared in the bundle's `README.md`; not part of the manifest schema. Future versions of the contract may add a `regulatory_contexts: list[string]` field if Phase E or later real-world bundles need machine-readable declaration.
- **Validator tool-qualification levels** (TCL per ISO 26262-8, similar concepts in DO-178C). The framework is open-source code; tool qualification is determined per-project based on context, not declared by the bundle.

Phase C ships the contract + the commission skill + the recorder + the installer + sdlc-enforcer adaptation. Bundles get built on top.
