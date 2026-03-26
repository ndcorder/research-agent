#!/usr/bin/env bash
# Scan pipeline and command files for known prompt anti-patterns.
# Exit 0 if clean, 1 if issues found.

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TEMPLATE="$REPO_ROOT/template"
PIPELINE="$TEMPLATE/claude/pipeline"
COMMANDS="$TEMPLATE/claude/commands"
ISSUES=0
ISSUE_COUNT=0

issue() {
    echo "  ISSUE: $1"
    ISSUE_COUNT=$((ISSUE_COUNT + 1))
    ISSUES=1
}

# Collect all target files
PROMPT_FILES=()
for f in "$PIPELINE"/*.md "$COMMANDS"/*.md; do
    [ -f "$f" ] && PROMPT_FILES+=("$f")
done

# ---------- 1. Haiku references ----------
echo "=== Check: No haiku model references ==="

for f in "${PROMPT_FILES[@]}"; do
    while IFS= read -r match; do
        lineno=$(echo "$match" | cut -d: -f1)
        content=$(echo "$match" | cut -d: -f2-)
        # Skip rule statements like "Never use Haiku"
        echo "$content" | grep -qi 'never use haiku' && continue
        issue "$(basename "$f"):$lineno — references 'haiku' (forbidden model)"
    done < <(grep -ni 'haiku' "$f" 2>/dev/null || true)
done

if [ "$ISSUE_COUNT" -eq 0 ]; then echo "  OK — no haiku references found"; fi
PREV_COUNT=$ISSUE_COUNT

# ---------- 2. Model references without [1m] suffix ----------
echo ""
echo "=== Check: Model references include [1m] suffix ==="

for f in "${PROMPT_FILES[@]}"; do
    # Match bare claude-opus-4-6 or claude-sonnet-4-6 NOT followed by [1m]
    # Use perl for negative lookahead
    while IFS= read -r match; do
        lineno=$(echo "$match" | cut -d: -f1)
        content=$(echo "$match" | cut -d: -f2-)
        issue "$(basename "$f"):$lineno — bare model ref without [1m]:$(echo "$content" | head -c 80)"
    done < <(perl -ne 'print "$.:$_" if /claude-(?:opus|sonnet)-4-6(?!\[1m\])/' "$f" 2>/dev/null || true)
done

if [ "$ISSUE_COUNT" -eq "$PREV_COUNT" ]; then echo "  OK — all model refs have [1m] suffix"; fi
PREV_COUNT=$ISSUE_COUNT

# ---------- 3. Pipeline stage files start with Prerequisites referencing shared-protocols.md ----------
echo ""
echo "=== Check: Pipeline stages have Prerequisites line ==="

for f in "$PIPELINE"/*.md; do
    bname=$(basename "$f")
    # Skip shared-protocols.md itself
    [ "$bname" = "shared-protocols.md" ] && continue

    # Check first 5 lines for a Prerequisites line referencing shared-protocols.md
    if ! head -5 "$f" | grep -qi 'prerequisites.*shared-protocols'; then
        issue "$bname — missing Prerequisites line referencing shared-protocols.md in first 5 lines"
    fi
done

if [ "$ISSUE_COUNT" -eq "$PREV_COUNT" ]; then echo "  OK — all stages reference shared-protocols.md"; fi
PREV_COUNT=$ISSUE_COUNT

# ---------- 4. Duplicate large blocks (5+ consecutive lines shared between shared-protocols.md and stage files) ----------
echo ""
echo "=== Check: No duplicate blocks between shared-protocols.md and stage files ==="

SHARED="$PIPELINE/shared-protocols.md"
if [ -f "$SHARED" ]; then
    SHARED_LINES=$(wc -l < "$SHARED")
    WINDOW=5

    for f in "$PIPELINE"/*.md; do
        [ "$f" = "$SHARED" ] && continue
        bname=$(basename "$f")
        found_dup=0

        # Read stage file into a variable for substring matching
        stage_content=$(cat "$f")

        line_num=0
        while IFS= read -r _; do
            line_num=$((line_num + 1))
            [ "$line_num" -gt $((SHARED_LINES - WINDOW + 1)) ] && break

            # Build a 5-line block starting at line_num
            block=$(sed -n "${line_num},$((line_num + WINDOW - 1))p" "$SHARED")

            # Skip blocks that are mostly blank or markdown separators
            non_empty=$(echo "$block" | grep -cve '^\s*$' -e '^---' -e '^```' -e '^#' || true)
            [ "$non_empty" -lt 4 ] && continue

            # Check if the exact consecutive block appears in the stage file
            # Use python for reliable multi-line substring matching
            if python3 -c "
import sys
block = open('$SHARED').readlines()[$((line_num - 1)):$((line_num - 1 + WINDOW))]
block_str = ''.join(block)
stage = open(sys.argv[1]).read()
sys.exit(0 if block_str in stage else 1)
" "$f" 2>/dev/null; then
                issue "$bname — duplicates 5+ consecutive lines from shared-protocols.md (near shared line $line_num)"
                found_dup=1
                break
            fi
        done < "$SHARED"
    done
fi

if [ "$ISSUE_COUNT" -eq "$PREV_COUNT" ]; then echo "  OK — no duplicate blocks found"; fi
PREV_COUNT=$ISSUE_COUNT

# ---------- 5. TODO / FIXME / HACK in pipeline files ----------
echo ""
echo "=== Check: No TODO/FIXME/HACK in pipeline files ==="

for f in "$PIPELINE"/*.md; do
    while IFS= read -r match; do
        lineno=$(echo "$match" | cut -d: -f1)
        content=$(echo "$match" | cut -d: -f2-)
        # Skip lines that mention TODO/FIXME as things to check FOR (inside agent prompts)
        echo "$content" | grep -qiE '(no TODO|No TODO|check.*TODO|placeholder.*TODO|TODO.*TBD.*FIXME)' && continue
        issue "$(basename "$f"):$lineno —$(echo "$content" | head -c 80)"
    done < <(grep -nEi '\b(TODO|FIXME|HACK)\b' "$f" 2>/dev/null || true)
done

if [ "$ISSUE_COUNT" -eq "$PREV_COUNT" ]; then echo "  OK — no TODO/FIXME/HACK found"; fi
PREV_COUNT=$ISSUE_COUNT

# ---------- 6. Agent prompts specify a model ----------
echo ""
echo "=== Check: Agent prompts in pipeline files specify a model ==="

for f in "$PIPELINE"/*.md; do
    bname=$(basename "$f")
    # Find lines that define specific agent prompts (with parenthetical model specs)
    # Pattern: "Spawn a/an ... agent" or "**Agent N —" — these are agent definitions
    while IFS= read -r match; do
        lineno=$(echo "$match" | cut -d: -f1)
        content=$(echo "$match" | cut -d: -f2-)

        # Check if this agent line includes a model specification
        # Accept both model: "claude-..." and model: claude-... (with or without quotes)
        # Also accept (model: ...) in backticks
        if ! echo "$content" | grep -qE 'model:\s*["`'"'"']?claude-'; then
            issue "$bname:$lineno — agent prompt without model spec:$(echo "$content" | head -c 80)"
        fi
    done < <(grep -nE '(Spawn (a |an |the )\*\*.*\*\* agent|\*\*Agent [0-9]+)' "$f" 2>/dev/null || true)
done

if [ "$ISSUE_COUNT" -eq "$PREV_COUNT" ]; then echo "  OK — all agent prompts specify a model"; fi

# ---------- Summary ----------
echo ""
echo "==============================="
echo "  ISSUES FOUND: $ISSUE_COUNT"
echo "==============================="

exit $ISSUES
