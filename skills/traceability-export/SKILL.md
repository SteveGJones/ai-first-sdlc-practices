---
name: traceability-export
description: Export the REQ↔DES↔TEST traceability matrix for a feature in csv or markdown format. Phase D ships csv + markdown; Phase E (Assured) extends with standard-specific formats.
disable-model-invocation: false
argument-hint: "<format> <feature-id> [output-path]"
---

# Export Traceability Matrix

Produce an audit-friendly REQ↔DES↔TEST traceability matrix.

## Arguments

- `<format>` — `csv` or `markdown`
- `<feature-id>` — short slug for the feature
- `[output-path]` — optional. Defaults to `docs/specs/<feature-id>/traceability.<ext>` where `.ext` is `.csv` or `.md`.

## Steps

```bash
FORMAT="$1"
FEATURE_ID="$2"
OUTPUT_PATH="${3:-}"

if [ -z "$FORMAT" ] || [ -z "$FEATURE_ID" ]; then
    echo "Usage: traceability-export <format> <feature-id> [output-path]" >&2
    exit 1
fi

case "$FORMAT" in
    csv|markdown) ;;
    *)
        echo "format must be one of: csv, markdown" >&2
        exit 1
        ;;
esac

FEATURE_DIR="docs/specs/$FEATURE_ID"

if [ -z "$OUTPUT_PATH" ]; then
    case "$FORMAT" in
        csv) OUTPUT_PATH="$FEATURE_DIR/traceability.csv" ;;
        markdown) OUTPUT_PATH="$FEATURE_DIR/traceability.md" ;;
    esac
fi

python3 << PYEOF
from pathlib import Path
from sdlc_programme_scripts.programme.traceability import (
    TraceabilityError, export_csv, export_markdown,
)

format = "$FORMAT"
feature_id = "$FEATURE_ID"
feature_dir = Path("$FEATURE_DIR")
output_path = Path("$OUTPUT_PATH")

try:
    if format == "csv":
        text = export_csv(feature_dir, feature_id)
    elif format == "markdown":
        text = export_markdown(feature_dir, feature_id)
except TraceabilityError as e:
    print(f"ERROR: {e}", flush=True)
    raise SystemExit(1)

output_path.parent.mkdir(parents=True, exist_ok=True)
output_path.write_text(text)
print(f"Wrote {format} traceability matrix to {output_path}")
PYEOF
```

## Done

Report:

- Format used (csv or markdown)
- Output path
- Number of REQ rows in the matrix
- Any orphan REQs (declared but no DES/TEST satisfying them) — these are coverage gaps the team should resolve

## Model selection

This skill runs deterministic Python helpers. Smaller models are sufficient.
