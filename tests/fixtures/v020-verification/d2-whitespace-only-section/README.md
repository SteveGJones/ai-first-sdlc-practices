## Defect: D2 — Whitespace-only Motivation section

`requirements-spec.md` has a `## Motivation` section whose body contains only
whitespace (spaces). `requirements_gate` from `sdlc-programme` should fire and
report the section as empty/whitespace-only. The test calls
`requirements_gate(feature_dir, "fxd2")` on the `docs/specs/fxd2/` directory.
