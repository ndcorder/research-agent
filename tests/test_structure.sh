#!/usr/bin/env bash
# Verify every pipeline file referenced in write-paper.md actually exists,
# every command referenced in CLAUDE.md exists, and all venue JSONs are valid.
# Exit 0 if all pass, 1 if any fail.

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TEMPLATE="$REPO_ROOT/template"
FAIL=0
PASS_COUNT=0
FAIL_COUNT=0

pass() { echo "  PASS: $1"; PASS_COUNT=$((PASS_COUNT + 1)); }
fail() { echo "  FAIL: $1"; FAIL_COUNT=$((FAIL_COUNT + 1)); FAIL=1; }

# ---------- 1. Pipeline files referenced in write-paper.md ----------
echo "=== Pipeline file references (write-paper.md) ==="

while IFS= read -r line; do
    # Extract the pipeline filename from backtick-quoted paths like `pipeline/stage-1-research.md`
    file=$(echo "$line" | grep -oE 'pipeline/[a-z0-9._-]+\.md' | head -1)
    [ -z "$file" ] && continue
    if [ -f "$TEMPLATE/claude/$file" ]; then
        pass "$file"
    else
        fail "$file — referenced but missing"
    fi
done < "$TEMPLATE/claude/commands/write-paper.md"

# ---------- 2. Commands referenced in CLAUDE.md ----------
echo ""
echo "=== Command references (CLAUDE.md) ==="

while IFS= read -r line; do
    # Extract command name from lines like "- `/foo-bar` — description"
    cmd=$(echo "$line" | grep -oE '`/[a-z][-a-z0-9]*`' | tr -d '`/' | head -1)
    [ -z "$cmd" ] && continue
    # Deduplicate: some commands appear more than once (e.g. /export-sources, /import-sources)
    if [ -f "$TEMPLATE/claude/commands/${cmd}.md" ]; then
        pass "/$cmd -> commands/${cmd}.md"
    else
        fail "/$cmd — no matching commands/${cmd}.md"
    fi
done < <(grep -E '^\- `/[a-z]' "$TEMPLATE/claude/CLAUDE.md" | sort -u)

# Also check that write-paper command exists (it's the primary pipeline entry)
if [ -f "$TEMPLATE/claude/commands/write-paper.md" ]; then
    pass "/write-paper -> commands/write-paper.md"
else
    fail "/write-paper — no matching commands/write-paper.md"
fi

# ---------- 3. Venue JSON validation ----------
echo ""
echo "=== Venue JSON validation ==="

for json_file in "$TEMPLATE/venues"/*.json; do
    basename=$(basename "$json_file")
    if python3 -c "import json; json.load(open('$json_file'))" 2>/dev/null; then
        pass "$basename — valid JSON"
    else
        fail "$basename — invalid JSON"
    fi
    # Validate preamble_extra and forbidden_packages are present and are arrays
    if python3 -c "
import json, sys
d = json.load(open('$json_file'))
assert isinstance(d.get('preamble_extra'), list), 'preamble_extra missing or not array'
assert isinstance(d.get('forbidden_packages'), list), 'forbidden_packages missing or not array'
" 2>/dev/null; then
        pass "$basename — has preamble_extra and forbidden_packages arrays"
    else
        fail "$basename — missing preamble_extra or forbidden_packages array"
    fi
done

# ---------- 4. Pipeline stage files reference consistency ----------
echo ""
echo "=== Pipeline stage files exist on disk ==="

for md_file in "$TEMPLATE/claude/pipeline"/*.md; do
    basename=$(basename "$md_file")
    if [ -f "$md_file" ]; then
        pass "$basename"
    else
        fail "$basename — listed but missing"
    fi
done

# ---------- Summary ----------
echo ""
echo "==============================="
echo "  PASSED: $PASS_COUNT"
echo "  FAILED: $FAIL_COUNT"
echo "==============================="

exit $FAIL
