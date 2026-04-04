# Preview Pipeline — Codex Dry Run

Show what the autonomous pipeline will do under the Codex runtime without executing it.

## Instructions

1. Read `.paper.json`, `.venue.json` if present, `main.tex`, `references.bib`, and `.paper-state.json` if present.
2. Read `.codex/runtime-contract.md`.
3. Inspect the shared pipeline stage list from `.codex/pipeline/`.
4. Produce a dry-run plan that shows:
   - each stage in order
   - whether it will RUN, SKIP, or SKIP BY RUNTIME
   - current resume state from `.paper-state.json`
   - skills path as `.codex/skills/`
   - deep reasoning vs tool-heavy tier usage rather than Claude model ids
5. Mark legacy external-Codex review stages as `SKIP BY RUNTIME`.
6. Do not execute any stage work.

$ARGUMENTS
