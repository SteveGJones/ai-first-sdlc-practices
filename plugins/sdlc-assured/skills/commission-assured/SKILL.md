---
name: commission-assured
description: Commission a project to the Assured (Method 2) SDLC bundle — install plugin, scaffold programs.yaml, set granularity and regulatory context, configure change-impact-gate.
disable-model-invocation: true
---

# Skill: commission-assured

**Use this skill** when the user wants to commission a project to the Assured (Method 2) SDLC option. This is a one-time installation that scaffolds the decomposition declaration, sets regulatory context, and configures optional validators.

This skill assumes:
- The project already has the `sdlc-programme` plugin installed (Assured layers on Programme).
- The user has authority to commission (this is an irrevocable decision per Article 16).

## Steps

1. **Verify prerequisites.** Confirm `sdlc-programme` is installed; confirm `sdlc-knowledge-base` is initialised (run `kb-init` if not).

2. **Prompt for regulatory context.**
    - Which regulatory standards apply? (DO-178C / IEC 62304 / ISO 26262 / IEC 61508 / FDA 21 CFR §820 / none / multiple)
    - For IEC 62304: software safety class (A / B / C)
    - For ISO 26262: ASIL level (A / B / C / D)
    - For DO-178C: DAL (A / B / C / D / E)

3. **Prompt for decomposition.**
    - Does the project have one logical area or multiple? (single → use default `P1.SP1.M1`; multiple → scaffold a `programs.yaml` with placeholders to fill in)
    - If multiple: how many programs? Sub-programs per program? Modules per sub-program?

4. **Scaffold the artefacts.**
    - Copy `programs.yaml` template to `programs.yaml` (project root) with placeholders substituted.
    - Copy `visibility-rules.md` template to `docs/architecture/visibility-rules.md`.
    - For regulated contexts (IEC 62304 ≥ B, FDA, ISO 26262 ASIL ≥ C): copy `change-impact.md` template to `docs/change-impacts/CHG-template.md`.
    - Add `library/_ids.md` and `library/_code-index.md` placeholders (will be populated by `kb-codeindex` and `kb-rebuild-indexes`).

5. **Configure validators.**
    - Set commissioning flags in `.sdlc/team-config.json`:
      - `assured.visibility_mode: strict` for regulated contexts; `advisory` otherwise
      - `assured.change_impact_gate: enabled` for IEC 62304 ≥ B, FDA, ISO 26262 ASIL ≥ C; `disabled` otherwise

6. **Run initial validation.**
    - `python3 -m sdlc_assured_scripts.assured.ids` to build initial `library/_ids.md`
    - `kb-codeindex` to build initial `library/_code-index.md` (will be empty until annotations exist)
    - Confirm validators run cleanly on the empty/scaffolded project.

7. **Wire the Assured library sources into the knowledge base.**

    The `_code-index.md` and `_spec-findings.md` files emitted by `kb-codeindex` and `kb-rebuild-indexes` are shelf-index documents that must be registered as library sources so the `research-librarian` and `synthesis-librarian` agents can query them.

    Run `kb-register-library` for each source:
    ```
    /sdlc-knowledge-base:kb-register-library \
        --handle <project-handle>-code \
        --path library/_code-index.md \
        --domain code-annotations

    /sdlc-knowledge-base:kb-register-library \
        --handle <project-handle>-specs \
        --path library/_spec-findings.md \
        --domain spec-requirements
    ```

    Confirm both handles appear in `library/.sdlc-kb/registry.json` (or the project's active registry). The `SYNTHESISE-ACROSS-SPEC-TYPES` mode in `synthesis-librarian` queries these handles; without this registration step, spec-as-KB-finding queries will return empty results.

8. **Commit the commissioning.**
    - One commit per scaffolded artefact group (programs.yaml + visibility-rules.md as one; change-impact template as another; library wiring as a third).

## Done criteria

- `programs.yaml` committed with no placeholder text remaining.
- `library/_ids.md` and `library/_code-index.md` exist (may be empty).
- `.sdlc/team-config.json` has `assured.*` flags set.
- Validators run without errors on the freshly-commissioned project.
