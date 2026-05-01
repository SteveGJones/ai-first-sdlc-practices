---
name: phase-review
description: Dispatch a structured cross-phase review of a phase artefact. MANDATORY for design-spec and test-spec; the gate validator checks for the resulting review record before passing. Recommended for requirements-spec.
disable-model-invocation: false
argument-hint: "<phase> <feature-id>"
---
<!-- implements: DES-programme-skills-004 -->

# Cross-Phase Review

Dispatch a structured review of a phase artefact against its cited prior artefacts.

## Arguments

- `<phase>` — one of `requirements`, `design`, `test`
- `<feature-id>` — short slug for the feature

## Why this is mandatory for design and test

`phase-gate` checks structure: do citations resolve to declared IDs? `phase-review` checks meaning: do the citations actually capture the requirement / design intent? Programme Article 14 requires the review record for design-spec and test-spec — the gate validator looks for `docs/specs/<feature-id>/reviews/<phase>-review-*.md` before passing.

## Steps

```bash
PHASE="$1"
FEATURE_ID="$2"

if [ -z "$PHASE" ] || [ -z "$FEATURE_ID" ]; then
    echo "Usage: phase-review <phase> <feature-id>" >&2
    exit 1
fi

case "$PHASE" in
    requirements|design|test) ;;
    *)
        echo "phase must be one of: requirements, design, test" >&2
        exit 1
        ;;
esac

FEATURE_DIR="docs/specs/$FEATURE_ID"
SPEC_PATH="$FEATURE_DIR/$PHASE-spec.md"

if [ ! -f "$SPEC_PATH" ]; then
    echo "$SPEC_PATH does not exist; run phase-init $PHASE $FEATURE_ID first" >&2
    exit 1
fi

REVIEWS_DIR="$FEATURE_DIR/reviews"
mkdir -p "$REVIEWS_DIR"

# Determine reviewer agent based on phase
case "$PHASE" in
    requirements)
        REVIEWER_AGENT="sdlc-team-common:solution-architect"
        REVIEWER_LABEL="solution-architect"
        ;;
    design)
        REVIEWER_AGENT="sdlc-team-common:solution-architect"
        REVIEWER_LABEL="solution-architect"
        ;;
    test)
        REVIEWER_AGENT="sdlc-team-fullstack:backend-architect"
        REVIEWER_LABEL="backend-architect"
        ;;
esac

REVIEW_PATH="$REVIEWS_DIR/$PHASE-review-$REVIEWER_LABEL.md"
```

Now use the `Agent` tool to dispatch `$REVIEWER_AGENT` (substituting the value from the bash variable) with this prompt:

```
You are reviewing a $PHASE-spec for feature $FEATURE_ID.

Read the artefact at: $SPEC_PATH

Required prior artefacts to read:
- For design phase: docs/specs/$FEATURE_ID/requirements-spec.md (the requirements being satisfied)
- For test phase: both docs/specs/$FEATURE_ID/requirements-spec.md AND docs/specs/$FEATURE_ID/design-spec.md

Your review must answer:

1. **Coverage**: are all REQ-IDs from the prior phase(s) addressed by this artefact's elements?
2. **Soundness**: do the satisfies references make semantic sense — does each cited DES/TEST actually address what the cited REQ/DES says?
3. **Completeness**: are there obvious requirements / design elements missing that should have been declared?
4. **Out-of-scope cleanliness**: does the artefact stay within scope, or does it sneak in elements that don't trace back?

Return your review as a markdown file with these sections:
- ## Reviewer
- ## Coverage assessment
- ## Soundness assessment
- ## Completeness assessment
- ## Out-of-scope concerns
- ## Verdict: APPROVE / NEEDS-REWORK / NOT-APPROVED

Save the review to: $REVIEW_PATH (use the Write tool)
```

After the agent dispatch completes, verify the review file was created:

```bash
if [ -f "$REVIEW_PATH" ]; then
    echo "Review record created at $REVIEW_PATH"
    git add "$REVIEW_PATH"
    echo "Stage the review record with the next commit."
else
    echo "ERROR: $REVIEW_PATH was not created" >&2
    exit 1
fi
```

## Done

Report:

- Phase artefact reviewed
- Reviewer agent used (`solution-architect` for design; `backend-architect` for test)
- Review record path
- Verdict from the review (APPROVE / NEEDS-REWORK / NOT-APPROVED)

If verdict is NEEDS-REWORK or NOT-APPROVED, the user must address the review's findings before commit/push.

## Model selection

This skill is **structured comparison and reasoning** — comparing artefacts against prior phases, surfacing semantic gaps. Prefer a model with strong reasoning over one optimised for throughput. Reviewer agents (`solution-architect`, `backend-architect`) are dispatched via the Agent tool; they should run on a high-quality model.
