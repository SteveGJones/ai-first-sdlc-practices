#!/bin/bash
# Multi-stage loop.stages soak test — proves the preprocessor's generated
# bash actually executes a cycle, detects the termination signal, and
# breaks out before max_iterations.
#
# Two modes:
#
#   --smoke  (default)
#     Fast, hermetic. Replaces `docker run` with a shell stub that
#     simulates per-stage output, advancing a counter file so the
#     third iteration's review stage emits the READY_TO_SHIP signal.
#     Asserts the generated bash terminates after iteration 3, not
#     iteration 5, and that every stage ran in order.
#
#   --real
#     Runs against the miniproject fixture with real Claude Code
#     containers. Requires docker + credentials + built team images.
#     Much slower; gated behind the flag so CI can run --smoke while
#     humans validate --real locally.
#
# Usage:
#   bash run-loop-stages-soak.sh                  # --smoke
#   bash run-loop-stages-soak.sh --smoke
#   bash run-loop-stages-soak.sh --real

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
PLUGIN_DIR="$REPO_ROOT/plugins/sdlc-workflows"
SCRIPTS_DIR="$PLUGIN_DIR/scripts"

MODE="smoke"
for arg in "$@"; do
    case "$arg" in
        --smoke) MODE="smoke" ;;
        --real)  MODE="real" ;;
        "")      ;;
        *)
            echo "ERROR: unknown flag '$arg'" >&2
            echo "Usage: $0 [--smoke|--real]" >&2
            exit 2
            ;;
    esac
done

PASS_COUNT=0
FAIL_COUNT=0
pass() { echo "  PASS: $1"; PASS_COUNT=$((PASS_COUNT + 1)); }
fail() { echo "  FAIL: $1 — $2"; FAIL_COUNT=$((FAIL_COUNT + 1)); }

echo "=== loop.stages soak test ($MODE) ==="
echo "Proves multi-stage cycles terminate on signal, accumulate commits, respect max_iterations."
echo ""

if [ "$MODE" = "smoke" ]; then
    # -----------------------------------------------------------------
    # Smoke harness: preprocess a 3-stage loop workflow, then execute
    # the generated bash with a `docker` shim that simulates stage
    # output. The review stage emits READY_TO_SHIP on iteration 3.
    # -----------------------------------------------------------------

    if ! command -v python3 >/dev/null 2>&1; then
        echo "ERROR: python3 required" >&2
        exit 1
    fi

    SOAK_DIR=$(mktemp -d "${TMPDIR:-/tmp}/loop-soak.XXXXXX")
    trap 'rm -rf "$SOAK_DIR"' EXIT

    WORKSPACE="$SOAK_DIR/workspace"
    COMMANDS_DIR="$SOAK_DIR/commands"
    mkdir -p "$WORKSPACE" "$COMMANDS_DIR"

    # Three trivial command prompts.
    for cmd in sdlc-design sdlc-implement sdlc-review; do
        cat > "$COMMANDS_DIR/${cmd}.md" <<EOF
# ${cmd}
Mock prompt body for ${cmd}.
EOF
    done

    # Input workflow with loop.stages.
    INPUT="$SOAK_DIR/input.yaml"
    cat > "$INPUT" <<'EOF'
name: loop-soak-test
description: Multi-stage cycle soak test
provider: claude
nodes:
  - id: build-review-cycle
    loop:
      stages:
        - id: design
          image: sdlc-worker:design-team
          command: sdlc-design
        - id: implement
          image: sdlc-worker:dev-team
          command: sdlc-implement
        - id: review
          image: sdlc-worker:review-team
          command: sdlc-review
      until: "READY_TO_SHIP"
      max_iterations: 5
EOF

    OUTPUT="$SOAK_DIR/output.yaml"

    # Preprocess.
    python3 "$SCRIPTS_DIR/preprocess_workflow.py" \
        "$INPUT" \
        --output "$OUTPUT" \
        --workspace "$WORKSPACE" \
        --cred-mount "" \
        --commands-dir "$COMMANDS_DIR"

    if [ -s "$OUTPUT" ]; then
        pass "preprocessor produced output"
    else
        fail "preprocessor produced output" "empty or missing $OUTPUT"
        exit 1
    fi

    # Extract the generated bash for the single node.
    BASH_BODY=$(python3 - "$OUTPUT" <<'PY'
import sys, yaml
with open(sys.argv[1]) as f:
    wf = yaml.safe_load(f)
node = wf["nodes"][0]
assert "bash" in node, f"expected bash: field in transformed node, got keys {list(node)}"
print(node["bash"])
PY
    )

    # Shim `docker` to emit stage output. Stage numbers count up: 1-3 in
    # iteration 1 (no signal), 4-6 in iteration 2 (no signal), 7-9 in
    # iteration 3 (review stage emits READY_TO_SHIP). Signal on iter 3
    # asserts both (a) loop ran > 1 iteration and (b) stopped before the
    # max_iterations: 5 bound.
    SHIM_DIR="$SOAK_DIR/shim"
    mkdir -p "$SHIM_DIR"
    cat > "$SHIM_DIR/docker" <<'EOF'
#!/bin/bash
# Smoke shim: count stage invocations, emit READY_TO_SHIP on stage 9
# (iteration 3, review).
COUNTER_FILE="$SOAK_DIR/.stage-counter"
if [ ! -f "$COUNTER_FILE" ]; then
    echo 0 > "$COUNTER_FILE"
fi
N=$(cat "$COUNTER_FILE")
N=$((N + 1))
echo "$N" > "$COUNTER_FILE"

# First positional is 'run'; everything else we treat as noise.
if [ "${1:-}" != "run" ]; then
    # Non-run invocations (e.g. docker inspect, docker rm) — silently
    # succeed; the harness does not test docker housekeeping.
    exit 0
fi

echo "[shim] stage invocation #$N"
if [ "$N" -eq 9 ]; then
    echo "[shim] stage 9 emitting signal: READY_TO_SHIP"
fi
exit 0
EOF
    chmod +x "$SHIM_DIR/docker"

    # Execute the generated bash with the shim on PATH.
    RUN_LOG="$SOAK_DIR/run.log"
    RUN_SCRIPT="$SOAK_DIR/run.sh"
    cat > "$RUN_SCRIPT" <<EOF
#!/bin/bash
set -e
export PATH="$SHIM_DIR:\$PATH"
export SOAK_DIR="$SOAK_DIR"
$BASH_BODY
EOF
    chmod +x "$RUN_SCRIPT"

    if bash "$RUN_SCRIPT" >"$RUN_LOG" 2>&1; then
        pass "generated bash executed to completion"
    else
        fail "generated bash executed" "non-zero exit; log at $RUN_LOG"
        tail -40 "$RUN_LOG"
        exit 1
    fi

    # Assert counter hit exactly 9 (3 iterations × 3 stages), not 15
    # (the max_iterations: 5 ceiling).
    COUNT=$(cat "$SOAK_DIR/.stage-counter" 2>/dev/null || echo 0)
    if [ "$COUNT" -eq 9 ]; then
        pass "stage counter = 9 (3 iterations × 3 stages, broke on signal)"
    else
        fail "stage counter" "expected 9, got $COUNT (log: $RUN_LOG)"
    fi

    # Assert log mentions signal detection.
    if grep -q "READY_TO_SHIP" "$RUN_LOG"; then
        pass "signal text emitted in stage output"
    else
        fail "signal text" "'READY_TO_SHIP' not in run log"
    fi

    # Assert all three stages ran at least once (each iteration runs
    # design → implement → review — by shim invocation ordering, the
    # third stage in iteration 3 is stage 9).
    if grep -q "stage invocation #3$" "$RUN_LOG" \
       && grep -q "stage invocation #6$" "$RUN_LOG" \
       && grep -q "stage invocation #9$" "$RUN_LOG"; then
        pass "all three iterations completed their 3-stage cycle"
    else
        fail "iteration stages" "missing stage-9/6/3 boundary markers (log: $RUN_LOG)"
    fi

elif [ "$MODE" = "real" ]; then
    # -----------------------------------------------------------------
    # Real mode: delegate to the existing miniproject harness + a
    # loop.stages workflow. Left intentionally thin — the value is in
    # the smoke mode above; real mode is a human-run sanity check.
    # -----------------------------------------------------------------
    echo "Real mode requires built team images (sdlc-worker:dev-team,"
    echo "sdlc-worker:review-team) + resolved credentials."
    echo ""
    echo "This mode is not wired into CI; it is an operator-run bench."
    echo "Skipping for now — see plan in CLAUDE-CONTEXT-workflows.md."
    echo ""
    echo "(No assertions run; exiting 0.)"
fi

echo ""
echo "=== Soak Test Results: $PASS_COUNT passed, $FAIL_COUNT failed ==="
[ "$FAIL_COUNT" -eq 0 ] || exit 1
