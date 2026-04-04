# Scripts Reference

CLI reference for all 12 utility scripts in `template/scripts/`. These are symlinked into paper projects at `scripts/` and used by the pipeline, slash commands, and manual invocation.

| Script | Purpose | Dependencies |
|-|-|-|
| `knowledge.py` | LightRAG knowledge graph builder and query engine | `OPENROUTER_API_KEY`, LightRAG (auto-installed) |
| `quality.py` | Multi-dimensional paper quality scorer | Stdlib only |
| `verify-references.py` | CrossRef/search citation verification | Stdlib only |
| `format_sentences.py` | LaTeX one-sentence-per-line formatter | Stdlib only |
| `parse-pdf.py` | PDF to markdown converter | `pip install docling` |
| `update-manifest.py` | Rebuild source-manifest.json from project state | Stdlib only |
| `reviewer-kb.py` | Reviewer defense knowledge base builder | Requires knowledge.py |
| `research-story.py` | Provenance narrative generator | Stdlib only |
| `openrouter-fallback.py` | LLM fallback routing via OpenRouter | `OPENROUTER_API_KEY` |
| `pdf-cache.sh` | Shared PDF dedup cache management | Bash, sha256sum/shasum |
| `ensure-venv.sh` | Python venv bootstrapper for knowledge.py | Bash |

## knowledge.py — Knowledge Graph

LightRAG-based knowledge graph builder and query engine. Requires `OPENROUTER_API_KEY`.

### Batch Ingestion (legacy)

```bash
python scripts/knowledge.py build          # Full build from all sources
python scripts/knowledge.py update         # Incremental (new/changed files only)
```

### Streaming Ingestion (preferred)

```bash
python scripts/knowledge.py serve          # Start background worker (one per project)
python scripts/knowledge.py enqueue file [file...]          # Queue files for ingestion
python scripts/knowledge.py enqueue --reindex file...       # Force re-ingestion
python scripts/knowledge.py status         # Show queue: pending/done/failed, worker alive?
python scripts/knowledge.py drain [--timeout N]             # Block until queue empty
python scripts/knowledge.py stop           # Graceful worker shutdown
```

### Querying

```bash
python scripts/knowledge.py query "question"               # Freeform semantic search
python scripts/knowledge.py contradictions                  # Find conflicting claims
python scripts/knowledge.py evidence-for "claim"            # Sources supporting a claim
python scripts/knowledge.py evidence-against "claim"        # Sources challenging a claim
python scripts/knowledge.py entities                        # List extracted entities
python scripts/knowledge.py relationships "entity"          # Show entity connections
python scripts/knowledge.py coverage "document.md"          # Check entity coverage
```

### Ingestion Priority

| Priority | Source | Description |
|-|-|-|
| 1 (highest) | `research/sources/*.md` | Curated source extracts |
| 2 | `research/prepared/**/*.md` | Structured claims/methodology docs (from reviewer-kb.py) |
| 3 | `attachments/parsed/*.md` | Docling-parsed full-text PDFs |
| 4 (lowest) | `attachments/*.pdf` | Raw PDF fallback (pymupdf extraction) |

### Environment

| Variable | Required | Description |
|-|-|-|
| `OPENROUTER_API_KEY` | Yes | LLM calls via OpenRouter (Gemini Flash + Qwen3 8B) |

Graph data is stored in `research/knowledge/` (gitignored). Auto-bootstraps a `.venv` at the repo root on first run.

---

## parse-pdf.py — PDF to Markdown

Converts PDFs to markdown with extracted figures using Docling.

```bash
python3 scripts/parse-pdf.py <pdf_path> [--output-dir <dir>] [--force]
```

| Argument | Description |
|-|-|
| `pdf_path` | Path to the PDF file (required) |
| `--output-dir` | Output directory (default: same directory as the resolved PDF) |
| `--force` | Force re-parse even if markdown already exists |

### Output

- `<pdf_stem>.md` — Markdown with referenced images
- `<pdf_stem>_figures/` — Extracted figures and images

If the PDF is a symlink (e.g., to the shared PDF cache), output goes next to the real file so parsing happens once per unique PDF.

### Exit Codes

| Code | Meaning |
|-|-|
| 0 | Success (prints markdown path to stdout) |
| 1 | Error |
| 2 | Skipped (markdown already exists and is newer than PDF) |

### Dependencies

```bash
pip install docling
```

---

## verify-references.py — Reference Integrity

Verifies every `\cite`/`\citep`/`\citet` key in `main.tex` has a BibTeX entry, source extract, content snapshot, and appropriate access level.

```bash
python3 scripts/verify-references.py                # Verify and report
python3 scripts/verify-references.py --fix          # Verify + auto-remediate fabricated refs
python3 scripts/verify-references.py --json         # JSON output
python3 scripts/verify-references.py --check        # Exit 1 if FABRICATED found
```

### Exit Codes

| Code | Meaning |
|-|-|
| 0 | All references verified (or only warnings) |
| 1 | FABRICATED references found (with `--check`) |
| 2 | Error (missing files, parse failure) |

### Files Read/Written

- Reads: `main.tex`, `references.bib`, `research/sources/`, `attachments/`, `attachments/parsed/`
- Writes: `research/reference_integrity.json`, `research/provenance.jsonl` (with `--fix`)

---

## update-manifest.py — Source Manifest

Rebuilds `research/source-manifest.json` from current project state. Scans bib entries, source extracts, PDFs, and parsed markdown to track all artifacts per source.

```bash
python3 scripts/update-manifest.py                  # Full rebuild from disk
python3 scripts/update-manifest.py --key smith2024  # Update one entry only
```

### Exit Codes

| Code | Meaning |
|-|-|
| 0 | Success |
| 1 | Error |

---

## quality.py — Paper Quality Scorer

Multi-dimensional quality scoring engine. Evaluates papers across 5 dimensions (evidence, writing, structure, research depth, provenance coverage) and produces a JSON scorecard with letter grade. Stdlib-only (no external dependencies).

```bash
python3 scripts/quality.py score                          # Full scorecard (text)
python3 scripts/quality.py score --format json            # JSON output
python3 scripts/quality.py score --dimension evidence     # Single dimension
python3 scripts/quality.py history                        # Score history for this paper
python3 scripts/quality.py record-outcome accepted        # Log submission result
python3 scripts/quality.py record-outcome rejected --notes "Reviewer 2 wanted more experiments"
python3 scripts/quality.py insights                       # Cross-paper analytics
```

### Scoring Dimensions

| Dimension | What it measures |
|-|-|
| Evidence | Citation density, source access levels, claims matrix coverage |
| Writing | Paragraph structure, hedging appropriateness, AI-pattern absence |
| Structure | Section completeness, cross-references, figure/table presence |
| Research | Source count, snowballing coverage, methodology depth |
| Provenance | Provenance log completeness, traceability of claims to sources |

### Grade Scale

A+ (95+), A (90+), A- (85+), B+ (80+), B (75+), B- (70+), C+ (65+), C (60+), C- (55+), D (50+), F (<50)

### Pipeline Integration

- **Stage 5 (QA)**: Runs a baseline score before the review loop starts
- **Stage 6 (Finalization)**: Runs a final score, persists to analytics
- **`/auto`**: Runs before and after each iteration to measure improvement delta
- **`/score`**: Manual invocation from any paper project

### Cross-Paper Analytics

Scores persist to `~/.research-agent/analytics/scores.jsonl`. The `insights` subcommand analyzes trends across all papers: dimension breakdowns, improvement trajectories, venue-specific patterns.

---

## reviewer-kb.py — Reviewer Defense Knowledge Base

Reads structured project files (claims matrix, assumptions, methodology notes) and generates narrative documents optimized for knowledge graph ingestion.

```bash
python scripts/reviewer-kb.py prepare          # Generate research/prepared/
python scripts/reviewer-kb.py build            # prepare + knowledge.py build
python scripts/reviewer-kb.py refresh          # Incremental prepare + kg update
python scripts/reviewer-kb.py defense-brief    # Pre-compute defense for all claims
python scripts/reviewer-kb.py status           # Report graph state + coverage
```

### Files Read

- `research/claims_matrix.md`
- `research/assumptions.md`
- `research/methodology-notes.md`
- `reviews/*.md`

### Output

- `research/prepared/**/*.md` — Structured documents for knowledge graph ingestion

---

## research-story.py — Provenance Narrative

Generates a chronological markdown narrative of the research process from provenance logs.

```bash
python scripts/research-story.py                    # Full story
python scripts/research-story.py --stage 3          # Just the writing stage
python scripts/research-story.py --compact          # Condensed version
python scripts/research-story.py -o story.md        # Write to file
```

### Files Read

- `research/provenance.jsonl`
- `research/log.md`

---

## format_sentences.py — LaTeX Formatter

Reformats LaTeX to one-sentence-per-line (semantic linebreaks) and lints for common issues (non-breaking spaces, smart quotes, ellipsis, en-dashes).

```bash
python scripts/format_sentences.py              # Format main.tex in-place
python scripts/format_sentences.py paper.tex    # Format specified file
python scripts/format_sentences.py --check      # Dry run, exit 1 if changes needed
```

LaTeX treats single newlines as spaces, so compiled output is identical. Sentence splitting is disabled inside protected environments (equation, verbatim, tikzpicture, tabular, algorithm, etc.).

---

## openrouter-fallback.py — Content Filter Bypass

Replays a prompt through OpenRouter when Claude Code's output is blocked by content filtering (e.g., verbatim academic quotes containing sensitive examples).

```bash
python3 scripts/openrouter-fallback.py prompt.txt [model] [max_tokens]
echo "..." | python3 scripts/openrouter-fallback.py - [model] [max_tokens]
python3 scripts/openrouter-fallback.py prompt.txt google/gemini-2.5-flash
```

Output goes to stdout. Caller writes to the target file.

### Model Cascade (default)

1. `google/gemini-2.5-flash` — fast, 1M context, good at academic text
2. `meta-llama/llama-4-maverick` — zero content filter

### Environment

| Variable | Required | Description |
|-|-|-|
| `OPENROUTER_API_KEY` | Yes | API key for OpenRouter |

---

## pdf-cache.sh — Shared PDF Cache

Deduplication and symlink management for cached PDFs across paper projects. Cache location: `~/.research-agent/pdf-cache/`.

```bash
bash scripts/pdf-cache.sh lookup <doi> <title>                                    # Find cache entry
bash scripts/pdf-cache.sh store <bibtexkey> <pdf_path> <title> [doi resolver url authors]  # Cache PDF
bash scripts/pdf-cache.sh link <cache_key> <project_dir> <local_bibtexkey>        # Link cached PDF into project
bash scripts/pdf-cache.sh list                                                     # List all cached entries
bash scripts/pdf-cache.sh info <cache_key>                                         # Show cache entry details
```

PDFs are matched by DOI, content hash, or fuzzy title match. When a PDF is linked into a project, a symlink is created in `attachments/` pointing to the cache.

---

## ensure-venv.sh — Virtual Environment Bootstrap

Creates and maintains the Python virtual environment for knowledge.py and other Python scripts.

```bash
bash scripts/ensure-venv.sh
```

- Creates `.venv` at the repo root if it doesn't exist
- Installs/updates `requirements-knowledge.txt` when the file's hash changes
- Sets `VENV_PYTHON` environment variable to the venv's `python3` path
- Called automatically by `knowledge.py` via `_ensure_venv()`
