#!/usr/bin/env sh
# Create a new Vespawd project (interactive by default).
set -e
SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
FRAMEWORK_ROOT="$(dirname -- "$SCRIPT_DIR")"
cd "$FRAMEWORK_ROOT"
exec python "$SCRIPT_DIR/new_project.py" "$@"
