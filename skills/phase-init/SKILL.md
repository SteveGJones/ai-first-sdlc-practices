---
name: phase-init
description: Instantiate a phase artefact (requirements-spec / design-spec / test-spec) from the Programme bundle's template into docs/specs/<feature-id>/. Refuses to overwrite existing artefacts.
disable-model-invocation: false
argument-hint: "<phase> <feature-id>"
---
<!-- implements: DES-programme-skills-002 -->

# Initialise a Phase Artefact

Instantiate a phase artefact from the Programme bundle's template.

## Arguments

- `<phase>` — one of `requirements`, `design`, `test`
- `<feature-id>` — short slug for the feature (e.g., `oauth-flow`, `cross-library-query`)

## Steps

```bash
PHASE="$1"
FEATURE_ID="$2"

if [ -z "$PHASE" ] || [ -z "$FEATURE_ID" ]; then
    echo "Usage: phase-init <phase> <feature-id>" >&2
    exit 1
fi

case "$PHASE" in
    requirements|design|test) ;;
    *)
        echo "phase must be one of: requirements, design, test" >&2
        exit 1
        ;;
esac

# Validate feature-id format (lowercase alphanumeric + hyphens, starting with alpha-numeric)
if ! echo "$FEATURE_ID" | grep -qE '^[a-z0-9][a-z0-9-]*$'; then
    echo "feature-id must match /^[a-z0-9][a-z0-9-]*$/" >&2
    exit 1
fi

FEATURE_DIR="docs/specs/$FEATURE_ID"
SPEC_PATH="$FEATURE_DIR/$PHASE-spec.md"

if [ -f "$SPEC_PATH" ]; then
    echo "$SPEC_PATH already exists; refusing to overwrite" >&2
    exit 1
fi

mkdir -p "$FEATURE_DIR"

# Locate the template — try project-installed first (./.sdlc/templates/), then fallback to plugin
if [ -f ".sdlc/templates/$PHASE-spec.md" ]; then
    TEMPLATE=".sdlc/templates/$PHASE-spec.md"
elif [ -f "$CLAUDE_PLUGIN_ROOT/templates/$PHASE-spec.md" ]; then
    TEMPLATE="$CLAUDE_PLUGIN_ROOT/templates/$PHASE-spec.md"
else
    echo "template for phase '$PHASE' not found (looked in .sdlc/templates/ and \$CLAUDE_PLUGIN_ROOT/templates/)" >&2
    exit 1
fi

# Copy template; substitute the feature-id placeholder
sed "s/<feature-id>/$FEATURE_ID/g" "$TEMPLATE" > "$SPEC_PATH"

echo "Created $SPEC_PATH from $TEMPLATE"
echo "Edit the file, then run: phase-gate $PHASE $FEATURE_ID"
```

## Done

Report:

- File created: `docs/specs/<feature-id>/<phase>-spec.md`
- Source template: shown in output
- Next step: edit the file, then `phase-gate <phase> <feature-id>`

## Model selection

This skill is mechanical (file copy + sed substitution). Smaller models are sufficient.
