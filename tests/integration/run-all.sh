#!/bin/bash
# Run all sdlc-workflows integration test layers with a common reporter.
#
# Layers (outermost first):
#   python      — tests/integration/workforce-smoke/run-python-integration.sh
#                 Pure-Python management-script integration (8 checks)
#   docker      — tests/integration/workforce-smoke/run-containers.sh
#                 Container-build + Phase 5 hardening smoke (20 checks)
#   acceptance  — tests/integration/workforce-smoke/run-acceptance.sh
#                 Real Claude Code auth + execution (7 checks)
#   e2e         — tests/integration/workforce-smoke/run-e2e.sh
#                 Sequential + parallel Archon orchestration (14 checks)
#   formation   — tests/integration/workforce-smoke/run-full-formation.sh
#                 §7.4 multi-team super-smoke: 4 teams, 6 nodes, every
#                 override propagated (12 structural checks)
#
# Flags:
#   --no-python       Skip the python layer
#   --no-docker       Skip the docker-image / container smoke layer
#   --no-acceptance   Skip the acceptance layer (fastest feedback loop)
#   --no-e2e          Skip the end-to-end orchestration layer
#   --no-formation    Skip the §7.4 multi-team super-smoke
#
# Exit code is 0 iff every selected layer exited 0.  Each layer's own
# banner is preserved; this script adds a single summary block at the end.

set -u

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SMOKE_DIR="$SCRIPT_DIR/workforce-smoke"

RUN_PYTHON=1
RUN_DOCKER=1
RUN_ACCEPTANCE=1
RUN_E2E=1
RUN_FORMATION=1

for arg in "$@"; do
    case "$arg" in
        --no-python)     RUN_PYTHON=0 ;;
        --no-docker)     RUN_DOCKER=0 ;;
        --no-acceptance) RUN_ACCEPTANCE=0 ;;
        --no-e2e)        RUN_E2E=0 ;;
        --no-formation)  RUN_FORMATION=0 ;;
        -h|--help)
            sed -n '1,25p' "$0" | sed 's/^# \{0,1\}//'
            exit 0
            ;;
        *)
            echo "Unknown flag: $arg" >&2
            exit 2
            ;;
    esac
done

declare -a LAYER_NAMES
declare -a LAYER_RESULTS

run_layer() {
    local name="$1"
    local script="$2"
    echo ""
    echo "================================================================"
    echo "  LAYER: $name"
    echo "  Script: $script"
    echo "================================================================"
    if bash "$script"; then
        LAYER_NAMES+=("$name")
        LAYER_RESULTS+=("PASS")
    else
        LAYER_NAMES+=("$name")
        LAYER_RESULTS+=("FAIL")
    fi
}

[ "$RUN_PYTHON" -eq 1 ] && run_layer "python" "$SMOKE_DIR/run-python-integration.sh"
[ "$RUN_DOCKER" -eq 1 ] && run_layer "docker" "$SMOKE_DIR/run-containers.sh"
[ "$RUN_ACCEPTANCE" -eq 1 ] && run_layer "acceptance" "$SMOKE_DIR/run-acceptance.sh"
[ "$RUN_E2E" -eq 1 ] && run_layer "e2e" "$SMOKE_DIR/run-e2e.sh"
[ "$RUN_FORMATION" -eq 1 ] && run_layer "formation" "$SMOKE_DIR/run-full-formation.sh"

echo ""
echo "================================================================"
echo "  SUMMARY"
echo "================================================================"
ANY_FAIL=0
for idx in "${!LAYER_NAMES[@]}"; do
    name="${LAYER_NAMES[$idx]}"
    result="${LAYER_RESULTS[$idx]}"
    printf "  %-12s %s\n" "$name" "$result"
    [ "$result" = "FAIL" ] && ANY_FAIL=1
done

if [ "$ANY_FAIL" -eq 0 ]; then
    echo ""
    echo "All integration layers: PASS"
    exit 0
else
    echo ""
    echo "One or more integration layers: FAIL"
    exit 1
fi
