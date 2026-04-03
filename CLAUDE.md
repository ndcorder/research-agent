# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

Research Agent is an autonomous paper-writing harness for Claude Code. It scaffolds paper projects, symlinks shared templates/commands/pipeline instructions into them, and orchestrates a 19-stage pipeline that produces journal-quality LaTeX papers from a topic prompt.

**This repo is the template/toolkit itself, not a paper project.** Paper projects are created elsewhere via `create-paper` and symlink back here. Edits to `template/` propagate instantly to all paper projects.

## Development Commands

```bash
# Run all tests (structure, prompt linting, schema validation)
bash tests/run_all.sh

# Individual tests
bash tests/test_structure.sh          # Template file existence and structure
bash tests/test_prompts.sh            # Lint command/pipeline markdown syntax
python3 tests/test_schema.py          # Venue JSON schema + .paper-state.json schema

# Validate a specific paper state file
python3 tests/test_schema.py path/to/.paper-state.json

# Test a paper project end-to-end
create-paper test-paper "Test topic" --venue generic
cd test-paper && write-paper

# Format LaTeX to one-sentence-per-line (run from paper project)
python scripts/format_sentences.py main.tex
python scripts/format_sentences.py --check  # dry run
```

No build step, no linter beyond the test suite. CI runs `bash tests/run_all.sh` on Python 3.12.

## Architecture

### Two-layer design

1. **This repo** (`research-agent/`): contains the template, commands, pipeline stages, venues, scripts, and entry-point scripts (`create-paper`, `write-paper`, `sync-papers`).
2. **Paper projects** (created elsewhere): symlink `.claude/` back to `template/claude/`, so they inherit all commands and pipeline instructions.

### Entry points

- **`create-paper <name> <topic> [--venue V] [--depth D]`** (Bash): scaffolds a paper directory with `main.tex`, `.paper.json`, symlinked `.claude/`, cloned submodules (`vendor/claude-scientific-skills`, `vendor/praxis`), initial git commit.
- **`write-paper`** (Bash): thin launcher that runs `claude --dangerously-skip-permissions "/write-paper <TOPIC>"` inside a paper project.
- **`sync-papers <dir>`**: migrates old copy-based projects to symlinks.

### Pipeline orchestration (`template/claude/commands/write-paper.md`)

The `/write-paper` slash command (~200 lines) is the orchestrator. It does NOT contain stage logic inline. Instead it:

1. Reads `.paper.json` (topic, venue, depth) and `.venue.json` (format rules)
2. Reads `pipeline/shared-protocols.md` once for cross-cutting concerns
3. For each of 19 stages: reads `pipeline/stage-N-*.md` **fresh from disk** (prevents context compression from degrading late-stage instructions in multi-hour sessions)
4. Spawns parallel agents (Sonnet 1M for research/review, Opus 1M for writing/reasoning)
5. Checkpoints progress to `.paper-state.json` for resume-on-interrupt

Stages: research (5-12 parallel agents) -> snowballing -> co-citation -> codex cross-check -> source acquisition (14-resolver OA cascade) -> deep source reading (parallel agents read full PDFs) -> synthesis (cross-source analysis) -> planning -> codex thesis stress-test -> targeted research (deep only) -> novelty check -> assumptions -> section writing (sequential) -> coherence check -> reference integrity -> figures -> QA loop (parallel reviewers, adaptive convergence detection, up to 5-10 iterations) -> post-QA audits -> finalization.

### `/auto` improvement loop (`template/claude/commands/auto.md`)

Post-pipeline iterative improvement. Each iteration reads 4 phase files fresh from `pipeline/auto-phase-*.md`: assessment (5 parallel reviewer agents) -> prioritization (rank issues, consider cuts) -> execution (targeted research + revision) -> verification (regression check, quality gates).

### Key directories under `template/`

| Path | Purpose |
|-|-|
| `claude/commands/` | 46 slash commands (`.md` files). Symlinked into paper projects. |
| `claude/pipeline/` | 24 stage/phase instruction files read on-demand by orchestrators. `shared-protocols.md` has cross-cutting protocols (provenance logging, codex telemetry, tool fallback chain, Codex deliberation, domain detection, Semantic Scholar rate limiting). |
| `venues/` | 7 venue configs (JSON). Each specifies documentclass, packages, citation style, page limit, section order, and a 500+ word writing guide. |
| `template/scripts/knowledge.py` | LightRAG (>=1.4.12) knowledge graph builder (requires `OPENROUTER_API_KEY`). Supports optional OpenSearch backend (`LIGHTRAG_STORAGE=opensearch`). Builds from source extracts + PDFs, supports semantic queries, contradiction detection, evidence search. Venv auto-bootstraps on first run (`.venv/` at repo root). Supports streaming ingestion via `serve`/`enqueue` for non-blocking pipeline use. |
| `template/scripts/parse-pdf.py` | Docling-based PDF parser. Converts PDFs to markdown with extracted figures. Used by Stage 1d, 1e, and `/ingest-papers`. Requires `pip install docling`. |
| `template/scripts/update-manifest.py` | Rebuilds `research/source-manifest.json` from current project state. Scans bib, source extracts, PDFs, and parsed markdown to track all artifacts per source. |
| `template/scripts/format_sentences.py` | Reformats LaTeX to one-sentence-per-line for cleaner diffs. |
| `template/scripts/quality.py` | Multi-dimensional paper quality scorer (evidence, writing, structure, research, provenance). Stdlib-only. Produces JSON/text scorecards, persists scores to `~/.research-agent/analytics/` for cross-paper comparison. Used by `/score`, Stage 5 (QA baseline), Stage 6 (final), and `/auto` (per-iteration delta). |

### Submodules

- **`vendor/claude-scientific-skills`** (tracked in `.gitmodules`): 177 domain-specific skills (literature databases, analysis tools). Symlinked to `.claude/skills/` in paper projects. Contains executable Python.
- **`vendor/praxis`** (cloned by `create-paper` into paper projects, not tracked in this repo's `.gitmodules`): Scientific data analysis toolkit. Optional.

### State files in paper projects (not in this repo)

- `.paper.json`: topic, venue, depth, OA resolver config, `knowledge_namespace` (per-project isolation for OpenSearch backend)
- `.paper-state.json`: checkpoint/resume state (stage completion, section progress, agent status)
- `.venue.json`: copy of the selected venue config
- `research/sources/<key>.md`: per-paper source extracts with access level, content snapshot, provenance
- `research/provenance.jsonl`: append-only ledger of every write/revise/cut action
- `research/claims_matrix.md`: Toulmin-structured claims with evidence density scoring

## Editing Guidelines

### Modifying commands or pipeline stages

All command/pipeline files are markdown instructions for Claude Code agents. Changes here affect every paper project immediately (symlinks). Test after editing:

```bash
bash tests/run_all.sh
```

### Adding a venue

1. Create `template/venues/<name>.json` (see `docs/DEVELOPER-GUIDE.md` for required fields)
2. Update `create-paper` help text (~line 53-60)
3. Test: `create-paper test "Test" --venue <name>`

### Adding a slash command

Create `template/claude/commands/<name>.md`. It's automatically available in all projects via symlink. Commands that modify manuscripts should log to `research/provenance.jsonl`. Commands that spawn agents should specify model tier.

### Adding a pipeline stage

1. Create `template/claude/pipeline/stage-N-<name>.md`
2. Update `template/claude/CLAUDE.md` project structure listing
3. Update `template/claude/commands/write-paper.md` to read and execute the stage
4. Add stage to schema in `tests/test_schema.py`

### Venue JSON fields

Each venue config now includes:
- `preamble_extra`: LaTeX lines emitted after packages (float tuning, orphan/widow control, caption position). Injected by `create-paper`.
- `forbidden_packages`: packages incompatible with the venue's document class. Checked by QA reviewers and the Stage 6 preamble audit.

When editing venues, ensure `preamble_extra` and `forbidden_packages` are present. The test suite validates this.

### Model references

Pipeline instructions use `"claude-opus-4-6[1m]"` and `"claude-sonnet-4-6[1m]"` (1M context variants). The shorthand `"opus"` / `"sonnet"` resolves to standard context models, which are insufficient for this pipeline. Always use the full `[1m]` model IDs.

## Permissions model

`template/claude/settings.local.json` defines the auto-approved tool allowlist (symlinked into paper projects). It scopes Bash to specific commands (latexmk, pdflatex, bibtex, python3, curl for APIs, wc, mkdir, etc.). Anything not in the allowlist (git push, arbitrary shell, system package installs) requires manual approval.
