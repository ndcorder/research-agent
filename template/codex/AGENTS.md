# Research Paper Writing Agent

Scientific paper writing workspace powered by Codex with shared pipeline files and runtime-specific command adapters.

## Runtime

This project is configured for the `codex` runtime.

Read these files first when running major commands:

1. `.paper.json`
2. `.codex/commands/<command>.md`
3. `.codex/pipeline/shared-protocols.md`
4. `.codex/pipeline/<stage>.md` as each stage requires
5. `.codex/runtime-contract.md`

## Codex Adapter Rules

1. `.paper-state.json` is the execution source of truth. Update it after every completed stage or section.
2. Use `update_plan` for visible progress tracking. Keep one in-progress step at a time.
3. Use sub-agents only for bounded, sidecar work that does not block the next local step.
4. Shared pipeline files may still mention Claude task APIs, model ids, or `.claude/skills/` paths. Translate those using `.codex/runtime-contract.md`.
5. The active skills directory is `.codex/skills/`.
6. If a legacy stage calls for Codex Bridge as an external reviewer, skip that external-review step. Record the skip in `.paper-state.json` and continue.
7. Prefer file-based resume semantics over runtime memory. Re-read instructions from disk before each stage.

## Command Entry

Use the runtime-neutral launcher from the project root:

```bash
scripts/run-paper-command <command> [args...]
```

Examples:

```bash
scripts/run-paper-command write-paper
scripts/run-paper-command preview-pipeline
scripts/run-paper-command health
scripts/run-paper-command targeted-research --claims C1,C4
```

## Interactive Use

If you are running interactively in Codex, this repository root `AGENTS.md` is a symlink to `.codex/AGENTS.md`. Treat the `.codex/commands/*.md` files as the source of truth for command behavior.
