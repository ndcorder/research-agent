# Write Paper — Codex Runtime Orchestrator

Run the full autonomous paper-writing pipeline under Codex.

## Instructions

1. Read `.paper.json` and treat `runtime: "codex"` as authoritative.
2. Read `.codex/runtime-contract.md` and apply its compatibility rules to all shared pipeline files.
3. Read `.venue.json` if present, then `main.tex` and `references.bib`.
4. Read `.paper-state.json` if present and resume from it. `.paper-state.json` is the source of truth.
5. Run the same preflight checks and project initialization expected by the legacy `/write-paper` flow.
6. Read `.codex/pipeline/shared-protocols.md` once at startup, then re-read each stage file from `.codex/pipeline/` immediately before executing that stage.
7. Follow the shared stage order from the pipeline, but skip legacy external-Codex stages when Codex is the active runtime:
   - `stage-1c-codex-crosscheck.md`
   - `stage-2b-codex-thesis.md`
   - any Codex-bridge substep inside later stages
   Record each skip in `.paper-state.json` with a note that the active runtime cannot act as an external reviewer.
8. Translate shared legacy references as follows:
   - `.claude/skills/...` => `.codex/skills/...`
   - Claude task primitives => `update_plan` plus `.paper-state.json`
   - `claude-opus-4-6[1m]` => deep reasoning / writing tier
   - `claude-sonnet-4-6[1m]` => tool-heavy research / review tier
9. Use sub-agents only for bounded research, review, or writing sidecars. Keep control flow in the main agent.
10. Preserve all artifact contracts, provenance logging, resume semantics, and quality gates from the shared pipeline files.

$ARGUMENTS
