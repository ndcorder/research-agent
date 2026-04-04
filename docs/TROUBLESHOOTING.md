# Troubleshooting

## Installation Issues

### "command not found: create-paper"

The entry-point scripts are not on your PATH. Symlink them:

```bash
ln -s $(pwd)/create-paper ~/.local/bin/create-paper
ln -s $(pwd)/write-paper ~/.local/bin/write-paper
```

Ensure `~/.local/bin` is in your PATH (add `export PATH="$HOME/.local/bin:$PATH"` to your shell profile if needed).

### "command not found: pdflatex"

LaTeX is not installed. Install a TeX distribution:

- **macOS**: `brew install --cask mactex-no-gui`
- **Ubuntu/Debian**: `apt install texlive-full`
- **Fedora**: `dnf install texlive-scheme-full`

### Submodule errors or missing vendor directories

```bash
git submodule update --init --recursive
```

If a paper project is missing its vendor symlinks, run `sync-papers` from the research-agent root.

## Pipeline Issues

### Pipeline interrupted mid-run

Re-run `write-paper` in the same paper directory. The pipeline reads `.paper-state.json` and skips completed stages automatically. No data is lost.

### Unexpected permission prompt during write-paper

The pipeline attempted a tool call not on the allowlist in `.claude/settings.local.json`. You can approve it once for the current run. If it is a legitimate operation that should always be allowed, add the command pattern to `settings.local.json`.

### Rate limited by Semantic Scholar

The shared protocols include rate limiting, but heavy parallel research (especially at `--deep` depth) can still trigger 429 errors. Wait 2-3 minutes, then resume with `write-paper`. The pipeline picks up where it left off.

### LaTeX compilation errors

Run `claude "/compile"` inside the paper project for detailed error output. Common causes:

- **Missing packages**: Add the required package to your venue config or `main.tex` preamble.
- **Broken cross-references**: Run compilation twice (or use `latexmk`).
- **BibTeX key mismatches**: Run `claude "/check-citations"` to find keys referenced in text but missing from the `.bib` file.

### Knowledge graph fails to build

The knowledge graph requires `OPENROUTER_API_KEY` to be set. It is optional -- the pipeline works without it. To diagnose:

```bash
python3 scripts/knowledge.py status
```

If the venv failed to bootstrap, delete `.venv/` and retry. The script auto-creates it on first run.

## Quality Issues

### Paper has too many bullet points or listy structure

Run `claude "/review"` to get specific structural feedback, then `claude "/revise-section <section>"` to rewrite problem sections in flowing prose.

### Citations look fabricated

Run `claude "/check-citations"` to verify all BibTeX entries against CrossRef and Semantic Scholar. This flags entries with no DOI match, wrong metadata, or no online trace.

### Paper reads like AI-generated text

Run `claude "/de-ai-polish"` to reduce AI-typical patterns: excessive hedging, em dashes, filler phrases ("it is important to note"), and formulaic transitions.

## Configuration

### How do I use a custom venue?

Create a JSON file in `template/venues/`. See [VENUE-REFERENCE.md](VENUE-REFERENCE.md) for required fields including `preamble_extra` and `forbidden_packages`. Then pass `--venue <name>` to `create-paper`.

### How do I change research depth?

Use the `--deep` flag when creating a paper:

```bash
create-paper my-paper "My topic" --venue neurips --deep
```

This increases research effort from 5 parallel agents to 12 and adds extra snowballing rounds.

### Where are API keys configured?

Set them as environment variables. No config file is needed.

- `OPENROUTER_API_KEY` -- Required for the knowledge graph. Optional for the core pipeline.
- `CORE_API_KEY` -- Used by the open-access PDF resolver cascade.

## Diagnostics

- **`claude "/health"`** -- Run inside a paper project for a comprehensive setup check (LaTeX, submodules, API keys, venue config).
- **`claude "/status"`** -- Shows pipeline progress: which stages are completed, in progress, or remaining.
- **`claude "/score"`** -- Runs the multi-dimensional quality scorer on the current manuscript and prints a scorecard.
