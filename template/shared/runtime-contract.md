# Runtime Contract

This repository supports multiple execution harnesses over the same paper artifact model.

## Shared Artifacts

All runtimes operate on the same files:

- `main.tex`
- `references.bib`
- `.paper.json`
- `.paper-state.json`
- `research/`
- `reviews/`
- `figures/`
- `provenance/`

## Runtime Fields

`.paper.json` declares the active harness:

```json
{
  "runtime": "claude"
}
```

Supported values:

- `claude`
- `codex`

If `runtime` is absent, treat the project as `claude` for backward compatibility.

## Adapter Responsibilities

Each runtime adapter must define:

- launch command
- instructions file
- skills directory
- command invocation style
- progress reporting behavior
- child-agent strategy

## Runtime Matrix

| Capability | Claude | Codex |
| - | - | - |
| Harness id | `claude` | `codex` |
| Instructions file | `.claude/CLAUDE.md` | `.codex/AGENTS.md` |
| Skills directory | `.claude/skills/` | `.codex/skills/` |
| Command entrypoint | slash commands | `scripts/run-paper-command <command>` |
| Full pipeline launcher | `write-paper` -> `/write-paper` | `write-paper` -> `codex exec` |
| Progress source of truth | `.paper-state.json` plus runtime task UI | `.paper-state.json` plus `update_plan` |
| Child agents | Claude task agents | Codex sub-agents for bounded sidecar work |

## Compatibility Rules

Shared pipeline files still contain some Claude-era wording. Runtime adapters must reinterpret them as follows:

- `.claude/skills/...` means the active runtime skills directory.
- Claude task primitives such as `TaskCreate` and `TaskUpdate` mean runtime-native progress tracking plus `.paper-state.json` updates.
- Claude model ids are legacy tier markers:
  - `claude-opus-4-6[1m]` => deep reasoning / writing tier
  - `claude-sonnet-4-6[1m]` => tool-heavy research / review tier
- Slash command references mean the runtime's command entrypoint for the same command name.

## Codex-Specific Review Rule

When Codex is the active runtime, do not describe Codex as an external reviewer. Skip or relabel any legacy Codex-bridge stage that would make the orchestrator review itself as a third party.
