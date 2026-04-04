# Contributing to Research Agent

Research Agent is an autonomous paper-writing harness for Claude Code. The repo contains a template directory with slash commands, pipeline stages, venue configs, and scripts. Paper projects created via `create-paper` symlink back to this template, so changes here propagate instantly to all projects.

## Getting Started

1. Fork and clone the repository.
2. Initialize submodules:
   ```bash
   git submodule update --init
   ```
3. Install prerequisites:
   - **Claude Code CLI** (required to run paper pipelines)
   - **LaTeX** distribution (TeX Live or equivalent; `latexmk`, `pdflatex`, `bibtex`)
   - **Python 3.10+**
   - **Git**
4. Run the test suite to confirm everything works:
   ```bash
   bash tests/run_all.sh
   ```

## Repository Layout

| Path | Purpose |
|-|-|
| `template/claude/commands/` | 46 slash commands (markdown instruction files for Claude Code agents) |
| `template/claude/pipeline/` | 24 pipeline stage/phase instruction files read on-demand by orchestrators |
| `template/venues/` | 7 venue JSON configs (documentclass, citation style, writing guide, etc.) |
| `template/scripts/` | Python/Bash utility scripts (knowledge graph, PDF parsing, quality scoring, etc.) |
| `create-paper` | Entry-point script: scaffolds a new paper project with symlinks back to this repo |
| `write-paper` | Entry-point script: launches the autonomous writing pipeline in a paper project |
| `sync-papers` | Migrates old copy-based paper projects to symlinks |
| `tests/` | Test suite (structure, schema validation, prompt linting) |
| `docs/` | Extended documentation and developer guides |

## Running Tests

```bash
bash tests/run_all.sh
```

The test suite checks:
- Template file existence and directory structure
- Venue JSON schema compliance
- Pipeline stage structure and ordering
- Command cross-references and consistency
- Prompt/markdown syntax linting

Individual tests can be run separately:
```bash
bash tests/test_structure.sh          # Template file existence
bash tests/test_prompts.sh            # Prompt markdown linting
python3 tests/test_schema.py          # Venue and state JSON schemas
```

## How to Contribute

### Adding a Slash Command

1. Create `template/claude/commands/<name>.md`.
2. Commands that modify manuscripts should log actions to `research/provenance.jsonl`.
3. Commands that spawn subagents should specify model tier: use `claude-opus-4-6[1m]` or `claude-sonnet-4-6[1m]` (the `[1m]` suffix is required for 1M context).
4. Run `bash tests/run_all.sh` to verify.

The new command is automatically available in all paper projects via symlink.

### Adding a Pipeline Stage

1. Create `template/claude/pipeline/stage-N-<name>.md`.
2. Update `template/claude/commands/write-paper.md` to read and execute the new stage.
3. Update `template/claude/CLAUDE.md` project structure listing.
4. Add the stage to the schema in `tests/test_schema.py`.
5. Run `bash tests/run_all.sh`.

### Adding a Venue

1. Create `template/venues/<name>.json`. See `docs/VENUE-REFERENCE.md` for required fields.
2. Required fields: `name`, `documentclass`, `packages`, `citation_style`, `writing_guide`, `section_order`, `page_limit`, `preamble_extra`, `forbidden_packages`.
3. Update `create-paper` help text (around line 53-60).
4. Test with: `create-paper test "Test topic" --venue <name>`.

### Modifying Scripts

- Scripts live in `template/scripts/`.
- Most scripts are stdlib-only. Exceptions:
  - `knowledge.py` requires LightRAG >= 1.4.12 (deps listed in `requirements-knowledge.txt`).
  - `parse-pdf.py` requires Docling.
- Run relevant tests after changes.

## Code Style

- **Command and pipeline files** are markdown instructions for Claude Code agents. Write them as clear, unambiguous directives.
- **Python scripts** use stdlib where possible. When external dependencies are needed, document them explicitly.
- **Bash scripts** should be POSIX-compatible where feasible.
- There is no build step or linter beyond the test suite.

## PR Guidelines

- Run `bash tests/run_all.sh` before submitting.
- Keep PRs focused: one feature or fix per PR.
- Update `CLAUDE.md` if you add or remove commands, pipeline stages, or scripts.
- Update relevant docs in `docs/` if changing user-facing behavior.

## Architecture Note

Everything under `template/` is symlinked into paper projects. A change to any command, pipeline stage, venue config, or script takes effect immediately in every existing paper project. Test changes carefully before merging.
