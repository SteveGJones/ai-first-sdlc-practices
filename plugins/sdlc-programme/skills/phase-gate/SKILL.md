---
name: phase-gate
description: Run a Programme phase gate validator (requirements / design / test / code) against docs/specs/<feature-id>/. Block on missing artefact or broken cross-phase reference.
disable-model-invocation: false
argument-hint: "<phase> <feature-id> [code-file-glob-for-code-gate]"
---

# Run a Phase Gate

Run the named gate validator against a feature's phase artefacts.

## Arguments

- `<phase>` — one of `requirements`, `design`, `test`, `code`
- `<feature-id>` — short slug for the feature
- `[code-file-glob]` — only required when `<phase>` is `code`; e.g., `src/**/*.py`

## Steps

```bash
PHASE="$1"
FEATURE_ID="$2"
CODE_GLOB="${3:-}"

if [ -z "$PHASE" ] || [ -z "$FEATURE_ID" ]; then
    echo "Usage: phase-gate <phase> <feature-id> [code-file-glob]" >&2
    exit 1
fi

case "$PHASE" in
    requirements|design|test|code) ;;
    *)
        echo "phase must be one of: requirements, design, test, code" >&2
        exit 1
        ;;
esac

FEATURE_DIR="docs/specs/$FEATURE_ID"

if [ "$PHASE" = "code" ] && [ -z "$CODE_GLOB" ]; then
    echo "code phase requires a code-file-glob (e.g., 'src/**/*.py')" >&2
    exit 1
fi

python3 << PYEOF
from pathlib import Path
from sdlc_programme_scripts.programme.gates import (
    code_gate, design_gate, requirements_gate, test_gate,
)

phase = "$PHASE"
feature_id = "$FEATURE_ID"
feature_dir = Path("$FEATURE_DIR")

if phase == "requirements":
    result = requirements_gate(feature_dir, feature_id)
elif phase == "design":
    result = design_gate(feature_dir, feature_id)
elif phase == "test":
    result = test_gate(feature_dir, feature_id)
elif phase == "code":
    code_glob = "$CODE_GLOB"
    code_text = ""
    for path in Path().glob(code_glob):
        if path.is_file():
            code_text += path.read_text() + "\n"
    result = code_gate(feature_dir, feature_id, code_text=code_text)

if result.passed:
    print(f"PASS: {result.gate_name}-gate for feature {result.feature_id}")
    raise SystemExit(0)
else:
    print(f"FAIL: {result.gate_name}-gate for feature {result.feature_id}")
    for err in result.errors:
        print(f"  - {err}")
    raise SystemExit(1)
PYEOF
```

## Done

Report:

- Gate name and feature-id
- PASS or FAIL
- For FAIL: each broken reference / missing artefact

If FAIL, the user must fix the cited issues before commit/push. The same gates run at pre-push validation.

## Model selection

This skill runs deterministic Python validators. Smaller models are sufficient.
