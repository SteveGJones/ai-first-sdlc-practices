#!/bin/bash
# Detect whether the Archon loop completion signal bug is present.
# Returns 0 if the bug IS present (workaround needed).
# Returns 1 if the bug is NOT present (workaround not needed).
#
# Conditional — same pattern as the ARM64 workaround. When Archon
# fixes bug #1126, this detection returns 1 and the workaround skips.

# Check if Archon has a known fix marker (version check or code grep)
if archon --version 2>/dev/null | grep -q "loop-signal-fix"; then
    echo "Loop signal bug: FIXED in this Archon version"
    exit 1
fi

# Check if the Archon source has the fix applied
if [ -f /opt/archon/packages/workflows/src/dag-executor.ts ]; then
    if grep -q 'loopSignalFixed' /opt/archon/packages/workflows/src/dag-executor.ts 2>/dev/null; then
        echo "Loop signal bug: FIXED (detected in source)"
        exit 1
    fi
fi

echo "Loop signal bug: PRESENT (workaround will be active)"
exit 0
