#!/usr/bin/env bash
# Ensure .venv exists in the research-agent repo root.
# Usage: eval "$(bash /path/to/ensure-venv.sh)"
#   Sets VENV_PYTHON to the venv's python3 path.
set -euo pipefail

SOURCE="${BASH_SOURCE[0]}"
while [[ -L "$SOURCE" ]]; do
    DIR="$(cd "$(dirname "$SOURCE")" && pwd)"
    SOURCE="$(readlink "$SOURCE")"
    [[ "$SOURCE" != /* ]] && SOURCE="$DIR/$SOURCE"
done
SCRIPTS_DIR="$(cd "$(dirname "$SOURCE")" && pwd)"
REPO_ROOT="$(cd "$SCRIPTS_DIR/../.." && pwd)"
VENV_DIR="$REPO_ROOT/.venv"
REQ_FILE="$SCRIPTS_DIR/requirements-knowledge.txt"
STAMP_FILE="$VENV_DIR/.requirements-stamp"

if [[ ! -d "$VENV_DIR" ]]; then
    echo "Creating Python venv at $VENV_DIR ..." >&2
    python3 -m venv "$VENV_DIR"
fi

REQ_HASH=$(shasum -a 256 "$REQ_FILE" 2>/dev/null | cut -d' ' -f1)
STAMP_HASH=""
[[ -f "$STAMP_FILE" ]] && STAMP_HASH=$(cat "$STAMP_FILE")

if [[ "$REQ_HASH" != "$STAMP_HASH" ]]; then
    echo "Installing/updating dependencies ..." >&2
    "$VENV_DIR/bin/pip" install -q -r "$REQ_FILE"
    echo "$REQ_HASH" > "$STAMP_FILE"
fi

echo "VENV_PYTHON='$VENV_DIR/bin/python3'"
