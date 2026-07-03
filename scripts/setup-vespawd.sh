#!/usr/bin/env sh
# One-time Vespawd setup (installs the Vedaws runtime).
set -e
SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
FRAMEWORK_ROOT="$(dirname -- "$SCRIPT_DIR")"
cd "$FRAMEWORK_ROOT"
exec python "$SCRIPT_DIR/setup.py" "$@"
