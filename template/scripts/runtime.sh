#!/usr/bin/env bash
set -euo pipefail

paper_json_value() {
    local key="$1"
    local default_value="${2:-}"

    if [[ ! -f .paper.json ]]; then
        printf '%s\n' "$default_value"
        return 0
    fi

    python3 - "$key" "$default_value" <<'PYEOF' 2>/dev/null || printf '%s\n' "$default_value"
import json
import sys

key = sys.argv[1]
default = sys.argv[2]

try:
    with open(".paper.json", "r", encoding="utf-8") as handle:
        data = json.load(handle)
except Exception:
    print(default)
    raise SystemExit(0)

value = data.get(key, default)
if value is None:
    value = default
print(value)
PYEOF
}

paper_runtime() {
    paper_json_value "runtime" "claude"
}

paper_runtime_dir() {
    case "$(paper_runtime)" in
        codex) printf '.codex\n' ;;
        *) printf '.claude\n' ;;
    esac
}
