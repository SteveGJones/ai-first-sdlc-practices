#!/bin/bash
# Apply SDLC patches to Archon for ContainerProvider + per-node image support.
# All patches are conditional — skip if the feature already exists.
#
# See: https://github.com/coleam00/Archon/issues/1197
set -e

ARCHON_DIR="${1:-/opt/archon}"
PATCHES_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== SDLC Archon Patches ==="

# Patch 1: ContainerProvider (additive — new file)
PROVIDER_DIR="$ARCHON_DIR/packages/isolation/src/providers"
if [ -f "$PROVIDER_DIR/container.ts" ]; then
    echo "[1/3] ContainerProvider: SKIP (already exists)"
else
    if [ -d "$PROVIDER_DIR" ]; then
        echo "[1/3] ContainerProvider: APPLYING"
        cp "$PATCHES_DIR/container-provider.ts" "$PROVIDER_DIR/container.ts"
    else
        echo "[1/3] ContainerProvider: SKIP (provider directory not found at $PROVIDER_DIR)"
    fi
fi

# Patch 2: Node schema — add image? field
NODE_SCHEMA="$ARCHON_DIR/packages/workflows/src/schemas/dag-node.ts"
if [ -f "$NODE_SCHEMA" ]; then
    if grep -q 'image\?' "$NODE_SCHEMA" 2>/dev/null; then
        echo "[2/3] Node schema image field: SKIP (already exists)"
    else
        echo "[2/3] Node schema image field: APPLYING"
        # Add image?: string field after the command field in the schema
        sed -i 's/command:/command:\n  image?: string;  \/\/ Docker image for container isolation (SDLC patch)/' \
            "$NODE_SCHEMA"
        # D-M-1: verify the edit landed.  Silent sed failure (mismatched
        # BRE vs ERE, file moved, sed variant quirk) would otherwise leave
        # a broken image but an apparently-successful build.
        if ! grep -q 'image?: string' "$NODE_SCHEMA"; then
            echo "ERROR: Patch 2 failed to apply — 'image?: string' not found in $NODE_SCHEMA after sed."
            exit 1
        fi
    fi
else
    echo "[2/3] Node schema: SKIP (file not found at $NODE_SCHEMA)"
fi

# Patch 3: Executor — route image: nodes to ContainerProvider
EXECUTOR="$ARCHON_DIR/packages/workflows/src/dag-executor.ts"
if [ -f "$EXECUTOR" ]; then
    if grep -q 'ContainerProvider' "$EXECUTOR" 2>/dev/null; then
        echo "[3/3] Executor container routing: SKIP (already exists)"
    else
        echo "[3/3] Executor container routing: APPLYING"
        # Add import at top of file
        sed -i '1i\import { ContainerProvider } from "../isolation/src/providers/container";  // SDLC patch' \
            "$EXECUTOR"
        # D-M-1: verify the edit landed.
        if ! grep -q 'ContainerProvider' "$EXECUTOR"; then
            echo "ERROR: Patch 3 failed to apply — 'ContainerProvider' import not found in $EXECUTOR after sed."
            exit 1
        fi
    fi
else
    echo "[3/3] Executor: SKIP (file not found at $EXECUTOR)"
fi

echo "=== Patches complete ==="
