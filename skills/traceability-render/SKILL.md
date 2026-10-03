---
name: traceability-render
description: Render module-scoped human-readable traceability for a single module — REQs, DESs, TESTs, code locations with anchor links, plus the module-dependency graph as a markdown edge-list.
---

<!-- implements: DES-assured-skills-007 -->

# Skill: traceability-render

**Use this skill** when a reviewer or auditor needs a human-readable view of one module's traceability. Produces a markdown document with anchors that resolve in any markdown renderer, no Sphinx required.

## Inputs

- `<module-id>` — e.g., `P1.SP1.M1`. If the project uses default decomposition, just `M1` is accepted.

## Steps

1. **Validate the module exists.** Read `programs.yaml`; confirm the module is declared.

2. **Load the registry.** Read `library/_ids.md` and `library/_code-index.md`.

3. **Filter to the module.** Keep only IDs whose module assignment matches.

4. **Render the module scope.** Use `render_module_scope`.

5. **Render the dependency graph.** Walk source-file imports to derive the `actual_edges`. Use `render_module_dependency_graph`.

6. **Concatenate** scope + dependency graph into one document.

7. **Write to `docs/traceability/<module-id>.md`.** Idempotent.

8. **Print** the path of the rendered document.

## Done criteria

- Document written.
- Contains REQs, DESs, TESTs, code, orphan code, dependency graph.
- Idempotent.
