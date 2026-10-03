#!/bin/bash
set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
case "${1:-base}" in
    base) bash "$SCRIPT_DIR/build-base.sh" ;;
    full) bash "$SCRIPT_DIR/build-full.sh" ;;
    *) echo "Usage: build.sh [base|full]"; exit 1 ;;
esac
