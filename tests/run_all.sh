#!/usr/bin/env bash
# Run all tests and report summary.

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TOTAL=0
PASSED=0
FAILED=0
FAILED_NAMES=()

run_test() {
    local name="$1"
    local cmd="$2"
    ((TOTAL++))
    echo ""
    echo "================================================================"
    echo "  Running: $name"
    echo "================================================================"
    if eval "$cmd"; then
        ((PASSED++))
        echo ""
        echo "  >>> $name: PASSED"
    else
        ((FAILED++))
        FAILED_NAMES+=("$name")
        echo ""
        echo "  >>> $name: FAILED"
    fi
}

run_test "test_structure.sh" "bash '$SCRIPT_DIR/test_structure.sh'"
run_test "test_prompts.sh"   "bash '$SCRIPT_DIR/test_prompts.sh'"
run_test "test_schema.py"    "python3 '$SCRIPT_DIR/test_schema.py'"

# Python unit tests (reviewer-kb, knowledge). Exit code 5 = no tests collected (skip OK).
PYTEST_CMD="python3 -m pytest '$SCRIPT_DIR' -v --tb=short"
((TOTAL++))
echo ""
echo "================================================================"
echo "  Running: pytest"
echo "================================================================"
if eval "$PYTEST_CMD"; then
    ((PASSED++))
    echo ""
    echo "  >>> pytest: PASSED"
elif [ $? -eq 5 ]; then
    ((PASSED++))
    echo ""
    echo "  >>> pytest: SKIPPED (no tests collected)"
else
    ((FAILED++))
    FAILED_NAMES+=("pytest")
    echo ""
    echo "  >>> pytest: FAILED"
fi

echo ""
echo "================================================================"
echo "  SUMMARY: $PASSED/$TOTAL passed, $FAILED failed"
if [ "$FAILED" -gt 0 ]; then
    echo "  Failed tests:"
    for name in "${FAILED_NAMES[@]}"; do
        echo "    - $name"
    done
fi
echo "================================================================"

exit "$FAILED"
