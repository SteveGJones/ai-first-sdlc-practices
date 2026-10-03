# Option Bundle Contract Review — Independent Critical Assessment

**Reviewer:** Claude Opus 4.6 (independent, no prior involvement in contract authoring)
**Date:** 2026-04-29
**Contract reviewed:** `docs/architecture/option-bundle-contract.md` (Version 1, Draft, Phase C)
**Method:** Read-only review against 5 specified documents + filesystem walk of existing plugin family

---

## Question 1: Manifest Schema Permissiveness

**Verdict: AGREE-WITH-CONCERNS**

The manifest schema is broadly adequate for Programme, Assured, and future Solo/Single-team bundles. The field set covers the essential identity (`name`, `version`, `schema_version`), capability declaration (`supported_levels`, `agents`, `skills`, `templates`, `validators`), and dependency tracking (`depends_on`). The reserved Phase E fields handle the decomposition/traceability axis without polluting the Phase D surface.

**Concerns:**

1. **No `constitution` field.** The file layout mandates `CONSTITUTION.md` at the bundle root, but the manifest schema has no field declaring its presence or version. Every other shipped artefact type (agents, skills, templates, validators) has a manifest field. The constitution is the single most load-bearing artefact a bundle ships — it defines what rules apply. Its absence from the manifest means tooling cannot programmatically verify "does this bundle ship a constitution?" without filesystem probing. A `constitution: CONSTITUTION.md` field (or even `constitution_version: string`) would close this gap. This is a minor gap — the file layout convention works — but it is an asymmetry worth noting.

2. **No `regulatory_contexts` field at the manifest level.** METHODS.md Section 4 describes the Assured bundle's commissioning script asking about regulatory context (DO-178C, IEC 62304, ISO 26262, IEC 61508, FDA). The contract reserves `commissioning_options` in team-config.json for this, but the bundle manifest itself has no way to declare "this bundle is designed for these regulatory contexts." A Programme bundle author cannot declare "I support IEC 62304 Class B but not Class C" in the manifest. This is arguably a Phase E concern, but since the contract claims to be authoritative for the Assured bundle, the omission is worth flagging. The `supported_levels` field (prototype/production/enterprise) is the closest analogue but operates on a different axis.

3. **`templates` field is a flat list of strings.** Templates in METHODS.md are typed by phase (requirements-spec, design-spec, test-spec). The manifest schema provides no way to declare template type or phase association. A bundle author listing `["requirements-spec.md", "design-spec.md", "test-spec.md"]` loses the semantic that these are ordered phase artefacts. For Programme bundle this matters — template order IS the phase sequence. This could be deferred to Phase D if the template-to-phase mapping is handled by convention (directory structure within `templates/`), but the contract does not specify that convention.

4. **No field that no bundle would use.** All current fields have plausible consumers. `supported_levels` might seem unused by a Solo bundle (which would presumably support only `prototype`), but even Solo benefits from declaring its scope. No dead weight found.

**Bottom line:** The schema is permissive enough for Phase D to proceed without retrofit. The concerns are additive (fields that could be added) rather than structural (fields that need reshaping). Phase D plan-writing should decide whether `constitution` and `regulatory_contexts` are worth adding before the schema leaves draft status.

---

## Question 2: Phase E Reserved Fields Adequacy

**Verdict: AGREE-WITH-CONCERNS**

The 5 manifest capability flags map cleanly to the decomposition spike's 4 schema gaps:

| Spike gap | Reserved field | Coverage |
|---|---|---|
| Gap 1: `source-paths`/`derived-paths` split | `paths_split_supported` (bool) | Covered as a capability flag. The actual schema extension (adding `source-paths`/`derived-paths` to the `programs` block) is project-scope, not bundle-scope — correctly separated. |
| Gap 2: `known-violation` field | `known_violations_field` (bool) | Covered as capability flag. |
| Gap 3: Cross-module-mutation validator | Not directly reserved | **Partially uncovered.** The contract does not reserve a field declaring "this bundle ships a cross-module-mutation validator." The `validators` object could accommodate this naturally (just add `cross_module_mutation` to the validator lists), but the contract does not mention it. |
| Gap 4: `anaemic-context-detection` opt-out | `anaemic_context_opt_out` (bool) | Covered. |
| Gap 5 (Finding 2): ID format | `id_format` (enum: positional/named) | Covered, with the correct acknowledgement that the definitive choice is deferred. |

**Concerns:**

1. **Gap 3 has no dedicated capability flag.** The cross-module-mutation validator is a Phase E validator, not a capability flag. The existing `validators` object can absorb it, but the contract's reserved-fields table does not mention it. This is arguably fine — the `validators` object is explicitly extensible ("Phase D and Phase E refine the registry shape") — but a reader checking "are all spike gaps covered?" will not find Gap 3 in the reserved-fields table.

2. **The reserved fields are all booleans except `id_format`.** This is intentionally minimal, but Phase E may need richer shapes. For example, `known_violations_field: bool` says "this bundle supports known-violations" but does not specify the violation schema shape. When Phase E implements the actual `known-violations:` array in the `programs` block, the bundle capability flag alone does not constrain what shape the violations take. This is acceptable for a reserved field (the contract explicitly says "Phase C does not validate their semantics") but Phase E plan-writing should be aware that these booleans are placeholders for richer type definitions.

3. **The `commissioning_options` reserved field in team-config.json is a catch-all.** It lists `regulatory_context`, `change_impact_gate_enabled`, `id_format` as examples. This is flexible but could become a dumping ground. Phase E should define a sub-schema for `commissioning_options` rather than treating it as unstructured.

**Bottom line:** 4 of 5 gaps are covered by reserved fields. Gap 3 (cross-module-mutation validator) is implicitly covered by the extensible `validators` object but not explicitly reserved. No reserved field appears to be the wrong shape — they are intentionally minimal booleans that Phase E will refine. The reservations are sufficient for Phase E plan-writing to proceed.

---

## Question 3: File Layout vs Existing 12-Plugin Family

**Verdict: DISAGREE**

The contract specifies this bundle plugin layout:

```
plugins/sdlc-<option>/
  .claude-plugin/plugin.json
  manifest.yaml
  CONSTITUTION.md
  agents/
  skills/
  templates/
  validators/
```

Walking the actual plugin family reveals significant divergences:

**Divergence 1: `manifest.yaml` does not exist in any shipping plugin.** Zero of the 12 existing plugins have a `manifest.yaml` at their root. The only `manifest.yaml` in the entire repo is in `plugins/sdlc-core/skills/commission/templates/sample-bundle/manifest.yaml` — a mock template, not a real plugin. This is expected and intentional (bundles are a new concept), but the contract should explicitly acknowledge that bundle plugins introduce `manifest.yaml` as a new convention that existing non-bundle plugins do not use. The contract says "bundle plugins are identified by the presence of manifest.yaml in the plugin root" — this is correct but the reverse implication (existing plugins lack it) is unstated.

**Divergence 2: `CONSTITUTION.md` does not exist in any shipping plugin (at the plugin root).** The only `CONSTITUTION.md` in any plugin is `plugins/sdlc-core/skills/commission/templates/sample-bundle/CONSTITUTION.md` — again, a mock. The repo-root `CONSTITUTION.md` exists but is not inside any plugin. Bundle plugins would be the first to ship their own constitution. This is again expected, but worth noting for clarity.

**Divergence 3: `validators/` directory does not exist in ANY plugin.** This is the most surprising divergence. The contract specifies `validators/` as a MUST-contain directory in the bundle layout. But:

- No existing plugin has a `validators/` directory.
- All validators live in `tools/validation/` at the repo root, outside any plugin.
- The `sdlc-core` plugin does not ship validators as plugin content — it invokes them from the root `tools/validation/` path.
- The sample bundle in `plugins/sdlc-core/skills/commission/templates/sample-bundle/` does NOT have a `validators/` directory.

The contract describes a `validators/` directory containing "the mapping from identifier to actual command — typically a small YAML or JSON registry plus a `validators/run.sh` dispatcher." This is entirely aspirational — nothing like this exists anywhere in the codebase. The manifest's `validators` object (listing identifiers like `python_ast`, `check_technical_debt`) is a different thing from a `validators/` directory with a dispatcher. The contract conflates two concepts: (a) the manifest field listing which validators run at which phase (this exists in the sample bundle), and (b) a directory containing validator implementation/configuration (this does not exist anywhere).

**Divergence 4: `templates/` as a top-level bundle directory.** Existing plugins that have templates put them inside skill directories (`plugins/sdlc-knowledge-base/skills/kb-init/templates/`, `plugins/sdlc-core/skills/new-feature/templates/`). The sample bundle does have a top-level `templates/` directory, so this is at least partially established, but it differs from how existing plugins organize template content.

**Divergence 5: Missing common plugin files.** Every shipping plugin has `README.md` and `pyproject.toml` at the root. The contract's file layout does not mention either. These may be assumed, but a "MUST contain" layout that omits files every real plugin has is incomplete.

**Divergence 6: No `scripts/` directory mentioned.** Both `sdlc-knowledge-base` and `sdlc-workflows` have `scripts/` directories containing Python implementation code. If a bundle ships Python validators or commissioning logic, it would need `scripts/`. The contract does not mention this.

**Bottom line:** The contract's file layout is aspirational, not grounded in how the existing 12 plugins are actually packaged. The `validators/` directory is the most problematic divergence — it specifies infrastructure that does not exist anywhere and conflates manifest configuration with directory structure. Phase D plan-writing must reconcile the contract's layout with the actual plugin packaging pattern, or the first real bundle will immediately diverge from the contract.

---

## Question 4: Backward Compatibility Tightness

**Verdict: AGREE**

The contract claims: "Existing projects without `sdlc_option` in `.sdlc/team-config.json` continue to work unchanged. The sdlc-enforcer silently defaults to `single-team` for any project where `sdlc_option` is unset."

The sdlc-enforcer agent (`agents/core/sdlc-enforcer.md`) implements this precisely. The "Read commissioning record on every invocation" section contains Python code that:

1. Checks `is_commissioned(team_config)` — reads the team-config.json and determines if a commissioning record exists.
2. If commissioned: reads `record.sdlc_option`, `record.sdlc_level`, `record.option_bundle_version`.
3. If NOT commissioned: calls `default_option_for_uncommissioned()` which returns the default option (single-team), sets level to `production`, and `option_bundle_version` to `unset`.

The backward-compatibility text in the enforcer reads: "projects without `sdlc_option` continue to work as before, defaulting to `single-team` behaviour. No project must take action to keep working when commissioning ships."

**For the specific scenario posed** — a project with `.sdlc/team-config.json` containing only `team_name` and `created` (no `sdlc_option`): the `is_commissioned()` function would return `false` (since `sdlc_option` is absent), and the enforcer would fall through to `default_option_for_uncommissioned()`, producing `sdlc_option=single-team`, `sdlc_level=production`. The project continues to work with single-team enforcement at production level — which is exactly what such a project currently experiences.

The contract accurately describes what was built. No overstatement detected.

**One minor note:** The contract says the enforcer "silently defaults." The implementation does `print(f'sdlc_option={default_option_for_uncommissioned()}')` — it prints the default, which is visible in the enforcer's output. "Silently" means "without requiring user action," not "without any output." The contract's language is acceptable but could be more precise.

---

## Question 5: Regulated-Industry Adoption Gap

**Verdict: AGREE-WITH-CONCERNS**

Walking through the viewpoint of a regulated-industry team reading this contract to understand what their Assured bundle manifest must declare:

**Can they declare per-validator audit-evidence requirements?**

No. The contract's `validators` object is a flat mapping of pipeline phase to identifier list:
```yaml
validators:
  syntax: [python_ast]
  pre_push: [python_ast, check_technical_debt, ...]
```

There is no field for "this validator's output is the regulator-facing artefact" or "this validator produces audit evidence that must be retained for N years." The contract says validators are "bundle-defined identifiers" with a dispatcher in `validators/`, but the dispatcher concept has no schema for evidence-metadata.

**Is this a gap?** Partially. The contract's scope is the bundle manifest schema, not the validator implementation. A bundle could ship validators whose dispatchers produce audit-grade output, documented in the bundle's README. The manifest does not need to declare evidence-retention policy — that is an operational concern handled by the organization's quality management system, not the framework. However, a regulated team would want at least a way to tag validators as "audit-evidence-producing" vs "internal-only" so that CI pipelines know which outputs to archive. This is a reasonable Phase E addition but arguably out of scope for the framework-level contract.

**Can they declare bundle-level certification scope?**

No. There is no field for "this bundle supports DO-178C Level B but not Level A" or "this bundle is designed for IEC 62304 Class C." The `supported_levels` field (prototype/production/enterprise) is the framework's own maturity axis, not a regulatory-standard axis. The reserved `commissioning_options` field could carry `regulatory_context` per project, but the bundle manifest has no way to declare its own regulatory design intent.

**Is this a gap?** This is correctly out of scope for the framework itself. The contract explicitly states (via METHODS.md Section 6): "The Assured bundle produces substrate that helps reach assurance, not certification." A bundle claiming "I support DO-178C Level B" would be a framework making certification claims, which METHODS.md and the regulatory traceability baseline both explicitly reject. The bundle's README and commissioning guidance are the right place for this — not the manifest schema. Attempting to schema-ify certification scope would create false confidence.

**Can they declare validator tool-qualification levels (TCL per ISO 26262-8)?**

No. Tool Confidence Levels (TCL 1/2/3 per ISO 26262-8) and tool qualification (per DO-178C Annex A) are certification-authority concerns that apply to specific tool versions in specific deployment contexts. A markdown-based framework cannot declare its own TCL — that determination is made by a qualified assessor examining the tool in context. The contract is correctly silent on this.

**Is this a gap?** No. This is definitively out of scope. Tool qualification requires formal verification evidence (test suites with MC/DC coverage, etc.) that is far beyond what an open-source SDLC framework should claim. A regulated team would use this framework as one input to their tool qualification case, not expect the framework to self-qualify.

**Concerns (within scope):**

1. **No guidance on what "audit-friendly" means for `traceability-export`.** The contract mentions `traceability-export <format>` in METHODS.md but the bundle contract itself does not specify what export formats the manifest can declare or how a regulated team would know which formats their bundle supports. The `skills` list in the manifest is just skill directory names — there is no way to declare "this bundle supports `traceability-export do-178c-rtm`" at the manifest level. Phase D/E should consider whether export-format capability belongs in the manifest.

2. **No `audit_trail` or `evidence_retention` manifest-level metadata.** Regulated industries require knowing where evidence lives and how long it is retained. The framework's answer (Git + markdown = inherent audit trail) is correct but unstated in the contract. A single sentence acknowledging "traceability evidence is the committed markdown + Git history; retention is the repository's responsibility" would help regulated adopters understand the framework's evidence model.

**Bottom line:** The three specific capabilities asked about (per-validator audit-evidence, certification scope, tool qualification levels) are all correctly out of scope for the framework. The contract does not overreach. Two minor gaps exist in regulated-team guidance (export-format declaration and evidence-model statement) that would improve the contract for Phase E adoption without changing the schema.

---

## Summary

The option bundle contract is **good enough to feed Phase D plan-writing** (roadmap, skill inventory, commissioning flow). Phase D can proceed against this contract with confidence that the manifest schema, reserved fields, backward compatibility, and scope boundaries are sound.

The contract is **conditionally good enough for Phase E plan-writing**, with one structural issue that should be resolved:

- **The `validators/` directory specification (Question 3) is the most significant problem.** The contract mandates a directory structure that does not exist in any shipping plugin, conflates manifest configuration with filesystem layout, and describes dispatcher infrastructure that has never been built. Phase E plan-writing will need to decide: do bundles actually ship a `validators/` directory with a dispatcher, or do they declare validator identifiers in the manifest and rely on the existing `tools/validation/` infrastructure? The contract should clarify this before Phase E designs validators against it.

The remaining concerns are additive rather than structural:
- Missing `constitution` field in manifest (Question 1) — easy to add.
- Gap 3 (cross-module-mutation validator) not explicitly reserved (Question 2) — implicitly covered by extensible `validators` object.
- Missing `README.md`, `pyproject.toml`, `scripts/` in the file layout (Question 3) — convention gap, not schema gap.
- Export-format and evidence-model guidance for regulated teams (Question 5) — documentation gap, not schema gap.

**Recommendation:** Resolve the `validators/` directory question before Phase E plan-writing begins. All other issues can be resolved during Phase D or Phase E without blocking. The contract's backward-compatibility claim and Phase E reserved-field design are both sound and can be relied upon.

| Question | Verdict |
|---|---|
| 1. Manifest schema permissiveness | AGREE-WITH-CONCERNS |
| 2. Phase E reserved fields adequacy | AGREE-WITH-CONCERNS |
| 3. File layout vs existing plugin family | DISAGREE |
| 4. Backward compatibility tightness | AGREE |
| 5. Regulated-industry adoption gap | AGREE-WITH-CONCERNS |
