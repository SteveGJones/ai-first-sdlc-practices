# Phase F — Dogfood Findings

## F-001 — `# implements:` annotation parser does not handle markdown files

**Severity:** IMPORTANT
**Surfaced during:** Task 4 (Stage 1 proof-of-flow)
**Reproduction:** The `_IMPLEMENTS_RE` regex in `plugins/sdlc-assured/scripts/assured/code_index.py` matches `^\s*#\s*implements:\s*(?P<ids>.+)$`. In a markdown file, the line `# implements: REQ-x-001` parses as an H1 heading by markdown renderers AND matches the regex — producing a fake annotation that displays as a giant title. The HTML-comment workaround `<!-- implements: REQ-x-001 -->` displays correctly in markdown but does NOT match the regex.
**Impact on regulated-industry users:** high — most user-facing artefacts (SKILLs, agents, design docs) are markdown, not Python. Regulated-industry users will hit this within the first feature.
**Suggested resolution:** v0.2.0 — extend `_IMPLEMENTS_RE` to recognise both forms, or add a second regex `_HTML_IMPLEMENTS_RE = re.compile(r"<!--\s*implements:\s*(?P<ids>.+)\s*-->")`. Alternative: define a project-wide rule that markdown annotations live in YAML frontmatter (`implements: [DES-x-001, ...]`).
**Related code:** plugins/sdlc-assured/scripts/assured/code_index.py:9-13, plugins/sdlc-assured/scripts/assured/traceability_validators.py:_IMPLEMENTS_RE

## F-002 — programs.yaml `paths` cannot scope to a section of a file

**Severity:** MINOR
**Surfaced during:** Task 2 (Stage 1)
**Reproduction:** Module M3 (kb-bridge) implements only the SYNTHESISE-ACROSS-SPEC-TYPES section of synthesis-librarian.md, not the whole file. programs.yaml `paths` is whole-directory only.
**Impact on regulated-industry users:** medium — fine-grained ownership of file sections is common in regulated codebases (e.g., MISRA-C compliant subset of a header file)
**Suggested resolution:** consider line-range or section-anchor support in v0.2.0; or document the limitation
**Related:** plugins/sdlc-assured/scripts/assured/decomposition.py:Module.paths

---

## Stage 1 checkpoint reflection

**Time spent on Tasks 1-4:** ~50 min total across 4 dispatches (Task 1: ~8 min commission scaffold; Task 2: ~12 min programs.yaml decomposition; Task 3: ~10 min REQ inventory checklist; Task 4: ~20 min M3 spec authoring + annotation + two findings).
**Friction productivity:** Productive. Both F-001 and F-002 surfaced design-level gaps the spec did not anticipate — F-001 exposes a genuine hole in the annotation coverage model for non-Python artefacts, F-002 exposes a granularity ceiling in the `paths` ownership model. Neither is noise. A purely clerical stage would have produced zero findings.
**REQ-statement level (M3 proof-of-flow):** User-visible-capability level. REQ-kb-bridge-mode-001 states what the agent MUST recognise; REQ-kb-bridge-mode-002 states what the whitelist MUST accept. Neither paraphrases a function signature; both could be evaluated by a reviewer who has never read the implementation.
**Commission-assured concreteness:** Concrete. The `.sdlc/team-config.json` produced in Task 1 carries three operationally meaningful fields — `visibility_mode`, `change_impact_gate`, `decomposition` — each with a non-default value that implies a real behaviour choice. The scaffold is not aspirational placeholder text.
**Recommendation:** PROCEED at full scope
**Rationale:** The Stage 1 tripwire condition ("if 1-module's-worth feels overwhelming, escalate") is not triggered. Task 4 produced a complete REQ/DES/TEST chain for M3 in one dispatch, surfaced two honest findings, and left the artefacts in committed, reviewable state. The REQs are at the right granularity; the commission scaffold is functional, not aspirational; and the two findings strengthen rather than undermine the case for continuing — they are exactly the kind of friction a recursive dogfood exercise is designed to expose. The 44-REQ paperwork risk identified in §11 remains theoretical at this point: the M3 chain required only 2 REQs, 2 DES items, and 2 TEST cases, which is proportionate. No blocker exists. Stage 2 (remaining modules in the REQ inventory) should proceed as planned.
