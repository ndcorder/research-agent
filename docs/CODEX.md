# Codex Runtime Guide

Research Agent can run paper projects with Codex instead of Claude.

## Create a Codex Project

```bash
create-paper my-paper "Your topic" --runtime codex
cd my-paper
```

This writes `"runtime": "codex"` to `.paper.json` and scaffolds:

- `.codex/AGENTS.md`
- `.codex/commands/`
- `.codex/pipeline/`
- `.codex/skills/`
- `AGENTS.md` -> `.codex/AGENTS.md`

## Run Commands

Use the runtime-neutral launcher:

```bash
write-paper
scripts/run-paper-command preview-pipeline
scripts/run-paper-command health
scripts/run-paper-command targeted-research --claims C1,C2
```

`write-paper` reads `.paper.json` and dispatches to the active runtime automatically.

## Notes

- Shared paper artifacts stay the same across runtimes.
- Shared pipeline files live in `template/shared/pipeline/`.
- Codex projects reuse the same scientific skills through `.codex/skills/`.
- Most Codex command files are thin wrappers over the existing command instructions, interpreted through the runtime contract.
- Legacy external-Codex review stages are skipped when Codex is the active harness.
