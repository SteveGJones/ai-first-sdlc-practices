#!/bin/bash
# Loop signal workaround for Archon bug #1126.
#
# After each loop iteration, scans the output directory for the
# completion signal pattern. If found, writes a sentinel file and
# exits cleanly, even when Archon reports max_iterations_reached.
#
# This script is sourced by the entrypoint when:
# 1. The loop bug is detected as present
# 2. The current workflow uses loop nodes
#
# Self-deactivating: detect-loop-bug.sh is checked on every container start.
# When Archon fixes the bug, detection returns non-zero and this script
# is never sourced.
#
# See: docs/issues/archon-loop-completion-signal.md
# See: https://github.com/coleam00/Archon/issues/1197

SENTINEL_FILE="${WORKSPACE:-.}/.archon-loop-complete"

check_loop_completion() {
    local signal_pattern="${1:-LOOP_COMPLETE}"
    local output_dir="${WORKSPACE:-.}/.archon/output"

    if [ -d "$output_dir" ]; then
        if grep -rq "$signal_pattern" "$output_dir" 2>/dev/null; then
            echo "[loop-workaround] Completion signal '$signal_pattern' detected in output"
            touch "$SENTINEL_FILE"
            return 0
        fi
    fi
    return 1
}

cleanup_sentinel() {
    rm -f "$SENTINEL_FILE"
}

export -f check_loop_completion
export -f cleanup_sentinel
export SENTINEL_FILE
